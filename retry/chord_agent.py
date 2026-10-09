"""Test whether the controller target skips an otherwise safe obstacle detour."""

import numpy as np

from retry.connected_agent import connected_route
from retry.route_agent import route_target
from retry.schedule_agent import HazardScheduledAgent


def clear_chord(point, obstacles):
    squared = float(np.dot(point, point))
    for x, y, radius in obstacles:
        if y <= 0:
            continue
        obstacle = np.array([x, y])
        closest = point * np.clip(np.dot(point, obstacle) / max(squared, 1e-8), 0, 1)
        if np.linalg.norm(obstacle - closest) <= 2.6 + radius:
            return False
    return True


def chord_target(path, speed, obstacles):
    target = route_target(path, speed)
    if target is None or clear_chord(target, obstacles):
        return target
    remaining = float(np.clip(4 + .35 * speed, 6, 14))
    selected = None
    for a, b in zip(np.asarray(path)[:-1], np.asarray(path)[1:]):
        length = float(np.linalg.norm(b - a))
        if length > remaining:
            break
        remaining -= length
        if clear_chord(b, obstacles):
            selected = b
    return selected if selected is not None else target


class ChordTargetAgent(HazardScheduledAgent):
    def act(self, observation):
        if getattr(self, "warming_reference", False):
            return super().act(observation)
        image = observation[-1]
        speed = max(0., self.speed_gain * float(image[74:83, 9:14].sum()) + self.speed_bias)
        obstacles = self.tracked_obstacles(image, speed)
        lookahead = float(np.clip(4 + .35 * speed, 6, 14))
        near = any(y > 0 and np.hypot(x, y) <= lookahead + 2.6 + radius for x, y, radius in obstacles)
        self.controller.lateral_acceleration = self.lateral_safe if near else self.lateral_fast
        target = chord_target(connected_route(image, obstacles), speed, obstacles)
        if target is None:
            return self.controller.action(None, speed)
        return self.controller.action_target(float(target[0]), float(target[1]), speed)
