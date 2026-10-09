"""Preregistered DEV boundary and minimal speed/target ablation."""

import argparse
import json
from pathlib import Path

import numpy as np

from retry.arc_agent import ArcAgent, arc_target
from retry.clearance_agent import ClearanceAgent, road_and_obstacles
from retry.diagnose import Budget, onsets, trace
from retry.evaluate import check_window, digest


class ArcLegacySpeed(ArcAgent):
    def act(self, observation):
        path, obstacles = road_and_obstacles(observation[-1])
        speed = float(np.sum(observation[-1, 74:82, 10:13] > 0.75)) / 3 / 0.042
        target = arc_target(path, speed, obstacles)
        if target is None:
            return self.controller.action(None, speed)
        return self.controller.action_target(float(target[0]), float(target[1]), speed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    check_window(plan)
    output = args.plan.parent / "boundaries"
    output.mkdir(exist_ok=False)
    sources = output / "sources"
    sources.mkdir()
    for source in Path(__file__).parent.glob("*.py"):
        (sources / source.name).write_bytes(source.read_bytes())
    (output / "metadata.json").write_text(json.dumps({"plan_sha256": digest(args.plan),
        "source_sha256": {p.name: digest(p) for p in sources.glob("*.py")},
        "scope": "Reset to fixed350-action partial boundary or earlier natural terminal. No prefix rescue or full2000 gate claim."}, indent=2) + "\n")
    calibration = plan["pixel_speed_calibration"]
    records = []
    for arm, indices, cls, stage in [
        ("arc_corrected", plan["remaining_DEV_indices"], ArcAgent, "boundary_arc"),
        ("fixed_corrected", plan["ablation_DEV_indices"], ClearanceAgent, "boundary_ablation"),
        ("arc_legacy_speed", plan["ablation_DEV_indices"], ArcLegacySpeed, "boundary_ablation"),
    ]:
        budget = Budget(args.plan, stage)
        for index in indices:
            rows, summary = trace(plan["cases"][index], arm, budget, output / f"case-{index}-{arm}",
                max_steps=plan["max_steps_boundary"], factory=lambda: cls(
                    calibration["coefficient_speed_per_intensity"], calibration["intercept"]))
            terminal = rows[-1]["terminated"] or rows[-1]["truncated"] if rows else False
            records.append({**summary, "DEV_index": index, "onsets": onsets(rows),
                "evaluation_scope": "partial_reset_boundary350",
                "reached_cap_or_finished": summary["steps"] == plan["max_steps_boundary"] or summary["completed"],
                "retired_early": terminal and not summary["completed"], "natural_terminal": terminal})
    (output / "result.json").write_text(json.dumps(records, indent=2) + "\n")


if __name__ == "__main__":
    main()
