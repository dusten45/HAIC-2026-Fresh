"""Synthetic feature-boundary checks; no simulator or teacher action calls."""
from contextlib import ExitStack
import unittest
from unittest.mock import patch

import numpy as np

from retry.imitation_features import PixelMemoryFeatures
from retry.temporal_agent import TemporalRouteAgent


class ImitationFeatureTests(unittest.TestCase):
    def observation(self):
        observation = np.full((4, 84, 84), .6, dtype=np.float32)
        observation[:, :61, 27:57] = .4
        observation[:, 61:] = 0.
        return observation

    def test_no_teacher_decision_or_controller_instantiation(self):
        forbidden = ["retry.schedule_agent.HazardScheduledAgent.act",
                     "retry.geometry_agent.GeometryController.__init__",
                     "retry.geometry_agent.GeometryController.action",
                     "retry.parameter_agent.SpeedController.action_target",
                     "retry.connected_agent.connected_route", "retry.route_agent.route_target",
                     "retry.temporal_agent.route_target", "retry.pixel_agent.PixelAgent.act"]
        with ExitStack() as stack:
            for name in forbidden:
                stack.enter_context(patch(name, side_effect=AssertionError("teacher decision called")))
            extractor = PixelMemoryFeatures(1., 0.)
            x = extractor.observe(self.observation())
        self.assertEqual(x.shape, (95,))
        self.assertEqual(len(extractor.feature_names), 95)
        np.testing.assert_array_equal(x[4:55].reshape(17, 3)[:, 2], np.ones(17))

    def test_previous_action_is_shifted_own_copy_and_pixels_are_current(self):
        extractor = PixelMemoryFeatures(1., 0.)
        observation = self.observation()
        first = extractor.observe(observation)
        action = np.array([.2, .25, .1], dtype=np.float32)
        extractor.record_action(action)
        action[:] = 0.
        observation[-1, 74:83, 9:14] = .2
        second = extractor.observe(observation)
        np.testing.assert_allclose(second[1:4], [.5, .5, .2])
        np.testing.assert_array_equal(first[1:4], np.zeros(3))
        self.assertGreater(second[0], first[0])
        extractor.reset(observation)
        np.testing.assert_array_equal(extractor.previous_action, np.zeros(3))

    def test_tracker_updates_once_and_retained_age_is_a_feature(self):
        extractor = PixelMemoryFeatures(1., 0.)
        observation = self.observation()
        observation[-1, 45:48, 40:42] = .68
        original = TemporalRouteAgent.tracked_obstacles
        with patch.object(TemporalRouteAgent, "tracked_obstacles", wraps=original) as update:
            first = extractor.observe(observation)
            second = extractor.observe(self.observation())
            self.assertEqual(update.call_count, 2)
        self.assertEqual(first[59], 1.)
        self.assertEqual(first[58], 0.)
        self.assertEqual(second[59], 1.)
        self.assertEqual(second[58], 1 / 8)


if __name__ == "__main__":
    unittest.main()
