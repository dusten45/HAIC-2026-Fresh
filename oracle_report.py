"""Summarize saved oracle episodes and inspect the first adverse events."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def report(directory, events=False):
    summaries = [json.loads(path.read_text())
                 for path in sorted(directory.glob("*.summary.json"))]
    if not summaries:
        raise ValueError(f"No complete episode summaries in {directory}")
    roads = {(s["track_id"], s["geometry_seed"]) for s in summaries}
    good_roads = {road for road in roads if all(
        s["finished"] for s in summaries
        if (s["track_id"], s["geometry_seed"]) == road
    )}
    print(f"{directory}: finishes {sum(s['finished'] for s in summaries)}/{len(summaries)} episodes; "
          f"all-repeat finishes {len(good_roads)}/{len(roads)} roads")
    print("episode finish steps progress damage max_error first_collision first_departure lap_ms")
    repeat_hashes = {}
    for summary in summaries:
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
    print("Step range:", min(s["steps"] for s in summaries), max(s["steps"] for s in summaries))
    print("Lap ms range:", min((round((s["finish_time_s"] - s["start_t"]) * 1000)
                                   for s in summaries if s["finished"]), default=None),
          max((round((s["finish_time_s"] - s["start_t"]) * 1000)
               for s in summaries if s["finished"]), default=None))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--events", action="store_true")
    args = parser.parse_args()
    report(args.directory, args.events)
