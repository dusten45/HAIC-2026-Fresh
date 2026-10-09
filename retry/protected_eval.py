"""One locked protected-split run; collect metrics without diagnostic truth/images."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time

import numpy as np

from retry.diagnose import Budget, BudgetStop, make_env
from retry.evaluate import check_window, digest, observation_contract, percentiles
from retry.process_probe import Participant, valid_action


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    check_window(plan)
    study = args.plan.parent.parent.resolve()
    original = study / "preregistered-v1.json"
    assert digest(original) == plan["original_plan_sha256"]
    declared = json.loads(original.read_text())["split"]
    assert plan["split"] == "HOLDOUT" and plan["cases"] == declared["HOLDOUT"]
    identities = [{(c["track_id"], c["seed"]) for c in declared[s]} for s in ["DEV", "HOLDOUT", "SEALED"]]
    assert all(not identities[a].intersection(identities[b]) for a, b in [(0, 1), (0, 2), (1, 2)])
    upstream = (args.plan.parent / plan["upstream_decision"]).resolve()
    assert digest(upstream) == plan["upstream_decision_sha256"]
    assert json.loads(upstream.read_text())["G2_pass"]
    freeze_path = (args.plan.parent / plan["freeze_file"]).resolve()
    assert digest(freeze_path) == plan["freeze_sha256"]
    freeze = json.loads(freeze_path.read_text())
    package = (args.plan.parent / plan["package_directory"]).resolve()
    assert package.is_relative_to(study) and freeze_path.is_relative_to(study)
    assert digest(package / "candidate.zip") == freeze["zip_sha256"]
    for name, expected in freeze["members_sha256"].items():
        assert digest(package / "extracted" / name) == expected
    root = Path(__file__).resolve().parents[1]
    preservation = json.loads((study / "preservation.json").read_text())
    for name, expected in preservation["files"].items():
        assert digest(root / name) == expected
    # Shared with the original evaluator: a crash also consumes this split opening.
    with (study / "HOLDOUT.opened").open("x") as handle:
        json.dump({"opened_at": datetime.now(timezone.utc).isoformat(),
            "plan_sha256": digest(args.plan), "frozen_zip_sha256": freeze["zip_sha256"]}, handle)
    output = args.plan.parent / "HOLDOUT"
    output.mkdir(exist_ok=False)
    sources = output / "sources"
    sources.mkdir()
    for path in Path(__file__).parent.glob("*.py"):
        (sources / path.name).write_bytes(path.read_bytes())
    (output / "metadata.json").write_text(json.dumps({"plan_sha256": digest(args.plan),
        "frozen_zip_sha256": freeze["zip_sha256"], "scope": "full_locked_HOLDOUT_once",
        "records_diagnostic_truth_or_pixels": False,
        "source_sha256": {p.name: digest(p) for p in sources.glob("*.py")}}, indent=2) + "\n")
    budget = Budget(args.plan, "HOLDOUT")
    records = []
    for index, case in enumerate(plan["cases"]):
        check_window(plan)
        child = Participant(root / ".venv/bin/python", package_root=package / "extracted")
        env = make_env()
        started = time.perf_counter()
        act_times, env_times, rss, used, stop = [], [], [], 0, None
        try:
            obs, _ = env.reset(seed=case["seed"], options={"track_id": case["track_id"]})
            observation_contract(obs)
            _, reset_s = child.call("reset", obs)
            for _ in range(plan["max_steps"]):
                check_window(plan)
                response, elapsed = child.call("act", obs)
                assert valid_action(response), "Protected-run invalid action"
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
            result = {**case, "HOLDOUT_index": index, "completed": finish is not None,
                "steps": used, "progress": env._calculate_progress(), "damage": env.damage.damage,
                "lap_ms": None if finish is None else round((finish - 1.02) * 1000),
                "retire_reason": None if finish is not None else stop or (info["retire_reason"] if used else "no_actions") or "max_steps",
                "act_including_IPC": percentiles(act_times), "environment_latency": percentiles(env_times),
                "import_init_ms": child.import_init_s * 1000, "reset_ms": reset_s * 1000,
                "child_peak_rss_mib": max(rss, default=0), "wall_s": time.perf_counter() - started,
                "invalid_actions": 0, "frozen_zip_sha256": freeze["zip_sha256"],
                "scope": "full_reset_finish_or_retirement_max2000"}
            records.append(result)
            (output / "result.json").write_text(json.dumps(records, indent=2) + "\n")
            print(json.dumps({k: result[k] for k in ["HOLDOUT_index", "completed", "steps", "progress", "damage", "lap_ms", "retire_reason"]}), flush=True)
            if stop:
                break
        finally:
            child.close()
            env.close()
    decision = {"cases": len(records), "completions": sum(r["completed"] for r in records),
        "median_progress": float(np.median([r["progress"] for r in records])),
        "median_damage": float(np.median([r["damage"] for r in records])), "invalid_actions": 0,
        "G3_pass": len(records) == 8 and sum(r["completed"] for r in records) >= 6,
        "policy_changed": False, "split_opened_once": True, "SEALED_opened": False,
        "official_server_parity_verified": False, "deployment_eligible": False}
    (output / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision), flush=True)


if __name__ == "__main__":
    main()
