"""Mocked supervisor integration; no environment or participant execution."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from retry import gentle_curve_transfer_probe as runner


class StopContractTests(unittest.TestCase):
    def run_batch(self, outcomes, reproduction=None):
        calls = []
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cases = [{'id':f'{condition}-{coef}','condition':condition,'coefficient':coef}
                     for condition,coef in [('high',7),('high',14),('low',7),('low',14)]]
            plan = {'cases':cases,'max_actions':8000,'stage_budgets':{c['id']:2000 for c in cases},
                    'source_sha256':{},'reference_sha256':{}}
            (root/'plan.json').write_text(json.dumps(plan))
            (root/'plan.sha256').write_text('digest')
            (root/'preflight.json').write_text(json.dumps({'status':'PASS','plan_sha256':'digest'}))
            def fake_execute(case, _plan, _path):
                calls.append(case['id'])
                (root/case['id']).mkdir()
                status = outcomes.get(case['id'],'COMPLETE')
                return {**case,'status':status,'completed':status=='COMPLETE',
                        'charged_wrapper_actions':5,'error':'mock' if status=='TECHNICAL_ERROR' else None}, status=='TECHNICAL_ERROR'
            def qualify(_root, case):
                if reproduction and case['condition'] in reproduction:
                    raise AssertionError('mock baseline mismatch')
                return {'status':'PASS'}
            with patch.object(runner.native,'sha',return_value='digest'), \
                 patch.object(runner.native,'available'), \
                 patch.object(runner,'execute',side_effect=fake_execute), \
                 patch.object(runner,'reproduce',side_effect=qualify), \
                 patch('sys.argv',['probe','--plan',str(root/'plan.json')]), \
                 contextlib.redirect_stdout(io.StringIO()):
                code = runner.main()
            report = json.loads((root/'cohort-results.json').read_text())
        return code,calls,report

    def test_native_failure_runs_the_other_condition_and_retains_failed_result(self):
        code,calls,report = self.run_batch({'high-14':'DNF','low-14':'RESOURCE_CENSORED'})
        self.assertEqual(code,0)
        self.assertEqual(calls,['high-7','high-14','low-7','low-14'])
        self.assertEqual([r['status'] for r in report['results']],['COMPLETE','DNF','COMPLETE','RESOURCE_CENSORED'])
        self.assertIsNone(report['stop_reason'])

    def test_shared_technical_error_leaves_remaining_episodes_unexecuted(self):
        code,calls,report = self.run_batch({'high-14':'TECHNICAL_ERROR'})
        self.assertEqual(code,1)
        self.assertEqual(calls,['high-7','high-14'])
        self.assertEqual([r['status'] for r in report['results'][2:]],['UNEXECUTED','UNEXECUTED'])

    def test_baseline_mismatch_disqualifies_only_its_pair(self):
        code,calls,report = self.run_batch({},reproduction={'high'})
        self.assertEqual(code,1)
        self.assertEqual(calls,['high-7','low-7','low-14'])
        self.assertEqual(report['results'][1]['status'],'UNEXECUTED')
        self.assertEqual(report['pair_qualification']['low']['status'],'PASS')


if __name__ == '__main__':
    unittest.main()
