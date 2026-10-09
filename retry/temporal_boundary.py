"""A preregistered remaining-DEV boundary for the unchanged temporal candidate."""

import argparse
import json
from pathlib import Path

import numpy as np

from retry.diagnose import Budget, onsets, trace
from retry.evaluate import check_window, digest, percentiles
from retry.route_probe import TimedTemporal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    check_window(plan)
    root = Path(__file__).resolve().parents[1]
    for name, expected in plan["candidate_source_sha256"].items():
        assert digest(root / name) == expected
    prerequisite = (args.plan.parent / plan["full_case_prerequisite"]).resolve()
    assert digest(prerequisite) == plan["full_case_prerequisite_sha256"]
    assert json.loads(prerequisite.read_text())["diagnostic_completion_criterion_pass"]
    output = args.plan.parent / "boundary"
    output.mkdir(exist_ok=False)
    sources = output / "sources"
    sources.mkdir()
    for path in Path(__file__).parent.glob("*.py"):
        (sources / path.name).write_bytes(path.read_bytes())
    (output / "metadata.json").write_text(json.dumps({"plan_sha256": digest(args.plan),
        "source_sha256": {p.name: digest(p) for p in sources.glob("*.py")},
        "scope": "remaining_five_reset_partial_boundary350"}, indent=2) + "\n")
    budget = Budget(args.plan, "temporal_boundary")
    c, records = plan["pixel_speed_calibration"], []
    for index in plan["boundary_indices"]:
        agent = TimedTemporal(c["coefficient_speed_per_intensity"], c["intercept"])
        rows, summary = trace(plan["cases"][index], plan["candidate"], budget,
            output / f"case-{index}", max_steps=plan["boundary_max_steps"], factory=lambda: agent)
        records.append({**summary, "DEV_index": index, "onsets": onsets(rows),
            "act_latency": percentiles(agent.latencies), "invalid_actions": 0,
            "survived_boundary": summary["completed"] or summary["steps"] == plan["boundary_max_steps"],
            "scope": "reset_partial_boundary350"})
        (output / "result.json").write_text(json.dumps(records, indent=2) + "\n")
    decision = {"cases": len(records), "survived": sum(r["survived_boundary"] for r in records),
        "median_progress": float(np.median([r["progress"] for r in records])),
        "median_damage": float(np.median([r["damage"] for r in records])), "invalid_actions": 0,
        "scope": "reset_partial_boundary350", "full_completion_claim": False}
    decision["gate_pass"] = len(records) == 5 and decision["survived"] >= 4 and decision["median_progress"] >= 0.35 and decision["median_damage"] <= 0.4
    (output / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision), flush=True)


if __name__ == "__main__":
    main()
