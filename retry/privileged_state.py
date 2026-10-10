"""Research-only current privileged observations, not a pixel submission agent.

Road/obstacle geometry is static ground truth.  Hull-origin position and COM
linear velocity are distinct current measurements; no transition is predicted.
The adapter imports no environment, policy, teacher, or learned model.
"""
from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class ObservationSpec:
    version: str = "current-privileged-23-v1"
    lookahead_arc_m: tuple = (5., 10., 20., 30.)
    obstacle_count: int = 2
    obstacle_range_m: float = 40.
    speed_scale: float = 30.
    yaw_rate_scale: float = 3.
    position_scale: float = 30.
    radius_scale: float = 3.
    # Current core/vendor/car_racing.py: TRACK_WIDTH = 40 / SCALE, SCALE = 6.
    road_half_width_m: float = 40. / 6.


SPEC = ObservationSpec()
FEATURE_NAMES = (
    "com_speed", "com_velocity_body_right", "com_velocity_body_forward",
    "yaw_rate", "heading_error_sin", "heading_error_cos", "hull_lateral",
    *(f"road_arc_{int(d)}m_{axis}" for d in SPEC.lookahead_arc_m
      for axis in ("body_right", "body_forward")),
    *(f"obstacle_{i}_{axis}" for i in range(SPEC.obstacle_count)
      for axis in ("body_right", "body_forward", "radius", "present")),
)
FEATURE_DIM = len(FEATURE_NAMES)


def _local_road(points, position):
    """Nearest closed-centerline segment; local ties use static row order."""
    ends = np.roll(points, -1, axis=0)
    vectors = ends - points
    squared = np.einsum("ij,ij->i", vectors, vectors)
    valid = squared > 1e-12
    if not valid.any():
        raise ValueError("nondegenerate closed road required")
    fractions = np.clip(np.einsum("ij,ij->i", position - points, vectors)
                        / np.where(valid, squared, 1.), 0., 1.)
    projections = points + fractions[:, None] * vectors
    distances = np.sum((projections - position) ** 2, axis=1)
    distances[~valid] = np.inf
    index = int(np.argmin(distances))
    lengths = np.sqrt(squared)
    cumulative = np.r_[0., np.cumsum(lengths)]
    arc = cumulative[index] + fractions[index] * lengths[index]
    queries = (arc + np.asarray(SPEC.lookahead_arc_m)) % cumulative[-1]
    closed = np.vstack((points, points[0]))
    future_geometry = np.column_stack([
        np.interp(queries, cumulative, closed[:, axis]) for axis in range(2)])
    return projections[index], vectors[index] / lengths[index], future_geometry


def privileged_features(env):
    """Return float32(23,) from the current env.unwrapped, without mutation.

    Heading zero points along world +Y; body right=(cos(h),sin(h)), forward=
    (-sin(h),cos(h)). Heading error is hull minus projected-road heading.
    Obstacles are the nearest two centers within 40m, including behind the car;
    their circular radii and presence masks are explicit. Missing slots are 0.
    No seed/ID, absolute pose, map index, lap/progress, reward, damage, wheel,
    teacher action, future realized state, or best-action label is an input.
    """
    raw = env.unwrapped
    hull = raw.car.hull
    position = np.asarray(hull.position, dtype=np.float64)
    velocity = np.asarray(hull.linearVelocity, dtype=np.float64)
    heading, yaw_rate = float(hull.angle), float(hull.angularVelocity)
    track = np.asarray(raw.track, dtype=np.float64)
    if (position.shape != (2,) or velocity.shape != (2,) or track.ndim != 2
            or track.shape[1] != 4 or len(track) < 3):
        raise ValueError("current 2D pose/velocity and Nx4 track required")
    points = track[:, 2:4]
    if not (np.isfinite(points).all() and np.isfinite(position).all()
            and np.isfinite(velocity).all() and math.isfinite(heading)
            and math.isfinite(yaw_rate)):
        raise ValueError("finite current state and static geometry required")
    projection, tangent, geometry = _local_road(points, position)
    right = np.array([math.cos(heading), math.sin(heading)])
    forward = np.array([-math.sin(heading), math.cos(heading)])
    road_right = np.array([tangent[1], -tangent[0]])
    road_heading = math.atan2(-tangent[0], tangent[1])
    error = heading - road_heading
    features = [np.linalg.norm(velocity) / SPEC.speed_scale,
        velocity @ right / SPEC.speed_scale, velocity @ forward / SPEC.speed_scale,
        yaw_rate / SPEC.yaw_rate_scale, math.sin(error), math.cos(error),
        (position - projection) @ road_right / SPEC.road_half_width_m]
    local_geometry = (geometry - position) @ np.column_stack((right, forward))
    features.extend((local_geometry / SPEC.position_scale).ravel())
    obstacles = []
    for body in raw.obstacles:
        delta = np.asarray(body.position, dtype=np.float64) - position
        radius = float(body.fixtures[0].shape.radius)
        if delta.shape != (2,) or not np.isfinite(delta).all() or not math.isfinite(radius) or radius <= 0:
            raise ValueError("finite circular obstacle geometry required")
        distance = float(np.linalg.norm(delta))
        if distance <= SPEC.obstacle_range_m:
            obstacles.append((distance, float(delta @ right), float(delta @ forward), radius))
    obstacles.sort(key=lambda o: (o[0], o[2], o[1], o[3]))
    for _, x, y, radius in obstacles[:SPEC.obstacle_count]:
        features.extend((x / SPEC.position_scale, y / SPEC.position_scale,
                         radius / SPEC.radius_scale, 1.))
    features.extend([0.] * (4 * max(0, SPEC.obstacle_count - len(obstacles))))
    result = np.asarray(features, dtype=np.float32)
    if result.shape != (FEATURE_DIM,) or not np.isfinite(result).all():
        raise ValueError("finite fixed privileged observation required")
    return result
