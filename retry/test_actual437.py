"""Actual dispatch negatives and synthetic pending algebra; no new world."""
import copy,json,unittest
from pathlib import Path
from types import SimpleNamespace
from dataclasses import asdict,replace
from unittest.mock import patch
import numpy as np
from core.finish_line import FinishLineTracker
from retry.actual437_boundary import *
from retry.planner419 import Current,Parent,H
from retry.early429 import ProtocolStop
from retry.pilot420_backend import rnghash
from retry.loss389_analyze import read
from retry.proposal429 import bounds
R=Path('/workspace/haic-private-retry-20261009')

def synthetic_pending_fixture():
 from retry.test_parent436 import stored_parent
 b=stored_parent();a=ActualAuthority437(b.authority.source_versions,b.authority.geometry_total_length_m,'LIVE_ACTUAL_POST_TICK_OBSERVER437')
 b=replace(b,authority=a,history_provenance='SYNTHETIC435_ALGEBRA_ONLY_NO_ACTUAL_EXECUTION')
 return b,b.context()

class ActualControls437(unittest.TestCase):
 def test_synthetic_pending_adapter_algebra_has_no_done_or_execution_rights(self):
  b,c=synthetic_pending_fixture();info=b.validate(b.parent_token,c);self.assertEqual(info['gate'],'REGISTERED_PENDING_GUARDIAN_ONLY');self.assertFalse(b.actual_DONE_allowed);self.assertFalse(b.actual_execution_allowed);self.assertFalse(b.parent_done)
 def test_archived_or_model_history_cannot_claim_live_actual_pending(self):
  b,c=synthetic_pending_fixture();owner=SimpleNamespace(require_live=lambda:None,token=b.parent_token,dispatcher=SimpleNamespace(calls=176),env=object(),obs=None,ctrl=SimpleNamespace(memory=lambda:{}),ledger=c.ledger,actions=[None]*58,root_dispatch=118,actual_commits=58);p=ActualPending437(b,owner.token,176,fingerprint({}),encoded(asdict(c.ledger)))
  with patch('retry.actual437_boundary.complete_state',return_value={}):
   with self.assertRaises(ProtocolStop):p.validate(owner,c)
 def test_model_certificate_or_other_ticket_cannot_commit_actual(self):
  d=Dispatch437(object(),'SYNTHETIC');d.ticket=object()
  for fake in [None,dict(actual_done_allowed=True,model_confirmation_qualified=True),SimpleNamespace(success=True)]:
   with self.assertRaises(ProtocolStop):d.check(fake,{})
 def test_undispatched_or_failed_native_ticket_cannot_commit(self):
  env=object();d=Dispatch437(env,'SYNTHETIC');d.calls=1;t=SimpleNamespace(owner=d,env=env,number=1,success=False);d.ticket=t
  with self.assertRaises(ProtocolStop):d.check(t,{})
 def test_model_prediction_cannot_advance_actual_ledger(self):
  g=GoalLedger.start(1.,50)
  with self.assertRaises(Exception):g.advance_actual(ModelPrediction(2.,54,True))
  self.assertFalse(g.done)
 def test_actual_DONE_requires_live_official_tracker_not_forecast(self):
  row=json.loads((R/'stage427/actual_P/trace-private.jsonl').read_text().splitlines()[-1]);env=SimpleNamespace(unwrapped=SimpleNamespace(t=row['post']['time'],finish_time_s=None,finish_line_tracker=SimpleNamespace(finish_time_s=None)));d=Dispatch437(env,'SYNTHETIC');d.calls=1;t=SimpleNamespace(owner=d,env=env,number=1,success=True,command=row['command'],start=row['pre']['time'],end=row['post']['time'],posts=[{}]*row['raw_ticks']);d.ticket=t
  with self.assertRaises(ProtocolStop):d.check(t,row)
 def test_other_env_counter_command_clock_or_consumed_ticket_rejected(self):
  d=Dispatch437(object(),'SYNTHETIC');d.calls=2
  for owner,env,n in [(object(),d.env,2),(d,object(),2),(d,d.env,1)]:
   t=SimpleNamespace(owner=owner,env=env,number=n,success=True);d.ticket=t
   with self.assertRaises(ProtocolStop):d.check(t,{})
  t=object();d.ticket=t;d.consume(t)
  with self.assertRaises(ProtocolStop):d.consume(t)
 def test_actual_and_model_worst_bounds_include_qualification_and_both_arms(self):
  b=bounds(qualification_ticks=1242,qualification_worlds=35);self.assertEqual((b['total_tick_cap_required']-720,b['total_world_cap_required']-2),(518426,883));self.assertEqual(2*118+80+100,416);self.assertLessEqual(518426,524288);self.assertLessEqual(883,1024)
 def test_prefix_is_actual_and_has_all_fidelity_fields(self):
  r=[json.loads(t) for t in (R/'stage423/actual_C0/trace-private.jsonl').read_text().splitlines()][:118];self.assertEqual(len(r),118)
  for x in r:self.assertTrue(all(k in x for k in ['raw_hull','raw_tire_samples','memory_before','nominal_memory_after','pre','post','command']))
 def test_actual_model_memory_or_ledger_mismatch_stops_before_commit(self):
  h=ActualHistory437.__new__(ActualHistory437);h.require_live=lambda:None;h.dispatcher=SimpleNamespace(check=lambda *x:None);h.ledger=GoalLedger.start(1.,50);h.ctrl=SimpleNamespace(memory=lambda:{'wrong':True});row=dict(post=dict(time=1.08),memory_before={},nominal_memory_after={});frame=dict(memory_before={},memory_after={})
  with self.assertRaises(ProtocolStop):h.commit(None,row,None,frame)
  self.assertFalse(h.ledger.done)

 def test_saved_native_finish_ticket_and_tracker_positive_static_only(self):
  row=json.loads((R/'stage427/actual_P/trace-private.jsonl').read_text().splitlines()[-1]);full=read(R/'stage427/actual_P/final-private.json');tracker=full['wrapper']['finish_tracker'];env=SimpleNamespace(unwrapped=SimpleNamespace(t=row['post']['time'],finish_time_s=row['finish_time_s'],finish_line_tracker=SimpleNamespace(**tracker)));d=Dispatch437(env,'STATIC_ONLY');d.calls=1;t=SimpleNamespace(owner=d,env=env,number=1,success=True,command=row['command'],start=row['pre']['time'],end=row['post']['time'],posts=[dict(tracker_after=tracker)]*row['raw_ticks']);d.ticket=t;d.check(t,row);d.consume(t);self.assertIsNone(d.ticket)

 def test_actual_call_caps_reject_before_new_call(self):
  from retry.paired437_meter import Meter
  for kind,arm,actions,resets,aa,ar in [('action','P',416,1,200,1),('reset','P',200,2,100,1),('action','C0',198,1,198,1),('action','P',218,1,218,1)]:
   m=Meter.__new__(Meter);m.actual_start=True;m.active=None;m.guard=lambda:None;m.persist=lambda:None;m.nb=dict(actions=actions,resets=resets,arm_actions={arm:aa},arm_resets={arm:ar});old=copy.deepcopy(m.nb)
   with self.assertRaises(Exception):m.charge(kind,arm)
   self.assertEqual(m.nb,old)
