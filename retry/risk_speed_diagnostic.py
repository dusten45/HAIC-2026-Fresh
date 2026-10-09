"""Offline DEV risk-speed substitution; never creates a simulator or policy ZIP."""

import argparse
import json
from pathlib import Path

import numpy as np

from retry.memory_agent import MinimalMemoryAgent
from retry.schedule_agent import HazardScheduledAgent


def inspect(source, kind, calibration, parameters):
    rows = [json.loads(line) for line in (source / "trace.jsonl").read_text().splitlines()]
    data = np.load(source / "pixels-actions.npz")
    actor = (HazardScheduledAgent if kind == "original" else MinimalMemoryAgent)(
        calibration["coefficient_speed_per_intensity"], calibration["intercept"],
        parameters["speed_cap"], parameters["lateral_fast"], parameters["lateral_safe"])
    captured = {}
    tracking, control = actor.tracked_obstacles, actor.controller.action_target

    def tracked(image, speed):
        captured["obstacles"] = tracking(image, speed)
        captured["speed"] = speed
        return captured["obstacles"]

    def target(x, forward, speed):
        captured["target"] = [float(x), float(forward)]
        return control(x, forward, speed)

    actor.tracked_obstacles, actor.controller.action_target = tracked, target

    def observation(index):
        return np.asarray([data["frames"][max(0, index - j)] for j in [3, 2, 1, 0]],
            dtype=np.float32) / 255

    actor.reset(observation(0))
    results = []
    for i, row in enumerate(rows):
        captured.clear()
        obs = observation(i)
        action = actor.act(obs)
        np.testing.assert_array_equal(action, data["actions"][i])
        np.testing.assert_array_equal(action, np.asarray(row["action"], dtype=np.float32))
        true_speed = float(np.linalg.norm(row["state_before"]["velocity"]))
        assert abs(true_speed - row["truth"]["speed_m_s"]) < 1e-10
        if i:
            assert rows[i - 1]["state_after"] == row["state_before"]
        speed, obstacles = captured["speed"], captured["obstacles"]

        def risk(value):
            lookahead = float(np.clip(4 + .35 * value, 6, 14))
            margins = [lookahead + 2.6 + radius - float(np.hypot(x, y))
                for x, y, radius in obstacles if y > 0]
            return lookahead, bool(margins and max(margins) >= 0), max(margins, default=None)

        observed, substitute = risk(speed), risk(true_speed)
        old_lateral = parameters["lateral_safe"] if observed[1] else parameters["lateral_fast"]
        new_lateral = parameters["lateral_safe"] if substitute[1] else parameters["lateral_fast"]
        assert actor.controller.lateral_acceleration == old_lateral
        proposed = action.copy()
        old_target_speed = new_target_speed = None
        if "target" in captured:
            x, forward = captured["target"]
            curvature = 2 * x / max(forward * forward + x * x, 1e-6)
            old_target_speed = min(parameters["speed_cap"], float(np.sqrt(old_lateral / (abs(curvature) + .003))))
            new_target_speed = min(parameters["speed_cap"], float(np.sqrt(new_lateral / (abs(curvature) + .003))))
            proposed[1:] = [np.clip(.08 * (new_target_speed - speed), 0, .5),
                np.clip(.04 * (speed - new_target_speed), 0, .5)]
        patch = obs[-1, 74:83, 9:14]
        results.append({"step": i + 1, "time_before_s": row["state_before"]["time"],
            "raw_action_duration_s": row["state_after"]["time"] - row["state_before"]["time"],
            "pixel_speed_m_s": speed, "true_pre_action_speed_m_s": true_speed,
            "speed_error_m_s": speed - true_speed, "obstacles_fixed": obstacles,
            "observed_lookahead": observed[0], "true_speed_risk_lookahead": substitute[0],
            "observed_near": observed[1], "true_speed_risk_near": substitute[1],
            "observed_risk_margin_m": observed[2], "true_speed_risk_margin_m": substitute[2],
            "risk_decision_changed": observed[1] != substitute[1],
            "target_fixed": captured.get("target"), "control_feedback_speed_fixed": speed,
            "observed_target_speed": old_target_speed, "risk_only_target_speed": new_target_speed,
            "recorded_action": action.tolist(), "risk_only_offline_action": proposed.tolist(),
            "gas_brake_changed": not np.array_equal(action[1:], proposed[1:]),
            "ROI_column_integrals": patch.sum(axis=0).tolist(), "ROI_gray_u8": np.rint(patch * 255).astype(int).tolist(),
            "collision": row["collision"], "off_track_counter": row["off_track_counter"]})
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--freeze", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    manifest, frozen = json.loads(args.manifest.read_text()), json.loads(args.freeze.read_text())
    args.output.mkdir(exist_ok=False)
    for case in manifest["offline_sources"]:
        results = inspect(args.manifest.parent / case["source"], case["policy"],
            frozen["calibration"], frozen["parameters"])
        (args.output / (case["id"] + ".jsonl")).write_text("".join(json.dumps(r) + "\n" for r in results))
        print(json.dumps({"id": case["id"], "saved_actions_exact": len(results), "new_physics_actions": 0}))


if __name__ == "__main__":
    main()
