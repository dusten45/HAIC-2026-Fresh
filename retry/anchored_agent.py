"""Arc target measured from the observable vehicle origin, with frozen control."""

import numpy as np

from retry.arc_agent import ArcAgent
from retry.clearance_agent import clearance_target, path_x, road_and_obstacles


def anchored_target(path, speed, obstacles):
    if not path:
        return None
    path = np.asarray(path, dtype=float).copy()
    fixed = clearance_target(path.tolist(), obstacles)
    base = path_x(path.tolist(), 27 / 1.701)
    if fixed is not None and base is not None:
        path[:, 0] += (fixed - 42) / 1.3608 - base
    start = int(np.argmin(np.sum(path[:6] ** 2, axis=1)))
    lookahead = float(np.clip(4 + 0.35 * speed, 6, 14))
    origin_distance = float(np.linalg.norm(path[start]))
    if origin_distance >= lookahead:
        return path[start] * lookahead / origin_distance
    remaining = lookahead - origin_distance
    for a, b in zip(path[start:-1], path[start + 1:]):
        distance = float(np.linalg.norm(b - a))
        if distance > 1e-8 and distance >= remaining:
            return a + (b - a) * remaining / distance
        remaining -= distance
    return path[-1]


class AnchoredAgent(ArcAgent):
    def act(self, observation):
        path, obstacles = road_and_obstacles(observation[-1])
        integral = float(observation[-1, 74:83, 9:14].sum())
        speed = max(0.0, self.speed_gain * integral + self.speed_bias)
        target = anchored_target(path, speed, obstacles)
        if target is None:
            return self.controller.action(None, speed)
        return self.controller.action_target(float(target[0]), float(target[1]), speed)
