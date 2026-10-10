"""Compare paired driving endpoints without mixing completion and damage."""

import math
import statistics


def compare_pairs(pairs):
    """Input is iterable of (case_id, baseline, candidate) valid endpoints."""
    groups = {k: [] for k in ("preserved", "new_completion", "lost_completion", "common_failure")}
    laps, failure, records = [], [], []
    for case, old, new in pairs:
        category = {(True, True): "preserved", (False, True): "new_completion",
                    (True, False): "lost_completion", (False, False): "common_failure"}[
                        bool(old["completed"]), bool(new["completed"])]
        groups[category].append(case)
        row = {"case": case, "category": category}
        if category == "preserved":
            ratio = new["lap_ms"] / old["lap_ms"]
            laps.append(math.log(ratio))
            row.update(lap_delta_ms=new["lap_ms"] - old["lap_ms"], lap_ratio=ratio)
        elif category == "common_failure":
            delta = new["progress"] - old["progress"]
            failure.append(delta)
            row.update(progress_delta=delta, unique_tiles_delta=new["unique_tiles"] - old["unique_tiles"])
        records.append(row)
    median_lap = statistics.median(laps) if laps else None
    median_failure = statistics.median(failure) if failure else None
    preserved = not groups["lost_completion"]
    promising = preserved and (bool(groups["new_completion"]) or
                (median_lap is not None and median_lap < 0) or
                (all(x <= 0 for x in laps) and median_failure is not None and median_failure > 0))
    pareto = all(x <= 0 for x in laps) and all(x >= 0 for x in failure) and (
        any(x < 0 for x in laps) or any(x > 0 for x in failure))
    return {"categories": groups, "pairs": records, "median_common_lap_log_ratio": median_lap,
            "median_common_failure_progress_delta": median_failure, "promising": promising,
            "transfer_keep": preserved and (bool(groups["new_completion"]) or pareto)}


def selection_key(candidate_id, comparison):
    """Use only after valid endpoints and zero lost completions are established.

    Preserved baseline completions have the same road set for all eligible
    candidates. Failure progress is a separate tie breaker, never a lap utility.
    Damage is deliberately absent. No minimum percentage improvement applies.
    """
    lap = comparison["median_common_lap_log_ratio"]
    failure = comparison["median_common_failure_progress_delta"]
    return (-len(comparison["categories"]["new_completion"]),
            lap if lap is not None else 0.0,
            -(failure if failure is not None else 0.0), candidate_id)
