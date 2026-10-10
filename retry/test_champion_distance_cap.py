import unittest
import numpy as np

from retry.champion_distance_cap import ChampionDistanceCapMixin, near_distance_cap
from retry.parameter_agent import SpeedController


class Base:
    def __init__(self):
        self.controller = SpeedController(28, 5)
        self.hazards = []

    def act(self, observation):
        x, forward, speed = observation
        if x is None:
            return self.controller.action(None, speed)
        return self.controller.action_target(x, forward, speed)


class Limited(ChampionDistanceCapMixin, Base):
    pass


class ChampionDistanceCapTests(unittest.TestCase):
    def test_fixed_envelope_front_eligibility_floor_and_release(self):
        cap, eligible, clearances = near_distance_cap([(0, 6, 1.2, 0)], 0)
        self.assertAlmostEqual(clearances[0], 2.2)
        self.assertAlmostEqual(cap, np.sqrt(22))
        self.assertEqual(len(eligible), 1)
        self.assertEqual(near_distance_cap([(0, 2, 1.2, 0)], 0)[0], 4)
        self.assertEqual(near_distance_cap([(0, -2, 1.2, 0), (20, 2, 1.2, 0)], 0)[0], 28)
        self.assertEqual(near_distance_cap([], 20)[0], 28)

    def test_only_pedals_change_original_steering_memory_and_fallback_survive(self):
        original, limited = Base(), Limited()
        for i in range(30):
            limited.hazards = [(0, 4, 1.2, 0)]
            observation = ((-1) ** i * .03, 8, 10)
            before = original.act(observation)
            after = limited.act(observation)
            self.assertEqual(before[0], after[0])
            self.assertEqual(original.controller.previous_steer, limited.controller.previous_steer)
            self.assertEqual(after[1], 0)
            self.assertAlmostEqual(float(after[2]), .24, places=6)
        limited.hazards = []
        self.assertTrue(np.array_equal(original.act((.4, 8, 10)), limited.act((.4, 8, 10))))
        self.assertFalse(limited.distance_cap_diagnostic["cap_active"])
        self.assertTrue(np.array_equal(original.act((None, 8, 10)), limited.act((None, 8, 10))))
        self.assertIsNone(limited.distance_cap_diagnostic)


if __name__ == "__main__":
    unittest.main()
