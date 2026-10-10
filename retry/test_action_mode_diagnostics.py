import unittest
import numpy as np
from retry.action_mode_diagnostics import action_events, contiguous_runs


class ActionModeDiagnosticsTests(unittest.TestCase):
    def test_deadband_and_small_mode_boundary_crossings_are_separate(self):
        student = np.array([[.01, .09, 0], [.20, .5, 0], [.1, .2, .2]])
        teacher = np.array([[-.01, .11, 0], [-.20, 0, .5], [.1, .2, .2]])
        events, sm, tm = action_events(student, teacher)
        np.testing.assert_array_equal(events['near_zero_opposed_steer'], [True, False, False])
        np.testing.assert_array_equal(events['robust_opposed_steer'], [False, True, False])
        np.testing.assert_array_equal(events['mode_mismatch'], [True, True, False])
        np.testing.assert_array_equal(events['major_mode_mismatch'], [False, True, False])
        self.assertEqual((sm[-1], tm[-1]), (3, 3))

    def test_action_gaps_break_runs_and_actual_timestamps_define_duration(self):
        runs = contiguous_runs([True, True, True, False, True], [4, 5, 8, 9, 10],
            [1., 1.08, 2., 2.04, 2.12], [1.08, 1.12, 2.04, 2.12, 2.20])
        self.assertEqual([(r['start_action'], r['end_action'], r['actions']) for r in runs],
            [(4, 5, 2), (8, 8, 1), (10, 10, 1)])
        self.assertAlmostEqual(runs[0]['duration_s'], .12)
        self.assertAlmostEqual(runs[1]['duration_s'], .04)


if __name__ == '__main__':
    unittest.main()
