import unittest
import numpy as np

from retry.champion_distance_cap import ChampionDistanceCapMixin
from retry.champion_fresh_distance_cap import ChampionFreshDistanceCapMixin
from retry.parameter_agent import SpeedController


class Base:
    def __init__(self):
        self.controller = SpeedController(28, 5)
        self.hazards = []
        self.target_calls = 0
        target = self.controller.action_target

        def counted(*args):
            self.target_calls += 1
            return target(*args)
        self.controller.action_target = counted

    def act(self, observation):
        x, forward, speed = observation
        if x is None:
            return self.controller.action(None, speed)
        return self.controller.action_target(x, forward, speed)


class OriginalCap(ChampionDistanceCapMixin, Base):
    pass


class FreshCap(ChampionFreshDistanceCapMixin, Base):
    pass


class FreshCapTests(unittest.TestCase):
    def test_current_detection_preserves_cap_action_and_single_controller_call(self):
        old, new = OriginalCap(), FreshCap()
        old.hazards = [(0, 4, 1.2, 0)]
        new.hazards = list(old.hazards)
        for i in range(30):
            obs = ((-1) ** i * .03, 8, 10)
            self.assertTrue(np.array_equal(old.act(obs), new.act(obs)))
            self.assertEqual(new.target_calls, i + 1)
            self.assertEqual(old.controller.previous_steer, new.controller.previous_steer)

    def test_aged_cap_releases_without_deleting_memory_or_changing_steering(self):
        original, old, new = Base(), OriginalCap(), FreshCap()
        hazards = [(0, 4, 1.2, 1)]
        old.hazards = list(hazards)
        new.hazards = hazards
        for i in range(30):
            obs = ((-1) ** i * .03, 8, 10)
            inherited, capped, fresh = original.act(obs), old.act(obs), new.act(obs)
            self.assertTrue(np.array_equal(inherited, fresh))
            self.assertEqual(capped[0], fresh[0])
            self.assertEqual(old.controller.previous_steer, new.controller.previous_steer)
            self.assertIs(new.hazards, hazards)
            self.assertEqual(new.hazards, [(0, 4, 1.2, 1)])
            self.assertEqual(new.target_calls, i + 1)
            self.assertFalse(new.distance_cap_diagnostic["cap_active"])
        self.assertTrue(np.array_equal(original.act((None, 8, 10)), new.act((None, 8, 10))))
        self.assertIsNone(new.distance_cap_diagnostic)

    def test_fresh_hazard_still_limits_when_stronger_aged_hazard_is_present(self):
        only_fresh, mixed = FreshCap(), FreshCap()
        only_fresh.hazards = [(0, 6, 1.2, 0)]
        mixed.hazards = [(0, 2, 1.2, 8), (0, 6, 1.2, 0)]
        self.assertTrue(np.array_equal(only_fresh.act((.03, 8, 10)), mixed.act((.03, 8, 10))))
        self.assertTrue(mixed.distance_cap_diagnostic["cap_active"])
        self.assertEqual(mixed.distance_cap_diagnostic["cap_input_count"], 1)
        self.assertEqual(len(mixed.hazards), 2)


if __name__ == "__main__":
    unittest.main()
