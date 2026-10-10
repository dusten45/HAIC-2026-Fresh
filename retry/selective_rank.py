"""Deterministic selective ranking and paired offline diagnostics.

Tolerances specify practical indifference, not statistical confidence bounds.
Keep all candidates, including abstentions, in the paired comparison.
"""
from dataclasses import dataclass
from itertools import combinations
import math


@dataclass(frozen=True)
class CandidateScore:
    identifier: str
    applicable: bool
    unsafe: bool
    advance: float
    margin: float


def pair_order(a, b, advance_tolerance, margin_tolerance):
    if a.unsafe != b.unsafe:
        return 1 if not a.unsafe else -1
    for value, tolerance in [(a.advance - b.advance, advance_tolerance),
                             (a.margin - b.margin, margin_tolerance)]:
        if abs(value) > tolerance:
            return 1 if value > 0 else -1
    return 0


def selective_choice(scores, advance_tolerance, margin_tolerance):
    eligible = [s for s in scores if s.applicable and not s.unsafe]
    if len(eligible) < 2:
        return None, [], "INSUFFICIENT_APPLICABLE_CANDIDATES"
    if not any(pair_order(a, b, advance_tolerance, margin_tolerance)
               for a, b in combinations(eligible, 2)):
        return None, [], "NO_PREDICTED_SEPARATION"
    best_advance = max(s.advance for s in eligible)
    top = [s for s in eligible if s.advance >= best_advance - advance_tolerance]
    best_margin = max(s.margin for s in top)
    top = sorted(s.identifier for s in top
                 if s.margin >= best_margin - margin_tolerance)
    return top[0], top, "SELECTED_FROM_PRACTICAL_TOP_SET"


def compare_scores(predictions, outcomes, chosen, advance_tolerance, margin_tolerance):
    predicted = {s.identifier: s for s in predictions}
    actual = {s.identifier: s for s in outcomes}
    if len(predicted) != len(predictions) or len(actual) != len(outcomes) or predicted.keys() != actual.keys():
        raise ValueError("one paired result for every original candidate required")
    if not all(math.isfinite(s.advance) and math.isfinite(s.margin)
               for s in [*predictions, *outcomes]):
        raise ValueError("finite scores required")
    pairs = []
    for a, b in combinations(predictions, 2):
        po = pair_order(a, b, advance_tolerance, margin_tolerance)
        ao = pair_order(actual[a.identifier], actual[b.identifier], advance_tolerance, margin_tolerance)
        pairs.append({"ids": [a.identifier, b.identifier],
                      "both_applicable": a.applicable and b.applicable,
                      "predicted_order": po, "actual_order": ao,
                      "inversion": po * ao < 0,
                      "actual_comparable": ao != 0,
                      "missed_separation": ao != 0 and po == 0,
                      "agreed_separation": po != 0 and po == ao})
    safe = [s for s in outcomes if not s.unsafe]
    best_safe = max((s.advance for s in safe), default=None)
    selected = None if chosen is None else actual[chosen]
    return {"candidate_count": len(predictions),
            "applicable_count": sum(s.applicable for s in predictions),
            "abstained_count": sum(not s.applicable for s in predictions),
            "chosen": chosen,
            "chosen_actual_unsafe": None if selected is None else selected.unsafe,
            "safe_progress_regret_against_all_candidates":
                None if selected is None or selected.unsafe or best_safe is None
                else max(0., best_safe - selected.advance),
            "actual_unsafe_count": sum(s.unsafe for s in outcomes),
            "applicable_actual_unsafe_ids": [s.identifier for s in predictions
                                             if s.applicable and actual[s.identifier].unsafe],
            "pairs": pairs}
