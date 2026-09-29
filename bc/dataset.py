"""Collect local oracle trajectories; privileged annotations are never model inputs."""

import argparse
import hashlib
import importlib.metadata
import os
from pathlib import Path
import platform
import subprocess
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import numpy as np
from gymnasium.wrappers.time_limit import TimeLimit

from core.vendor.car_racing import CarRacing
from env_wrapper import CarEnvironment
from oracle.oracle_controller import OracleController
from oracle.oracle_runner import encode, vehicle_state


SPLIT_SEEDS = {"train": list(range(11, 31)), "val": list(range(31, 36)),
               "test": list(range(36, 41))}
EXPOSED_SEEDS = list(range(1, 11))
TRACK_IDS = (1, 2, 3, 4, 5)
OBSERVATION_SHAPE = (4, 84, 84)


def _write_json(path, value):
    with path.open("x") as stream:
        stream.write(encode(value) + "\n")


def _provenance(args):
    root = Path(__file__).resolve().parent.parent
    sources = [root / name for name in
               ("bc/dataset.py", "env_wrapper.py", "damage.py", "local_runner.py",
                "oracle/oracle_runner.py", "oracle/oracle_controller.py")]
    sources += sorted((root / "core").rglob("*.py"))
    return {
        "schema_version": 1, "command": ["python", "-m", "bc.dataset", *sys.argv[1:]],
        "arguments": vars(args),
        "git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "source_sha256": {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in sources},
        "packages": {name: importlib.metadata.version(name)
                     for name in ("numpy", "gymnasium", "opencv-python", "box2d-py")},
        "python": sys.version, "platform": platform.platform(),
        "conditions": {"render_mode": "rgb_array", "domain_randomize": False,
                       "frame_skip": args.frame_skip, "warmup": args.warmup,
                       "stack_frames": 4, "target_speed": args.target_speed,
                       "avoid_obstacles": True, "max_steps": args.max_steps,
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
    base = CarRacing(continuous=True, render_mode="rgb_array", domain_randomize=False)
    env = CarEnvironment(TimeLimit(base, max_episode_steps=args.max_steps * args.frame_skip + 200),
                         skip_frames=args.frame_skip, no_operation=args.warmup)
    try:
        observation, reset_info = env.reset(seed=seed, options={"track_id": track_id})
        controller = OracleController(base, target_speed=args.target_speed, avoid_obstacles=True)
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
                   "steps": steps, "complete": bool(terminated or truncated),
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
    parser.add_argument("--output", required=True, type=Path, help="New directory; parent must exist")
    parser.add_argument("--split", required=True, choices=tuple(SPLIT_SEEDS))
    parser.add_argument("--track-ids", type=int, nargs="+", default=list(TRACK_IDS))
    parser.add_argument("--seeds", type=int, nargs="+", required=True,
                        help="Bounded subset of the selected split's geometry seeds")
    parser.add_argument("--max-steps", type=int, default=2000)
    parser.add_argument("--frame-skip", type=int, default=4)
    parser.add_argument("--warmup", type=int, default=50)
    parser.add_argument("--target-speed", type=float, default=12.0)
    args = parser.parse_args(argv)
    if (not args.track_ids or len(set(args.track_ids)) != len(args.track_ids)
            or any(track not in TRACK_IDS for track in args.track_ids)):
        parser.error("track-ids must be unique values from 1..5")
    if (not args.seeds or len(set(args.seeds)) != len(args.seeds)
            or any(seed not in SPLIT_SEEDS[args.split] for seed in args.seeds)):
        parser.error("seeds must be unique and belong to the selected split (never exposed 1..10)")
    if (args.max_steps < 1 or args.max_steps > 2000 or args.frame_skip < 1
            or args.warmup < 0 or not np.isfinite(args.target_speed) or args.target_speed <= 0):
        parser.error("max-steps must be 1..2000, frame-skip positive, warmup nonnegative, speed positive")
    if not args.output.parent.is_dir() or args.output.exists():
        parser.error("output must not exist and its parent directory must already exist")
    args.output.mkdir()
    _write_json(args.output / "provenance.json", _provenance(args))
    episodes = [collect_episode(args, args.output, track, seed)
                for track in args.track_ids for seed in args.seeds]
    manifest = {"schema_version": 1, "split_seeds": SPLIT_SEEDS,
                "exposed_seeds_excluded": EXPOSED_SEEDS, "track_ids": list(TRACK_IDS),
                "selected_split": args.split, "selected_track_ids": args.track_ids,
                "selected_seeds": args.seeds, "train": [], "val": [], "test": [],
                "eligibility": "Only completed, finished episodes; no repeats or privileged model inputs"}
    for episode in episodes:
        if episode["complete"] and episode["finished"]:
            manifest[_seed_split(episode["geometry_seed"])].append(episode["trajectory"])
    _write_json(args.output / "split_manifest.json", manifest)
    _write_json(args.output / "manifest.json", {"episodes": episodes,
                "episode_count": len(episodes), "finished_count": sum(e["finished"] for e in episodes),
                "eligible_count": sum(len(manifest[split]) for split in SPLIT_SEEDS),
                "road_count": len(episodes)})


if __name__ == "__main__":
    main()
