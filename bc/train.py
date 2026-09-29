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


ROAD_NAME = re.compile(r"track\d+_seed(\d+)\.npz\Z")
ACTION_NAMES = ("steer", "gas", "brake")
SPLIT_SEEDS = {"train": range(11, 31), "val": range(31, 36)}
ACTIVE_GAS_WEIGHT = 40.0


def road_paths(dataset, manifest, val_dataset=None, val_manifest=None):
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
    return splits


def read_road(path):
    # npz arrays cannot be memmapped; release each road before opening the next.
    with np.load(path, allow_pickle=False) as data:
        observations = data["observations"]
        actions = data["actions"]
    if (observations.dtype != np.float32 or observations.ndim != 4
            or observations.shape[1:] != (4, 84, 84)
            or actions.dtype != np.float32 or actions.shape != (len(observations), 3)
            or len(observations) == 0):
        raise ValueError(f"Invalid observation/action arrays in {path}")
    if not np.isfinite(observations).all() or not np.isfinite(actions).all():
        raise ValueError(f"Nonfinite observations/actions in {path}")
    if (np.any(observations < 0) or np.any(observations > 1)
            or np.any(actions < [-1, 0, 0]) or np.any(actions > 1)):
        raise ValueError(f"Observations/actions outside official ranges in {path}")
    return observations, actions


def evaluate(model, paths, batch_size, gas_weight=ACTIVE_GAS_WEIGHT, brake_weight=1):
    model.eval()
    squared = np.zeros(3, dtype=np.float64)
    absolute = np.zeros(3, dtype=np.float64)
    weighted_squared = np.zeros(3, dtype=np.float64)
    weight_sum = np.zeros(3, dtype=np.float64)
    count = 0
    device = next(model.parameters()).device
    with torch.inference_mode():
        for path in paths:
            observations, actions = read_road(path)
            for offset in range(0, len(actions), batch_size):
                end = offset + batch_size
                target = torch.from_numpy(actions[offset:end]).to(device)
                predictions = model(torch.from_numpy(observations[offset:end]).to(device))
                errors = predictions - target
                weight = torch.ones_like(target)
                weight[:, 1] += (gas_weight - 1) * (target[:, 1] > .1)
                weight[:, 2] += (brake_weight - 1) * (target[:, 2] > .1)
                squared += errors.square().sum(dim=0).double().cpu().numpy()
                absolute += errors.abs().sum(dim=0).double().cpu().numpy()
                weighted_squared += (weight * errors.square()).sum(dim=0).double().cpu().numpy()
                weight_sum += weight.sum(dim=0).double().cpu().numpy()
            count += len(actions)
            del observations, actions
    mse = squared / count
    mae = absolute / count
    weighted_mse = weighted_squared / weight_sum
    return {"samples": count, "mse": dict(zip(ACTION_NAMES, mse.tolist())),
            "mae": dict(zip(ACTION_NAMES, mae.tolist())), "mean_mse": float(mse.mean()),
            "weighted_mse": dict(zip(ACTION_NAMES, weighted_mse.tolist())),
            "weighted_mean_mse": float(weighted_mse.mean())}


def train(args):
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
    dataset = Path(args.dataset)
    with (dataset / "split_manifest.json").open() as source:
        manifest = json.load(source)
    val_manifest = None
    if args.val_dataset is not None:
        with (args.val_dataset / "split_manifest.json").open() as source:
            val_manifest = json.load(source)
    paths = road_paths(dataset, manifest, args.val_dataset, val_manifest)
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
    torch.set_num_threads(args.num_threads)
    torch.manual_seed(args.seed)
    random.seed(args.seed)
    rng = np.random.default_rng(args.seed)
    if args.device == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA requested but unavailable")
    device = torch.device("cuda" if args.device == "cuda" or
                          args.device == "auto" and torch.cuda.is_available() else "cpu")
    model = BCPolicy(motion=args.motion_features).to(device)
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
        for path, limit, is_recovery in plan:
            if not limit:
                continue
            observations, actions = read_road(path)
            indices = (rng.choice(len(actions), size=limit, replace=limit > len(actions))
                       if is_recovery else rng.permutation(len(actions))[:limit])
            for offset in range(0, len(indices), args.batch_size):
                batch_indices = indices[offset:offset + args.batch_size]
                x = torch.from_numpy(observations[batch_indices]).to(device)
                y = torch.from_numpy(actions[batch_indices]).to(device)
                optimizer.zero_grad(set_to_none=True)
                errors = model(x) - y
                weight = torch.ones_like(y)
                weight[:, 1] += (args.active_gas_weight - 1) * (y[:, 1] > .1)
                weight[:, 2] += (args.active_brake_weight - 1) * (y[:, 2] > .1)
                if is_recovery and args.recovery_steering_only:
                    weight[:, 0] = 3
                    weight[:, 1:] = 0
                if is_recovery and args.recovery_controls_only:
                    weight[:, 0] = 0
                    weight[:, 1:] *= 1.5
                loss = (weight * errors.square()).mean()
                loss.backward()
                optimizer.step()
                total_squared += errors.detach().square().sum(dim=0).double().cpu().numpy()
                trained += len(batch_indices)
            del observations, actions
        if not trained:
            raise ValueError("No training samples available")
        validation = evaluate(model, paths["val"], args.batch_size,
                              args.active_gas_weight, args.active_brake_weight)
        record = {"epoch": epoch, "train_samples": trained,
                  "recovery_samples": recovery_budget,
                  "train_mse": dict(zip(ACTION_NAMES, (total_squared / trained).tolist())),
                  "val": validation}
        history.append(record)
        selection = (validation["mse"]["steer"] if args.recovery_steering_only
                     else (validation["weighted_mse"]["gas"] + validation["weighted_mse"]["brake"]) / 2
                     if args.recovery_controls_only else validation["weighted_mean_mse"])
        if selection < best_loss:
            best_loss = selection
            torch.save({"model": "BCPolicy-motion-v2" if args.motion_features else "BCPolicy-v1",
                        "state_dict": {key: value.cpu() for key, value in model.state_dict().items()},
                        "epoch": epoch, "seed": args.seed, "val": validation},
                       args.output / "best.pt")
        print(json.dumps(record), flush=True)

    best = BCPolicy.from_checkpoint(args.output / "best.pt")
    train_prediction = evaluate(best, paths["train"], args.batch_size,
                                args.active_gas_weight, args.active_brake_weight)
    result = {"seed": args.seed, "train_roads": [p.name for p in paths["train"]],
               "val_roads": [p.name for p in paths["val"]],
               "recovery_roads": [p.name for p in recovery_paths],
               "max_train_samples_per_epoch": args.max_train_samples,
               "config": {"epochs": args.epochs, "batch_size": args.batch_size,
                          "learning_rate": args.lr, "num_threads": args.num_threads,
                          "device": str(device), "active_gas_weight": args.active_gas_weight,
                          "active_brake_weight": args.active_brake_weight,
                          "recovery_fraction": args.recovery_fraction if recovery_paths else 0,
                          "motion_features": args.motion_features,
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
    (args.output / "history.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--val-dataset", type=Path,
                        help="Separate collector output containing the validation split")
    parser.add_argument("--recovery-dataset", type=Path,
                        help="Student-visited oracle-labeled training roads from bc.evaluate")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--num-threads", type=int, default=2)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--motion-features", action="store_true",
                        help="Add observation-only temporal pixel-change magnitudes")
    parser.add_argument("--active-gas-weight", type=float, default=ACTIVE_GAS_WEIGHT)
    parser.add_argument("--active-brake-weight", type=float, default=1)
    parser.add_argument("--recovery-steering-only", action="store_true",
                        help="On student states, fit only steering; keep normal-road gas/brake training")
    parser.add_argument("--recovery-controls-only", action="store_true",
                        help="On student states, fit only gas/brake; keep normal-road steering training")
    parser.add_argument("--recovery-fraction", type=float, default=.25,
                        help="Fraction of per-epoch sampling budget for student-visited states")
    parser.add_argument("--max-train-samples", type=int, default=20000,
                        help="Maximum samples per epoch, distributed across training roads")
    return train(parser.parse_args(argv))


if __name__ == "__main__":
    main()
