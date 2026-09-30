import unittest

import numpy as np

from oracle.v2_controller import V2Controller
from oracle.v3_controller import V3Controller
from tests.test_v2_controller import circle_env


class TestV3Controller(unittest.TestCase):
    def test_pace_stage_preserves_frozen_control_actions(self):
        env = circle_env(60)
        np.testing.assert_array_equal(V3Controller(env, "pace").act()[0], V2Controller(env).act()[0])

    def test_envelope_preserves_v2_line_but_raises_speed_limits(self):
        v2 = V2Controller(circle_env(60))
        v3 = V3Controller(circle_env(60), "envelope")
        np.testing.assert_array_equal(v2.path.points, v3.path.points)
        self.assertGreater(np.mean(v3.speed_limits), np.mean(v2.speed_limits))
        self.assertLessEqual(np.max(v3.speed_limits), 95)

    def test_cyclic_profile_is_braking_reachable(self):
        controller = V3Controller(circle_env(60))
        squared = controller.speed_profile**2
        intervals = np.diff(np.r_[controller.arcs, controller.path.length])
        self.assertTrue((squared - np.roll(squared, -1)
                         <= 2 * controller.config.braking_deceleration * intervals + 1e-8).all())
        self.assertTrue((controller.speed_profile <= controller.speed_limits + 1e-8).all())

    def test_future_apex_brakes_with_no_simultaneous_throttle(self):
        controller = V3Controller(circle_env(120, 70), "envelope")
        controller.speed_limits[:] = 95
        controller.speed_limits[12] = 20
        action, diagnostic = controller.act()
        self.assertLess(diagnostic["target_speed"], 70)
        self.assertEqual(action[1], 0)
        self.assertGreater(action[2], 0)
        self.assertTrue(np.isfinite(action).all())
        self.assertTrue(((action[1:] >= 0) & (action[1:] <= 1)).all())

    def test_physical_longitudinal_actions_match_nominal_acceleration(self):
        for speed in (20, 100):
            with self.subTest(speed=speed):
                action, diagnostic = V3Controller(circle_env(60, speed), "drive").act()
                acceleration = diagnostic["commanded_acceleration"]
                self.assertAlmostEqual(float(action[1]), float(np.clip(
                    acceleration * 29.2498 * (speed + 2.7) / 80000, 0, 1)), places=6)
                self.assertAlmostEqual(float(action[2]), float(np.clip(
                    -acceleration / 303.8958, 0, .89)), places=6)
                self.assertFalse(action[1] > 0 and action[2] > 0)

    def test_corrective_steering_can_limit_speed_below_reference_envelope(self):
        action, diagnostic = V3Controller(circle_env(60, 70), "steer_limit").act()
        self.assertLessEqual(diagnostic["target_speed"], diagnostic["steering_speed_limit"])
        self.assertTrue(np.isfinite(action).all())

    def test_default_is_selected_responsive_stage_not_failed_limit(self):
        env = circle_env(60)
        default = V3Controller(env)
        self.assertEqual(default.stage, "responsive")
        np.testing.assert_array_equal(default.act()[0], V3Controller(env, "responsive").act()[0])


if __name__ == "__main__":
    unittest.main()
