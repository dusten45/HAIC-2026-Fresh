import json
from pathlib import Path
import unittest
from unittest.mock import patch

from bc.teacher_report import report


class TestTeacherReport(unittest.TestCase):
    def setUp(self):
        self.artifacts = {}
        for arm in ("v1", "v2", "mixed"):
            self.artifacts[f"runs/teacher_model_{arm}/history.json"] = {
                "seed": 0, "config": {"epochs": 5}, "source_sha256": {"bc/train.py": "same"},
                "train_roads": ["same_train"], "val_roads": ["same_val"],
                "best_checkpoint_sha256": arm,
                "history": [{"epoch": epoch, "train_samples": 2560, "optimizer_steps": 40,
                             "val": {"weighted_mean_mse": 1 / epoch}} for epoch in range(1, 6)]}
            for track in range(1, 6):
                self.artifacts[f"runs/teacher_closed_{arm}_t{track}/summary.json"] = {
                    "checkpoint_sha256": arm, "source_sha256": {"bc/evaluate.py": "same"},
                    "results": [{"track_id": track, "geometry_seed": seed,
                                 "reference": {"finished": True},
                                 "student": {"finished": False, "progress": .2,
                                             "damage": 0, "reason": "max_steps"}}
                                for seed in (31, 32, 33)]}

    def run_report(self):
        with patch.object(Path, "read_text", autospec=True,
                          side_effect=lambda path: json.dumps(self.artifacts[str(path)])):
            return report(Path("runs"))

    def test_zero_finish_tie_is_inconclusive_with_exact_budget(self):
        result = self.run_report()
        self.assertEqual(result["decision"], "inconclusive_finish_tie")
        for arm in result["arms"].values():
            self.assertEqual((arm["episodes"], arm["roads"], arm["reference_finishes"]), (15, 15, 15))
            self.assertEqual(sum(arm["budget"]["updates_per_epoch"]), 200)
            self.assertEqual(arm["selected_epoch"], 5)

    def test_unmatched_budget_or_duplicate_roads_refused(self):
        self.artifacts["runs/teacher_model_v2/history.json"]["seed"] = 1
        with self.assertRaisesRegex(ValueError, "different model budgets"):
            self.run_report()
        self.artifacts["runs/teacher_model_v2/history.json"]["seed"] = 0
        results = self.artifacts["runs/teacher_closed_v2_t1/summary.json"]["results"]
        results[1] = results[0]
        with self.assertRaisesRegex(ValueError, "Missing, duplicate"):
            self.run_report()

    def test_assisted_rollout_or_changed_sources_refused(self):
        summary = self.artifacts["runs/teacher_closed_mixed_t3/summary.json"]
        summary["oracle_prefix_steps"] = 10
        with self.assertRaisesRegex(ValueError, "Assisted/diagnostic"):
            self.run_report()
        summary["oracle_prefix_steps"] = 0
        summary["source_sha256"] = {"bc/evaluate.py": "different"}
        with self.assertRaisesRegex(ValueError, "Evaluation sources or conditions differ"):
            self.run_report()


if __name__ == "__main__":
    unittest.main()
