"""One structural pixel correction and a fixed-speed geometry diagnostic."""

import argparse
import json
from pathlib import Path

from retry.anchored_agent import AnchoredAgent
from retry.arc_agent import ArcAgent, arc_target
from retry.diagnose import Budget, onsets, trace
from retry.evaluate import check_window, digest
from retry.ridge_agent import RidgeAgent
from retry.waypoint_agent import WaypointAgent


class OracleGeometry(ArcAgent):
    def act_features(self, truth, observation):
        integral = float(observation[-1, 74:83, 9:14].sum())
        speed = max(0.0, self.speed_gain * integral + self.speed_bias)
        target = arc_target(truth["forward_points_local"], speed, truth["obstacles_local"])
        return self.controller.action_target(float(target[0]), float(target[1]), speed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--mode", choices=["candidate", "geometry"], required=True)
    parser.add_argument("--candidate", choices=["anchored", "ridge", "waypoint"], default="anchored")
    args = parser.parse_args()
    plan, manifest = json.loads(args.plan.read_text()), json.loads(args.manifest.read_text())
    check_window(plan)
    assert digest(args.plan) == manifest["plan_sha256"]
    candidate_path = Path(f"retry/{args.candidate}_agent.py")
    assert digest(candidate_path) == manifest["candidate_sha256"]
    if args.candidate == "ridge":
        assert args.mode == "candidate"
        assert json.loads((args.plan.parent / "ridge-offline-decision.json").read_text())["offline_gate_pass"]
    freeze_path = args.plan.parent / "freeze-v1.json"
    assert digest(freeze_path) == manifest["freeze_sha256"]
    freeze = json.loads(freeze_path.read_text())
    for name, expected in freeze["members_sha256"].items():
        if name.startswith("retry/"):
            assert digest(Path(name)) == expected
    calibration = freeze["calibration"]
    candidate = {"anchored": AnchoredAgent, "ridge": RidgeAgent, "waypoint": WaypointAgent}[args.candidate]
    factory = lambda: (candidate if args.mode == "candidate" else OracleGeometry)(
        calibration["coefficient_speed_per_intensity"], calibration["intercept"])
    output = args.plan.parent / manifest["output"] / args.mode
    output.mkdir(parents=True, exist_ok=False)
    sources = output / "sources"
    sources.mkdir()
    for path in Path(__file__).parent.glob("*.py"):
        (sources / path.name).write_bytes(path.read_bytes())
    (output / "metadata.json").write_text(json.dumps({"manifest_sha256": digest(args.manifest),
        "privileged_input_diagnostic_only": args.mode == "geometry",
        "source_sha256": {p.name: digest(p) for p in sources.glob("*.py")}}, indent=2) + "\n")
    stage = f"{args.candidate}_candidate" if args.mode == "candidate" else "geometry_speed_fixed"
    budget = Budget(args.plan, stage)
    source = args.plan.parent / manifest["reference"]
    assert digest(source / "trace.jsonl") == manifest["reference_trace_sha256"]
    variant = f"{args.candidate}_arc" if args.mode == "candidate" else "oracle_geometry_pixel_speed"
    rows, summary = trace(plan["cases"][manifest["failure_case_index"]], variant,
        budget, output / "branch", max_steps=manifest["rollout_actions"], factory=factory,
        input_source="pixels" if args.mode == "candidate" else "oracle_geometry",
        replay_source=source, prefix=manifest["prefix_actions"])
    records = [{**summary, "onsets": onsets(rows), "final_off_track_counter": rows[-1]["off_track_counter"],
        "scope": "exact_shared_prefix_partial_rollout"}]
    (output / "result.json").write_text(json.dumps(records, indent=2) + "\n")
    if args.mode == "candidate":
        for index in manifest["startup_case_indices"]:
            rows, summary = trace(plan["cases"][index], variant, budget,
                output / f"startup-{index}", max_steps=manifest["startup_actions"], factory=factory)
            records.append({**summary, "onsets": onsets(rows), "scope": "reset_partial_startup"})
            (output / "result.json").write_text(json.dumps(records, indent=2) + "\n")
    branch = records[0]
    rescue = (branch["progress"] - manifest["baseline_progress"] >= manifest["min_progress_gain"]
        and branch["damage"] <= manifest["max_damage"]
        and branch["final_off_track_counter"] < manifest["max_counter_exclusive"])
    startup = args.mode != "candidate" or all(r["steps"] == manifest["startup_actions"]
        and r["progress"] >= manifest["startup_min_progress"] and r["damage"] <= manifest["startup_max_damage"] for r in records[1:])
    decision = {"local_rescue_criterion": rescue, "startup_criterion": startup,
        "candidate_gate_pass": args.mode == "candidate" and rescue and startup,
        "progress_gain": branch["progress"] - manifest["baseline_progress"],
        "deployment_eligible": False, "full_completion_claim": False}
    (output / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision), flush=True)


if __name__ == "__main__":
    main()
