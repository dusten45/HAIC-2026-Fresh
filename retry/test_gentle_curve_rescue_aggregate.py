"""Synthetic saved contracts only; no policies, environments or models."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from retry.gentle_curve_rescue_aggregate import analyze


def write_fixture(root, candidate_status='COMPLETE'):
    write = lambda name,data:(root/name).write_text(json.dumps(data))
    write('plan.json', {'cases':[{'id':'a','coefficient':7,'expected_baseline_lap_ms':8000,'expected_baseline_damage':.2},
                                {'id':'b','coefficient':14,'expected_baseline_lap_ms':8000,'expected_baseline_damage':.2}],
                        'max_actions':4000,'stage_budgets':{'a':2000,'b':2000}})
    results=[{'id':'a','coefficient':7,'status':'COMPLETE','completed':True,
              'official_lap_ms':8000,'damage':.2,'charged_wrapper_actions':100},
             {'id':'b','coefficient':14,'status':candidate_status,'completed':candidate_status=='COMPLETE',
              'official_lap_ms':7000 if candidate_status=='COMPLETE' else None,
              'damage':.2,'charged_wrapper_actions':100}]
    qualification={'status':'PASS','damage':.2,'official_lap_ms':8000,
                   'frames_exact':True,'actions_exact':True,'masks_exact':True}
    write('cohort-results.json',{'results':results,'stop_reason':None,'baseline_qualification':qualification})
    write('budget.json',{'actions':200,'stages':{'a':100,'b':100}})
    write('baseline-reproduction.json',qualification)


class RescueAggregateTests(unittest.TestCase):
    def test_two_case_contract_preserves_nonzero_damage_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);write_fixture(root)
            with patch('retry.gentle_curve_rescue_aggregate._verify_case',return_value=({'verification_pass':True},[])):
                out=analyze(root)
            self.assertTrue(out['all_required_evidence_verified'])
            self.assertTrue(out['pair']['both_completed_verified'])
            self.assertEqual(out['pair']['common_completed_lap_delta_ms'],-1000)
            self.assertEqual(out['pair']['baseline_damage'],.2)
            self.assertEqual(out['pair']['damage_delta'],0.)
            cohort=json.loads((root/'cohort-results.json').read_text())
            cohort['results'][0]['charged_wrapper_actions']=2001
            (root/'cohort-results.json').write_text(json.dumps(cohort))
            (root/'budget.json').write_text(json.dumps({'actions':2101,'stages':{'a':2001,'b':100}}))
            with patch('retry.gentle_curve_rescue_aggregate._verify_case',return_value=({'verification_pass':True},[])):
                overspent=analyze(root)
            self.assertFalse(overspent['budget_ledger_pass'])
            self.assertIsNone(overspent['pair']['common_completed_lap_delta_ms'])
            qualification=json.loads((root/'baseline-reproduction.json').read_text());qualification['damage']=0.
            (root/'baseline-reproduction.json').write_text(json.dumps(qualification))
            with patch('retry.gentle_curve_rescue_aggregate._verify_case',return_value=({'verification_pass':True},[])):
                mismatched=analyze(root)
            self.assertFalse(mismatched['all_required_evidence_verified'])
            self.assertIsNone(mismatched['pair']['common_completed_lap_delta_ms'])
            plan=json.loads((root/'plan.json').read_text());plan['cases'].append({'id':'c','coefficient':7})
            (root/'plan.json').write_text(json.dumps(plan))
            with self.assertRaises(ValueError):analyze(root)

    def test_missing_evidence_retains_censor_without_claiming_dnf_or_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);write_fixture(root,'RESOURCE_CENSORED')
            out=analyze(root)
            self.assertFalse(out['all_required_evidence_verified'])
            self.assertEqual(out['reported_status_counts']['RESOURCE_CENSORED'],1)
            self.assertEqual(out['reported_status_counts']['DNF'],0)
            self.assertTrue(out['pair']['candidate_resource_censored'])
            self.assertFalse(out['pair']['native_completion_lost_verified'])
            self.assertIsNone(out['pair']['common_completed_lap_delta_ms'])
            self.assertEqual(len(out['verification_errors']),2)
            self.assertEqual(out['new_wrapper_actions'],200)


if __name__ == '__main__':
    unittest.main()
