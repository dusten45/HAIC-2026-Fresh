"""Match the oracle's geometric support to the policy's visible image region."""

import argparse
import json
from pathlib import Path

import numpy as np

from retry.anchored_probe import OracleGeometry
from retry.arc_agent import arc_target
from retry.diagnose import Budget, onsets, trace
from retry.evaluate import check_window, digest


def first_visible_path(points):
    lower = np.array([(3 - 42) / 1.3608, (63 - 56) / 1.701])
    upper = np.array([(81 - 42) / 1.3608, (63 - 24) / 1.701])
    result = []
    for a, b in zip(np.asarray(points)[:-1], np.asarray(points)[1:]):
        lo, hi = 0.0, 1.0
        delta = b - a
        for axis in [0, 1]:
            if abs(delta[axis]) < 1e-12:
                if not lower[axis] <= a[axis] <= upper[axis]:
                    lo, hi = 1.0, 0.0
            else:
                limits = sorted([(lower[axis] - a[axis]) / delta[axis], (upper[axis] - a[axis]) / delta[axis]])
                lo, hi = max(lo, limits[0]), min(hi, limits[1])
        if lo <= hi:
            if not result:
                result.append((a + lo * delta).tolist())
            result.append((a + hi * delta).tolist())
            if hi < 1.0:
                break
        elif result:
            break
    return result


class VisibleOracle(OracleGeometry):
    def act_features(self, truth, observation):
        speed = max(0.0, self.speed_gain * float(observation[-1, 74:83, 9:14].sum()) + self.speed_bias)
        path = first_visible_path(truth["forward_points_local"])
        obstacles = [p for p in truth["obstacles_local"] if 3 <= 42 + 1.3608 * p[0] <= 81 and 0 <= 63 - 1.701 * p[1] < 61]
        target = arc_target(path, speed, obstacles)
        if target is None:
            return self.controller.action(None, speed)
        return self.controller.action_target(float(target[0]), float(target[1]), speed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    plan, manifest = json.loads(args.plan.read_text()), json.loads(args.manifest.read_text())
    check_window(plan)
    assert digest(args.plan) == manifest["plan_sha256"]
    assert digest(Path(__file__)) == manifest["visible_oracle_sha256"]
    freeze = json.loads((args.plan.parent / "freeze-v1.json").read_text())
    source = args.plan.parent / manifest["reference"]
    assert digest(source / "trace.jsonl") == manifest["reference_trace_sha256"]
    output = args.plan.parent / "visible-oracle"
    output.mkdir(exist_ok=False)
    sources = output / "sources"
    sources.mkdir()
    for p in Path(__file__).parent.glob("*.py"):
        (sources / p.name).write_bytes(p.read_bytes())
    (output / "metadata.json").write_text(json.dumps({"manifest_sha256": digest(args.manifest),
        "source_sha256": {p.name: digest(p) for p in sources.glob("*.py")},
        "privileged_input_diagnostic_only": True, "same_pixel_speed": True}, indent=2) + "\n")
    calibration = freeze["calibration"]
    factory = lambda: VisibleOracle(calibration["coefficient_speed_per_intensity"], calibration["intercept"])
    rows, summary = trace(plan["cases"][manifest["failure_case_index"]], "visible_geometry_pixel_speed", Budget(args.plan, "visible_oracle"),
        output / "branch", max_steps=manifest["rollout_actions"], factory=factory, input_source="oracle_geometry",
        replay_source=source, prefix=manifest["prefix_actions"])
    gain = summary["progress"] - manifest["baseline_progress"]
    decision = {"summary": summary, "onsets": onsets(rows), "progress_gain": gain,
        "visible_geometry_rescue_pass": gain >= manifest["min_progress_gain"] and summary["damage"] <= manifest["max_damage"] and rows[-1]["off_track_counter"] < manifest["max_counter_exclusive"],
        "final_off_track_counter": rows[-1]["off_track_counter"], "deployment_eligible": False,
        "scope": "exact_shared_prefix_partial_rollout"}
    (output / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision), flush=True)


if __name__ == "__main__":
    main()
