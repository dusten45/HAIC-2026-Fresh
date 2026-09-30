"""Collect local oracle trajectories; privileged annotations are never model inputs."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from uuid import uuid4

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import numpy as np
from gymnasium.wrappers.time_limit import TimeLimit

from core.vendor.car_racing import CarRacing
from env_wrapper import CarEnvironment
from oracle.oracle_controller import OracleController
from oracle.recording import encode, execution_fingerprint, snapshot_sources, vehicle_state
from bc.contracts import BASELINE_CONDITIONS, EXPOSED_SEEDS, OBSERVATION_SHAPE, SPLIT_SEEDS, TRACK_IDS


def _write_json(path, value, mode="x"):
    with path.open(mode) as stream:
        stream.write(encode(value) + "\n")


def _provenance(args):
    root = Path(__file__).resolve().parent.parent
    fingerprint = execution_fingerprint(
        ("bc/dataset.py", "bc/contracts.py", "env_wrapper.py", "damage.py", "local_runner.py",
         "oracle/oracle_runner.py", "oracle/oracle_controller.py", "oracle/recording.py"))
    return {
        "schema_version": 1, "command": ["python", "-m", "bc.dataset", *sys.argv[1:]],
        "arguments": vars(args),
        "git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        **fingerprint, "platform": platform.platform(),
        "conditions": {**BASELINE_CONDITIONS,
                        "frame_skip": args.frame_skip, "warmup": args.warmup,
                        "target_speed": args.target_speed, "max_steps": args.max_steps,
                       "raw_frame_budget": args.max_steps * args.frame_skip + 200},
        "observation": "pre-action float32 (4,84,84), exact wrapper pixels in [0,1]",
        "model_inputs": ["observations"], "model_targets": ["actions"],
        "annotations": "Privileged states and environment info are analysis-only JSONL/episode sidecars",
    }


def _observation(value):
    array = np.asarray(value)
    if array.dtype != np.float32 or array.shape != OBSERVATION_SHAPE or not np.all(np.isfinite(array)):
        raise ValueError("Policy observation must be finite float32 (4,84,84)")
    if np.any(array < 0) or np.any(array > 1):
        raise ValueError("Policy observation must be in [0,1]")
    return array


def _analysis(state, progress, damage):
    return {"progress": float(progress), "speed": state["speed"],
            "position": state["position"], "heading": state["angle"],
            "heading_convention": "Box2D hull angle (forward = (-sin(angle), cos(angle)))",
            "damage": float(damage), "state": state}


def _seed_split(seed):
    return next(split for split, seeds in SPLIT_SEEDS.items() if seed in seeds)


def collect_episode(args, output, track_id, seed):
    """Write one attempted episode; only finished rollouts enter the learning split."""
    name = f"track{track_id}_seed{seed}"
    raw_path = output / f"{name}.partial.float32"
    npz_path = output / f"{name}.npz"
    base = CarRacing(continuous=True, render_mode=BASELINE_CONDITIONS["render_mode"],
                     domain_randomize=BASELINE_CONDITIONS["domain_randomize"])
    env = CarEnvironment(TimeLimit(base, max_episode_steps=args.max_steps * args.frame_skip + 200),
                         skip_frames=args.frame_skip, no_operation=args.warmup,
                         stack_frames=BASELINE_CONDITIONS["stack_frames"])
    try:
        observation, reset_info = env.reset(seed=seed, options={"track_id": track_id})
        controller = OracleController(base, target_speed=args.target_speed,
                                      avoid_obstacles=BASELINE_CONDITIONS["avoid_obstacles"])
        _write_json(output / f"{name}.episode.json", {
            "track_id": track_id, "geometry_seed": seed,
            "reset": {"seed": seed, "options": {"track_id": track_id}, "info": reset_info},
            "track_point_columns": ["alpha", "beta", "x", "y"],
            "track_points": base.track, "track_variables": base.track_variables,
            "start_t": base.t, "conditions": {"frame_skip": args.frame_skip,
                "warmup": args.warmup, "target_speed": args.target_speed,
                "avoid_obstacles": True, "domain_randomize": False,
                "max_steps": args.max_steps}})
        start_t = base.t
        steps = 0
        actions = []
        terminated = truncated = False
        info = reset_info
        state = vehicle_state(base)
        state["off_track_counter"] = env.off_track_counter
        with raw_path.open("xb") as pixels, (output / f"{name}.jsonl").open("x") as trace:
            while steps < args.max_steps:
                pre = _analysis(state, env._calculate_progress(), env.damage.damage)
                action, diagnostics = controller.act()
                action = np.asarray(action, dtype=np.float32)
                if action.shape != (3,) or not env.action_space.contains(action):
                    raise ValueError(f"Invalid oracle action: {action}")
                pixels.write(_observation(observation).tobytes(order="C"))
                actions.append(action)
                observation, reward, terminated, truncated, info = env.step(action)
                steps += 1
                state = vehicle_state(base)
                state["off_track_counter"] = env.off_track_counter
                trace.write(encode({"track_id": track_id, "geometry_seed": seed,
                                    "step": steps - 1, "pre": pre, "action": action,
                                    "oracle_diagnostics": diagnostics, "reward": reward,
                                    "post": _analysis(state, info["progress"], info["damage"]),
                                    "info": info, "finished": info["finished"],
                                    "terminated": terminated, "truncated": truncated}) + "\n")
                if terminated or truncated:
                    break
        finished = base.finish_time_s is not None
        reason = ("finished" if finished else info.get("retire_reason")
                  or ("environment_terminated" if terminated else
                      "environment_truncated" if truncated else "runner_max_steps"))
        # The raw stream is exactly the sequence of pre-action float32 observations.
        pixels_shape = (steps, *OBSERVATION_SHAPE)
        pixels = (np.memmap(raw_path, dtype=np.float32, mode="r", shape=pixels_shape)
                  if steps else np.empty(pixels_shape, dtype=np.float32))
        actions = np.asarray(actions, dtype=np.float32).reshape(steps, 3)
        with npz_path.open("xb") as stream:
            np.savez_compressed(stream, observations=pixels, actions=actions)
        del pixels
        raw_path.unlink()
        digest = hashlib.sha256()
        with npz_path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        finish_time = base.finish_time_s
        summary = {"track_id": track_id, "geometry_seed": seed, "split": _seed_split(seed),
                   "trajectory": npz_path.name, "analysis": f"{name}.jsonl",
                    "steps": steps, "attempt_finalized": True, "complete": bool(terminated or truncated),
                   "finished": finished, "finish_time_s": finish_time,
                   "lap_time_ms": round((finish_time - start_t) * 1000) if finish_time is not None else None,
                   "progress": env._calculate_progress(), "damage": env.damage.damage,
                   "terminated": terminated, "truncated": truncated, "reason": reason,
                   "start_t": start_t, "end_t": base.t,
                   "sha256": digest.hexdigest()}
        _write_json(output / f"{name}.summary.json", summary)
        print(f"{name}: finish={finished} steps={steps} reason={reason}", flush=True)
        return summary
    finally:
        env.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="New directory; existing only with --resume")
    parser.add_argument("--resume", action="store_true", help="Resume an existing compatible collection")
    parser.add_argument("--split", required=True, choices=tuple(SPLIT_SEEDS))
    parser.add_argument("--track-ids", type=int, nargs="+", default=list(TRACK_IDS))
    parser.add_argument("--seeds", type=int, nargs="+", required=True,
                        help="Bounded subset of the selected split's geometry seeds")
    parser.add_argument("--max-steps", type=int, default=BASELINE_CONDITIONS["max_steps"])
    parser.add_argument("--frame-skip", type=int, default=BASELINE_CONDITIONS["frame_skip"])
    parser.add_argument("--warmup", type=int, default=BASELINE_CONDITIONS["warmup"])
    parser.add_argument("--target-speed", type=float, default=BASELINE_CONDITIONS["target_speed"])
    args = parser.parse_args(argv)
    if (not args.track_ids or len(set(args.track_ids)) != len(args.track_ids)
            or any(track not in TRACK_IDS for track in args.track_ids)):
        parser.error("track-ids must be unique values from 1..5")
    if (not args.seeds or len(set(args.seeds)) != len(args.seeds)
            or any(seed not in SPLIT_SEEDS[args.split] for seed in args.seeds)):
        parser.error("seeds must be unique and belong to the selected split (never exposed 1..10)")
    if (args.max_steps < 1 or args.max_steps > BASELINE_CONDITIONS["max_steps"] or args.frame_skip < 1
            or args.warmup < 0 or not np.isfinite(args.target_speed) or args.target_speed <= 0):
        parser.error("max-steps must be 1..2000, frame-skip positive, warmup nonnegative, speed positive")
    if args.resume:
        if not args.output.is_dir():
            parser.error("resume output must be an existing collection directory")
        provenance_path = args.output / "provenance.json"
        try:
            original = json.loads(provenance_path.read_text())
        except (OSError, ValueError) as error:
            parser.error(f"cannot read resume provenance: {error}")
        provenance = _provenance(args)
        previous = original.get("arguments", {})
        if (previous.get("split") != args.split
                or set(previous.get("track_ids", [])) != set(args.track_ids)
                or set(previous.get("seeds", [])) != set(args.seeds)
                or original.get("conditions") != provenance["conditions"]):
            parser.error("resume requires the same grid and conditions as original provenance")
        frozen = lambda hashes: {name: digest for name, digest in hashes.items()
                                 if name != "bc/dataset.py"}
        old_hashes = frozen(original.get("source_sha256", {}))
        current_hashes = frozen(provenance["source_sha256"])
        added_helpers = {"bc/contracts.py", "oracle/recording.py"} - old_hashes.keys()
        if (not old_hashes or old_hashes != {name: digest for name, digest in current_hashes.items()
                                             if name not in added_helpers}):
            parser.error("resume requires unchanged frozen teacher and environment source hashes")
        provenance["original_provenance_sha256"] = hashlib.sha256(provenance_path.read_bytes()).hexdigest()
        provenance["collector_source_change"] = {
            "original": original["source_sha256"].get("bc/dataset.py"),
            "current": provenance["source_sha256"]["bc/dataset.py"]}
        if added_helpers:
            provenance["source_fingerprint_migration"] = {
                "verification": "Original frozen hashes verified; added helpers describe this resume only",
                "added_source_sha256": {name: current_hashes[name] for name in sorted(added_helpers)}}
        _write_json(args.output / f"resume_{uuid4().hex}.json", provenance)
    else:
        if not args.output.parent.is_dir() or args.output.exists():
            parser.error("output must not exist and its parent directory must already exist")
        args.output.mkdir()
        provenance = _provenance(args)
        provenance["source_snapshot"] = snapshot_sources(args.output, provenance)
        _write_json(args.output / "provenance.json", provenance)
    for track in args.track_ids:
        for seed in args.seeds:
            name = f"track{track}_seed{seed}"
            summary_path = args.output / f"{name}.summary.json"
            if args.resume:
                try:
                    summary = json.loads(summary_path.read_text())
                except (OSError, ValueError):
                    summary = {}
                # Old collectors wrote a summary only after finalizing the NPZ, including caps.
                finalized = summary.get("attempt_finalized", bool(summary.get("trajectory")))
                if finalized and (args.output / f"{name}.npz").is_file():
                    continue
                artifacts = [args.output / f"{name}{suffix}" for suffix in
                             (".episode.json", ".jsonl", ".partial.float32", ".npz", ".summary.json")]
                artifacts = [path for path in artifacts if path.exists()]
                if artifacts:
                    archive = args.output / "interrupted_attempts" / uuid4().hex
                    archive.mkdir(parents=True)
                    for path in artifacts:
                        path.rename(archive / path.name)
            collect_episode(args, args.output, track, seed)
    # Read the full grid, including roads completed before this invocation.
    episodes = [json.loads((args.output / f"track{track}_seed{seed}.summary.json").read_text())
                for track in args.track_ids for seed in args.seeds]
    manifest = {"schema_version": 1, "split_seeds": SPLIT_SEEDS,
                "exposed_seeds_excluded": EXPOSED_SEEDS, "track_ids": list(TRACK_IDS),
                "selected_split": args.split, "selected_track_ids": args.track_ids,
                "selected_seeds": args.seeds, "train": [], "val": [], "test": [],
                "eligibility": "Only completed, finished episodes; no repeats or privileged model inputs"}
    for episode in episodes:
        if episode["complete"] and episode["finished"]:
            manifest[_seed_split(episode["geometry_seed"])].append(episode["trajectory"])
    _write_json(args.output / "split_manifest.json", manifest, mode="w" if args.resume else "x")
    _write_json(args.output / "manifest.json", {"episodes": episodes,
                "episode_count": len(episodes), "finished_count": sum(e["finished"] for e in episodes),
                "eligible_count": sum(len(manifest[split]) for split in SPLIT_SEEDS),
                "road_count": len(episodes)}, mode="w" if args.resume else "x")


if __name__ == "__main__":
    main()
