import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from bc.contracts import BASELINE_CONDITIONS, environment_conditions
from bc.teacher_views import main
from bc.train import read_road, road_paths


class TestTeacherViews(unittest.TestCase):
    def raw(self, root, teacher, track=1, seeds=(11,), rows=300, legacy=False):
        directory = root / f"raw_{teacher}_{track}"
        directory.mkdir()
        conditions = dict(BASELINE_CONDITIONS) if legacy else environment_conditions(BASELINE_CONDITIONS)
        provenance = {"conditions": conditions,
                      "source_sha256": {"env_wrapper.py": "wrapper", "damage.py": "damage",
                                        "core/vendor/car_racing.py": "simulator"},
                      "python": "fixture-python", "platform": "fixture-platform",
                      "packages": {name: "fixture-version" for name in
                                   ("numpy", "gymnasium", "opencv-python", "box2d-py")}}
        if not legacy:
            provenance["teacher"] = {"name": teacher, "config": {"fixture": teacher}}
        (directory / "provenance.json").write_text(json.dumps(provenance))
        names = [f"track{track}_seed{seed}.npz" for seed in seeds]
        split = "val" if seeds[0] >= 31 else "train"
        (directory / "split_manifest.json").write_text(json.dumps({
            "selected_split": split, "selected_track_ids": [track], "selected_seeds": list(seeds),
            "train": names if split == "train" else [], "val": names if split == "val" else [], "test": []}))
        for name in names:
            seed = int(name.split("_seed")[1].removesuffix(".npz"))
            episode = {"track_id": track, "geometry_seed": seed, "track_points": [[0, 0, 1, 2]],
                       "track_variables": {"obstacles": []}, "start_t": 1.0,
                       "reset": {"seed": seed, "options": {"track_id": track}, "info": {}},
                       "conditions": conditions}
            (directory / name.replace(".npz", ".episode.json")).write_text(json.dumps(episode))
            values = (np.arange(rows, dtype=np.float32)[:, None]
                      + np.arange(4, dtype=np.float32)[None, :] / 8) / (rows + 2)
            if teacher == "v2":
                values = 1 - values
            observations = np.broadcast_to(values[:, :, None, None], (rows, 4, 84, 84)).copy()
            actions = np.zeros((rows, 3), dtype=np.float32)
            actions[:, 0] = np.arange(rows, dtype=np.float32) / rows
            actions[:, 1] = .2 if teacher == "v1" else .8
            actions[:, 2] = np.arange(rows, dtype=np.float32)[::-1] / rows
            np.savez_compressed(directory / name, observations=observations, actions=actions)
            summary = {"finished": True, "complete": True, "steps": rows, "trajectory": name}
            (directory / name.replace(".npz", ".summary.json")).write_text(json.dumps(summary))
        return directory

    def command(self, root, v1, v2, **options):
        return ["--v1-dataset", *map(str, v1), "--v2-dataset", *map(str, v2),
                "--output", str(root / options.get("output", "views")),
                "--track-ids", *map(str, options.get("tracks", (1,))),
                "--seeds", *map(str, options.get("seeds", (11,))),
                "--rows-per-road", str(options.get("rows", 256)),
                "--split", options.get("split", "train")]

    def test_exact_unique_quotas_balance_alignment_and_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            v1 = self.raw(root, "v1", seeds=(11, 12), legacy=True)
            v2 = self.raw(root, "v2", seeds=(11,))
            command = self.command(root, [v1], [v2])
            main(command)
            main(self.command(root, [v1], [v2], output="repeat"))
            name = "track1_seed11.npz"
            pure_rows = {}
            for arm in ("v1", "v2", "mixed"):
                directory = root / "views" / arm
                manifest = json.loads((directory / "split_manifest.json").read_text())
                self.assertEqual(manifest["train"], [name])
                self.assertEqual(manifest["val"], [])
                provenance = json.loads((directory / "provenance.json").read_text())
                self.assertEqual(provenance["seed"], 0)
                self.assertEqual(provenance["rows_per_road"], 256)
                self.assertEqual(provenance["kind"], "matched_teacher_view")
                with np.load(directory / name, allow_pickle=False) as data, \
                        np.load(root / "repeat" / arm / name, allow_pickle=False) as repeat:
                    self.assertEqual(set(data.files), {"observations", "actions", "source_rows", "source_teachers"})
                    self.assertEqual(data["observations"].shape, (256, 4, 84, 84))
                    self.assertEqual(data["actions"].shape, (256, 3))
                    self.assertEqual(data["source_rows"].dtype, np.int64)
                    for key in data.files:
                        np.testing.assert_array_equal(data[key], repeat[key])
                    for teacher, raw in (("v1", v1), ("v2", v2)):
                        mask = data["source_teachers"] == teacher
                        rows = data["source_rows"][mask]
                        expected = 128 if arm == "mixed" else 256 if arm == teacher else 0
                        self.assertEqual(len(rows), expected)
                        self.assertEqual(len(set(rows.tolist())), expected)
                        if not expected:
                            continue
                        x, y = read_road(raw / name)
                        np.testing.assert_array_equal(data["observations"][mask], x[rows])
                        np.testing.assert_array_equal(data["actions"][mask], y[rows])
                        source = provenance["sources"][teacher][name]
                        self.assertEqual(source["path"], str((raw / name).resolve()))
                        self.assertEqual(source["sha256"], hashlib.sha256((raw / name).read_bytes()).hexdigest())
                        self.assertEqual(source["teacher"]["name"], teacher)
                        if arm != "mixed":
                            pure_rows[teacher] = set(rows.tolist())
                        else:
                            self.assertTrue(set(rows.tolist()) <= pure_rows[teacher])
                    if arm == "mixed":
                        np.testing.assert_array_equal(data["source_teachers"], np.tile(["v1", "v2"], 128))

    def test_multiple_raw_dirs_and_validation_views_are_train_compatible(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            v1 = [self.raw(root, "v1", track=t, seeds=(31,), rows=10) for t in (1, 2)]
            v2 = [self.raw(root, "v2", track=t, seeds=(31,), rows=10) for t in (1, 2)]
            main(self.command(root, v1, v2, tracks=(1, 2), seeds=(31,), split="val", rows=8))
            val = root / "views" / "mixed"
            manifest = json.loads((val / "split_manifest.json").read_text())
            self.assertEqual(manifest["val"], ["track1_seed31.npz", "track2_seed31.npz"])
            paths = road_paths(Path("train"), {"train": ["track1_seed11.npz"]}, val, manifest)
            self.assertEqual([p.name for p in paths["val"]], manifest["val"])
            for path in paths["val"]:
                x, y = read_road(path)
                self.assertEqual(x.shape, (8, 4, 84, 84))
                self.assertEqual(y.shape, (8, 3))

    def test_missing_failed_short_duplicate_wrong_teacher_and_conditions_fail(self):
        for failure in ("missing", "failed", "short", "duplicate", "teacher", "conditions", "summary_teacher"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                v1 = self.raw(root, "v1", rows=10)
                v2 = self.raw(root, "v2", rows=10)
                directories = [v2]
                summary_path = v2 / "track1_seed11.summary.json"
                if failure == "missing":
                    (v2 / "track1_seed11.npz").unlink()
                elif failure in ("failed", "short", "summary_teacher"):
                    summary = json.loads(summary_path.read_text())
                    if failure == "summary_teacher":
                        summary["teacher"] = {"name": "v1"}
                    else:
                        summary["finished" if failure == "failed" else "steps"] = False if failure == "failed" else 4
                    summary_path.write_text(json.dumps(summary))
                elif failure == "duplicate":
                    directories.append(v2)
                else:
                    path = v2 / "provenance.json"
                    provenance = json.loads(path.read_text())
                    if failure == "teacher":
                        provenance["teacher"]["name"] = "v1"
                    else:
                        provenance["conditions"]["frame_skip"] = 2
                    path.write_text(json.dumps(provenance))
                with self.assertRaises(ValueError):
                    main(self.command(root, [v1], directories, rows=8))
                self.assertFalse((root / "views").exists())

    def test_per_teacher_config_is_consistent_across_raw_batches(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            v1 = self.raw(root, "v1", rows=10)
            v2 = [self.raw(root, "v2", track=t, rows=10) for t in (1, 2)]
            path = v2[1] / "provenance.json"
            provenance = json.loads(path.read_text())
            provenance["teacher"]["config"] = {"fixture": "different"}
            path.write_text(json.dumps(provenance))
            with self.assertRaisesRegex(ValueError, "Inconsistent v2 configurations"):
                main(self.command(root, [v1], v2, rows=8))
            self.assertFalse((root / "views").exists())

    def test_paired_simulator_runtime_and_episode_identity_must_match(self):
        for field in ("source_sha256", "python", "platform", "packages", "track_points",
                      "track_variables", "start_t", "reset", "conditions"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                v1 = self.raw(root, "v1", rows=10, legacy=True)
                v2 = self.raw(root, "v2", rows=10)
                is_runtime = field in ("source_sha256", "python", "platform", "packages")
                path = v2 / ("provenance.json" if is_runtime else "track1_seed11.episode.json")
                value = json.loads(path.read_text())
                if field == "source_sha256":
                    value[field]["core/vendor/car_racing.py"] = "different simulator"
                elif field == "packages":
                    value[field]["numpy"] = "different version"
                elif field == "conditions":
                    value[field]["warmup"] = 0
                else:
                    value[field] = "different"
                path.write_text(json.dumps(value))
                with self.assertRaisesRegex(ValueError, "fingerprints differ|episode geometry, reset or conditions differ"):
                    main(self.command(root, [v1], [v2], rows=8))
                self.assertFalse((root / "views").exists())

    def test_declared_grid_does_not_silently_intersect_or_include_test_roads(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            v1 = self.raw(root, "v1", seeds=(11, 12), rows=10)
            v2 = self.raw(root, "v2", seeds=(11,), rows=10)
            with self.assertRaisesRegex(ValueError, "Missing shared v2 roads"):
                main(self.command(root, [v1], [v2], seeds=(11, 12), rows=8))
            with self.assertRaisesRegex(ValueError, "selected train/val split"):
                main(self.command(root, [v1], [v2], seeds=(36,), rows=8))
            with self.assertRaisesRegex(ValueError, "positive and even"):
                main(self.command(root, [v1], [v2], rows=7))
            self.assertFalse((root / "views").exists())


if __name__ == "__main__":
    unittest.main()
