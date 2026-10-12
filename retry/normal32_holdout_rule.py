"""Frozen normal32 HOLDOUT rule: preserve completion and transfer lap gain.

The common-completion sum is the registered local decision rule. The median
and damage are diagnostics; a new completion alone does not establish time
transfer, and a lost baseline completion cannot be offset by faster laps.
"""


def performance_verdict(summary):
    if summary['counts']['lost_completion']:
        return 'KEEP_CHAMPION_COMPLETION_LOSS'
    if not summary['cohort_complete']:
        return 'KEEP_CHAMPION_INCONCLUSIVE_COHORT'
    common = summary['common_completion_metrics']
    if not common:
        return 'KEEP_CHAMPION_NO_COMMON_TIME_EVIDENCE'
    if sum(row['lap_delta_ms'] for row in common) < 0:
        return 'FRESH_HOLDOUT_PASS_COMMON_TIME_GAIN'
    return 'KEEP_CHAMPION_NO_COMMON_TIME_GAIN'
