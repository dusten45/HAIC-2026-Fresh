"""Diagnostic action-channel perturbation, never installed in the champion.

The pixel actor runs once and its memory is untouched. Only the applied steering
is offset for a predeclared short pulse. Gas/brake remain byte-identical to that
actor's output at the same input; later observations can change all outputs.
"""
import numpy as np


def apply_steering_pulse(original, offset):
    original = np.asarray(original, dtype=np.float32)
    assert original.shape == (3,) and np.isfinite(original).all()
    assert offset in (-0.08, 0.0, 0.08)
    changed = original.copy()
    if offset:
        changed[0] = np.clip(float(original[0]) + offset, -0.4, 0.4)
    assert changed[1:].tobytes() == original[1:].tobytes()
    return changed
