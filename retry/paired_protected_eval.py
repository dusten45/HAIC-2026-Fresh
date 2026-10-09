"""One preregistered paired protected comparison; metrics only, no diagnostic traces."""

import argparse
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import time

import numpy as np

from retry.connectivity_probe import verify_reference
from retry.diagnose import Budget, BudgetStop, make_env
from retry.evaluate import check_window, digest, observation_contract, percentiles
from retry.process_probe import Participant, valid_action


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def pool_name(plan):
    return plan.get("pool_name", "HOLDOUT_B")


def verify(plan_path):
    plan = json.loads(plan_path.read_text())
    check_window(plan)
    assert digest(plan_path) == plan_path.with_suffix(".sha256").read_text().split()[0]
    directory, root = plan_path.parent, Path(__file__).resolve().parents[1]
    for name, expected in plan["source_sha256"].items():
        assert digest(root / name) == expected
    reference_plan_path = directory / plan["reference_plan"]
    assert digest(reference_plan_path) == plan["reference_plan_sha256"]
    reference_plan = json.loads(reference_plan_path.read_text())
    if plan.get("reference_guard") == "parameter":
        from retry.parameter_probe import guard_reference
        guard_reference(reference_plan, directory)
    else:
        verify_reference(reference_plan, directory)
    preservation = json.loads((directory.parent / "preservation.json").read_text())
    for name, expected in preservation["files"].items():
        assert digest(root / name) == expected
    prior = directory / plan["upstream_decision"]
    assert digest(prior) == plan["upstream_decision_sha256"]
    assert json.loads(prior.read_text())[plan.get("upstream_gate", "E_DEV_preservation_pass")]
    for gate in plan.get("additional_gates", []):
        source = directory / gate["file"]
        assert digest(source) == gate["sha256"]
        assert json.loads(source.read_text())[gate["key"]]
    reservation = directory / plan["reservation_file"]
    assert digest(reservation) == plan["reservation_sha256"]
    registry = json.loads(reservation.read_text())
    assert registry[pool_name(plan)]["status"] == "reserved_unopened"
    assert registry[pool_name(plan)]["cases"] == plan["cases"]
    original = json.loads((directory.parent / "preregistered-v1.json").read_text())
    used_ids = {(c["track_id"], c["seed"]) for cases in original["split"].values() for c in cases}
    assert not used_ids.intersection((c["track_id"], c["seed"]) for c in plan["cases"])
    excluded = {(c["track_id"], c["seed"]) for c in plan.get("additional_identity_exclusions", [])}
    assert not excluded.intersection((c["track_id"], c["seed"]) for c in plan["cases"])
    assert len(set((c["track_id"], c["seed"]) for c in plan["cases"])) == 16
    for role, config in plan["roles"].items():
        frozen = directory / config["freeze_file"]
        assert digest(frozen) == config["freeze_sha256"]
        freeze = json.loads(frozen.read_text())
        package = (directory / config["package_directory"]).resolve()
        assert package.is_relative_to(directory.parent)
        assert digest(package / "candidate.zip") == config["zip_sha256"] == freeze["zip_sha256"]
        for name, expected in freeze["members_sha256"].items():
            assert digest(package / "extracted" / name) == expected
    return plan


def claim(plan_path, plan, role=None, case_index=None):
    registry_path = (plan_path.parent / plan["query_ledger"]).resolve()
    with registry_path.open("r+") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        registry = json.load(handle)
        pool = pool_name(plan)
        block = registry[pool]
        stamp = datetime.now(timezone.utc).isoformat()
        if role is None:
            assert block["status"] == "reserved_unopened" and block["episode_queries_used"] == 0
            if "prepare_min_actions_left" in plan:
                ledger = json.loads((plan_path.parent / plan["ledger_relative_path"]).read_text())
                assert plan["max_actions"] - ledger["actions"] >= plan["prepare_min_actions_left"]
                wall_left = ledger["started_epoch"] + plan["max_experiment_wall_s"] - time.time()
                assert wall_left >= plan["prepare_min_wall_s_left"]
            with (plan_path.parent / f"{pool}.opened").open("x") as marker:
                json.dump({"at": stamp, "plan_sha256": digest(plan_path),
                    "versions": {r: c["zip_sha256"] for r, c in plan["roles"].items()}}, marker)
            block.update(status="opened_once_no_retries", comparison_batches_used=1,
                plan_sha256=digest(plan_path), episode_claims=[], metric_read_accesses=[])
        else:
            assert block["plan_sha256"] == digest(plan_path)
            assert block["episode_queries_used"] < block["episode_queries_max"] == 32
            assert not any(x["role"] == role and x["case_index"] == case_index for x in block["episode_claims"])
            assert sum(x["role"] == role for x in block["episode_claims"]) < 16
            block["episode_claims"].append({"role": role, "case_index": case_index,
                "at": stamp, "zip_sha256": plan["roles"][role]["zip_sha256"]})
            block["episode_queries_used"] += 1
        handle.seek(0)
        json.dump(registry, handle, indent=2)
        handle.truncate()
        handle.flush()


def run_role(plan_path, plan, role):
    directory = plan_path.parent
    pool = pool_name(plan)
    marker = json.loads((directory / f"{pool}.opened").read_text())
    assert marker["plan_sha256"] == digest(plan_path)
    with (directory / f"{pool}.{role}.started").open("x") as handle:
        json.dump({"at": datetime.now(timezone.utc).isoformat()}, handle)
    output = directory / pool / role
    output.mkdir()
    config = plan["roles"][role]
    package = (directory / config["package_directory"]).resolve()
    root = Path(__file__).resolve().parents[1]
    budget = Budget(plan_path, config.get("budget_stage", f"{pool}_{role}"))
    records = []
    for index, case in enumerate(plan["cases"]):
        check_window(plan)
        claim(plan_path, plan, role, index)  # Crashed or interrupted episodes also consume a query.
        child, env = None, None
        started, used, stop = time.perf_counter(), 0, None
        act_times, env_times, rss = [], [], []
        try:
            child = Participant(root / ".venv/bin/python", package_root=package / "extracted")
            env = make_env()
            obs, _ = env.reset(seed=case["seed"], options={"track_id": case["track_id"]})
            observation_contract(obs)
            _, reset_s = child.call("reset", obs)
            for _ in range(plan["max_steps"]):
                check_window(plan)
                response, elapsed = child.call("act", obs)
                assert valid_action(response), "Protected comparison invalid action"
                before = time.perf_counter()
                try:
                    obs, _, ended, truncated, info = budget.step(env, np.asarray(response["action"], dtype=np.float32))
                except BudgetStop as error:
                    stop = str(error)
                    break
                used += 1
                observation_contract(obs)
                act_times.append(elapsed)
                env_times.append(time.perf_counter() - before)
                rss.append(response["rss_mib"])
                if ended or truncated:
                    break
            finish = env.unwrapped.finish_time_s
            result = {"case_index": index, "role": role, "completed": finish is not None,
                "steps": used, "progress": env._calculate_progress(), "damage": env.damage.damage,
                "lap_ms": None if finish is None else round((finish - 1.02) * 1000),
                "retire_reason": None if finish is not None else stop or (info["retire_reason"] if used else "no_actions") or "max_steps",
                "act_including_IPC": percentiles(act_times), "environment_latency": percentiles(env_times),
                "import_init_ms": child.import_init_s * 1000, "reset_ms": reset_s * 1000,
                "child_peak_rss_mib": max(rss, default=0), "wall_s": time.perf_counter() - started,
                "invalid_actions": 0, "frozen_zip_sha256": config["zip_sha256"]}
            records.append(result)
            write_json(output / "result.json", records)
            print(json.dumps({k: result[k] for k in ["role", "case_index", "completed", "steps", "damage", "lap_ms", "retire_reason"]}), flush=True)
            if stop:
                break
        except Exception as error:
            write_json(output / "failure.json", {"case_index": index, "queries_consumed": True,
                "error": str(error), "retry_allowed": False})
            raise
        finally:
            if child is not None:
                child.close()
            if env is not None:
                env.close()


def decide(plan_path, plan):
    directory, roles = plan_path.parent, {}
    pool = pool_name(plan)
    registry_path = directory / plan["query_ledger"]
    with registry_path.open("r+") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        registry = json.load(handle)
        registry[pool]["metric_read_accesses"].append({"at": datetime.now(timezone.utc).isoformat(), "purpose": "single_preregistered_paired_adoption_decision"})
        handle.seek(0)
        json.dump(registry, handle, indent=2)
        handle.truncate()
    for role in plan["roles"]:
        records = json.loads((directory / pool / role / "result.json").read_text())
        assert [r["case_index"] for r in records] == list(range(16))
        assert all(r["frozen_zip_sha256"] == plan["roles"][role]["zip_sha256"] for r in records)
        roles[role] = records
    base, new = roles["baseline"], roles["challenger"]
    common = [(a, b) for a, b in zip(base, new) if a["completed"] and b["completed"]]
    lost = [a["case_index"] for a, b in zip(base, new) if a["completed"] and not b["completed"]]
    repaired = [a["case_index"] for a, b in zip(base, new) if not a["completed"] and b["completed"]]
    counts = {r: sum(x["completed"] for x in rows) for r, rows in roles.items()}
    damages = {r: float(np.median([x["damage"] for x in rows])) for r, rows in roles.items()}
    deltas = [b["lap_ms"] - a["lap_ms"] for a, b in common]
    median_delta = float(np.median(deltas)) if deltas else None
    ratios = [b["lap_ms"] / a["lap_ms"] for a, b in common]
    median_ratio = float(np.median(ratios)) if ratios else None
    if counts["challenger"] > counts["baseline"]:
        lap_pass = "more_completion_max_lap_ratio" not in plan or (median_ratio is not None and median_ratio <= plan["more_completion_max_lap_ratio"])
    else:
        lap_pass = (median_ratio is not None and median_ratio <= plan["equal_completion_max_lap_ratio"]) if "equal_completion_max_lap_ratio" in plan else (median_delta is not None and median_delta <= 0)
    passed = (counts["challenger"] >= plan["minimum_completions"] and not lost
        and damages["challenger"] <= damages["baseline"] + plan["damage_margin"]
        and all(x["invalid_actions"] == 0 for rows in roles.values() for x in rows)
        and lap_pass)
    decision = {plan.get("decision_key", "E_HOLD_B_pass"): bool(passed), "selected_role": "challenger" if passed else "baseline",
        "completions": counts, "median_damage": damages, "lost_baseline_completion_indices": lost,
        "repaired_completion_indices": repaired, "common_completed_pairs": len(common),
        "paired_lap_delta_ms": deltas, "median_paired_lap_delta_ms": median_delta,
        "pool": pool, "paired_lap_ratios": ratios, "median_paired_lap_ratio": median_ratio,
        "cases_per_role": 16, "episode_queries_consumed": 32, "split_reuse_allowed": False,
        "policy_changed_after_query": False, "SEALED_opened": False,
        "official_server_parity_verified": False, "deployment_eligible": False,
        "plan_sha256": digest(plan_path)}
    with (directory / pool / "decision.json").open("x") as handle:
        json.dump(decision, handle, indent=2)
    print(json.dumps(decision), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--mode", choices=["prepare", "baseline", "challenger", "decide"], required=True)
    args = parser.parse_args()
    plan = verify(args.plan)
    if args.mode == "prepare":
        claim(args.plan, plan)
        output = args.plan.parent / pool_name(plan)
        output.mkdir(exist_ok=False)
        sources = output / "sources"
        sources.mkdir()
        for name in plan["source_sha256"]:
            (sources / Path(name).name).write_bytes(Path(name).read_bytes())
        write_json(output / "metadata.json", {"plan_sha256": digest(args.plan),
            "records_diagnostic_truth_or_pixels": False, "source_sha256": plan["source_sha256"],
            "version_count": 2, "comparison_batches": 1, "retries_allowed": False})
    elif args.mode == "decide":
        decide(args.plan, plan)
    else:
        run_role(args.plan, plan, args.mode)


if __name__ == "__main__":
    main()
