"""Completion-first descriptive paired summaries; no selection thresholds."""

import math
from statistics import mean, median


def _outcome(record):
    if record is None:
        return "missing"
    required = {"completed", "terminal_observed", "censored", "lap_ms",
                "unique_tiles", "total_tiles", "damage", "retire_reason"}
    if not isinstance(record, dict) or not required.issubset(record):
        return "indeterminate"
    if record["censored"]:
        return "censored"
    if not record["terminal_observed"]:
        return "indeterminate"
    try:
        tiles, total = float(record["unique_tiles"]), float(record["total_tiles"])
        damage = float(record["damage"])
        if not all(math.isfinite(v) for v in (tiles, total, damage)):
            return "indeterminate"
        if not 0 <= tiles <= total or total <= 0:
            return "indeterminate"
        if record["completed"]:
            lap = float(record["lap_ms"])
            if not math.isfinite(lap) or lap <= 0:
                return "indeterminate"
            return "completed"
    except (TypeError, ValueError):
        return "indeterminate"
    return "dnf"


def summarize(pairs, expected_case_ids):
    """Summarize fixed cases in expected order, keeping unknowns outside DNF.

    A candidate of None or a missing pair is unexecuted. Censored and other
    nonterminal/invalid records are inconclusive; only normal observed endpoints
    enter the four completion categories. Counts have explicit denominators.
    Time and damage are descriptive, and do not determine a winner or verdict.
    """
    expected = list(expected_case_ids)
    if len(set(expected)) != len(expected):
        raise ValueError("expected case IDs must be unique")
    indexed = {}
    for pair in pairs:
        case = pair["case"]
        if case in indexed:
            raise ValueError(f"duplicate pair case: {case}")
        if case not in expected:
            raise ValueError(f"unexpected pair case: {case}")
        indexed[case] = pair
    categories = {name: [] for name in (
        "new_completion", "lost_completion", "common_dnf", "common_completed")}
    unexecuted, inconclusive, case_results = [], [], []
    common_laps, common_dnfs = [], []
    baseline_completed = candidate_completed = 0
    baseline_normal = candidate_normal = 0
    damage_totals = {"baseline": 0.0, "candidate": 0.0}
    damage_records = {"baseline": 0, "candidate": 0}

    for case in expected:
        pair = indexed.get(case, {})
        baseline, candidate = pair.get("baseline"), pair.get("candidate")
        outcomes = {"baseline": _outcome(baseline), "candidate": _outcome(candidate)}
        baseline_normal += outcomes["baseline"] in ("completed", "dnf")
        candidate_normal += outcomes["candidate"] in ("completed", "dnf")
        baseline_completed += outcomes["baseline"] == "completed"
        candidate_completed += outcomes["candidate"] == "completed"
        for arm, record in (("baseline", baseline), ("candidate", candidate)):
            if isinstance(record, dict):
                try:
                    damage = float(record["damage"])
                    if math.isfinite(damage):
                        damage_totals[arm] += damage
                        damage_records[arm] += 1
                except (KeyError, TypeError, ValueError):
                    pass
        item = {"case": case, "baseline_outcome": outcomes["baseline"],
                "candidate_outcome": outcomes["candidate"]}
        if candidate is None:
            item["category"] = "unexecuted"
            unexecuted.append(case)
        elif any(outcome not in ("completed", "dnf") for outcome in outcomes.values()):
            item["category"] = "inconclusive"
            inconclusive.append(case)
        else:
            b, c = outcomes["baseline"] == "completed", outcomes["candidate"] == "completed"
            category = ("common_completed" if b and c else "lost_completion" if b
                        else "new_completion" if c else "common_dnf")
            item["category"] = category
            categories[category].append(case)
            if category == "common_completed":
                metrics = {"case": case, "baseline_lap_ms": float(baseline["lap_ms"]),
                           "candidate_lap_ms": float(candidate["lap_ms"]),
                           "lap_delta_ms": float(candidate["lap_ms"]) - float(baseline["lap_ms"]),
                           "lap_ratio": float(candidate["lap_ms"]) / float(baseline["lap_ms"]),
                           "damage_delta": float(candidate["damage"]) - float(baseline["damage"])}
                common_laps.append(metrics)
                item["descriptive_metrics"] = metrics
            elif category == "common_dnf":
                metrics = {"case": case,
                           "baseline_unique_tiles": int(baseline["unique_tiles"]),
                           "candidate_unique_tiles": int(candidate["unique_tiles"]),
                           "baseline_total_tiles": int(baseline["total_tiles"]),
                           "candidate_total_tiles": int(candidate["total_tiles"]),
                           "baseline_progress": baseline["unique_tiles"] / baseline["total_tiles"],
                           "candidate_progress": candidate["unique_tiles"] / candidate["total_tiles"]}
                common_dnfs.append(metrics)
                item["descriptive_metrics"] = metrics
        case_results.append(item)

    return {
        "expected_case_ids": expected, "expected_count": len(expected),
        "case_results": case_results,
        "category_case_ids": categories,
        "counts": {name: len(cases) for name, cases in categories.items()},
        "baseline_completed_count": baseline_completed,
        "candidate_completed_count": candidate_completed,
        "baseline_normal_endpoint_count": baseline_normal,
        "candidate_normal_endpoint_count": candidate_normal,
        "comparable_pair_count": sum(map(len, categories.values())),
        "unexecuted": unexecuted, "inconclusive": inconclusive,
        "censored_cases": [item["case"] for item in case_results
                           if "censored" in (item["baseline_outcome"], item["candidate_outcome"])],
        "cohort_complete": bool(expected) and not unexecuted and not inconclusive,
        "common_dnf_unique_tile_vectors": {
            "case_ids": [item["case"] for item in common_dnfs],
            "baseline": [item["baseline_unique_tiles"] for item in common_dnfs],
            "candidate": [item["candidate_unique_tiles"] for item in common_dnfs],
            "baseline_total_tiles": [item["baseline_total_tiles"] for item in common_dnfs],
            "candidate_total_tiles": [item["candidate_total_tiles"] for item in common_dnfs]},
        "common_dnf_metrics": common_dnfs,
        "common_completion_metrics": common_laps,
        "common_completion_median_lap_delta_ms": median(item["lap_delta_ms"] for item in common_laps) if common_laps else None,
        "common_completion_mean_lap_ratio": mean(item["lap_ratio"] for item in common_laps) if common_laps else None,
        "total_damage_diagnostic": {"sums": damage_totals, "observed_record_counts": damage_records,
                                    "qualification": "Descriptive only: episode durations, completion and censoring exposures may differ."},
    }
