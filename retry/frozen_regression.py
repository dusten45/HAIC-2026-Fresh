"""Serial frozen-policy regression against existing normal baseline endpoints.

Run with --plan pointing to a private hash-bound plan.json. No policy search,
baseline replay, prefix or retry is performed. A common DNF is not a lost
completion; missing official endpoints remain inconclusive.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def stop_reason(baseline, candidate):
    if not baseline.get("terminal_observed") or baseline.get("censored", True):
        return "BASELINE_NOT_NORMAL_ENDPOINT"
    if not candidate.get("terminal_observed") or candidate.get("censored", True):
        return "MISSING_OFFICIAL_ENDPOINT"
    if baseline["completed"] and not candidate["completed"]:
        return "FIRST_LOST_PRIOR_COMPLETION_STOP_UNLAUNCHED"
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    path = args.plan.resolve()
    assert path.name == "plan.json"
    directory = path.parent
    assert hashlib.sha256(path.read_bytes()).hexdigest() == (directory / "plan.sha256").read_text().strip()
    plan = json.loads(path.read_text())
    root = Path(__file__).resolve().parents[1]
    start = time.perf_counter()
    episodes, termination = [], None
    for index, case in enumerate(plan["cases"]):
        if (directory / "stop.json").exists():
            termination = "shared_stop"
            break
        ledger = json.loads((directory / "budget.json").read_text())
        left = datetime.datetime.fromisoformat(plan["deadline_utc"]).timestamp() - time.time()
        remaining_actions = min((len(plan["cases"]) - index) * plan["max_steps"], plan["max_actions"] - ledger["actions"])
        rate = min([plan["prior_required_single_actions_per_s"]] + [e["actions_per_s"] for e in episodes]) * .7
        if remaining_actions <= 0 or remaining_actions / rate + 120 >= left:
            termination = "COST_OR_RESOURCE_CENSORED_BEFORE_NEW_EPISODE"
            break
        baseline_path = Path(case["baseline_result_path"])
        assert hashlib.sha256(baseline_path.read_bytes()).hexdigest() == case["baseline_result_sha256"]
        baseline = json.loads(baseline_path.read_text())
        assert baseline["terminal_observed"] and not baseline["censored"]
        case_start = time.perf_counter()
        with (directory / (case["id"] + ".stdout")).open("w") as log:
            subprocess.run([str(root / ".venv/bin/python"), "-B", "-m", "retry.frozen_regression_case", "--plan", str(path), "--case", case["id"]],
                           cwd=root, stdout=log, stderr=subprocess.STDOUT, check=False,
                           env={**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"})
        candidate = json.loads((directory / "runs" / case["id"] / "result.json").read_text())
        wall = time.perf_counter() - case_start
        episode = {"case": case["id"], "wall_s": wall, "new_actions": candidate["charged_wrapper_actions"],
                   "actions_per_s": candidate["charged_wrapper_actions"] / wall,
                   "official_endpoint": bool(candidate["terminal_observed"] and not candidate["censored"]),
                   "baseline_completed": baseline["completed"], "completed": candidate["completed"]}
        episodes.append(episode)
        (directory / "coordinate-progress.json").write_text(json.dumps({"episodes": episodes}, indent=2) + "\n")
        print(json.dumps(episode), flush=True)
        termination = stop_reason(baseline, candidate)
        if termination:
            (directory / "stop.json").write_text(json.dumps({"kind": termination, "case": case["id"], "unexecuted": [c["id"] for c in plan["cases"][index + 1:]]}, indent=2) + "\n")
            break
    executed = {e["case"] for e in episodes}
    result = {"episodes": episodes, "wall_s": time.perf_counter() - start, "termination": termination,
              "unexecuted": [c["id"] for c in plan["cases"] if c["id"] not in executed],
              "number_order_preserved": True, "simulators_max": 1}
    (directory / "coordinate-result.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
