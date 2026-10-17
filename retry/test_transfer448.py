"""Recorded current-root and negative fixtures; no native/model integration."""
import copy,json,tempfile,unittest
from pathlib import Path
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from retry.query448 import Query448,recipe448,finite_guard448
from retry.meter448 import Meter448
from retry.pilot420_backend import ResourceStop
from retry.fixture438 import stored_env
from retry.actual437_boundary import live_proxy
from retry.paired417_common import SourceC
from retry.receipt421_io import load_receipt
from retry.audit439 import root_ledger
from retry.loss389_analyze import read,save
R=Path('/workspace/haic-private-retry-20261009')

@contextmanager
def current_fixture():
    full=load_receipt(R/'stage442/actual_C0/C0_step23-before-native-private.json')['full_pre_before_nominal']
    old=read(R/'stage447/plan.json');fixed=read(Path(old['fixed_plan']));pace=np.asarray(read(R/'stage404/profiles-private.json')['frozen268'])
    actual=[json.loads(t) for t in (R/'stage442/actual_C0/trace-private.jsonl').read_text().splitlines()][22]
    ledger=root_ledger(actual);env=stored_env(copy.deepcopy(full));obs=np.zeros((4,84,84),np.float32)
    ctrl=SourceC(fixed,pace,copy.deepcopy(full['controller']));before=copy.deepcopy(ctrl.memory());nominal=ctrl.act(live_proxy(env))
    history=SimpleNamespace(env=env,obs=obs,ctrl=ctrl,ledger=ledger,initial=SimpleNamespace(actual_root_digest=ledger.digest()),require_live=lambda:None)
    with tempfile.TemporaryDirectory() as td:
        d=Path(td);save(d/'plan.json',dict(semantic_sources=old['semantic_sources'],fixed_plan=old['fixed_plan'],deadline_utc='2026-10-20T10:01:55Z'))
        meter=Meter448(d);query=Query448.__new__(Query448);query.root=R;query.d=d;query.meter=meter;query.fixed=fixed;query.pace=pace;query.children=[];query.policy_digest='fixture448'
        def world(state,tag):
            m=live_proxy(stored_env(copy.deepcopy(full)));m.native_ticks=0;m.close=lambda:None
            meter.auth[id(m)]=dict(number=len(meter.auth)+1,constructor_proof_sha256='0'*64)
            return m
        frame=read(R/'stage444/H1/nominal1-private.json')['rows'][0]
        def guard(child,tag,line,exit_progress):
            computed=child.ctrl.act(child.m);child.rows=[copy.deepcopy(frame)];child.stream.actions=[dict(nominal=computed.tolist())]
            return dict(reached=False,rawtick_bracket=None)
        with patch.object(meter,'world',side_effect=world),patch.object(meter,'step',side_effect=AssertionError('FORBIDDEN_INTEGRATION')) as step,patch('retry.query448.finite_guard448',side_effect=guard) as guardmock:
            try:yield query,history,before,nominal,step,guardmock
            finally:
                for c in query.children:
                    if not c.closed:c.close()
                assert step.call_count==0

class Transfer448Tests(unittest.TestCase):
    def test_fixed_pulse_only_candidate_first(self):
        self.assertEqual(recipe448('fullgas',1),'fullgas')
        for d in range(2,27):self.assertEqual(recipe448('fullgas',d),'nominal')
        for d in range(1,27):self.assertEqual(recipe448('nominal',d),'nominal')
        for arm,d in [('other',1),('nominal',27),('fullgas',0)]:
            with self.assertRaises(Exception):recipe448(arm,d)
    def test_real_current_context_to_child_constructor_observer_pair(self):
        with current_fixture() as(q,h,b,n,step,guard):
            first,record=q.query_fixed(h,b,n,'nominal',1,h.ledger.progress_m+60)
            self.assertEqual(guard.call_count,2);self.assertEqual(step.call_count,0)
            self.assertTrue(record['independent_repeat_exact']);self.assertFalse(record['actual_DONE_allowed'])
            self.assertEqual(first['memory_after'],h.ctrl.memory());self.assertEqual(len(q.meter.queries),1)
    def test_wrong_current_memory_blocks_dispatch_evidence(self):
        with current_fixture() as(q,h,b,n,step,guard):
            bad=copy.deepcopy(b);bad['C']['s']+=.001
            with self.assertRaises(Exception):q.query_fixed(h,bad,n,'nominal',1,h.ledger.progress_m+60)
            self.assertEqual(q.meter.queries,[]);self.assertEqual(step.call_count,0)
    def test_repeat_difference_blocks_dispatch_evidence(self):
        with current_fixture() as(q,h,b,n,step,guard):
            original=guard.side_effect;calls=[]
            def altered(*args):
                out=original(*args);calls.append(1)
                if len(calls)==2:args[0].rows[0]['model_progress']+=.001
                return out
            guard.side_effect=altered
            with self.assertRaises(Exception):q.query_fixed(h,b,n,'nominal',1,h.ledger.progress_m+60)
            self.assertEqual(q.meter.queries,[])
    def test_native_parent_mutation_blocks_dispatch_evidence(self):
        with current_fixture() as(q,h,b,n,step,guard):
            original=guard.side_effect
            def altered(*args):
                out=original(*args);h.env.unwrapped.car.hull.position[0]+=.001;return out
            guard.side_effect=altered
            with self.assertRaises(Exception):q.query_fixed(h,b,n,'nominal',1,h.ledger.progress_m+60)
            self.assertEqual(q.meter.queries,[])
    def test_finite_guard_stops_at_common_exit_without_padding(self):
        c=SimpleNamespace(rows=[],status='ACTIVE',ledger=SimpleNamespace(deadline_missed=False),root_ledger=SimpleNamespace(progress_m=1.))
        c.one=lambda tag:c.rows.append(dict(safety=[]))
        with patch('retry.query448.arrival',side_effect=[dict(reached=False),dict(reached=True)]):
            self.assertTrue(finite_guard448(c,'fixture',[],61.)['reached']);self.assertEqual(len(c.rows),2)
    def test_finite_guard_rejects_first_safety_failure(self):
        c=SimpleNamespace(rows=[],status='ACTIVE',ledger=SimpleNamespace(deadline_missed=False),root_ledger=SimpleNamespace(progress_m=1.))
        c.one=lambda tag:c.rows.append(dict(safety=['collision_or_obstacle']))
        with self.assertRaises(Exception):finite_guard448(c,'fixture',[],61.)
        self.assertEqual(len(c.rows),1)
    def test_native_and_model_hard_caps_charge_before_call(self):
        with current_fixture() as(q,h,b,n,step,guard):
            m=q.meter;m.actual_start=(1.,1.);m.active=None;m.guard=lambda:None;m.persist=lambda:None
            m.nb['actions']=96
            with self.assertRaises(ResourceStop):m.charge('action','nominal')
            m.b['worlds']=128
            with self.assertRaises(ResourceStop):Meter448.world(m,{},'fixture')
            m.b['reserved_ticks']=6144
            with self.assertRaises(ResourceStop):Meter448.step(m,object(),[],'fixture')
