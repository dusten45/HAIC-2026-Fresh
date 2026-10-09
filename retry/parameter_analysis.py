"""DEV-only default equivalence and speed-law regime/failure diagnostics."""

import argparse
import json
from pathlib import Path

import numpy as np

from retry.evaluate import check_window, digest
from retry.parameter_agent import ParameterizedConnectedAgent, SpeedController
from retry.parameter_probe import guard_reference
from retry.submission_probe import stack, validate_source


class RecordingController(SpeedController):
    def action(self, far_x, speed):
        self.last = {"regime": "no_path", "pixel_speed": speed, "target_speed": 0, "curvature": None}
        return super().action(far_x, speed)

    def action_target(self, x, forward, speed):
        curvature = 2 * x / max(forward * forward + x * x, 1e-6)
        corner = float(np.sqrt(self.lateral_acceleration / (abs(curvature) + 0.003)))
        target = min(self.speed_cap, corner)
        self.last = {"regime": "cap" if corner >= self.speed_cap else "corner", "pixel_speed": speed,
            "target_speed": target, "curvature": curvature}
        return super().action_target(x, forward, speed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    check_window(plan)
    freeze, _ = guard_reference(plan, args.plan.parent)
    root = Path(__file__).resolve().parents[1]
    validate_source("parameter_agent.py", (root / "retry/parameter_agent.py").read_text())
    c = freeze["calibration"]
    records, all_regimes, exact = [], [], 0
    for part in sorted((args.plan.parent / "baseline").glob("partition-*")):
        summaries = json.loads((part / "result.json").read_text())
        for summary in summaries:
            index = summary["case_index"]
            source = part / f"case-{index}"
            data = np.load(source / "pixels-actions.npz")
            rows = [json.loads(x) for x in (source / "trace.jsonl").read_text().splitlines()]
            agent = ParameterizedConnectedAgent(c["coefficient_speed_per_intensity"], c["intercept"])
            agent.controller = RecordingController(28, 5)
            agent.reset(stack(data["frames"], 0))
            telemetry = []
            for i, expected in enumerate(data["actions"]):
                check_window(plan)
                actual = agent.act(stack(data["frames"], i))
                np.testing.assert_array_equal(actual, expected)
                exact += 1
                row = rows[i]
                telemetry.append({"step": i + 1, **agent.controller.last,
                    "true_speed_diagnostic": row["truth"]["speed_m_s"], "heading_error_diagnostic": row["truth"]["heading_error_rad"],
                    "lateral_m_diagnostic": row["truth"]["lateral_m"], "damage": row["damage"],
                    "collision": row["collision"], "off_track_counter": row["off_track_counter"]})
            (source / "speed-regimes.json").write_text(json.dumps(telemetry) + "\n")
            regimes = {label: sum(r["regime"] == label for r in telemetry) for label in ["cap", "corner", "no_path"]}
            all_regimes.extend(r["regime"] for r in telemetry)
            valid = [r for r in telemetry if r["regime"] != "no_path"]
            records.append({"case_index": index, "completed": summary["completed"], "lap_ms": summary["lap_ms"],
                "damage": summary["damage"], "steps": summary["steps"], "source": str(source.relative_to(args.plan.parent)),
                "regime_counts": regimes, "median_actual_speed_m_s": float(np.median([r["true_speed_diagnostic"] for r in telemetry])),
                "median_target_speed_m_s": float(np.median([r["target_speed"] for r in valid])) if valid else None,
                "onsets": summary["onsets"], "retire_reason": summary["retire_reason"],
                "source_trace_sha256": digest(source / "trace.jsonl")})
    records.sort(key=lambda r: r["case_index"])
    assert [r["case_index"] for r in records] == list(range(8))
    valid_count = sum(x != "no_path" for x in all_regimes)
    cap_fraction = sum(x == "cap" for x in all_regimes) / max(valid_count, 1)
    result = {"plan_sha256": digest(args.plan), "candidate_source_sha256": digest(root / "retry/parameter_agent.py"),
        "default_exact_equivalence_pass": True, "exact_default_actions": exact, "baseline_completions": sum(r["completed"] for r in records),
        "baseline_cases": records, "cap_binding_fraction_target_valid_actions": cap_fraction,
        "search_dimensions": ["speed_cap", "lateral_acceleration"] if cap_fraction >= 0.05 else ["lateral_acceleration"],
        "protected_data_used": False, "new_simulation_actions": 0}
    output = args.plan.parent / "baseline-analysis.json"
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
