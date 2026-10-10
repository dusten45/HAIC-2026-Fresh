"""Small coordinate checks for the fixed research steering law; no simulator."""
import unittest

import numpy as np

from retry.stanley_teacher import steering_from_front_error


class SteeringCoordinates(unittest.TestCase):
    def test_left_right_and_heading_correction(self):
        left = steering_from_front_error(0., [0., 1.], -.25, 10.)[0]
        right = steering_from_front_error(0., [0., 1.], .25, 10.)[0]
        self.assertGreater(left, 0.)
        self.assertLess(right, 0.)
        self.assertAlmostEqual(left, -right)
        self.assertGreater(steering_from_front_error(.1, [0., 1.], 0., 10.)[0], 0.)
        self.assertLess(steering_from_front_error(-.1, [0., 1.], 0., 10.)[0], 0.)

    def test_straight_alignment_and_finite_low_speed(self):
        self.assertEqual(steering_from_front_error(0., [0., 1.], 0., 0.)[0], 0.)
        low = steering_from_front_error(0., [0., 1.], .25, 0.)[0]
        self.assertTrue(np.isfinite(low))
        self.assertAlmostEqual(low, -np.arctan(.25))
        self.assertEqual(steering_from_front_error(0., [0., 1.], 100., 0.)[0], -.4)

    def test_rotated_coordinates(self):
        heading, path_heading, rotation = .31, .44, 1.13
        tangent = np.array([-np.sin(path_heading), np.cos(path_heading)])
        rotation_matrix = np.array([[np.cos(rotation), -np.sin(rotation)],
                                    [np.sin(rotation), np.cos(rotation)]])
        original = steering_from_front_error(heading, tangent, .17, 5.)
        rotated = steering_from_front_error(heading + rotation, rotation_matrix @ tangent, .17, 5.)
        np.testing.assert_allclose(original, rotated, rtol=0., atol=1e-14)


if __name__ == '__main__':
    unittest.main()
