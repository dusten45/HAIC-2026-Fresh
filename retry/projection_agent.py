"""Pixel-centre projection hypothesis; no fitted offsets or speed-law changes."""

import numpy as np

from retry.connected_agent import connected_route
from retry.route_agent import route_target
from retry.schedule_agent import HazardScheduledAgent


class PixelCentreAgent(HazardScheduledAgent):
    def __init__(self, speed_gain, speed_bias, speed_cap, lateral_fast, lateral_safe, origin_x, origin_y):
        super().__init__(speed_gain, speed_bias, speed_cap, lateral_fast, lateral_safe)
        self.dx, self.dy = (42 - origin_x) / 1.3608, (origin_y - 63) / 1.701

    def act(self, observation):
        if getattr(self, "warming_reference", False):
            return super().act(observation)
        image = observation[-1]
        speed = max(0., self.speed_gain * float(image[74:83, 9:14].sum()) + self.speed_bias)
        obstacles = self.tracked_obstacles(image, speed)
        lookahead = float(np.clip(4 + .35 * speed, 6, 14))
        near = any(y + self.dy > 0 and np.hypot(x + self.dx, y + self.dy) <= lookahead + 2.6 + radius
            for x, y, radius in obstacles)
        self.controller.lateral_acceleration = self.lateral_safe if near else self.lateral_fast
        # Relative grid distances are invariant to a common origin translation.
        path = connected_route(image, obstacles)
        physical = [(0., 0.)] + [(x + self.dx, y + self.dy) for x, y in path[1:]] if path else []
        target = route_target(physical, speed)
        if target is None:
            return self.controller.action(None, speed)
        return self.controller.action_target(float(target[0]), float(target[1]), speed)
