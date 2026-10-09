"""Frozen DEV detector check and route hypothesis; oracle is diagnostic only."""

import argparse
import json
from pathlib import Path

import numpy as np

from retry.clearance_agent import ClearanceAgent, clearance_target, road_and_obstacles
from retry.diagnose import Budget, onsets, trace
from retry.evaluate import check_window, digest
from retry.geometry_agent import GeometryController


class OracleClearance:
    def __init__(self):
        self.controller = GeometryController()

    def reset(self, observation):
        self.controller.reset()

    def act_features(self, truth):
        target = clearance_target(truth["forward_points_local"], truth["obstacles_local"])
        return self.controller.action(target, truth["speed_m_s"])


def detector_check(root):
    tp = fp = fn = 0
    for source in sorted((root / "contrast").glob("case-*")):
        rows = [json.loads(line) for line in (source / "trace.jsonl").read_text().splitlines()]
        frames = np.load(source / "pixels-actions.npz")["frames"]
        for row, frame in zip(rows, frames):
            _, predicted = road_and_obstacles(frame.astype(np.float32) / 255)
            eligible = [[x, y] for x, y, _ in row["truth"]["obstacles_local"]
                        if 3 <= 42 + 1.3608 * x <= 81 and 3 <= 63 - 1.701 * y <= 60]
            unmatched = set(range(len(eligible)))
            for x, y, _ in predicted:
                if not (3 <= 42 + 1.3608 * x <= 81 and 3 <= 63 - 1.701 * y <= 60):
                    continue
                matches = [(np.hypot((x - eligible[i][0]) * 1.3608, (y - eligible[i][1]) * 1.701), i) for i in unmatched]
                if matches and min(matches)[0] <= 3:
                    tp += 1
                    unmatched.remove(min(matches)[1])
                else:
                    fp += 1
            fn += len(unmatched)
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    return {"TP": tp, "FP": fp, "FN": fn, "precision": precision, "recall": recall,
            "passed": precision >= 0.7 and recall >= 0.6,
            "scope": "Correlated visible-obstacle frames on selected DEV; no independent test-track claim."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    check_window(plan)
    manifest_path = args.plan.parent / "followup-preregistered.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["stage_plan_sha256"] == digest(args.plan)
    output = args.plan.parent / "clearance"
    output.mkdir(exist_ok=False)
    sources = output / "sources"
    sources.mkdir()
    for source in Path(__file__).parent.glob("*.py"):
        (sources / source.name).write_bytes(source.read_bytes())
    detector = detector_check(args.plan.parent)
    (output / "detector.json").write_text(json.dumps(detector, indent=2) + "\n")
    (output / "metadata.json").write_text(json.dumps({"manifest_sha256": digest(manifest_path),
        "source_sha256": {p.name: digest(p) for p in sources.glob("*.py")},
        "oracle_diagnostic_only": True}, indent=2) + "\n")
    print(json.dumps(detector), flush=True)
    budget = Budget(args.plan, "adaptive_followup")
    records = []
    calibration = json.loads((args.plan.parent / "hud-calibration.json").read_text())
    for index in manifest["case_indices"]:
        for arm in (["oracle", "pixels"] if detector["passed"] else ["oracle"]):
            factory = OracleClearance if arm == "oracle" else lambda: ClearanceAgent(
                calibration["coefficient_speed_per_intensity"], calibration["intercept"])
            rows, summary = trace(plan["cases"][index], "clearance", budget,
                output / f"case-{index}-{arm}", max_steps=manifest["max_steps"], factory=factory, input_source=arm)
            reference = [json.loads(line) for line in (args.plan.parent / "contrast" / f"case-{index}-{arm}/trace.jsonl").read_text().splitlines()]
            reference_progress = reference[min(400, len(reference)) - 1]["progress"]
            records.append({**summary, "onsets": onsets(rows), "reference_progress": reference_progress,
                "matched_cap_progress_gain": summary["progress"] - reference_progress})
    (output / "result.json").write_text(json.dumps(records, indent=2) + "\n")


if __name__ == "__main__":
    main()
