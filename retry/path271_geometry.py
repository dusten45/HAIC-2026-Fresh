"""Privileged frozen whole-map free-path slice; no speed-profile input."""
import numpy as np

SPACING = 1 / 1.701  # Existing pixel path's vertical metre-per-pixel unit.
BOUNDS = np.array([(3-42)/1.3608, (80-42)/1.3608,
                   (63-56)/1.701, (63-24)/1.701])

def project(line, position, index):
    n = len(line)
    candidates = np.arange(max(0, index-2), index+18)
    nearest = int(candidates[np.argmin(np.linalg.norm(line[candidates % n]-position, axis=1))])
    index = max(index, nearest)
    i = index % n
    delta = line[(i+1) % n]-line[i]
    u = float(np.clip((position-line[i])@delta/max(delta@delta, 1e-9), 0, 1))
    point = line[i]+u*delta
    return index, u, point, float(np.linalg.norm(position-point))

def clip_segment(a, b):
    lower, upper = np.array([BOUNDS[0], BOUNDS[2]]), np.array([BOUNDS[1], BOUNDS[3]])
    lo, hi = 0., 1.
    d = b-a
    for k in range(2):
        if abs(d[k]) < 1e-12:
            if a[k] < lower[k] or a[k] > upper[k]: return None
        else:
            t0, t1 = sorted([(lower[k]-a[k])/d[k], (upper[k]-a[k])/d[k]])
            lo, hi = max(lo, t0), min(hi, t1)
            if lo > hi: return None
    return a+lo*d, a+hi*d, hi

def local_path(line, position, angle, index):
    """Origin prefix, then first contiguous forward ordered routing-window slice.

    Same (right, forward) metres as240; no row sorting, IDs or teacher pace.
    The global path was optimized with foresight; cropping cannot remove it.
    """
    index, u, projection, error = project(line, position, index)
    n = len(line)
    right = np.array([np.cos(angle), np.sin(angle)])
    forward = np.array([-np.sin(angle), np.cos(angle)])
    basis = np.stack([right, forward], axis=1)
    world = np.vstack([projection, line[(np.arange(index+1, index+33)) % n]])
    body = (world-position)@basis
    path = [(0., 0.)]
    entered = False
    for a, b in zip(body[:-1], body[1:]):
        clipped = clip_segment(a, b)
        if clipped is None:
            if entered: break
            continue
        a, b, hi = clipped
        if not entered:
            # Do not pick a reversed/look-behind entry at a tracking loss.
            if (b-a)@np.array([0., 1.]) <= 0: break
            path.append(tuple(map(float, a))); entered = True
        length = float(np.linalg.norm(b-a))
        pieces = max(1, int(np.ceil(length/SPACING)))
        for point in a+(b-a)*np.linspace(0, 1, pieces+1)[1:, None]:
            if np.linalg.norm(point-np.array(path[-1])) > 1e-9:
                path.append(tuple(map(float, point)))
        if hi < 1-1e-10: break
    return path if len(path)>2 else [], index, dict(path_error_m=error,
        projection_fraction=u, path_points=max(0, len(path) if len(path)>2 else 0),
        whole_map_GT_foresight=True, coordinate_order='right_forward_metres')

def pack(observation, mode=0, path=()):
    return np.concatenate([observation.ravel(), np.array([mode, len(path)], np.float64),
                           np.asarray(path, np.float64).ravel()]).astype(np.float64)
