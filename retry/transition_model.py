"""Small, coordinate invariant transition regression for offline research.

Only an initial state and an explicitly supplied action sequence enter rollout.
Fitted parameters and experimental data belong outside the public repository.
"""

from dataclasses import dataclass

import numpy as np


def rotation(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, -s], [s, c]])


def wrap(angle):
    return (angle + np.pi) % (2 * np.pi) - np.pi


@dataclass
class MotionState:
    position: np.ndarray
    heading: float
    velocity: np.ndarray
    yaw_rate: float
    auxiliary: np.ndarray


def local_state(state):
    return np.r_[rotation(state.heading).T @ state.velocity,
                 state.yaw_rate, state.auxiliary]


def transition_target(before, after):
    return np.r_[rotation(before.heading).T @ (after.position - before.position),
                 wrap(after.heading - before.heading),
                 local_state(after) - local_state(before)]


def polynomial(values):
    values = np.asarray(values, dtype=float)
    i, j = np.triu_indices(values.shape[-1])
    return np.concatenate([np.ones((*values.shape[:-1], 1)), values,
                           values[..., i] * values[..., j]], axis=-1)


class PolynomialTransition:
    def __init__(self, ridge, use_action=True, auxiliary_bounds=None):
        if not np.isfinite(ridge) or ridge <= 0:
            raise ValueError("ridge must be finite and positive")
        self.ridge = float(ridge)
        self.use_action = use_action
        self.auxiliary_bounds = auxiliary_bounds

    def inputs(self, state, action):
        values = local_state(state)
        return np.r_[values, action] if self.use_action else values

    def fit(self, before, actions, after, weights=None):
        if not len(before) == len(actions) == len(after):
            raise ValueError("aligned training arrays required")
        x = np.array([self.inputs(s, a) for s, a in zip(before, actions)])
        y = np.array([transition_target(s, t) for s, t in zip(before, after)])
        if not len(x) or not np.isfinite(x).all() or not np.isfinite(y).all():
            raise ValueError("finite nonempty training transitions required")
        self.input_mean = x.mean(0)
        self.input_scale = np.maximum(x.std(0), 1e-6)
        features = polynomial((x - self.input_mean) / self.input_scale)
        self.feature_mean = features.mean(0)
        self.feature_scale = np.maximum(features.std(0), 1e-6)
        self.feature_mean[0], self.feature_scale[0] = 0., 1.
        features = (features - self.feature_mean) / self.feature_scale
        weights = np.ones(len(x)) if weights is None else np.asarray(weights)
        if (weights.shape != (len(x),) or not np.isfinite(weights).all()
                or np.any(weights <= 0)):
            raise ValueError("positive finite sample weights required")
        weighted = features * weights[:, None]
        penalty = np.eye(features.shape[1]) * weights.sum() * self.ridge
        penalty[0, 0] = 0.
        self.coefficients = np.linalg.solve(features.T @ weighted + penalty,
                                           weighted.T @ y)
        return self

    def step(self, state, action):
        x = (self.inputs(state, action) - self.input_mean) / self.input_scale
        features = (polynomial(x) - self.feature_mean) / self.feature_scale
        delta = features @ self.coefficients
        heading = float(wrap(state.heading + delta[2]))
        local = local_state(state) + delta[3:]
        auxiliary = local[3:]
        if self.auxiliary_bounds is not None:
            auxiliary = np.clip(auxiliary, *self.auxiliary_bounds)
        return MotionState(state.position + rotation(state.heading) @ delta[:2],
                           heading, rotation(heading) @ local[:2],
                           float(local[2]), auxiliary)

    def rollout(self, initial, actions):
        predictions, current = [], initial
        for action in actions:
            current = self.step(current, action)
            predictions.append(current)
        return predictions
