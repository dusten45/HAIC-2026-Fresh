"""Pixel route candidate. Privileged positions never enter this module."""

import cv2
import numpy as np

from retry.geometry_agent import GeometryController
from retry.pixel_agent import PixelAgent


def road_and_obstacles(image):
    road = ((image > 0.32) & (image < 0.47)).astype(np.uint8)
    road[61:] = 0
    closed = cv2.morphologyEx(road, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    holes = ((closed != 0) & (road == 0) & (image >= 0.64) & (image <= 0.71)).astype(np.uint8)
    holes[61:] = 0
    count, _, stats, centers = cv2.connectedComponentsWithStats(holes, connectivity=8)
    obstacles = []
    for index in range(1, count):
        _, _, width, height, area = stats[index]
        if 3 <= area <= 30 and 2 <= width <= 9 and 2 <= height <= 9:
            cx, cy = centers[index]
            obstacles.append(((float(cx) - 42) / 1.3608, (63 - float(cy)) / 1.701, 1.2))
    repaired = np.where(closed, np.float32(0.4), image)
    centers = PixelAgent().road_centers(repaired)
    path = [((x - 42) / 1.3608, (63 - row) / 1.701) for row, x in centers]
    return path, obstacles


def path_x(path, forward):
    for a, b in zip(path[:-1], path[1:]):
        if (a[1] - forward) * (b[1] - forward) <= 0 and abs(b[1] - a[1]) > 1e-8:
            return float(a[0] + (b[0] - a[0]) * (forward - a[1]) / (b[1] - a[1]))
    if path:
        return float(min(path, key=lambda p: abs(p[1] - forward))[0])
    return None


def clearance_target(path, obstacles):
    far = path_x(path, (63 - 36) / 1.701)
    if far is None:
        return None
    for x, y, _ in sorted(obstacles, key=lambda p: p[1]):
        if not -4 <= y <= 35:
            continue
        center = path_x(path, y)
        if center is None or abs(x - center) >= 3.2:
            continue
        candidates = [goal for goal in [x - 3.2, x + 3.2] if abs(goal - center) <= 5]
        if not candidates:
            continue
        goal = min(candidates, key=lambda value: abs(value - center))
        far += goal - center
        break
    return float(42 + far * 1.3608)


class ClearanceAgent:
    def __init__(self, speed_gain, speed_bias):
        self.speed_gain, self.speed_bias = float(speed_gain), float(speed_bias)
        self.controller = GeometryController()

    def reset(self, observation):
        self.controller.reset()

    def act(self, observation):
        path, obstacles = road_and_obstacles(observation[-1])
        target = clearance_target(path, obstacles)
        integral = float(observation[-1, 74:83, 9:14].sum())
        speed = max(0.0, self.speed_gain * integral + self.speed_bias)
        return self.controller.action(target, speed)
