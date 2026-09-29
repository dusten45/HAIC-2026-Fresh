"""Summarize saved local oracle episodes and inspect the first adverse events."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def report(directories, events=False):
    if len({p.resolve() for p in directories}) != len(directories):
        raise ValueError("Duplicate run directories would double-count episodes")
    episodes = []
    fingerprints, missing_provenance = set(), 0
    for directory in directories:
        paths = sorted(directory.glob("*.summary.json"))
        completed = {p.name.removesuffix(".summary.json") for p in paths}
        interrupted = {p.stem for p in directory.glob("*.jsonl")} - completed
        provenance = json.loads((directory / "metadata.json").read_text())
        planned = provenance["args"]
        if "source_sha256" in provenance:
            control = {key: planned.get(key) for key in (
                "mode", "target_speed", "avoid_obstacles", "frame_skip", "warmup",
                "max_steps", "action_seed", "manual_steering", "timeout_seconds")}
            fingerprints.add(hashlib.sha256(json.dumps({
                "sources": provenance["source_sha256"], "control": control,
                "python": provenance.get("python"), "packages": provenance.get("packages"),
            }, sort_keys=True).encode()).hexdigest())
        else:
            missing_provenance += 1
        expected = {f"track{t}_seed{s}_repeat{r}" for t in planned["track_ids"]
                    for s in planned["seeds"] for r in range(1, planned["repeats"] + 1)}
        if (completed | interrupted) - expected:
            raise ValueError(f"Unexpected episode artifacts in {directory}")
        missing = expected - completed
        print(f"{directory}: {len(paths)}/{len(expected)} planned episodes have summaries; "
              f"{len(interrupted)} incomplete traces excluded; "
              f"{len(missing - interrupted)} unstarted/missing episodes")
        episodes.extend((json.loads(path.read_text()), directory) for path in paths)
    summaries = [s for s, _ in episodes]
    if not summaries:
        raise ValueError("No episode summaries in requested directories")
    print(f"Execution fingerprints (sources/settings/packages): {len(fingerprints)}; "
          f"directories missing source provenance: {missing_provenance}")
    if len(fingerprints) != 1 or missing_provenance:
        print("WARNING: this aggregate does not establish one frozen execution configuration")
    roads = {(s["track_id"], s["geometry_seed"]) for s in summaries}
    good_roads = {road for road in roads if all(
        s["finished"] for s in summaries
        if (s["track_id"], s["geometry_seed"]) == road
    )}
    print(f"Total: finishes {sum(s['finished'] for s in summaries)}/{len(summaries)} episodes; "
          f"every observed episode finished on {len(good_roads)}/{len(roads)} observed roads")
    print("episode finish steps progress damage max_error first_collision first_departure lap_ms")
    repeat_hashes = {}
    conditions, geometries = {}, set()
    speeds, steering, path_errors = [], [], []
    saturated_steps = collision_steps = 0
    for summary, directory in episodes:
        episode = summary["episode"]
        trace_path = directory / f"{episode}.jsonl"
        trace = [json.loads(line) for line in trace_path.read_text().splitlines()]
        metadata = json.loads((directory / f"{episode}.metadata.json").read_text())
        first_collision = summary["first_collision"]
        first_departure = summary["first_road_departure"]
        lap_ms = (round((summary["finish_time_s"] - summary["start_t"]) * 1000)
                  if summary["finished"] else None)
        print(episode, int(summary["finished"]), summary["steps"],
              round(summary["progress"], 6), summary["damage"],
              round(summary["max_abs_center_error"], 3),
              first_collision["step"] if first_collision else None,
              first_departure["step"] if first_departure else None, lap_ms)
        # Trace records omit wall time; identical hashes test full-state/action/image repeatability.
        road = (summary["track_id"], summary["geometry_seed"])
        repeat_hashes.setdefault(road, []).append(hashlib.sha256(trace_path.read_bytes()).hexdigest())
        geometry = hashlib.sha256(json.dumps(metadata["track_points"]).encode()).hexdigest()
        obstacles = hashlib.sha256(json.dumps(metadata["obstacles"], sort_keys=True).encode()).hexdigest()
        geometries.add(geometry)
        conditions.setdefault(road, set()).add((geometry, obstacles))
        for record in trace[1:]:
            speeds.append(record["post_state"]["speed"])
            steering.append(abs(record["action"][0]))
            saturated_steps += abs(record["action"][0]) >= 0.4
            collision_steps += bool(record["info"]["collision"])
            if "path_error" in record["diagnostics"]:
                path_errors.append(abs(record["diagnostics"]["path_error"]))
        if events and not summary["finished"]:
            event_steps = {summary["steps"]}
            event_steps.update(e["step"] for e in (first_collision, first_departure) if e)
            for step in sorted(event_steps):
                print(f"  event window around step {step}; reason={summary['reason']}")
                for record in trace[max(1, step - 3): step + 2]:
                    state = record["post_state"]
                    nearest = min(float(np.linalg.norm(np.array(state["position"]) - o["position"]))
                                  for o in metadata["obstacles"])
                    print(json.dumps({"step": record["step"], "position": state["position"],
                        "waypoint": state["track"]["segment"],
                        "speed": round(state["speed"], 3),
                        "center_error": round(state["track"]["center_error"], 3),
                        "nearest_obstacle_center": round(nearest, 3),
                        "action": record["action"], "reward": record["reward"],
                        "collision": record["info"]["collision"],
                        "damage": record["info"]["damage"],
                        "progress": record["info"]["progress"]}))
    repeated = {r: hashes for r, hashes in repeat_hashes.items() if len(hashes) > 1}
    if repeated:
        print(f"Exact repeated trace hashes: {sum(len(set(h)) == 1 for h in repeated.values())}"
              f"/{len(repeated)} repeated roads")
    print(f"Unique base geometries: {len(geometries)}; matched geometry/obstacles: "
          f"{sum(len(values) == 1 for values in conditions.values())}/{len(conditions)} roads")
    if speeds:
        print(f"Sampled max speed={max(speeds):.6f}; max |command steer|={max(steering):.6f}; "
              f"steer >= physical .4 target: {saturated_steps}/{len(steering)} actions; "
              f"collision-positive actions: {collision_steps}")
    if path_errors:
        print(f"Maximum sampled |reference-path error|={max(path_errors):.6f}")
    print("Step range:", min(s["steps"] for s in summaries), max(s["steps"] for s in summaries))
    print("Lap ms range:", min((round((s["finish_time_s"] - s["start_t"]) * 1000)
                                   for s in summaries if s["finished"]), default=None),
          max((round((s["finish_time_s"] - s["start_t"]) * 1000)
               for s in summaries if s["finished"]), default=None))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", type=Path, nargs="+")
    parser.add_argument("--events", action="store_true")
    args = parser.parse_args()
    report(args.directories, args.events)
