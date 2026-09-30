import hashlib
from argparse import Namespace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import torch

from bc.model import BCPolicy
from bc.contracts import BASELINE_CONDITIONS
from bc.dataset import _provenance
from bc.train import (action_weights, assemble_history, evaluate, main, road_paths,
                      selection_score, training_batches)


class TestBCTraining(unittest.TestCase):
    def write_provenance(self, directory, split="train", seed=11):
        conditions = BASELINE_CONDITIONS
        provenance = _provenance(Namespace(
            output=directory, resume=False, split=split, track_ids=[1, 2], seeds=[seed],
            max_steps=conditions["max_steps"], frame_skip=conditions["frame_skip"],
            warmup=conditions["warmup"], target_speed=conditions["target_speed"]))
        provenance["fixture"] = "Synthetic pixels/actions under the baseline collector condition contract"
        (directory / "provenance.json").write_text(json.dumps(provenance, default=str))

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
        self.write_provenance(dataset)
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
                self.assertEqual(result["history"][0]["sampled_conditional_counts"]["high_gas"], 6)
                self.assertFalse(result["config"]["balanced_actions"])
                self.assertEqual([row["optimizer_steps"] for row in result["history"]], [2, 2])
                self.assertNotIn("extra_train_manifest_sha256", result)
                self.assertFalse(result["config"]["continuous_batches"])
                self.assertEqual(result["config"]["active_gas_weight"], 1)
                self.assertEqual(result["config"]["history_spacing_simulator_ticks"], 4)
                self.assertEqual(result["config"]["history_spacing_seconds"], .08)
                self.assertIn("bc/contracts.py", result["source_sha256"])
                self.assertTrue((output / result["source_snapshot"]).is_dir())
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

    def test_history8_cli_rejects_motion_and_recovery_before_reading(self):
        for incompatible in (["--motion-features"], ["--recovery-dataset", "unused"]):
            with self.subTest(incompatible=incompatible), \
                    self.assertRaisesRegex(ValueError, "history8 cannot be combined"):
                main(["--dataset", "unused", "--output", "unused", "--history-frames", "8",
                      *incompatible])

    def test_history_cli_default_and_eight_option(self):
        for option, expected in (([], 4), (["--history-frames", "8"], 8)):
            with patch("bc.train.train") as trainer:
                main(["--dataset", "unused", "--output", "unused", *option])
            self.assertEqual(trainer.call_args.args[0].history_frames, expected)

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
            self.write_provenance(val_dataset, "val", 31)
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

    def test_extra_train_manifest_needs_no_validation_and_records_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            dataset, manifest = self.make_dataset(directory)
            extra = directory / "extra"
            extra.mkdir()
            self.write_provenance(extra, seed=21)
            name = "track3_seed21.npz"
            (extra / name).write_bytes((dataset / manifest["train"][0]).read_bytes())
            manifest_path = extra / "split_manifest.json"
            manifest_path.write_text(json.dumps({"train": [name], "test": ["missing_final.npz"]}))
            result = main(["--dataset", str(dataset), "--extra-train-dataset", str(extra),
                           "--output", str(directory / "model"), "--device", "cpu",
                           "--epochs", "1", "--batch-size", "2", "--max-train-samples", "9",
                           "--num-threads", "1"])
            self.assertEqual(result["train_roads"], manifest["train"] + [name])
            self.assertEqual(result["val_roads"], manifest["val"])
            self.assertEqual(result["extra_train_manifest_sha256"],
                             hashlib.sha256(manifest_path.read_bytes()).hexdigest())
            self.assertEqual(result["history"][0]["train_samples"], 9)
            # Three independent 3-sample roads each produce two batches, not ceil(9 / 2).
            self.assertEqual(result["history"][0]["optimizer_steps"], 6)
            self.assertEqual(result["best_train_prediction"]["samples"], 12)
            self.assertEqual(result, json.loads((directory / "model" / "history.json").read_text()))

    def test_extra_training_roads_are_validated(self):
        manifest = {"train": ["track1_seed11.npz"], "val": ["track1_seed31.npz"]}
        cases = [
            (["track1_seed11.npz"], "Duplicate training road names"),
            (["track1_seed21.npz", "track1_seed21.npz"], "unique road files"),
            ([], "nonempty list"),
            (["../track1_seed21.npz"], "Invalid train road filename"),
            (["track0_seed21.npz"], "Invalid train road filename"),
            (["track6_seed21.npz"], "Invalid train road filename"),
            (["track2_seed31.npz"], "share geometry seeds"),
            (["track1_seed36.npz"], "outside its declared geometry split"),
        ]
        for names, error in cases:
            with self.subTest(names=names), self.assertRaisesRegex(ValueError, error):
                road_paths(Path("base"), manifest, extra_train_dataset=Path("extra"),
                           extra_train_manifest={"train": names})

    def test_conditional_metrics_use_target_component_and_strict_threshold(self):
        model = torch.nn.Linear(1, 3)
        with torch.no_grad():
            model.weight.zero_()
            model.bias.copy_(torch.tensor([.05, .2, .3]))
        actions = np.array([[-.4, .1, .5], [.2, .4, .1], [-.1, .8, 0],
                            [.1, 0, .3], [0, .2, .9]], dtype=np.float32)
        predictions = np.tile(model.bias.detach().numpy(), (len(actions), 1))
        observations = np.zeros((len(actions), 1), dtype=np.float32)
        with patch("bc.train.read_road", return_value=(observations, actions)):
            result = evaluate(model, [Path("first"), Path("second")], batch_size=2)
        self.assertEqual(result["samples"], 10)
        for component, name in enumerate(("large_steer", "high_gas", "high_brake")):
            mask = np.abs(actions[:, component]) > .1
            target = actions[mask, component]
            prediction = predictions[mask, component]
            conditional = result["conditional"][name]
            self.assertEqual(conditional["count"], 2 * len(target))
            self.assertAlmostEqual(conditional["mae"], np.abs(prediction - target).mean())
            self.assertAlmostEqual(conditional["mse"], np.square(prediction - target).mean())
            self.assertAlmostEqual(conditional["target_mean"], target.mean())
            self.assertAlmostEqual(conditional["prediction_mean"], prediction.mean())
            self.assertAlmostEqual(result["mse"][("steer", "gas", "brake")[component]],
                                   np.square(predictions - actions).mean(axis=0)[component])

    def test_empty_conditional_metrics_are_json_null(self):
        model = torch.nn.Linear(1, 3)
        with patch("bc.train.read_road", return_value=(np.zeros((2, 1), dtype=np.float32),
                                                       np.zeros((2, 3), dtype=np.float32))):
            result = evaluate(model, [Path("road")], batch_size=1)
        expected = {"count": 0, "mae": None, "mse": None,
                    "target_mean": None, "prediction_mean": None}
        for metrics in result["conditional"].values():
            self.assertEqual(metrics, expected)
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)

    def test_signed_errors_use_gas_minus_brake_and_original_tail_masks(self):
        model = torch.nn.Linear(1, 3)
        with torch.no_grad():
            model.weight.zero_()
            model.bias.copy_(torch.tensor([0., .2, .1]))
        actions = np.array([[0, .4, 0], [0, 0, .3], [0, .1, 0]], dtype=np.float32)
        signed_target = actions[:, 1] - actions[:, 2]
        with patch("bc.train.read_road", return_value=(np.zeros((3, 1), dtype=np.float32), actions)):
            result = evaluate(model, [Path("road")], 2, include_startup=True)
        for name, mask in (("all", np.ones(3, dtype=bool)),
                           ("high_gas", actions[:, 1] > .1), ("high_brake", actions[:, 2] > .1)):
            metrics = result["longitudinal"][name]
            self.assertEqual(metrics["count"], int(mask.sum()))
            self.assertAlmostEqual(metrics["mae"], np.abs(.1 - signed_target[mask]).mean())
        self.assertAlmostEqual(result["startup"]["by_step"][0]["longitudinal"]["mae"], .3)
        self.assertAlmostEqual(result["startup"]["by_step"][1]["longitudinal"]["mae"], .4)

    def test_signed_training_roundtrip_and_unchanged_selection(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            dataset, _ = self.make_dataset(directory)
            result = main(["--dataset", str(dataset), "--output", str(directory / "signed"),
                           "--device", "cpu", "--epochs", "1", "--max-train-samples", "8",
                           "--num-threads", "1", "--history-frames", "8", "--signed-longitudinal",
                           "--balanced-actions", "--continuous-batches"])
            self.assertEqual(result["selection_metric"], "weighted_mean_mse")
            self.assertEqual(result["config"]["training_objective"], "(steer_mse+signed_longitudinal_mse)/3")
            self.assertEqual(result["history"][0]["train_samples"], 8)
            self.assertEqual(result["best_val_selection_score"], result["history"][0]["val"]["mean_mse"])
            policy = BCPolicy.from_checkpoint(directory / "signed" / "best.pt")
            self.assertTrue(policy.signed_longitudinal)
            action = policy.act(np.zeros((4, 84, 84), dtype=np.float32))
            self.assertEqual(action[1] * action[2], 0)

    def test_startup_metrics_reset_each_road_and_stop_at_ten(self):
        model = torch.nn.Linear(1, 3)
        with torch.no_grad():
            model.weight.zero_()
            model.bias.fill_(.2)
        actions = np.zeros((12, 3), dtype=np.float32)
        actions[0, 1] = .4
        actions[10:, 1] = 1
        with patch("bc.train.read_road", return_value=(np.zeros((12, 1), dtype=np.float32), actions)):
            result = evaluate(model, [Path("one"), Path("two")], 3, include_startup=True)
        startup = result["startup"]
        self.assertEqual(startup["first_10"]["gas"]["count"], 20)
        self.assertAlmostEqual(startup["first_10"]["gas"]["target_mean"], .04)
        self.assertAlmostEqual(startup["first_10"]["gas"]["mae"], .2)
        self.assertEqual(len(startup["by_step"]), 10)
        self.assertEqual(startup["by_step"][0]["gas"]["count"], 2)
        self.assertAlmostEqual(startup["by_step"][0]["gas"]["target_mean"], .4)
        self.assertAlmostEqual(startup["by_step"][9]["gas"]["target_mean"], 0)

    def test_continuous_batches_preserve_sample_order_and_flush_once(self):
        roads = {
            "first": (np.arange(5).reshape(-1, 1), np.arange(5).reshape(-1, 1)),
            "second": (np.arange(5, 7).reshape(-1, 1), np.arange(5, 7).reshape(-1, 1)),
            "third": (np.arange(7, 10).reshape(-1, 1), np.arange(7, 10).reshape(-1, 1)),
        }
        plan = [("first", 3, False), ("skipped", 0, False),
                ("second", 8, False), ("third", 2, False)]
        results = []
        for continuous in (False, True):
            rng = np.random.default_rng(42)
            with patch("bc.train.read_road", side_effect=roads.__getitem__) as reader:
                batches = list(training_batches(plan, rng, 4, continuous))
            self.assertEqual(reader.call_count, 3)
            self.assertEqual([len(y) for _, y, _ in batches], [4, 3] if continuous else [3, 2, 2])
            samples = np.concatenate([x for x, _, _ in batches])
            targets = np.concatenate([y for _, y, _ in batches])
            np.testing.assert_array_equal(samples, targets)
            self.assertTrue(all(not recovery for _, _, recovery in batches))
            results.append((samples, rng.integers(100000)))
        np.testing.assert_array_equal(results[0][0], results[1][0])
        self.assertEqual(results[0][1], results[1][1])

    def test_geometry_layouts_have_matched_continuous_optimizer_steps(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for roads, rows, historical_steps in ((50, 400, 350), (100, 200, 400)):
                dataset = directory / f"dataset_{roads}"
                dataset.mkdir()
                self.write_provenance(dataset)
                names = [f"track{track}_seed{seed}.npz" for track in range(1, 6)
                         for seed in range(11, 11 + roads // 5)]
                (dataset / "split_manifest.json").write_text(json.dumps({
                    "train": names, "val": ["track1_seed31.npz"]}))
                arrays = (np.zeros((rows, 1), dtype=np.float32),
                          np.zeros((rows, 3), dtype=np.float32))
                for continuous in (False, True):
                    with self.subTest(roads=roads, continuous=continuous):
                        model = torch.nn.Linear(1, 3)
                        with patch("bc.train.read_road", return_value=arrays), \
                                patch("bc.train.BCPolicy", return_value=model) as policy, \
                                patch("builtins.print"):
                            policy.from_checkpoint.return_value = model
                            result = main([
                                "--dataset", str(dataset), "--output", str(directory / f"model_{roads}_{continuous}"),
                                "--epochs", "2", "--batch-size", "64", "--max-train-samples", "20000",
                                "--device", "cpu", "--num-threads", "1",
                                *(["--continuous-batches"] if continuous else [])])
                        self.assertEqual(result["config"]["continuous_batches"], continuous)
                        for epoch in result["history"]:
                            self.assertEqual(epoch["train_samples"], 20000)
                            self.assertEqual(epoch["optimizer_steps"], 313 if continuous else historical_steps)

    def test_continuous_batches_reject_recovery_before_reading_data(self):
        with self.assertRaisesRegex(ValueError, "continuous-batches cannot be combined with recovery"):
            main(["--dataset", "unused", "--output", "unused", "--recovery-dataset", "unused",
                   "--continuous-batches"])

    def test_balanced_sampling_replays_tails_without_corrupting_history(self):
        observations = np.broadcast_to(
            np.arange(16, dtype=np.float32)[:, None, None, None] / 16, (16, 4, 84, 84)).copy()
        actions = np.zeros((16, 3), dtype=np.float32)
        actions[:, 0] = np.arange(16) / 16
        actions[0, 1] = .4
        actions[4, 2] = .3
        results = []
        for _ in range(2):
            rng = np.random.default_rng(0)
            with patch("bc.train.read_road", return_value=(observations, actions)):
                batches = list(training_batches([(Path("road"), 16, False)], rng, 5,
                                                continuous=True, history_frames=8, balanced_actions=True))
            self.assertEqual([len(y) for _, y, _ in batches], [5, 5, 5, 1])
            x = np.concatenate([x for x, _, _ in batches])
            y = np.concatenate([y for _, y, _ in batches])
            self.assertGreaterEqual(np.count_nonzero(y[:, 1] > .1), 2)
            self.assertGreaterEqual(np.count_nonzero(y[:, 2] > .1), 2)
            indices = (y[:, 0] * 16).astype(int)
            np.testing.assert_array_equal(x, assemble_history(observations, indices, 8))
            results.append((indices, rng.integers(100000)))
        np.testing.assert_array_equal(results[0][0], results[1][0])
        self.assertEqual(results[0][1], results[1][1])

    def test_balanced_missing_bins_reallocate_budget_and_keep_313_updates(self):
        arrays = (np.zeros((200, 1), dtype=np.float32), np.full((200, 3), .1, dtype=np.float32))
        plan = [(Path(f"road{index}"), 200, False) for index in range(100)]
        with patch("bc.train.read_road", return_value=arrays):
            batches = list(training_batches(plan, np.random.default_rng(0), 64,
                                            continuous=True, balanced_actions=True))
        self.assertEqual(len(batches), 313)
        self.assertEqual(sum(len(y) for _, y, _ in batches), 20000)
        self.assertTrue(all(np.all(y == .1) for _, y, _ in batches))

    def test_balanced_opt_out_preserves_natural_rng_and_recovery_is_rejected(self):
        observations = np.arange(16).reshape(-1, 1)
        actions = np.zeros((16, 3))
        expected_rng = np.random.default_rng(42)
        expected = expected_rng.permutation(16)[:12]
        rng = np.random.default_rng(42)
        with patch("bc.train.read_road", return_value=(observations, actions)):
            batches = list(training_batches([(Path("road"), 12, False)], rng, 5, balanced_actions=False))
        np.testing.assert_array_equal(np.concatenate([x for x, _, _ in batches])[:, 0], expected)
        self.assertEqual(rng.integers(100000), expected_rng.integers(100000))
        with self.assertRaisesRegex(ValueError, "balanced-actions cannot be combined"):
            main(["--dataset", "unused", "--output", "unused", "--balanced-actions",
                  "--recovery-dataset", "unused"])

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

    def test_collector_baseline_conditions_required_before_training(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            dataset, _ = self.make_dataset(directory)
            path = dataset / "provenance.json"
            original = json.loads(path.read_text())
            changes = {"frame_skip": 2, "warmup": 0,
                       "stack_frames": 8, "domain_randomize": True, "max_steps": 1000,
                       "raw_frame_budget": 4200, "render_mode": "human"}
            for field, value in changes.items():
                with self.subTest(field=field):
                    path.write_text(json.dumps({**original, "conditions": {
                        **original["conditions"], field: value}}))
                    with patch("bc.train.BCPolicy") as policy, patch("bc.train.read_road") as reader, \
                            self.assertRaisesRegex(ValueError, "collector conditions deviate from BC baseline"):
                        main(["--dataset", str(dataset), "--output", str(directory / "unused")])
                    policy.assert_not_called()
                    reader.assert_not_called()
                    self.assertFalse((directory / "unused").exists())
            path.unlink()
            with self.assertRaisesRegex(ValueError, "Cannot verify train collector provenance"):
                main(["--dataset", str(dataset), "--output", str(directory / "unused")])

    def test_separate_validation_and_extra_training_conditions_verified(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            dataset, manifest = self.make_dataset(directory)
            for flag, label, split, seed in (("--val-dataset", "val", "val", 31),
                                             ("--extra-train-dataset", "extra_train", "train", 21)):
                with self.subTest(flag=flag):
                    other = directory / label
                    other.mkdir()
                    self.write_provenance(other, split, seed)
                    (other / "split_manifest.json").write_text(json.dumps({split: [f"track1_seed{seed}.npz"]}))
                    path = other / "provenance.json"
                    original = json.loads(path.read_text())
                    original["conditions"]["frame_skip"] = 1
                    path.write_text(json.dumps(original))
                    with patch("bc.train.read_road") as reader, self.assertRaisesRegex(
                            ValueError, f"{label} collector conditions deviate"):
                        main(["--dataset", str(dataset), flag, str(other),
                              "--output", str(directory / "unused")])
                    reader.assert_not_called()

    def test_legacy_v1_and_v2_teacher_configs_are_not_environment_conditions(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            dataset, manifest = self.make_dataset(directory)
            path = dataset / "provenance.json"
            original = json.loads(path.read_text())
            legacy = {**original, "conditions": {**original["conditions"],
                                                 "target_speed": 12.0, "avoid_obstacles": True}}
            legacy.pop("teacher")
            path.write_text(json.dumps(legacy))
            val = directory / "validation"
            val.mkdir()
            (val / "split_manifest.json").write_text(json.dumps({"val": manifest["val"]}))
            (val / "provenance.json").write_text(json.dumps({
                **original, "teacher": {"name": "v2", "stage": "pace", "config": {"straight_limit": 30}}}))
            # Stop after condition checks; no model, optimizer or trajectory is executed.
            with patch("bc.train.execution_fingerprint", side_effect=RuntimeError("conditions verified")), \
                    self.assertRaisesRegex(RuntimeError, "conditions verified"):
                main(["--dataset", str(dataset), "--val-dataset", str(val),
                      "--output", str(directory / "unused")])

    def test_sampled_teacher_views_reject_reconstructed_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            dataset, _ = self.make_dataset(directory)
            path = dataset / "provenance.json"
            provenance = json.loads(path.read_text())
            path.write_text(json.dumps({**provenance, "kind": "matched_teacher_view"}))
            with patch("bc.train.BCPolicy") as policy, self.assertRaisesRegex(
                    ValueError, "stored four-frame inputs"):
                main(["--dataset", str(dataset), "--output", str(directory / "unused"),
                      "--history-frames", "8"])
            policy.assert_not_called()

    def test_plain_defaults_and_legacy_weighting_selection_are_preserved(self):
        for options, expected in (([], 1), (["--active-gas-weight", "40"], 40)):
            with patch("bc.train.train") as trainer:
                main(["--dataset", "unused", "--output", "unused", *options])
            self.assertEqual(trainer.call_args.args[0].active_gas_weight, expected)
        target = torch.tensor([[0., .1, .2], [0., .2, .1]])
        torch.testing.assert_close(action_weights(target), torch.ones_like(target))
        torch.testing.assert_close(action_weights(target, 40, 3),
                                   torch.tensor([[1., 1., 3.], [1., 40., 1.]]))
        validation = {"mse": {"steer": 2}, "weighted_mse": {"gas": 4, "brake": 6},
                      "weighted_mean_mse": 7}
        self.assertEqual(selection_score(validation), 7)
        self.assertEqual(selection_score(validation, steering_only=True), 2)
        self.assertEqual(selection_score(validation, controls_only=True), 5)


if __name__ == "__main__":
    unittest.main()
