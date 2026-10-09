"""One motion-model-gated contrast; no gain or horizon sweep."""

import argparse
import json
from pathlib import Path
import time

import numpy as np

from retry.connectivity_probe import verify_reference, warm_agent
from retry.diagnose import Budget, onsets, trace
from retry.evaluate import check_window, digest, percentiles
from retry.finite_horizon_agent import FiniteHorizonAgent
from retry.motion_model import advance_front_angle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    plan, manifest = json.loads(args.plan.read_text()), json.loads(args.manifest.read_text())
    check_window(plan)
    assert digest(args.plan) == manifest["plan_sha256"]
    assert digest(Path("retry/finite_horizon_agent.py")) == manifest["candidate_sha256"]
    model_path = args.plan.parent / "motion-model/result.json"
    assert digest(model_path) == manifest["model_result_sha256"]
    model = json.loads(model_path.read_text())
    assert model["model_gate_pass"]
    freeze = verify_reference(plan, args.plan.parent)
    c = freeze["calibration"]
    gain, bias, gamma = c["coefficient_speed_per_intensity"], c["intercept"], model["yaw_coefficient"]
    output = args.plan.parent / "alternative"
    output.mkdir(exist_ok=False)
    sources = output / "sources"
    sources.mkdir()
    for p in Path(__file__).parent.glob("*.py"):
        (sources / p.name).write_bytes(p.read_bytes())
    (output / "metadata.json").write_text(json.dumps({"plan_sha256": digest(args.plan),
        "manifest_sha256": digest(args.manifest), "source_sha256": {p.name: digest(p) for p in sources.glob("*.py")},
        "runtime_privileged_input": False}, indent=2) + "\n")
    budget, records = Budget(args.plan, "alternative_branch"), []
    for task in manifest["tasks"]:
        source = (args.plan.parent / task["reference"]).resolve() if "reference" in task else None
        if source:
            assert digest(source / "trace.jsonl") == task["reference_trace_sha256"]
            saved = np.load(source / "pixels-actions.npz")
            historical_actions = saved["actions"][:task["prefix_actions"]]
        else:
            historical_actions = []
        class BoundModel(FiniteHorizonAgent):
            def __init__(self, g, b):
                super().__init__(g, b, gamma)
                self.latencies = []
            def reset(self, observation):
                super().reset(observation)
                for action in historical_actions:
                    self.front_angle, _ = advance_front_angle(self.front_angle, action[0])
            def act(self, observation):
                started = time.perf_counter()
                action = super().act(observation)
                self.latencies.append(time.perf_counter() - started)
                return action
        agent = warm_agent(BoundModel, gain, bias, saved["frames"], task["prefix_actions"]) if source else BoundModel(gain, bias)
        rows, summary = trace(plan["cases"][task["case_index"]], "finite_horizon_motion", budget,
            output / f"case-{task['case_index']}", max_steps=task["rollout_actions"], factory=lambda: agent,
            replay_source=source, prefix=task.get("prefix_actions", 0))
        record = {**summary, "DEV_index": task["case_index"], "onsets": onsets(rows),
            "act": percentiles(agent.latencies), "final_off_track_counter": rows[-1]["off_track_counter"]}
        if source:
            record["progress_gain"] = summary["progress"] - task["baseline_final_progress"]
            record["pass"] = record["progress_gain"] >= 0.08 and summary["damage"] <= 0.4 and record["final_off_track_counter"] < 10
        else:
            record["pass"] = summary["steps"] == 128 and summary["progress"] >= 0.15 and summary["damage"] <= 0.2
        record["pass"] &= record["act"]["p95_ms"] <= 100
        records.append(record)
        (output / "result.json").write_text(json.dumps(records, indent=2) + "\n")
    decision = {"passes": sum(r["pass"] for r in records), "cases": len(records),
        "pilot_gate_pass": all(r["pass"] for r in records), "deployment_eligible": False,
        "different_assumption": "short attainable motion arcs replace a global visible-grid goal and path follower"}
    (output / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision), flush=True)


if __name__ == "__main__":
    main()
