"""Actual-call scalar checks for the restricted cap pedal contrast.

The original pedals at the same target/HUD are arithmetic, not a policy replay.
GT speed labels never enter the participant, target, eligibility or command.
"""
import numpy as np

from retry.cap_pedal_candidate import BAND_M_S, effective_error, eligible
from retry.compact_dev_diagnostic import ScalarStats


def original_pedals(target, feedback):
    return np.asarray([np.clip(.08*(target-feedback), 0, .5),
                       np.clip(.04*(feedback-target), 0, .5)], np.float32).tolist()


class CapPedalStats(ScalarStats):
    def __init__(self):
        super().__init__()
        self.counts = dict.fromkeys(('target_rows', 'target_none_rows',
            'eligible_cap_rows', 'eligible_small_error_rows', 'changed_command_rows',
            'near_rows', 'near_changed_rows', 'curvature_limited_or_tied_rows',
            'curvature_limited_or_tied_changed_rows', 'excluded_mode_changed_rows',
            'outside_band_rows', 'outside_band_changed_rows',
            'overspeed_at_least_one_bin_rows', 'large_error_brake_changed_rows',
            'large_error_brake_deceleration_rows', 'saturated_brake_rows',
            'saturated_brake_changed_rows', 'small_brake_reduction_rows'), 0)
        self.eligible_cap_s = self.changed_command_s = 0.0
        self.first_change = self.first_large_brake = None
        self.large_brake_pre = self.large_brake_after = None

    def add(self, row):
        c = self.counts
        target = row['target_m_s']
        if target is None:
            c['target_none_rows'] += 1
        else:
            c['target_rows'] += 1
            mode = eligible(row['curvature'], row['selected_lateral_budget'], 45., row['near'])
            small = abs(target-row['feedback_m_s']) < BAND_M_S
            expected = original_pedals(target, row['feedback_m_s'])
            changed = expected != [row['gas'],row['brake']]
            curve = float(np.sqrt(row['selected_lateral_budget']/max(abs(row['curvature']),1e-6))) <= 45.
            c['eligible_cap_rows'] += mode
            c['eligible_small_error_rows'] += mode and small
            c['changed_command_rows'] += changed
            c['near_rows'] += bool(row['near'])
            c['near_changed_rows'] += bool(row['near'] and changed)
            c['curvature_limited_or_tied_rows'] += curve
            c['curvature_limited_or_tied_changed_rows'] += curve and changed
            c['excluded_mode_changed_rows'] += not mode and changed
            c['outside_band_rows'] += not small
            c['outside_band_changed_rows'] += not small and changed
            self.eligible_cap_s += mode * row['dwell_s']
            self.changed_command_s += changed * row['dwell_s']
            assert not changed or (mode and small and not row['near'] and not curve)
            if changed and self.first_change is None:
                self.first_change = dict(row, original_pedals_same_input=expected)
            if row['feedback_m_s']-target >= BAND_M_S:
                c['overspeed_at_least_one_bin_rows'] += 1
                c['large_error_brake_changed_rows'] += row['brake'] != expected[1]
                c['large_error_brake_deceleration_rows'] += row['speed_after_m_s'] < row['speed_before_m_s']
                assert row['brake'] == expected[1]
                if self.first_large_brake is None:
                    self.first_large_brake = dict(row, original_pedals_same_input=expected)
                    self.large_brake_pre, self.large_brake_after = list(self.window), []
            if expected[1] == .5:
                c['saturated_brake_rows'] += 1
                c['saturated_brake_changed_rows'] += row['brake'] != .5
                assert row['brake'] == .5
            c['small_brake_reduction_rows'] += row['brake'] < expected[1]
        if (self.first_large_brake is not None and row['step'] > self.first_large_brake['step']
                and len(self.large_brake_after) < 4):
            self.large_brake_after.append(dict(row))
        super().add(row)

    def summary(self, completed):
        result = super().summary(completed)
        result.pop('near5_rows', None)
        result.update(cap_pedal_checks=self.counts, eligible_normal_cap_s=self.eligible_cap_s,
            changed_pedal_s=self.changed_command_s, first_intervention=self.first_change,
            first_large_error_brake=self.first_large_brake,
            first_large_error_brake_pre_window=self.large_brake_pre,
            first_large_error_brake_following=self.large_brake_after,
            scope='Near/curve/tie/outside-band equality is at the same actual input. Closed-loop trajectories can change. Small overspeed braking in eligible cap mode is intentionally reduced; completion/time are the performance gate, damage and reversals are diagnostics.')
        return result


def cap_pedal_episode(plan_path, plan, case, initial_pairs):
    from retry import frozen_composite_runtime as runtime
    from retry.compact_dev_diagnostic import compact_episode

    original_prepare = runtime.prepare
    state = {}

    def prepare(*args, **kwargs):
        worker = original_prepare(*args, **kwargs)
        original_call = worker.call

        def call(operation, observation):
            response, elapsed = original_call(operation, observation)
            if operation == 'act':
                state['probe'] = response['contact_probe']
            return response, elapsed

        worker.call = call
        return worker

    runtime.prepare = prepare
    try:
        return compact_episode(plan_path, plan, case, initial_pairs, [],
            pedal_error_transform=lambda error: effective_error(error, state['probe']),
            stats_factory=CapPedalStats)
    finally:
        runtime.prepare = original_prepare
