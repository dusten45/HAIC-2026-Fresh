import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from bc.dataset import SPLIT_SEEDS, _observation, main
from core.vendor.car_racing import CarRacing
from env_wrapper import CarEnvironment
from gymnasium.wrappers.time_limit import TimeLimit
from oracle.oracle_controller import OracleController


class TestDataset(unittest.TestCase):
    def test_split_rejects_exposed_mismatched_and_duplicate_seeds(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stderr(io.StringIO()):
            path = str(Path(temporary) / "dataset")
            for split, seeds in (("train", ["10"]), ("val", ["11"]),
                                 ("test", ["31"]), ("train", ["11", "11"])):
                with self.subTest(split=split, seeds=seeds), self.assertRaises(SystemExit):
                    main(["--output", path, "--split", split, "--seeds", *seeds])
                self.assertFalse(Path(path).exists())
            with self.assertRaises(SystemExit):
                main(["--output", path, "--split", "train", "--seeds", "11",
                      "--track-ids", "1", "1"])
            self.assertFalse(Path(path).exists())

    def test_immutable_split_manifest_contains_only_finished_complete_roads(self):
        def fake_episode(args, output, track, seed):
            return {"trajectory": f"track{track}_seed{seed}.npz", "geometry_seed": seed,
                    "finished": seed == 31, "complete": seed == 31}

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "dataset"
            with patch("bc.dataset.collect_episode", side_effect=fake_episode) as collect:
                main(["--output", str(output), "--split", "val", "--track-ids", "2",
                      "--seeds", "31", "32"])
            self.assertEqual(collect.call_count, 2)
            manifest = json.loads((output / "split_manifest.json").read_text())
            self.assertEqual(manifest["split_seeds"], SPLIT_SEEDS)
            self.assertEqual(manifest["exposed_seeds_excluded"], list(range(1, 11)))
            self.assertEqual(manifest["train"], [])
            self.assertEqual(manifest["val"], ["track2_seed31.npz"])
            self.assertEqual(manifest["test"], [])
            self.assertEqual(json.loads((output / "manifest.json").read_text())["eligible_count"], 1)
            before = (output / "split_manifest.json").read_bytes()
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(["--output", str(output), "--split", "val", "--seeds", "31"])
            self.assertEqual((output / "split_manifest.json").read_bytes(), before)

    def test_observations_require_exact_float32_policy_shape(self):
        valid = np.zeros((4, 84, 84), dtype=np.float32)
        self.assertIs(_observation(valid), valid)
        for invalid in (valid.astype(np.float64), valid[0],
                        np.full_like(valid, np.nan), np.full_like(valid, 2)):
            with self.subTest(dtype=invalid.dtype, shape=invalid.shape), self.assertRaises(ValueError):
                _observation(invalid)

    def test_real_short_rollout_pre_action_alignment_and_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "dataset"
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--output", str(output), "--split", "train", "--track-ids", "1",
                      "--seeds", "11", "--max-steps", "1"])
            summary = json.loads((output / "track1_seed11.summary.json").read_text())
            manifest = json.loads((output / "split_manifest.json").read_text())
            trace = [json.loads(line) for line in (output / "track1_seed11.jsonl").read_text().splitlines()]
            with np.load(output / "track1_seed11.npz", allow_pickle=False) as data:
                observations, actions = data["observations"], data["actions"]
            self.assertEqual(observations.shape, (1, 4, 84, 84))
            self.assertEqual(observations.dtype, np.float32)
            self.assertEqual(actions.shape, (1, 3))
            self.assertEqual(actions.dtype, np.float32)
            self.assertEqual(summary["steps"], len(trace))
            self.assertFalse(summary["finished"])
            self.assertFalse(summary["complete"])
            self.assertEqual(summary["reason"], "runner_max_steps")
            self.assertEqual(manifest["train"], [])
            self.assertEqual(trace[0]["step"], 0)
            self.assertEqual(trace[0]["pre"]["position"], trace[0]["pre"]["state"]["position"])
            self.assertIn("damage", trace[0]["post"])
            self.assertIn("finished", trace[0])
            self.assertFalse((output / "track1_seed11.partial.float32").exists())
            self.assertEqual(hashlib.sha256((output / "track1_seed11.npz").read_bytes()).hexdigest(),
                             summary["sha256"])
            provenance = json.loads((output / "provenance.json").read_text())
            self.assertIn("oracle/oracle_controller.py", provenance["source_sha256"])
            self.assertIn("env_wrapper.py", provenance["source_sha256"])
            self.assertFalse(provenance["conditions"]["domain_randomize"])
            base = CarRacing(continuous=True, render_mode="rgb_array", domain_randomize=False)
            env = CarEnvironment(TimeLimit(base, max_episode_steps=204), skip_frames=4, no_operation=50)
            try:
                reset_observation, _ = env.reset(seed=11, options={"track_id": 1})
                expected_action, _ = OracleController(base, target_speed=12.0,
                                                       avoid_obstacles=True).act()
                np.testing.assert_array_equal(observations[0], reset_observation)
                np.testing.assert_array_equal(actions[0], expected_action)
                np.testing.assert_array_equal(actions[0], trace[0]["action"])
            finally:
                env.close()


if __name__ == "__main__":
    unittest.main()
