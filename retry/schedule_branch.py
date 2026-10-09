"""One predeclared DEV branch; a passed result is required before full cohorts."""

import argparse
import json
from pathlib import Path

import numpy as np

from retry.diagnose import Budget, trace
from retry.evaluate import check_window, digest
from retry.parameter_probe import guard_reference
from retry.schedule_agent import HazardScheduledAgent
from retry.submission_probe import stack


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    directory, plan = args.plan.parent, json.loads(args.plan.read_text())
    check_window(plan)
    assert digest(args.plan) == args.plan.with_suffix(".sha256").read_text().split()[0]
    assert digest(Path(__file__).parent / "schedule_agent.py") == plan["schedule_source_sha256"]
    freeze, _ = guard_reference(plan, directory)
    c = freeze["calibration"]
    task, p = plan["branch_task"], plan["schedule_parameters"]
    source = directory / task["source"]
    assert source.resolve().is_relative_to(directory.resolve())
    assert digest(source / "trace.jsonl") == task["trace_sha256"]
    data = np.load(source / "pixels-actions.npz")
    saved = [json.loads(x) for x in (source / "trace.jsonl").read_text().splitlines()]
    prefix = task["prefix_actions"]

    class Warm(HazardScheduledAgent):
        def __init__(self):
            super().__init__(c["coefficient_speed_per_intensity"], c["intercept"],
                p["speed_cap"], p["lateral_fast"], p["lateral_safe"])

        def reset(self, observation):
            super().reset(observation)
            self.warming_fixed_reference = True
            for index in range(prefix):
                np.testing.assert_array_equal(self.act(stack(data["frames"], index)), data["actions"][index])
            self.replayed_previous_steer = self.controller.previous_steer
            self.warming_fixed_reference = False

    output = directory / "schedule/local-branch"
    rows, result = trace(plan["split"]["SCREEN"][task["case_index"]], "hazard_scheduled_local", Budget(args.plan, "schedule_branch"),
        output, max_steps=task["rollout_actions"], factory=Warm, replay_source=source, prefix=prefix)
    control = json.loads((directory / task["matched_control_result"]).read_text())
    assert digest(directory / task["matched_control_result"]) == task["matched_control_sha256"]
    assert control["exact_continuation_verified"]
    start = saved[prefix - 1]["progress"]
    retention = (result["progress"] - start) / (control["progress"] - start)
    result.update(progress_increment_retention_vs_fast=retention,
        damage_reduction_vs_fast=control["damage"] - result["damage"], final_off_track_counter=rows[-1]["off_track_counter"],
        local_gate_pass=retention >= 0.9 and control["damage"] - result["damage"] >= 0.2 - 1e-6 and rows[-1]["off_track_counter"] < 10,
        scope="one partial DEV contrast; no protected data or full completion claim", new_simulation_actions=prefix + len(rows))
    (directory / "schedule/local-decision.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["progress", "damage", "progress_increment_retention_vs_fast", "damage_reduction_vs_fast", "local_gate_pass"]}), flush=True)


if __name__ == "__main__":
    main()
