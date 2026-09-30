"""No-training train/validation conditional and startup prediction diagnosis."""

import argparse
import hashlib
import json
from pathlib import Path

import torch

from bc.model import BCPolicy
from bc.train import evaluate, road_paths
from oracle.recording import execution_fingerprint, snapshot_sources


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, nargs="+", required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--extra-train-dataset", type=Path)
    parser.add_argument("--val-dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    args = parser.parse_args(argv)
    if args.batch_size < 1:
        parser.error("batch-size must be positive")
    torch.set_num_threads(2)
    manifests = {}
    hashes = {}
    for label, directory in (("train", args.dataset), ("val", args.val_dataset),
                             ("extra_train", args.extra_train_dataset)):
        if directory is not None:
            path = directory / "split_manifest.json"
            manifests[label] = json.loads(path.read_text())
            hashes[label] = hashlib.sha256(path.read_bytes()).hexdigest()
    paths = road_paths(args.dataset, manifests["train"], args.val_dataset, manifests["val"],
                       args.extra_train_dataset, manifests.get("extra_train"))
    args.output.mkdir(exist_ok=False)
    fingerprint = execution_fingerprint(("bc/diagnose.py", "bc/train.py", "bc/model.py", "bc/contracts.py"))
    snapshot = snapshot_sources(args.output, fingerprint)
    result = {"kind": "bc_offline_diagnosis", **fingerprint, "source_snapshot": snapshot,
              "device": args.device, "manifest_sha256": hashes,
              "roads": {split: [str(path) for path in roads] for split, roads in paths.items()},
              "models": []}
    for checkpoint in args.checkpoint:
        model = BCPolicy.from_checkpoint(checkpoint).to(args.device)
        record = {"checkpoint": str(checkpoint),
                  "checkpoint_sha256": hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
                  "history_frames": model.history_frames}
        for split in ("train", "val"):
            record[split] = evaluate(model, paths[split], args.batch_size, include_startup=True)
        result["models"].append(record)
        (args.output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(record), flush=True)
    return result


if __name__ == "__main__":
    main()
