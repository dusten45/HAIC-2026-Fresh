"""Synthetic cap/geometry arithmetic checks; no policy or simulator execution."""
import math
import unittest

import numpy as np

from retry.dev_lap_bottleneck import project, target_limits


class BottleneckArithmeticTests(unittest.TestCase):
    def test_global_removal_includes_duplicate_distance_sentinel(self):
        telemetry = {'speed_estimate': 0., 'route_obstacle_inputs': [],
                     'controller_target': [0., 6.]}
        out = target_limits(telemetry, {'radial_clearances': []})
        self.assertEqual(out['final'], 28.)
        self.assertEqual(out['without']['one_global_code_site'], 28.)
        self.assertEqual(out['without']['distance'], 28.)
        self.assertAlmostEqual(out['without']['global'], math.sqrt(7 / .003))
        self.assertGreater(out['without']['global'], out['final'])

    def test_near_schedule_can_be_masked_by_fresh_distance_limit(self):
        telemetry = {'speed_estimate': 0., 'route_obstacle_inputs': [[0., 5., 1.2]],
                     'controller_target': [1., 10.]}
        masked = target_limits(telemetry, {'radial_clearances': [1.2]})
        self.assertTrue(masked['near'])
        self.assertEqual(masked['final'], 4.)
        self.assertEqual(masked['without']['near_safe_schedule'], 4.)
        self.assertGreater(masked['without']['distance'], 4.)
        # A carried hazard can select safe lateral gain without age-zero cap.
        unmasked = target_limits(telemetry, {'radial_clearances': []})
        self.assertGreater(unmasked['without']['near_safe_schedule'], unmasked['final'])

    def test_closed_polyline_projection_is_rotation_translation_equivariant(self):
        xy = np.array([[0., 0.], [10., 0.], [10., 10.], [0., 10.]])
        points = np.array([[3., 1.], [11., 4.], [-1., 6.]])
        track = np.c_[np.zeros((4, 2)), xy]
        arc, tangent, offset, length = project(points, track)
        np.testing.assert_allclose(arc, [3., 14., 34.])
        np.testing.assert_allclose(tangent, [[1., 0.], [0., 1.], [0., -1.]])
        np.testing.assert_allclose(offset, 1.)
        self.assertEqual(length, 40.)
        angle = .7
        rotation = np.array([[math.cos(angle), -math.sin(angle)],
                             [math.sin(angle), math.cos(angle)]])
        translation = np.array([31., -17.])
        rotated_track = np.c_[np.zeros((4, 2)), xy @ rotation.T + translation]
        a2, t2, o2, l2 = project(points @ rotation.T + translation, rotated_track)
        np.testing.assert_allclose(a2, arc, atol=1e-12)
        np.testing.assert_allclose(t2, tangent @ rotation.T, atol=1e-12)
        np.testing.assert_allclose(o2, offset, atol=1e-12)
        self.assertAlmostEqual(l2, length)


if __name__ == '__main__':
    unittest.main()
