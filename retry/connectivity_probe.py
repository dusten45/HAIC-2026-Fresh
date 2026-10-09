"""Two fixed causal contrasts with exact physics and observed-history prefixes."""

import argparse
import json
from pathlib import Path

import numpy as np

from retry.connected_agent import ConnectedTemporalAgent, connected_route, routing_problem
from retry.diagnose import Budget, onsets, trace
from retry.evaluate import check_window, digest
from retry.route_agent import safe_route
from retry.temporal_agent import TemporalRouteAgent


def verify_reference(plan, directory):
    freeze_path = (directory / plan["baseline_freeze_file"]).resolve()
    assert digest(freeze_path) == plan["baseline_freeze_sha256"]
    freeze = json.loads(freeze_path.read_text())
    package = (directory / plan["baseline_package"]).resolve()
    assert digest(package / "candidate.zip") == plan["baseline_zip_sha256"]
    for name, expected in freeze["members_sha256"].items():
        assert digest(package / "extracted" / name) == expected
        if name.startswith("retry/"):
            assert digest(Path(name)) == expected
    return freeze


def warm_agent(base, gain, bias, frames, prefix):
    class WarmAgent(base):
        def reset(self, observation):
            super().reset(observation)
            # Only the actual observed images preceding the frozen prefix action
            # enter memory. The environment's hidden state never enters policy.
            for frame in frames[:prefix]:
                image = frame.astype(np.float32) / 255
                speed = max(0.0, gain * float(image[74:83, 9:14].sum()) + bias)
                self.tracked_obstacles(image, speed)
    return WarmAgent(gain, bias)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--mode", choices=["diagnose", "baseline", "component"], required=True)
    args = parser.parse_args()
    plan, manifest = json.loads(args.plan.read_text()), json.loads(args.manifest.read_text())
    check_window(plan)
    assert digest(args.plan) == manifest["plan_sha256"]
    assert digest(Path("retry/connected_agent.py")) == manifest["candidate_sha256"]
    freeze = verify_reference(plan, args.plan.parent)
    c = freeze["calibration"]
    gain, bias = c["coefficient_speed_per_intensity"], c["intercept"]
    output = args.plan.parent / args.mode
    output.mkdir(exist_ok=False)
    sources = output / "sources"
    sources.mkdir()
    for p in Path(__file__).parent.glob("*.py"):
        (sources / p.name).write_bytes(p.read_bytes())
    (output / "metadata.json").write_text(json.dumps({"plan_sha256": digest(args.plan),
        "manifest_sha256": digest(args.manifest), "baseline_zip_sha256": plan["baseline_zip_sha256"],
        "source_sha256": {p.name: digest(p) for p in sources.glob("*.py")}}, indent=2) + "\n")
    records = []
    for task in plan["branch_tasks"]:
        source = (args.plan.parent / task["reference"]).resolve()
        assert digest(source / "trace.jsonl") == task["reference_trace_sha256"]
        reference = [json.loads(x) for x in (source / "trace.jsonl").read_text().splitlines()]
        frames = np.load(source / "pixels-actions.npz")["frames"]
        if args.mode == "diagnose":
            agent = TemporalRouteAgent(gain, bias)
            agent.reset(np.stack([frames[0]] * 4).astype(np.float32) / 255)
            samples, streak = [], 0
            for index, row in enumerate(reference):
                obs = np.asarray([frames[max(0, index - j)] for j in [3, 2, 1, 0]], np.float32) / 255
                action = agent.act(obs)
                assert np.array_equal(action, row["action"])
                missing = action[1] == 0 and action[2] == 0.25
                streak = streak + 1 if missing else 0
                if streak not in [1, 10, 100]:
                    continue
                hazards = [h[:3] for h in agent.hazards]
                allowed, _, start, old, new, labels = routing_problem(obs[-1], hazards)
                old_reachable = start is not None and old is not None and labels[start] == labels[old]
                new_path = connected_route(obs[-1], hazards)
                samples.append({"step": index + 1, "missing_streak": streak, "damage": row["damage"],
                    "progress": row["progress"], "speed_m_s_diagnostic": row["truth"]["speed_m_s"],
                    "true_nearest_obstacle_m_diagnostic": row["truth"]["nearest_obstacle_distance_m"],
                    "start": start, "legacy_goal": old, "reachable_goal": new,
                    "legacy_goal_reachable_no_corner_cutting": bool(old_reachable),
                    "legacy_path_empty": not safe_route(obs[-1], hazards),
                    "legacy_path_empty_without_obstacle_inflation": not safe_route(obs[-1], []),
                    "reachable_path_points": len(new_path), "hazards": agent.hazards})
            records.append({"DEV_index": task["case_index"], "entire_reference_action_sequence_exact": True,
                "samples": samples, "new_simulation_actions": 0})
        else:
            budget = Budget(args.plan, f"connectivity_{args.mode}")
            base = TemporalRouteAgent if args.mode == "baseline" else ConnectedTemporalAgent
            rows, summary = trace(plan["cases"][task["case_index"]], args.mode, budget,
                output / f"case-{task['case_index']}", max_steps=task["rollout_actions"],
                factory=lambda: warm_agent(base, gain, bias, frames, task["prefix_actions"]),
                replay_source=source, prefix=task["prefix_actions"])
            record = {**summary, "DEV_index": task["case_index"], "onsets": onsets(rows),
                "observed_history_warmed_actions": task["prefix_actions"],
                "final_off_track_counter": rows[-1]["off_track_counter"],
                "progress_gain_vs_frozen_endpoint": summary["progress"] - task["baseline_final_progress"],
                "scope": "exact_physics_and_observed_history_prefix_partial_rollout"}
            if args.mode == "baseline":
                paired = reference[task["prefix_actions"]:task["prefix_actions"] + len(rows)]
                assert all(a["state_after"] == b["state_after"] and a["observation_sha256_after"] == b["observation_sha256_after"]
                    and np.array_equal(a["action"], b["action"]) for a, b in zip(rows, paired))
                assert len(rows) == len(paired)
                record["entire_baseline_continuation_exact"] = True
            else:
                record["local_gate_pass"] = record["progress_gain_vs_frozen_endpoint"] >= 0.08 and summary["damage"] <= 0.4 and record["final_off_track_counter"] < 10
            records.append(record)
        (output / "result.json").write_text(json.dumps(records, indent=2) + "\n")
    if args.mode == "component":
        decision = {"cases": len(records), "passes": sum(r["local_gate_pass"] for r in records),
            "local_gate_pass": len(records) == 2 and all(r["local_gate_pass"] for r in records),
            "deployment_eligible": False, "full_completion_claim": False}
        (output / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")
        print(json.dumps(decision), flush=True)
    verify_reference(plan, args.plan.parent)


if __name__ == "__main__":
    main()
