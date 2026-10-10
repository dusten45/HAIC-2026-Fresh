import unittest
from types import SimpleNamespace

import numpy as np
from retry.incremental_imitation import batch_indices, continue_model, parameter_digest


class IncrementalImitationTests(unittest.TestCase):
    def test_matched_updates_use_exact_source_ratio(self):
        common = dict(seed=7, updates=5, batch_size=128)
        old = list(batch_indices(20, 3, mixed=False, **common))
        mix = list(batch_indices(20, 3, mixed=True, **common))
        for (a, b), (c, d) in zip(old, mix):
            self.assertEqual((len(a), len(b), len(c), len(d)), (128, 0, 64, 64))
            np.testing.assert_array_equal(a[:64], c)

    def test_extra_updates_start_from_existing_parameters_and_keep_normalization(self):
        rng = np.random.default_rng(4)
        arrays = [(rng.normal(size=(4, 2)).astype(np.float32), np.ones(4, np.float32)),
                  (rng.normal(size=(3, 4)).astype(np.float32), np.ones(3, np.float32))]
        model = SimpleNamespace(arrays=arrays, mean=np.array([2., 3.], np.float32),
            scale=np.array([.5, .7], np.float32), label_mean=np.ones(3, np.float32), label_scale=np.ones(3, np.float32))
        initial = parameter_digest(model)
        norms = {n: getattr(model, n).copy() for n in ['mean', 'scale', 'label_mean', 'label_scale']}
        receipt = continue_model(model, np.ones((8, 2), np.float32), np.zeros((8, 3), np.float32),
            old_weights=np.ones(8), seed=9, updates=2, learning_rate=.003, batch_size=4)
        self.assertEqual(receipt['initial_parameter_digest'], initial)
        self.assertNotEqual(receipt['final_parameter_digest'], initial)
        self.assertEqual((receipt['updates'], receipt['old_draws'], receipt['correction_draws']), (2, 8, 0))
        for n, v in norms.items(): np.testing.assert_array_equal(getattr(model, n), v)


if __name__ == '__main__': unittest.main()
