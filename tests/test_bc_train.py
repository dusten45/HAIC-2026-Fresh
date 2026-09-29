import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from bc.model import BCPolicy
from bc.train import main, road_paths


class TestBCTraining(unittest.TestCase):
    def make_dataset(self, directory):
        dataset = directory / "dataset"
        dataset.mkdir()
        names = ["track1_seed11.npz", "track2_seed12.npz", "track1_seed31.npz"]
        for index, name in enumerate(names):
            observations = np.full((4, 4, 84, 84), index / 4, dtype=np.float32)
            actions = np.tile(np.array([0.1 * index, 0.7, 0.0], dtype=np.float32), (4, 1))
            np.savez(dataset / name, observations=observations, actions=actions)
        # A manifest test entry must never be opened for model selection.
        manifest = {"train": names[:2], "val": names[2:], "test": ["missing_final.npz"]}
        (dataset / "split_manifest.json").write_text(json.dumps(manifest))
        return dataset, manifest

    def test_training_reproducible_and_cpu_inference(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            dataset, manifest = self.make_dataset(directory)
            outputs = []
            for name in ("first", "second"):
                output = directory / name
                result = main(["--dataset", str(dataset), "--output", str(output), "--device", "cpu",
                               "--epochs", "2", "--batch-size", "3", "--seed", "42",
                               "--max-train-samples", "6", "--num-threads", "1"])
                self.assertEqual(result["train_roads"], manifest["train"])
                self.assertEqual(result["val_roads"], manifest["val"])
                self.assertEqual(len(result["history"]), 2)
                self.assertEqual(result["history"][0]["train_samples"], 6)
                self.assertEqual(result["history"][0]["val"]["samples"], 4)
                self.assertEqual(result["best_train_prediction"]["samples"], 8)
                self.assertEqual(set(result["history"][0]["val"]["mse"]),
                                 {"steer", "gas", "brake"})
                self.assertEqual(result, json.loads((output / "history.json").read_text()))
                policy = BCPolicy.from_checkpoint(output / "best.pt")
                action = policy.act(np.zeros((4, 84, 84), dtype=np.float32))
                self.assertEqual(action.shape, (3,))
                self.assertEqual(action.dtype, np.float32)
                self.assertTrue(np.isfinite(action).all())
                self.assertTrue(np.all(action >= [-1, 0, 0]))
                self.assertTrue(np.all(action <= [1, 1, 1]))
                outputs.append(result)
                with self.assertRaises(FileExistsError):
                    main(["--dataset", str(dataset), "--output", str(output), "--device", "cpu",
                          "--epochs", "1", "--num-threads", "1"])
            self.assertEqual(outputs[0], outputs[1])

    def test_train_val_same_geometry_seed_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "share geometry seeds"):
                road_paths(Path(temporary), {"train": ["track1_seed11.npz"],
                                             "val": ["track2_seed11.npz"]})

    def test_final_test_seed_cannot_be_training_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "outside its declared geometry split"):
                road_paths(Path(temporary), {"train": ["track1_seed36.npz"],
                                             "val": ["track1_seed31.npz"]})

    def test_separate_collector_split_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            dataset, manifest = self.make_dataset(directory)
            val_dataset = directory / "validation"
            val_dataset.mkdir()
            (dataset / manifest["val"][0]).rename(val_dataset / manifest["val"][0])
            (dataset / "split_manifest.json").write_text(json.dumps({
                "train": manifest["train"], "val": [], "test": []}))
            (val_dataset / "split_manifest.json").write_text(json.dumps({
                "train": [], "val": manifest["val"], "test": []}))
            result = main(["--dataset", str(dataset), "--val-dataset", str(val_dataset),
                           "--output", str(directory / "model"), "--device", "cpu", "--epochs", "1",
                           "--batch-size", "4", "--max-train-samples", "4"])
            self.assertEqual(result["history"][0]["val"]["samples"], 4)

    def test_incorrect_observation_shape_rejected(self):
        with self.assertRaisesRegex(ValueError, "Expected finite observation"):
            BCPolicy().act(np.zeros((3, 84, 84), dtype=np.float32))

    def test_recovery_states_are_explicit_budget_not_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            dataset, _ = self.make_dataset(directory)
            recovery = directory / "recovery"
            recovery.mkdir()
            np.savez(recovery / "track1_seed11_recovery.npz",
                     observations=np.zeros((3, 4, 84, 84), dtype=np.float32),
                     actions=np.tile(np.array([0, 0, .5], dtype=np.float32), (3, 1)))
            result = main(["--dataset", str(dataset), "--recovery-dataset", str(recovery),
                           "--output", str(directory / "model"), "--device", "cpu",
                           "--epochs", "1", "--batch-size", "4", "--max-train-samples", "12"])
            self.assertEqual(result["history"][0]["recovery_samples"], 3)
            self.assertEqual(result["history"][0]["val"]["samples"], 4)
            self.assertEqual(result["recovery_roads"], ["track1_seed11_recovery.npz"])


if __name__ == "__main__":
    unittest.main()
