import tempfile
import unittest
from pathlib import Path
import numpy as np

from retry.imitation_model import ImitationAgent, SmallActionMLP


class ModelBoundaryTests(unittest.TestCase):
    def test_student_records_its_own_executed_action(self):
        class Features:
            def reset(self, observation): self.events = []
            def observe(self, observation):
                self.events.append('observe')
                return np.array([1., 2.])
            def record_action(self, action):
                self.events.append(action.copy())
        class Model:
            def predict(self, current): return np.array([[.1, .2, 0.]], np.float32)
        features = Features()
        student = ImitationAgent(features, Model())
        student.reset(None)
        action = student.act(None)
        self.assertEqual(features.events[0], 'observe')
        np.testing.assert_array_equal(features.events[1], action)

    def test_saved_inference_matches_without_training_or_teacher(self):
        model = SmallActionMLP()
        model.mean, model.scale = np.zeros(2), np.ones(2)
        model.label_mean, model.label_scale = np.zeros(3), np.ones(3)
        model.arrays = [(np.eye(2), np.zeros(2)), (np.eye(2), np.zeros(2)),
                        (np.array([[1., 0.], [0., 1.], [1., 1.]]), np.zeros(3))]
        x = np.array([[.2, .3], [-.8, .9]])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'private.npz'
            model.save(path)
            np.testing.assert_array_equal(model.predict(x), SmallActionMLP.load(path).predict(x))


if __name__ == '__main__':
    unittest.main()
