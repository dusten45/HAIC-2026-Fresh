"""Local coupled-grip and feedforward teacher, preserving frozen oracle-v3."""

from dataclasses import dataclass
import math
from types import MappingProxyType

import numpy as np

from .v3_controller import STAGE_CONFIG as V3_CONFIG, V3Config, V3Controller


@dataclass(frozen=True)
class V4Config(V3Config):
    grip_acceleration: float = 210.98
    acceleration_feedforward: bool = False
    profile_control: bool = True
    buffered_profile: bool = True
    legacy_braking_guard: bool = False
    gas_midpoint: bool = False


STAGE_CONFIG = MappingProxyType({
    "pace": V4Config(**vars(V3_CONFIG["pace"]), profile_control=False),
    "responsive": V4Config(**vars(V3_CONFIG["responsive"]), profile_control=False),
    "profile": V4Config(**vars(V3_CONFIG["responsive"])),
    "feedforward": V4Config(**vars(V3_CONFIG["responsive"]), acceleration_feedforward=True),
    "guarded": V4Config(**vars(V3_CONFIG["responsive"]), acceleration_feedforward=True,
                        buffered_profile=False, legacy_braking_guard=True),
    "midpoint": V4Config(**vars(V3_CONFIG["responsive"]), acceleration_feedforward=True,
                         buffered_profile=False, legacy_braking_guard=True, gas_midpoint=True),
})


class V4Controller(V3Controller):
    STAGES = tuple(STAGE_CONFIG)

    def __init__(self, base_env, stage="midpoint"):
        if stage not in self.STAGES:
            raise ValueError(stage)
        super().__init__(base_env, stage="responsive")
        self.stage = stage
        self.config = STAGE_CONFIG[stage]
        if not self.config.profile_control:
            if stage == "pace":
                self.speed_limits = np.clip(np.sqrt(self.config.lateral_limit
                    / np.maximum(np.abs(self.curvature), 1e-5)),
                    self.config.minimum_speed, self.config.straight_limit)
            return
        self._plan_profile()
        self.start_arc, _, _ = self.path.project(base_env.car.hull.position)
        self.last_arc = self.start_arc
        self.travelled = 0.0
        self.launch_arcs = np.r_[self.arcs, self.path.length]
        steady_squared = np.interp((self.start_arc + self.launch_arcs) % self.path.length,
                                  self.launch_arcs, np.r_[self.speed_profile**2,
                                                         self.speed_profile[0]**2])
        launch_squared = steady_squared.copy()
        launch_squared[0] = min(launch_squared[0], float(np.linalg.norm(
            base_env.car.hull.linearVelocity))**2)
        launch_curvature = np.interp((self.start_arc + self.launch_arcs) % self.path.length,
                                    self.launch_arcs, np.r_[self.curvature, self.curvature[0]])
        for i, distance in enumerate(np.diff(self.launch_arcs)):
            bend = max(abs(launch_curvature[i]), abs(launch_curvature[i + 1]))
            launch_squared[i + 1] = self._forward_bound(
                launch_squared[i], launch_squared[i + 1], bend, distance)
        self.launch_profile = np.sqrt(launch_squared)
        self.profile_acceleration = np.diff(launch_squared) / (2 * np.diff(self.launch_arcs))
        self.profile_times = np.r_[0.0, np.cumsum(2 * np.diff(self.launch_arcs)
            / np.maximum(self.launch_profile[:-1] + self.launch_profile[1:], 1e-8))]

    def _longitudinal_limits(self, speed, curvature):
        lateral = abs(curvature) * speed**2
        residual = math.sqrt(max(0.0, 1 - (lateral / self.config.grip_acceleration)**2))
        # Rear-wheel traction must accelerate both vehicle and passive front-wheel
        # spin. Its acceleration budget differs from all-wheel braking's budget.
        acceleration = min(43.7736 * residual, 80000 / (29.2498 * (speed + 2.7)))
        braking = min(self.config.braking_deceleration, self.config.grip_acceleration * residual)
        return acceleration, braking

    def _forward_bound(self, before, limit, curvature, distance):
        if limit <= before:
            return limit
        acceleration, _ = self._longitudinal_limits(math.sqrt(limit), curvature)
        if limit <= before + 2 * acceleration * distance:
            return limit
        low = before
        high = min(limit, before + 2 * 43.7736 * distance)
        for _ in range(16):
            middle = .5 * (low + high)
            acceleration, _ = self._longitudinal_limits(math.sqrt(middle), curvature)
            if middle <= before + 2 * acceleration * distance:
                low = middle
            else:
                high = middle
        return low

    def _plan_profile(self):
        intervals = np.diff(np.r_[self.arcs, self.path.length])
        bends = np.maximum(np.abs(self.curvature), np.abs(np.roll(self.curvature, -1)))
        squared = self.speed_limits**2

        def reachable(values):
            for _ in range(16):
                previous = values.copy()
                for i in range(len(values) - 1, -1, -1):
                    following = (i + 1) % len(values)
                    next_squared = values[following]
                    if values[i] > next_squared:
                        scale = 1 + (2 * intervals[i] * bends[i])**2
                        discriminant = max(0.0, scale * self.config.grip_acceleration**2
                                           - (bends[i] * next_squared)**2)
                        bound = (next_squared + 2 * intervals[i] * math.sqrt(discriminant)) / scale
                        values[i] = min(values[i], bound,
                                        next_squared + 2 * self.config.braking_deceleration * intervals[i])
                for i, distance in enumerate(intervals):
                    following = (i + 1) % len(values)
                    values[following] = self._forward_bound(values[i], values[following], bends[i], distance)
                if np.max(previous - values) < 1e-6:
                    break
            return values

        squared = reachable(squared)
        # Preserve v3's braking buffer without looking ahead to accelerate before
        # the current corner has cleared. Restore reachability after this shift.
        if self.config.buffered_profile:
            preview_arcs = (self.arcs + self.config.braking_margin
                            + self.config.reaction_time * np.sqrt(squared)) % self.path.length
            buffered = np.interp(preview_arcs, np.r_[self.arcs, self.path.length],
                                 np.r_[squared, squared[0]])
            squared = reachable(np.minimum(squared, buffered))
        self.speed_profile = np.sqrt(squared)

    def act(self):
        action, diagnostic = super().act()
        if not self.config.profile_control:
            return action, diagnostic
        arc = diagnostic["path_arc"]
        delta = (arc - self.last_arc + .5 * self.path.length) % self.path.length - .5 * self.path.length
        self.travelled = max(0.0, self.travelled + delta)
        self.last_arc = arc
        speed = diagnostic["speed"]
        reference_arc = min(self.travelled, self.path.length)
        squared = self.launch_profile**2
        target_speed = math.sqrt(float(np.interp(reference_arc, self.launch_arcs, squared)))
        index = min(int(np.searchsorted(self.launch_arcs, reference_arc, side="right") - 1),
                    len(self.profile_acceleration) - 1)
        elapsed = 2 * (reference_arc - self.launch_arcs[index]) / max(
            self.launch_profile[index] + target_speed, 1e-8)
        profile_time = self.profile_times[index] + elapsed
        future_speed = float(np.interp(profile_time + self.config.reaction_time,
                                       self.profile_times, self.launch_profile))
        averaged_acceleration = (future_speed - target_speed) / self.config.reaction_time
        feedforward = averaged_acceleration if self.config.acceleration_feedforward else 0.0
        # Position-only feedback otherwise cannot leave an exactly zero-speed
        # start. Both stages get the same one-interval launch bootstrap only.
        bootstrap_distance = max(.01, .5 * max(self.profile_acceleration[0], 0)
                                 * self.config.reaction_time**2)
        if self.travelled < bootstrap_distance:
            target_speed = max(target_speed, float(np.interp(
                self.config.reaction_time, self.profile_times, self.launch_profile)))
        curvature = float(np.interp(arc, np.r_[self.arcs, self.path.length],
                                    np.r_[self.curvature, self.curvature[0]]))
        yaw_curvature = abs(float(self.env.car.hull.angularVelocity)) / max(speed, 1e-8)
        budget_curvature = max(abs(curvature), yaw_curvature)
        acceleration_limit, braking_limit = self._longitudinal_limits(speed, budget_curvature)
        nominal_acceleration = feedforward + self.config.speed_error_gain * (target_speed - speed)
        if self.config.legacy_braking_guard:
            guard_target = diagnostic["target_speed"]
            nominal_acceleration = min(nominal_acceleration,
                                       self.config.speed_error_gain * (guard_target - speed))
            diagnostic.update(guard_target_speed=guard_target)
        acceleration = float(np.clip(nominal_acceleration,
                                     -braking_limit, acceleration_limit))
        inverse_speed = speed
        if self.config.gas_midpoint:
            inverse_speed += .5 * max(acceleration, 0) * self.config.reaction_time
        action[1] = np.clip(acceleration * 29.2498 * (inverse_speed + 2.7) / 80000, 0, 1)
        action[2] = np.clip(-acceleration / 303.8958, 0, .89)
        diagnostic.update(target_speed=target_speed, commanded_acceleration=acceleration,
                          acceleration_feedforward=feedforward, profile_arc=reference_arc,
                          travelled=self.travelled, acceleration_limit=acceleration_limit,
                          braking_limit=braking_limit, profile_curvature=curvature,
                          profile_time=profile_time,
                          inverse_speed=inverse_speed,
                          lateral_acceleration_estimate=budget_curvature * speed**2)
        return action, diagnostic
