"""Synthetic coordinate and recursive-input checks without simulator calls."""

import unittest

import numpy as np

from retry.transition_model import (
    MotionState, PolynomialTransition, rotation, transition_target,
)


class TransitionTests(unittest.TestCase):
    def state(self, speed=1.):
        return MotionState(np.zeros(2), 0., np.array([0., speed]), 0., np.zeros(1))

    def test_target_is_invariant_to_world_rotation_and_translation(self):
        a, b = self.state(), self.state(2.)
        b.position, b.heading = np.array([.1, .2]), .1
        r, offset = rotation(.7), np.array([100., -10.])
        transformed = [MotionState(r @ s.position + offset, s.heading + .7,
                                   r @ s.velocity, s.yaw_rate, s.auxiliary)
                       for s in [a, b]]
        np.testing.assert_allclose(transition_target(a, b),
                                   transition_target(*transformed), atol=1e-12)

    def test_rollout_passes_its_own_predicted_state(self):
        model = PolynomialTransition(.001)
        received = []
        def step(state, action):
            received.append(state.velocity[1])
            return self.state(state.velocity[1] + action[1])
        model.step = step
        outputs = model.rollout(self.state(), [[0., 1., 0.]] * 5)
        self.assertEqual(received, [1., 2., 3., 4., 5.])
        self.assertEqual(outputs[-1].velocity[1], 6.)

    def test_fit_scaling_is_training_only_and_prediction_does_not_mutate_it(self):
        before = [self.state(v) for v in range(1, 21)]
        after = [self.state(v + .1) for v in range(1, 21)]
        for state in after:
            state.position[1] = state.velocity[1] * .08
        model = PolynomialTransition(.001).fit(before, np.zeros((20, 3)), after)
        saved = model.input_mean.copy()
        model.rollout(self.state(100.), [[1., 1., 1.]] * 5)
        np.testing.assert_array_equal(saved, model.input_mean)


if __name__ == "__main__":
    unittest.main()
