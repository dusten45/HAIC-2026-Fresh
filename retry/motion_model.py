"""Actuator prediction from public steering commands and simulator constants."""

import numpy as np


def advance_front_angle(angle, command):
    target = float(np.clip(command, -0.4, 0.4))
    tangents = []
    for _ in range(4):
        angle += float(np.clip(50 * (target - angle), -3, 3)) * 0.02
        tangents.append(np.tan(angle))
    return angle, float(np.mean(tangents))
