import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from oracle.oracle_controller import TrackPath
from oracle.v2_report import corners, driving_metrics, main, matched_deltas, report


class TestV2Report(unittest.TestCase):
    def provenance(self, baseline=False, stage="braking", teacher_source="teacher"):
        return {"args": {"track_ids": [1], "seeds": [1, 2, 3],
                         **({"repeats": 1, "frame_skip": 4, "warmup": 50} if baseline else {"stage": stage})},
                "source_sha256": {"env_wrapper.py": "wrapper", "damage.py": "damage",
                                  "core/vendor/car_racing.py": "physics",
                                  ("oracle/oracle_controller.py" if baseline else "oracle/v2_controller.py"): teacher_source},
                "packages": {"numpy": "1.26.0", "gymnasium": "0.29.1",
                             "opencv-python": "4.8.1", "box2d-py": "2.3.5",
                             **({"unrelated-installed-tool": "1"} if baseline else {})},
                "python": "3.11", "platform": "linux", "fps": 50,
                "sdl": {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"},
                "render_mode": "rgb_array", "domain_randomize": False}

    def fixture(self, directory, seed=1, finished=True, baseline=False, lap=1000,
                stage="braking", teacher_source="teacher"):
        directory.mkdir(exist_ok=True)
        (directory / "metadata.json").write_text(json.dumps(self.provenance(baseline, stage, teacher_source)))
        name = f"track1_seed{seed}" + ("_repeat1" if baseline else "")
        metadata = {"track_points": [[0, 0, 0, 0], [0, 0, 100, 0],
                                     [0, 0, 100, 100], [0, 0, 0, 100]], "obstacles": [],
                    "track_id": 1, "geometry_seed": seed, "frame_skip": 4, "warmup": 50,
                    "start_t": 1.02, **({"repeat": 1} if baseline else {"stage": stage})}
        summary = {"episode": name, "track_id": 1, "geometry_seed": seed,
                   **({"repeat": 1} if baseline else {"stage": stage}),
                   "steps": 1, "finished": finished, "lap_time_ms": lap if finished else None,
                   "straight_max_speed": 3,
                   "damage": 0 if finished else .2, "reason": "finished" if finished else "damage"}
        trace = {"step": 1, "pre_state": {"position": [50, 0], "speed": 19},
                 "post_state": {"position": [52, 0], "speed": 20}, "action": [.4, 0, .1],
                 "info": {"collision": not finished}, "diagnostics": {"limiting_curvature": .5}}
        for suffix, content in ((".summary.json", summary), (".metadata.json", metadata), (".jsonl", trace)):
            (directory / f"{name}{suffix}").write_text(json.dumps(content) + "\n")
        return summary, metadata

    def test_local_straight_and_geometric_brake_onset(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.fixture(directory)
            result = report([directory])
        metrics = result["episodes"][0]
        self.assertEqual(metrics["straight_max_speed"], 20)
        self.assertEqual(metrics["local_centerline_straight_max_speed"], 20)
        self.assertEqual(metrics["planner_limited_straight_max_speed"], 3)
        self.assertEqual(result["aggregate"]["planner_limited_straight_max_speed"], 3)
        self.assertEqual(metrics["steering_saturated_actions"], 1)
        self.assertEqual(len(metrics["brake_onsets"]), 1)
        self.assertAlmostEqual(metrics["brake_onsets"][0]["distance_to_apex_m"], 50)
        self.assertTrue(all(c["apex_sample"] is None for c in metrics["corners"]))

    def test_corner_matching_two_meter_limit_and_circular_group(self):
        angles = np.linspace(0, 2 * np.pi, 160, endpoint=False)
        points = np.column_stack((30 * np.cos(angles), 30 * np.sin(angles)))
        path = TrackPath(points)
        self.assertEqual(len(corners(path)), 1)
        # Square corners provide distinct landmarks, unlike the all-turn circle.
        metadata = {"track_points": [[0, 0, 0, 0], [0, 0, 100, 0], [0, 0, 100, 100], [0, 0, 0, 100]]}
        trace = [{"step": i, "pre_state": {"position": p, "speed": v},
                  "post_state": {"position": p, "speed": v}, "action": [0, 0, 0], "info": {}}
                 for i, (p, v) in enumerate((([98, 0], 12), ([100, 3], 50)), 1)]
        metrics = driving_metrics(metadata, trace)
        turn = next(c for c in metrics["corners"] if c["apex_arc_m"] == 100)
        self.assertEqual(turn["apex_sample"]["speed"], 12)
        self.assertEqual(turn["apex_sample"]["arc_error_m"], 2)
        metrics = driving_metrics(metadata, trace[1:])
        turn = next(c for c in metrics["corners"] if c["apex_arc_m"] == 100)
        self.assertIsNone(turn["apex_sample"])

    def test_aggregate_failures_repeats_and_missing_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, repeat = root / "first", root / "repeat"
            self.fixture(first)
            self.fixture(first, seed=2, finished=False)
            self.fixture(repeat)
            (repeat / "track1_seed2.jsonl").write_text("{unfinished")
            result = report([first, repeat])
            aggregate = result["aggregate"]
            self.assertEqual(aggregate["complete_episodes"], 3)
            self.assertEqual(aggregate["distinct_roads"], 2)
            self.assertEqual(aggregate["finished_episodes"], 2)
            self.assertEqual(aggregate["finished_roads"], 1)
            self.assertEqual(aggregate["damaged_episodes"], 1)
            self.assertEqual(aggregate["collision_positive_actions"], 1)
            self.assertEqual(aggregate["failure_reasons"], {"damage": 1})
            self.assertEqual(aggregate["success_mean_lap_ms"], 1000)
            self.assertEqual(aggregate["incomplete_episodes"], 1)
            self.assertEqual(aggregate["missing_planned_episodes"], 2)
            (repeat / "track1_seed1.jsonl").write_text("")
            result = report([repeat])
            self.assertEqual(result["aggregate"]["complete_episodes"], 0)
            self.assertEqual(result["aggregate"]["incomplete_episodes"], 2)
            self.assertIn("trace_steps", result["artifacts"][0]["incomplete"][0]["missing"])
            with self.assertRaises(ValueError):
                report([first, first])

    def test_success_only_matched_geometry_and_obstacles(self):
        metadata = {"track_points": [[0, 0, 0, 0]], "obstacles": [],
                    "frame_skip": 4, "warmup": 50, "start_t": 1.02,
                    "run_provenance": self.provenance()}
        entry = {"track_id": 1, "geometry_seed": 1, "stage": "speed", "finished": True, "lap_time_ms": 800}
        current = [(entry, metadata), (dict(entry, lap_time_ms=1000), metadata),
                   (dict(entry, finished=False, lap_time_ms=None), metadata)]
        baseline = [(dict(entry, lap_time_ms=1200), metadata), (dict(entry, lap_time_ms=1400), metadata)]
        result = matched_deltas(current, baseline)
        self.assertEqual(result["successful_road_stage_pairs"], 1)
        self.assertEqual(result["mean_delta_ms"], -400)
        self.assertEqual(result["pairs"][0]["v2_successful_episodes"], 2)
        for changed in (dict(metadata, obstacles=[{"position": [1, 2]}]),
                        dict(metadata, track_points=[[0, 0, 1, 0]])):
            result = matched_deltas(current, [(entry, changed)])
            self.assertEqual(result["successful_road_stage_pairs"], 0)
            self.assertEqual(result["excluded"][0]["reason"], "geometry_or_obstacles_mismatch")
        result = matched_deltas(current, [(dict(entry, finished=False), metadata)])
        self.assertEqual(result["excluded"][0]["reason"], "no_successful_pair")
        provenance = self.provenance(baseline=True, teacher_source="intentional-v1-source")
        legacy = dict(metadata, run_provenance=provenance)
        self.assertEqual(matched_deltas(current, [(entry, legacy)])["successful_road_stage_pairs"], 1)
        for field, value in (("fps", 60), ("domain_randomize", True), ("python", "3.12"),
                             ("packages", dict(provenance["packages"], numpy="2")),
                             ("source_sha256", dict(provenance["source_sha256"], **{"env_wrapper.py": "changed"}))):
            changed = dict(legacy, run_provenance=dict(provenance, **{field: value}))
            result = matched_deltas(current, [(entry, changed)])
            self.assertEqual(result["excluded"][0]["reason"], "environment_or_execution_conditions_mismatch")
        result = matched_deltas(current, [(entry, dict(legacy, frame_skip=8))])
        self.assertEqual(result["excluded"][0]["reason"], "environment_or_execution_conditions_mismatch")
        missing = dict(metadata)
        missing.pop("run_provenance")
        result = matched_deltas(current, [(entry, missing)])
        self.assertEqual(result["excluded"][0]["reason"], "unverifiable_conditions")
        self.assertIn("packages.numpy", result["excluded"][0]["missing_fields"])

    def test_expected_grid_and_all_identity_fields_before_counting(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for label, key, value, suffix in (
                    ("summary_name", "episode", "track1_seed2", ".summary.json"),
                    ("summary_track", "track_id", 2, ".summary.json"),
                    ("summary_seed", "geometry_seed", 2, ".summary.json"),
                    ("summary_stage", "stage", "pace", ".summary.json"),
                    ("metadata_track", "track_id", 2, ".metadata.json"),
                    ("metadata_seed", "geometry_seed", 2, ".metadata.json"),
                    ("metadata_stage", "stage", "pace", ".metadata.json")):
                directory = root / label
                self.fixture(directory)
                path = directory / f"track1_seed1{suffix}"
                content = json.loads(path.read_text())
                content[key] = value
                path.write_text(json.dumps(content))
                with self.subTest(label=label), self.assertRaisesRegex(ValueError, "identity mismatch"):
                    report([directory])
            directory = root / "unexpected"
            self.fixture(directory, seed=4)
            with self.assertRaisesRegex(ValueError, "Unexpected complete"):
                report([directory])
            (directory / "track1_seed4.jsonl").write_text("{unfinished")
            result = report([directory])
            self.assertEqual(result["aggregate"]["complete_episodes"], 0)
            self.assertIn("trace_json", result["artifacts"][0]["incomplete"][0]["missing"])
            (directory / "track1_seed4.summary.json").unlink()
            result = report([directory])
            self.assertEqual(result["aggregate"]["complete_episodes"], 0)
            self.assertEqual(result["artifacts"][0]["unexpected_episodes"], ["track1_seed4"])
            self.assertEqual(result["aggregate"]["incomplete_episodes"], 1)

    def test_mixed_sources_remain_visible_with_stage_aggregates(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root / "first", stage="pace", teacher_source="first-source")
            self.fixture(root / "repeat", stage="pace", teacher_source="final-source")
            self.fixture(root / "speed", stage="speed", teacher_source="final-source")
            result = report([root / "first", root / "repeat", root / "speed"])
            self.assertEqual(result["aggregate"]["complete_episodes"], 3)
            self.assertEqual(result["per_stage"]["pace"]["complete_episodes"], 2)
            self.assertEqual(result["per_stage"]["speed"]["complete_episodes"], 1)
            self.assertEqual(result["source_group_count"], 2)
            self.assertEqual(len(result["execution_groups"]), 3)
            self.assertTrue(any("Mixed source groups" in w for w in result["warnings"]))
            self.assertEqual(result["artifacts"][0]["provenance"]["source_sha256"]["oracle/v2_controller.py"],
                             "first-source")
            self.assertEqual(result["unverifiable_episodes"], [])

    def test_cli_baseline_and_json_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root / "v2", lap=800)
            self.fixture(root / "v1", baseline=True, lap=1200)
            output = root / "report.json"
            with contextlib.redirect_stdout(io.StringIO()):
                main([str(root / "v2"), "--baseline", str(root / "v1"), "--output", str(output)])
            result = json.loads(output.read_text())
            self.assertEqual(result["matched_v1_v2"]["mean_delta_ms"], -400)
            self.assertIn("definitions", result)

    def test_low_gain_braking_is_visible(self):
        metadata = {"track_points": [[0, 0, 0, 0], [0, 0, 100, 0],
                                      [0, 0, 100, 100], [0, 0, 0, 100]]}
        trace = [{"step": 1, "pre_state": {"position": [50, 0], "speed": 20},
                  "post_state": {"position": [52, 0], "speed": 20},
                  "action": [0, 0, .003], "info": {},
                  "diagnostics": {"limiting_distance": 22}}]
        result = driving_metrics(metadata, trace)
        self.assertEqual(len(result["brake_onsets"]), 1)
        self.assertEqual(result["brake_onsets"][0]["planner_limiting_distance"], 22)


if __name__ == "__main__":
    unittest.main()
