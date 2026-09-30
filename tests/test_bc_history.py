from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import torch
from torch import nn

from bc.model import BCPolicy
from bc.train import assemble_history, evaluate, training_batches


def chronological_observations(rows=9, base=0.0):
    observations = np.full((rows, 4, 84, 84), .9, dtype=np.float32)
    observations[:, 3] = (base + np.arange(rows, dtype=np.float32) / 20)[:, None, None]
    return observations


class TestBCHistory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_threads = torch.get_num_threads()
        torch.set_num_threads(1)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.previous_threads)

    def test_indexed_history_is_causal_and_uses_only_newest_channels(self):
        observations = chronological_observations()
        original = observations.copy()
        indices = np.array([8, 0, 6, 2, 8])
        histories = assemble_history(observations, indices, 8)
        for index, history in zip(indices, histories):
            expected = np.stack([observations[max(0, index - lag), 3]
                                 for lag in range(7, -1, -1)])
            np.testing.assert_array_equal(history, expected)
        np.testing.assert_array_equal(observations, original)
        np.testing.assert_array_equal(assemble_history(observations, indices), observations[indices])
        self.assertEqual(histories.dtype, np.float32)

    def test_online_offline_rows_zero_through_eight_and_episode_reset(self):
        observations = chronological_observations()
        policy = BCPolicy(history_frames=8).eval()
        captured = []
        handle = policy.register_forward_pre_hook(
            lambda model, inputs: captured.append(inputs[0].clone()))
        try:
            for explicit_reset in (False, True):
                if explicit_reset:
                    policy.reset(observations[0])
                for row, observation in enumerate(observations):
                    action = policy.act(observation)
                    expected = assemble_history(observations, np.array([row]), 8)
                    np.testing.assert_array_equal(captured[-1].numpy(), expected)
                    self.assertEqual(action.shape, (3,))
                    self.assertEqual(action.dtype, np.float32)
                    self.assertTrue(np.isfinite(action).all())
                    self.assertTrue(np.all(action >= [-1, 0, 0]) and np.all(action <= 1))
                    # History owns its frames rather than retaining a mutable observation view.
                    observation[-1, 0, 0] = .8
                    assert policy._history is not None
                    np.testing.assert_array_equal(policy._history[-1], expected[0, -1])
                    observation[-1, 0, 0] = row / 20
            next_episode = chronological_observations(1, base=.6)[0]
            policy.reset(next_episode)
            assert policy._history is not None
            self.assertEqual(len(policy._history), 7)
            policy.act(next_episode)
            np.testing.assert_array_equal(captured[-1].numpy(),
                                          np.repeat(next_episode[None, -1:], 8, axis=1))
            before = np.stack(tuple(policy._history))
            policy(torch.zeros((2, 8, 84, 84)))
            np.testing.assert_array_equal(np.stack(tuple(policy._history)), before)
        finally:
            handle.remove()

    def test_seeded_initialization_matches_unchanged_cnn_and_rng(self):
        for seed in (0, 42):
            with self.subTest(seed=seed):
                torch.manual_seed(seed)
                original = nn.Module()
                original.features = nn.Sequential(
                    nn.Conv2d(4, 8, kernel_size=8, stride=4), nn.ReLU(),
                    nn.Conv2d(8, 16, kernel_size=4, stride=2), nn.ReLU(),
                    nn.Conv2d(16, 16, kernel_size=3), nn.ReLU(), nn.Flatten())
                original.head = nn.Sequential(nn.Linear(16 * 7 * 7, 32), nn.ReLU(), nn.Linear(32, 3))
                original_rng = torch.get_rng_state().clone()
                torch.manual_seed(seed)
                four = BCPolicy()
                self.assertTrue(torch.equal(torch.get_rng_state(), original_rng))
                torch.manual_seed(seed)
                eight = BCPolicy(history_frames=8)
                self.assertTrue(torch.equal(torch.get_rng_state(), original_rng))
                self.assertEqual(sum(p.numel() for p in four.parameters()), 31659)
                self.assertEqual(sum(p.numel() for p in eight.parameters()), 33707)
                for name, parameter in original.state_dict().items():
                    self.assertTrue(torch.equal(parameter, four.state_dict()[name]), name)
                    extended = eight.state_dict()[name]
                    if name == "features.0.weight":
                        self.assertEqual(torch.count_nonzero(extended[:, :4]).item(), 0)
                        extended = extended[:, 4:]
                    self.assertTrue(torch.equal(parameter, extended), name)
                images = torch.rand((3, 8, 84, 84))
                with torch.inference_mode():
                    torch.testing.assert_close(eight(images), four(images[:, 4:]), rtol=1e-6, atol=1e-7)

    def test_zero_initialized_older_channels_receive_gradients(self):
        torch.manual_seed(0)
        policy = BCPolicy(history_frames=8)
        policy(torch.rand((3, 8, 84, 84))).sum().backward()
        gradient = policy.features[0].weight.grad[:, :4]
        self.assertTrue(torch.isfinite(gradient).all())
        self.assertTrue(torch.all(gradient.abs().sum(dim=(0, 2, 3)) > 0))

    def test_shuffled_batches_keep_road_history_before_cross_road_carry(self):
        roads = {
            "first": (chronological_observations(9), np.arange(9).reshape(-1, 1)),
            "second": (chronological_observations(4, base=.5), np.arange(9, 13).reshape(-1, 1)),
        }
        plan = [("first", 9, False), ("second", 4, False)]
        results = []
        for history_frames in (4, 8):
            for continuous in (False, True):
                rng = np.random.default_rng(42)
                with patch("bc.train.read_road", side_effect=roads.__getitem__):
                    batches = list(training_batches(plan, rng, 5, continuous, history_frames))
                self.assertEqual([len(y) for _, y, _ in batches],
                                 [5, 5, 3] if continuous else [5, 4, 4])
                images = np.concatenate([x for x, _, _ in batches])
                targets = np.concatenate([y for _, y, _ in batches]).ravel()
                for image, target in zip(images, targets):
                    road = roads["first" if target < 9 else "second"][0]
                    index = target if target < 9 else target - 9
                    expected = assemble_history(road, np.array([index]), history_frames)[0]
                    np.testing.assert_array_equal(image, expected)
                results.append((targets, rng.integers(100000)))
        for targets, next_random in results[1:]:
            np.testing.assert_array_equal(targets, results[0][0])
            self.assertEqual(next_random, results[0][1])

    def test_evaluate_reconstructs_each_indexed_batch_and_road(self):
        model = BCPolicy(history_frames=8)
        roads = [chronological_observations(), chronological_observations(3, base=.5)]
        captured = []
        handle = model.register_forward_pre_hook(
            lambda model, inputs: captured.append(inputs[0].clone()))
        try:
            with patch("bc.train.read_road", side_effect=[
                    (road, np.zeros((len(road), 3), dtype=np.float32)) for road in roads]):
                result = evaluate(model, ["first", "second"], batch_size=4)
            self.assertEqual(result["samples"], 12)
            self.assertEqual([len(batch) for batch in captured], [4, 4, 1, 3])
            expected = np.concatenate([assemble_history(road, np.arange(len(road)), 8)
                                       for road in roads])
            np.testing.assert_array_equal(torch.cat(captured).numpy(), expected)
        finally:
            handle.remove()

    def test_checkpoint_roundtrip_and_both_legacy_formats(self):
        formats = [("BCPolicy-v1", {}), ("BCPolicy-motion-v2", {"motion": True}),
                   ("BCPolicy-history8-v3", {"history_frames": 8})]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "checkpoint.pt"
            for version, kwargs in formats:
                with self.subTest(version=version):
                    policy = BCPolicy(**kwargs)
                    checkpoint = {"model": version, "state_dict": policy.state_dict()}
                    if version == "BCPolicy-history8-v3":
                        checkpoint["history_frames"] = 8
                    torch.save(checkpoint, path)
                    loaded = BCPolicy.from_checkpoint(path)
                    self.assertEqual(loaded.history_frames, kwargs.get("history_frames", 4))
                    self.assertEqual(loaded.motion, kwargs.get("motion", False))
                    self.assertFalse(loaded.training)
                    self.assertIsNone(loaded._history)
                    for name, value in policy.state_dict().items():
                        self.assertTrue(torch.equal(value, loaded.state_dict()[name]))
                    images = torch.rand((2, loaded.history_frames, 84, 84))
                    with torch.inference_mode():
                        torch.testing.assert_close(loaded(images), policy(images), rtol=0, atol=0)
            torch.save({"model": "BCPolicy-history8-v3",
                        "state_dict": BCPolicy(history_frames=8).state_dict()}, path)
            with self.assertRaisesRegex(ValueError, "history length"):
                BCPolicy.from_checkpoint(path)

    def test_history8_rejects_motion_recovery_and_invalid_external_shape(self):
        with self.assertRaisesRegex(ValueError, "motion features"):
            BCPolicy(motion=True, history_frames=8)
        with self.assertRaisesRegex(ValueError, "must be 4 or 8"):
            BCPolicy(history_frames=6)
        with patch("bc.train.read_road") as reader:
            with self.assertRaisesRegex(ValueError, "recovery"):
                list(training_batches([("unused", 1, True)], np.random.default_rng(0),
                                      4, history_frames=8))
            reader.assert_not_called()
        policy = BCPolicy(history_frames=8)
        for operation in (policy.reset, policy.act):
            with self.assertRaisesRegex(ValueError, "Expected finite observation"):
                operation(np.zeros((8, 84, 84), dtype=np.float32))


if __name__ == "__main__":
    unittest.main()
