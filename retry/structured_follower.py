"""Expose the pixel champion's frozen low-level equations to learned goals.

The original SpeedController internally derives desired speed from curvature
and its speed schedule. This adapter receives that high-level desired speed,
while preserving its steering smoothing and gas/brake conversion. It is not a
different research follower and does not call the teacher planner at runtime.
"""
import numpy as np


def clip_targets(values):
    """Fixed local-target domain; no fitted or DEV-selected bounds."""
    return np.clip(values, [-35., .1, 0.], [35., 35., 28.]).astype(np.float32)


def actions_from_targets(targets, current_pixel_speed, previous_executed_steer):
    targets = np.asarray(targets, np.float64)
    speed = np.asarray(current_pixel_speed, np.float64)
    previous = np.asarray(previous_executed_steer, np.float64)
    if targets.ndim != 2 or targets.shape[1] != 3 or speed.shape != (len(targets),) or previous.shape != (len(targets),):
        raise ValueError('same-row target point/speed and legal speed/past steer required')
    if not np.isfinite(targets).all() or not np.isfinite(speed).all() or not np.isfinite(previous).all():
        raise ValueError('finite target and legal context required')
    x, forward, desired = targets.T
    curvature = 2*x/np.maximum(forward*forward+x*x, 1e-6)
    steer = .8*np.clip(np.arctan(3.24*curvature), -.4, .4) + .2*previous
    gas = np.clip(.08*(desired-speed), 0., .5)
    brake = np.clip(.04*(speed-desired), 0., .5)
    return np.column_stack([steer, gas, brake]).astype(np.float32)
