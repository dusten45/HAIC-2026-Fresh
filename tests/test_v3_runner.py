import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from oracle.v3_runner import ROADS, main


class TestV3Runner(unittest.TestCase):
    def test_designated_roads_are_paired_not_a_cartesian_grid(self):
        def episode(output, track_id, seed, stage, repeat):
            return {"track_id": track_id, "geometry_seed": seed, "repeat": repeat,
                    "finished": track_id != 2, "lap_time_ms": 12000 if track_id != 2 else None,
                    "damage": 0, "collisions": 0}

        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            output = Path(temporary) / "run"
            with patch("oracle.v3_runner.run", side_effect=episode) as rollout:
                main(["--output", str(output), "--repeats", "2"])
            summary = json.loads((output / "summary.json").read_text())
            self.assertEqual(rollout.call_count, 6)
            self.assertEqual((summary["episodes"], summary["roads"], summary["finishes"]), (6, 3, 4))
            self.assertEqual({(e["track_id"], e["geometry_seed"]) for e in summary["results"]}, set(ROADS))
            self.assertEqual(summary["mean_lap_ms"], 12000)
            metadata = json.loads((output / "metadata.json").read_text())
            self.assertIn("oracle/v3_controller.py", metadata["source_sha256"])
            self.assertTrue((output / "source_snapshot").is_dir())

    def test_single_road_can_be_reproduced_without_extra_episodes(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            output = Path(temporary) / "run"
            result = {"track_id": 2, "geometry_seed": 644062, "finished": False,
                      "damage": 1, "collisions": 5}
            with patch("oracle.v3_runner.run", return_value=result) as rollout:
                main(["--road", "2", "644062", "--output", str(output)])
            self.assertEqual(rollout.call_count, 1)
            summary = json.loads((output / "summary.json").read_text())
            self.assertEqual(summary["finishes"], 0)
            self.assertIsNone(summary["mean_lap_ms"])

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main(["--output", temporary])


if __name__ == "__main__":
    unittest.main()
