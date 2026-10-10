"""Pure full-race outcome accounting; no policy or simulator calls."""

NORMAL_ACTION_HORIZON = 2000


def race_outcome(*, completed, physical_terminal, charged_steps,
                 planned_horizon, stop_reason=None, resource_stopped=False):
    """A spent normal horizon is DNF; an interrupted prefix is incomplete."""
    assert 0 <= charged_steps <= planned_horizon
    normal_horizon = charged_steps >= NORMAL_ACTION_HORIZON
    evaluation_terminal = bool(completed or physical_terminal or normal_horizon)
    censored = bool(not evaluation_terminal and resource_stopped)
    indeterminate = bool(not evaluation_terminal and not censored)
    return {"evaluation_outcome": "completed" if completed else "dnf" if evaluation_terminal
            else "censored" if censored else "indeterminate",
            "evaluation_terminal": evaluation_terminal,
            "normal_horizon_reached": normal_horizon,
            "censored": censored, "indeterminate": indeterminate,
            "interruption_reason": stop_reason if not evaluation_terminal else None}


def pair_category(baseline, candidate):
    if baseline["censored"] or candidate["censored"]:
        return "censored"
    if not all(result.get("evaluation_terminal", result["terminal_observed"])
               for result in (baseline, candidate)):
        return "indeterminate"
    return {(True, True): "preserved", (False, True): "new_completion",
            (True, False): "lost_completion", (False, False): "common_failure"}[
                (baseline["completed"], candidate["completed"])]
