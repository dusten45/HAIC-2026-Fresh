"""Privileged high-grip teacher; never part of the submitted pixel-only Agent."""

from dataclasses import dataclass, replace
from types import MappingProxyType

import numpy as np

from .v2_controller import STAGE_CONFIG as V2_CONFIG, StageConfig, V2Controller


@dataclass(frozen=True)
class V3Config(StageConfig):
    braking_deceleration: float = 60
    reaction_time: float = .08
    braking_margin: float = 3
    physical_longitudinal: bool = False
    speed_error_gain: float = 8
    steering_lateral_limit: float | None = None


ENVELOPE = V3Config(**vars(replace(V2_CONFIG["pace"], straight_limit=95, lateral_limit=80)))
STAGE_CONFIG = MappingProxyType({
    "pace": V3Config(**vars(V2_CONFIG["pace"]), braking_deceleration=5, reaction_time=0),
    "envelope": ENVELOPE,
    "drive": replace(ENVELOPE, physical_longitudinal=True),
    "grip": replace(ENVELOPE, physical_longitudinal=True,
                    lateral_limit=160, braking_deceleration=120),
    "responsive": replace(ENVELOPE, physical_longitudinal=True,
                          lateral_limit=160, braking_deceleration=120, lookahead_slew=100),
    "limit": replace(ENVELOPE, physical_longitudinal=True,
                     lateral_limit=190, braking_deceleration=120, lookahead_slew=100),
    "steer_limit": replace(ENVELOPE, physical_longitudinal=True,
                           lateral_limit=190, braking_deceleration=120, lookahead_slew=100,
                           steering_lateral_limit=160),
})


class V3Controller(V2Controller):
    STAGES = tuple(STAGE_CONFIG)

    def __init__(self, base_env, stage="responsive"):
        if stage not in self.STAGES:
            raise ValueError(stage)
        # Reuse v2's integrated obstacle line without editing the frozen teacher.
        super().__init__(base_env, stage="pace")
        self.stage = stage
        self.config = STAGE_CONFIG[stage]
        self.speed_limits = np.clip(np.sqrt(
            self.config.lateral_limit / np.maximum(np.abs(self.curvature), 1e-5)),
            self.config.minimum_speed, self.config.straight_limit)
        squared = self.speed_limits**2
        intervals = np.diff(np.r_[self.arcs, self.path.length])
        for _ in range(2):
            for i in range(len(squared) - 1, -1, -1):
                squared[i] = min(squared[i], squared[(i + 1) % len(squared)]
                                 + 2 * self.config.braking_deceleration * intervals[i])
        self.speed_profile = np.sqrt(squared)

    def act(self):
        action, diagnostic = super().act()
        if self.stage == "pace":
            return action, diagnostic
        speed = diagnostic["speed"]
        distances = (self.arcs - diagnostic["path_arc"]) % self.path.length
        # Include one control interval of travel before braking can take effect.
        available = np.maximum(distances - self.config.braking_margin
                               - self.config.reaction_time * speed, 0)
        allowed = np.sqrt(self.speed_limits**2 + 2 * self.config.braking_deceleration * available)
        index = int(np.argmin(allowed))
        target_speed = float(allowed[index])
        if self.config.steering_lateral_limit is not None:
            # Corrective steering can demand a tighter radius than the planned
            # line. Do not accelerate using reference curvature alone in that case.
            steering_curvature = abs(float(np.tan(np.clip(action[0], -.4, .4)))) / 3.24
            steering_speed_limit = float(np.sqrt(self.config.steering_lateral_limit
                                                / max(steering_curvature, 1e-5)))
            target_speed = min(target_speed, steering_speed_limit)
            diagnostic.update(steering_curvature=steering_curvature,
                              steering_speed_limit=steering_speed_limit)
        error = target_speed - speed
        action[1] = np.clip(self.config.gas_gain * error, 0, .65)
        action[2] = np.clip(-self.config.brake_gain * error, 0, .65)
        if self.config.physical_longitudinal:
            acceleration = float(np.clip(self.config.speed_error_gain * error,
                                         -self.config.braking_deceleration, 43.7736))
            # Wheel inertia contributes to rolling mass. Brake directly reduces
            # wheel spin; these constants derive from the unchanged car dynamics.
            action[1] = np.clip(acceleration * 29.2498 * (speed + 2.7) / 80000, 0, 1)
            action[2] = np.clip(-acceleration / 303.8958, 0, .89)
            diagnostic.update(commanded_acceleration=acceleration)
        diagnostic.update(target_speed=target_speed,
                          limiting_distance=float(distances[index]),
                          limiting_apex_speed=float(self.speed_limits[index]),
                          limiting_curvature=float(self.curvature[index]),
                          required_braking_distance=max(0.0, (speed**2 - self.speed_limits[index]**2)
                                                        / (2 * self.config.braking_deceleration)))
        return action, diagnostic
