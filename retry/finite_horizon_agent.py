"""Different planning assumption: evaluate short attainable motion arcs, not grid goals."""

import cv2
import numpy as np

from retry.motion_model import advance_front_angle
from retry.temporal_agent import TemporalRouteAgent


class FiniteHorizonAgent(TemporalRouteAgent):
    def __init__(self, speed_gain, speed_bias, yaw_coefficient):
        super().__init__(speed_gain, speed_bias)
        self.yaw_coefficient = float(yaw_coefficient)

    def reset(self, observation):
        super().reset(observation)
        self.front_angle = 0.0

    def act(self, observation):
        image = observation[-1]
        speed = max(0.0, self.speed_gain * float(image[74:83, 9:14].sum()) + self.speed_bias)
        obstacles = self.tracked_obstacles(image, speed)
        road = ((image > 0.32) & (image < 0.47)).astype(np.uint8)
        road[61:] = 0
        road = cv2.morphologyEx(road, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
        distance = cv2.distanceTransform(road, cv2.DIST_L2, 5)
        horizon = float(np.clip(4 + 0.35 * speed, 6, 14))
        traveled = np.arange(0, horizon + 0.001, 0.5)
        feasible = []
        for primitive in np.linspace(-0.4, 0.4, 9):
            steer = float(0.8 * primitive + 0.2 * self.controller.previous_steer)
            angle, tangent = advance_front_angle(self.front_angle, steer)
            curvature = self.yaw_coefficient * tangent
            if abs(curvature) < 1e-8:
                xs, ys = np.zeros_like(traveled), traveled
            else:
                xs = (1 - np.cos(curvature * traveled)) / curvature
                ys = np.sin(curvature * traveled) / curvature
            visible = ys >= 7 / 1.701
            if not np.any(visible):
                continue
            px, py = np.rint(42 + 1.3608 * xs[visible]).astype(int), np.rint(63 - 1.701 * ys[visible]).astype(int)
            if np.any(px < 3) or np.any(px >= 81) or np.any(py < 24) or np.any(py > 56):
                continue
            clearance = distance[py, px]
            if np.any(clearance < 1.5):
                continue
            if any(np.min((xs - x) ** 2 + (ys - y) ** 2) <= (2.6 + radius) ** 2 for x, y, radius in obstacles):
                continue
            # Lexicographic road margin then mean margin, without tuned weights.
            rank = (float(np.min(clearance)), float(np.mean(clearance)), -abs(steer - self.controller.previous_steer))
            feasible.append((rank, steer, angle, curvature))
        if not feasible:
            self.front_angle, _ = advance_front_angle(self.front_angle, self.controller.previous_steer)
            return self.controller.action(None, speed)
        _, steer, angle, curvature = max(feasible, key=lambda value: value[0])
        self.front_angle, self.controller.previous_steer = angle, steer
        target = min(28.0, float(np.sqrt(5.0 / (abs(curvature) + 0.003))))
        gas = float(np.clip(0.08 * (target - speed), 0, 0.5))
        brake = float(np.clip(0.04 * (speed - target), 0, 0.5))
        return np.array([steer, gas, brake], dtype=np.float32)
