import unittest
from dataclasses import FrozenInstanceError
import operator
from types import SimpleNamespace
from typing import Any, cast

import numpy as np

from oracle.v2_controller import STAGE_CONFIG, V2Controller


def circle_env(radius=30, speed=20):
    angles = np.linspace(0, 2 * np.pi, 120, endpoint=False)
    points = radius * np.column_stack([np.cos(angles), np.sin(angles)])
    return SimpleNamespace(
        track=[(0, 0, *p) for p in points],
        track_variables=SimpleNamespace(obstacles=[]),
        car=SimpleNamespace(hull=SimpleNamespace(
            position=(radius, 0), linearVelocity=(0, speed), angle=0)),
    )


class TestV2Controller(unittest.TestCase):
    def test_stage_table_is_immutable_and_preserves_ablation_settings(self):
        self.assertEqual(V2Controller.STAGES, (
            "speed", "braking", "profile", "control", "lookahead", "racing", "linked", "integrated", "fast", "pace"))
        for stage, config in STAGE_CONFIG.items():
            with self.subTest(stage=stage):
                self.assertEqual(config.braking_preview, stage != "speed")
                self.assertEqual(config.acceleration_profile, stage == "profile")
                self.assertEqual(config.adaptive_lookahead,
                                 stage in ("lookahead", "racing", "linked", "integrated", "fast", "pace"))
                self.assertEqual((config.gas_gain, config.brake_gain),
                                 (.14, .12) if stage in ("speed", "braking", "profile") else (.025, .015))
                self.assertEqual(config.straight_limit, 30 if stage in ("fast", "pace") else 24)
                self.assertEqual(config.lateral_limit, 8.0 if stage == "pace" else 5.5)
                self.assertEqual(config.corridor_limit, 4.2 if stage in ("integrated", "fast", "pace") else 3.0)
                self.assertEqual(config.minimum_speed, 9)
                self.assertEqual((config.lookahead_base, config.lookahead_speed_gain, config.lookahead_curvature_gain,
                                  config.lookahead_min, config.lookahead_max, config.lookahead_slew,
                                  config.curvature_preview_min, config.curvature_preview_time),
                                 (6, .4, 12, 6, 17, .35, 12, .8))
        with self.assertRaises(TypeError):
            operator.setitem(cast(Any, STAGE_CONFIG), "pace", STAGE_CONFIG["fast"])
        with self.assertRaises(FrozenInstanceError):
            setattr(STAGE_CONFIG["pace"], "straight_limit", 24)

    def test_curvature_speed_is_not_uniform(self):
        tight = V2Controller(circle_env(15), stage="speed")
        gentle = V2Controller(circle_env(60), stage="speed")
        self.assertLess(np.mean(tight.speed_limits), np.mean(gentle.speed_limits))

    def test_braking_previews_a_future_apex(self):
        controller = V2Controller(circle_env(60), stage="braking")
        controller.speed_limits[:] = 24
        controller.speed_limits[8] = 9
        action, diagnostic = controller.act()
        self.assertGreater(diagnostic["limiting_distance"], 15)
        self.assertLess(diagnostic["target_speed"], 20)
        self.assertGreater(action[2], 0)
        self.assertEqual(action[1], 0)

    def test_actions_are_finite_and_bounded(self):
        action, _ = V2Controller(circle_env(), stage="braking").act()
        self.assertTrue(np.isfinite(action).all())
        self.assertGreaterEqual(action[0], -1)
        self.assertLessEqual(action[0], 1)
        self.assertTrue(((action[1:] >= 0) & (action[1:] <= 1)).all())

    def test_profile_respects_acceleration_and_braking(self):
        controller = V2Controller(circle_env(60), stage="profile")
        squared = controller.speed_profile**2
        distances = np.diff(np.r_[controller.arcs, controller.path.length])
        differences = np.roll(squared, -1) - squared
        self.assertTrue((differences <= 6 * distances + 1e-8).all())
        self.assertTrue((-differences <= 10 * distances + 1e-8).all())
        self.assertTrue((controller.speed_profile <= controller.speed_limits + 1e-8).all())

    def test_integrated_corridors_do_not_constrain_remote_obstacles(self):
        env = circle_env(60)
        env.track_variables.obstacles = [
            SimpleNamespace(position=(0, 58), radius=1.2),
            SimpleNamespace(position=(0, -62), radius=1.2),
        ]
        controller = V2Controller(env, stage="integrated")
        for obstacle in env.track_variables.obstacles:
            _, distance, _ = controller.path.project(obstacle.position)
            self.assertGreater(abs(distance), 4.1)
        displacement = np.linalg.norm(controller.path.points - controller.centerline.points, axis=1)
        self.assertLessEqual(float(np.max(displacement)), 4.2 + 1e-8)
        at_gate = np.minimum(controller.centerline.cumulative[:-1],
                             controller.centerline.length - controller.centerline.cumulative[:-1]) < 20
        np.testing.assert_allclose(controller.path.points[at_gate], controller.centerline.points[at_gate])

    def test_adaptive_lookahead_shortens_tight_turns(self):
        _, tight = V2Controller(circle_env(15, 10), stage="lookahead").act()
        _, fast = V2Controller(circle_env(120, 24), stage="lookahead").act()
        self.assertLess(tight["lookahead"], fast["lookahead"])

    def test_gentle_feedback_matches_speed_error(self):
        action, diagnostic = V2Controller(circle_env(60, 20), stage="control").act()
        error = diagnostic["target_speed"] - 20
        self.assertAlmostEqual(float(action[1]), max(0, .025 * error), places=6)
        self.assertAlmostEqual(float(action[2]), max(0, -.015 * error), places=6)

    def test_pace_changes_curvature_envelope_not_only_fixed_speed(self):
        gentle = V2Controller(circle_env(60), stage="fast")
        pace = V2Controller(circle_env(60), stage="pace")
        self.assertGreater(np.mean(pace.speed_limits), np.mean(gentle.speed_limits))
        self.assertLess(np.min(pace.speed_limits), 30)
        self.assertLessEqual(np.max(pace.speed_limits), 30)

    def test_default_is_selected_high_speed_teacher(self):
        default = V2Controller(circle_env(60))
        selected = V2Controller(circle_env(60), stage="pace")
        self.assertEqual(default.stage, "pace")
        np.testing.assert_array_equal(default.path.points, selected.path.points)
        np.testing.assert_array_equal(default.act()[0], selected.act()[0])


if __name__ == "__main__":
    unittest.main()
