"""Localize a conservative speed law using existing observed hazard geometry."""

import numpy as np

from retry.connected_agent import connected_route
from retry.parameter_agent import ParameterizedConnectedAgent
from retry.route_agent import route_target


class HazardScheduledAgent(ParameterizedConnectedAgent):
    def __init__(self, speed_gain, speed_bias, speed_cap, lateral_fast, lateral_safe):
        super().__init__(speed_gain, speed_bias, speed_cap, lateral_fast)
        self.lateral_fast, self.lateral_safe = float(lateral_fast), float(lateral_safe)

    def act(self, observation):
        image = observation[-1]
        speed = max(0.0, self.speed_gain * float(image[74:83, 9:14].sum()) + self.speed_bias)
        obstacles = self.tracked_obstacles(image, speed)
        lookahead = float(np.clip(4 + 0.35 * speed, 6, 14))
        near = not getattr(self, "warming_fixed_reference", False) and any(
            y > 0 and np.hypot(x, y) <= lookahead + 2.6 + radius for x, y, radius in obstacles)
        self.controller.lateral_acceleration = self.lateral_safe if near else self.lateral_fast
        target = route_target(connected_route(image, obstacles), speed)
        if target is None:
            return self.controller.action(None, speed)
        return self.controller.action_target(float(target[0]), float(target[1]), speed)
