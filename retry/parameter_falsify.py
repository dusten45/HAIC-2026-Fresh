"""One speed-law backoff contrast with exact physics and legal observed history."""

import argparse
import json
from pathlib import Path

import numpy as np

from retry.diagnose import Budget, trace
from retry.evaluate import check_window, digest
from retry.parameter_agent import ParameterizedConnectedAgent
from retry.parameter_probe import guard_reference
from retry.submission_probe import stack


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--arm", choices=["continue", "backoff"], required=True)
    args = parser.parse_args()
    directory = args.plan.parent
    plan, manifest = json.loads(args.plan.read_text()), json.loads(args.manifest.read_text())
    check_window(plan)
    assert manifest["plan_sha256"] == digest(args.plan)
    assert digest(args.manifest) == args.manifest.with_suffix(".sha256").read_text().split()[0]
    assert manifest["parameter_source_sha256"] == digest(Path(__file__).parent / "parameter_agent.py")
    assert manifest["split"] in ["SCREEN", "OLD_DEV"]
    source = (directory / manifest["source"]).resolve()
    assert source.is_relative_to(directory.resolve())
    assert digest(source / "trace.jsonl") == manifest["trace_sha256"]
    assert digest(source / "pixels-actions.npz") == manifest["pixels_actions_sha256"]
    assert 2 * (manifest["prefix_actions"] + manifest["rollout_actions"]) <= 3000
    freeze, _ = guard_reference(plan, directory)
    c = freeze["calibration"]
    data = np.load(source / "pixels-actions.npz")
    before = [json.loads(x) for x in (source / "trace.jsonl").read_text().splitlines()]
    prefix = manifest["prefix_actions"]
    fast = manifest["tested_parameters"]
    changed = manifest["backoff_parameters"]
    assert sum(fast[k] != changed[k] for k in fast) == 1

    class Warm(ParameterizedConnectedAgent):
        def __init__(self):
            super().__init__(c["coefficient_speed_per_intensity"], c["intercept"],
                fast["speed_cap"], fast["lateral_acceleration"])

        def reset(self, observation):
            super().reset(observation)
            for index in range(prefix):
                np.testing.assert_array_equal(self.act(stack(data["frames"], index)), data["actions"][index])
            # Retain the full-precision controller state; the issued float32
            # action alone need not recover its previous steering value exactly.
            self.replayed_previous_steer = self.controller.previous_steer
            if args.arm == "backoff":
                self.controller.speed_cap = changed["speed_cap"]
                self.controller.lateral_acceleration = changed["lateral_acceleration"]

    output = directory / "falsification" / args.arm
    output.mkdir(exist_ok=False)
    budget = Budget(args.plan, "falsification")
    rows, result = trace(plan["split"][manifest["split"]][manifest["case_index"]], args.arm, budget,
        output / "trajectory", max_steps=manifest["rollout_actions"], factory=Warm,
        replay_source=source, prefix=prefix)
    if args.arm == "continue":
        recorded = before[prefix:prefix + len(rows)]
        assert len(rows) == len(recorded)
        assert all(a["state_after"] == b["state_after"] and a["observation_sha256_after"] == b["observation_sha256_after"]
            and np.array_equal(a["action"], b["action"]) for a, b in zip(rows, recorded))
    result.update(arm=args.arm, post_prefix_collision_steps=[r["step"] for r in rows if r["collision"]],
        final_off_track_counter=rows[-1]["off_track_counter"],
        exact_continuation_verified=args.arm == "continue", full_precision_controller_replayed=True,
        no_hidden_state_in_policy=True, scope="partial_causal_branch_not_completion_or_adoption")
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
