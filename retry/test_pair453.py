"""Whole-policy integration fixtures, forbidden constructors and native authority."""
import copy,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from retry.query453 import Query453,mode453
from retry.paired442_query import Query442
from retry.meter453 import Meter453
from retry.pilot420_backend import ResourceStop
from retry.planner419 import GoalLedger
from retry.planner419_model_ledger import ForecastLedger
from retry.test_transfer448 import current_fixture
from retry.loss389_analyze import read
R=Path('/workspace/haic-private-retry-20261009')

class Pair453Tests(unittest.TestCase):
    def test_frozen_modes_pulse270_switch_and_pending(self):
        self.assertEqual(mode453('candidate',1,False,'FIRST_LAP',False),('FIXED_FIRST_PULSE','fullgas'))
        self.assertEqual(mode453('baseline',1,False,'FIRST_LAP',False),('FIXED_NOMINAL_TO270','nominal'))
        self.assertEqual(mode453('candidate',2,False,'FIRST_LAP',False),('FIXED_NOMINAL_TO270','nominal'))
        self.assertEqual(mode453('candidate',60,True,'FIRST_LAP',False),('CONDITIONAL_B','nominal'))
        self.assertEqual(mode453('candidate',190,True,'FINISH_CONFIRM',True),('REGISTERED_PENDING_B','nominal'))
        for args in [('candidate',1,True,'FIRST_LAP',False),('baseline',199,True,'FIRST_LAP',False),('baseline',100,True,'FINISH_CONFIRM',False),('baseline',50,False,'FIRST_LAP',True)]:
            with self.assertRaises(Exception):mode453(*args)
    def recorded_query(self,arm,B_started,valid=True):
        with current_fixture() as(old,h,b,n,step,guard):
            q=Query453.__new__(Query453);q.__dict__.update(old.__dict__);q.alternatives=[]
            recipe='fullgas' if arm=='candidate' and not B_started else 'nominal'
            frame=read(R/('stage444/H1/'+recipe+'1-private.json'))['rows'][0]
            calls=[]
            def pair(parent,ctx,before,label,selected_recipe):
                calls.append(selected_recipe);q.alternatives.append(dict(recipe=selected_recipe,valid=valid,certificate=None))
                return dict(valid=valid,first=copy.deepcopy(frame),recipe=selected_recipe,certificate=None)
            with patch.object(q,'short_pair',side_effect=pair):
                if valid:
                    first,record,pending=q.query_policy(h,b,n,arm,1,B_started);self.assertEqual(record['selected_recipe'],recipe);self.assertIsNone(pending)
                else:
                    with self.assertRaises(Exception):q.query_policy(h,b,n,arm,1,B_started)
            self.assertEqual(calls,[recipe]);self.assertEqual(step.call_count,0)
    def test_native_current_adapter_fixed_pulse_no_step(self):self.recorded_query('candidate',False)
    def test_fixed_nominal_invalid_does_not_fallback(self):self.recorded_query('baseline',False,False)
    def test_native_current_conditional_B_nominal_no_step(self):self.recorded_query('baseline',True)
    def test_forecast_cannot_replace_current_native_ledger(self):
        with current_fixture() as(old,h,b,n,step,guard):
            q=Query453.__new__(Query453);q.__dict__.update(old.__dict__);h.ledger=ForecastLedger.fork(h.ledger)
            with self.assertRaises(Exception):q.query_policy(h,b,n,'baseline',1,False)
            self.assertEqual(step.call_count,0)
    def test_late_FINISHED_shadow_requires_registered_no_native_DONE_certificate(self):
        g=GoalLedger.start(1.,51);q=Query453.__new__(Query453);q.history=SimpleNamespace(ledger=g);q.children=[];q.alternatives=[];ctx=SimpleNamespace(ledger=g)
        def late(*args):
            q.children.append(SimpleNamespace(status='FINISHED',guardian_certificate=dict(model_confirmation_qualified=True,actual_done_allowed=False)))
            return dict(valid=True,certificate=q.children[-1].guardian_certificate)
        with patch.object(Query442,'short_pair',side_effect=late):self.assertTrue(q.short_pair(None,ctx,None,'fixture','nominal')['valid'])
        def invalid(*args):
            q.children.append(SimpleNamespace(status='FINISHED',guardian_certificate=dict(model_confirmation_qualified=True,actual_done_allowed=True)))
            return dict(valid=True,certificate=q.children[-1].guardian_certificate)
        with patch.object(Query442,'short_pair',side_effect=invalid):
            with self.assertRaises(Exception):q.short_pair(None,ctx,None,'fixture','nominal')
    def test_legacy1024_world_limit_is_not_a_hidden_new_cap(self):
        with tempfile.TemporaryDirectory() as td:
            m=Meter453.__new__(Meter453);m.active=(0.,0.);m.inputs=dict(fixture='recorded');m.guard=lambda:None;m.persist=lambda:None;m.timing=lambda *args:None;m.d=Path(td);m.sequence=0;m.live=[];m.auth={};m.b=dict(worlds=1024,worlds_by_tag={},confirmed_worlds=1024,max_live_worlds=0)
            world=SimpleNamespace(initial_bodies_exact=True,initial_tiles_exact=True,initial_progress_exact=True,initial_finish_exact=True)
            with patch('retry.meter453.TerminalVehicleTransition',return_value=world):self.assertIs(m.world({},'fixture'),world)
            self.assertEqual(m.b['worlds'],1025);self.assertEqual(len(m.auth),1)
            m.b['worlds']=1792
            with self.assertRaises(ResourceStop):m.world({},'fixture')
    def test_native440_arm220_reset2_and_model98304_caps(self):
        m=Meter453.__new__(Meter453);m.actual_start=(1.,1.);m.active=None;m.guard=lambda:None;m.persist=lambda:None;m.nb=dict(actions=440,resets=2,arm_actions={},arm_resets={});m.b=dict(reserved_ticks=98304)
        with self.assertRaises(ResourceStop):m.charge('action','candidate')
        with self.assertRaises(ResourceStop):m.charge('reset','baseline')
        with self.assertRaises(ResourceStop):m.step(object(),[],'fixture')
