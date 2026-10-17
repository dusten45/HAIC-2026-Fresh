"""Actual first-shadow constructor path with recorded stand-ins, zero integration."""
import copy
import tempfile
import unittest
from contextlib import contextmanager
from dataclasses import asdict, replace, FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from retry.query445 import bind_model_query, QueryChannelError
from retry.experiment445 import Experiment445
from retry.experiment444 import Meter444
from retry.paired417_common import SourceC
from retry.planner419 import GoalLedger
from retry.planner419_model_ledger import ForecastLedger, ModelPrediction
from retry.fixture438 import stored_env
from retry.actual437_boundary import live_proxy
from retry.audit439 import root_ledger
from retry.receipt421_io import load_receipt
from retry.loss389_analyze import read, save
from retry.terminal410_model import snapshot
R=Path('/workspace/haic-private-retry-20261009')


@contextmanager
def fixture():
    import json
    import numpy as np
    full=load_receipt(R/'stage442/actual_C0/C0_step90-before-native-private.json')['full_pre_before_nominal']
    old=read(R/'stage442/plan.json')
    fixed=read(Path(old['fixed_plan']))
    pace=np.asarray(read(R/'stage404/profiles-private.json')['frozen268'])
    row=json.loads((R/'stage442/actual_C0/trace-private.jsonl').read_text().splitlines()[89])
    actual=root_ledger(row)
    def recorded_world():
        world=live_proxy(stored_env(copy.deepcopy(full)))
        world.native_ticks=0
        world.close=lambda:None
        return world
    parent=SimpleNamespace(m=recorded_world(),ctrl=SourceC(fixed,pace,copy.deepcopy(full['controller'])),ledger=ForecastLedger.fork(actual))
    before=copy.deepcopy(parent.ctrl.memory());nominal=parent.ctrl.act(parent.m)
    with tempfile.TemporaryDirectory() as temp:
        d=Path(temp)
        save(d/'plan.json',dict(semantic_sources=old['semantic_sources'],deadline_utc='2026-10-20T10:01:55Z',caps=dict(ticks=6656,worlds=128,CPU_s=240,wall_s=480)))
        meter=Meter444(d)
        def no_physics_world(state,tag):
            world=recorded_world()
            meter.auth[id(world)]=dict(number=len(meter.auth)+1,constructor_proof_sha256='0'*64)
            return world
        ex=Experiment445.__new__(Experiment445)
        ex.root=R;ex.d=d;ex.fixed=fixed;ex.pace=pace;ex.actual=actual;ex.actual_stamp=actual.digest();ex.meter=meter;ex.children=[]
        with patch.object(meter,'world',side_effect=no_physics_world),patch.object(meter,'step',side_effect=AssertionError('FORBIDDEN_INTEGRATION')) as step:
            q=bind_model_query(parent,actual,before,nominal,fixed,'fixture445')
            try:
                yield ex,parent,actual,q,step
            finally:
                for c in ex.children:
                    if not c.closed:ex.close(c)
                assert step.call_count==0


class Query445Tests(unittest.TestCase):
    def test_production_first_shadow_constructor_value_view_to_stream(self):
        with fixture() as (ex,p,a,q,step):
            c=q.spawn(ex,p,a,'first_shadow','nominal')
            self.assertIs(type(c.ledger),ForecastLedger)
            self.assertEqual(c.ledger.actual_root_digest,q.context.ledger.digest())
            self.assertEqual(c.stream.posts,[])
            self.assertEqual(c.stream.actions,[])
            self.assertEqual(q.context.ledger.progress_m,p.ledger.progress_m)
            self.assertNotEqual(id(c.ledger),id(p.ledger))
            self.assertFalse(q.actual_execution_allowed)
            self.assertFalse(q.actual_DONE_allowed)
            self.assertEqual(step.call_count,0)

    def test_original_forecast_input_still_rejected_no_digest_added(self):
        with fixture() as (ex,p,a,q,step):
            self.assertFalse(hasattr(p.ledger,'digest'))
            with self.assertRaises(AttributeError):
                ex.new(snapshot(p.m),q.before,p.ledger,'old_bad_input',guardian=True)

    def test_wrong_type_channel_or_actual_root_rejected(self):
        with fixture() as (ex,p,a,q,step):
            original=p.ledger;p.ledger=a
            with self.assertRaises(QueryChannelError):q.validate(p,a)
            p.ledger=original
            with self.assertRaises(QueryChannelError):q.validate(p,original)
            p.ledger=replace(original,actual_root_digest='bad')
            with self.assertRaises(QueryChannelError):q.validate(p,a)
            p.ledger=original

    def test_stale_parent_ledger_clock_and_mutation_rejected(self):
        with fixture() as (ex,p,a,q,step):
            original=p.ledger
            p.ledger=original.advance_prediction(ModelPrediction(original.progress_m+1,original.last_clock_tick+4))
            with self.assertRaises(QueryChannelError):q.validate(p,a)
            p.ledger=original;p.m.native_ticks+=4
            with self.assertRaises(QueryChannelError):q.validate(p,a)
            p.m.native_ticks-=4
            with self.assertRaises(QueryChannelError):q.validate(SimpleNamespace(**p.__dict__),a)

    def test_forged_value_context_or_permission_rejected(self):
        with fixture() as (ex,p,a,q,step):
            ctx=replace(q.context,ledger=replace(q.context.ledger,progress_m=q.context.ledger.progress_m+.1))
            with self.assertRaises(QueryChannelError):replace(q,context=ctx).validate(p,a)
            with self.assertRaises(QueryChannelError):replace(q,actual_DONE_allowed=True).validate(p,a)

    def test_shadow_memory_and_frozen_ledger_cannot_change_parent(self):
        with fixture() as (ex,p,a,q,step):
            old=copy.deepcopy(p.ctrl.memory());ledger=asdict(p.ledger);actual=asdict(a)
            c=q.spawn(ex,p,a,'isolated_shadow','nominal')
            c.ctrl.scope['laststeer']+=1
            c.ledger=replace(c.ledger,progress_m=c.ledger.progress_m+1)
            self.assertEqual(p.ctrl.memory(),old);self.assertEqual(asdict(p.ledger),ledger);self.assertEqual(asdict(a),actual)
            with self.assertRaises(FrozenInstanceError):p.ledger.progress_m=0
            q.validate(p,a)

    def test_parent_memory_and_RNG_tamper_rejected(self):
        with fixture() as (ex,p,a,q,step):
            old=p.ctrl.scope['laststeer'];p.ctrl.scope['laststeer']+=1
            with self.assertRaises(QueryChannelError):q.validate(p,a)
            p.ctrl.scope['laststeer']=old
            with patch('retry.query445.rnghash',return_value='changed'):
                with self.assertRaises(QueryChannelError):q.validate(p,a)

    def test_model_DONE_and_value_view_never_native_authority(self):
        from retry.authority439 import NativeAuthority439
        with fixture() as (ex,p,a,q,step):
            with self.assertRaises(QueryChannelError):q.commit_actual_done(True)
            original=p.ledger;p.ledger=replace(original,done=True)
            with self.assertRaises(QueryChannelError):q.validate(p,a)
            p.ledger=original
            native=NativeAuthority439(object(),object(),q.context.ledger,ex.fixed)
            with self.assertRaises(Exception):native.dispatch([0.,0.,0.],None)
            self.assertTrue(native.halted)
