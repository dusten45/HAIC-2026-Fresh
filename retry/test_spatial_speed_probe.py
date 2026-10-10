"""The speed contrast must not alter reference targets or steering."""
import unittest
import numpy as np

from retry.spatial_speed_probe import SpatialSpeedProbe


class SpatialSpeedProbeTests(unittest.TestCase):
    def make(self, limit=None):
        theta = np.linspace(0, 2 * np.pi, 32, endpoint=False)
        road = np.column_stack((theta, theta, 50 * np.cos(theta), 50 * np.sin(theta)))
        probe = SpatialSpeedProbe([0., 500.], [4., 504.], limit)
        probe.reset(road, np.empty((0, 3)), 6.6666666667)
        return probe

    def test_velocity_and_speed_arm_do_not_change_targets_or_steering(self):
        nominal, low = self.make(), self.make(3.)
        for index in (0, 1, 3, 6):
            position = nominal.path[index]
            heading = float(np.arctan2(-position[1], position[0]))
            a = nominal.act(position, heading, [0., 8.])
            b = low.act(position, heading, [0., 2.])
            np.testing.assert_array_equal(nominal.last_diagnostic['target_world'], low.last_diagnostic['target_world'])
            self.assertEqual(nominal.last_diagnostic['lookahead_m'], low.last_diagnostic['lookahead_m'])
            self.assertEqual(a[0], b[0])
            self.assertLessEqual(low.last_diagnostic['target_speed_m_s'], 3.)
        self.assertFalse(np.array_equal(a[1:], b[1:]))

    def test_prefix_memory_preserves_target_floor(self):
        probe = self.make(3.)
        probe.prime(0, 0., 0., 8., .1)
        probe.act(probe.path[0], 0., [0., 0.])
        self.assertEqual(probe.last_diagnostic['target_arc_unwrapped_m'], 8.)
        self.assertEqual(probe.last_diagnostic['target_arc_held_m'], 4.)

    def test_invalid_or_out_of_domain_reference_is_rejected(self):
        with self.assertRaises(ValueError):
            SpatialSpeedProbe([0., 1.], [4., 3.])
        probe = self.make()
        probe.prime(0, 501., 0., 505., 0.)
        with self.assertRaises(ValueError):
            probe.act(probe.path[0], 0., [0., 0.])


if __name__ == '__main__':
    unittest.main()
