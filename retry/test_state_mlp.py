"""State regression output must retain physical units through serialization."""
import tempfile
from pathlib import Path
import unittest
import numpy as np
from retry.state_mlp import SmallStateMLP


class StateMLPContractTests(unittest.TestCase):
    def test_serialized_state_outputs_are_not_action_clipped(self):
        model = SmallStateMLP(hidden=1)
        model.mean = np.array([10., -4.])
        model.scale = np.array([2., .5])
        model.target_mean = np.array([1., 20., -.7])
        model.arrays = [(np.array([[1., 0.]], np.float32), np.zeros(1, np.float32)),
                        (np.ones((1, 1), np.float32), np.zeros(1, np.float32)),
                        (np.ones((3, 1), np.float32), np.zeros(3, np.float32))]
        inputs = np.array([[10., -4.], [12., -4.]])
        expected = np.array([[1., 20., -.7],
                             [1., 20., -.7]]) + np.array([[0.], [np.tanh(np.tanh(1.))]])
        np.testing.assert_allclose(model.predict(inputs), expected, atol=1e-7, rtol=0)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'model.npz'
            model.save(path)
            restored = SmallStateMLP.load(path)
            np.testing.assert_array_equal(restored.predict(inputs), model.predict(inputs))

    def test_wrong_feature_dimension_is_rejected(self):
        model = SmallStateMLP(hidden=1)
        model.mean, model.scale = np.zeros(2), np.ones(2)
        with self.assertRaises(ValueError):
            model.predict(np.zeros((1, 3)))


if __name__ == '__main__':
    unittest.main()
