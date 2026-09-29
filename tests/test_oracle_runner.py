import dataclasses
import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from oracle.oracle_runner import encode, main, observation_summary, vehicle_state


class TestOracleRunner(unittest.TestCase):
    def test_numpy_and_dataclass_serialization(self):
        @dataclasses.dataclass
        class Record:
            value: np.float32
        result = json.loads(encode({"record": Record(np.float32(0.5)),
                                    "array": np.array([1, 2]), "flag": np.bool_(True)}))
        self.assertEqual(result, {"record": {"value": 0.5}, "array": [1, 2], "flag": True})
        with self.assertRaises(ValueError):
            encode({"invalid": float("nan")})

    def test_observation_hash_and_summary(self):
        array = np.zeros((4, 84, 84), dtype=np.float32)
        before = observation_summary(array)
        self.assertEqual(before["shape"], [4, 84, 84])
        self.assertEqual(before["dtype"], "float32")
        self.assertEqual(before["min"], 0)
        self.assertEqual(before["sha256"], observation_summary(array.copy())["sha256"])
        array[0, 0, 0] = 1
        self.assertNotEqual(before["sha256"], observation_summary(array)["sha256"])

    def test_projection_and_raw_frames(self):
        hull = SimpleNamespace(position=(1, 5), angle=0, linearVelocity=(0, 2), angularVelocity=0)
        car = SimpleNamespace(hull=hull, wheels=[SimpleNamespace(joint=SimpleNamespace(angle=0.2), tiles={1})] * 4)
        base = SimpleNamespace(car=car, t=1.02, tile_visited_count=2, track=[(0, 0, 0, 0), (0, 0, 0, 10),
                                                     (0, 0, -10, 10), (0, 0, -10, 0)])
        state = vehicle_state(base)
        self.assertEqual(state["raw_frame"], 51)
        self.assertEqual(state["speed"], 2)
        self.assertEqual(state["forward_velocity"], 2)
        self.assertEqual(state["right_velocity"], 0)
        self.assertEqual(state["wheels_on_road"], 4)
        self.assertEqual(state["track"]["center_error"], -1)
        self.assertEqual(state["track"]["fraction"], 0.5)
        np.testing.assert_array_equal(state["track"]["projection"], [0, 5])

    def test_refuses_existing_output_and_missing_parent(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main(["--output", temporary])
            with self.assertRaises(SystemExit):
                main(["--output", str(Path(temporary) / "missing" / "run")])

    def test_external_limits_do_not_fabricate_environment_truncation(self):
        for limit, extra, expected_steps in (("runner_max_steps", [], 1),
                                            ("runner_timeout", ["--timeout-seconds", "1e-12"], 0)):
            with self.subTest(limit=limit), tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary) / "run"
                with contextlib.redirect_stdout(io.StringIO()):
                    main(["--output", str(output), "--track-ids", "5", "--seeds", "10",
                          "--max-steps", "1", *extra])
                summary = json.loads((output / "summary.json").read_text())
                episode = summary["episodes"][0]
                self.assertEqual(episode["reason"], limit)
                self.assertEqual(episode["steps"], expected_steps)
                self.assertFalse(episode["terminated"])
                self.assertFalse(episode["truncated"])
                self.assertFalse(episode["finished"])
                self.assertEqual(summary["episode_count"], 1)
                self.assertEqual(summary["road_count"], 1)
                trace = [json.loads(line) for line in (output / "track5_seed10_repeat1.jsonl").read_text().splitlines()]
                self.assertEqual(len(trace), expected_steps + 1)
                self.assertEqual(trace[0]["state"]["raw_frame"], 51)
                if expected_steps:
                    self.assertEqual(trace[1]["pre_state"], trace[0]["state"])
                    self.assertEqual(trace[1]["post_state"]["raw_frame"], 55)
                    self.assertIs(trace[1]["info"]["finished"], False)

    def test_default_grid_is_fifty_configurations(self):
        def episode(args, output, track_id, seed, repeat):
            return {"track_id": track_id, "geometry_seed": seed, "finished": False}
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "run"
            with patch("oracle.oracle_runner.run_episode", side_effect=episode) as rollout:
                main(["--output", str(output)])
            summary = json.loads((output / "summary.json").read_text())
            self.assertEqual(rollout.call_count, 50)
            self.assertEqual(summary["road_count"], 50)
            self.assertEqual({(e["track_id"], e["geometry_seed"]) for e in summary["episodes"]},
                             {(t, s) for t in range(1, 6) for s in range(1, 11)})


if __name__ == "__main__":
    unittest.main()
