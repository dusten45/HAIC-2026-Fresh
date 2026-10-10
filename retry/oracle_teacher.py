"""Research-only map planner and classical controller with privileged inputs.

This is not a participant Agent and is never imported by the pixel submission.
reset receives the actual static road (alpha,beta,x,y), obstacle circles and
road half-width. act receives current hull position/heading and COM velocity.
No simulator object, seed, clock, reward, collision flag, future vehicle
trajectory, or recorded policy action is accepted. Planned map waypoints are
reference geometry, not future realized states.
"""

import itertools

import numpy as np


def _finite_array(value, shape_last):
    result = np.asarray(value, dtype=np.float64)
    if result.ndim != 2 or result.shape[1] != shape_last or not np.isfinite(result).all():
        raise ValueError("Malformed or nonfinite static geometry")
    return result.copy()


def segment_clearance(points, obstacles):
    """Minimum reference-origin distance to each static obstacle circle center."""
    a, b = points, np.roll(points, -1, axis=0)
    delta = b - a
    squared = np.maximum(np.sum(delta * delta, axis=1), 1e-12)
    distances = []
    for x, y, _ in obstacles:
        u = np.clip(np.sum((np.array([x, y]) - a) * delta, axis=1) / squared, 0., 1.)
        distances.append(float(np.min(np.linalg.norm(a + u[:, None] * delta - [x, y], axis=1))))
    return np.asarray(distances)


def path_curvature(points):
    before, after = points - np.roll(points, 1, axis=0), np.roll(points, -1, axis=0) - points
    lb, la = np.linalg.norm(before, axis=1), np.linalg.norm(after, axis=1)
    turn = np.arctan2(before[:,0] * after[:,1] - before[:,1] * after[:,0], np.sum(before * after, axis=1))
    return turn / np.maximum(.5 * (lb + la), 1e-8)


class OracleTeacher:
    """Fixed conservative law; only its geometric plan depends on the map."""

    # Lateral road allowance differs from circular obstacle inflation: a
    # 2.9m disc used for both would remove some perfectly usable corridors.
    ROAD_LATERAL_ALLOWANCE = 1.65
    OBSTACLE_ORIGIN_ALLOWANCE = 3.1
    DETOUR_EXTRA_MARGIN = .2
    DETOUR_HALF_LENGTH = 30.0
    MAP_SPACING = .75
    SPEED_CAP = 14.0
    LATERAL_ACCELERATION = 3.0
    BRAKING_ACCELERATION = 2.5
    NEAR_OBSTACLE_SPEED = 6.0

    def reset(self, road, obstacles, road_half_width):
        road = _finite_array(road, 4)
        obstacles = _finite_array(obstacles, 3)
        if len(road) < 12 or np.any(obstacles[:,2] <= 0):
            raise ValueError("Insufficient road or invalid obstacle radius")
        if not np.isfinite(road_half_width) or road_half_width <= self.ROAD_LATERAL_ALLOWANCE:
            raise ValueError("Invalid road half-width")
        center = road[:,2:4]
        normals = np.column_stack((np.cos(road[:,1]), np.sin(road[:,1])))
        length = np.linalg.norm(np.roll(center, -1, axis=0) - center, axis=1)
        if np.any(length < 1e-6):
            raise ValueError("Degenerate road segment")
        source_s = np.concatenate(([0.], np.cumsum(length)))
        self.loop_length = float(source_s[-1])
        sample_s = np.linspace(0., self.loop_length, max(24, int(np.ceil(self.loop_length / self.MAP_SPACING))), endpoint=False)
        extended_center = np.vstack((center, center[0]))
        extended_normals = np.vstack((normals, normals[0]))
        center = np.column_stack([np.interp(sample_s, source_s, extended_center[:,j]) for j in (0,1)])
        normals = np.column_stack([np.interp(sample_s, source_s, extended_normals[:,j]) for j in (0,1)])
        normals /= np.linalg.norm(normals, axis=1)[:,None]
        usable_offset = float(road_half_width - self.ROAD_LATERAL_ALLOWANCE)
        self.obstacles = obstacles
        self.centerline = center
        self.normals = normals
        self.sample_s = sample_s
        bumps, amplitude_options = [], []
        segment = np.roll(center, -1, axis=0) - center
        denominator = np.sum(segment * segment, axis=1)
        for x, y, radius in obstacles:
            point = np.array([x,y])
            fraction = np.clip(np.sum((point - center) * segment, axis=1) / denominator, 0., 1.)
            projections = center + fraction[:,None] * segment
            nearest = int(np.argmin(np.sum((projections - point) ** 2, axis=1)))
            normal = (1. - fraction[nearest]) * normals[nearest] + fraction[nearest] * normals[(nearest + 1) % len(center)]
            normal /= np.linalg.norm(normal)
            lateral = float(np.dot(point - projections[nearest], normal))
            s_obstacle = sample_s[nearest] + fraction[nearest] * self.loop_length / len(center)
            ds = (sample_s - s_obstacle + self.loop_length / 2.) % self.loop_length - self.loop_length / 2.
            bump = np.where(np.abs(ds) <= self.DETOUR_HALF_LENGTH,
                .5 * (1. + np.cos(np.pi * ds / self.DETOUR_HALF_LENGTH)), 0.)
            clearance_goal = float(radius + self.OBSTACLE_ORIGIN_ALLOWANCE + self.DETOUR_EXTRA_MARGIN)
            options = [0.] if abs(lateral) >= clearance_goal else [lateral - clearance_goal, lateral + clearance_goal]
            options = [a for a in options if abs(a) <= usable_offset]
            if not options:
                raise ValueError("No lateral corridor under this teacher's geometric allowance")
            bumps.append(bump)
            amplitude_options.append(options)

        best = None
        # At most 2^6 side combinations in the official six-obstacle map.
        # This is static path planning, not simulator rollout/parameter search.
        if len(obstacles) > 10:
            raise ValueError("Bounded research planner supports at most ten obstacles")
        for amplitudes in itertools.product(*amplitude_options):
            offset = np.zeros(len(center))
            for amplitude, bump in zip(amplitudes, bumps):
                offset += amplitude * bump
            if np.max(np.abs(offset)) > usable_offset:
                continue
            path = center + offset[:,None] * normals
            clearance = segment_clearance(path, obstacles)
            if len(clearance) and np.any(clearance < obstacles[:,2] + self.OBSTACLE_ORIGIN_ALLOWANCE):
                continue
            curvature = path_curvature(path)
            ds = np.linalg.norm(np.roll(path, -1, axis=0) - path, axis=1)
            cost = float(np.sum(ds * (1. + 35. * curvature ** 2)) + .015 * np.sum(offset ** 2) * self.loop_length / len(center))
            if best is None or cost < best[0]:
                best = (cost, path, curvature, ds, clearance, tuple(amplitudes), offset)
        if best is None:
            raise ValueError("No reference path clears all obstacles under this geometric approximation")
        _, self.path, curvature, self.ds, clearance, amplitudes, offset = best
        caps = np.minimum(self.SPEED_CAP, np.sqrt(self.LATERAL_ACCELERATION / (np.abs(curvature) + .002)))
        for x, y, _ in obstacles:
            near = np.linalg.norm(self.path - [x,y], axis=1) < 14.
            caps[near] = np.minimum(caps[near], self.NEAR_OBSTACLE_SPEED)
        # Periodic backward braking envelope, including the loop seam.
        for _ in range(3):
            for i in range(len(caps) - 1, -1, -1):
                caps[i] = min(caps[i], np.sqrt(caps[(i + 1) % len(caps)] ** 2 + 2. * self.BRAKING_ACCELERATION * self.ds[i]))
        self.speed_profile = caps
        self.cursor = None
        self.previous_steer = 0.
        self.plan_diagnostic = {'path_points': len(self.path), 'centerline_length_m': self.loop_length,
            'planned_length_m': float(np.sum(self.ds)), 'side_amplitudes_m': list(amplitudes),
            'reference_origin_clearance_m': clearance.tolist(), 'max_abs_lateral_offset_m': float(np.max(np.abs(offset))),
            'min_planned_speed_m_s': float(np.min(caps)), 'max_planned_speed_m_s': float(np.max(caps)),
            'footprint_guarantee': False, 'privileged_research_only': True}

    def act(self, position, heading, velocity):
        position, velocity = np.asarray(position, dtype=float), np.asarray(velocity, dtype=float)
        if position.shape != (2,) or velocity.shape != (2,) or not np.isfinite([*position, heading, *velocity]).all():
            raise ValueError("Invalid current privileged state")
        speed = float(np.linalg.norm(velocity))
        n = len(self.path)
        candidates = np.arange(n) if self.cursor is None else (self.cursor + np.arange(-10, 41)) % n
        distances = np.sum((self.path[candidates] - position) ** 2, axis=1)
        self.cursor = int(candidates[np.argmin(distances)])
        lookahead = float(np.clip(3. + .20 * speed, 3., 6.))
        remaining, i = lookahead, self.cursor
        for _ in range(n):
            next_i = (i + 1) % n
            if self.ds[i] >= remaining:
                target = self.path[i] + (self.path[next_i] - self.path[i]) * remaining / max(self.ds[i], 1e-8)
                break
            remaining -= self.ds[i]
            i = next_i
        else:
            raise ValueError("Degenerate reference path")
        delta = target - position
        right = np.array([np.cos(heading), np.sin(heading)])
        forward = np.array([-np.sin(heading), np.cos(heading)])
        x, y = float(np.dot(delta, right)), float(np.dot(delta, forward))
        curvature = 2. * x / max(float(np.dot(delta, delta)), 1e-6)
        raw_steer = float(np.clip(np.arctan(3.24 * curvature), -.4, .4))
        steer = .8 * raw_steer + .2 * self.previous_steer
        self.previous_steer = steer
        target_speed = min(float(self.speed_profile[self.cursor]), np.sqrt(self.LATERAL_ACCELERATION / (abs(curvature) + .002)))
        if y <= 0 or abs(np.arctan2(x, y)) > .85:
            target_speed = min(target_speed, 4.)
        gas = float(np.clip(.12 * (target_speed - speed), 0., .5))
        brake = float(np.clip(.08 * (speed - target_speed), 0., .5))
        action = np.asarray([steer, gas, brake], dtype=np.float32)
        self.last_diagnostic = {'path_cursor': self.cursor, 'target_world': target.tolist(),
            'target_body': [x,y], 'speed_m_s': speed, 'target_speed_m_s': float(target_speed),
            'lookahead_m': lookahead, 'curvature_command': curvature,
            'distance_to_reference_point_m': float(np.sqrt(np.min(distances)))}
        return action
