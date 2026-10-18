"""Static recovery inventory; never imports research modules or starts physics.

This reads fixed public receipts and explicitly named workspace locations only.
It does not search the host, contact accounts, reconstruct inputs, or transfer files.
Network/account observations are recorded separately in recovery502_result.md.
"""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time


G = Path(__file__).resolve().parents[1]
REFERENCE = "e0755373b9b4dfd6ae87c762e2e21bf846db4938"
MAIN = "dfb7a2de2178825ca5c5ce20bab01ba67052ba31"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=G)


def public_json(name):
    return json.loads(git("show", REFERENCE + ":retry/" + name))


def inventory():
    start, cpu = time.perf_counter(), time.process_time()
    retention = public_json("screen501_retention.json")
    contract = public_json("screen501_contract.json")
    frozen_checks = {}
    for name, expected in contract["frozen_code_pins"].items():
        path = G / "retry" / name
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        frozen_checks[str(path.relative_to(G))] = {
            "expected_sha256": expected,
            "actual_sha256": actual,
            "match": actual == expected,
        }
    published_checks = {}
    for name, expected in retention["public_files"].items():
        data = (G / name).read_bytes()
        published_checks[name] = {
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "match": len(data) == expected["bytes"]
            and hashlib.sha256(data).hexdigest() == expected["sha256"],
        }
    private = Path("/workspace/haic-private-retry-20261009")
    # Names are already public in run501/law473. No contents are read here.
    required = {
        "501_raw": Path("/tmp/haic-retry-stage501-private"),
        "501_control_and_retention": private / "stage501",
        "501_source_binding": private / "stage501-source-private",
        "frozen_line_and_model": private / "stage269/N1-plan-private.json",
        "frozen_pace": private / "stage404/profiles-private.json",
        "frozen_projection": private / "stage466-numeric-recovery1/projection-and-segments-private.json",
        "original_pre23_native_receipts": private / "stage453",
        "original_factual472": private / "stage472",
        "original_model473": private / "stage473",
        "private_budget_authority": private / "project-effective-budget-v495.json",
    }
    mounts = {}
    for path in (Path("/workspace/library-files"), Path("/workspace/scratch"),
                 Path("/workspace/shared/downloads")):
        mounts[str(path)] = {
            "exists": path.is_dir(),
            "direct_file_count": sum(p.is_file() for p in path.iterdir())
            if path.is_dir() else None,
        }
    names = git("ls-tree", "-r", "--name-only", REFERENCE).decode().splitlines()
    correction = git("show", REFERENCE + ":retry/diagnostic497_correction.md").decode()
    result = {
        "scope": "RECOVERY_INVESTIGATION_ONLY_NOT_502_TRANSITION_ANALYSIS",
        "observed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "public_reference": REFERENCE,
        "main_expected": MAIN,
        "main_ref_unchanged": git("rev-parse", "refs/heads/main").decode().strip() == MAIN,
        "authorization_deadline_KST": contract["authorization_deadline_KST"],
        "public497_correction_confirms_Oct20": "2026-10-20 19:01:55 KST" in correction,
        "private_authorization_original_recovered": False,
        "frozen_code_checks": frozen_checks,
        "published_receipt_checks": published_checks,
        "all_public_pins_match": all(x["match"] for x in [*frozen_checks.values(), *published_checks.values()]),
        "required_private_locations_present": {k: p.exists() for k, p in required.items()},
        "named_upload_locations": mounts,
        "tracked_workflow_files_at_reference": sum(n.startswith(".github/workflows/") for n in names),
        "tracked_501_package_files": [n for n in names if n.startswith("retry/") and "501" in Path(n).name],
        "historical_501_raw_receipt_only": {
            "files": retention["raw_files"], "bytes": retention["raw_bytes"],
            "private_manifest_sha256": retention["private_audit_sha256"],
            "raw_available_now": False,
            "receipt_is_not_a_backup": True,
        },
        "historical463_backup_receipt_only": {
            "archive_bytes": public_json("transfer463_retention.json")["archive_bytes"],
            "currently_accessible_archive_identified": False,
        },
        "transition_analysis502": "NOT_PERFORMED_MISSING_ORIGINAL_RAW_AND_PRIVATE_INPUTS",
        "original_experiment_reconstruction_from_public_only": "NOT_POSSIBLE",
        "no_proof_of_global_backup_absence": True,
        "worlds_resets_integrations_seed_generation_tuning": 0,
        "raw_transfers_uploads_downloads": 0,
        "research_balance_recorded_publicly": 26027,
        "reserve_recorded_publicly": 84000,
        "private_budget_ledger_recovered_or_rewritten": False,
        "new_action_debit": 0,
        "conditional_future_source_smoke_proposal_NOT_AUTHORIZED_OR_EXECUTED": {
            "requires": ["user-provided confirmed DEV case and private frozen controller inputs",
                         "reconciled authoritative budget and exposure/split records",
                         "separate preregistration and permission for new physics",
                         "user-operated persistent private preservation before further work"],
            "native_reset_cap": 1,
            "native_wrapper_action_cap": 38,
            "native_prefix_actions": 22,
            "recorded_calibration_suffix_actions": 16,
            "native_raw_tick_cap_including_51_reset_ticks": 203,
            "model_world_cap": 1,
            "model_replay_holds_cap": 16,
            "model_raw_tick_cap": 64,
            "action_balance_if_full_cap_charged": 25989,
            "reserve_used": 0,
            "suggested_CPU_s_cap": 120,
            "suggested_wall_s_cap": 180,
            "suggested_raw_bytes_cap": 134217728,
            "free_disk_reserve_bytes": 536870912,
            "cost_is_not_an_original_experiment_replay_or_full_rebuild_quote": True,
            "missing_input_regeneration_cost": None,
        },
    }
    result["inventory_process_CPU_s"] = time.process_time() - cpu
    result["inventory_wall_s"] = time.perf_counter() - start
    return result


if __name__ == "__main__":
    # An exclusive new report, never an overwrite of prior experiment records.
    out = G / "retry/recovery502_inventory.json"
    with out.open("x") as handle:
        json.dump(inventory(), handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    print(str(out))
