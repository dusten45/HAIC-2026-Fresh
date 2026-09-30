import contextlib
import copy
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
            summary = {"trajectory": f"track{track}_seed{seed}.npz", "geometry_seed": seed,
                       "finished": seed == 21, "complete": seed == 21}
            (output / f"track{track}_seed{seed}.summary.json").write_text(json.dumps(summary))
            return summary

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "dataset"
            with patch("bc.dataset.collect_episode", side_effect=fake_episode) as collect:
                main(["--output", str(output), "--split", "train", "--track-ids", "2",
                      "--seeds", "21", "22"])
            self.assertEqual(collect.call_count, 2)
            manifest = json.loads((output / "split_manifest.json").read_text())
            self.assertEqual(manifest["split_seeds"], SPLIT_SEEDS)
            self.assertEqual(manifest["exposed_seeds_excluded"], list(range(1, 11)))
            self.assertEqual(manifest["train"], ["track2_seed21.npz"])
            self.assertEqual(manifest["val"], [])
            self.assertEqual(manifest["test"], [])
            self.assertEqual(json.loads((output / "manifest.json").read_text())["eligible_count"], 1)
            before = (output / "split_manifest.json").read_bytes()
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(["--output", str(output), "--split", "train", "--seeds", "21"])
            self.assertEqual((output / "split_manifest.json").read_bytes(), before)

    def test_resume_skips_completed_and_archives_interrupted_road_once(self):
        def fake_episode(args, output, track, seed):
            name = f"track{track}_seed{seed}"
            summary = {"track_id": track, "geometry_seed": seed, "complete": True,
                       "finished": seed == 21, "trajectory": f"{name}.npz"}
            (output / f"{name}.npz").write_bytes(b"complete trajectory")
            (output / f"{name}.summary.json").write_text(json.dumps(summary))
            return summary

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "dataset"
            command = ["--output", str(output), "--split", "train", "--track-ids", "2",
                       "--seeds", "21", "28"]
            with patch("bc.dataset.collect_episode", side_effect=fake_episode):
                main(command)
            original = json.loads((output / "provenance.json").read_text())
            original["arguments"].pop("resume")  # Pre-resume collector provenance.
            original["source_sha256"]["bc/dataset.py"] = "previous collector hash"
            for name in ("bc/contracts.py", "oracle/recording.py"):
                original["source_sha256"].pop(name)
            (output / "provenance.json").write_text(json.dumps(original))
            provenance_before = (output / "provenance.json").read_bytes()
            complete_before = {path.name: path.read_bytes() for path in
                               (output / "track2_seed21.summary.json", output / "track2_seed21.npz")}
            partial = {"track2_seed28.episode.json": b"old episode",
                       "track2_seed28.jsonl": b"old trace",
                       "track2_seed28.partial.float32": b"old pixels",
                       "track2_seed28.npz": b"interrupted NPZ",
                       "track2_seed28.summary.json": b'{"complete": false}'}
            for name, content in partial.items():
                (output / name).write_bytes(content)

            def recollect(args, path, track, seed):
                self.assertEqual((track, seed), (2, 28))
                self.assertTrue(all(not (path / name).exists() for name in partial))
                return fake_episode(args, path, track, seed)

            with patch("bc.dataset.collect_episode", side_effect=recollect) as collect:
                main([*command, "--resume"])
            self.assertEqual(collect.call_count, 1)
            archives = list((output / "interrupted_attempts").iterdir())
            self.assertEqual(len(archives), 1)
            self.assertEqual({path.name: path.read_bytes() for path in archives[0].iterdir()}, partial)
            self.assertEqual((output / "provenance.json").read_bytes(), provenance_before)
            for name, content in complete_before.items():
                self.assertEqual((output / name).read_bytes(), content)
            resume = json.loads(next(output.glob("resume_*.json")).read_text())
            self.assertTrue(resume["arguments"]["resume"])
            self.assertEqual(resume["original_provenance_sha256"],
                             hashlib.sha256(provenance_before).hexdigest())
            self.assertEqual(resume["collector_source_change"]["original"], "previous collector hash")
            self.assertNotEqual(resume["collector_source_change"]["current"], "previous collector hash")
            self.assertEqual(resume["source_sha256"]["oracle/oracle_controller.py"],
                             original["source_sha256"]["oracle/oracle_controller.py"])
            self.assertEqual(set(resume["source_fingerprint_migration"]["added_source_sha256"]),
                             {"bc/contracts.py", "oracle/recording.py"})
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertEqual(manifest["episode_count"], 2)
            self.assertEqual(manifest["finished_count"], 1)
            self.assertEqual(manifest["eligible_count"], 1)
            self.assertEqual(json.loads((output / "split_manifest.json").read_text())["train"],
                             ["track2_seed21.npz"])
            with patch("bc.dataset.collect_episode") as collect:
                main([*command, "--resume"])
            collect.assert_not_called()
            self.assertEqual(len(list(output.glob("resume_*.json"))), 2)
            self.assertEqual(list((output / "interrupted_attempts").iterdir()), archives)

    def test_resume_rejects_incompatible_grid_conditions_and_frozen_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "dataset"
            command = ["--output", str(output), "--split", "train", "--track-ids", "2",
                       "--seeds", "21"]
            with patch("bc.dataset.collect_episode", side_effect=RuntimeError("interrupted")):
                with self.assertRaises(RuntimeError):
                    main(command)
            original = json.loads((output / "provenance.json").read_text())
            for field, value in (("split", "val"), ("track_ids", [1]), ("seeds", [22]),
                                 ("conditions", {"target_speed": 13}),
                                 ("oracle/oracle_controller.py", "changed teacher"),
                                 ("env_wrapper.py", "changed environment"),
                                 ("core/vendor/car_racing.py", "changed core")):
                with self.subTest(field=field):
                    incompatible = copy.deepcopy(original)
                    if field == "conditions":
                        incompatible[field].update(value)
                    elif field.endswith(".py"):
                        incompatible["source_sha256"][field] = value
                    else:
                        incompatible["arguments"][field] = value
                    (output / "provenance.json").write_text(json.dumps(incompatible))
                    before = (output / "provenance.json").read_bytes()
                    with patch("bc.dataset.collect_episode") as collect:
                        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                            main([*command, "--resume"])
                    collect.assert_not_called()
                    self.assertEqual((output / "provenance.json").read_bytes(), before)
                    self.assertEqual({path.name for path in output.iterdir()},
                                     {"provenance.json", "source_snapshot"})

    def test_resume_preserves_new_and_legacy_finalized_capped_attempts(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy), tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary) / "dataset"
                command = ["--output", str(output), "--split", "train", "--track-ids", "1",
                           "--seeds", "21", "--max-steps", "1"]

                def capped(args, directory, track, seed):
                    name = f"track{track}_seed{seed}"
                    summary = {"track_id": track, "geometry_seed": seed, "complete": False,
                               "finished": False, "reason": "runner_max_steps", "steps": 1,
                               "trajectory": f"{name}.npz"}
                    if not legacy:
                        summary["attempt_finalized"] = True
                    (directory / f"{name}.npz").write_bytes(b"finalized capped trajectory")
                    (directory / f"{name}.summary.json").write_text(json.dumps(summary))
                    return summary

                with patch("bc.dataset.collect_episode", side_effect=capped):
                    main(command)
                original = (output / "track1_seed21.summary.json").read_bytes()
                with patch("bc.dataset.collect_episode") as collect:
                    main([*command, "--resume"])
                    main([*command, "--resume"])
                collect.assert_not_called()
                self.assertEqual((output / "track1_seed21.summary.json").read_bytes(), original)
                self.assertFalse((output / "interrupted_attempts").exists())
                self.assertEqual(json.loads((output / "split_manifest.json").read_text())["train"], [])

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
                      "--seeds", "21", "--max-steps", "1"])
            summary = json.loads((output / "track1_seed21.summary.json").read_text())
            manifest = json.loads((output / "split_manifest.json").read_text())
            trace = [json.loads(line) for line in (output / "track1_seed21.jsonl").read_text().splitlines()]
            with np.load(output / "track1_seed21.npz", allow_pickle=False) as data:
                observations, actions = data["observations"], data["actions"]
            self.assertEqual(observations.shape, (1, 4, 84, 84))
            self.assertEqual(observations.dtype, np.float32)
            self.assertEqual(actions.shape, (1, 3))
            self.assertEqual(actions.dtype, np.float32)
            self.assertEqual(summary["steps"], len(trace))
            self.assertFalse(summary["finished"])
            self.assertFalse(summary["complete"])
            self.assertTrue(summary["attempt_finalized"])
            self.assertEqual(summary["reason"], "runner_max_steps")
            self.assertEqual(manifest["train"], [])
            self.assertEqual(trace[0]["step"], 0)
            self.assertEqual(trace[0]["pre"]["position"], trace[0]["pre"]["state"]["position"])
            self.assertIn("damage", trace[0]["post"])
            self.assertIn("finished", trace[0])
            self.assertFalse((output / "track1_seed21.partial.float32").exists())
            self.assertEqual(hashlib.sha256((output / "track1_seed21.npz").read_bytes()).hexdigest(),
                             summary["sha256"])
            provenance = json.loads((output / "provenance.json").read_text())
            self.assertIn("oracle/oracle_controller.py", provenance["source_sha256"])
            self.assertIn("env_wrapper.py", provenance["source_sha256"])
            self.assertFalse(provenance["conditions"]["domain_randomize"])
            base = CarRacing(continuous=True, render_mode="rgb_array", domain_randomize=False)
            env = CarEnvironment(TimeLimit(base, max_episode_steps=204), skip_frames=4, no_operation=50)
            try:
                reset_observation, _ = env.reset(seed=21, options={"track_id": 1})
                expected_action, _ = OracleController(base, target_speed=12.0,
                                                       avoid_obstacles=True).act()
                np.testing.assert_array_equal(observations[0], reset_observation)
                np.testing.assert_array_equal(actions[0], expected_action)
                np.testing.assert_array_equal(actions[0], trace[0]["action"])
            finally:
                env.close()


if __name__ == "__main__":
    unittest.main()
