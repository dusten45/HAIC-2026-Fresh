"""Privileged DEV intervention in longitudinal feedback only; no policy package."""

import argparse
import json
from pathlib import Path

import numpy as np

from retry.diagnose import Budget, trace
from retry.evaluate import check_window, digest
from retry.memory_agent import MinimalMemoryAgent
from retry.schedule_agent import HazardScheduledAgent
from retry.submission_probe import stack


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--scene", required=True)
    parser.add_argument("--arm", required=True, choices=["observed", "true_feedback"])
    args = parser.parse_args()
    directory = args.plan.parent
    plan, task = json.loads(args.plan.read_text()), json.loads(args.manifest.read_text())
    check_window(plan)
    assert digest(args.plan) == task["plan_sha256"]
    assert digest(args.manifest) == args.manifest.with_suffix(".sha256").read_text().split()[0]
    for name, expected in task["source_sha256"].items():
        assert digest(Path(name)) == expected
    scene = next(s for s in task["scenes"] if s["id"] == args.scene)
    source = directory / scene["source"]
    assert digest(source / "trace.jsonl") == scene["trace_sha256"]
    data = np.load(source / "pixels-actions.npz")
    expected = [json.loads(s) for s in (source / "trace.jsonl").read_text().splitlines()]
    freeze_path = directory / plan["reference_freeze"]
    assert digest(freeze_path) == plan["reference_freeze_sha256"]
    frozen = json.loads(freeze_path.read_text())
    c, p = frozen["calibration"], frozen["parameters"]
    values = [c["coefficient_speed_per_intensity"], c["intercept"], p["speed_cap"], p["lateral_fast"], p["lateral_safe"]]
    cls = HazardScheduledAgent if scene["policy"] == "original" else MinimalMemoryAgent

    class Warm(cls):
        def __init__(self):
            super().__init__(*values)
            original = self.controller.action_target

            def feedback(x, forward, pixel_speed):
                action = original(x, forward, pixel_speed)
                curvature = 2 * x / max(forward * forward + x * x, 1e-6)
                target = min(self.controller.speed_cap,
                    float(np.sqrt(self.controller.lateral_acceleration / (abs(curvature) + .003))))
                effective = pixel_speed if self.warming or args.arm == "observed" else self.true_feedback_speed
                changed = action.copy()
                if not self.warming and args.arm == "true_feedback":
                    changed[1:] = [np.clip(.08 * (target - effective), 0, .5),
                        np.clip(.04 * (effective - target), 0, .5)]
                assert changed[0] == action[0]
                self.feature.update(target=[float(x), float(forward)], target_speed=target,
                    risk_lateral=self.controller.lateral_acceleration,
                    pixel_speed=pixel_speed, feedback_speed=effective,
                    pixel_shadow_action=action.tolist(), actual_action=changed.tolist())
                return changed

            self.controller.action_target = feedback

        def reset(self, observation):
            super().reset(observation)
            self.warming = True
            for i in range(scene["prefix_actions"]):
                self.feature = {}
                np.testing.assert_array_equal(self.act(stack(data["frames"], i)), data["actions"][i])
            self.replayed_previous_steer = self.controller.previous_steer
            self.warming = False
            self.features = []

        def act_features(self, truth, observation):
            self.true_feedback_speed = float(truth["speed_m_s"])
            self.feature = {"true_pre_action_speed": self.true_feedback_speed}
            action = self.act(observation)
            self.feature.setdefault("actual_action", action.tolist())
            self.features.append(self.feature)
            return action

    actor = Warm()
    output = directory / task["output"] / args.scene / args.arm
    output.parent.mkdir(parents=True, exist_ok=True)
    rows, result = trace(scene["case"], "feedback_" + args.scene + "_" + args.arm,
        Budget(args.plan, task["stage"]), output, max_steps=scene["rollout_actions"],
        factory=lambda: actor, input_source="oracle_geometry", replay_source=source,
        prefix=scene["prefix_actions"])
    exact = None
    if args.arm == "observed":
        comparison = expected[scene["prefix_actions"]:scene["prefix_actions"] + len(rows)]
        assert len(comparison) == len(rows)
        assert all(a["state_after"] == b["state_after"]
            and a["observation_sha256_after"] == b["observation_sha256_after"]
            and np.array_equal(a["action"], b["action"]) for a, b in zip(rows, comparison))
        exact = True
    result.update(reference_continuation_exact=exact,
        max_off_track_counter=max(r["off_track_counter"] for r in rows),
        final_off_track_counter=rows[-1]["off_track_counter"],
        changed_input="aligned current speed in gas/brake feedback only" if args.arm == "true_feedback" else "none",
        risk_target_path_motion_steer_inputs="pixel based on each actual current observation; unchanged formula and coefficients",
        subsequent_observations="actual closed-loop output, not fixed replay or future recorded actions",
        speed_filter="none, inherited unchanged", future_recorded_actions_copied=False,
        scope="privileged matched-prefix DEV diagnostic; not a deployable policy or full-reset policy score")
    (output / "features.jsonl").write_text("".join(json.dumps(r) + "\n" for r in actor.features))
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["completed", "progress", "damage", "steps", "retire_reason", "max_off_track_counter"]}), flush=True)


if __name__ == "__main__":
    main()
