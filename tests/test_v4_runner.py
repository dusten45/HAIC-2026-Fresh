import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

from oracle.v4_runner import ROADS, main, run


class TestV4Runner(unittest.TestCase):
    def test_default_roads_repeats_nonfinishes_and_source_snapshots(self):
        def episode(output, track_id, seed, stage, repeat):
            return {"track_id": track_id, "geometry_seed": seed, "repeat": repeat,
                    "finished": track_id != 2, "lap_time_ms": 12000 if track_id != 2 else None,
                    "damage": int(track_id == 2), "collisions": int(track_id == 2)}

        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            output = Path(temporary) / "run"
            with patch("oracle.v4_runner.run", side_effect=episode) as rollout:
                main(["--output", str(output), "--repeats", "2"])
            self.assertEqual(ROADS, ((1, 516237), (2, 644062), (3, 1007)))
            self.assertEqual(rollout.call_args_list,
                              [call(output, t, s, "midpoint", repeat)
                              for repeat in (1, 2) for t, s in ROADS])
            summary = json.loads((output / "summary.json").read_text())
            self.assertEqual((summary["episodes"], summary["roads"], summary["finishes"]), (6, 3, 4))
            self.assertEqual((summary["damaged"], summary["collisions"]), (2, 2))
            self.assertEqual(summary["mean_lap_ms"], 12000)
            self.assertEqual(summary["median_lap_ms"], 12000)
            self.assertEqual(summary["best_lap_ms"], 12000)
            metadata = json.loads((output / "metadata.json").read_text())
            snapshot, = (output / "source_snapshot").iterdir()
            for source in ("oracle/v4_controller.py", "oracle/v4_runner.py",
                           "oracle/v3_controller.py", "oracle/v2_controller.py"):
                with self.subTest(source=source):
                    saved = (snapshot / source).read_bytes()
                    self.assertEqual(hashlib.sha256(saved).hexdigest(), metadata["source_sha256"][source])
                    self.assertEqual(saved, (Path(__file__).resolve().parent.parent / source).read_bytes())

    def test_explicit_road_stage_and_three_failed_repeats(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            output = Path(temporary) / "run"
            result = {"track_id": 2, "geometry_seed": 644062, "finished": False,
                      "damage": 1, "collisions": 5}
            with patch("oracle.v4_runner.run", return_value=result) as rollout:
                main(["--road", "2", "644062", "--stage", "profile", "--repeats", "3",
                      "--output", str(output)])
            self.assertEqual(rollout.call_args_list,
                             [call(output, 2, 644062, "profile", repeat) for repeat in (1, 2, 3)])
            summary = json.loads((output / "summary.json").read_text())
            self.assertEqual((summary["episodes"], summary["roads"], summary["finishes"]), (3, 1, 0))
            for field in ("mean_lap_ms", "median_lap_ms", "best_lap_ms"):
                self.assertIsNone(summary[field])

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stderr(io.StringIO()):
            with patch("oracle.v4_runner.run") as rollout, self.assertRaises(SystemExit):
                main(["--output", temporary])
            rollout.assert_not_called()
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_episode_timing_trace_and_optional_profile_metadata_without_simulator(self):
        for optional in (False, True):
            with self.subTest(optional=optional), tempfile.TemporaryDirectory() as temporary, \
                    contextlib.redirect_stdout(io.StringIO()):
                output = Path(temporary)
                base = SimpleNamespace(t=1.02, track=[], track_variables=SimpleNamespace(obstacles=[]),
                                       lap_complete_percent=0.95, finish_time_s=None)
                env = Mock(_stack_frames=4, max_off_track_steps=10,
                           damage=SimpleNamespace(damage=0))
                env._calculate_progress.return_value = 1.0

                def step(action):
                    base.t = base.finish_time_s = 1.10
                    return None, 1.0, True, False, {}

                env.step.side_effect = step
                controller = SimpleNamespace(path=SimpleNamespace(points=[]), config={}, arcs=[0],
                                             speed_limits=[95], speed_profile=[0], curvature=[0],
                                             act=lambda: ([0, 1, 0], {"target_speed": 10}))
                if optional:
                    controller.launch_arcs = [0, 1]
                    controller.launch_profile = [0, 2]
                    controller.profile_acceleration = [2]
                with patch("oracle.v4_runner.CarRacing", return_value=base) as raw, \
                        patch("oracle.v4_runner.TimeLimit") as limit, \
                        patch("oracle.v4_runner.CarEnvironment", return_value=env) as wrapper, \
                        patch("oracle.v4_runner.V4Controller", return_value=controller) as policy, \
                        patch("oracle.v4_runner.vehicle_state", return_value={"speed": 2}):
                    summary = run(output, 1, 516237, "feedforward", 1)
                raw.assert_called_once_with(continuous=True, render_mode="rgb_array")
                limit.assert_called_once_with(base, max_episode_steps=8200)
                wrapper.assert_called_once_with(limit.return_value, skip_frames=4, no_operation=50)
                env.reset.assert_called_once_with(seed=516237, options={"track_id": 1})
                policy.assert_called_once_with(base, stage="feedforward")
                env.close.assert_called_once_with()
                self.assertEqual(summary["lap_time_ms"], 80)
                self.assertTrue(summary["finished"])
                metadata = json.loads((output / "track1_seed516237_repeat1.metadata.json").read_text())
                self.assertEqual(metadata["start_t"], 1.02)
                self.assertEqual(metadata["max_steps"], 2000)
                self.assertFalse(metadata["domain_randomize"])
                for field in ("launch_arcs", "launch_profile", "profile_acceleration"):
                    self.assertEqual(field in metadata, optional)
                    if optional:
                        self.assertEqual(metadata[field], getattr(controller, field))
                trace = json.loads((output / "track1_seed516237_repeat1.jsonl").read_text())
                self.assertEqual(set(trace), {"step", "pre_state", "post_state", "action", "diagnostics",
                                             "reward", "info", "terminated", "truncated"})
                self.assertEqual(trace["action"], [0, 1, 0])
                self.assertTrue(trace["terminated"])


if __name__ == "__main__":
    unittest.main()
