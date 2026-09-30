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
from bc.contracts import BASELINE_CONDITIONS, OBSERVATION_SHAPE, SIMULATOR_FPS, SPLIT_SEEDS
from oracle.recording import execution_fingerprint, snapshot_sources


ROAD_NAME = re.compile(r"track[1-5]_seed(\d+)\.npz\Z")
ACTION_NAMES = ("steer", "gas", "brake")
ACTIVE_GAS_WEIGHT = 1.0


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


def evaluate(model, paths, batch_size, gas_weight=ACTIVE_GAS_WEIGHT, brake_weight=1):
    model.eval()
    squared = np.zeros(3, dtype=np.float64)
    absolute = np.zeros(3, dtype=np.float64)
    weighted_squared = np.zeros(3, dtype=np.float64)
    weight_sum = np.zeros(3, dtype=np.float64)
    conditional_sums = {name: np.zeros(5, dtype=np.float64)
                        for name in ("large_steer", "high_gas", "high_brake")}
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
                predictions = model(torch.from_numpy(images).to(device))
                errors = predictions - target
                weight = action_weights(target, gas_weight, brake_weight)
                squared += errors.square().sum(dim=0).double().cpu().numpy()
                absolute += errors.abs().sum(dim=0).double().cpu().numpy()
                weighted_squared += (weight * errors.square()).sum(dim=0).double().cpu().numpy()
                weight_sum += weight.sum(dim=0).double().cpu().numpy()
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
    return {"samples": count, "mse": dict(zip(ACTION_NAMES, mse.tolist())),
            "mae": dict(zip(ACTION_NAMES, mae.tolist())), "mean_mse": float(mse.mean()),
            "weighted_mse": dict(zip(ACTION_NAMES, weighted_mse.tolist())),
            "weighted_mean_mse": float(weighted_mse.mean()), "conditional": conditional}


def training_batches(plan, rng, batch_size, continuous=False, history_frames=4):
    """Stream the same sampled rows, optionally carrying one partial batch across roads."""
    if history_frames not in (4, 8):
        raise ValueError("history_frames must be 4 or 8")
    pending = None
    for path, limit, is_recovery in plan:
        if history_frames == 8 and is_recovery:
            raise ValueError("history8 cannot be combined with recovery")
        if continuous and is_recovery:
            raise ValueError("continuous-batches cannot be combined with recovery")
        if not limit:
            continue
        observations, actions = read_road(path)
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
        actual = provenance.get("conditions", {})
        deviations = {key: {"expected": value, "actual": actual.get(key)}
                      for key, value in BASELINE_CONDITIONS.items() if actual.get(key) != value}
        if deviations:
            raise ValueError(f"{label} collector conditions deviate from BC baseline: {deviations}")
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
    model = BCPolicy(motion=args.motion_features, history_frames=args.history_frames).to(device)
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
        for observations, actions, is_recovery in training_batches(
                plan, rng, args.batch_size, args.continuous_batches, args.history_frames):
            x = torch.from_numpy(observations).to(device)
            y = torch.from_numpy(actions).to(device)
            optimizer.zero_grad(set_to_none=True)
            errors = model(x) - y
            weight = action_weights(y, args.active_gas_weight, args.active_brake_weight)
            if is_recovery and args.recovery_steering_only:
                weight[:, 0] = 3
                weight[:, 1:] = 0
            if is_recovery and args.recovery_controls_only:
                weight[:, 0] = 0
                weight[:, 1:] *= 1.5
            loss = (weight * errors.square()).mean()
            loss.backward()
            optimizer.step()
            optimizer_steps += 1
            total_squared += errors.detach().square().sum(dim=0).double().cpu().numpy()
            trained += len(actions)
        if not trained:
            raise ValueError("No training samples available")
        validation = evaluate(model, paths["val"], args.batch_size,
                              args.active_gas_weight, args.active_brake_weight)
        record = {"epoch": epoch, "train_samples": trained,
                  "optimizer_steps": optimizer_steps,
                  "recovery_samples": recovery_budget,
                  "train_mse": dict(zip(ACTION_NAMES, (total_squared / trained).tolist())),
                  "val": validation}
        history.append(record)
        selection = selection_score(validation, args.recovery_steering_only, args.recovery_controls_only)
        if selection < best_loss:
            best_loss = selection
            torch.save({"model": ("BCPolicy-history8-v3" if args.history_frames == 8 else
                                  "BCPolicy-motion-v2" if args.motion_features else "BCPolicy-v1"),
                        "history_frames": args.history_frames,
                        "state_dict": {key: value.cpu() for key, value in model.state_dict().items()},
                        "epoch": epoch, "seed": args.seed, "val": validation},
                       args.output / "best.pt")
        print(json.dumps(record), flush=True)

    best = BCPolicy.from_checkpoint(args.output / "best.pt")
    train_prediction = evaluate(best, paths["train"], args.batch_size,
                                args.active_gas_weight, args.active_brake_weight)
    result = {**run_provenance, "seed": args.seed, "train_roads": [p.name for p in paths["train"]],
               "val_roads": [p.name for p in paths["val"]],
               "recovery_roads": [p.name for p in recovery_paths],
               "max_train_samples_per_epoch": args.max_train_samples,
               "config": {"epochs": args.epochs, "batch_size": args.batch_size,
                           "continuous_batches": args.continuous_batches,
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
