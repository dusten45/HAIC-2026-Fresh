"""Small numeric and mock-adapter checks; no HAIC simulation or training."""
import math
import unittest
import numpy as np
from retry.expected_action import capped_positive_normal_mean, expected_control_action


class ExpectedActionTests(unittest.TestCase):
    def test_closed_form_matches_fixed_quadrature(self):
        nodes, weights = np.polynomial.legendre.leggauss(128)
        positions = (nodes + 1.) / 2.
        for mean in (-2., -.7, 0., .8, 2.):
            for std in (.5, .6):
                integral = .5 * sum(w * .5 * math.erfc((t - mean) / (std * math.sqrt(2.)))
                                     for t, w in zip(positions, weights))
                self.assertAlmostEqual(capped_positive_normal_mean(mean, std), integral, places=12)

    def test_zero_variance_recovers_original_control(self):
        from retry.privileged_ppo import control_action
        for mean in ((-2., .3), (.2, -.4), (2., -2.), (0., 0.)):
            np.testing.assert_array_equal(expected_control_action(mean, (0., 0.)), control_action(mean))

    def test_zero_mean_has_positive_expected_pedals(self):
        actual = expected_control_action((0., 0.), (.5, .5))
        self.assertEqual(actual[0], 0.)
        self.assertGreater(actual[1], 0.)
        self.assertEqual(actual[1], actual[2])

    def test_invalid_shape_or_variance_is_rejected(self):
        for mean, std in (((0.,), (.5, .5)), ((0., 0.), (-.5, .5)), ((math.nan, 0.), (.5, .5))):
            with self.assertRaises(ValueError):
                expected_control_action(mean, std)

    def test_custom_adapter_keeps_raw_coordinates_and_actual_control(self):
        from retry.privileged_ppo import PrivilegedPilotEnv
        from retry.test_privileged_ppo import CurrentStateEnv
        raw = CurrentStateEnv()
        rows, requested, executed = [], [], []
        def transform(mean):
            requested.append(np.asarray(mean).copy())
            return expected_control_action(mean, (.5, .6))
        def execute(base, actual):
            executed.append(actual.copy())
            return base.step(actual)
        env = PrivilegedPilotEnv(raw, 12, {'track_id': 4},
                                 execute=execute, observe=rows.append,
                                 action_transform=transform)
        env.reset()
        mean = np.asarray([2., .7], np.float32)
        env.step(mean)
        np.testing.assert_array_equal(requested[0], mean)
        np.testing.assert_array_equal(executed[0], expected_control_action(mean, (.5, .6)))
        np.testing.assert_array_equal(rows[0]['executed_action'], executed[0])
        self.assertTrue(rows[0]['custom_action_transform'])
        self.assertIsNone(rows[0]['normalized_applied_action'])
        np.testing.assert_array_equal(rows[0]['policy_action_coordinates'], mean)
        env.close()


if __name__ == '__main__':
    unittest.main()
