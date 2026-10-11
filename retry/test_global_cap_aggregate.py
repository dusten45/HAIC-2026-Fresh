"""Native DNF and missing evidence retain their outcomes without a lap claim."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from retry.global_cap_aggregate import analyze


class OutcomeRetentionTests(unittest.TestCase):
    def prepare(self, root, status, initial=True):
        old=root/'old';old.mkdir();(old/'baseline').mkdir();(root/'candidate').mkdir()
        baseline={'status':'COMPLETE','completed':True,'official_lap_ms':59560,'damage':0,
                  'unique_tiles':271,'total_tiles':271,'charged_wrapper_actions':745}
        candidate={'status':status,'completed':False,'official_lap_ms':None,'damage':.4,
                   'unique_tiles':139,'total_tiles':271,'charged_wrapper_actions':400}
        (old/'baseline/result.json').write_text(json.dumps(baseline))
        (root/'candidate/result.json').write_text(json.dumps(candidate))
        start={'initial':{},'initial_observation_sha256':'pixels','geometry_sha256':'road','obstacles_sha256':'hazards'}
        (old/'baseline/started.json').write_text(json.dumps(start))
        if initial:(root/'candidate/started.json').write_text(json.dumps(start))
        (root/'plan.json').write_text(json.dumps({'historical_baseline':{'directory':str(old),'case_id':'baseline'},'cases':[{'id':'candidate'}]}))
        (root/'budget.json').write_text(json.dumps({'actions':400,'stages':{'candidate':400}}))
        (root/'preflight.json').write_text(json.dumps({'historical_baseline_comparable':True,'cached_baseline_reproduction_pass':True}))

    def test_native_dnf_keeps_progress_without_lap_delta(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.prepare(root,'DNF')
            with patch('retry.global_cap_aggregate.audit',return_value=({'verification_pass':True},[])):
                report=analyze(root)
            self.assertTrue(report['pair']['native_completion_lost_verified'])
            self.assertIsNone(report['pair']['common_completed_lap_delta_ms'])
            self.assertEqual(report['results'][1]['unique_tiles'],139)
            self.assertEqual(report['new_wrapper_actions'],400)

    def test_missing_evidence_retains_resource_censor(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.prepare(root,'RESOURCE_CENSORED',initial=False)
            with patch('retry.global_cap_aggregate.audit',side_effect=ValueError('missing stream')):
                report=analyze(root)
            self.assertEqual(report['results'][1]['status'],'RESOURCE_CENSORED')
            self.assertFalse(report['all_required_evidence_verified'])
            self.assertFalse(report['pair']['native_completion_lost_verified'])
            self.assertIsNone(report['pair']['common_completed_lap_delta_ms'])
            self.assertEqual(report['results'][1]['unique_tiles'],139)


if __name__=='__main__':unittest.main()
