"""One preregistered DEV failure contrast; privileged features remain diagnostic."""

import argparse
import json
from pathlib import Path

import numpy as np

from retry.arc_agent import ArcAgent
from retry.arc_probe import OracleArc
from retry.diagnose import Budget, onsets, trace
from retry.evaluate import check_window, digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    manifest = json.loads(args.manifest.read_text())
    check_window(plan)
    assert manifest["plan_sha256"] == digest(args.plan)
    freeze_path = args.plan.parent / "freeze-v1.json"
    assert manifest["freeze_sha256"] == digest(freeze_path)
    freeze = json.loads(freeze_path.read_text())
    for name, expected in freeze["members_sha256"].items():
        if name.startswith("retry/"):
            assert digest(Path(name)) == expected
    source = args.plan.parent / manifest["reference"]
    assert digest(source / "trace.jsonl") == manifest["reference_trace_sha256"]
    reference = [json.loads(line) for line in (source / "trace.jsonl").read_text().splitlines()]
    output = args.plan.parent / manifest["output"]
    output.mkdir(exist_ok=False)
    sources = output / "sources"
    sources.mkdir()
    for path in Path(__file__).parent.glob("*.py"):
        (sources / path.name).write_bytes(path.read_bytes())
    (output / "metadata.json").write_text(json.dumps({
        "manifest_sha256": digest(args.manifest),
        "privileged_input_diagnostic_only": True,
        "source_sha256": {p.name: digest(p) for p in sources.glob("*.py")},
    }, indent=2) + "\n")
    budget = Budget(args.plan, "failure_probe")
    calibration = freeze["calibration"]
    records = []
    for arm in ["pixels", "oracle"]:
        factory = OracleArc if arm == "oracle" else lambda: ArcAgent(
            calibration["coefficient_speed_per_intensity"], calibration["intercept"])
        rows, summary = trace(plan["cases"][manifest["case_index"]], "frozen_arc_failure", budget,
            output / arm, max_steps=manifest["rollout_actions"], factory=factory,
            input_source=arm, replay_source=source, prefix=manifest["prefix_actions"])
        record = {**summary, "onsets_within_branch": onsets(rows),
            "final_off_track_counter": rows[-1]["off_track_counter"],
            "scope": "exact_shared_prefix_then_partial_rollout"}
        if arm == "pixels":
            paired = reference[manifest["prefix_actions"]:manifest["prefix_actions"] + len(rows)]
            assert len(paired) == len(rows)
            assert all(a["observation_sha256_after"] == b["observation_sha256_after"]
                and a["state_after"] == b["state_after"]
                and np.array_equal(a["action"], b["action"]) for a, b in zip(rows, paired))
            record["entire_pixel_continuation_exact"] = True
        records.append(record)
        (output / "result.json").write_text(json.dumps(records, indent=2) + "\n")
    pixel, oracle = records
    supported = (oracle["progress"] - pixel["progress"] >= manifest["min_progress_gain"]
        and oracle["damage"] <= manifest["max_oracle_damage"]
        and oracle["final_off_track_counter"] < manifest["max_oracle_counter_exclusive"]
        and pixel["final_off_track_counter"] >= manifest["min_pixel_counter"])
    decision = {"combined_observable_representation_bottleneck_supported": supported,
        "progress_gain": oracle["progress"] - pixel["progress"],
        "criteria": manifest["criteria"], "deployment_eligible": False,
        "caveat": "Truth changes road, obstacle and speed inputs together; this is neither an oracle upper bound nor a full-run completion test."}
    (output / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision), flush=True)


if __name__ == "__main__":
    main()
