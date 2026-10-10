import copy
import unittest
from types import SimpleNamespace

import numpy as np
from retry.incremental_aggregation import batch_indices, continue_aggregated_model
from retry.incremental_imitation import parameter_digest


class IncrementalAggregationTests(unittest.TestCase):
    def test_matched_draws_and_equal_new_source_probability(self):
        common = dict(seed=11, updates=4, batch_size=128)
        control = list(batch_indices(17, 23, 9, aggregate=False, **common))
        treatment = list(batch_indices(17, 23, 9, aggregate=True, **common))
        for (a, b, c), (x, y, z) in zip(control, treatment):
            self.assertEqual((len(a), len(b), len(c)), (64, 64, 0))
            self.assertEqual((len(x), len(y), len(z)), (64, 32, 32))
            np.testing.assert_array_equal(a, x)
            np.testing.assert_array_equal(b[:32], y)
            self.assertTrue(np.all((z >= 0) & (z < 9)))
        with self.assertRaises(ValueError):
            list(batch_indices(17, 23, 0, aggregate=True, **common))

    def test_new_labels_affect_updates_while_checkpoint_normalizers_stay_fixed(self):
        model = SimpleNamespace(arrays=[(np.zeros((3, 2), np.float32), np.zeros(3, np.float32))],
            mean=np.array([2., 3.], np.float32), scale=np.array([.5, .7], np.float32),
            label_mean=np.zeros(3, np.float32), label_scale=np.ones(3, np.float32))
        control, treatment = copy.deepcopy(model), copy.deepcopy(model)
        initial = parameter_digest(model)
        x = np.ones((8, 2), np.float32)
        zero, one = np.zeros((8, 3), np.float32), np.ones((8, 3), np.float32)
        common = dict(old_weights=np.ones(8), seed=9, updates=2, learning_rate=.003,
            batch_size=4, correction_inputs=x, correction_labels=zero)
        a = continue_aggregated_model(control, x, zero, **common)
        b = continue_aggregated_model(treatment, x, zero, phase2_inputs=x, phase2_labels=one, **common)
        self.assertEqual(a['initial_parameter_digest'], initial)
        self.assertEqual(b['initial_parameter_digest'], initial)
        self.assertEqual(a['final_parameter_digest'], initial)
        self.assertNotEqual(b['final_parameter_digest'], initial)
        self.assertEqual((a['old_draws'], a['correction_draws'], a['phase2_draws']), (4, 4, 0))
        self.assertEqual((b['old_draws'], b['correction_draws'], b['phase2_draws']), (4, 2, 2))
        for item in [control, treatment]:
            for name in ['mean', 'scale', 'label_mean', 'label_scale']:
                np.testing.assert_array_equal(getattr(item, name), getattr(model, name))


if __name__ == '__main__':
    unittest.main()
