"""External, privileged Phase 1/2 diagnostics; not a submission agent."""

import argparse
import dataclasses
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import numpy as np
from gymnasium.wrappers.time_limit import TimeLimit

from core.vendor.car_racing import CarRacing, FPS, TRACK_WIDTH
from env_wrapper import CarEnvironment


def json_default(value):
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.asdict(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def encode(value):
    return json.dumps(value, default=json_default, allow_nan=False, sort_keys=True)


def observation_summary(observation):
    array = np.asarray(observation)
    return {"shape": list(array.shape), "dtype": str(array.dtype),
            "min": float(array.min()), "max": float(array.max()),
            "sha256": hashlib.sha256(array.tobytes(order="C")).hexdigest()}


def vehicle_state(base):
    hull = base.car.hull
    position = np.asarray(hull.position, dtype=float)
    points = np.asarray(base.track, dtype=float)[:, 2:4]
    segments = np.roll(points, -1, axis=0) - points
    lengths2 = np.sum(segments * segments, axis=1)
    fractions = np.clip(np.sum((position - points) * segments, axis=1)
                        / np.maximum(lengths2, 1e-12), 0, 1)
    projections = points + fractions[:, None] * segments
    distances = np.linalg.norm(position - projections, axis=1)
    index = int(np.argmin(distances))
    tangent = segments[index] / max(float(np.sqrt(lengths2[index])), 1e-12)
    left = np.array([-tangent[1], tangent[0]])
    velocity = np.asarray(hull.linearVelocity, dtype=float)
    forward = np.array([-np.sin(hull.angle), np.cos(hull.angle)])
    return {"position": position, "angle": float(hull.angle), "velocity": velocity,
            "speed": float(np.linalg.norm(velocity)),
            "forward_velocity": float(np.dot(velocity, forward)),
            "right_velocity": float(np.dot(velocity, [forward[1], -forward[0]])),
            "wheels_on_road": sum(bool(w.tiles) for w in base.car.wheels),
            "tile_visited_count": base.tile_visited_count,
            "angularVelocity": float(hull.angularVelocity),
            "front_steering": [float(w.joint.angle) for w in base.car.wheels[:2]],
            "t": float(base.t), "raw_frame": round(base.t * FPS),
            "track": {"segment": index, "fraction": float(fractions[index]),
                      "projection": projections[index], "tangent": tangent,
                      "center_error": float(np.dot(position - projections[index], left)),
                      "center_distance": float(distances[index]), "road_halfwidth": TRACK_WIDTH}}


def provenance(args):
    root = Path(__file__).resolve().parent
    def git(*command):
        return subprocess.check_output(["git", *command], cwd=root, text=True).strip()
    sources = [root / name for name in
               ("env_wrapper.py", "damage.py", "local_runner.py", "oracle_runner.py", "oracle_controller.py")]
    sources += sorted((root / "core").rglob("*.py"))
    status = git("status", "--porcelain", "--untracked-files=all")
    return {"args": vars(args), "command": sys.argv, "git_revision": git("rev-parse", "HEAD"),
            "git_dirty": bool(status), "git_status": status,
            "source_sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                              if p.exists() else None for p in sources},
            "python": sys.version, "platform": platform.platform(),
            "packages": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
            "sdl": {k: os.environ[k] for k in ("SDL_VIDEODRIVER", "SDL_AUDIODRIVER")},
            "render_mode": "rgb_array", "fps": FPS, "domain_randomize": False,
            "center_error_convention": "signed left of increasing track index",
            "event_resolution": "wrapper step boundaries; collision may occur anywhere within skipped frames",
            "random_actions": "NumPy default_rng(action_seed), restarted identically each episode",
            "limits": "runner max_steps/timeout do not set environment truncated",
            "road_designation": "exposed development/evaluation, not untouched holdout"}


def run_episode(args, output, track_id, seed, repeat):
    name = f"track{track_id}_seed{seed}_repeat{repeat}"
    raw_budget = args.max_steps * args.frame_skip + 200
    base = CarRacing(continuous=True, render_mode="rgb_array")
    env = CarEnvironment(TimeLimit(base, max_episode_steps=raw_budget),
                         skip_frames=args.frame_skip, no_operation=args.warmup)
    try:
        observation, info = env.reset(seed=seed, options={"track_id": track_id})
        assert base.track_variables is not None
        if not env.observation_space.contains(observation):
            raise ValueError("Reset observation does not match declared observation space")
        controller = None
        if args.mode == "oracle":
            from oracle_controller import OracleController
            controller = OracleController(base, target_speed=args.target_speed,
                                          avoid_obstacles=args.avoid_obstacles)
        rng = np.random.default_rng(args.action_seed)
        state = vehicle_state(base)
        state["off_track_counter"] = env.off_track_counter
        start_t, start_wall = base.t, time.monotonic()
        episode_metadata = {"track_id": track_id, "geometry_seed": seed, "repeat": repeat,
                            "reset": {"seed": seed, "options": {"track_id": track_id}},
                            "track_point_columns": ["alpha", "beta", "x", "y"],
                            "track_points": base.track, "track_variables": base.track_variables,
                            "obstacles": base.track_variables.obstacles,
                            "raw_frame_budget": raw_budget, "start_t": start_t,
                            "warmup": env.warmup_steps, "frame_skip": args.frame_skip,
                            "stack_frames": env._stack_frames,
                            "max_off_track_steps": env.max_off_track_steps,
                            "lap_complete_percent": base.lap_complete_percent}
        (output / f"{name}.metadata.json").write_text(encode(episode_metadata) + "\n")
        first_collision = first_departure = None
        max_error = abs(state["track"]["center_error"])
        total_reward, steps = 0.0, 0
        terminated = truncated = False
        runner_limit = None
        with (output / f"{name}.jsonl").open("x") as trace:
            trace.write(encode({"step": 0, "event": "reset", "state": state,
                                "observation": observation_summary(observation), "info": info}) + "\n")
            while steps < args.max_steps:
                if args.timeout_seconds is not None and time.monotonic() - start_wall >= args.timeout_seconds:
                    runner_limit = "runner_timeout"
                    break
                diagnostics = {}
                if controller is not None:
                    action, diagnostics = controller.act()
                elif args.mode == "random":
                    action = rng.uniform([-1, 0, 0], [1, 1, 1])
                else:
                    action = [args.manual_steering, 0.2, 0] if args.mode == "manual" else [0, 0, 0]
                action = np.asarray(action, dtype=np.float32)
                if action.shape != (3,) or not env.action_space.contains(action):
                    raise ValueError(f"Invalid action: {action}")
                pre_state = state
                observation, reward, terminated, truncated, info = env.step(action)
                steps += 1
                total_reward += float(reward)
                state = vehicle_state(base)
                state["off_track_counter"] = env.off_track_counter
                record = {"step": steps, "pre_state": pre_state, "diagnostics": diagnostics,
                          "action": action, "reward": reward, "post_state": state, "info": info,
                          "terminated": terminated, "truncated": truncated,
                          "observation": observation_summary(observation)}
                trace.write(encode(record) + "\n")
                if info.get("collision") and first_collision is None:
                    first_collision = {"step": steps, "pre_state": pre_state, "post_state": state}
                for event_step, candidate in ((steps - 1, pre_state), (steps, state)):
                    error = abs(candidate["track"]["center_error"])
                    max_error = max(max_error, error)
                    if error > TRACK_WIDTH and first_departure is None:
                        first_departure = {"step": event_step, "state": candidate}
                if terminated or truncated:
                    break
        finished = base.finish_time_s is not None
        if not (terminated or truncated) and steps >= args.max_steps:
            runner_limit = "runner_max_steps"
        reason = ("finished" if finished else runner_limit or info.get("retire_reason")
                  or ("environment_terminated" if terminated else "environment_truncated"))
        summary = {"episode": name, "track_id": track_id, "geometry_seed": seed, "repeat": repeat,
                   "finished": finished, "info_finished": info.get("finished"),
                   "finish_qualified": base.finish_qualified_time_s is not None,
                   "finish_time_s": base.finish_time_s, "progress": env._calculate_progress(),
                   "lap_time_ms": round((base.finish_time_s - start_t) * 1000) if base.finish_time_s is not None else None,
                   "damage": env.damage.damage, "steps": steps, "total_reward": total_reward,
                   "terminated": terminated, "truncated": truncated, "reason": reason,
                   "runner_limit": runner_limit, "max_steps": args.max_steps,
                   "timeout_seconds": args.timeout_seconds, "raw_frame_budget": raw_budget,
                   "start_t": start_t, "end_t": base.t, "elapsed_sim_s": base.t - start_t,
                   "elapsed_raw_frames": round((base.t - start_t) * FPS),
                   "wall_seconds": time.monotonic() - start_wall,
                   "first_collision": first_collision, "first_road_departure": first_departure,
                   "max_abs_center_error": max_error, "final_state": state}
        (output / f"{name}.summary.json").write_text(encode(summary) + "\n")
        print(f"{name}: finish={finished} progress={summary['progress']:.4f} "
              f"damage={summary['damage']:.2f} steps={steps} reason={reason}", flush=True)
        return summary
    finally:
        env.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("noop", "random", "manual", "oracle"), default="noop")
    parser.add_argument("--track-ids", type=int, nargs="+", default=[1, 2, 3, 4])
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=2000)
    parser.add_argument("--frame-skip", type=int, default=4)
    parser.add_argument("--warmup", type=int, default=50)
    parser.add_argument("--action-seed", type=int, default=0)
    parser.add_argument("--manual-steering", type=float, default=0.0)
    parser.add_argument("--target-speed", type=float, default=12.0)
    parser.add_argument("--avoid-obstacles", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, help="Cooperative per-episode wall limit, checked between actions")
    parser.add_argument("--output", type=Path, required=True, help="New directory, e.g. runs/noop; parent must exist")
    args = parser.parse_args(argv)
    if min(args.repeats, args.max_steps, args.frame_skip) < 1 or args.warmup < 0:
        parser.error("repeats, max-steps, frame-skip must be positive; warmup must be nonnegative")
    if not -1 <= args.manual_steering <= 1 or not np.isfinite(args.target_speed) or args.target_speed <= 0:
        parser.error("manual-steering must be in [-1,1]; target-speed must be finite and positive")
    if args.timeout_seconds is not None and (not np.isfinite(args.timeout_seconds) or args.timeout_seconds <= 0):
        parser.error("timeout-seconds must be finite and positive")
    if any(t not in (1, 2, 3, 4) for t in args.track_ids) or any(not 0 <= s <= 0xFFFFFFFF for s in args.seeds):
        parser.error("track-ids must be 1..4 and seeds 0..4294967295")
    if len(set(args.track_ids)) != len(args.track_ids) or len(set(args.seeds)) != len(args.seeds) or args.action_seed < 0:
        parser.error("track-ids/seeds must be unique; action-seed must be nonnegative")
    if not args.output.parent.is_dir() or args.output.exists():
        parser.error("output must not exist and its parent directory must already exist")
    args.output.mkdir()
    (args.output / "metadata.json").write_text(encode(provenance(args)) + "\n")
    episodes = []
    for track_id in args.track_ids:
        for seed in args.seeds:
            for repeat in range(1, args.repeats + 1):
                episodes.append(run_episode(args, args.output, track_id, seed, repeat))
    roads = {(e["track_id"], e["geometry_seed"]) for e in episodes}
    finished_roads = {(e["track_id"], e["geometry_seed"]) for e in episodes if e["finished"]}
    summary = {"episode_count": len(episodes), "finish_count": sum(e["finished"] for e in episodes),
               "road_count": len(roads), "roads_with_any_finish": len(finished_roads), "episodes": episodes}
    (args.output / "summary.json").write_text(encode(summary) + "\n")


if __name__ == "__main__":
    main()
