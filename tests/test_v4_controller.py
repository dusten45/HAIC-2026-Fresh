import hashlib
from pathlib import Path
import unittest

import numpy as np

from oracle.v3_controller import V3Controller
from oracle.v4_controller import V4Controller
from tests.test_v2_controller import circle_env as v2_circle_env


def circle_env(radius=60, speed=0):
    env = v2_circle_env(radius, speed)
    env.car.hull.angularVelocity = 0
    return env


class TestV4Controller(unittest.TestCase):
    def test_v3_executable_checkpoint_is_frozen(self):
        root = Path(__file__).resolve().parents[1]
        hashes = {
            "oracle/v3_controller.py": "dd4f008e4279933209079eb220badab21d84fe404466387ca4fd027f76efea03",
            "oracle/v3_runner.py": "1f156e4c722de73e91ccae6bc4527e1f49cd18058744398ec9a363197cc76018",
        }
        for name, expected in hashes.items():
            with self.subTest(source=name):
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), expected)

    def test_reference_stage_preserves_v3_actions_and_line(self):
        env = circle_env(60)
        baseline = V3Controller(env)
        reference = V4Controller(env, "responsive")
        np.testing.assert_array_equal(reference.path.points, baseline.path.points)
        np.testing.assert_array_equal(reference.act()[0], baseline.act()[0])

    def test_standing_launch_does_not_force_a_stop_at_the_finish(self):
        controller = V4Controller(circle_env(60, 0), "profile")
        self.assertEqual(controller.launch_profile[0], 0)
        self.assertEqual(controller.launch_arcs[-1], controller.path.length)
        self.assertGreater(controller.launch_profile[-1], 20)
        self.assertTrue((controller.speed_profile <= controller.speed_limits + 1e-8).all())

    def test_grip_budget_reduces_available_longitudinal_acceleration(self):
        controller = V4Controller(circle_env(60, 0), "profile")
        straight = controller._longitudinal_limits(60, 0)
        turning = controller._longitudinal_limits(60, .04)
        self.assertLess(turning[0], straight[0])
        self.assertLessEqual(turning[1], straight[1])

    def test_feedforward_changes_launch_actuation_not_path_or_profile(self):
        env = circle_env(60, 0)
        feedback = V4Controller(env, "profile")
        feedforward = V4Controller(env, "feedforward")
        np.testing.assert_array_equal(feedback.path.points, feedforward.path.points)
        np.testing.assert_array_equal(feedback.speed_profile, feedforward.speed_profile)
        a_feedback, _ = feedback.act()
        a_feedforward, diagnostic = feedforward.act()
        self.assertGreater(diagnostic["acceleration_feedforward"], 0)
        self.assertGreater(a_feedforward[1], a_feedback[1])

    def test_planned_stages_have_finite_bounded_exclusive_actions(self):
        for stage in ("profile", "feedforward", "guarded", "midpoint"):
            for speed in (0, 50, 100):
                with self.subTest(stage=stage, speed=speed):
                    action, _ = V4Controller(circle_env(60, speed), stage).act()
                    self.assertTrue(np.isfinite(action).all())
                    self.assertTrue(-1 <= action[0] <= 1)
                    self.assertTrue(((action[1:] >= 0) & (action[1:] <= 1)).all())
                    self.assertFalse(action[1] > 0 and action[2] > 0)

    def test_cyclic_profile_satisfies_coupled_acceleration_and_braking(self):
        controller = V4Controller(circle_env(60, 0), "guarded")
        controller.speed_limits[len(controller.arcs) // 2] = 20
        controller._plan_profile()
        squared = controller.speed_profile**2
        distances = np.diff(np.r_[controller.arcs, controller.path.length])
        bends = np.maximum(abs(controller.curvature), np.roll(abs(controller.curvature), -1))
        for i, distance in enumerate(distances):
            j = (i + 1) % len(squared)
            acceleration, braking = controller._longitudinal_limits(
                np.sqrt(max(squared[i], squared[j])), bends[i])
            self.assertLessEqual(squared[j] - squared[i], 2 * acceleration * distance + 1e-5)
            self.assertLessEqual(squared[i] - squared[j], 2 * braking * distance + 1e-5)

    def test_feedforward_averages_multiple_speed_nodes_over_action_interval(self):
        controller = V4Controller(circle_env(60, 40), "feedforward")
        controller.launch_arcs = np.array([0, 1, 3, 4, controller.path.length])
        controller.launch_profile = np.array([40, 41, 42, 43, 43], dtype=float)
        distance = np.diff(controller.launch_arcs)
        controller.profile_acceleration = np.diff(controller.launch_profile**2) / (2 * distance)
        controller.profile_times = np.r_[0, np.cumsum(
            2 * distance / (controller.launch_profile[:-1] + controller.launch_profile[1:]))]
        _, diagnostic = controller.act()
        expected = (np.interp(.08, controller.profile_times, controller.launch_profile) - 40) / .08
        self.assertAlmostEqual(diagnostic["acceleration_feedforward"], expected, places=6)
        self.assertNotAlmostEqual(expected, controller.profile_acceleration[0], places=2)

    def test_midpoint_changes_only_gas_inverse_not_planned_profile(self):
        env = circle_env(60, 0)
        previous = V4Controller(env, "guarded")
        midpoint = V4Controller(env, "midpoint")
        np.testing.assert_array_equal(previous.launch_profile, midpoint.launch_profile)
        previous_action, _ = previous.act()
        action, diagnostic = midpoint.act()
        acceleration = diagnostic["commanded_acceleration"]
        self.assertAlmostEqual(diagnostic["inverse_speed"], .04 * acceleration)
        self.assertAlmostEqual(float(action[1]), acceleration * 29.2498
                               * (.04 * acceleration + 2.7) / 80000, places=6)
        self.assertGreater(action[1], previous_action[1])

    def test_runtime_grip_budget_includes_measured_yaw_demand(self):
        env = circle_env(60, 50)
        env.car.hull.angularVelocity = 3
        _, diagnostic = V4Controller(env, "guarded").act()
        self.assertGreaterEqual(diagnostic["lateral_acceleration_estimate"], 150)

    def test_default_is_measured_midpoint_candidate(self):
        env = circle_env(60, 0)
        default = V4Controller(env)
        self.assertEqual(default.stage, "midpoint")
        np.testing.assert_array_equal(default.act()[0], V4Controller(env, "midpoint").act()[0])


if __name__ == "__main__":
    unittest.main()
