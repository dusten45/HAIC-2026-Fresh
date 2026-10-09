"""Preregistered closed-loop DEV information-factor interventions."""

import argparse
import json
from pathlib import Path

import numpy as np

from retry.diagnose import Budget, trace
from retry.evaluate import check_window, digest
from retry.factorial_agent import FactorialMemoryAgent
from retry.submission_probe import stack


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--case-index", type=int, required=True)
    parser.add_argument("--arm", required=True)
    args = parser.parse_args()
    directory = args.plan.parent
    plan, task = json.loads(args.plan.read_text()), json.loads(args.manifest.read_text())
    check_window(plan)
    assert digest(args.plan) == task["plan_sha256"]
    assert digest(args.manifest) == args.manifest.with_suffix(".sha256").read_text().split()[0]
    for name, expected in task["source_sha256"].items():
        assert digest(Path(name)) == expected
    freeze_path = directory / plan["reference_freeze"]
    assert digest(freeze_path) == plan["reference_freeze_sha256"]
    frozen = json.loads(freeze_path.read_text())
    for name, expected in frozen["members_sha256"].items():
        if name.startswith("retry/"):
            assert digest(Path(name)) == expected
    scene = next(s for s in task["scenes"] if s["case_index"] == args.case_index)
    assert args.arm in scene["arms"]
    source = directory / scene["source"]
    assert digest(source / "trace.jsonl") == scene["trace_sha256"]
    data = np.load(source / "pixels-actions.npz")
    original = [json.loads(line) for line in (source / "trace.jsonl").read_text().splitlines()]
    c, p = frozen["calibration"], frozen["parameters"]
    values = [c["coefficient_speed_per_intensity"], c["intercept"], p["speed_cap"], p["lateral_fast"], p["lateral_safe"]]
    path_mode, risk_mode = task["arms"][args.arm]

    class Warm(FactorialMemoryAgent):
        def reset(self, observation):
            super().reset(observation)
            self.warming_reference = True
            for i in range(scene["prefix_actions"]):
                np.testing.assert_array_equal(self.act(stack(data["frames"], i)), data["actions"][i])
            self.replayed_previous_steer = self.controller.previous_steer
            self.warming_reference = False
            self.branch_features = []

        def act(self, observation):
            action = super().act(observation)
            if not getattr(self, "warming_reference", True):
                self.branch_features.append(self.last_features)
            return action

    actor = Warm(*values, path_mode, risk_mode)
    output = directory / task["output"] / f"case-{args.case_index}" / args.arm
    output.parent.mkdir(parents=True, exist_ok=True)
    rows, result = trace(plan["split"]["SCREEN"][args.case_index], "factorial_" + args.arm,
        Budget(args.plan, task["stage"]), output, max_steps=scene["rollout_actions"],
        factory=lambda: actor, replay_source=source, prefix=scene["prefix_actions"])
    exact = None
    compare = original if args.arm == "OO" else None
    if args.arm == "MM" and "modified_trace" in scene:
        path = directory / scene["modified_trace"]
        assert digest(path) == scene["modified_trace_sha256"]
        compare = [json.loads(line) for line in path.read_text().splitlines()]
    if compare is not None:
        expected = compare[scene["prefix_actions"]:scene["prefix_actions"] + len(rows)]
        assert len(expected) == len(rows)
        assert all(a["state_after"] == b["state_after"] and a["observation_sha256_after"] == b["observation_sha256_after"]
            and np.array_equal(a["action"], b["action"]) for a, b in zip(rows, expected))
        exact = True
    result.update(max_off_track_counter=max(r["off_track_counter"] for r in rows),
        final_off_track_counter=rows[-1]["off_track_counter"], reference_continuation_exact=exact,
        path_memory=path_mode, speed_risk=risk_mode, policy_future_inputs="actual current pixels only",
        future_recorded_actions_copied=False, truth_supplied_to_policy=False,
        scope="matched DEV factor intervention; partial progress is not completion or full-reset policy performance")
    (output / "features.jsonl").write_text("".join(json.dumps(x) + "\n" for x in actor.branch_features))
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["variant", "completed", "progress", "damage", "max_off_track_counter", "retire_reason"]}), flush=True)


if __name__ == "__main__":
    main()
