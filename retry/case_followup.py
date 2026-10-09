"""One preregistered full-case diagnostic after a positive local learning test."""

import argparse
import json
from pathlib import Path

from retry.diagnose import Budget, onsets, trace
from retry.evaluate import check_window, digest
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
    parent = (args.plan.parent / plan["local_learning_result"]).resolve()
    assert digest(parent) == plan["local_learning_result_sha256"]
    records = json.loads(parent.read_text())
    local = next(r for r in records if r["DEV_index"] == plan["case_index"])
    baseline = plan["reference_route_v2_DEV2"]
    assert baseline["damage"] - local["damage"] >= 0.2 and local["progress"] >= baseline["progress"] - 0.02 and local["final_off_track_counter"] < 10
    output = args.plan.parent / "full-case"
    output.mkdir(exist_ok=False)
    sources = output / "sources"
    sources.mkdir()
    for path in Path(__file__).parent.glob("*.py"):
        (sources / path.name).write_bytes(path.read_bytes())
    (output / "metadata.json").write_text(json.dumps({"plan_sha256": digest(args.plan),
        "source_sha256": {p.name: digest(p) for p in sources.glob("*.py")},
        "privileged_input": False, "scope": "one_reset_full_case_diagnostic_not_G2"}, indent=2) + "\n")
    c = plan["pixel_speed_calibration"]
    agent = TimedTemporal(c["coefficient_speed_per_intensity"], c["intercept"])
    rows, summary = trace(plan["cases"][plan["case_index"]], plan["candidate"], Budget(args.plan, "temporal_full_case"),
        output / "case", max_steps=plan["max_steps"], factory=lambda: agent)
    from retry.evaluate import percentiles
    result = {**summary, "onsets": onsets(rows), "act_latency": percentiles(agent.latencies),
        "final_off_track_counter": rows[-1]["off_track_counter"],
        "reference_frozen_Arc_full": plan["reference_frozen_Arc_full"],
        "diagnostic_completion_criterion_pass": summary["completed"],
        "G2_assessed": False, "deployment_eligible": False, "HOLDOUT_authorized_by_result": False,
        "scope": "one_reset_full_case_diagnostic_not_G2"}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
