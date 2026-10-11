"""Synthetic checks of rejection and observation boundaries; no DEV inputs."""
import copy
import unittest

import numpy as np

from retry.hud_feedback_saved_audit import gate_group, longest_run, read_speed


class SavedHudGateTests(unittest.TestCase):
    def summary(self):
        return {'n': 20,
                'old': {'speed_error': dict(mae=2., p95=3., p99=4., maximum=5.),
                        'wrong_brake': dict(count=4, longest_run=2),
                        'wrong_gas': dict(count=2, longest_run=1)},
                'bar': {'speed_error': dict(mae=1., p95=2., p99=3., maximum=4.),
                        'wrong_brake': dict(count=2, longest_run=1),
                        'wrong_gas': dict(count=1, longest_run=1)}}

    def test_aggregate_improvement_does_not_hide_tail_regression(self):
        for metric in ('p95', 'p99', 'maximum'):
            with self.subTest(metric=metric):
                sample = self.summary()
                sample['bar']['speed_error'][metric] = sample['old']['speed_error'][metric] + .1
                self.assertEqual(gate_group(sample, strict_mae=True)['status'], 'FAIL')

    def test_speed_improvement_does_not_hide_wrong_gas(self):
        sample = self.summary()
        sample['bar']['wrong_gas']['count'] = 3
        self.assertEqual(gate_group(sample)['status'], 'FAIL')

    def test_equal_error_does_not_satisfy_strict_improvement(self):
        sample = self.summary()
        sample['bar']['speed_error'] = copy.deepcopy(sample['old']['speed_error'])
        self.assertEqual(gate_group(sample)['status'], 'PASS')
        self.assertEqual(gate_group(sample, strict_mae=True)['status'], 'FAIL')

    def test_lower_count_does_not_hide_longer_wrong_brake_run(self):
        sample = self.summary()
        sample['bar']['wrong_brake'] = dict(count=3, longest_run=3)
        self.assertEqual(gate_group(sample)['status'], 'FAIL')

    def test_missing_support_is_not_a_pass(self):
        sample = self.summary()
        sample['n'] = 4
        self.assertEqual(gate_group(sample)['status'], 'INSUFFICIENT_SUPPORT')

    def test_filtered_rows_do_not_join_disjoint_action_runs(self):
        self.assertEqual(longest_run([2, 3, 10, 11, 12]), 3)
        self.assertEqual(longest_run([]), 0)

    def test_pixels_outside_fixed_roi_cannot_change_reader(self):
        image = np.zeros((84, 84), np.float32)
        image[78, 11] = .5
        changed = np.ones_like(image)
        changed[74:83, 11:13] = image[74:83, 11:13]
        self.assertEqual(read_speed(image, [0., 1.], [0., 10.]),
                         read_speed(changed, [0., 1.], [0., 10.]))


if __name__ == '__main__':
    unittest.main()
