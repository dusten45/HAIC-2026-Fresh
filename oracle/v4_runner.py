"""Measure oracle-v4 full episodes in the unchanged official environment."""

import argparse
import os
from pathlib import Path
import statistics

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from gymnasium.wrappers.time_limit import TimeLimit

from core.vendor.car_racing import CarRacing
from env_wrapper import CarEnvironment
from .recording import encode, provenance, snapshot_sources, vehicle_state
from .v4_controller import V4Controller


ROADS = ((1, 516237), (2, 644062), (3, 1007))


def run(output, track_id, seed, stage, repeat):
    name = f"track{track_id}_seed{seed}_repeat{repeat}"
    base = CarRacing(continuous=True, render_mode="rgb_array")
    env = CarEnvironment(TimeLimit(base, max_episode_steps=8200), skip_frames=4,
                         no_operation=50)
    try:
        env.reset(seed=seed, options={"track_id": track_id})
        assert base.track_variables is not None
        start = base.t
        controller = V4Controller(base, stage=stage)
        metadata = {
            "track_id": track_id, "geometry_seed": seed, "stage": stage,
            "repeat": repeat, "track_points": base.track,
            "obstacles": base.track_variables.obstacles,
            "reference_points": controller.path.points,
            "config": controller.config, "speed_arcs": controller.arcs,
            "speed_limits": controller.speed_limits,
            "speed_profile": controller.speed_profile,
            "reference_curvature": controller.curvature,
            "start_t": start, "frame_skip": 4, "warmup": 50,
            "raw_frame_budget": 8200, "max_steps": 2000,
            "timeout_seconds": None, "stack_frames": env._stack_frames,
            "max_off_track_steps": env.max_off_track_steps,
            "lap_complete_percent": base.lap_complete_percent,
            "domain_randomize": False, "physical_obstacles": True}
        for field in ("launch_arcs", "launch_profile", "profile_acceleration"):
            if hasattr(controller, field):
                metadata[field] = getattr(controller, field)
        (output / f"{name}.metadata.json").write_text(encode(metadata) + "\n")
        collisions = 0
        first_collision = None
        max_speed = 0.0
        info = {}
        done = False
        step = 0
        terminated = truncated = False
        with (output / f"{name}.jsonl").open("x") as trace:
            for step in range(1, 2001):
                pre = vehicle_state(base)
                action, diagnostic = controller.act()
                _, reward, terminated, truncated, info = env.step(action)
                post = vehicle_state(base)
                trace.write(encode({"step": step, "pre_state": pre, "post_state": post,
                                    "action": action, "diagnostics": diagnostic,
                                    "reward": reward, "info": info,
                                    "terminated": terminated, "truncated": truncated}) + "\n")
                collisions += bool(info.get("collision"))
                if info.get("collision") and first_collision is None:
                    first_collision = step
                max_speed = max(max_speed, post["speed"])
                if terminated or truncated:
                    done = True
                    break
        summary = {"episode": name, "track_id": track_id, "geometry_seed": seed,
                   "repeat": repeat, "stage": stage,
                   "finished": base.finish_time_s is not None,
                   "lap_time_ms": round((base.finish_time_s - start) * 1000)
                   if base.finish_time_s is not None else None,
                   "steps": step, "damage": env.damage.damage, "collisions": collisions,
                   "terminated": terminated, "truncated": truncated,
                   "elapsed_simulation_s": base.t - start,
                   "first_collision": first_collision, "progress": env._calculate_progress(),
                   "reason": "finished" if base.finish_time_s is not None else
                   info.get("retire_reason") or ("environment_done" if done else "runner_max_steps"),
                   "max_speed": max_speed}
        (output / f"{name}.summary.json").write_text(encode(summary) + "\n")
        print(f"{name}: {summary['finished']} lap={summary['lap_time_ms']} "
              f"damage={summary['damage']} steps={step} reason={summary['reason']}", flush=True)
        return summary
    finally:
        env.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=V4Controller.STAGES, default="midpoint")
    parser.add_argument("--road", type=int, nargs=2, action="append", metavar=("TRACK", "SEED"),
                        help="paired track/seed; defaults to the three designated roads")
    parser.add_argument("--repeats", type=int, choices=range(1, 4), default=1)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if not args.output.parent.is_dir() or args.output.exists():
        parser.error("output must be new and parent must exist")
    args.output.mkdir()
    metadata = provenance(args, sources=("oracle/v4_controller.py", "oracle/v4_runner.py",
                                        "oracle/v3_controller.py", "oracle/v2_controller.py"))
    (args.output / "metadata.json").write_text(encode(metadata) + "\n")
    snapshot_sources(args.output, metadata)
    roads = args.road if args.road is not None else ROADS
    results = [run(args.output, t, s, args.stage, repeat)
               for repeat in range(1, args.repeats + 1) for t, s in roads]
    laps = [e["lap_time_ms"] for e in results if e["finished"]]
    aggregate = {"episodes": len(results), "roads": len({(e["track_id"], e["geometry_seed"])
                                                      for e in results}),
                 "finishes": len(laps), "damaged": sum(e["damage"] > 0 for e in results),
                 "collisions": sum(e["collisions"] for e in results),
                 "mean_lap_ms": statistics.mean(laps) if laps else None,
                 "median_lap_ms": statistics.median(laps) if laps else None,
                 "best_lap_ms": min(laps, default=None), "results": results}
    (args.output / "summary.json").write_text(encode(aggregate) + "\n")
    print({k: v for k, v in aggregate.items() if k != "results"}, flush=True)


if __name__ == "__main__":
    main()
