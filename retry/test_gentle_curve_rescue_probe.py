"""Nonzero reference damage and one-use rescue-pair qualification; no native calls."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from retry import gentle_curve_rescue_probe as runner


class RescueContractTests(unittest.TestCase):
    def test_nonzero_reference_damage_and_full_masks_are_required_for_reproduction(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'baseline').mkdir()
            result = {'status':'COMPLETE','completed':True,'official_lap_ms':69820,
                      'damage':.2,'action_sequence_sha256':'synthetic'}
            (root/'baseline'/'result.json').write_text(json.dumps(result))
            old = root/'reference.json'; old.write_text(json.dumps(result))
            frames = np.zeros((2,84,84),np.uint8)
            masks = frames.copy()
            actions = np.zeros((1,3),np.float32)
            for prefix in ['baseline','reference']:
                np.savez(root/(prefix+'-pixels-actions.npz'),frames=frames,actions=actions)
                np.savez(root/(prefix+'-student-masks.npz'),masks=masks)
            case = {'id':'baseline','baseline_result_path':str(old),'expected_baseline_lap_ms':69820,
                    'expected_baseline_damage':.2,'baseline_pixels_actions_path':str(root/'reference-pixels-actions.npz'),
                    'baseline_masks_path':str(root/'reference-student-masks.npz')}
            self.assertEqual(runner.reproduce(root,case)['status'],'PASS')
            masks[0,0,0]=1
            np.savez(root/'baseline-student-masks.npz',masks=masks)
            with self.assertRaises(AssertionError): runner.reproduce(root,case)

    def run_pair(self, *, disqualify=False, candidate_status='DNF'):
        calls=[]
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            cases=[{'id':f'pair-{a}','condition':'rescue','coefficient':a} for a in [7,14]]
            plan={'cases':cases,'max_actions':4000,'stage_budgets':{c['id']:2000 for c in cases},
                  'source_sha256':{},'reference_sha256':{}}
            (root/'plan.json').write_text(json.dumps(plan)); (root/'plan.sha256').write_text('digest')
            (root/'preflight.json').write_text(json.dumps({'status':'PASS','plan_sha256':'digest'}))
            def execute(case,_plan,_path):
                calls.append(case['coefficient']); (root/case['id']).mkdir()
                status='COMPLETE' if case['coefficient']==7 else candidate_status
                return {**case,'status':status,'completed':status=='COMPLETE','damage':.2,
                        'charged_wrapper_actions':5,'episode_count':1},False
            def reproduce(_directory,_case):
                if disqualify: raise AssertionError('mask mismatch')
                return {'status':'PASS','damage':.2}
            with patch.object(runner.native,'sha',return_value='digest'), patch.object(runner.native,'available'), \
                 patch.object(runner,'execute',side_effect=execute), patch.object(runner,'reproduce',side_effect=reproduce), \
                 patch('sys.argv',['probe','--plan',str(root/'plan.json')]), contextlib.redirect_stdout(io.StringIO()):
                code=runner.main()
            cohort=json.loads((root/'cohort-results.json').read_text())
        return code,calls,cohort

    def test_disqualified_baseline_keeps_outcome_and_skips_candidate(self):
        code,calls,cohort=self.run_pair(disqualify=True)
        self.assertEqual((code,calls),(1,[7]))
        self.assertEqual([r['status'] for r in cohort['results']],['COMPLETE','UNEXECUTED'])
        self.assertEqual(cohort['results'][0]['damage'],.2)

    def test_candidate_native_failure_and_censor_are_retained_without_retry(self):
        for status in ['DNF','RESOURCE_CENSORED']:
            code,calls,cohort=self.run_pair(candidate_status=status)
            self.assertEqual((code,calls),(0,[7,14]))
            self.assertEqual(cohort['results'][1]['status'],status)
            self.assertIsNone(cohort['stop_reason'])


if __name__ == '__main__':
    unittest.main()
