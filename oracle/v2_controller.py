"""Privileged high-speed teacher experiments, independent of the frozen v1 controller."""

import math
from dataclasses import dataclass
from types import MappingProxyType

import numpy as np

from .oracle_controller import OracleController, TrackPath


@dataclass(frozen=True)
class StageConfig:
    path_mode: str
    braking_preview: bool
    acceleration_profile: bool
    adaptive_lookahead: bool
    gas_gain: float
    brake_gain: float
    straight_limit: float
    lateral_limit: float
    corridor_limit: float
    minimum_speed: float = 9
    lookahead_base: float = 6
    lookahead_speed_gain: float = .4
    lookahead_curvature_gain: float = 12
    lookahead_min: float = 6
    lookahead_max: float = 17
    lookahead_slew: float = .35
    curvature_preview_min: float = 12
    curvature_preview_time: float = .8


STAGE_CONFIG = MappingProxyType({
    "speed": StageConfig("v1", False, False, False, .14, .12, 24, 5.5, 3.0),
    "braking": StageConfig("v1", True, False, False, .14, .12, 24, 5.5, 3.0),
    "profile": StageConfig("v1", True, True, False, .14, .12, 24, 5.5, 3.0),
    "control": StageConfig("v1", True, False, False, .025, .015, 24, 5.5, 3.0),
    "lookahead": StageConfig("v1", True, False, True, .025, .015, 24, 5.5, 3.0),
    "racing": StageConfig("racing", True, False, True, .025, .015, 24, 5.5, 3.0),
    "linked": StageConfig("linked", True, False, True, .025, .015, 24, 5.5, 3.0),
    "integrated": StageConfig("integrated", True, False, True, .025, .015, 24, 5.5, 4.2),
    "fast": StageConfig("integrated", True, False, True, .025, .015, 30, 5.5, 4.2),
    "pace": StageConfig("integrated", True, False, True, .025, .015, 30, 8.0, 4.2),
})


class V2Controller(OracleController):
    """Local high-speed teacher; explicit stages retain the measured ablations."""

    STAGES = tuple(STAGE_CONFIG)

    def __init__(self, base_env, stage="pace"):
        if stage not in self.STAGES:
            raise ValueError(stage)
        super().__init__(base_env, avoid_obstacles=True)
        self.stage = stage
        self.config = STAGE_CONFIG[stage]
        self.last_lookahead = None
        if self.config.path_mode != "v1":
            self._racing_path()
        self.spacing = 2.5
        self.arcs = np.arange(0, self.path.length, self.spacing)
        curvature = []
        for arc in self.arcs:
            before = self.path.sample(arc - 6)
            here = self.path.sample(arc)
            after = self.path.sample(arc + 6)
            left = here - before
            right = after - here
            chord = after - before
            denominator = np.linalg.norm(left) * np.linalg.norm(right) * np.linalg.norm(chord)
            curvature.append(2 * np.cross(left, right) / denominator if denominator else 0)
        self.curvature = np.asarray(curvature)
        self.speed_limits = np.clip(np.sqrt(self.config.lateral_limit / np.maximum(np.abs(self.curvature), 1e-5)),
                                    self.config.minimum_speed, self.config.straight_limit)
        self.speed_profile = self.speed_limits.copy()
        if self.config.acceleration_profile:
            # Couple entry braking and exit acceleration around the entire loop.
            # Forward reachability prevents a discontinuous gas burst just after
            # the limiting apex drops out of the preview window.
            squared = self.speed_limits**2
            intervals = np.diff(np.r_[self.arcs, self.path.length])
            for _ in range(3):
                for i in range(len(squared) - 1, -1, -1):
                    squared[i] = min(squared[i], squared[(i + 1) % len(squared)] + 10 * intervals[i])
                for i in range(len(squared)):
                    following = (i + 1) % len(squared)
                    squared[following] = min(squared[following], squared[i] + 6 * intervals[i])
            self.speed_profile = np.sqrt(squared)

    def _racing_path(self):
        center = self.centerline
        arcs = center.cumulative[:-1]
        tangents = center.delta + np.roll(center.delta, 1, axis=0)
        tangents /= np.linalg.norm(tangents, axis=1)[:, None]
        normals = np.column_stack([-tangents[:, 1], tangents[:, 0]])
        if self.config.path_mode == "racing":
            previous = np.roll(tangents, 1, axis=0)
            angles = np.arctan2(previous[:, 0] * tangents[:, 1] - previous[:, 1] * tangents[:, 0],
                                np.sum(previous * tangents, axis=1))
            bends = angles / center.lengths
            bends = np.mean(np.stack([np.roll(bends, shift) for shift in (-1, 0, 1)]), axis=0)
            signs = np.where(np.abs(bends) > 0.012, np.sign(bends), 0)
            starts = np.flatnonzero((signs != 0) & (signs != np.roll(signs, 1)))
            offsets = np.zeros(len(arcs))
            for start in starts:
                indices = [int(start)]
                while len(indices) < len(arcs):
                    following = (indices[-1] + 1) % len(arcs)
                    if signs[following] != signs[start]:
                        break
                    indices.append(following)
                apex = max(indices, key=lambda i: abs(bends[i]))
                span = (arcs[indices[-1]] - arcs[start]) % center.length
                apex_distance = (arcs[apex] - arcs[start]) % center.length
                # Late apex favors steering release and exit acceleration.
                knots = np.array([-25, -8, apex_distance + min(6, .1 * span), span + 10, span + 25])
                values = signs[start] * np.array([0, -2.2, 2.2, -2.2, 0])
                distance = (arcs - arcs[start] + center.length / 2) % center.length - center.length / 2
                for i in range(4):
                    mask = (distance >= knots[i]) & (distance < knots[i + 1])
                    fraction = (distance[mask] - knots[i]) / (knots[i + 1] - knots[i])
                    blend = .5 * (1 - np.cos(np.pi * fraction))
                    offsets[mask] += values[i] + (values[i + 1] - values[i]) * blend
            offsets = np.clip(offsets, -2.2, 2.2)
        else:
            offsets = self._linked_offsets(normals)
        if self.config.path_mode != "integrated":
            # Preserve the v1 obstacle reference rather than cancel clearance
            # with an additive racing offset. Selected stages optimize jointly.
            obstacle_mask = np.zeros(len(arcs))
            for obstacle in self.env.track_variables.obstacles:
                arc, _, _ = center.project(obstacle.position)
                distance = (arcs - arc + center.length / 2) % center.length - center.length / 2
                blend = .5 * (1 + np.cos(np.pi * np.clip(np.abs(distance) / 30, 0, 1)))
                obstacle_mask = np.maximum(obstacle_mask, blend)
            avoidance = np.sum((self.path.points - center.points) * normals, axis=1)
            offsets = offsets * (1 - obstacle_mask) + avoidance
        self.path = TrackPath(center.points + offsets[:, None] * normals)

    def _linked_offsets(self, normals):
        """Optimize actual geometric curvature over a coupled cyclic corridor.

        A whole-sequence objective permits sacrificing an early corner's exit
        position to straighten the next turn, instead of returning outside after
        every apex. The integrated stage includes obstacle constraints here.
        """
        center = self.centerline
        arcs = center.cumulative[:-1]
        limit = self.config.corridor_limit
        lower = np.full(len(arcs), -limit)
        upper = np.full(len(arcs), limit)
        if self.config.path_mode == "integrated":
            for obstacle in self.env.track_variables.obstacles:
                arc, lateral, _ = center.project(obstacle.position)
                clearance = obstacle.radius + 1.4 + 1.6
                shift = min(0.0, lateral - clearance) if lateral >= 0 else max(0.0, lateral + clearance)
                distance = (arcs - arc + center.length / 2) % center.length - center.length / 2
                # Hold the corridor through the rear-body clearance interval.
                blend = .5 * (1 + np.cos(np.pi * np.clip((np.abs(distance) - 4) / 30, 0, 1)))
                active = blend > 1e-8
                if shift < 0:
                    upper[active] = np.minimum(upper[active], shift * blend[active])
                else:
                    lower[active] = np.maximum(lower[active], shift * blend[active])
        at_gate = np.minimum(arcs, center.length - arcs) < 20
        lower[at_gate] = upper[at_gate] = 0
        offsets = np.clip(np.zeros(len(arcs)), lower, upper)

        def curvature_cost(before, here, after):
            left, right = here - before, after - here
            denominator = (np.linalg.norm(left, axis=1) * np.linalg.norm(right, axis=1)
                           * np.linalg.norm(after - before, axis=1))
            return (2 * (left[:, 0] * right[:, 1] - left[:, 1] * right[:, 0])
                    / np.maximum(denominator, 1e-8))**2

        def objective(values):
            points = center.points + values[:, None] * normals
            return float(np.sum(curvature_cost(np.roll(points, 1, axis=0), points,
                                                  np.roll(points, -1, axis=0)))
                         + 1e-6 * np.sum(values**2))

        learning_rate = 2000.0
        cost = objective(offsets)
        for _ in range(400):
            points = center.points + offsets[:, None] * normals
            previous, following = np.roll(points, 1, axis=0), np.roll(points, -1, axis=0)
            def local_cost(sign):
                changed = points + sign * .02 * normals
                return (curvature_cost(np.roll(points, 2, axis=0), previous, changed)
                        + curvature_cost(previous, changed, following)
                        + curvature_cost(changed, following, np.roll(points, -2, axis=0))
                        + 1e-6 * (offsets + sign * .02)**2)
            gradient = (local_cost(1) - local_cost(-1)) / .04
            candidate = np.clip(offsets - learning_rate * gradient, lower, upper)
            proposed_cost = objective(candidate)
            if proposed_cost < cost:
                offsets, cost = candidate, proposed_cost
                learning_rate = min(5000, learning_rate * 1.03)
            else:
                learning_rate *= .5
                if learning_rate < .01:
                    break
        return offsets

    def act(self):
        action, diagnostic = super().act()
        hull = self.env.car.hull
        position = np.asarray(hull.position, dtype=np.float64)
        velocity = np.asarray(hull.linearVelocity, dtype=np.float64)
        speed = float(np.linalg.norm(velocity))
        arc, _, _ = self.path.project(position)
        distances = (self.arcs - arc) % self.path.length
        if self.config.braking_preview:
            # Backward reachable-speed envelope at each future apex: allow room
            # for braking before the car arrives rather than at the corner.
            allowed = np.sqrt(self.speed_limits**2 + 2 * 5.0 * np.maximum(distances - 3, 0))
            index = int(np.argmin(np.where(distances < 110, allowed, np.inf)))
            target_speed = float(allowed[index])
            if self.config.acceleration_profile:
                target_speed = min(target_speed, float(np.interp(
                    arc, np.r_[self.arcs, self.path.length],
                    np.r_[self.speed_profile, self.speed_profile[0]])))
        else:
            index = int(np.argmin(distances))
            target_speed = float(self.speed_limits[index])
        speed_error = target_speed - speed
        if self.config.adaptive_lookahead:
            preview = np.abs(self.curvature[distances < max(
                self.config.curvature_preview_min, self.config.curvature_preview_time * speed)])
            bend = float(np.max(preview))
            desired = float(np.clip((self.config.lookahead_base + self.config.lookahead_speed_gain * speed)
                                    / (1 + self.config.lookahead_curvature_gain * bend),
                                    self.config.lookahead_min, self.config.lookahead_max))
            lookahead = desired if self.last_lookahead is None else float(np.clip(
                desired, self.last_lookahead - self.config.lookahead_slew,
                self.last_lookahead + self.config.lookahead_slew))
            self.last_lookahead = lookahead
            forward = np.array([-math.sin(hull.angle), math.cos(hull.angle)])
            right = np.array([forward[1], -forward[0]])
            rear = position - 1.64 * forward
            rear_arc, _, _ = self.path.project(rear)
            target = self.path.sample(rear_arc + lookahead)
            displacement = target - rear
            steer = math.atan2(2 * 3.24 * float(displacement @ right),
                               float(displacement @ displacement))
            action[0] = np.clip(steer, -1, 1)
            diagnostic.update(lookahead=lookahead, target=target.tolist(),
                              steer_saturated=abs(steer) >= 0.4)
        action[1] = np.clip(self.config.gas_gain * speed_error, 0, 0.65)
        action[2] = np.clip(-self.config.brake_gain * speed_error, 0, 0.65)
        diagnostic.update(target_speed=target_speed,
                          path_arc=arc,
                          local_speed_limit=float(self.speed_limits[int(np.argmin(distances))]),
                          limiting_distance=float(distances[index]),
                          limiting_apex_speed=float(self.speed_limits[index]),
                          required_braking_distance=max(0.0, (speed**2 - self.speed_limits[index]**2) / 10),
                          limiting_curvature=float(self.curvature[index]),
                          speed=speed)
        return action, diagnostic
