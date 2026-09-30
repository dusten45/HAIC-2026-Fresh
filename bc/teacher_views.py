"""Derive equal-budget v1/v2/mixed four-frame BC views from paired raw collections.

No environment or policy is executed. Explicit roads must succeed in both teachers.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from bc.contracts import (SPLIT_SEEDS, TRACK_IDS, environment_conditions,
                          verify_environment_conditions)
from bc.train import read_road
from oracle.recording import encode, execution_fingerprint, snapshot_sources


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def derive_views(args):
    if args.rows_per_road < 2 or args.rows_per_road % 2:
        raise ValueError("rows-per-road must be positive and even")
    if (not args.track_ids or len(set(args.track_ids)) != len(args.track_ids)
            or any(track not in TRACK_IDS for track in args.track_ids)
            or not args.seeds or len(set(args.seeds)) != len(args.seeds)
            or any(seed not in SPLIT_SEEDS[args.split] for seed in args.seeds)):
        raise ValueError("Explicit unique track IDs and seeds must belong to the selected train/val split")
    if args.output.exists() or not args.output.parent.is_dir():
        raise ValueError("output must be new and its parent must exist")
    names = [f"track{track}_seed{seed}.npz"
             for track in sorted(args.track_ids) for seed in sorted(args.seeds)]
    sources = {teacher: {} for teacher in ("v1", "v2")}
    episodes = {teacher: {} for teacher in ("v1", "v2")}
    conditions = None
    execution = None
    for teacher, directories in (("v1", args.v1_dataset), ("v2", args.v2_dataset)):
        teacher_config = None
        for directory in directories:
            provenance_path = directory / "provenance.json"
            provenance = json.loads(provenance_path.read_text())
            actual = verify_environment_conditions(provenance, teacher)
            if conditions is not None and conditions != actual:
                raise ValueError("Paired teacher environment conditions differ")
            conditions = actual
            environment_sources = {name: digest for name, digest in provenance.get("source_sha256", {}).items()
                                   if name.startswith("core/") or name in ("env_wrapper.py", "damage.py")}
            if (not {"env_wrapper.py", "damage.py"} <= environment_sources.keys()
                    or not any(name.startswith("core/") for name in environment_sources)):
                raise ValueError(f"Missing environment source fingerprints in {directory}")
            runtime = {"source_sha256": environment_sources,
                       **{key: provenance[key] for key in ("python", "platform")},
                       "packages": {name: provenance["packages"][name] for name in
                                    ("numpy", "gymnasium", "opencv-python", "box2d-py")}}
            if execution is not None and runtime != execution:
                raise ValueError("Paired teacher simulator sources or runtime fingerprints differ")
            execution = runtime
            teacher_metadata = provenance.get("teacher", {"name": "v1", "config": {
                key: provenance.get("conditions", {}).get(key)
                for key in ("target_speed", "avoid_obstacles")}})
            if teacher_metadata.get("name") != teacher or provenance.get("kind") == "matched_teacher_view":
                raise ValueError(f"Expected raw {teacher} collector provenance in {directory}")
            if teacher_config is not None and teacher_metadata != teacher_config:
                raise ValueError(f"Inconsistent {teacher} configurations across source directories")
            teacher_config = teacher_metadata
            manifest_path = directory / "split_manifest.json"
            manifest = json.loads(manifest_path.read_text())
            eligible = manifest.get(args.split, [])
            declared = {f"track{track}_seed{seed}.npz"
                        for track in manifest.get("selected_track_ids", [])
                        for seed in manifest.get("selected_seeds", [])}
            for name in names:
                if name not in eligible and name not in declared:
                    continue
                if name in sources[teacher]:
                    raise ValueError(f"Duplicate {teacher} source for {name}")
                summary = json.loads((directory / name.replace(".npz", ".summary.json")).read_text())
                if summary.get("teacher", teacher_metadata) != teacher_metadata:
                    raise ValueError(f"Summary teacher differs from source provenance: {teacher}/{name}")
                if not summary.get("finished") or not summary.get("complete") or name not in eligible:
                    raise ValueError(f"Failed or ineligible shared road: {teacher}/{name}")
                if summary.get("steps", 0) < args.rows_per_road:
                    raise ValueError(f"Too few samples: {teacher}/{name}")
                if not (directory / name).is_file():
                    raise ValueError(f"Missing shared road: {teacher}/{name}")
                episode_path = directory / name.replace(".npz", ".episode.json")
                episode = json.loads(episode_path.read_text())
                episodes[teacher][name] = {
                    **{key: episode[key] for key in
                       ("track_id", "geometry_seed", "track_points", "track_variables", "start_t", "reset")},
                    "conditions": environment_conditions(episode["conditions"])}
                sources[teacher][name] = {
                    "path": str((directory / name).resolve()), "teacher": teacher_metadata,
                    "provenance_sha256": _sha256(provenance_path),
                    "split_manifest_sha256": _sha256(manifest_path),
                    "summary_sha256": _sha256(directory / name.replace(".npz", ".summary.json")),
                    "episode_sha256": _sha256(episode_path),
                    "raw_rows": summary["steps"],
                }
        missing = set(names) - sources[teacher].keys()
        if missing:
            raise ValueError(f"Missing shared {teacher} roads: {sorted(missing)}")

    for name in names:
        if episodes["v1"][name] != episodes["v2"][name]:
            raise ValueError(f"Paired teacher episode geometry, reset or conditions differ: {name}")

    args.output.mkdir()
    for arm in ("v1", "v2", "mixed"):
        (args.output / arm).mkdir()
    rng = np.random.default_rng(args.seed)
    half = args.rows_per_road // 2
    for name in names:
        selected = {}
        for teacher in ("v1", "v2"):
            source = sources[teacher][name]
            path = Path(source["path"])
            observations, actions = read_road(path)
            if len(actions) != source["raw_rows"] or len(actions) < args.rows_per_road:
                raise ValueError(f"Too few samples or summary row mismatch: {teacher}/{name}")
            source["sha256"] = _sha256(path)
            indices = rng.choice(len(actions), args.rows_per_road, replace=False)
            # Copy whole official stacks; never reconstruct history after row sampling.
            selected[teacher] = (observations[indices], actions[indices], indices)
            del observations, actions
            x, y, rows = selected[teacher]
            np.savez_compressed(args.output / teacher / name, observations=x, actions=y,
                                source_rows=rows.astype(np.int64),
                                source_teachers=np.full(args.rows_per_road, teacher, dtype="U2"))
        x = np.stack([selected[t][0][:half] for t in ("v1", "v2")], axis=1)
        y = np.stack([selected[t][1][:half] for t in ("v1", "v2")], axis=1)
        rows = np.stack([selected[t][2][:half] for t in ("v1", "v2")], axis=1)
        np.savez_compressed(args.output / "mixed" / name,
                            observations=x.reshape(args.rows_per_road, *x.shape[2:]),
                            actions=y.reshape(args.rows_per_road, 3),
                            source_rows=rows.reshape(-1).astype(np.int64),
                            source_teachers=np.tile(np.array(["v1", "v2"], dtype="U2"), half))

    fingerprint = execution_fingerprint(("bc/teacher_views.py", "bc/contracts.py", "bc/train.py"))
    for arm in ("v1", "v2", "mixed"):
        directory = args.output / arm
        used_teachers = ("v1", "v2") if arm == "mixed" else (arm,)
        provenance = {
            "schema_version": 1, "kind": "matched_teacher_view", "arm": arm,
            "arguments": vars(args), "conditions": conditions, "seed": args.seed,
            "matched_collection_execution": execution,
            "rows_per_road": args.rows_per_road,
            "teacher_rows_per_road": {t: half if arm == "mixed" else args.rows_per_road
                                      for t in used_teachers},
            "sources": {t: sources[t] for t in used_teachers},
            "model_inputs": ["observations"], "model_targets": ["actions"],
            "row_provenance": "source_teachers + road filename resolve sources; source_rows are zero-based raw pre-action rows",
            "observation": "Unaltered float32 (N,4,84,84) official temporal stacks; sampled rows are not chronological",
            **fingerprint,
        }
        provenance["source_snapshot"] = snapshot_sources(directory, fingerprint)
        (directory / "provenance.json").write_text(encode(provenance) + "\n")
        manifest = {"schema_version": 1, "selected_split": args.split,
                    "selected_track_ids": sorted(args.track_ids), "selected_seeds": sorted(args.seeds),
                    **{split: names if split == args.split else [] for split in SPLIT_SEEDS}}
        (directory / "split_manifest.json").write_text(encode(manifest) + "\n")
    return args.output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v1-dataset", type=Path, nargs="+", required=True)
    parser.add_argument("--v2-dataset", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True, help="New root containing v1/v2/mixed dirs")
    parser.add_argument("--split", choices=("train", "val"), default="train")
    parser.add_argument("--track-ids", type=int, nargs="+", default=list(TRACK_IDS))
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--rows-per-road", type=int, default=256)
    parser.add_argument("--seed", type=int, default=0)
    return derive_views(parser.parse_args(argv))


if __name__ == "__main__":
    main()
