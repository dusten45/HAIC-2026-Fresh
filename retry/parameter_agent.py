"""Two speed-law parameters; preserve perception, routing, steering and memory."""

import numpy as np

from retry.connected_agent import ConnectedTemporalAgent
from retry.geometry_agent import GeometryController


class SpeedController(GeometryController):
    def __init__(self, speed_cap, lateral_acceleration):
        super().__init__()
        self.speed_cap = float(speed_cap)
        self.lateral_acceleration = float(lateral_acceleration)

    def action_target(self, x, forward, speed):
        curvature = 2 * x / max(forward * forward + x * x, 1e-6)
        steer = float(np.clip(np.arctan(3.24 * curvature), -0.4, 0.4))
        steer = 0.8 * steer + 0.2 * self.previous_steer
        self.previous_steer = steer
        target = min(self.speed_cap, float(np.sqrt(self.lateral_acceleration / (abs(curvature) + 0.003))))
        gas = float(np.clip(0.08 * (target - speed), 0, 0.5))
        brake = float(np.clip(0.04 * (speed - target), 0, 0.5))
        return np.array([steer, gas, brake], dtype=np.float32)


class ParameterizedConnectedAgent(ConnectedTemporalAgent):
    def __init__(self, speed_gain, speed_bias, speed_cap=28.0, lateral_acceleration=5.0):
        super().__init__(speed_gain, speed_bias)
        self.controller = SpeedController(speed_cap, lateral_acceleration)
