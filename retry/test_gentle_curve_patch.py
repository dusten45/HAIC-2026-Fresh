"""Synthetic controller fixtures only; no agent, model or environment calls."""
import copy
import math
from types import SimpleNamespace
import unittest

import numpy as np

from retry.gentle_curve_patch import gate, install


class FrozenControllerFixture:
    """Local arithmetic fixture for one inherited action_target invocation."""
    def __init__(self, *, hazards=(), distance_cap=28., previous_steer=-.1):
        self.hazards = list(hazards)
        self.calls = 0
        self.distance = distance_cap
        self.controller = SimpleNamespace(previous_steer=previous_steer,
                                          lateral_acceleration=7., speed_cap=28.)
        self.distance_cap_diagnostic = None
        self.controller.action_target = self._target

    def _target(self, x, forward, speed):
        self.calls += 1
        lookahead = float(np.clip(4 + .35 * speed, 6, 14))
        near = any(y > 0 and math.hypot(hx, y) <= lookahead + 2.6 + r
                   for hx, y, r, _age in self.hazards)
        self.controller.lateral_acceleration = 5. if near else 7.
        k = 2 * x / max(forward * forward + x * x, 1e-6)
        steer = .8 * float(np.clip(np.arctan(3.24 * k), -.4, .4))
        steer += .2 * self.controller.previous_steer
        self.controller.previous_steer = steer
        target = min(28., math.sqrt(self.controller.lateral_acceleration / (abs(k) + .003)),
                     self.distance)
        self.distance_cap_diagnostic = {'effective_target': target,
                                       'distance_cap': self.distance}
        return np.array([steer, np.clip(.08 * (target - speed), 0., .5),
                         np.clip(.04 * (speed - target), 0., .5)], np.float32)


def goal(k, forward=6.):
    return k * forward * forward / (1 + math.sqrt(1 - k * k * forward * forward)), forward


class GentleCurvePatchTests(unittest.TestCase):
    def test_single_call_changes_only_pedals_and_preserves_fullprecision_state(self):
        base, patched = FrozenControllerFixture(), FrozenControllerFixture()
        install(patched, 10)
        x, forward = goal(.03)
        expected = base.controller.action_target(x, forward, 15.)
        actual = patched.controller.action_target(x, forward, 15.)
        self.assertEqual(patched.calls, 1)
        self.assertEqual(actual[0].tobytes(), expected[0].tobytes())
        self.assertEqual(patched.controller.previous_steer, base.controller.previous_steer)
        self.assertEqual(patched.controller.lateral_acceleration, 7.)
        self.assertEqual(patched.distance_cap_diagnostic, base.distance_cap_diagnostic)
        self.assertEqual(patched.hazards, base.hazards)
        self.assertTrue(patched.curve_diagnostic['gate'])
        self.assertGreater(actual[1], expected[1])
        self.assertLess(actual[2], expected[2])
        target = math.sqrt(10 / (.03 + .003))
        self.assertAlmostEqual(patched.curve_diagnostic['applied_final_target'], target)
        self.assertEqual(actual.dtype, np.dtype(np.float32))

    def test_coefficient_seven_is_byte_exact_and_gate_edges_use_fullprecision(self):
        base, patched = FrozenControllerFixture(), FrozenControllerFixture()
        install(patched, 7)
        for k in (.02, -.03, .04, 0., .06):
            x, forward = goal(k)
            expected = base.controller.action_target(x, forward, 15.)
            actual = patched.controller.action_target(x, forward, 15.)
            self.assertEqual(actual.tobytes(), expected.tobytes())
            self.assertEqual(patched.controller.previous_steer, base.controller.previous_steer)
            self.assertEqual(patched.distance_cap_diagnostic, base.distance_cap_diagnostic)
        self.assertEqual(patched.calls, 5)
        for k in (.015, -.015, .05, -.05):
            self.assertTrue(gate(k, .18, False))
        self.assertFalse(gate(np.nextafter(.015, 0.), 0., False))
        self.assertFalse(gate(np.nextafter(.05, 1.), 0., False))
        precise = np.nextafter(.18, 1.)
        self.assertEqual(np.float32(precise), np.float32(.18))
        self.assertFalse(gate(.03, precise, False))
        self.assertFalse(gate(.03, 0., True))

    def test_near_global_and_distance_masking_preserve_original_action(self):
        # Near hazards are excluded, and straight/global-28 rows fail the k gate.
        # Artificial preexisting D=10 checks the outer min contract; this is not
        # an assertion that D<28 occurs on a real frozen near-false gate row.
        for kwargs, k in [({'hazards': [(0., 4., 1.2, 0)], 'distance_cap': 4.}, .03),
                          ({}, 0.), ({'distance_cap': 10.}, .03)]:
            base = FrozenControllerFixture(**copy.deepcopy(kwargs))
            patched = FrozenControllerFixture(**copy.deepcopy(kwargs))
            install(patched, 14)
            x, forward = goal(k)
            expected = base.controller.action_target(x, forward, 15.)
            actual = patched.controller.action_target(x, forward, 15.)
            self.assertEqual(actual.tobytes(), expected.tobytes())
            self.assertEqual(patched.controller.previous_steer, base.controller.previous_steer)
            self.assertEqual(patched.calls, 1)
            self.assertEqual(patched.curve_diagnostic['target_delta'], 0.)
        self.assertLess(math.sqrt(14 / (.015 + .003)), 28.)
        with self.assertRaises(ValueError):
            install(FrozenControllerFixture(), 9)


if __name__ == '__main__':
    unittest.main()
