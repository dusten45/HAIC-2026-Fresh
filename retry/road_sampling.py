"""Deterministic, count-matched sampling across distinct registered roads.

The caller supplies one complete episode per road in a frozen order. Sampling
uses row counts only, retains each endpoint, and samples without replacement.
Compute temporal features from the full episode before selecting these rows;
selected rows can have gaps and do not form a new contiguous history.
"""
import numpy as np


def matched_road_indices(lengths, total, *, seed):
    lengths = list(lengths)
    if not lengths or any(not isinstance(n, (int, np.integer)) or isinstance(n, (bool, np.bool_)) or n < 1 for n in lengths):
        raise ValueError('positive integer complete-episode lengths required')
    if not isinstance(total, (int, np.integer)) or isinstance(total, (bool, np.bool_)) or not len(lengths) <= total <= sum(lengths):
        raise ValueError('sample total must retain every road and fit available unique rows')
    counts = np.zeros(len(lengths), dtype=np.int64)
    remaining = int(total)
    while remaining:
        for i, n in enumerate(lengths):
            if counts[i] < n:
                counts[i] += 1
                remaining -= 1
                if remaining == 0:
                    break
    selected = []
    for i, (n, count) in enumerate(zip(lengths, counts)):
        rng = np.random.default_rng(np.random.SeedSequence([int(seed), i]))
        other = rng.choice(n-1, size=int(count)-1, replace=False)
        selected.append(np.sort(np.r_[other, n-1]).astype(np.int64))
    return selected
