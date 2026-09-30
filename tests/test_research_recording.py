import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

from oracle.catalog import catalog
from oracle.recording import encode, execution_fingerprint, snapshot_sources


class RecordingTests(unittest.TestCase):
    def test_helpers_do_not_bootstrap_environment(self):
        subprocess.run([sys.executable, "-c",
                        "import sys, os; before=dict(os.environ); import oracle.recording; "
                        "assert 'env_wrapper' not in sys.modules; "
                        "assert 'oracle.oracle_runner' not in sys.modules; "
                        "assert dict(os.environ)==before"], check=True)

    def test_serialization_and_recoverable_snapshot(self):
        self.assertEqual(json.loads(encode({"array": np.array([1]), "path": Path("a")})),
                         {"array": [1], "path": "a"})
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            fingerprint = execution_fingerprint()
            snapshot = snapshot_sources(output, fingerprint)
            self.assertEqual((output / snapshot / "oracle/recording.py").read_bytes(),
                             Path("oracle/recording.py").read_bytes())
            self.assertEqual(snapshot_sources(output, fingerprint), snapshot)

    def test_catalog_reads_summaries_and_preserves_decisions(self):
        with tempfile.TemporaryDirectory() as temporary:
            runs = Path(temporary)
            directory = runs / "example"
            directory.mkdir()
            (directory / "summary.json").write_text(json.dumps({"episodes": [
                {"track_id": 1, "geometry_seed": 2, "finished": False}]}))
            records = catalog(runs, [{"id": "example", "decision": "rejected", "note": "retain failure"}])
            self.assertEqual(records[0]["decision"], "rejected")
            self.assertEqual(records[0]["episodes"], 1)
            self.assertEqual(records[0]["finishes"], 0)
            self.assertEqual(records[0]["note"], "retain failure")
            partial = runs / "partial"
            partial.mkdir()
            (partial / "track1_seed3.summary.json").write_text(json.dumps(
                {"track_id": 1, "geometry_seed": 3, "finished": True}))
            indexed = {record["id"]: record for record in catalog(runs)}
            self.assertEqual(indexed["partial"]["episodes"], 1)
            self.assertEqual(indexed["partial"]["status"], "partial")

    def test_offline_diagnosis_is_not_an_episode_evaluation(self):
        with tempfile.TemporaryDirectory() as temporary:
            runs = Path(temporary)
            directory = runs / "bc_offline_fit"
            directory.mkdir()
            (directory / "summary.json").write_text(json.dumps({
                "kind": "bc_offline_diagnosis", "models": [{"checkpoint": "unused.pt"}],
                "roads": {"train": ["train.npz"], "val": ["val.npz"]}}))
            record, = catalog(runs)
            self.assertEqual(record["kind"], "bc_offline_diagnosis")
            self.assertEqual(record["models"], 1)
            self.assertEqual(record["roads"], {"train": 1, "val": 1})
            self.assertNotIn("finishes", record)

    def test_prefix_evaluation_is_explicitly_assisted_in_catalog(self):
        with tempfile.TemporaryDirectory() as temporary:
            runs = Path(temporary)
            directory = runs / "bc_closed_prefix"
            directory.mkdir()
            (directory / "summary.json").write_text(json.dumps({
                "oracle_prefix_steps": 16, "diagnostic_only": True,
                "results": [{"track_id": 1, "geometry_seed": 31,
                             "student": {"finished": False}, "reference": {"finished": True}}]}))
            record, = catalog(runs)
            self.assertTrue(record["diagnostic_only"])
            self.assertEqual(record["decision"], "bc_prefix_diagnosis")
            self.assertEqual(record["conditions"]["oracle_prefix_steps"], 16)
            self.assertEqual(record["finishes"], 0)
            self.assertEqual(record["oracle_finishes"], 1)


if __name__ == "__main__":
    unittest.main()
