"""Pure geometry screens for saved pre-contact path and vehicle diagnostics.

No simulator or policy calls. Held-curvature arcs are illustrative and cannot
certify dynamic feasibility. The rear-axle reference preserves the hull offset.
"""
import ast
from pathlib import Path

import numpy as np

G = Path(__file__).resolve().parents[1]
SKIN = 0.009999999776482582
SPACING = .05


def rotation(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, -s], [s, c]])


def read_shapes():
    tree = ast.parse((G / 'core/vendor/car_dynamics.py').read_text())
    names = {'SIZE', 'WHEEL_R', 'WHEEL_W', 'WHEELPOS', 'HULL_POLY1', 'HULL_POLY2', 'HULL_POLY3', 'HULL_POLY4'}
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in names:
            constants[node.targets[0].id] = ast.literal_eval(node.value)
    size = constants['SIZE']
    hull = [np.asarray(constants[f'HULL_POLY{i}'], float) * size for i in range(1, 5)]
    w, h = constants['WHEEL_W'] * size, constants['WHEEL_R'] * size
    wheel = np.array([[-w, h], [w, h], [w, -h], [-w, -h]])
    anchors = np.array(constants['WHEELPOS']) * size
    return hull, wheel, anchors


HULL, WHEEL, ANCHORS = read_shapes()
REAR = -ANCHORS[2, 1]
WHEELBASE = ANCHORS[0, 1] - ANCHORS[2, 1]
RADIUS = max(np.linalg.norm(p, axis=1).max() for p in HULL)
assert np.allclose([WHEELBASE, REAR], [3.24, 1.64], atol=1e-14, rtol=0)
# Wheel corners over their entire allowed turn stay within this hull-radius bound.
for delta in np.linspace(-.4, .4, 101):
    assert max(np.linalg.norm(WHEEL @ rotation(delta).T + a, axis=1).max() for a in ANCHORS) < RADIUS


def polygon_circle(poly, points, radius):
    """Signed nominal polygon-circle separation, including source polygon skin."""
    points = np.asarray(points).reshape(-1, 2)
    a, b = poly, np.roll(poly, -1, axis=0)
    edge = b - a
    rel = points[:, None, :] - a
    alpha = np.clip(np.sum(rel * edge, axis=-1) / np.sum(edge * edge, axis=-1), 0, 1)
    distance = np.linalg.norm(rel - alpha[:, :, None] * edge, axis=-1).min(axis=1)
    cross = edge[None, :, 0] * rel[:, :, 1] - edge[None, :, 1] * rel[:, :, 0]
    inside = np.all(cross >= -1e-12, axis=1) | np.all(cross <= 1e-12, axis=1)
    return np.where(inside, -distance, distance) - radius - SKIN


def local_points(center, positions, angles):
    rel = center - positions
    c, s = np.cos(angles), np.sin(angles)
    return np.c_[c * rel[:, 0] + s * rel[:, 1], -s * rel[:, 0] + c * rel[:, 1]]


def footprint_curve(positions, angles, front_delta, center, radius):
    """Kinematic rigid hull with steering front rectangles; static screen only."""
    values = [polygon_circle(p, local_points(center, positions, angles), radius) for p in HULL]
    for i, anchor in enumerate(ANCHORS):
        c, s = np.cos(angles), np.sin(angles)
        wp = positions + np.c_[c * anchor[0] - s * anchor[1], s * anchor[0] + c * anchor[1]]
        wa = angles - front_delta if i < 2 else angles
        values.append(polygon_circle(WHEEL, local_points(center, wp, wa), radius))
    values = np.asarray(values)
    fixture, sample = np.unravel_index(np.argmin(values), values.shape)
    return {'min_clearance_m': float(values[fixture, sample]), 'fixture': int(fixture),
            'sample': int(sample), 'position': positions[sample].tolist()}


def actual_footprint(pose, center, radius):
    point = (center - pose['position']) @ rotation(pose['angle'])
    values = [float(polygon_circle(p, [point], radius)[0]) for p in HULL]
    for wheel in pose['wheels']:
        point = (center - wheel['position']) @ rotation(wheel['angle'])
        values.append(float(polygon_circle(WHEEL, [point], radius)[0]))
    return {'min_clearance_m': min(values), 'fixture': int(np.argmin(values)), 'all_fixtures_m': values}


def prefix(path, length):
    result = [np.asarray(path[0], float)]
    remaining = length
    for a, b in zip(path[:-1], path[1:]):
        a, b = np.asarray(a), np.asarray(b)
        d = float(np.linalg.norm(b - a))
        if d <= 1e-12:
            continue
        if d >= remaining:
            result.append(a + (b - a) * remaining / d)
            return np.array(result)
        result.append(b)
        remaining -= d
    return np.array(result)


def route_curve(path, center, radius):
    a, b = path[:-1], path[1:]
    e = b - a
    lengths = np.linalg.norm(e, axis=1)
    keep = lengths > 1e-12
    a, b, e, lengths = a[keep], b[keep], e[keep], lengths[keep]
    alpha = np.clip(np.sum((center - a) * e, axis=1) / lengths**2, 0, 1)
    min_center = float(np.linalg.norm(center - (a + alpha[:, None] * e), axis=1).min())
    pos, angles = [], []
    for aa, ee, length in zip(a, e, lengths):
        t = np.linspace(0, 1, int(np.ceil(length / SPACING)) + 1)
        pos.extend(aa + t[:, None] * ee)
        angles.extend([-np.arctan2(ee[0], ee[1])] * len(t))
    nominal = footprint_curve(np.array(pos), np.array(angles), 0., center, radius)
    return {'min_center_distance_m': min_center,
            'all_heading_clearance_lower_bound_m': min_center - radius - RADIUS - SKIN,
            'tangent_footprint': nominal,
            'instantaneous_corner_count': int(np.sum(np.abs(np.diff(np.unwrap(-np.arctan2(e[:, 0], e[:, 1])))) > 1e-8)),
            'heading_limit': 'Polyline has no yaw state; tangent placement is illustrative, all-heading radius bound is sufficient when positive.'}


def arc(curvature, distance, center, radius, rear_reference):
    s = np.linspace(0, distance, max(2, int(np.ceil(distance / SPACING)) + 1))
    theta = curvature * s
    if abs(curvature) < 1e-10:
        pos = np.c_[np.zeros(len(s)), s]
    else:
        pos = np.c_[(1 - np.cos(theta)) / curvature, np.sin(theta) / curvature]
    if rear_reference:
        pos += np.c_[REAR * np.sin(theta), REAR * (np.cos(theta) - 1)]
    result = footprint_curve(pos, -theta, np.arctan(WHEELBASE * curvature), center, radius)
    result.update(curvature=float(curvature), distance_horizon_m=float(distance),
                  rear_axle_reference=rear_reference,
                  sampling_clearance_bound_m=float((s[1] - s[0]) * (1 + (RADIUS + REAR) * abs(curvature)) / 2))
    return result


def route_crossings(path, center):
    """Lateral offsets where a path crosses an obstacle's forward coordinate."""
    result = []
    for a, b in zip(path[:-1], path[1:]):
        if a[1] <= center[1] <= b[1] and b[1] > a[1]:
            result.append(float(a[0] + (b[0] - a[0]) *
                                (center[1] - a[1]) / (b[1] - a[1]) - center[0]))
    return result


def nonzero_sign_reversals(values):
    signs = np.sign(values)
    signs = signs[signs != 0]
    return int(np.sum(signs[1:] != signs[:-1]))
