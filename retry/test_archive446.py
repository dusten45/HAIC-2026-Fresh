"""Archived predicted-ledger/constructor fixture; no world or step integration."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from dataclasses import asdict,replace
from retry.archive446 import validate_archive,ArchiveGateError
from retry.extension446 import new_child,restore_rng
from retry.experiment444 import Meter444
from retry.fixture438 import stored_env
from retry.actual437_boundary import live_proxy
from retry.loss389_analyze import read,save
from retry.receipt421_io import load_receipt
from retry.planner419 import GoalLedger
R=Path('/workspace/haic-private-retry-20261009')


class Archive446Tests(unittest.TestCase):
    def setUp(self):
        self.data=read(R/'stage444/H1/nominal1-private.json')
        self.digest=self.data['model_ledger']['actual_root_digest']

    def test_valid_closed_archive_full_predicted_ledger(self):
        ledger=validate_archive(self.data,self.digest)
        self.assertEqual(asdict(ledger),self.data['model_ledger'])
        self.assertTrue(ledger.actual_root_goal_reached)
        self.assertFalse(ledger.done)

    def test_wrong_root_or_actual_channel_rejected(self):
        with self.assertRaises(ArchiveGateError):validate_archive(self.data,'wrong')
        bad=copy.deepcopy(self.data);bad['model_ledger']=GoalLedger.start(1.,1)
        with self.assertRaises(ArchiveGateError):validate_archive(bad,self.digest)

    def test_goal_age_and_clock_tampering_rejected(self):
        for field in ['goal_m','age_actions','last_clock_tick']:
            bad=copy.deepcopy(self.data);bad['model_ledger'][field]+=1
            with self.assertRaises(ArchiveGateError):validate_archive(bad,self.digest)

    def test_memory_coverage_or_done_rejected(self):
        bad=copy.deepcopy(self.data);bad['controller_memory']['laststeer']+=1
        with self.assertRaises(ArchiveGateError):validate_archive(bad,self.digest)
        bad=copy.deepcopy(self.data);bad['rows'].pop()
        with self.assertRaises(ArchiveGateError):validate_archive(bad,self.digest)
        bad=copy.deepcopy(self.data);bad['model_ledger']['done']=True
        with self.assertRaises(ArchiveGateError):validate_archive(bad,self.digest)

    def test_RNG_digest_failure_before_setstate(self):
        with self.assertRaises(ArchiveGateError):restore_rng({'RNG':{'global_pickle':b'bad','digest':'wrong'}})

    def test_constructor_restores_complete_forecast_not_fresh_actual_fork(self):
        old=read(R/'stage445/plan.json');full=load_receipt(R/'stage442/actual_C0/C0_step23-before-native-private.json')['full_pre_before_nominal']
        full['physical']=copy.deepcopy(self.data['final_state']['physical'])
        full['controller']=copy.deepcopy(self.data['controller_memory'])
        full['wrapper'].update(finish_tracker=copy.deepcopy(self.data['final_state']['finish_tracker']),elapsed_raw_steps=self.data['final_state']['elapsed_raw_steps'])
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);save(d/'plan.json',dict(semantic_sources=old['semantic_sources'],fixed_plan=old['fixed_plan'],pace_path=str(R/'stage404/profiles-private.json'),deadline_utc='2026-10-20T10:01:55Z',caps=dict(ticks=256,worlds=8,CPU_s=60,wall_s=120)))
            meter=Meter444(d)
            def fixture_world(state,tag):
                m=live_proxy(stored_env(copy.deepcopy(full)));m.native_ticks=0;m.close=lambda:None
                meter.auth[id(m)]=dict(number=1,constructor_proof_sha256='0'*64)
                return m
            with patch.object(meter,'world',side_effect=fixture_world),patch.object(meter,'step',side_effect=AssertionError('FORBIDDEN_INTEGRATION')) as step:
                c=new_child(meter,self.data,'recorded_archive')
                self.assertEqual(asdict(c.ledger),self.data['model_ledger'])
                self.assertEqual(c.ctrl.memory(),self.data['controller_memory'])
                c.ledger=replace(c.ledger,progress_m=c.ledger.progress_m+1)
                self.assertNotEqual(c.ledger.progress_m,self.data['model_ledger']['progress_m'])
                c.dump(d);c.close();self.assertEqual(step.call_count,0)
