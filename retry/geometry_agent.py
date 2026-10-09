"""Observation-only geometric control, with explicit pixel speed calibration."""

import numpy as np

from retry.pixel_agent import PixelAgent


class GeometryController:
    def __init__(self):
        self.previous_steer = 0.0

    def reset(self):
        self.previous_steer = 0.0

    def action(self, far_x, speed):
        if far_x is None:
            return np.array([self.previous_steer, 0, 0.25], dtype=np.float32)
        x = (far_x - 42) / 1.3608
        length = (63 - 36) / 1.701
        return self.action_target(x, length, speed)

    def action_target(self, x, forward, speed):
        curvature = 2 * x / max(forward * forward + x * x, 1e-6)
        steer = float(np.clip(np.arctan(3.24 * curvature), -0.4, 0.4))
        steer = 0.8 * steer + 0.2 * self.previous_steer
        self.previous_steer = steer
        target = min(28.0, float(np.sqrt(5.0 / (abs(curvature) + 0.003))))
        gas = float(np.clip(0.08 * (target - speed), 0, 0.5))
        brake = float(np.clip(0.04 * (speed - target), 0, 0.5))
        return np.array([steer, gas, brake], dtype=np.float32)


class GeometryAgent:
    def __init__(self, speed_gain, speed_bias):
        self.speed_gain, self.speed_bias = float(speed_gain), float(speed_bias)
        self.extractor = PixelAgent()
        self.controller = GeometryController()

    def reset(self, observation):
        self.controller.reset()

    def act(self, observation):
        centers = self.extractor.road_centers(observation[-1])
        far = None
        if centers:
            rows, xs = np.asarray(centers).T
            far = float(xs[np.argmin(abs(rows - 36))])
        integral = float(observation[-1, 74:83, 9:14].sum())
        speed = max(0.0, self.speed_gain * integral + self.speed_bias)
        return self.controller.action(far, speed)
