import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import torch
from torch import nn

from bc.contracts import BASELINE_CONDITIONS
from bc.model import BCPolicy
from bc.train import evaluate, main


class ScriptedControls(nn.Module):
    """Read a synthetic row ID from the newest causal image."""

    history_frames = 8

    def __init__(self, controls, mode=True):
        super().__init__()
        self.anchor = nn.Parameter(torch.zeros(()))
        self.register_buffer("controls", controls)
        self.mode_longitudinal = mode
        self.signed_longitudinal = not mode

    def forward(self, images, decode=True):
        indices = (images[:, -1, 0, 0] * 20).round().long()
        controls = self.controls[indices]
        if not decode:
            return controls
        decoder = BCPolicy.decode_mode if self.mode_longitudinal else BCPolicy.decode_signed
        return decoder(controls)


class TestBCMode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_threads = torch.get_num_threads()
        torch.set_num_threads(1)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.previous_threads)

    def test_forward_preserves_logits_and_decode_is_exclusive(self):
        model = BCPolicy(history_frames=8, mode_longitudinal=True)
        with torch.no_grad():
            model.head[-1].weight.zero_()
            model.head[-1].bias.copy_(torch.tensor([.3, -4., 2., 7., -.4]))
        images = torch.zeros((2, 8, 84, 84))
        with torch.inference_mode():
            controls = model(images, decode=False)
            self.assertEqual(controls.shape, (2, 5))
            expected = torch.tensor([[torch.tanh(torch.tensor(.3)), -4., 2., 7.,
                                      torch.sigmoid(torch.tensor(-.4))]]).repeat(2, 1)
            torch.testing.assert_close(controls, expected)
            torch.testing.assert_close(model(images), BCPolicy.decode_mode(controls))
        controls = torch.tensor([[.2, 3., -1., 0., .4], [-.1, 0., 3., 1., .9],
                                 [.5, -1., 0., 2., .3], [0., 2., 2., 2., .7]])
        decoded = BCPolicy.decode_mode(controls)
        torch.testing.assert_close(decoded, torch.tensor([[.2, .4, 0.], [-.1, 0., 0.],
                                                          [.5, 0., .3], [0., .7, 0.]]))
        self.assertTrue(torch.all(decoded[:, 1] * decoded[:, 2] == 0))

    def test_targets_are_strict_lossless_and_reject_any_overlap(self):
        actions = torch.tensor([[.2, .7, 0.], [-.3, 0., .1], [0., 0., 0.],
                                [.4, 1e-8, 0.], [-.4, 0., 1e-8]])
        modes, magnitude = BCPolicy.longitudinal_targets(actions)
        self.assertEqual(modes.dtype, torch.long)
        self.assertEqual(modes.device, actions.device)
        torch.testing.assert_close(modes, torch.tensor([0, 2, 1, 0, 2]))
        torch.testing.assert_close(magnitude.reshape(-1), actions[:, 1:].amax(dim=1))
        logits = torch.nn.functional.one_hot(modes, num_classes=3).to(actions.dtype)
        controls = torch.cat((actions[:, :1], logits, magnitude.reshape(-1, 1)), dim=1)
        torch.testing.assert_close(BCPolicy.decode_mode(controls), actions, rtol=0, atol=0)
        for gas, brake in ((.7, .1), (1e-8, 1e-8)):
            with self.subTest(gas=gas, brake=brake), self.assertRaises(ValueError):
                BCPolicy.longitudinal_targets(torch.tensor([[0., gas, brake]]))
        with self.assertRaises(ValueError):
            BCPolicy(history_frames=8, mode_longitudinal=True, signed_longitudinal=True)
        with self.assertRaises(ValueError):
            BCPolicy(mode_longitudinal=True)

    def test_initialization_preserves_shared_layers_steering_and_rng(self):
        torch.manual_seed(0)
        original = BCPolicy(history_frames=8)
        original_rng = torch.get_rng_state().clone()
        torch.manual_seed(0)
        mode = BCPolicy(history_frames=8, mode_longitudinal=True)
        self.assertTrue(torch.equal(torch.get_rng_state(), original_rng))
        self.assertEqual(mode.head[-1].out_features, 5)
        for name, value in original.state_dict().items():
            actual = mode.state_dict()[name]
            if name.startswith("head.2."):
                value, actual = value[:1], actual[:1]
            self.assertTrue(torch.equal(value, actual), name)
        self.assertFalse(torch.equal(mode.head[-1].weight[1:3], original.head[-1].weight[1:3]))
        self.assertFalse(torch.equal(mode.head[-1].weight[4], original.head[-1].weight[1]))
        torch.manual_seed(0)
        repeat = BCPolicy(history_frames=8, mode_longitudinal=True)
        for name, value in mode.state_dict().items():
            self.assertTrue(torch.equal(value, repeat.state_dict()[name]), name)
        with torch.inference_mode():
            images = torch.rand((2, 8, 84, 84))
            torch.testing.assert_close(mode(images)[:, 0], original(images)[:, 0])

    def test_v5_checkpoint_loads_cpu_and_act_decodes_with_reset_history(self):
        policy = BCPolicy(history_frames=8, mode_longitudinal=True).eval()
        with torch.no_grad():
            policy.head[-1].weight.zero_()
            policy.head[-1].bias.copy_(torch.tensor([.2, -2., -1., 3., .4]))
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "mode.pt"
            torch.save({"model": "BCPolicy-mode-history8-v5", "history_frames": 8,
                        "state_dict": policy.state_dict()}, checkpoint)
            loaded = BCPolicy.from_checkpoint(checkpoint)
            self.assertTrue(loaded.mode_longitudinal)
            self.assertFalse(loaded.signed_longitudinal)
            self.assertFalse(loaded.training)
            self.assertEqual(next(loaded.parameters()).device.type, "cpu")
            observation = np.full((4, 84, 84), .3, dtype=np.float32)
            loaded.reset(observation)
            with torch.inference_mode():
                images = torch.full((1, 8, 84, 84), .3)
                torch.testing.assert_close(loaded(images), policy(images), rtol=0, atol=0)
                expected = loaded(images)[0].numpy()
            action = loaded.act(observation)
            np.testing.assert_array_equal(action, expected)
            self.assertEqual(action.shape, (3,))
            self.assertEqual(action.dtype, np.float32)
            self.assertTrue(np.isfinite(action).all())
            self.assertTrue(np.all(action >= [-1, 0, 0]) and np.all(action <= 1))
            self.assertEqual(action[1], 0)
            self.assertGreater(action[2], 0)

    def test_mode_trainer_roundtrip_keeps_decoded_unit_weight_selection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dataset = root / "synthetic"
            dataset.mkdir()
            names = ["track1_seed11.npz", "track2_seed12.npz", "track1_seed31.npz"]
            actions = np.array([[.1, .4, 0.], [-.1, 0., .05], [0., 0., 0.]], dtype=np.float32)
            for name in names:
                np.savez(dataset / name, observations=np.zeros((3, 4, 84, 84), dtype=np.float32),
                         actions=actions)
            (dataset / "split_manifest.json").write_text(json.dumps({
                "train": names[:2], "val": names[2:], "test": ["never_open.npz"]}))
            (dataset / "provenance.json").write_text(json.dumps({
                "conditions": BASELINE_CONDITIONS, "fixture": "synthetic mode test only"}))
            output = root / "model"
            with patch("builtins.print"):
                result = main(["--dataset", str(dataset), "--output", str(output), "--device", "cpu",
                               "--epochs", "1", "--batch-size", "4", "--max-train-samples", "6",
                               "--num-threads", "1", "--history-frames", "8", "--mode-longitudinal",
                               "--balanced-actions", "--continuous-batches"])
            self.assertTrue(result["config"]["mode_longitudinal"])
            self.assertFalse(result["config"]["signed_longitudinal"])
            self.assertEqual(result["config"]["training_objective"],
                             "(steer_mse+mode_ce+active_magnitude_mse)/3")
            self.assertEqual(result["config"]["active_gas_weight"], 1)
            self.assertEqual(result["config"]["active_brake_weight"], 1)
            self.assertEqual(result["selection_metric"], "weighted_mean_mse")
            record = result["history"][0]
            self.assertEqual(record["train_samples"], 6)
            self.assertEqual(record["optimizer_steps"], 2)
            self.assertEqual(result["best_val_selection_score"], record["val"]["weighted_mean_mse"])
            self.assertEqual(record["val"]["weighted_mean_mse"], record["val"]["mean_mse"])
            self.assertEqual(result, json.loads((output / "history.json").read_text()))
            checkpoint = torch.load(output / "best.pt", map_location="cpu", weights_only=True)
            self.assertEqual(checkpoint["model"], "BCPolicy-mode-history8-v5")
            policy = BCPolicy.from_checkpoint(output / "best.pt")
            self.assertTrue(policy.mode_longitudinal)
            action = policy.act(np.zeros((4, 84, 84), dtype=np.float32))
            self.assertEqual(action[1] * action[2], 0)

    def assert_mode_metrics(self, metrics, actions, predicted_modes, predicted_magnitude):
        target_modes = np.where(actions[:, 1] > 0, 0, np.where(actions[:, 2] > 0, 2, 1))
        confusion = np.zeros((3, 3), dtype=int)
        np.add.at(confusion, (target_modes, predicted_modes), 1)
        self.assertEqual(metrics["names"], ["accelerate", "coast", "brake"])
        self.assertEqual(metrics["confusion"], confusion.tolist())
        self.assertEqual(metrics["count"], len(actions))
        accuracy = np.mean(target_modes == predicted_modes) if len(actions) else None
        if accuracy is None:
            self.assertIsNone(metrics["accuracy"])
        else:
            self.assertAlmostEqual(metrics["accuracy"], accuracy)
        brakes = int(np.count_nonzero(target_modes == 2))
        self.assertEqual(metrics["brake_recall"], None if not brakes else confusion[2, 2] / brakes)
        for name, target, predicted in (("accelerate_to_brake", 0, 2), ("brake_to_accelerate", 2, 0)):
            total = int(confusion[target].sum())
            count = int(confusion[target, predicted])
            self.assertEqual(metrics[name], {"count": count, "total": total,
                                             "rate": count / total if total else None})
        magnitude_error = np.abs(predicted_magnitude - actions[:, 1:].max(axis=1))
        active = target_modes != 1
        for actual, mask in ((metrics["active_magnitude"], active),
                             (metrics["active_magnitude"]["by_mode"]["accelerate"], target_modes == 0),
                             (metrics["active_magnitude"]["by_mode"]["brake"], target_modes == 2)):
            self.assertEqual(actual["count"], int(mask.sum()))
            if mask.any():
                self.assertAlmostEqual(actual["mae"], float(magnitude_error[mask].mean()), places=6)
            else:
                self.assertIsNone(actual["mae"])
        small = (actions[:, 2] > 0) & (actions[:, 2] <= .1)
        count = int(small.sum())
        self.assertEqual(metrics["small_brake"], {
            "count": count, "recall": float(np.mean(predicted_modes[small] == 2)) if count else None,
            "accelerate_confusion_count": int(np.count_nonzero(predicted_modes[small] == 0))})

    def test_mode_metrics_raw_magnitude_denominators_and_first_ten_across_roads(self):
        target_modes = np.array([0, 2, 2, 1, 0, 2, 0, 1, 2, 0, 2, 0, 2, 0, 1])
        target_magnitude = np.array([.4, .1, .05, 0, .8, .2, 1e-6, 0, .3, .2, .9, .7, .08, .6, 0],
                                    dtype=np.float32)
        predicted_modes = np.array([2, 0, 2, 0, 1, 1, 0, 1, 2, 0, 0, 2, 2, 2, 1])
        magnitude = np.array([.5, .2, .1, .7, .9, .4, .1, .6, .2, .3, .8, .6, .04, .5, .9],
                             dtype=np.float32)
        actions = np.zeros((15, 3), dtype=np.float32)
        actions[:, 1] = np.where(target_modes == 0, target_magnitude, 0)
        actions[:, 2] = np.where(target_modes == 2, target_magnitude, 0)
        logits = np.full((15, 3), -2., dtype=np.float32)
        logits[np.arange(15), predicted_modes] = 2
        controls = torch.from_numpy(np.column_stack((np.zeros(15, dtype=np.float32), logits, magnitude)))
        observations = np.broadcast_to(np.arange(15, dtype=np.float32)[:, None, None, None] / 20,
                                       (15, 4, 84, 84)).copy()
        roads = {"long": (observations[:12], actions[:12]), "short": (observations[12:], actions[12:])}
        for mode in (True, False):
            with self.subTest(mode=mode):
                signed = np.where(predicted_modes == 0, magnitude,
                                  np.where(predicted_modes == 2, -magnitude, 0))
                model = ScriptedControls(controls if mode else torch.from_numpy(
                    np.column_stack((np.zeros(15, dtype=np.float32), signed))), mode=mode)
                measured_magnitude = magnitude if mode else np.abs(signed)
                with patch("bc.train.read_road", side_effect=roads.__getitem__):
                    result = evaluate(model, ["long", "short"], batch_size=4, include_startup=True)
                self.assertEqual(result["samples"], 15)
                self.assert_mode_metrics(result["longitudinal_mode"], actions,
                                         predicted_modes, measured_magnitude)
                self.assertEqual(result["longitudinal_mode"]["confusion"],
                                 [[2, 1, 3], [1, 2, 0], [2, 1, 3]])
                startup = result["startup"]["mode"]
                initial = np.r_[0:10, 12:15]
                self.assert_mode_metrics(startup["first_10"], actions[initial],
                                         predicted_modes[initial], measured_magnitude[initial])
                self.assertEqual(len(startup["by_step"]), 10)
                for step, metrics in enumerate(startup["by_step"]):
                    self.assertEqual(metrics["step"], step)
                    indices = np.array([step, 12 + step] if step < 3 else [step])
                    self.assert_mode_metrics(metrics, actions[indices], predicted_modes[indices],
                                             measured_magnitude[indices])
                self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)


if __name__ == "__main__":
    unittest.main()
