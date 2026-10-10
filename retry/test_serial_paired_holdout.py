"""Pure decision checks, without simulator or policy execution."""
import unittest

from retry.serial_paired_holdout import completion_loss, promotion_review_verdict


class DecisionTests(unittest.TestCase):
    def test_completion_loss_requires_two_valid_endpoints(self):
        baseline = dict(terminal_observed=True, censored=False, completed=True)
        candidate = dict(terminal_observed=True, censored=False, completed=False)
        self.assertTrue(completion_loss(baseline, candidate))
        self.assertFalse(completion_loss(baseline, {**candidate, 'censored':True}))
        self.assertFalse(completion_loss(baseline, {}))
        self.assertFalse(completion_loss({**baseline, 'completed':False}, candidate))

    def test_loss_stops_even_when_later_cases_are_unexecuted(self):
        self.assertEqual(promotion_review_verdict({
            'counts':{'lost_completion':1}, 'cohort_complete':False}),
            'RETIRE_COMPLETION_LOSS_STOP')

    def test_median_and_mean_ratio_are_both_required(self):
        summary = {'counts':{'lost_completion':0, 'new_completion':0, 'common_completed':2},
                   'cohort_complete':True, 'common_completion_median_lap_delta_ms':-1,
                   'common_completion_mean_lap_ratio':1.001}
        self.assertEqual(promotion_review_verdict(summary), 'MIXED_OR_NO_LAP_GAIN')
        summary['common_completion_mean_lap_ratio'] = .999
        self.assertEqual(promotion_review_verdict(summary), 'KEEP_FOR_PROMOTION_REVIEW')
        summary['common_completion_median_lap_delta_ms'] = 0
        self.assertEqual(promotion_review_verdict(summary), 'MIXED_OR_NO_LAP_GAIN')

    def test_invalid_and_small_cohorts_do_not_pass(self):
        summary = {'counts':{'lost_completion':0, 'new_completion':0, 'common_completed':1},
                   'cohort_complete':False}
        self.assertEqual(promotion_review_verdict(summary), 'INCONCLUSIVE_INCOMPLETE_OR_INVALID_COHORT')
        summary['cohort_complete'] = True
        self.assertEqual(promotion_review_verdict(summary), 'INSUFFICIENT_COMMON_COMPLETIONS')


if __name__ == '__main__':
    unittest.main()
