import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from oracle.oracle_report import report


class TestOracleReport(unittest.TestCase):
    def test_incomplete_run_is_not_silently_treated_as_complete(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "metadata.json").write_text(json.dumps({"args": {
                "track_ids": [1], "seeds": [1, 2], "repeats": 2}}))
            (directory / "track1_seed1_repeat1.jsonl").write_text("{}\n")
            output = io.StringIO()
            with contextlib.redirect_stdout(output), self.assertRaises(ValueError):
                report([directory])
            self.assertIn("0/4 planned", output.getvalue())
            self.assertIn("1 incomplete traces excluded", output.getvalue())
            self.assertIn("3 unstarted/missing", output.getvalue())

    def test_duplicate_directories_rejected(self):
        with self.assertRaises(ValueError):
            report([Path("runs/example"), Path("runs/example")])

    def test_nonempty_partial_and_repeated_directory_aggregation(self):
        with tempfile.TemporaryDirectory() as temporary:
            directories = [Path(temporary) / name for name in ("partial", "repeat")]
            episode = "track1_seed1_repeat1"
            summary = {"episode": episode, "track_id": 1, "geometry_seed": 1,
                       "finished": True, "steps": 1, "progress": 1, "damage": 0,
                       "max_abs_center_error": 0, "first_collision": None,
                       "first_road_departure": None, "finish_time_s": 2, "start_t": 1}
            trace = [{"step": 0}, {"post_state": {"speed": 12}, "action": [0, 0, 0],
                                   "info": {"collision": False}, "diagnostics": {}}]
            for index, directory in enumerate(directories):
                directory.mkdir()
                (directory / "metadata.json").write_text(json.dumps({
                    "args": {"track_ids": [1], "seeds": [1, 2] if index == 0 else [1],
                             "repeats": 1}, "source_sha256": {"controller": "same"}}))
                (directory / f"{episode}.summary.json").write_text(json.dumps(summary))
                (directory / f"{episode}.metadata.json").write_text(json.dumps({
                    "track_points": [[0, 0], [1, 0]], "obstacles": []}))
                (directory / f"{episode}.jsonl").write_text(
                    "\n".join(json.dumps(record) for record in trace))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                report(directories)
            self.assertIn("1/2 planned", output.getvalue())
            self.assertIn("1 unstarted/missing", output.getvalue())
            self.assertIn("finishes 2/2 episodes", output.getvalue())
            self.assertIn("Exact repeated trace hashes: 1/1", output.getvalue())
            self.assertIn("Execution fingerprints (sources/settings/packages): 1", output.getvalue())


if __name__ == "__main__":
    unittest.main()
