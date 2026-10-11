"""Keep nonzero-damage reuse eligible while rejecting changed policy or budget."""
import copy
import unittest

from retry.cap_rescue_validation_probe import admit


class FrozenRescueAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.plan = {'stage': 100, 'cases': [{'id': 'candidate', 'coefficient': 7}],
                     'global_cap': 40, 'max_actions': 2000, 'native_horizon_raw_ticks': 8200,
                     'stage_budgets': {'candidate': 2000}, 'candidate': {'archive_sha256': 'frozen'},
                     'B_operating_cap': 650000, 'final_reserved_actions': 84000,
                     'prior_cumulative': 561417, 'research_remaining_before': 4583,
                     'historical_baseline': {'official_lap_ms': 69820, 'damage': .2},
                     'independent_of_stage99_results': True}
        self.budget = {'B_operating_cap': 650000, 'final_reserved_actions': 84000,
                       'actual_cumulative_wrapper_actions': 561417, 'research_remaining': 4583}
        self.reuse = {'status': 'PASS', 'cached_baseline_reproduction_pass': True,
                      'baseline_lap_ms': 69820, 'baseline_damage': .2,
                      'baseline_new_native_episodes': 0}
        self.frozen = {'private_artifact_hashes': {'candidate40.zip': 'frozen'}}

    def test_verified_nonzero_damage_reference_is_eligible(self):
        self.assertEqual(admit(self.plan, self.budget, self.reuse, self.frozen)['status'], 'PASS')

    def test_changed_combination_is_not_silently_admitted(self):
        changed = copy.deepcopy(self.plan); changed['cases'][0]['coefficient'] = 14
        with self.assertRaises(AssertionError):
            admit(changed, self.budget, self.reuse, self.frozen)

    def test_missing_reproduction_stops_admission(self):
        self.reuse['cached_baseline_reproduction_pass'] = False
        with self.assertRaises(AssertionError):
            admit(self.plan, self.budget, self.reuse, self.frozen)

    def test_reserve_cannot_be_reassigned_to_research(self):
        self.budget['research_remaining'] += 1; self.budget['final_reserved_actions'] -= 1
        with self.assertRaises(AssertionError):
            admit(self.plan, self.budget, self.reuse, self.frozen)


if __name__ == '__main__':
    unittest.main()
