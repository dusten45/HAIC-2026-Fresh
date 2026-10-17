"""Recorded stand-ins exercise real440 APIs; no solver, new model or real env."""
import copy,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from dataclasses import asdict,replace
import numpy as np
from retry.native440 import Native440
from retry.routing440 import ObservedHistory440,ObservedRouteValues440
from retry.fixture440 import recorded_case
from retry.step440 import suffix_step
from retry.loss389_analyze import read
from retry.receipt421_io import load_receipt
from retry.parent436 import encoded,decode
from retry.ledger439 import require,LedgerStop439
from retry.fixture438 import stored_env
from retry.pilot420_json import restore_bytes
from retry.observer435 import current_rng
from retry.planner419 import GoalLedger,Parent
R=Path('/workspace/haic-private-retry-20261009')

def bind_case(directory,kind='first'):
 env,ctrl,trace,ledger,frame,row=recorded_case(R,kind);fixed=read(Path(read(R/'stage438/plan.json')['fixed_plan']));charges=[]
 def charge():charges.append(env.recorded_steps);require(env.recorded_steps==0,'CHARGE_MUST_PRECEDE_RECORDED_STEP')
 native=Native440(env,ctrl,ledger,fixed,charge_native=charge,obs=env.obs,directory=directory,arm='STATIC_'+kind);history=ObservedHistory440(native,fixed,'0'*64,'fixture');native.prepare_step(row['step']);nominal=ctrl.act(env);native.bind_nominal(nominal);return native,history,frame,row,trace,charges

class Native440Tests(unittest.TestCase):
 def test_recorded_first_dispatch_snapshot_fact_comparison_path(self):
  with tempfile.TemporaryDirectory() as td:
   n,h,f,r,tr,charges=bind_case(td);row,fact,proof=suffix_step(n,h,f,tr);self.assertEqual(charges,[0]);self.assertEqual(n.env.recorded_steps,1);self.assertEqual(n.ledger.progress_m,r['progress_after']);self.assertNotEqual(n.ledger.progress_m,f['model_progress']);self.assertTrue(proof['overall_verification_success']);self.assertEqual(h.verified,1);self.assertEqual(h.values.progress_m,n.ledger.progress_m);self.assertNotEqual(h.values.progress_m,f['model_progress']);self.assertEqual(len(h.posts),4);self.assertEqual(len(h.actions),1)
   pre=load_receipt(Path(td)/(n.label()+'-before-native-private.json'));post=load_receipt(Path(td)/(n.label()+'-after-native-private.json'));facts=load_receipt(Path(td)/(n.label()+'-actual-fact-private.json'));self.assertTrue(post['native_full_clock_verified']);self.assertTrue(facts['forecast_not_read']);self.assertEqual(pre['actual_calls_in_this_env_before'],0);self.assertEqual(post['native_sequence'],1);n.close_log()
 def test_recorded_prefix_uses_native_facts_and_existing_exact_reference(self):
  with tempfile.TemporaryDirectory() as td:
   n,h,f,r,tr,charges=bind_case(td,'prefix');n.dispatch(r['command'],tr);fact=n.commit_native_observation();n.verify_prefix(r,f);self.assertFalse(n.awaiting_verification);self.assertEqual(n.ledger.progress_m,r['progress_after']);self.assertEqual(charges,[0]);self.assertTrue(fact['native_fact_committed']);n.close_log()
 def test_failed_forecast_retains_fact_and_blocks_charge_and_next_dispatch(self):
  with tempfile.TemporaryDirectory() as td:
   n,h,f,r,tr,charges=bind_case(td);bad=copy.deepcopy(f);bad['model_progress']+=.001
   with self.assertRaises(Exception):suffix_step(n,h,bad,tr)
   self.assertTrue(n.halted);self.assertEqual(n.ledger.progress_m,r['progress_after']);self.assertEqual(len(n.rows),1);self.assertEqual(h.verified,0)
   with self.assertRaises(Exception):n.dispatch(r['command'],tr)
   with self.assertRaises(Exception):n.prepare_step(r['step']+1)
   with self.assertRaises(Exception):h.require_live()
   self.assertEqual(n.env.recorded_steps,1);self.assertEqual(charges,[0]);self.assertTrue((Path(td)/(n.label()+'-forecast-mismatch-private.json')).exists());n.close_log()
 def test_guardian_future_done_has_no_actual_DONE_before_own_pending_step(self):
  with tempfile.TemporaryDirectory() as td:
   n,h,f,r,tr,charges=bind_case(td,'pending');self.assertTrue(f['predicted']['finished']);self.assertFalse(n.ledger.done);self.assertEqual(n.env.recorded_steps,0);p=SimpleNamespace(actual_token=h.token,dispatch_count=0,actual_ledger_bytes=encoded(asdict(n.ledger)));row,fact,proof=suffix_step(n,h,f,tr,p);self.assertTrue(n.ledger.done);self.assertTrue(row['completed']);self.assertEqual(row['finish_time_s'],r['finish_time_s']);self.assertGreater(row['post']['time'],row['finish_time_s']);self.assertEqual(row['raw_ticks'],1);self.assertEqual(charges,[0]);self.assertTrue(proof['overall_verification_success']);n.close_log()
 def test_other_or_failed_native_ticket_blocks_fact_and_next_dispatch(self):
  with tempfile.TemporaryDirectory() as td:
   n,h,f,r,tr,charges=bind_case(td);n.dispatch(r['command'],tr);n.ticket.env=object()
   with self.assertRaises(Exception):n.commit_native_observation()
   self.assertTrue(n.halted);self.assertEqual(len(n.rows),0)
   with self.assertRaises(Exception):n.dispatch(r['command'],tr)
   self.assertEqual(charges,[0]);self.assertEqual(n.env.recorded_steps,1);n.close_log()
 def test_native_full_pre_snapshot_tamper_stops_before_charge(self):
  with tempfile.TemporaryDirectory() as td:
   n,h,f,r,tr,charges=bind_case(td);n.env.unwrapped.car.hull.position[0]+=.001
   with self.assertRaises(Exception):n.dispatch(r['command'],tr)
   self.assertTrue(n.halted);self.assertEqual(charges,[]);self.assertEqual(n.env.recorded_steps,0);self.assertEqual(len(list(Path(td).glob('*snapshot-mismatch-private.json'))),1);n.close_log()
 def test_observed_routing_values_cannot_be_native_ledger_authority(self):
  g=GoalLedger.start(1.,50);v=ObservedRouteValues440.from_actual_root(g)
  from retry.authority439 import NativeAuthority439
  with self.assertRaises(Exception):NativeAuthority439(object(),object(),v,{})
 def test_actual_pending_route_full_synthetic_observed_history_binding(self):
  # Synthetic algebra based on saved435 posts, not an actual history claim.
  from retry.test_parent436 import stored_parent
  p=stored_parent();ctx=p.context();state=decode(p.snapshot_bytes);full=read(R/'stage437/actual_C0/final-private.json');full['physical']=copy.deepcopy(state['physical']);full['wrapper'].update(finish_tracker=copy.deepcopy(state['finish_tracker']),elapsed_raw_steps=state['elapsed_raw_steps'],finish_time_s=None,finish_qualified_time_s=state['finish_tracker']['qualified_time_s']);env=stored_env(full);memory=decode(p.memory_after_nominal_bytes);ctrl=SimpleNamespace(memory=lambda:copy.deepcopy(memory));initial=ObservedRouteValues440(**decode(p.history_initial_ledger_bytes));values=ObservedRouteValues440(**decode(p.forecast_ledger_bytes));ledger=GoalLedger(values.progress_m,values.goal_m,values.age_actions,values.last_clock_tick,values.deadline_missed,values.done);actions=decode(p.history_actions_bytes);native=SimpleNamespace(env=env,ctrl=ctrl,obs=np.zeros((4,84,84),np.float32),ledger=ledger,halted=False,awaiting_verification=False,dispatcher=SimpleNamespace(calls=len(actions)));h=ObservedHistory440.__new__(ObservedHistory440);h.native=native;h.fixed=read(Path(read(R/'stage438/plan.json')['fixed_plan']));h.bound_env=env;h.bound_ctrl=ctrl;h.token='SYNTHETIC_NATIVE440';h.root=decode(p.history_root_bytes);h.initial=initial;h.values=values;h.posts=decode(p.history_posts_bytes);h.actions=actions;h.root_dispatch=0;h.verified=len(actions);src,mem,rng=ctx.parent.fork_inputs();rng['model_global_rng_digest']=current_rng()['digest'];ctx=replace(ctx,parent=Parent.current(src,mem,rng,ctx.parent.raw_clock_tick));pending=h.pending(ctx,decode(p.memory_before_bytes),dict(p.authority.source_versions));self.assertEqual(pending.validate(h,ctx)['gate'],'REGISTERED_PENDING_GUARDIAN_ONLY');self.assertFalse(pending.actual_DONE_allowed)
  with self.assertRaises(Exception):replace(pending,actual_token='other').validate(h,ctx)
  h.verified-=1
  with self.assertRaises(Exception):h.pending(ctx,decode(p.memory_before_bytes),dict(p.authority.source_versions))
