"""Analytic expectation of the existing Gaussian-to-car control transform.

This is the mean of the executed control vector, not the expected simulator
transition. Gas and brake can both be positive in that mean even though each
individual signed-pedal sample activates only one pedal.
"""
import math
import numpy as np


def capped_positive_normal_mean(mean, std):
    """Return E[min(max(X, 0), 1)] for X ~ Normal(mean, std**2)."""
    mean, std = float(mean), float(std)
    if not math.isfinite(mean) or not math.isfinite(std) or std < 0:
        raise ValueError("finite mean and nonnegative finite std required")
    if std == 0:
        return min(1., max(0., mean))
    a, b = -mean / std, (1. - mean) / std
    root_two = math.sqrt(2.)
    cdf = lambda z: .5 * math.erfc(-z / root_two)
    survival = lambda z: .5 * math.erfc(z / root_two)
    density = lambda z: math.exp(-.5 * z * z) / math.sqrt(2. * math.pi)
    mass = survival(a) - survival(b) if a >= 0 else cdf(b) - cdf(a)
    value = mean * mass + std * (density(a) - density(b)) + survival(b)
    # Roundoff can put a saturated expectation just outside its exact range.
    return min(1., max(0., value))


def expected_control_action(mean, std):
    """Return float32 steer/gas/brake E[T(X)] from the raw two Gaussian means.

Do not clip ``mean`` before this function or convert the returned pedals back
to one signed pedal; either operation would change the requested expectation.
"""
    mean, std = np.asarray(mean, np.float64), np.asarray(std, np.float64)
    if mean.shape != (2,) or std.shape != (2,):
        raise ValueError("two means and two standard deviations required")
    positive = [capped_positive_normal_mean(m, s) for m, s in zip(mean, std)]
    negative = [capped_positive_normal_mean(-m, s) for m, s in zip(mean, std)]
    return np.asarray([.4 * (positive[0] - negative[0]),
                       .5 * positive[1], .5 * negative[1]], np.float32)
