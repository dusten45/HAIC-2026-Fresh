"""Bounded DEV branches for two registered structural hypotheses."""

import argparse
import json
from pathlib import Path

import numpy as np

from retry.chord_agent import ChordTargetAgent
from retry.projection_agent import PixelCentreAgent
from retry.diagnose import Budget, trace
from retry.evaluate import check_window, digest
from retry.submission_probe import stack


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--arm", choices=["projection", "chord"], required=True)
    parser.add_argument("--case-index", type=int, required=True)
    args = parser.parse_args()
    directory = args.plan.parent
    plan, task = json.loads(args.plan.read_text()), json.loads(args.manifest.read_text())
    check_window(plan)
    assert digest(args.manifest) == args.manifest.with_suffix(".sha256").read_text().split()[0]
    assert digest(args.plan) == task["plan_sha256"]
    for name, expected in task["source_sha256"].items():
        assert digest(Path(name)) == expected
    frozen_path = directory / plan["challenger_freeze"]
    assert digest(frozen_path) == plan["challenger_freeze_sha256"]
    frozen = json.loads(frozen_path.read_text())
    for name, expected in frozen["members_sha256"].items():
        if name.startswith("retry/"):
            assert digest(Path(name)) == expected
    scene = next(x for x in task["scenes"] if x["case_index"] == args.case_index)
    source = directory / scene["source"]
    assert digest(source / "trace.jsonl") == scene["trace_sha256"]
    data = np.load(source / "pixels-actions.npz")
    c, p = frozen["calibration"], frozen["parameters"]
    values = [c["coefficient_speed_per_intensity"], c["intercept"], p["speed_cap"], p["lateral_fast"], p["lateral_safe"]]
    cls = PixelCentreAgent if args.arm == "projection" else ChordTargetAgent
    if args.arm == "projection":
        values += task["projection_origin_pixel_xy"]

    class Warm(cls):
        def reset(self, observation):
            super().reset(observation)
            self.warming_reference = True
            for i in range(scene["prefix_actions"]):
                np.testing.assert_array_equal(self.act(stack(data["frames"], i)), data["actions"][i])
            self.replayed_previous_steer = self.controller.previous_steer
            self.warming_reference = False

    rows, result = trace(plan["split"]["SCREEN"][args.case_index], "structural_" + args.arm,
        Budget(args.plan, "falsifications"), directory / task["output"] / f"case-{args.case_index}" / args.arm,
        max_steps=scene["rollout_actions"], factory=lambda: Warm(*values),
        replay_source=source, prefix=scene["prefix_actions"])
    result.update(final_off_track_counter=rows[-1]["off_track_counter"], scope="one matched partial DEV branch; not full-reset or adoption")
    (directory / task["output"] / f"case-{args.case_index}" / args.arm / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["progress", "damage", "final_off_track_counter"]}), flush=True)


if __name__ == "__main__":
    main()
