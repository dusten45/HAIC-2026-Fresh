"""Aim at the observable obstacle passage instead of a shifted distant target."""

import numpy as np

from retry.arc_agent import ArcAgent, arc_target
from retry.clearance_agent import path_x, road_and_obstacles


def passage_target(path, obstacles):
    if not path:
        return None
    for x, y, _ in sorted(obstacles, key=lambda p: p[1]):
        if not 0 < y <= 18:
            continue
        center = path_x(path, y)
        if center is None or abs(x - center) >= 3.2:
            continue
        candidates = [goal for goal in [x - 3.2, x + 3.2] if abs(goal - center) <= 5]
        if candidates:
            return min(candidates, key=lambda value: abs(value - center)), max(y, 3.0)
    return None


class WaypointAgent(ArcAgent):
    def act(self, observation):
        path, obstacles = road_and_obstacles(observation[-1])
        integral = float(observation[-1, 74:83, 9:14].sum())
        speed = max(0.0, self.speed_gain * integral + self.speed_bias)
        target = passage_target(path, obstacles)
        if target is None:
            target = arc_target(path, speed, obstacles)
        if target is None:
            return self.controller.action(None, speed)
        return self.controller.action_target(float(target[0]), float(target[1]), speed)
