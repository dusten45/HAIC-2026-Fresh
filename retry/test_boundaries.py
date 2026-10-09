"""Critical evaluation boundaries beyond the upstream contract tests."""

import ast
import datetime as dt
from pathlib import Path
import unittest
from unittest.mock import patch

import gymnasium as gym
import numpy as np

from env_wrapper import CarEnvironment
from retry.evaluate import check_window, window_open


class TickEnvironment(gym.Env):
    observation_space = gym.spaces.Box(0, 255, (96, 96, 3), dtype=np.uint8)
    action_space = gym.spaces.Box(-1, 1, (3,), dtype=np.float32)

    def __init__(self):
        self.car = type("Car", (), {"set_damage_effects": lambda *args: None})()
        self.track = [None] * 10
        self.tile_visited_count = 0
        self.tick = 0
        self.positive_tick = None
        self.collision_ticks = set()
        self.finish_tick = None

    def reset(self, **kwargs):
        self.tick = 0
        return np.zeros((96, 96, 3), dtype=np.uint8), {}

    def step(self, action):
        self.tick += 1
        return np.full((96, 96, 3), self.tick % 256, dtype=np.uint8), (
            1.0 if self.tick == self.positive_tick else -0.1), False, (
            self.tick == self.finish_tick), {"collision": self.tick in self.collision_ticks}


class BoundaryTests(unittest.TestCase):
    def test_warmup_not_in_agent_stack_history(self):
        raw = TickEnvironment()
        env = CarEnvironment(raw)
        obs, _ = env.reset()
        self.assertEqual(raw.tick, 50)
        self.assertTrue(np.array_equal(obs[0], obs[-1]))
        self.assertAlmostEqual(float(obs[-1, 0, 0]), 50 / 255, places=6)

    def test_stack_oldest_first_and_one_image_per_action(self):
        env = CarEnvironment(TickEnvironment(), no_operation=0)
        old, _ = env.reset()
        obs, *_ = env.step([0, 0, 0])
        self.assertTrue(np.array_equal(old[1:], obs[:3]))
        self.assertAlmostEqual(float(obs[-1, 0, 0]), 4 / 255, places=6)

    def test_offtrack_exactly_101_actions(self):
        env = CarEnvironment(TickEnvironment(), no_operation=0)
        env.reset()
        for _ in range(100):
            _, _, ended, _, _ = env.step([0, 0, 0])
            self.assertFalse(ended)
        _, _, ended, _, info = env.step([0, 0, 0])
        self.assertTrue(ended)
        self.assertEqual(info["retire_reason"], "off_track")

    def test_nonnegative_aggregate_resets_offtrack_counter(self):
        raw = TickEnvironment()
        env = CarEnvironment(raw, no_operation=0)
        env.reset()
        for _ in range(3):
            env.step([0, 0, 0])
        raw.positive_tick = raw.tick + 2
        env.step([0, 0, 0])
        self.assertEqual(env.off_track_counter, 0)

    def test_collision_in_early_skip_tick_not_lost(self):
        raw = TickEnvironment()
        raw.collision_ticks = {1}
        env = CarEnvironment(raw, no_operation=0)
        env.reset()
        _, _, _, _, info = env.step([0, 0, 0])
        self.assertTrue(info["collision"])
        self.assertEqual(info["damage"], 0.2)

    def test_window_endpoint_is_exclusive(self):
        plan = {"start_utc": "2030-01-01T00:00:00+00:00", "deadline_utc": "2030-01-02T00:00:00+00:00"}
        with patch("retry.evaluate.now", return_value=dt.datetime.fromisoformat(plan["start_utc"])):
            check_window(plan)
            self.assertTrue(window_open(plan))
        with patch("retry.evaluate.now", return_value=dt.datetime.fromisoformat(plan["deadline_utc"])):
            self.assertFalse(window_open(plan))
            with self.assertRaises(RuntimeError):
                check_window(plan)

    def test_policy_cannot_import_environment_or_forbidden_modules(self):
        tree = ast.parse(Path(__file__).with_name("pixel_agent.py").read_text())
        modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                modules.append(node.module)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, {"exec", "eval", "compile", "__import__", "open"})
        self.assertEqual(modules, ["numpy"])


if __name__ == "__main__":
    unittest.main()
