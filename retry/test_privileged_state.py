"""Meaningful geometry/boundary checks on fake data; no simulator instances."""
from dataclasses import FrozenInstanceError
import math
from types import SimpleNamespace as NS
import unittest

import numpy as np

from retry.privileged_state import FEATURE_DIM, FEATURE_NAMES, SPEC, privileged_features


def obstacle(x, y, radius=1.):
    return NS(position=(x, y), fixtures=[NS(shape=NS(radius=radius))])


class CurrentOnly:
    """Fail on any undeclared input or on environment execution."""
    def __init__(self, **values):
        self.__dict__.update(values)

    def __getattr__(self, name):
        raise AssertionError(f"undeclared runtime input: {name}")

    def reset(self, *args, **kwargs):
        raise AssertionError("environment reset forbidden")

    def step(self, *args, **kwargs):
        raise AssertionError("environment step forbidden")


def scene(position=(2., 20.), heading=0., velocity=(3., 4.), obstacles=()):
    points = np.array([[0., 0.], [0., 100.], [100., 100.], [100., 0.]])
    track = np.c_[np.zeros((4, 2)), points]
    hull = CurrentOnly(position=position, linearVelocity=velocity, angle=heading, angularVelocity=.6)
    raw = CurrentOnly(car=CurrentOnly(hull=hull), track=track, obstacles=list(obstacles))
    return CurrentOnly(unwrapped=raw)


class PrivilegedStateTests(unittest.TestCase):
    def test_straight_coordinate_signs_scales_and_local_geometry(self):
        env = scene(obstacles=[obstacle(-1., 25.), obstacle(4., 40., 1.5)])
        x = privileged_features(env)
        self.assertEqual(x.shape, (23,)); self.assertEqual(x.dtype, np.float32)
        self.assertEqual(FEATURE_DIM, len(FEATURE_NAMES))
        np.testing.assert_allclose(x[:7], [5/30, 3/30, 4/30, .2, 0., 1., .3], atol=1e-7)
        np.testing.assert_allclose(x[7:15].reshape(4, 2),
            [[-2/30, d/30] for d in SPEC.lookahead_arc_m], atol=1e-7)
        np.testing.assert_allclose(x[15:], [-3/30, 5/30, 1/3, 1., 2/30, 20/30, .5, 1.], atol=1e-7)

    def test_rigid_transform_invariance_no_absolute_pose_or_map_phase(self):
        env = scene(obstacles=[obstacle(-1., 25.)]); expected = privileged_features(env)
        angle = .7; rotation = np.array([[math.cos(angle), -math.sin(angle)],
                                       [math.sin(angle), math.cos(angle)]])
        shift = np.array([120., -300.]); raw = env.unwrapped; hull = raw.car.hull
        hull.position = rotation @ hull.position + shift
        hull.linearVelocity = rotation @ hull.linearVelocity
        hull.angle += angle
        raw.track[:, 2:] = raw.track[:, 2:] @ rotation.T + shift
        raw.track[:, :2] = 987654.  # Track alpha/beta values do not enter features.
        for body in raw.obstacles: body.position = rotation @ body.position + shift
        np.testing.assert_allclose(privileged_features(env), expected, atol=2e-7)

    def test_periodic_arc_crosses_seam_without_progress_or_cursor(self):
        env = scene(position=(20., 0.), heading=math.pi/2, velocity=(-4., 0.))
        x = privileged_features(env)
        np.testing.assert_allclose(x[7:15].reshape(4, 2),
            [[0., 5/30], [0., 10/30], [0., 20/30], [10/30, 20/30]], atol=1e-7)
        env.unwrapped.track = np.roll(env.unwrapped.track, 2, axis=0)
        np.testing.assert_allclose(privileged_features(env), x, atol=1e-7)

    def test_hazard_range_padding_order_and_read_only_contract(self):
        near = obstacle(-1., 25.); far = obstacle(2., 61.)
        env = scene(obstacles=[far, near]); before = env.unwrapped.track.copy()
        x = privileged_features(env)
        np.testing.assert_array_equal(x[19:], np.zeros(4))
        env.unwrapped.obstacles.reverse()
        np.testing.assert_array_equal(privileged_features(env), x)
        np.testing.assert_array_equal(env.unwrapped.track, before)
        self.assertEqual(env.unwrapped.car.hull.position, (2., 20.))
        with self.assertRaises(FrozenInstanceError): SPEC.obstacle_range_m = 99.

    def test_heading_and_lateral_signs_and_invalid_geometry(self):
        x = privileged_features(scene(position=(-2., 20.), heading=.3))
        np.testing.assert_allclose(x[4:7], [math.sin(.3), math.cos(.3), -.3], atol=1e-7)
        env = scene(); env.unwrapped.track[:, 2:] = 0.
        with self.assertRaises(ValueError): privileged_features(env)


if __name__ == "__main__":
    unittest.main()
