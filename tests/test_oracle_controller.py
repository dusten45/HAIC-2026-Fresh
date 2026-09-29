import unittest
from types import SimpleNamespace

import numpy as np

from oracle_controller import OracleController, TrackPath


class TestTrackPath(unittest.TestCase):
    def test_projection_and_wrap(self):
        path = TrackPath([[0, 0], [10, 0], [10, 10], [0, 10]])
        arc, lateral, index = path.project([5, 2])
        self.assertEqual((arc, lateral, index), (5.0, 2.0, 0))
        np.testing.assert_allclose(path.sample(42), [2, 0])
        np.testing.assert_allclose(path.sample(-2), [0, 2])
        self.assertEqual(path.length, 40)

    def test_zero_segment_rejected(self):
        with self.assertRaises(ValueError):
            TrackPath([[0, 0], [0, 0]])


class TestOracleController(unittest.TestCase):
    def test_steering_sign_and_speed_feedback(self):
        # Facing +y, with the path to the right: positive action must turn right.
        hull = SimpleNamespace(position=(0, 10), linearVelocity=(0, 0), angle=0)
        env = SimpleNamespace(
            car=SimpleNamespace(hull=hull),
            track=[(0, 0, 2, 0), (0, 0, 2, 100),
                   (0, 0, -100, 100), (0, 0, -100, 0)],
        )
        controller = OracleController(env)
        action, diagnostic = controller.act()
        self.assertGreater(action[0], 0)
        self.assertGreater(action[1], 0)
        self.assertEqual(action[2], 0)
        self.assertEqual(diagnostic["center_error"], 2)
        hull.linearVelocity = (0, 15)
        action, _ = controller.act()
        self.assertEqual(action[1], 0)
        self.assertGreater(action[2], 0)


if __name__ == "__main__":
    unittest.main()
