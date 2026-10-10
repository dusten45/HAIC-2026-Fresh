"""Pure checks of offline sequence boundaries and input validation."""
import unittest

import numpy as np

from retry.action_sequence import ActionSequence


class SequenceContract(unittest.TestCase):
    def test_phase_boundaries_and_baseline_restoration(self):
        sequence = ActionSequence([{'duration_actions': 2, 'action': [-.2, .1, 0.]},
                                   {'duration_actions': 3, 'action': [.1, 0., .2]}])
        baseline = np.asarray([.3, .4, 0.], dtype=np.float32)
        for offset in [0, 1]:
            action, active = sequence.apply(offset, baseline)
            self.assertTrue(active)
            np.testing.assert_array_equal(action, np.asarray([-.2, .1, 0.], dtype=np.float32))
        for offset in [2, 4]:
            np.testing.assert_array_equal(sequence.apply(offset, baseline)[0],
                                          np.asarray([.1, 0., .2], dtype=np.float32))
        for offset in [-1, 5]:
            action, active = sequence.apply(offset, baseline)
            self.assertFalse(active)
            np.testing.assert_array_equal(action, baseline)

    def test_no_change_and_no_aliasing(self):
        baseline = np.asarray([0., .2, 0.], dtype=np.float32)
        action, active = ActionSequence([]).apply(0, baseline)
        self.assertFalse(active)
        action[0] = .4
        self.assertEqual(baseline[0], 0.)

    def test_invalid_phase_and_offset(self):
        for duration, action in [(0, [0., 0., 0.]), (True, [0., 0., 0.]),
                                 (1, [0., -1., 0.]), (1, [float('nan'), 0., 0.])]:
            with self.assertRaises(ValueError):
                ActionSequence([{'duration_actions': duration, 'action': action}])
        with self.assertRaises(ValueError):
            ActionSequence([]).apply(.5, [0., 0., 0.])


if __name__ == '__main__':
    unittest.main()
