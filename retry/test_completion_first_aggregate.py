import unittest

from retry.completion_first_aggregate import summarize


def record(completed, tiles=30, lap=1000, damage=0, terminal=True, censored=False):
    return {"completed": completed, "terminal_observed": terminal, "censored": censored,
            "lap_ms": lap if completed else None, "unique_tiles": tiles,
            "total_tiles": 100, "damage": damage,
            "retire_reason": None if completed else "off_track"}


class CompletionFirstAggregateTests(unittest.TestCase):
    def test_four_normal_categories_stable_order_and_descriptive_metrics(self):
        pairs = [
            {"case": "dnf", "baseline": record(False, 21), "candidate": record(False, 40)},
            {"case": "common", "baseline": record(True, 100, 1000, .2),
             "candidate": record(True, 100, 1200, .4)},
            {"case": "lost", "baseline": record(True, 100), "candidate": record(False, 60)},
            {"case": "new", "baseline": record(False, 80), "candidate": record(True, 100)},
        ]
        result = summarize(pairs, ["new", "lost", "common", "dnf"])
        self.assertEqual([item["case"] for item in result["case_results"]],
                         ["new", "lost", "common", "dnf"])
        self.assertEqual(result["counts"], {"new_completion": 1, "lost_completion": 1,
                                           "common_dnf": 1, "common_completed": 1})
        self.assertTrue(result["cohort_complete"])
        self.assertEqual(result["baseline_completed_count"], 2)
        self.assertEqual(result["candidate_completed_count"], 2)
        self.assertEqual(result["common_dnf_unique_tile_vectors"]["baseline"], [21])
        self.assertEqual(result["common_dnf_unique_tile_vectors"]["candidate"], [40])
        self.assertEqual(result["common_completion_median_lap_delta_ms"], 200)
        self.assertAlmostEqual(result["common_completion_mean_lap_ratio"], 1.2)
        self.assertAlmostEqual(result["common_completion_metrics"][0]["damage_delta"], .2)
        self.assertAlmostEqual(result["total_damage_diagnostic"]["sums"]["candidate"], .4)

    def test_missing_censored_and_nonterminal_are_never_failed_completions(self):
        pairs = [
            {"case": "censored", "baseline": record(True, 100),
             "candidate": record(False, 20, terminal=False, censored=True)},
            {"case": "unexecuted", "baseline": record(True, 100), "candidate": None},
            {"case": "unknown", "baseline": record(True, 100),
             "candidate": record(False, 20, terminal=False)},
        ]
        result = summarize(pairs, ["missing", "unknown", "unexecuted", "censored"])
        self.assertFalse(result["cohort_complete"])
        self.assertEqual(result["unexecuted"], ["missing", "unexecuted"])
        self.assertEqual(result["inconclusive"], ["unknown", "censored"])
        self.assertEqual(result["censored_cases"], ["censored"])
        self.assertEqual(result["comparable_pair_count"], 0)
        self.assertEqual(result["counts"]["lost_completion"], 0)
        self.assertEqual(result["counts"]["common_dnf"], 0)
        self.assertIsNone(result["common_completion_mean_lap_ratio"])
        self.assertEqual(result["total_damage_diagnostic"]["observed_record_counts"],
                         {"baseline": 3, "candidate": 2})
        for bad_pairs, expected in ((pairs + [pairs[0]], ["censored", "unexecuted", "unknown"]),
                                    (pairs, ["unknown", "unknown"]),
                                    (pairs, ["unknown"])):
            with self.assertRaises(ValueError):
                summarize(bad_pairs, expected)


if __name__ == "__main__":
    unittest.main()
