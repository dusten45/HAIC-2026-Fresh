"""The stage166 preview with a single vehicle-scale curvature support."""
import numpy as np

# (front axle +80 - rear axle -82) * SIZE .02 from car_dynamics.py.
# Total arc support, not the distance on each side: one 3.24 m wheelbase.
CURVATURE_SPAN_M = 3.24


def visible_curvature_preview(path, speed, lateral_budget):
    """Keep the same preview vertices; interpolate at +/-1.62 m along the path.

    Use only the already selected current-image path. No extrapolation, new
    perception, smoothing threshold, path modification, or simulator import.
    """
    points = np.asarray(path, dtype=float).reshape(-1, 2)
    lookahead = float(np.clip(4 + 0.35 * speed, 6, 14))
    info = dict(start_arc_m=lookahead, end_arc_m=lookahead + 4.0,
                considered_triplets=0, peak_abs_curvature=0.0,
                peak_center_arc_m=None, peak_triplet_index=None,
                speed_limit_m_s=None, available_arc_m=0.0,
                curvature_span_m=CURVATURE_SPAN_M)
    if len(points) < 3:
        return info
    arc = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    info['available_arc_m'] = float(arc[-1])
    half = CURVATURE_SPAN_M / 2
    for i in range(1, len(points) - 1):
        if not lookahead <= arc[i] <= lookahead + 4.0:
            continue
        if arc[i] < half or arc[i] + half > arc[-1]:
            continue
        sample_arc = [arc[i] - half, arc[i], arc[i] + half]
        samples = np.column_stack([np.interp(sample_arc, arc, points[:,axis]) for axis in (0, 1)])
        u, v = samples[1] - samples[0], samples[2] - samples[1]
        denominator = float(np.linalg.norm(u) * np.linalg.norm(v) * np.linalg.norm(u+v))
        if denominator <= 1e-9:
            continue
        curvature = abs(float(2 * (u[0]*v[1] - u[1]*v[0]) / denominator))
        info['considered_triplets'] += 1
        if curvature > info['peak_abs_curvature']:
            info.update(peak_abs_curvature=curvature,
                        peak_center_arc_m=float(arc[i]), peak_triplet_index=i)
    if info['peak_abs_curvature'] > 0:
        info['speed_limit_m_s'] = float(np.sqrt(lateral_budget / info['peak_abs_curvature']))
    return info
