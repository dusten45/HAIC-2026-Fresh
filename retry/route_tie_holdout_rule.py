"""Completion-first rule for the frozen route-tie generalization check.

Common official lap-time differences are summed across the registered pairs.
The median and damage remain descriptive. A zero median can coexist with a
real gain; a completion loss cannot be canceled by faster completed laps.
"""


def performance_verdict(summary):
    if summary['counts']['lost_completion']:
        return 'RETIRE_FIXED_TIE_COMPLETION_LOSS'
    if not summary['cohort_complete']:
        return 'KEEP_CHAMPION_INCONCLUSIVE_COHORT'
    if summary['counts']['new_completion']:
        return 'FRESH_HOLDOUT_PASS_COMPLETION_GAIN'
    common = summary['common_completion_metrics']
    if not common:
        return 'KEEP_CHAMPION_NO_COMMON_COMPLETION_EVIDENCE'
    if sum(row['lap_delta_ms'] for row in common) < 0:
        return 'FRESH_HOLDOUT_PASS_COMMON_TIME_GAIN'
    return 'RETIRE_FIXED_TIE_TIME_GAIN_DISAPPEARED'
