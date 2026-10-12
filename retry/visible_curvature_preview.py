"""One fixed speed-only preview from an already selected image-derived path."""
import numpy as np


def visible_curvature_preview(path, speed, lateral_budget):
    """Use three-point curvature in the next 4 m after the original lookahead.

    No environment, future state, new perception, or path/steering modification.
    The 4 m span is fixed before DEV observation; no fitted threshold or sweep.
    """
    points = np.asarray(path, dtype=float).reshape(-1, 2)
    lookahead = float(np.clip(4 + 0.35 * speed, 6, 14))
    info = dict(start_arc_m=lookahead, end_arc_m=lookahead + 4.0,
                considered_triplets=0, peak_abs_curvature=0.0,
                peak_center_arc_m=None, peak_triplet_index=None,
                speed_limit_m_s=None, available_arc_m=0.0)
    if len(points) < 3:
        return info
    arc = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    info['available_arc_m'] = float(arc[-1])
    for i in range(1, len(points) - 1):
        if not lookahead <= arc[i] <= lookahead + 4.0:
            continue
        u, v = points[i] - points[i-1], points[i+1] - points[i]
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
