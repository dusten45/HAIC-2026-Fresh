"""One trace-derived DEV candidate: limit steering transitions in near mode.

Only the preceding applied steering is retained. Source controller memory and
route selection are untouched; every new call still computes its original path.
The0.18rad bound is an empirical candidate, not a proven dynamics model.
"""
import numpy as np

MAX_NEAR_CHANGE_RAD = 0.18


class SteeringTransitionLimiter:
    def __init__(self):
        self.reset()

    def reset(self):
        self.previous_applied = 0.0

    def apply(self, original, near):
        original = np.asarray(original, dtype=np.float32)
        assert original.shape == (3,) and np.isfinite(original).all()
        applied = original.copy()
        if near and abs(float(original[0]) - self.previous_applied) > MAX_NEAR_CHANGE_RAD:
            applied[0] = self.previous_applied + np.clip(
                float(original[0]) - self.previous_applied,
                -MAX_NEAR_CHANGE_RAD, MAX_NEAR_CHANGE_RAD)
        self.previous_applied = float(applied[0])
        assert applied[1:].tobytes() == original[1:].tobytes()
        return applied
