"""DEV-only matched information contrasts with the frozen controller unchanged."""

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from retry.connected_agent import connected_route
from retry.diagnose import Budget, trace
from retry.evaluate import check_window, digest
from retry.route_agent import route_target
from retry.schedule_agent import HazardScheduledAgent
from retry.submission_probe import stack


def visible_obstacles(truth):
    return [p for p in truth["obstacles_local"]
        if 3 <= 42 + 1.3608 * p[0] <= 81 and 0 <= 63 - 1.701 * p[1] < 61]


def local_road_image(points, half_width):
    """Semantic road inside the rendered support, including occluded asphalt."""
    mask = np.zeros((84, 84), np.uint8)
    for a, b in zip(np.asarray(points)[:-1], np.asarray(points)[1:]):
        delta = b - a
        length = np.linalg.norm(delta)
        if length < 1e-8:
            continue
        normal = np.array([delta[1], -delta[0]]) / length * half_width
        corners = np.array([a + normal, b + normal, b - normal, a - normal])
        pixels = np.rint(np.column_stack((42 + 1.3608 * corners[:, 0], 63 - 1.701 * corners[:, 1]))).astype(np.int32)
        cv2.fillPoly(mask, [pixels], 1)
    mask[61:] = 0
    return np.where(mask, np.float32(.4), np.float32(.6))


def recorded_geometry(source, frozen):
    """Reconstruct legal policy state; return diagnostic path/target differences."""
    c, p = frozen["calibration"], frozen["parameters"]
    class Inspect(HazardScheduledAgent):
        def tracked_obstacles(self, image, speed):
            self.current_obstacles = super().tracked_obstacles(image, speed)
            return self.current_obstacles
    actor = Inspect(c["coefficient_speed_per_intensity"], c["intercept"], p["speed_cap"], p["lateral_fast"], p["lateral_safe"])
    data = np.load(source / "pixels-actions.npz")
    rows = [json.loads(l) for l in (source / "trace.jsonl").read_text().splitlines()]
    actor.reset(stack(data["frames"], 0))
    features = []
    for i, expected in enumerate(data["actions"]):
        observation = stack(data["frames"], i)
        np.testing.assert_array_equal(actor.act(observation), expected)
        image = observation[-1]
        speed = max(0., actor.speed_gain * float(image[74:83, 9:14].sum()) + actor.speed_bias)
        obstacles = actor.current_obstacles
        path = connected_route(image, obstacles)
        target = route_target(path, speed)
        margins, errors = [], []
        if target is not None:
            for x, y, radius in obstacles:
                point = np.array([x, y])
                closest = target * np.clip(np.dot(point, target) / max(np.dot(target, target), 1e-8), 0, 1)
                margins.append(float(np.linalg.norm(point - closest) - 2.6 - radius))
        truth = np.asarray(rows[i]["truth"]["obstacles_local"])
        for x, y, _ in obstacles:
            errors.append(float(np.min(np.linalg.norm(truth[:, :2] - [x, y], axis=1))))
        features.append({"step": i + 1, "path_present": bool(path), "target": None if target is None else target.tolist(),
            "minimum_target_chord_margin_m": min(margins) if margins else None,
            "tracked_obstacles": obstacles, "tracked_position_errors_m": errors,
            "steering_at_limit": bool(abs(expected[0]) >= .395),
            "observed_control_exact": True})
    return features


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--arm", choices=["observed", "obstacles", "road", "joint"], required=True)
    args = parser.parse_args()
    directory = args.plan.parent
    plan = json.loads(args.plan.read_text())
    task = json.loads(args.manifest.read_text())
    check_window(plan)
    assert digest(args.manifest) == args.manifest.with_suffix(".sha256").read_text().split()[0]
    assert digest(args.plan) == task["plan_sha256"]
    assert digest(Path(__file__)) == task["contrast_source_sha256"]
    freeze_path = directory / plan["challenger_freeze"]
    assert digest(freeze_path) == plan["challenger_freeze_sha256"]
    frozen = json.loads(freeze_path.read_text())
    root = Path(__file__).resolve().parents[1]
    for name, expected in frozen["members_sha256"].items():
        if name.startswith("retry/"):
            assert digest(root / name) == expected
    c, p = frozen["calibration"], frozen["parameters"]
    source = directory / task["source"]
    assert digest(source / "trace.jsonl") == task["trace_sha256"]
    data = np.load(source / "pixels-actions.npz")
    original = [json.loads(x) for x in (source / "trace.jsonl").read_text().splitlines()]

    class Warm(HazardScheduledAgent):
        def __init__(self):
            super().__init__(c["coefficient_speed_per_intensity"], c["intercept"],
                p["speed_cap"], p["lateral_fast"], p["lateral_safe"])

        def reset(self, observation):
            super().reset(observation)
            for i in range(task["prefix_actions"]):
                np.testing.assert_array_equal(super().act(stack(data["frames"], i)), data["actions"][i])
            self.replayed_previous_steer = self.controller.previous_steer

        def act_features(self, truth, observation):
            image = observation[-1]
            speed = max(0.0, self.speed_gain * float(image[74:83, 9:14].sum()) + self.speed_bias)
            observed = self.tracked_obstacles(image, speed)
            lookahead = float(np.clip(4 + .35 * speed, 6, 14))
            near = any(y > 0 and np.hypot(x, y) <= lookahead + 2.6 + radius for x, y, radius in observed)
            self.controller.lateral_acceleration = self.lateral_safe if near else self.lateral_fast
            obstacles = visible_obstacles(truth) if args.arm in ["obstacles", "joint"] else observed
            road = local_road_image(truth["forward_points_local"], task["road_half_width_m"]) if args.arm in ["road", "joint"] else image
            target = route_target(connected_route(road, obstacles), speed)
            if target is None:
                return self.controller.action(None, speed)
            return self.controller.action_target(float(target[0]), float(target[1]), speed)

    output = directory / task["output"] / args.arm
    rows, result = trace(plan["split"]["SCREEN"][task["case_index"]], "matched_information_" + args.arm,
        Budget(args.plan, "contrasts"), output, max_steps=task["rollout_actions"], factory=Warm,
        input_source="pixels" if args.arm == "observed" else "oracle_geometry", replay_source=source,
        prefix=task["prefix_actions"])
    if args.arm == "observed":
        expected = original[task["prefix_actions"]:task["prefix_actions"] + len(rows)]
        assert len(rows) == len(expected)
        assert all(a["state_after"] == b["state_after"] and a["observation_sha256_after"] == b["observation_sha256_after"]
            and np.array_equal(a["action"], b["action"]) for a, b in zip(rows, expected))
        result["entire_observed_continuation_exact"] = True
    result.update(final_off_track_counter=rows[-1]["off_track_counter"],
        manifest_sha256=digest(args.manifest), controller_and_speed_feature_unchanged=True,
        privilege="none" if args.arm == "observed" else "semantic geometry inside image ROI; diagnostic only, occlusions may be revealed",
        scope="matched partial DEV branch, no completion/generalization or deployment claim")
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["variant", "progress", "damage", "final_off_track_counter"]}), flush=True)


if __name__ == "__main__":
    main()
