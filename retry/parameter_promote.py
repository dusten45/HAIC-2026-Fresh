"""Conditional parameter gates; never retune a version after validation opens."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path

from retry.evaluate import check_window, digest
from retry.parameter_probe import guard_reference
from retry.parameter_search import assess, ranking, run_job, save


def stable(record, baseline):
    baseline_count = sum(r["completed"] for r in baseline)
    ratios = record["lap_ratios"]
    return bool(record["feasible"] and record["completions"] >= 6 and ratios and (
        (record["completions"] > baseline_count and record["median_lap_ratio"] <= 1.02) or
        (record["completions"] == baseline_count and record["median_lap_ratio"] <= 0.97 and max(ratios) <= 1.05)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--mode", choices=["validate", "package-plan", "preserve"], required=True)
    args = parser.parse_args()
    directory, plan = args.plan.parent, json.loads(args.plan.read_text())
    check_window(plan)
    freeze, _ = guard_reference(plan, directory)
    screen = json.loads((directory / "winners/decision.json").read_text())
    assert screen["deeper_gate_pass"]
    selected = screen["selected"]
    if args.mode == "validate":
        with (directory / "VALIDATE.opened").open("x") as handle:
            json.dump({"at": datetime.now(timezone.utc).isoformat(), "selected_parameters": selected["parameters"],
                "selected_id": selected["id"], "source_sha256": digest(Path(__file__).parent / "parameter_agent.py"),
                "selection_sha256": digest(directory / "winners/decision.json"), "retuning_or_reopening_allowed": False}, handle)
        (directory / "validation").mkdir(exist_ok=False)
        def one(role):
            return run_job(args.plan, {"id": "validation-" + role, "kind": "baseline" if role == "baseline" else "parameter",
                "split": "VALIDATE", "stage": "validation_baseline" if role == "baseline" else "validation_candidate",
                "case_indices": list(range(8)), "output": "validation/" + role,
                "parameters": plan["default_parameters"] if role == "baseline" else selected["parameters"]})
        with ThreadPoolExecutor(max_workers=2) as pool:
            rows = dict(zip(["baseline", "candidate"], pool.map(one, ["baseline", "candidate"])))
        result = assess(rows["candidate"], rows["baseline"], selected["id"], selected["parameters"])
        result["validation_gate_pass"] = stable(result, rows["baseline"])
        result["baseline_completions"] = sum(r["completed"] for r in rows["baseline"])
        result["version_changed_after_opening"] = False
        result["protected_pool_used"] = False
        save(directory / "validation/decision.json", result)
        print(json.dumps({k: result[k] for k in ["id", "completions", "baseline_completions", "median_lap_ratio", "lost_baseline_completions", "validation_gate_pass"]}), flush=True)
    elif args.mode == "package-plan":
        validated = directory / "validation/decision.json"
        decision = json.loads(validated.read_text())
        assert decision["validation_gate_pass"]
        package_plan = dict(plan)
        package_plan.update(id=plan["id"] + "-package-v1", parent_plan_sha256=digest(args.plan),
            validation_decision="validation/decision.json", validation_decision_sha256=digest(validated),
            parameter_source_sha256=digest(Path(__file__).parent / "parameter_agent.py"), parameters=selected["parameters"],
            pixel_speed_calibration=freeze["calibration"], cases=plan["split"]["VALIDATE"],
            submission_output="submission", submission_trace="validation/candidate/case-0", submission_budget_stage="submission",
            submission_check={"local_runner_case_index": 0, "max_steps": 128},
            registered_at=datetime.now(timezone.utc).isoformat())
        path = directory / "package-preregistered-v1.json"
        assert not path.exists()
        save(path, package_plan)
        path.with_suffix(".sha256").write_text(digest(path) + "\n")
        print(json.dumps({"package_plan_sha256": digest(path), "parameters": selected["parameters"]}), flush=True)
    else:
        validated = json.loads((directory / "validation/decision.json").read_text())
        assert validated["validation_gate_pass"]
        submission = json.loads((directory / "submission/result.json").read_text())
        assert submission["local_submission_path_passed"]
        frozen_path = directory / "freeze-parameters-v1.json"
        frozen = json.loads(frozen_path.read_text())
        rows = run_job(args.plan, {"id": "original-DEV-preservation", "kind": "frozen_challenger", "split": "OLD_DEV",
            "stage": "original_DEV_preservation", "case_indices": list(range(8)), "output": "original-DEV-preservation",
            "parameters": selected["parameters"], "freeze_file": frozen_path.name, "freeze_sha256": digest(frozen_path),
            "package_directory": "submission"})
        baseline = json.loads((directory.parent / "stage8/full-DEV/result.json").read_text())
        baseline = [{**r, "case_index": r["DEV_index"]} for r in baseline]
        result = assess(rows, baseline, selected["id"], selected["parameters"])
        result["original_preservation_gate_pass"] = not result["lost_baseline_completions"] and result["completions"] == 8 and result["median_damage"] <= 0.4
        result["frozen_zip_sha256"] = frozen["zip_sha256"]
        save(directory / "original-preservation-decision.json", result)
        print(json.dumps({k: result[k] for k in ["id", "completions", "median_lap_ratio", "lost_baseline_completions", "original_preservation_gate_pass"]}), flush=True)


if __name__ == "__main__":
    main()
