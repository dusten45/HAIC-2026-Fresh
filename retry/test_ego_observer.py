"""History boundaries and shared-current features, without any learner fit."""
import unittest
import numpy as np
from retry.ego_observer import CURRENT_NAMES, FEATURE_NAMES, extract_features


class HistoryBoundaryTest(unittest.TestCase):
    def test_reset_history_is_unavailable(self):
        obs = np.zeros((4, 84, 84), np.float32)
        result = extract_features(obs, [])
        self.assertEqual(result.shape, (172,))
        np.testing.assert_array_equal(result[len(CURRENT_NAMES):], 0.)

    def test_current_features_do_not_depend_on_past_bundle(self):
        rng = np.random.default_rng(50001)
        obs = rng.random((4, 84, 84), dtype=np.float32)
        changed = obs.copy(); changed[:3] = 0
        full = extract_features(obs, [[.1, .2, .0]]*3)
        control = extract_features(changed, [])
        np.testing.assert_array_equal(full[:52], control[:52])

    def test_short_action_history_is_left_padded(self):
        result = extract_features(np.zeros((4,84,84),np.float32), [[.2,.25,0]])
        offset = FEATURE_NAMES.index('past_action_0_steer')
        np.testing.assert_array_equal(result[offset:offset+9], [0,0,0,0,0,0,.5,.5,0])
        np.testing.assert_array_equal(result[-3:], [0,0,1])
        with self.assertRaises(ValueError):
            extract_features(np.zeros((4,84,84),np.float32), [[0,0,0]]*4)


if __name__ == '__main__':
    unittest.main()
