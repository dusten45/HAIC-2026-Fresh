"""Privileged research tracker: fixed Stanley steering with existing speed law.

The static planner is OracleTeacher's. The monotonic lookahead reference below
is retained solely for the inherited longitudinal heuristic. Steering instead
uses the front-wheel midpoint and the nearest local path segment, following
Thrun et al. (2006), section 9.2, basic equation (7). This is not a participant
Agent; the paper's ideal-model convergence guarantee is not assumed here.
"""

import numpy as np

from retry.oracle_teacher import OracleTeacher


GAIN_PER_S = 1.0
MIN_DENOMINATOR_SPEED_M_S = 1.0
FRONT_AXLE_OFFSET_M = 1.6
STEERING_LIMIT_RAD = .4


def steering_from_front_error(heading, tangent, cross_track_right_m, speed):
    """Return HAIC action steering, before the inherited command smoothing.

    Hull heading zero points along world +y; positive heading turns left.
    Right-positive cross-track error calls for a positive (left) joint angle.
    car_racing passes -action[0] to Car.steer, so action has the opposite sign.
    Speed is the current COM velocity norm, as in the inherited speed law.
    """
    tangent = np.asarray(tangent, dtype=float)
    path_heading = float(np.arctan2(-tangent[0], tangent[1]))
    heading_error = float((path_heading - heading + np.pi) % (2. * np.pi) - np.pi)
    correction = float(np.arctan(GAIN_PER_S * cross_track_right_m /
                                max(speed, MIN_DENOMINATOR_SPEED_M_S)))
    joint_command = heading_error + correction
    action = -float(np.clip(joint_command, -STEERING_LIMIT_RAD, STEERING_LIMIT_RAD))
    return action, heading_error, correction, joint_command


class StanleyTeacher(OracleTeacher):
    """One fixed steering law; no reacquisition state or spatial target table."""

    def reset(self, road, obstacles, road_half_width):
        super().reset(road, obstacles, road_half_width)
        self.path_arc = np.r_[0., np.cumsum(self.ds)]
        self.path_arc_length = float(self.path_arc[-1])
        self.cursor_arc_unwrapped = None
        self.previous_cursor_arc = None
        self.previous_target_arc = None

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
        # Preserve the hull cursor, target phase and longitudinal speed heuristic.
        cursor_arc = float(self.path_arc[self.cursor])
        if self.cursor_arc_unwrapped is None:
            self.cursor_arc_unwrapped = cursor_arc
        else:
            increment = (cursor_arc - self.previous_cursor_arc + self.path_arc_length / 2.) % self.path_arc_length - self.path_arc_length / 2.
            self.cursor_arc_unwrapped += increment
        self.previous_cursor_arc = cursor_arc
        raw_target_arc = self.cursor_arc_unwrapped + lookahead
        target_arc = raw_target_arc
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

        # Front anchors are (+/-55, +80) * .02 in car_dynamics hull coordinates.
        front = position + FRONT_AXLE_OFFSET_M * forward
        front_candidates = (self.cursor + np.arange(-10, 41)) % n
        a = self.path[front_candidates]
        segment = self.path[(front_candidates + 1) % n] - a
        squared = np.maximum(np.sum(segment * segment, axis=1), 1e-12)
        fractions = np.clip(np.sum((front - a) * segment, axis=1) / squared, 0., 1.)
        projections = a + fractions[:, None] * segment
        nearest = int(np.argmin(np.sum((front - projections) ** 2, axis=1)))
        tangent = segment[nearest] / np.sqrt(squared[nearest])
        path_right = np.array([tangent[1], -tangent[0]])
        cross_track = float(np.dot(front - projections[nearest], path_right))
        raw_steer, heading_error, correction, joint_command = steering_from_front_error(
            heading, tangent, cross_track, speed)
        steer = .8 * raw_steer + .2 * self.previous_steer
        self.previous_steer = steer
        target_speed = min(float(self.speed_profile[self.cursor]), np.sqrt(self.LATERAL_ACCELERATION / (abs(curvature) + .002)))
        if y <= 0 or abs(np.arctan2(x, y)) > .85:
            target_speed = min(target_speed, 4.)
        gas = float(np.clip(.12 * (target_speed - speed), 0., .5))
        brake = float(np.clip(.08 * (speed - target_speed), 0., .5))
        action = np.asarray([steer, gas, brake], dtype=np.float32)
        self.last_diagnostic = {'path_cursor': self.cursor, 'target_world': target.tolist(),
            'target_body': [x, y], 'speed_m_s': speed, 'target_speed_m_s': float(target_speed),
            'lookahead_m': lookahead, 'curvature_command': curvature,
            'distance_to_reference_point_m': float(np.sqrt(np.min(distances))),
            'cursor_arc_unwrapped_m': self.cursor_arc_unwrapped, 'raw_target_arc_unwrapped_m': raw_target_arc,
            'target_arc_unwrapped_m': target_arc, 'target_arc_held_m': target_arc - raw_target_arc,
            'front_world': front.tolist(), 'front_projection_world': projections[nearest].tolist(),
            'front_path_segment': int(front_candidates[nearest]),
            'front_cross_track_right_m': cross_track, 'path_heading_error_left_rad': heading_error,
            'cross_track_correction_left_rad': correction, 'joint_command_unclipped_left_rad': joint_command,
            'raw_steer_action': raw_steer,
            'front_distance_to_segment_m': float(np.linalg.norm(front - projections[nearest]))}
        return action
