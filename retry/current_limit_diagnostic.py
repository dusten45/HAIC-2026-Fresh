"""Online scalar target-limit exposure; evaluator only, no action changes.

Shares describe observed action intervals, including terminal callbacks. They
are not recoverable lap time. GT labels never enter the participant process.
"""
import math

from retry.compact_dev_diagnostic import ScalarStats, window_summary

CATEGORIES = ('normal_curvature24', 'near_additional5', 'global_cap40', 'missing_target')


def category(row):
    target = row['target_m_s']
    if target is None:
        return 'missing_target'
    k = max(abs(row['curvature']), 1e-6)
    normal = min(40.0, math.sqrt(24.0 / k))
    if row['near'] and target < normal - 1e-9:
        return 'near_additional5'
    return 'normal_curvature24' if normal < 40.0 - 1e-9 else 'global_cap40'


class LimitStats(ScalarStats):
    def __init__(self):
        super().__init__()
        fields = ('rows', 'dwell_s', 'feedback_bound_or_braking_s', 'GT_bound_or_braking_s',
            'GT_below_target_minus1_s', 'braking_s', 'gas_s', 'target_weighted_sum',
            'GT_speed_weighted_sum', 'GT_minus_target_weighted_sum', 'abs_GT_minus_target_weighted_sum',
            'feedback_minus_GT_weighted_sum', 'abs_feedback_minus_GT_weighted_sum')
        self.limits = {name:dict.fromkeys(fields, 0.0) for name in CATEGORIES}
        self.first_offtrack = self.first_offtrack_window = None

    def add(self, row):
        if (self.first_offtrack is None and row['offtrack_before']==0
                and row['offtrack_after']>0):
            self.first_offtrack = dict(row)
            self.first_offtrack_window = list(self.window)
        name = category(row)
        bucket = self.limits[name]
        duration = row['dwell_s']
        bucket['rows'] += 1
        bucket['dwell_s'] += duration
        if row['target_m_s'] is not None:
            target, speed, feedback = row['target_m_s'], row['speed_before_m_s'], row['feedback_m_s']
            brake = row['brake']>1e-6
            bucket['feedback_bound_or_braking_s'] += duration * (feedback>=target-1.0 or brake)
            bucket['GT_bound_or_braking_s'] += duration * (speed>=target-1.0 or brake)
            bucket['GT_below_target_minus1_s'] += duration * (speed<target-1.0)
            bucket['braking_s'] += duration * brake
            bucket['gas_s'] += duration * (row['gas']>1e-6)
            bucket['target_weighted_sum'] += duration * target
            bucket['GT_speed_weighted_sum'] += duration * speed
            bucket['GT_minus_target_weighted_sum'] += duration * (speed-target)
            bucket['abs_GT_minus_target_weighted_sum'] += duration * abs(speed-target)
            bucket['feedback_minus_GT_weighted_sum'] += duration * (feedback-speed)
            bucket['abs_feedback_minus_GT_weighted_sum'] += duration * abs(feedback-speed)
        super().add(row)

    def summary(self, completed):
        result = super().summary(completed)
        assert abs(sum(v['dwell_s'] for v in self.limits.values())-self.elapsed)<1e-8
        result.update(limit_exposure=self.limits,
            denominator='Actual native action interval dwell, including terminal callbacks; distinct from official lap.',
            bound_rule='Feedback or GT speed>=target-1m/s OR returned brake>1e-6; feedback rule reused138, GT added as independent label.',
            gap_rule='Before-action GT speed minus current target, time-weighted zero-order samples; not lap-time loss.',
            exposure_is_recoverable_time=False)
        if not completed and self.first_damage is None and self.first_offtrack is not None:
            result['first_offtrack_event']=self.first_offtrack
            result['first_offtrack_pre_window']=self.first_offtrack_window
            result['first_offtrack_pre_summary']=window_summary(self.first_offtrack_window)
        else:
            result['first_offtrack_event']=None
            result['first_offtrack_pre_window']=None
            result['first_offtrack_pre_summary']=None
        if self.first_damage is not None or result['first_offtrack_event'] is not None:
            result['last_action_if_not_completed']=None
            result['last_action_pre_window_if_not_completed']=None
        result['offtrack_label']='First0→positive simulator off_track_counter; can be nonterminal, not a unique failure cause.'
        return result
