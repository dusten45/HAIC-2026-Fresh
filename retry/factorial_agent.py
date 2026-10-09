"""Separate path obstacle beliefs from speed-risk estimates using pixels only."""

import numpy as np

from retry.clearance_agent import road_and_obstacles
from retry.connected_agent import connected_route
from retry.memory_agent import MinimalMemoryAgent
from retry.route_agent import route_target
from retry.schedule_agent import HazardScheduledAgent


class FactorialMemoryAgent(HazardScheduledAgent):
    """Research factor combinations; both trackers observe actual current frames.

    The modes change information sources, never future recorded actions. This
    class is a diagnostic prototype until separately validated from full reset.
    All modes perform the same tracker/detector calls per observed frame.
    """

    def __init__(self, speed_gain, speed_bias, speed_cap, lateral_fast, lateral_safe,
                 path_memory, speed_risk):
        super().__init__(speed_gain, speed_bias, speed_cap, lateral_fast, lateral_safe)
        assert path_memory in ["original", "confirmed", "fresh"]
        assert speed_risk in ["original", "confirmed", "always_safe"]
        values = [speed_gain, speed_bias, speed_cap, lateral_fast, lateral_safe]
        self.original_tracker = HazardScheduledAgent(*values)
        self.confirmed_tracker = MinimalMemoryAgent(*values)
        self.path_memory, self.speed_risk = path_memory, speed_risk

    def reset(self, observation):
        super().reset(observation)
        self.original_tracker.reset(observation)
        self.confirmed_tracker.reset(observation)

    def act(self, observation):
        image = observation[-1]
        speed = max(0., self.speed_gain * float(image[74:83, 9:14].sum()) + self.speed_bias)
        original = self.original_tracker.tracked_obstacles(image, speed)
        confirmed = self.confirmed_tracker.tracked_obstacles(image, speed)
        fresh = road_and_obstacles(image)[1]
        paths = {"original": original, "confirmed": confirmed, "fresh": fresh}
        warm = getattr(self, "warming_reference", False)
        obstacles = paths["original" if warm else self.path_memory]
        risk = paths["original" if warm else (self.speed_risk if self.speed_risk != "always_safe" else "original")]
        lookahead = float(np.clip(4 + .35 * speed, 6, 14))
        near = any(y > 0 and np.hypot(x, y) <= lookahead + 2.6 + radius for x, y, radius in risk)
        if not warm and self.speed_risk == "always_safe":
            near = True
        self.controller.lateral_acceleration = self.lateral_safe if near else self.lateral_fast
        target = route_target(connected_route(image, obstacles), speed)
        self.last_features = {"original": original, "confirmed": confirmed, "fresh": fresh,
            "path_memory": "original" if warm else self.path_memory,
            "speed_risk": "original" if warm else self.speed_risk, "risk_near": near,
            "lateral_acceleration": self.controller.lateral_acceleration,
            "target": None if target is None else target.tolist(), "speed_feature": speed}
        if target is None:
            return self.controller.action(None, speed)
        return self.controller.action_target(float(target[0]), float(target[1]), speed)
