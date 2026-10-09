"""Matched legal-history DEV branches for one pixel speed-bar representation."""

import argparse
import json
from pathlib import Path

import numpy as np

from retry.bar_feedback_agent import BarFeedbackAgent
from retry.diagnose import Budget, trace
from retry.evaluate import check_window, digest
from retry.submission_probe import stack


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--case-index", required=True, type=int)
    args = parser.parse_args()
    directory = args.plan.parent
    plan, task = json.loads(args.plan.read_text()), json.loads(args.manifest.read_text())
    check_window(plan)
    assert digest(args.plan) == task["plan_sha256"]
    assert digest(args.manifest) == args.manifest.with_suffix(".sha256").read_text().split()[0]
    for name, expected in task["source_sha256"].items():
        assert digest(Path(name)) == expected
    scene = next(s for s in task["scenes"] if s["case_index"] == args.case_index)
    source = directory / scene["source"]
    assert digest(source / "trace.jsonl") == scene["trace_sha256"]
    assert digest(source / "pixels-actions.npz") == scene["pixels_actions_sha256"]
    data = np.load(source / "pixels-actions.npz")
    freeze_path = directory / plan["reference_freeze"]
    assert digest(freeze_path) == plan["reference_freeze_sha256"]
    freeze = json.loads(freeze_path.read_text())
    c, p = freeze["calibration"], freeze["parameters"]
    table_path = directory / task["bar_table"]
    assert digest(table_path) == task["bar_table_sha256"]
    table = json.loads(table_path.read_text())

    class Warm(BarFeedbackAgent):
        def reset(self, observation):
            super().reset(observation)
            self.warm_reference = True
            for i in range(scene["prefix_actions"]):
                np.testing.assert_array_equal(self.act(stack(data["frames"], i)), data["actions"][i])
            self.replayed_previous_steer = self.controller.previous_steer
            self.warm_reference = False
            self.features = []

        def act(self, observation):
            action = super().act(observation)
            if not self.warm_reference:
                self.features.append(self.last_features)
            return action

    actor = Warm(c["coefficient_speed_per_intensity"], c["intercept"],
        p["speed_cap"], p["lateral_fast"], p["lateral_safe"], table["integrals"], table["speeds"])
    output = directory / task["output"] / f"case-{args.case_index}"
    output.parent.mkdir(parents=True, exist_ok=True)
    rows, result = trace(plan["split"]["SCREEN"][args.case_index], "bar_feedback",
        Budget(args.plan, "short"), output, max_steps=scene["rollout_actions"],
        factory=lambda: actor, replay_source=source, prefix=scene["prefix_actions"])
    result.update(max_off_track_counter=max(r["off_track_counter"] for r in rows),
        final_off_track_counter=rows[-1]["off_track_counter"],
        privileged_inputs=False, future_recorded_actions_copied=False,
        input_boundary="current pixels only; speed-bar substitution only in gas/brake feedback",
        scope="same-prefix partial DEV result; separate full-reset gate required")
    (output / "features.jsonl").write_text("".join(json.dumps(r) + "\n" for r in actor.features))
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["completed", "progress", "damage", "steps", "retire_reason", "max_off_track_counter"]}), flush=True)


if __name__ == "__main__":
    main()
