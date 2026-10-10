"""Research-only speed contrast with a frozen spatial target field.

The table contains reference arc coordinates, not future vehicle states.
It must be prepared outside this module and held identical across arms.
Current speed is used only by the longitudinal law. This is not a pixel Agent.
"""
import numpy as np

from retry.oracle_teacher import OracleTeacher


class SpatialSpeedProbe(OracleTeacher):
    def __init__(self, cursor_arc, target_arc, speed_limit=None):
        self.reference_cursor_arc = np.asarray(cursor_arc, dtype=float).copy()
        self.reference_target_arc = np.asarray(target_arc, dtype=float).copy()
        x, y = self.reference_cursor_arc, self.reference_target_arc
        if (x.ndim != 1 or y.shape != x.shape or len(x) < 2
                or not np.isfinite([x, y]).all() or np.any(np.diff(x) <= 0)
                or np.any(np.diff(y) < 0) or np.any(y < x)):
            raise ValueError('Invalid monotonic spatial reference')
        if speed_limit is not None and (not np.isfinite(speed_limit) or speed_limit <= 0):
            raise ValueError('Invalid speed limit')
        self.speed_limit = speed_limit

    def reset(self, road, obstacles, road_half_width):
        super().reset(road, obstacles, road_half_width)
        self.path_arc = np.r_[0., np.cumsum(self.ds)]
        self.path_arc_length = float(self.path_arc[-1])
        self.cursor_arc_unwrapped = None
        self.previous_cursor_arc = None
        self.previous_target_arc = None

    def prime(self, path_cursor, cursor_arc_unwrapped, previous_cursor_arc,
              previous_target_arc, previous_steer):
        """Prime controller memory after an independently replayed prefix.

        This transfers numeric controller memory, never simulator state.
        The caller must separately verify the actual fork state in each arm.
        """
        if not 0 <= path_cursor < len(self.path):
            raise ValueError('Invalid prefix cursor')
        if not np.isfinite([cursor_arc_unwrapped, previous_cursor_arc,
                            previous_target_arc, previous_steer]).all():
            raise ValueError('Invalid prefix controller memory')
        self.cursor = int(path_cursor)
        self.cursor_arc_unwrapped = float(cursor_arc_unwrapped)
        self.previous_cursor_arc = float(previous_cursor_arc)
        self.previous_target_arc = float(previous_target_arc)
        self.previous_steer = float(previous_steer)

    def act(self, position, heading, velocity):
        position, velocity = np.asarray(position, dtype=float), np.asarray(velocity, dtype=float)
        if position.shape != (2,) or velocity.shape != (2,) or not np.isfinite([*position, heading, *velocity]).all():
            raise ValueError('Invalid current privileged state')
        n = len(self.path)
        candidates = np.arange(n) if self.cursor is None else (self.cursor + np.arange(-10, 41)) % n
        distances = np.sum((self.path[candidates] - position) ** 2, axis=1)
        self.cursor = int(candidates[np.argmin(distances)])
        cursor_arc = float(self.path_arc[self.cursor])
        if self.cursor_arc_unwrapped is None:
            self.cursor_arc_unwrapped = cursor_arc
        else:
            increment = (cursor_arc - self.previous_cursor_arc + self.path_arc_length / 2.) % self.path_arc_length - self.path_arc_length / 2.
            self.cursor_arc_unwrapped += increment
        self.previous_cursor_arc = cursor_arc
        s = self.cursor_arc_unwrapped
        if not self.reference_cursor_arc[0] <= s <= self.reference_cursor_arc[-1]:
            raise ValueError('Current cursor outside frozen reference domain')
        frozen_target_arc = float(np.interp(s, self.reference_cursor_arc, self.reference_target_arc))
        target_arc = frozen_target_arc
        if self.previous_target_arc is not None:
            target_arc = max(target_arc, self.previous_target_arc)
        self.previous_target_arc = target_arc
        phase = target_arc % self.path_arc_length
        index = int(np.searchsorted(self.path_arc, phase, side='right') - 1)
        fraction = (phase - self.path_arc[index]) / max(self.ds[index], 1e-8)
        target = self.path[index] + (self.path[(index + 1) % n] - self.path[index]) * fraction
        delta = target - position
        right = np.array([np.cos(heading), np.sin(heading)])
        forward = np.array([-np.sin(heading), np.cos(heading)])
        x, y = float(np.dot(delta, right)), float(np.dot(delta, forward))
        curvature = 2. * x / max(float(np.dot(delta, delta)), 1e-6)
        raw_steer = float(np.clip(np.arctan(3.24 * curvature), -.4, .4))
        steer = .8 * raw_steer + .2 * self.previous_steer
        self.previous_steer = steer
        speed = float(np.linalg.norm(velocity))
        target_speed = min(float(self.speed_profile[self.cursor]), np.sqrt(self.LATERAL_ACCELERATION / (abs(curvature) + .002)))
        if y <= 0 or abs(np.arctan2(x, y)) > .85:
            target_speed = min(target_speed, 4.)
        if self.speed_limit is not None:
            target_speed = min(target_speed, self.speed_limit)
        gas = float(np.clip(.12 * (target_speed - speed), 0., .5))
        brake = float(np.clip(.08 * (speed - target_speed), 0., .5))
        self.last_diagnostic = {'path_cursor': self.cursor, 'target_world': target.tolist(),
            'target_body': [x, y], 'speed_m_s': speed, 'target_speed_m_s': float(target_speed),
            'lookahead_m': frozen_target_arc - s, 'curvature_command': curvature,
            'unclipped_steer': float(np.arctan(3.24 * curvature)), 'clipped_steer': raw_steer,
            'distance_to_reference_point_m': float(np.sqrt(np.min(distances))),
            'cursor_arc_unwrapped_m': s, 'frozen_target_arc_unwrapped_m': frozen_target_arc,
            'target_arc_unwrapped_m': target_arc, 'target_arc_held_m': target_arc - frozen_target_arc,
            'spatial_reference_only': True}
        return np.asarray([steer, gas, brake], dtype=np.float32)
