"""Gated local route-planner experiment; no private data enters participant code."""

import argparse
import json
from pathlib import Path
import time

import numpy as np

from retry.diagnose import Budget, onsets, trace
from retry.evaluate import check_window, digest, percentiles
from retry.route_agent import RouteAgent
from retry.temporal_agent import TemporalRouteAgent


class TimedRoute(RouteAgent):
    def __init__(self, gain, bias):
        super().__init__(gain, bias)
        self.latencies = []

    def act(self, observation):
        start = time.perf_counter()
        result = super().act(observation)
        self.latencies.append(time.perf_counter() - start)
        return result


class TimedTemporal(TemporalRouteAgent):
    def __init__(self, gain, bias):
        super().__init__(gain, bias)
        self.latencies = []

    def act(self, observation):
        start = time.perf_counter()
        result = super().act(observation)
        self.latencies.append(time.perf_counter() - start)
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--mode", choices=["branches", "startup"], required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    check_window(plan)
    root = Path(__file__).resolve().parents[1]
    for name, expected in plan["candidate_source_sha256"].items():
        assert digest(root / name) == expected
    output = args.plan.parent / args.mode
    output.mkdir(exist_ok=False)
    sources = output / "sources"
    sources.mkdir()
    for path in Path(__file__).parent.glob("*.py"):
        (sources / path.name).write_bytes(path.read_bytes())
    (output / "metadata.json").write_text(json.dumps({"plan_sha256": digest(args.plan),
        "source_sha256": {p.name: digest(p) for p in sources.glob("*.py")}, "privileged_input": False}, indent=2) + "\n")
    budget = Budget(args.plan, plan.get("budget_stage_prefix", "route") + f"_{args.mode}" + plan.get("budget_stage_suffix", ""))
    calibration = plan["pixel_speed_calibration"]
    tasks = plan["branch_tasks"] if args.mode == "branches" else plan["startup_tasks"]
    records = []
    for task in tasks:
        agent_class = TimedTemporal if plan["candidate"] == "TemporalRouteAgent_v1" else TimedRoute
        agent = agent_class(calibration["coefficient_speed_per_intensity"], calibration["intercept"])
        reference = None if args.mode == "startup" else (args.plan.parent / task["reference"]).resolve()
        if reference:
            assert digest(reference / "trace.jsonl") == task["reference_trace_sha256"]
        rows, summary = trace(plan["cases"][task["case_index"]], "safe_pixel_route", budget,
            output / f"case-{task['case_index']}", max_steps=task["rollout_actions"], factory=lambda: agent,
            replay_source=reference, prefix=task.get("prefix_actions", 0))
        record = {**summary, "DEV_index": task["case_index"], "onsets": onsets(rows),
            "act_latency": percentiles(agent.latencies), "final_off_track_counter": rows[-1]["off_track_counter"],
            "scope": "exact_shared_prefix_partial_rollout" if reference else "reset_partial_startup"}
        if reference:
            record["progress_gain"] = summary["progress"] - task["baseline_progress"]
            record["pass"] = record["progress_gain"] >= plan["branch_min_progress_gain"] and summary["damage"] <= plan["branch_max_damage"] and record["final_off_track_counter"] < 10
        else:
            record["pass"] = summary["steps"] == task["rollout_actions"] and summary["progress"] >= plan["startup_min_progress"] and summary["damage"] <= plan["startup_max_damage"]
        records.append(record)
        (output / "result.json").write_text(json.dumps(records, indent=2) + "\n")
    decision = {"cases": len(records), "passes": sum(r["pass"] for r in records),
        "gate_pass": len(records) == len(tasks) and all(r["pass"] for r in records),
        "deployment_eligible": False, "full_completion_claim": False}
    (output / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision), flush=True)


if __name__ == "__main__":
    main()
