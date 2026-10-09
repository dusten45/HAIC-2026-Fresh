"""Frozen archive DEV pairs with shared budgets and preregistered early stops."""

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import resource
import time

import numpy as np

from retry.diagnose import Budget, BudgetStop, make_env
from retry.evaluate import check_window, digest, observation_contract, percentiles
from retry.process_probe import Participant, valid_action


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def stage_count(budget, role):
    with budget.path.open() as handle:
        fcntl.flock(handle, fcntl.LOCK_SH)
        return json.load(handle)["stages"].get(role, 0)


def stop_pair(directory, reason, case_index):
    try:
        with (directory / "stop.json").open("x") as handle:
            json.dump({"at": datetime.now(timezone.utc).isoformat(),
                "reason": reason, "case_index": case_index}, handle)
    except FileExistsError:
        pass


def verify(plan_path, require_window=True):
    plan = json.loads(plan_path.read_text())
    if require_window:
        check_window(plan)
    assert plan["scope"] == "fresh_DEV_validation"
    assert digest(plan_path) == plan_path.with_suffix(".sha256").read_text().split()[0]
    directory, root = plan_path.parent, Path(__file__).resolve().parents[1]
    for name, expected in plan["source_sha256"].items():
        assert digest(root / name) == expected
    split = directory / plan["split_file"]
    assert digest(split) == plan["split_sha256"]
    assert json.loads(split.read_text())["cases"] == plan["cases"]
    for gate in plan["upstream_gates"]:
        source = directory / gate["file"]
        assert digest(source) == gate["sha256"]
        assert json.loads(source.read_text())[gate["key"]]
    for config in plan["roles"].values():
        frozen = directory / config["freeze_file"]
        assert digest(frozen) == config["freeze_sha256"]
        freeze = json.loads(frozen.read_text())
        package = directory / config["package_directory"]
        assert digest(package / "candidate.zip") == config["zip_sha256"] == freeze["zip_sha256"]
        for name, expected in freeze["members_sha256"].items():
            assert digest(package / "extracted" / name) == expected
    return plan


def run(plan_path, plan, role, index):
    directory = plan_path.parent
    assert not (directory / "stop.json").exists(), "Preregistered stop already reached"
    case, config = plan["cases"][index], plan["roles"][role]
    output = directory / "runs" / f"case-{index}" / role
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "started.json", {"at": datetime.now(timezone.utc).isoformat(),
        "plan_sha256": digest(plan_path), "archive_sha256": config["zip_sha256"]})
    child = env = None
    used, max_counter, stop, gate_reason = 0, 0, None, None
    rows, actions, env_times, rss = [], [], [], []
    budget = Budget(plan_path, role)
    stage_before = stage_count(budget, role)
    started = time.perf_counter()
    try:
        package = directory / config["package_directory"] / "extracted"
        child = Participant(Path(__file__).resolve().parents[1] / ".venv/bin/python", package_root=package)
        env = make_env()
        before = time.perf_counter()
        obs, _ = env.reset(seed=case["seed"], options={"track_id": case["track_id"]})
        env_reset_s = time.perf_counter() - before
        geometry = digest_track(env.unwrapped.track)
        assert geometry == case["road_geometry_sha256"], "Actual reset differs from registered source-only geometry"
        initial_observation = hashlib.sha256(obs.tobytes()).hexdigest()
        observation_contract(obs)
        _, reset_s = child.call("reset", obs)
        ended = truncated = False
        for _ in range(plan["max_steps"]):
            if (directory / "stop.json").exists():
                stop = "paired_gate_censored"
                break
            response, elapsed = child.call("act", obs)
            if not valid_action(response) or not (np.all(np.asarray(response["action"]) >= [-1, 0, 0]) and np.all(np.asarray(response["action"]) <= [1, 1, 1])):
                gate_reason = "invalid_action"
                stop_pair(directory, gate_reason, index)
                stop = "paired_gate_censored"
                break
            before = time.perf_counter()
            try:
                obs, _, ended, truncated, info = budget.step(env, np.asarray(response["action"], dtype=np.float32))
            except BudgetStop as error:
                stop = str(error)
                break
            used += 1
            observation_contract(obs)
            actions.append(elapsed)
            env_times.append(time.perf_counter() - before)
            rss.append(response["rss_mib"])
            max_counter = max(max_counter, env.off_track_counter)
            rows.append({"step": used, "progress": info["progress"], "damage": info["damage"],
                "off_track_counter": env.off_track_counter, "collision": info["collision"],
                "terminated": ended, "truncated": truncated, "retire_reason": info["retire_reason"]})
            if role == "candidate":
                if max_counter >= plan["counter_stop"]:
                    gate_reason = "candidate_counter_at_least_limit"
                reference = directory / "runs" / f"case-{index}" / "baseline" / "result.json"
                if reference.exists():
                    old = json.loads(reference.read_text())
                    if not old["censored"]:
                        if env.damage.damage > old["damage"] + plan["individual_damage_margin"] + 1e-9:
                            gate_reason = "candidate_damage_increment_above_margin"
                        if old["completed"] and env.unwrapped.finish_time_s is None:
                            elapsed_lap_ms = (env.unwrapped.t - 1.02) * 1000
                            if elapsed_lap_ms > old["lap_ms"] * plan["individual_lap_ratio_max"]:
                                gate_reason = "candidate_elapsed_lap_above_limit"
                if gate_reason:
                    stop_pair(directory, gate_reason, index)
                    if not (ended or truncated):
                        stop = "paired_gate_censored"
                        break
            if ended or truncated:
                break
        finish = env.unwrapped.finish_time_s
        if finish is None and not (ended or truncated) and used == plan["max_steps"] and stop is None:
            stop = "fixed_horizon_censored"
        censored = stop is not None
        reason = None if finish is not None else stop or ((rows[-1]["retire_reason"] if rows else None) or "max_steps")
        charged = stage_count(budget, role) - stage_before
        assert charged == used
        result = {"case_index": index, "role": role, "scope": "fresh_DEV_validation",
            "completed": finish is not None, "censored": censored,
            "terminal_observed": bool(ended or truncated),
            "steps": used, "charged_actions": charged, "progress": env._calculate_progress(),
            "damage": env.damage.damage, "max_off_track_counter": max_counter,
            "lap_ms": None if finish is None else round((finish - 1.02) * 1000),
            "retire_reason": reason, "gate_reason": gate_reason,
            "invalid_actions": int(gate_reason == "invalid_action"),
            "geometry_sha256": geometry, "initial_observation_sha256": initial_observation,
            "frozen_zip_sha256": config["zip_sha256"], "plan_sha256": digest(plan_path),
            "act_including_IPC": percentiles(actions), "environment_latency": percentiles(env_times),
            "import_init_ms": child.import_init_s * 1000, "participant_reset_ms": reset_s * 1000,
            "environment_reset_s": env_reset_s, "child_peak_RSS_mib": max(rss, default=0),
            "wall_s": time.perf_counter() - started, "harness_peak_RSS_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}
        (output / "metrics.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        write_json(output / "result.json", result)
        print(json.dumps({k: result[k] for k in ["role", "case_index", "completed", "censored", "steps", "damage", "lap_ms", "max_off_track_counter", "retire_reason", "gate_reason"]}), flush=True)
    except Exception as error:
        write_json(output / "failure.json", {"error": repr(error), "charged_actions":
            stage_count(budget, role) - stage_before,
            "role": role, "case_index": index, "policy_changed": False})
        stop_pair(directory, "technical_failure_requires_review", index)
        raise
    finally:
        if child is not None:
            child.close()
        if env is not None:
            env.close()


def digest_track(track):
    return hashlib.sha256(np.asarray(track, dtype="<f8").tobytes(order="C")).hexdigest()


def decide(plan_path, plan):
    directory = plan_path.parent
    counts = {"preserved": [], "new_completion": [], "lost_completion": [], "common_failure": [], "censored": [], "pending": []}
    pairs, hard = [], []
    for index, case in enumerate(plan["cases"]):
        paths = [directory / "runs" / f"case-{index}" / r / "result.json" for r in ["baseline", "candidate"]]
        if not all(p.exists() for p in paths):
            counts["pending"].append(index)
            continue
        old, new = [json.loads(p.read_text()) for p in paths]
        assert old["geometry_sha256"] == new["geometry_sha256"] == case["road_geometry_sha256"]
        assert old["initial_observation_sha256"] == new["initial_observation_sha256"]
        violations = []
        if new["gate_reason"]:
            violations.append(new["gate_reason"])
        if old["censored"] or new["censored"] or not (old["terminal_observed"] and new["terminal_observed"]):
            category = "censored"
        else:
            category = {(True, True): "preserved", (False, True): "new_completion",
                (True, False): "lost_completion", (False, False): "common_failure"}[(old["completed"], new["completed"])]
        counts[category].append(index)
        ratio = new["lap_ms"] / old["lap_ms"] if category == "preserved" else None
        if category == "lost_completion": violations.append("lost_baseline_completion")
        if not old["censored"] and new["damage"] > old["damage"] + plan["individual_damage_margin"] + 1e-9:
            violations.append("damage_increment_above_margin")
        if new["max_off_track_counter"] >= plan["counter_stop"]: violations.append("counter_at_least_limit")
        if new["invalid_actions"]: violations.append("invalid_action")
        if ratio is not None and ratio > plan["individual_lap_ratio_max"]: violations.append("lap_ratio_above_limit")
        if violations: hard.append({"case_index": index, "violations": sorted(set(violations))})
        pairs.append({"case_index": index, "category": category, "baseline": old,
            "candidate": new, "lap_ratio": ratio, "violations": sorted(set(violations))})
    ratios = [p["lap_ratio"] for p in pairs if p["lap_ratio"] is not None]
    common = [p for p in pairs if p["category"] == "preserved"]
    valid = [p for p in pairs if p["category"] != "censored"]
    median_ratio = float(np.median(ratios)) if ratios else None
    damage = {r: float(np.median([p[r]["damage"] for p in valid])) if valid else None for r in ["baseline", "candidate"]}
    common_damage = {r: float(np.median([p[r]["damage"] for p in common])) if common else None for r in ["baseline", "candidate"]}
    complete = not counts["pending"] and not counts["censored"]
    checks = {"all_eight_pairs_terminal": complete, "no_lost_completion": not counts["lost_completion"],
        "candidate_completion_count_not_lower": len(counts["new_completion"]) >= len(counts["lost_completion"]),
        "minimum_common_completions": len(common) >= plan["minimum_common_completions"],
        "median_common_lap_ratio": median_ratio is not None and median_ratio <= plan["median_lap_ratio_max"],
        "median_damage_not_worse": damage["candidate"] is not None and damage["candidate"] <= damage["baseline"] + 1e-9,
        "common_median_damage_not_worse": common_damage["candidate"] is not None and common_damage["candidate"] <= common_damage["baseline"] + 1e-9,
        "no_hard_robustness_violation": not hard}
    verdict = "kill" if hard else "keep" if all(checks.values()) else "inconclusive"
    if hard:
        stop_pair(directory, hard[0]["violations"][0], hard[0]["case_index"])
    decision = {"at": datetime.now(timezone.utc).isoformat(), "scope": "fresh_DEV_validation",
        "verdict": verdict, "gate_pass": all(checks.values()), "checks": checks,
        "completion_categories": counts, "common_completed_pairs": len(common),
        "completion_counts_terminal_pairs": {"baseline": len(counts["preserved"]) + len(counts["lost_completion"]),
            "candidate": len(counts["preserved"]) + len(counts["new_completion"])},
        "median_common_lap_ratio": median_ratio, "median_damage_terminal_pairs": damage,
        "median_damage_common_completion": common_damage, "hard_violations": hard, "pairs": pairs,
        "protected_queries": 0, "champion_promotion": False, "policy_tuned": False}
    write_json(directory / "decision.json", decision)
    print(json.dumps({k: decision[k] for k in ["verdict", "completion_categories", "median_common_lap_ratio", "median_damage_terminal_pairs", "hard_violations"]}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--mode", choices=["run", "decide"], required=True)
    parser.add_argument("--role", choices=["baseline", "candidate"])
    parser.add_argument("--case-index", type=int)
    args = parser.parse_args()
    plan = verify(args.plan, require_window=args.mode == "run")
    if args.mode == "run":
        assert args.role is not None and args.case_index is not None
        run(args.plan, plan, args.role, args.case_index)
    else:
        decide(args.plan, plan)


if __name__ == "__main__":
    main()
