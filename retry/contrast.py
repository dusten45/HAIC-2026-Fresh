"""DEV-only shared-controller input comparison; oracle stays in this harness."""

import argparse
import json
from pathlib import Path

from retry.diagnose import Budget, onsets, trace
from retry.evaluate import check_window, digest
from retry.geometry_agent import GeometryAgent, GeometryController


class OracleGeometry:
    def __init__(self):
        self.controller = GeometryController()

    def reset(self, observation):
        self.controller.reset()

    def act_features(self, truth):
        return self.controller.action(truth["centers"]["36"], truth["speed_m_s"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    check_window(plan)
    manifest_path = args.plan.parent / "contrast-preregistered.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["parent_stage_sha256"] == digest(args.plan)
    output = args.plan.parent / "contrast"
    output.mkdir(exist_ok=False)
    sources = output / "sources"
    sources.mkdir()
    for source in Path(__file__).parent.glob("*.py"):
        (sources / source.name).write_bytes(source.read_bytes())
    (output / "metadata.json").write_text(json.dumps({"manifest_sha256": digest(manifest_path),
        "source_sha256": {p.name: digest(p) for p in sources.glob("*.py")},
        "oracle_diagnostic_only": True, "protected_split_access": False}, indent=2) + "\n")
    budget = Budget(args.plan, "same_controller_oracle_vs_pixels")
    records = []
    calibration = manifest["pixel_speed_calibration"]
    for index in manifest["case_indices"]:
        for arm in ["oracle", "pixels"]:
            factory = OracleGeometry if arm == "oracle" else lambda: GeometryAgent(
                calibration["coefficient_speed_per_intensity"], calibration["intercept"])
            rows, summary = trace(plan["cases"][index], "geometry", budget,
                output / f"case-{index}-{arm}", max_steps=manifest["max_steps_per_arm"],
                factory=factory, input_source=arm)
            original = [json.loads(line) for line in (args.plan.parent / "traces" / f"case-{index}-basic/trace.jsonl").read_text().splitlines()]
            records.append({**summary, "onsets": onsets(rows),
                "matched_400_progress": rows[min(400, len(rows)) - 1]["progress"],
                "basic_reference_progress": original[-1]["progress"]})
    (output / "result.json").write_text(json.dumps(records, indent=2) + "\n")


if __name__ == "__main__":
    main()
