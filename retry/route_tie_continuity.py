"""Bounded route-score tie preference; no path or steering oracle.

Transport only the previous route reference with motion already computed by the
tracker. The router still returns a freshly computed current candidate. Missing
continuity or a score disadvantage beyond the band restores original ranking.
"""
import numpy as np

TIE_BAND_M = 0.05


def transport_path(path, transform, fallback_displacement):
    if not path:
        return []
    points = np.asarray(path, dtype=float)
    if transform is None:
        if fallback_displacement is None:
            return []
        return (points - [0.0, fallback_displacement]).tolist()
    pixels = np.column_stack((41.542 + 1.3608 * points[:, 0],
                              62.4475 - 1.701 * points[:, 1],
                              np.ones(len(points))))
    moved = pixels @ np.asarray(transform).T
    return np.column_stack(((moved[:, 0] - 41.542) / 1.3608,
                            (62.4475 - moved[:, 1]) / 1.701)).tolist()


def crossing_side(path, obstacle):
    if obstacle is None:
        return None
    x, forward = obstacle
    for first, second in zip(path, path[1:]):
        if (first[1] - forward) * (second[1] - forward) <= 0 and first[1] != second[1]:
            t = (forward - first[1]) / (second[1] - first[1])
            offset = first[0] + t * (second[0] - first[0]) - x
            return 1 if offset > 0 else -1 if offset < 0 else None
    return None


def choose_tied_route(candidates, scores, previous_path):
    original = min(scores)[1]
    best = min(scores)[0]
    obstacle = candidates[0].get('continuity_obstacle_xy')
    previous_side = crossing_side(previous_path, obstacle)
    sides = [crossing_side(c['path'], obstacle) for c in candidates]
    eligible = [(score, index) for score, index in scores
                if previous_side is not None and sides[index] == previous_side
                and score - best <= TIE_BAND_M]
    selected = min(eligible)[1] if eligible else original
    score_by_index = {index: score for score, index in scores}
    return selected, dict(tie_band_m=TIE_BAND_M, original_index=original,
                         previous_path_side=previous_side,
                         candidate_bypass_sides=sides, best_score_m=best,
                         selected_score_excess_m=score_by_index[selected] - best,
                         tie_held=selected != original)
