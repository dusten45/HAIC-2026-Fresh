"""Outcome-boundary regressions using synthetic records only."""

import unittest
from retry.outcomes import pair_category, race_outcome


def record(steps, *, completed=False, terminal=False, horizon=2000,
           resource=False, stop=None):
    return {"completed": completed, "terminal_observed": terminal,
            **race_outcome(completed=completed, physical_terminal=terminal,
                charged_steps=steps, planned_horizon=horizon,
                resource_stopped=resource, stop_reason=stop)}


class OutcomeTests(unittest.TestCase):
    def test_normal_horizon_dnf_counts_as_lost_completion(self):
        old = record(700, completed=True, terminal=True)
        new = record(2000)
        self.assertEqual(new["evaluation_outcome"], "dnf")
        self.assertFalse(new["terminal_observed"])
        self.assertFalse(new["censored"])
        self.assertEqual(pair_category(old, new), "lost_completion")
        self.assertEqual(pair_category(new, new), "common_failure")

    def test_resource_cutoff_before_horizon_has_no_completion_verdict(self):
        prefix = record(1999, resource=True, stop="Wall budget exhausted")
        self.assertEqual(prefix["evaluation_outcome"], "censored")
        self.assertEqual(pair_category(record(700, completed=True, terminal=True), prefix), "censored")
        self.assertEqual(record(2000, resource=True)["evaluation_outcome"], "dnf")

    def test_gate_or_short_diagnostic_is_indeterminate(self):
        for prefix in (record(500, stop="paired_gate_interrupted"), record(120, horizon=120)):
            self.assertFalse(prefix["censored"])
            self.assertTrue(prefix["indeterminate"])
            self.assertEqual(pair_category(prefix, prefix), "indeterminate")

    def test_actual_retirement_and_completion_override_interruptions(self):
        self.assertEqual(record(500, terminal=True, resource=True)["evaluation_outcome"], "dnf")
        self.assertEqual(record(2000, completed=True)["evaluation_outcome"], "completed")
        legacy = {"completed": False, "terminal_observed": True, "censored": False}
        self.assertEqual(pair_category(legacy, legacy), "common_failure")


if __name__ == "__main__":
    unittest.main()
