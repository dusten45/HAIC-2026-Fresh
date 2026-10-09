"""One frozen checkpoint contrast; true input exists only in this research harness."""

import argparse
import json
from pathlib import Path

from retry.arc_agent import ArcAgent, arc_target
from retry.diagnose import Budget, onsets, trace
from retry.evaluate import check_window, digest
from retry.geometry_agent import GeometryController


class OracleArc:
    def __init__(self):
        self.controller = GeometryController()

    def reset(self, observation):
        self.controller.reset()

    def act_features(self, truth):
        target = arc_target(truth["forward_points_local"], truth["speed_m_s"], truth["obstacles_local"])
        return self.controller.action_target(float(target[0]), float(target[1]), truth["speed_m_s"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    check_window(plan)
    manifest_path = args.plan.parent / "arc-branch-preregistered.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["stage_sha256"] == digest(args.plan)
    output = args.plan.parent / "arc"
    output.mkdir(exist_ok=False)
    sources = output / "sources"
    sources.mkdir()
    for source in Path(__file__).parent.glob("*.py"):
        (sources / source.name).write_bytes(source.read_bytes())
    (output / "metadata.json").write_text(json.dumps({"manifest_sha256": digest(manifest_path),
        "source_sha256": {p.name: digest(p) for p in sources.glob("*.py")},
        "privileged_input_diagnostic_only": True}, indent=2) + "\n")
    budget = Budget(args.plan, "adaptive_followup")
    calibration = json.loads((args.plan.parent / "hud-calibration.json").read_text())
    source = args.plan.parent / manifest["source"]
    reference = [json.loads(line) for line in (source / "trace.jsonl").read_text().splitlines()]
    endpoint = reference[min(len(reference), manifest["prefix_actions"] + manifest["rollout_actions"]) - 1]
    records = []
    for arm in ["oracle", "pixels"]:
        factory = OracleArc if arm == "oracle" else lambda: ArcAgent(
            calibration["coefficient_speed_per_intensity"], calibration["intercept"])
        rows, summary = trace(plan["cases"][manifest["case_index"]], "local_arc", budget,
            output / arm, max_steps=manifest["rollout_actions"], factory=factory, input_source=arm,
            replay_source=source, prefix=manifest["prefix_actions"])
        records.append({**summary, "onsets_within_branch": onsets(rows),
            "fixed_row_reference_progress": endpoint["progress"],
            "progress_gain_vs_fixed_row": summary["progress"] - endpoint["progress"]})
    (output / "result.json").write_text(json.dumps(records, indent=2) + "\n")


if __name__ == "__main__":
    main()
