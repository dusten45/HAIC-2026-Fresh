"""Scalar checks for a memoryless pedal contrast on actual native calls.

The original command at the same observed target/HUD pair is arithmetic only,
not a policy replay or a counterfactual vehicle trajectory. Bounded windows and
counts describe behavior; completion, lap time and damage decide performance.
"""
import numpy as np

from retry.compact_dev_diagnostic import ScalarStats
from retry.pedal_transition_candidate import HUD_BIN_M_S


def original_pedals(error):
    return [float(np.float32(np.clip(.08*error, 0, .5))),
            float(np.float32(np.clip(-.04*error, 0, .5)))]


class ControlStats(ScalarStats):
    def __init__(self):
        super().__init__()
        self.control = dict(target_rows=0, target_none_rows=0,
            small_error_rows=0, changed_command_rows=0,
            outside_band_rows=0, outside_band_changed_rows=0,
            overspeed_at_least_one_bin_rows=0, large_error_brake_changed_rows=0,
            original_saturated_brake_rows=0, saturated_brake_changed_rows=0,
            near_changed_command_rows=0,
            large_error_brake_actual_deceleration_rows=0,
            small_error_brake_reductions=0,
            maximum_small_error_brake_reduction=0.0)
        self.first_intervention = None
        self.first_large_brake = None
        self.first_large_brake_pre_window = None
        self.first_large_brake_following = []

    def add(self, row):
        if row['target_m_s'] is None:
            self.control['target_none_rows'] += 1
        else:
            error = row['target_m_s'] - row['feedback_m_s']
            original = original_pedals(error)
            actual = [row['gas'], row['brake']]
            changed = actual != original
            small = abs(error) < HUD_BIN_M_S
            c = self.control
            c['target_rows'] += 1
            c['small_error_rows'] += small
            c['changed_command_rows'] += changed
            c['outside_band_rows'] += not small
            c['outside_band_changed_rows'] += bool(not small and changed)
            c['near_changed_command_rows'] += bool(row['near'] and changed)
            if changed and self.first_intervention is None:
                self.first_intervention = dict(row, error_m_s=error,
                    original_pedals_same_input=original)
            if error <= -HUD_BIN_M_S:
                c['overspeed_at_least_one_bin_rows'] += 1
                c['large_error_brake_changed_rows'] += actual[1] != original[1]
                c['large_error_brake_actual_deceleration_rows'] += row['speed_after_m_s'] < row['speed_before_m_s']
                if self.first_large_brake is None:
                    self.first_large_brake = dict(row, original_pedals_same_input=original)
                    self.first_large_brake_pre_window = list(self.window)
            if original[1] == .5:
                c['original_saturated_brake_rows'] += 1
                c['saturated_brake_changed_rows'] += actual[1] != .5
            if small and actual[1] < original[1]:
                c['small_error_brake_reductions'] += 1
                c['maximum_small_error_brake_reduction'] = max(
                    c['maximum_small_error_brake_reduction'], original[1]-actual[1])
            assert not (not small and changed), 'Large-error pedal command changed'
        if (self.first_large_brake is not None
                and row['step'] > self.first_large_brake['step']
                and len(self.first_large_brake_following) < 4):
            self.first_large_brake_following.append(dict(row))
        super().add(row)

    def summary(self, completed):
        result = super().summary(completed)
        result.update(control_comparison=self.control,
            first_intervention=self.first_intervention,
            first_large_error_brake=self.first_large_brake,
            first_large_error_brake_pre_window=self.first_large_brake_pre_window,
            first_large_error_brake_following=self.first_large_brake_following,
            braking_scope='Commands match the original law immediately at the same actual input for overspeed>=2.5m/s. Smaller overspeed braking is intentionally softened; this does not prove all physically necessary braking is unchanged.')
        return result
