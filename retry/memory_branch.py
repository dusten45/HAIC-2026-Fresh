"""Registered matched DEV branches for pixel-only memory interventions."""

import argparse
import json
from pathlib import Path

import numpy as np

from retry.diagnose import Budget, trace
from retry.evaluate import check_window, digest
from retry.memory_agent import FreshDetectionAgent
from retry.schedule_agent import HazardScheduledAgent
from retry.submission_probe import stack


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--case-index", type=int, required=True)
    parser.add_argument("--arm", choices=["fresh", "minimal"], required=True)
    args = parser.parse_args()
    directory = args.plan.parent
    plan, task = json.loads(args.plan.read_text()), json.loads(args.manifest.read_text())
    check_window(plan)
    assert digest(args.manifest) == args.manifest.with_suffix(".sha256").read_text().split()[0]
    assert digest(args.plan) == task["plan_sha256"]
    for name, expected in task["source_sha256"].items():
        assert digest(Path(name)) == expected
    frozen_path = directory / plan["reference_freeze"]
    assert digest(frozen_path) == plan["reference_freeze_sha256"]
    frozen = json.loads(frozen_path.read_text())
    for name, expected in frozen["members_sha256"].items():
        if name.startswith("retry/"):
            assert digest(Path(name)) == expected
    scene = next(s for s in task["scenes"] if s["case_index"] == args.case_index)
    source = directory / scene["source"]
    assert digest(source / "trace.jsonl") == scene["trace_sha256"]
    data = np.load(source / "pixels-actions.npz")
    c, p = frozen["calibration"], frozen["parameters"]
    values = [c["coefficient_speed_per_intensity"], c["intercept"], p["speed_cap"], p["lateral_fast"], p["lateral_safe"]]
    if args.arm == "minimal":
        from retry.memory_agent import MinimalMemoryAgent
        cls = MinimalMemoryAgent
    else:
        cls = FreshDetectionAgent

    class Warm(cls):
        def reset(self, observation):
            super().reset(observation)
            reference = HazardScheduledAgent(*values)
            reference.reset(stack(data["frames"], 0))
            for i in range(scene["prefix_actions"]):
                observed = stack(data["frames"], i)
                np.testing.assert_array_equal(reference.act(observed), data["actions"][i])
                # Build the new estimator's state from the same legal history.
                # Its hypothetical prefix actions never drive the simulator.
                self.act(observed)
            self.replayed_previous_steer = reference.controller.previous_steer

    output = directory / task["output"] / f"case-{args.case_index}" / args.arm
    output.parent.mkdir(parents=True, exist_ok=True)
    rows, result = trace(plan["split"]["SCREEN"][args.case_index], "memory_" + args.arm,
        Budget(args.plan, "branches"), output,
        max_steps=scene["rollout_actions"], factory=lambda: Warm(*values), replay_source=source,
        prefix=scene["prefix_actions"])
    result.update(final_off_track_counter=rows[-1]["off_track_counter"],
        max_off_track_counter=max(r["off_track_counter"] for r in rows),
        privilege="none; policy reads pixels only", controller_and_speed_settings_fixed=True,
        manifest_sha256=digest(args.manifest), scope="matched partial DEV branch, not full-reset completion")
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["progress", "damage", "final_off_track_counter"]}), flush=True)


if __name__ == "__main__":
    main()
