"""Road-streamed, observation-only supervised behavior cloning.

Run from the repository root: python -m bc.train --dataset DATASET --output OUTPUT
Only train and val road files are opened. The final test split is not evaluated here.
"""

import argparse
import hashlib
import json
import random
import re
from pathlib import Path

import numpy as np
import torch

from bc.model import BCPolicy
from bc.contracts import (OBSERVATION_SHAPE, SIMULATOR_FPS, SPLIT_SEEDS,
                          verify_environment_conditions)
from oracle.recording import execution_fingerprint, snapshot_sources


ROAD_NAME = re.compile(r"track[1-5]_seed(\d+)\.npz\Z")
ACTION_NAMES = ("steer", "gas", "brake")
ACTIVE_GAS_WEIGHT = 1.0
MODE_NAMES = ("accelerate", "coast", "brake")


def action_weights(target, gas_weight=ACTIVE_GAS_WEIGHT, brake_weight=1):
    weight = torch.ones_like(target)
    weight[:, 1] += (gas_weight - 1) * (target[:, 1] > .1)
    weight[:, 2] += (brake_weight - 1) * (target[:, 2] > .1)
    return weight


def selection_score(validation, steering_only=False, controls_only=False):
    if steering_only:
        return validation["mse"]["steer"]
    if controls_only:
        return (validation["weighted_mse"]["gas"] + validation["weighted_mse"]["brake"]) / 2
    return validation["weighted_mean_mse"]


def road_paths(dataset, manifest, val_dataset=None, val_manifest=None,
               extra_train_dataset=None, extra_train_manifest=None):
    """Validate geometry disjointness and resolve combined or separate split dirs."""
    val_dataset = dataset if val_dataset is None else val_dataset
    val_manifest = manifest if val_manifest is None else val_manifest
    splits = {}
    seeds = {}
    for split in ("train", "val"):
        names = (manifest if split == "train" else val_manifest).get(split)
        if not isinstance(names, list) or not names or len(names) != len(set(names)):
            raise ValueError(f"{split} requires a nonempty list of unique road files")
        for name in names:
            match = ROAD_NAME.fullmatch(name) if isinstance(name, str) else None
            if match is None:
                raise ValueError(f"Invalid {split} road filename: {name!r}")
        seeds[split] = {int(name.split("_seed")[1].removesuffix(".npz")) for name in names}
        splits[split] = [(dataset if split == "train" else val_dataset) / name for name in names]
    if seeds["train"] & seeds["val"]:
        raise ValueError("Training and validation share geometry seeds")
    for split in ("train", "val"):
        if any(seed not in SPLIT_SEEDS[split] for seed in seeds[split]):
            raise ValueError(f"{split} includes a seed outside its declared geometry split")
    if extra_train_dataset is not None:
        extra_paths = road_paths(extra_train_dataset, extra_train_manifest,
                                 val_dataset, val_manifest)["train"]
        if {path.name for path in splits["train"]} & {path.name for path in extra_paths}:
            raise ValueError("Duplicate training road names across manifests")
        splits["train"].extend(extra_paths)
    return splits


def read_road(path):
    # npz arrays cannot be memmapped; release each road before opening the next.
    with np.load(path, allow_pickle=False) as data:
        observations = data["observations"]
        actions = data["actions"]
    if (observations.dtype != np.float32 or observations.ndim != 4
            or observations.shape[1:] != OBSERVATION_SHAPE
            or actions.dtype != np.float32 or actions.shape != (len(observations), 3)
            or len(observations) == 0):
        raise ValueError(f"Invalid observation/action arrays in {path}")
    if not np.isfinite(observations).all() or not np.isfinite(actions).all():
        raise ValueError(f"Nonfinite observations/actions in {path}")
    if (np.any(observations < 0) or np.any(observations > 1)
            or np.any(actions < [-1, 0, 0]) or np.any(actions > 1)):
        raise ValueError(f"Observations/actions outside official ranges in {path}")
    return observations, actions


def assemble_history(observations, indices, history_frames=4):
    """Reconstruct selected causal histories within one chronological road."""
    if history_frames == 4:
        return observations[indices]
    if history_frames != 8:
        raise ValueError("history_frames must be 4 or 8")
    history_indices = np.maximum(0, np.asarray(indices)[:, None] - np.arange(7, -1, -1))
    return observations[history_indices, 3]


def evaluate(model, paths, batch_size, gas_weight=ACTIVE_GAS_WEIGHT, brake_weight=1,
             include_startup=False):
    model.eval()
    squared = np.zeros(3, dtype=np.float64)
    absolute = np.zeros(3, dtype=np.float64)
    weighted_squared = np.zeros(3, dtype=np.float64)
    weight_sum = np.zeros(3, dtype=np.float64)
    conditional_sums = {name: np.zeros(5, dtype=np.float64)
                        for name in ("large_steer", "high_gas", "high_brake")}
    longitudinal_sums = {name: np.zeros(5, dtype=np.float64)
                         for name in ("all", "high_gas", "high_brake")}
    startup_sums = np.zeros((10, 4, 5), dtype=np.float64)
    mode_confusion = np.zeros((11, 3, 3), dtype=np.int64)
    magnitude_sums = np.zeros((11, 3, 2), dtype=np.float64)
    small_brake_sums = np.zeros((11, 3), dtype=np.int64)
    count = 0
    device = next(model.parameters()).device
    history_frames = getattr(model, "history_frames", 4)
    with torch.inference_mode():
        for path in paths:
            observations, actions = read_road(path)
            for offset in range(0, len(actions), batch_size):
                end = offset + batch_size
                target = torch.from_numpy(actions[offset:end]).to(device)
                images = (assemble_history(observations, np.arange(offset, min(end, len(actions))), 8)
                          if history_frames == 8 else observations[offset:end])
                inputs = torch.from_numpy(images).to(device)
                mode_model = getattr(model, "mode_longitudinal", False)
                controls = model(inputs, decode=False) if mode_model else model(inputs)
                predictions = BCPolicy.decode_mode(controls) if mode_model else controls
                errors = predictions - target
                signed_target = target[:, 1] - target[:, 2]
                signed_prediction = predictions[:, 1] - predictions[:, 2]
                signed_error = signed_prediction - signed_target
                target_mode = torch.where(signed_target > 0, 0, torch.where(signed_target < 0, 2, 1))
                predicted_mode = (controls[:, 1:4].argmax(dim=1) if mode_model else
                                  torch.where(signed_prediction > 0, 0, torch.where(signed_prediction < 0, 2, 1)))
                magnitude = controls[:, 4] if mode_model else signed_prediction.abs()
                magnitude_error = (magnitude - signed_target.abs()).abs().double().cpu().numpy()
                targets = target_mode.cpu().numpy()
                modes = predicted_mode.cpu().numpy()
                small_brakes = ((target[:, 2] > 0) & (target[:, 2] <= .1)).cpu().numpy()

                def accumulate_modes(index, rows):
                    t, p = targets[rows], modes[rows]
                    mode_confusion[index] += np.bincount(t * 3 + p, minlength=9).reshape(3, 3)
                    for active in (0, 2):
                        mask = t == active
                        magnitude_sums[index, active] += (mask.sum(), magnitude_error[rows][mask].sum())
                    small = small_brakes[rows]
                    small_brake_sums[index] += (small.sum(), (small & (p == 2)).sum(),
                                                (small & (p == 0)).sum())

                accumulate_modes(0, slice(None))
                if include_startup and offset < 10:
                    for local in range(min(10 - offset, len(target))):
                        accumulate_modes(1 + offset + local, slice(local, local + 1))
                for name, totals in longitudinal_sums.items():
                    mask = (torch.ones_like(signed_target, dtype=torch.bool) if name == "all" else
                            target[:, 1 if name == "high_gas" else 2] > .1)
                    selected_errors = signed_error[mask].double()
                    totals += np.array([
                        mask.sum().item(), selected_errors.abs().sum().item(),
                        selected_errors.square().sum().item(),
                        signed_target[mask].double().sum().item(),
                        signed_prediction[mask].double().sum().item()])
                weight = action_weights(target, gas_weight, brake_weight)
                squared += errors.square().sum(dim=0).double().cpu().numpy()
                absolute += errors.abs().sum(dim=0).double().cpu().numpy()
                weighted_squared += (weight * errors.square()).sum(dim=0).double().cpu().numpy()
                weight_sum += weight.sum(dim=0).double().cpu().numpy()
                if include_startup and offset < 10:
                    length = min(10 - offset, len(target))
                    initial_errors = torch.cat((errors[:length], signed_error[:length, None]), dim=1).double()
                    startup_sums[offset:offset + length] += np.stack((
                        np.ones((length, 4)),
                        initial_errors.abs().cpu().numpy(),
                        initial_errors.square().cpu().numpy(),
                        torch.cat((target[:length], signed_target[:length, None]), dim=1).double().cpu().numpy(),
                        torch.cat((predictions[:length], signed_prediction[:length, None]), dim=1).double().cpu().numpy()), axis=-1)
                for component, totals in enumerate(conditional_sums.values()):
                    mask = target[:, component].abs() > .1
                    selected_errors = errors[mask, component].double()
                    totals += np.array([
                        mask.sum().item(), selected_errors.abs().sum().item(),
                        selected_errors.square().sum().item(),
                        target[mask, component].double().sum().item(),
                        predictions[mask, component].double().sum().item()])
            count += len(actions)
            del observations, actions
    mse = squared / count
    mae = absolute / count
    weighted_mse = weighted_squared / weight_sum
    conditional = {
        name: {"count": int(totals[0]), **{
            metric: float(value / totals[0]) if totals[0] else None
            for metric, value in zip(("mae", "mse", "target_mean", "prediction_mean"), totals[1:])}}
        for name, totals in conditional_sums.items()}
    result = {"samples": count, "mse": dict(zip(ACTION_NAMES, mse.tolist())),
            "mae": dict(zip(ACTION_NAMES, mae.tolist())), "mean_mse": float(mse.mean()),
            "weighted_mse": dict(zip(ACTION_NAMES, weighted_mse.tolist())),
              "weighted_mean_mse": float(weighted_mse.mean()), "conditional": conditional}
    result["longitudinal"] = {
        name: {"count": int(totals[0]), **{
            metric: float(value / totals[0]) if totals[0] else None
            for metric, value in zip(("mae", "mse", "target_mean", "prediction_mean"), totals[1:])}}
        for name, totals in longitudinal_sums.items()}
    def mode_metrics(confusion, magnitude_totals, small):
        counts = confusion.sum(axis=1)
        def ratio(value, total):
            return float(value / total) if total else None
        active_count, active_error = magnitude_totals[[0, 2]].sum(axis=0)
        return {"names": list(MODE_NAMES), "confusion": confusion.tolist(),
                "count": int(counts.sum()), "accuracy": ratio(np.trace(confusion), counts.sum()),
                "brake_recall": ratio(confusion[2, 2], counts[2]),
                "accelerate_to_brake": {"count": int(confusion[0, 2]), "total": int(counts[0]),
                                        "rate": ratio(confusion[0, 2], counts[0])},
                "brake_to_accelerate": {"count": int(confusion[2, 0]), "total": int(counts[2]),
                                        "rate": ratio(confusion[2, 0], counts[2])},
                "active_magnitude": {"count": int(active_count), "mae": ratio(active_error, active_count),
                    "by_mode": {MODE_NAMES[i]: {"count": int(magnitude_totals[i, 0]),
                                                "mae": ratio(magnitude_totals[i, 1], magnitude_totals[i, 0])}
                                for i in (0, 2)}},
                "small_brake": {"count": int(small[0]), "recall": ratio(small[1], small[0]),
                                "accelerate_confusion_count": int(small[2])}}
    result["longitudinal_mode"] = mode_metrics(mode_confusion[0], magnitude_sums[0], small_brake_sums[0])
    if include_startup:
        def initial_metrics(totals):
            return {name: {"count": int(values[0]), **{
                metric: float(value / values[0]) if values[0] else None
                for metric, value in zip(("mae", "mse", "target_mean", "prediction_mean"), values[1:])}}
                for name, values in zip((*ACTION_NAMES, "longitudinal"), totals)}
        result["startup"] = {
            "indexing": "zero-based pre-action steps 0..9 (first ten actions)",
            "first_10": initial_metrics(startup_sums.sum(axis=0)),
            "by_step": [{"step": step, **initial_metrics(totals)}
                         for step, totals in enumerate(startup_sums)]}
        result["startup"]["mode"] = {
            "first_10": mode_metrics(mode_confusion[1:].sum(axis=0), magnitude_sums[1:].sum(axis=0),
                                      small_brake_sums[1:].sum(axis=0)),
            "by_step": [{"step": step, **mode_metrics(mode_confusion[step + 1],
                          magnitude_sums[step + 1], small_brake_sums[step + 1])} for step in range(10)]}
    return result


def training_batches(plan, rng, batch_size, continuous=False, history_frames=4,
                     balanced_actions=False):
    """Stream the same sampled rows, optionally carrying one partial batch across roads."""
    if history_frames not in (4, 8):
        raise ValueError("history_frames must be 4 or 8")
    pending = None
    for path, limit, is_recovery in plan:
        if history_frames == 8 and is_recovery:
            raise ValueError("history8 cannot be combined with recovery")
        if continuous and is_recovery:
            raise ValueError("continuous-batches cannot be combined with recovery")
        if balanced_actions and is_recovery:
            raise ValueError("balanced-actions cannot be combined with recovery")
        if not limit:
            continue
        observations, actions = read_road(path)
        if balanced_actions:
            # Replay rare labels, not trajectories; chronological pixels stay intact.
            selected = []
            for component in (1, 2):
                candidates = np.flatnonzero(actions[:, component] > .1)
                quota = limit // 8 if len(candidates) else 0
                selected.append(rng.choice(candidates, size=quota, replace=quota > len(candidates)))
            natural_count = limit - sum(len(indices) for indices in selected)
            selected.append(rng.choice(len(actions), size=natural_count, replace=True)
                            if natural_count > len(actions) else rng.permutation(len(actions))[:natural_count])
            indices = np.concatenate(selected)
            rng.shuffle(indices)
        else:
            indices = (rng.choice(len(actions), size=limit, replace=limit > len(actions))
                       if is_recovery else rng.permutation(len(actions))[:limit])
        offset = 0
        while offset < len(indices):
            needed = batch_size - (len(pending[1]) if pending is not None else 0)
            batch_indices = indices[offset:offset + needed]
            x = assemble_history(observations, batch_indices, history_frames)
            y = actions[batch_indices]
            offset += len(batch_indices)
            if pending is not None:
                x = np.concatenate((pending[0], x))
                y = np.concatenate((pending[1], y))
            if continuous and len(y) < batch_size:
                pending = (x, y)
            else:
                pending = None
                yield x, y, is_recovery
        del observations, actions
    if pending is not None:
        yield pending[0], pending[1], False


def train(args):
    if args.mode_longitudinal and (args.history_frames != 8 or args.signed_longitudinal
                                  or args.recovery_dataset is not None
                                  or args.active_gas_weight != 1 or args.active_brake_weight != 1):
        raise ValueError("mode-longitudinal requires history8, unit weights, no signed or recovery")
    if args.signed_longitudinal and (args.history_frames != 8 or args.recovery_dataset is not None
                                    or args.active_gas_weight != 1 or args.active_brake_weight != 1):
        raise ValueError("signed-longitudinal trial requires history8, unit weights and no recovery")
    if args.balanced_actions and args.recovery_dataset is not None:
        raise ValueError("balanced-actions cannot be combined with recovery")
    if args.history_frames == 8 and (args.motion_features or args.recovery_dataset is not None):
        raise ValueError("history8 cannot be combined with motion features or recovery")
    if args.epochs < 1 or args.batch_size < 1 or args.max_train_samples < 1 or args.num_threads < 1:
        raise ValueError("epochs, batch-size, max-train-samples and num-threads must be positive")
    if not np.isfinite(args.lr) or args.lr <= 0:
        raise ValueError("lr must be finite and positive")
    if not np.isfinite(args.active_gas_weight) or args.active_gas_weight < 1:
        raise ValueError("active-gas-weight must be finite and at least one")
    if not np.isfinite(args.active_brake_weight) or args.active_brake_weight < 1:
        raise ValueError("active-brake-weight must be finite and at least one")
    if args.recovery_steering_only and args.recovery_dataset is None:
        raise ValueError("steering-only recovery needs a recovery dataset")
    if args.recovery_controls_only and args.recovery_dataset is None:
        raise ValueError("controls-only recovery needs a recovery dataset")
    if args.recovery_controls_only and args.recovery_steering_only:
        raise ValueError("Choose only one recovery action group")
    if not 0 <= args.recovery_fraction < 1:
        raise ValueError("recovery-fraction must be in [0, 1)")
    if args.continuous_batches and args.recovery_dataset is not None:
        raise ValueError("continuous-batches cannot be combined with recovery")
    dataset = Path(args.dataset)
    with (dataset / "split_manifest.json").open() as source:
        manifest = json.load(source)
    val_manifest = None
    if args.val_dataset is not None:
        with (args.val_dataset / "split_manifest.json").open() as source:
            val_manifest = json.load(source)
    extra_train_manifest = None
    if args.extra_train_dataset is not None:
        with (args.extra_train_dataset / "split_manifest.json").open() as source:
            extra_train_manifest = json.load(source)
    paths = road_paths(dataset, manifest, args.val_dataset, val_manifest,
                       args.extra_train_dataset, extra_train_manifest)
    dataset_provenance = {}
    conditions = None
    for label, directory in (("train", dataset), ("val", args.val_dataset or dataset),
                             ("extra_train", args.extra_train_dataset)):
        if directory is None:
            continue
        provenance_path = directory / "provenance.json"
        try:
            provenance = json.loads(provenance_path.read_text())
        except (OSError, ValueError) as error:
            raise ValueError(f"Cannot verify {label} collector provenance: {error}") from error
        actual = verify_environment_conditions(provenance, label)
        if provenance.get("kind") == "matched_teacher_view" and args.history_frames != 4:
            raise ValueError("Matched teacher views contain stored four-frame inputs, not chronological roads")
        if conditions is not None and actual != conditions:
            raise ValueError(f"{label} collector conditions differ across training/validation datasets")
        conditions = actual
        dataset_provenance[label] = hashlib.sha256(provenance_path.read_bytes()).hexdigest()
    recovery_paths = []
    if args.recovery_dataset is not None:
        recovery_paths = sorted(args.recovery_dataset.glob("track*_seed*_recovery.npz"))
        if not recovery_paths:
            raise ValueError("Recovery directory has no student-state trajectories")
        for path in recovery_paths:
            match = re.fullmatch(r"track[1-5]_seed(\d+)_recovery\.npz", path.name)
            if match is None or int(match[1]) not in SPLIT_SEEDS["train"]:
                raise ValueError(f"Recovery road is not in training split: {path.name}")
        unique_paths = []
        seen = set()
        for path in recovery_paths:
            observations, actions = read_road(path)
            digest = hashlib.sha256(observations.tobytes() + actions.tobytes()).digest()
            if digest not in seen:
                unique_paths.append(path)
                seen.add(digest)
        recovery_paths = unique_paths
    args.output.mkdir(parents=True, exist_ok=False)
    fingerprint = execution_fingerprint(("bc/train.py", "bc/model.py", "bc/contracts.py"))
    source_snapshot = snapshot_sources(args.output, fingerprint)
    run_provenance = {**fingerprint, "source_snapshot": source_snapshot,
                      "collector_conditions": conditions,
                      "dataset_provenance_sha256": dataset_provenance}
    (args.output / "provenance.json").write_text(json.dumps(run_provenance, indent=2) + "\n")
    torch.set_num_threads(args.num_threads)
    torch.manual_seed(args.seed)
    random.seed(args.seed)
    rng = np.random.default_rng(args.seed)
    if args.device == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA requested but unavailable")
    device = torch.device("cuda" if args.device == "cuda" or
                          args.device == "auto" and torch.cuda.is_available() else "cpu")
    model = BCPolicy(motion=args.motion_features, history_frames=args.history_frames,
                      signed_longitudinal=args.signed_longitudinal,
                      mode_longitudinal=args.mode_longitudinal).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    best_loss = float("inf")
    history = []

    for epoch in range(1, args.epochs + 1):
        model.train()
        permutation = rng.permutation(len(paths["train"]))
        # Allocate the epoch budget evenly so later roads are never silently omitted.
        recovery_budget = int(args.max_train_samples * args.recovery_fraction) if recovery_paths else 0
        base, extra = divmod(args.max_train_samples - recovery_budget, len(permutation))
        plan = [(paths["train"][index], base + (position < extra), False)
                for position, index in enumerate(permutation)]
        if recovery_paths:
            per_road, extra = divmod(recovery_budget, len(recovery_paths))
            plan += [(path, per_road + (index < extra), True)
                     for index, path in enumerate(recovery_paths)]
            rng.shuffle(plan)
        total_squared = np.zeros(3, dtype=np.float64)
        trained = 0
        optimizer_steps = 0
        sampled_conditional = np.zeros(3, dtype=np.int64)
        for observations, actions, is_recovery in training_batches(
                plan, rng, args.batch_size, args.continuous_batches, args.history_frames,
                args.balanced_actions):
            x = torch.from_numpy(observations).to(device)
            y = torch.from_numpy(actions).to(device)
            optimizer.zero_grad(set_to_none=True)
            controls = model(x, decode=False) if args.signed_longitudinal or args.mode_longitudinal else model(x)
            errors = (BCPolicy.decode_mode(controls) if args.mode_longitudinal else
                      BCPolicy.decode_signed(controls) if args.signed_longitudinal else controls) - y
            weight = action_weights(y, args.active_gas_weight, args.active_brake_weight)
            if is_recovery and args.recovery_steering_only:
                weight[:, 0] = 3
                weight[:, 1:] = 0
            if is_recovery and args.recovery_controls_only:
                weight[:, 0] = 0
                weight[:, 1:] *= 1.5
            # Keep steering's original 1/3 coefficient when two controls become one.
            loss = ((errors[:, 0].square() + (controls[:, 1] - (y[:, 1] - y[:, 2])).square()).mean() / 3
                     if args.signed_longitudinal else (weight * errors.square()).mean())
            if args.mode_longitudinal:
                modes, magnitude = BCPolicy.longitudinal_targets(y)
                active = modes != 1
                magnitude_loss = ((controls[active, 4] - magnitude[active]).square().mean()
                                  if active.any() else controls[:, 4].sum() * 0)
                loss = (errors[:, 0].square().mean()
                        + torch.nn.functional.cross_entropy(controls[:, 1:4], modes)
                        + magnitude_loss) / 3
            loss.backward()
            optimizer.step()
            optimizer_steps += 1
            total_squared += errors.detach().square().sum(dim=0).double().cpu().numpy()
            trained += len(actions)
            sampled_conditional += (np.abs(actions) > .1).sum(axis=0)
        if not trained:
            raise ValueError("No training samples available")
        validation = evaluate(model, paths["val"], args.batch_size,
                               args.active_gas_weight, args.active_brake_weight,
                               include_startup=args.mode_longitudinal)
        record = {"epoch": epoch, "train_samples": trained,
                   "optimizer_steps": optimizer_steps,
                   "sampled_conditional_counts": dict(zip(
                       ("large_steer", "high_gas", "high_brake"), sampled_conditional.tolist())),
                  "recovery_samples": recovery_budget,
                  "train_mse": dict(zip(ACTION_NAMES, (total_squared / trained).tolist())),
                  "val": validation}
        history.append(record)
        selection = selection_score(validation, args.recovery_steering_only, args.recovery_controls_only)
        if selection < best_loss:
            best_loss = selection
            torch.save({"model": ("BCPolicy-mode-history8-v5" if args.mode_longitudinal else
                                  "BCPolicy-signed-history8-v4" if args.signed_longitudinal else
                                  "BCPolicy-history8-v3" if args.history_frames == 8 else
                                  "BCPolicy-motion-v2" if args.motion_features else "BCPolicy-v1"),
                        "history_frames": args.history_frames,
                        "state_dict": {key: value.cpu() for key, value in model.state_dict().items()},
                        "epoch": epoch, "seed": args.seed, "val": validation},
                       args.output / "best.pt")
        print(json.dumps(record), flush=True)

    best = BCPolicy.from_checkpoint(args.output / "best.pt")
    train_prediction = evaluate(best, paths["train"], args.batch_size,
                                 args.active_gas_weight, args.active_brake_weight,
                                 include_startup=args.mode_longitudinal)
    result = {**run_provenance, "seed": args.seed, "train_roads": [p.name for p in paths["train"]],
               "val_roads": [p.name for p in paths["val"]],
               "recovery_roads": [p.name for p in recovery_paths],
               "max_train_samples_per_epoch": args.max_train_samples,
               "config": {"epochs": args.epochs, "batch_size": args.batch_size,
                            "continuous_batches": args.continuous_batches,
                            "balanced_actions": args.balanced_actions,
                             "signed_longitudinal": args.signed_longitudinal,
                             "mode_longitudinal": args.mode_longitudinal,
                             "training_objective": ("(steer_mse+mode_ce+active_magnitude_mse)/3"
                                                    if args.mode_longitudinal else
                                                    "(steer_mse+signed_longitudinal_mse)/3"
                                                   if args.signed_longitudinal else "weighted_action_mean_mse"),
                            "sampling": ("per_road_1/8_high_gas_1/8_high_brake_3/4_natural"
                                         if args.balanced_actions else "natural_per_road"),
                          "learning_rate": args.lr, "num_threads": args.num_threads,
                          "device": str(device), "active_gas_weight": args.active_gas_weight,
                          "active_brake_weight": args.active_brake_weight,
                          "recovery_fraction": args.recovery_fraction if recovery_paths else 0,
                           "motion_features": args.motion_features,
                           "history_frames": args.history_frames,
                           "history_initialization": ("fresh_4frame_copy_newest4_zero_older4"
                                                      if args.history_frames == 8 else "fresh_4frame"),
                           "history_padding": ("repeat_reset_image" if args.history_frames == 8
                                               else "official_observation_stack"),
                           "history_spacing_decisions": 1,
                            "history_spacing_simulator_ticks": conditions["frame_skip"],
                            "history_spacing_seconds": conditions["frame_skip"] / SIMULATOR_FPS,
                          "recovery_steering_only": args.recovery_steering_only,
                          "recovery_controls_only": args.recovery_controls_only},
               "train_manifest_sha256": hashlib.sha256((dataset / "split_manifest.json").read_bytes()).hexdigest(),
               "val_manifest_sha256": hashlib.sha256(((args.val_dataset or dataset) / "split_manifest.json").read_bytes()).hexdigest(),
               "best_checkpoint_sha256": hashlib.sha256((args.output / "best.pt").read_bytes()).hexdigest(),
               "best_train_prediction": train_prediction,
               "best_val_selection_score": best_loss,
               "selection_metric": ("steer_mse" if args.recovery_steering_only else
                                    "weighted_gas_brake_mse" if args.recovery_controls_only else
                                    "weighted_mean_mse"),
               "history": history}
    if args.extra_train_dataset is not None:
        result["extra_train_manifest_sha256"] = hashlib.sha256(
            (args.extra_train_dataset / "split_manifest.json").read_bytes()).hexdigest()
    (args.output / "history.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    diagnostic = parser.add_argument_group("Historical diagnostic options", "Explicit opt-in; not the plain BC baseline")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--val-dataset", type=Path,
                        help="Separate collector output containing the validation split")
    parser.add_argument("--extra-train-dataset", type=Path,
                        help="Append a separate collector training split with unique road names")
    diagnostic.add_argument("--recovery-dataset", type=Path,
                        help="Student-visited oracle-labeled training roads from bc.evaluate")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--continuous-batches", action="store_true",
                         help="Carry partial batches across roads; incompatible with recovery")
    diagnostic.add_argument("--balanced-actions", action="store_true",
                          help="Sample 1/8 high-gas + 1/8 high-brake per road; missing bins revert to natural")
    diagnostic.add_argument("--signed-longitudinal", action="store_true",
                           help="History8 trial: fit gas-minus-brake with tanh, decode mutually exclusive controls")
    diagnostic.add_argument("--mode-longitudinal", action="store_true",
                            help="Final BC trial: accelerate/coast/brake logits and active magnitude")
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--num-threads", type=int, default=2)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    diagnostic.add_argument("--motion-features", action="store_true",
                        help="Add observation-only temporal pixel-change magnitudes")
    diagnostic.add_argument("--history-frames", type=int, choices=(4, 8), default=4,
                        help="Eight-frame causal pixel history; incompatible with motion/recovery")
    diagnostic.add_argument("--active-gas-weight", type=float, default=ACTIVE_GAS_WEIGHT,
                           help="Rare-gas weighting diagnostic; plain baseline uses 1 (legacy experiments used 40)")
    diagnostic.add_argument("--active-brake-weight", type=float, default=1,
                           help="Rare-brake weighting diagnostic; plain baseline uses 1")
    diagnostic.add_argument("--recovery-steering-only", action="store_true",
                        help="On student states, fit only steering; keep normal-road gas/brake training")
    diagnostic.add_argument("--recovery-controls-only", action="store_true",
                        help="On student states, fit only gas/brake; keep normal-road steering training")
    diagnostic.add_argument("--recovery-fraction", type=float, default=.25,
                        help="Fraction of per-epoch sampling budget for student-visited states")
    parser.add_argument("--max-train-samples", type=int, default=20000,
                        help="Maximum samples per epoch, distributed across training roads")
    return train(parser.parse_args(argv))


if __name__ == "__main__":
    main()
