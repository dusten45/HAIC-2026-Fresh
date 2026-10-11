"""Regression for a failed preparation command followed by an attempted launch."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from retry.paired_audit_gate import publish_ready_plan, verify_readiness, claim_once

class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        (self.root/'sealed').mkdir();self.path=self.root/'sealed/plan.json'
        q=self.root/'qualification.json';q.write_text('{"status":"PASS"}')
        self.now=dt.datetime.now(dt.timezone.utc)
        self.plan={'simulation_deadline_utc':(self.now+dt.timedelta(seconds=600)).isoformat(),
                   'deadline_utc':(self.now+dt.timedelta(seconds=720)).isoformat(),
                   'qualification_path':str(q),'qualification_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),
                   'source_sha256':{},'runtime_sha256':{}}
        self.receipt={'status':'PASS','native_execution_authorized':True,
                      'qualification_sha256':self.plan['qualification_sha256'],
                      'native_deadline_utc':self.plan['simulation_deadline_utc'],
                      'overall_deadline_utc':self.plan['deadline_utc'],'required_native_window_s':500}
    def tearDown(self):self.tmp.cleanup()
    def test_failed_time_gate_publishes_nothing(self):
        with self.assertRaises(AssertionError):
            publish_ready_plan(self.path,self.plan,self.receipt,now=self.now+dt.timedelta(seconds=101))
        self.assertFalse(self.path.exists())
        self.assertFalse((self.root/'paired-protocol-receipt.json').exists())
    def test_valid_one_use_claim_and_stale_rejection(self):
        publish_ready_plan(self.path,self.plan,self.receipt,now=self.now)
        with self.assertRaises(AssertionError):verify_readiness(self.path,now=self.now+dt.timedelta(seconds=101))
        claim_once(self.path)
        with self.assertRaises(AssertionError):claim_once(self.path)
    def test_ready_entrypoint_claims_before_ordered_mocked_episodes(self):
        from retry import road_keep_holdout_probe as runner
        cases=[{'id':f'synthetic-{i}'} for i in range(8)]
        self.plan['cases']=cases
        publish_ready_plan(self.path,self.plan,self.receipt,now=self.now)
        ordered=[]
        def saved_episode(case,plan,path,initial):
            self.assertTrue((path.parent/'opening-receipt.json').exists())
            ordered.append(case['id'])
            return {'id':case['id'],'status':'COMPLETE','charged_wrapper_actions':0},False
        report={'aggregate':{'synthetic':True},'mechanical_receipt':{'pass':True}}
        with patch.object(runner,'episode',side_effect=saved_episode), \
             patch.object(runner.native,'make_env') as env, \
             patch.object(runner,'SandboxWorker') as actor, \
             patch('retry.road_keep_holdout_aggregate.aggregate',return_value=report) as aggregate, \
             patch('sys.argv',['audit','--plan',str(self.path)]), patch('builtins.print'):
            self.assertEqual(runner.main(),0)
            env.assert_not_called();actor.assert_not_called()
            aggregate.assert_called_once_with(self.path.parent,cases)
        self.assertEqual(ordered,[c['id'] for c in cases])
        self.assertEqual(json.loads((self.root/'aggregate.json').read_text()),report['aggregate'])

    def test_readiness_missing_failed_or_mismatched_has_zero_launches(self):
        from retry import road_keep_holdout_probe as runner
        self.path.write_text(json.dumps(self.plan))
        path=self.root/'paired-protocol-receipt.json'
        variants=[None, self.receipt|{'status':'FAIL','plan_sha256':hashlib.sha256(self.path.read_bytes()).hexdigest()},
                  self.receipt|{'plan_sha256':'0'*64},
                  self.receipt|{'required_native_window_s':9999,'plan_sha256':hashlib.sha256(self.path.read_bytes()).hexdigest()}]
        for value in variants:
            if value is not None:path.write_text(json.dumps(value))
            elif path.exists():path.unlink()
            with patch.object(runner,'episode') as run, patch.object(runner.native,'make_env') as env, \
                 patch.object(runner,'SandboxWorker') as actor, patch('sys.argv',['audit','--plan',str(self.path)]):
                with self.assertRaises((AssertionError,FileNotFoundError)):runner.main()
                run.assert_not_called();env.assert_not_called();actor.assert_not_called()

if __name__=='__main__':unittest.main()
