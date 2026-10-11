"""Protect completion-first adoption and censoring behavior without simulation."""
import unittest

from retry.completion_first_aggregate import summarize
from retry.frozen_paired_evaluation import performance_verdict


def endpoint(completed=True, lap=1000, censored=False, damage=0):
    return dict(completed=completed, terminal_observed=not censored, censored=censored,
                lap_ms=lap if completed else None, unique_tiles=100 if completed else 30,
                total_tiles=100, damage=damage, retire_reason=None if completed else 'off_track')


class CompletionFirstTests(unittest.TestCase):
    def classify(self, pairs):
        data = [{'case': str(i), 'baseline': b, 'candidate': c} for i, (b, c) in enumerate(pairs)]
        return performance_verdict(summarize(data, [row['case'] for row in data]))

    def test_completion_loss_beats_lap_gain(self):
        self.assertEqual(self.classify([(endpoint(), endpoint(False)), (endpoint(), endpoint(lap=1))]),
                         'KEEP_CHAMPION_COMPLETION_LOSS')

    def test_loss_and_new_completion_do_not_cancel(self):
        self.assertEqual(self.classify([(endpoint(), endpoint(False)), (endpoint(False), endpoint())]),
                         'KEEP_CHAMPION_COMPLETION_LOSS')

    def test_new_completion_precedes_common_lap(self):
        self.assertEqual(self.classify([(endpoint(False), endpoint()), (endpoint(), endpoint(lap=2000))]),
                         'COMPARISON_PASS_COMPLETION_GAIN')

    def test_small_gain_has_no_percent_cutoff_and_damage_is_separate(self):
        self.assertEqual(self.classify([(endpoint(), endpoint(lap=999, damage=.8))] * 2),
                         'COMPARISON_PASS_PAIRED_LAP_GAIN')

    def test_censor_is_inconclusive_not_dnf(self):
        self.assertEqual(self.classify([(endpoint(), endpoint(False, censored=True))]),
                         'KEEP_CHAMPION_INCONCLUSIVE_COHORT')

    def test_mixed_direction_does_not_promote(self):
        self.assertEqual(self.classify([(endpoint(lap=1000), endpoint(lap=1010)),
                                       (endpoint(lap=10000), endpoint(lap=9980))]),
                         'KEEP_CHAMPION_MIXED_OR_NO_LAP_GAIN')

    def test_missing_pair_does_not_promote(self):
        self.assertEqual(self.classify([(endpoint(), None)]), 'KEEP_CHAMPION_INCONCLUSIVE_COHORT')


if __name__ == '__main__':
    unittest.main()
