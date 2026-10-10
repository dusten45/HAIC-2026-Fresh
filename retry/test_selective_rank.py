import unittest

from retry.selective_rank import CandidateScore as S, compare_scores, selective_choice


class SelectiveRankTests(unittest.TestCase):
    def test_abstained_candidate_is_excluded_from_choice_but_kept_in_regret(self):
        predicted = [S('a', True, False, 1., 1.), S('b', True, False, 2., 1.),
                     S('c', False, False, 3., 1.)]
        chosen, _, _ = selective_choice(predicted, .1, .1)
        self.assertEqual(chosen, 'b')
        result = compare_scores(predicted, predicted, chosen, .1, .1)
        self.assertEqual(result['candidate_count'], 3)
        self.assertEqual(result['abstained_count'], 1)
        self.assertEqual(result['safe_progress_regret_against_all_candidates'], 1.)

    def test_practical_ties_do_not_create_a_useful_selection(self):
        scores = [S('a', True, False, 1., 1.), S('b', True, False, 1.05, 1.05)]
        self.assertEqual(selective_choice(scores, .1, .1)[0], None)

    def test_selected_risk_error_and_inversion_remain_visible(self):
        predictions = [S('a', True, False, 2., 1.), S('b', True, False, 1., 1.)]
        outcomes = [S('a', True, True, 2., -1.), S('b', True, False, 1., 1.)]
        result = compare_scores(predictions, outcomes, 'a', .1, .1)
        self.assertTrue(result['chosen_actual_unsafe'])
        self.assertTrue(result['pairs'][0]['inversion'])
        self.assertEqual(result['applicable_actual_unsafe_ids'], ['a'])


if __name__ == '__main__':
    unittest.main()
