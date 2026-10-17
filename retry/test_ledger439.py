"""Static contract tests using saved data and analytic geometries only."""
import copy,json,math,unittest
from dataclasses import replace,asdict
from pathlib import Path
from types import SimpleNamespace
from retry.geometry439 import Projection439,Interval,GeometryStop439,Telescope439
from retry.ledger439 import *
from retry.authority439 import NativeAuthority439
from retry.receipt421_io import load_receipt
from retry.fixture438 import stored_env
from retry.loss389_analyze import read
R=Path('/workspace/haic-private-retry-20261009')
def stored():
 packet=load_receipt(R/'stage438/C0_decision1-before-actual-dispatch-private.json');row=json.loads((R/'stage438/actual_C0/trace-private.jsonl').read_text().splitlines()[-1]);fixed=read(Path(read(R/'stage438/plan.json')['fixed_plan']));return GoalLedger(**packet['context']['ledger']),packet['selected_first'],row,fixed

def recorded_authority():
 old,f,r,fixed=stored();full=read(R/'stage438/actual_C0/final-private.json');env=stored_env(full);ctrl=SimpleNamespace(phase=lambda:r['nominal_memory_after']['C']['phase'],memory=lambda:copy.deepcopy(r['nominal_memory_after']));a=NativeAuthority439(env,ctrl,old,fixed);root=dict(pre=r['pre'],memory=r['memory_before'],phase=r['memory_before']['C']['phase'],ledger=asdict(old),tracker=read(R/'stage438/actual_C0/fork-private.json')['wrapper']['finish_tracker']);a.prepared=root;a.dispatcher.calls=1;tracker=copy.deepcopy(env.unwrapped.finish_line_tracker.__dict__);ticket=SimpleNamespace(owner=a.dispatcher,env=env,number=1,success=True,start=r['pre']['time'],end=r['post']['time'],command=r['command'],posts=[dict(tracker_after=tracker,collision=False,wheel_road_contacts=4) for _ in range(r['raw_ticks'])],native_prepared=root,nominal_memory=r['nominal_memory_after'],nominal_phase=r['nominal_memory_after']['C']['phase'],native_post=r['post'],native_out=(None,0.,r['ended'],r['truncated'],dict(collision=r['collision'])),native_tires=r['raw_tire_samples'],native_hulls=r['raw_hull']);a.ticket=ticket;a.dispatcher.ticket=ticket
 return a,old,f,r,fixed
class Ledger439(unittest.TestCase):
 def test_438_progress_difference_passes_new_static_bound_actual_values_only(self):
  old,f,r,fixed=stored();a,c=compare_first(old,f,r,fixed);self.assertEqual(a.progress_m,r['progress_after']);self.assertNotEqual(a.progress_m,f['model_progress']);self.assertTrue(c['goal_hit_exact']);self.assertFalse(c['model_replaces_actual']);self.assertFalse(c['actual_DONE_authorized'])
 def test_actual_candidate_independent_of_forecast(self):
  old,f,r,fixed=stored();a,_=row_candidate(old,r,fixed['line'],sum(fixed['free_profile']['ds']));bad=copy.deepcopy(f);bad['model_progress']+=100
  with self.assertRaises(LedgerStop439):compare_first(old,bad,r,fixed)
  again,_=row_candidate(old,r,fixed['line'],sum(fixed['free_profile']['ds']));self.assertEqual(a,again);self.assertFalse(old.done)
 def test_tampered_observed_progress_goal_or_claimed_hit_rejected(self):
  old,f,r,fixed=stored()
  for field,val in [('progress_after',r['progress_after']+1e-10),('progress_before',r['progress_before']+.01),('goal_before',r['goal_before']+.01),('goal_hit_actual_step',False)]:
   x=copy.deepcopy(r);x[field]=val
   with self.assertRaises(LedgerStop439):compare_first(old,f,x,fixed)
 def test_tampered_model_progress_even_inside_geometric_bound_rejected(self):
  old,f,r,fixed=stored()
  for field,val in [('model_progress',f['model_progress']+1e-10),('model_goal',f['model_goal']+1e-10),('model_age',1),('actual_root_ledger_digest','other')]:
   x=copy.deepcopy(f);x[field]=val
   with self.assertRaises(LedgerStop439):compare_first(old,x,r,fixed)
 def test_goal_boundary_reversal_not_hidden_by_continuous_bound(self):
  old=GoalLedger(4.,5.,12,50);a=old.advance_actual(ActualObservation(5.01,54));m=ForecastLedger.fork(old).advance_prediction(ModelPrediction(4.99,54))
  with self.assertRaisesRegex(LedgerStop439,'GOAL_BOUNDARY_REVERSAL'):compare_ledgers(old,a,ForecastLedger.fork(old),m,True,False,Interval(4.8,5.2),Interval.point(5.))
 def test_clock_age_deadline_DONE_and_bool_types_exact(self):
  old=GoalLedger.start(1.,50);a=old.advance_actual(ActualObservation(2.,54));m=ForecastLedger.fork(old).advance_prediction(ModelPrediction(2.,54))
  for field,value in [('last_clock_tick',55),('age_actions',0),('deadline_missed',True),('done',True),('done',0)]:
   with self.assertRaises(LedgerStop439):compare_ledgers(old,a,ForecastLedger.fork(old),replace(m,**{field:value}),False,False,Interval(1.8,2.2),Interval.point(old.goal_m))
 def test_both_deadline_missed_still_rejected(self):
  old=GoalLedger(1.,5.,12,50);a=old.advance_actual(ActualObservation(1.1,54));m=ForecastLedger.fork(old).advance_prediction(ModelPrediction(1.1,54))
  with self.assertRaisesRegex(LedgerStop439,'ACTUAL_PROGRESS_DEADLINE'):compare_ledgers(old,a,ForecastLedger.fork(old),m,False,False,Interval(1.,1.2),Interval.point(5.))
 def test_NaN_inf_model_or_observed_rejected(self):
  old,f,r,fixed=stored()
  for val in [float('nan'),float('inf')]:
   x=copy.deepcopy(f);x['predicted']['position'][0]=val
   with self.assertRaises(Exception):compare_first(old,x,r,fixed)
   x=copy.deepcopy(r);x['progress_after']=val
   with self.assertRaises(Exception):compare_first(old,f,x,fixed)
 def test_geometry_interval_derived_from_existing_tolerance_not_observed_delta(self):
  p=Projection439([[0,0],[20,0],[20,20],[0,20]],80.,.1)
  for dx,dy in [(0.05,0.),(-.1,0.),(0.,.05)]:
   a=dict(pos=[5.,.2],vel=[1.,0.]);b=dict(pos=[6.,.2],vel=[1.,0.]);t=p.transition(a,b,a,dict(pos=[6.+dx,.2+dy],vel=[1.,0.]),'FIRST_LAP','FIRST_LAP');i=p.progress_interval(Interval.point(5.),t);self.assertTrue(i.contains(p.progress(5.,t,'model')));self.assertGreater(i.hi-i.lo,.1);self.assertEqual(t['after']['position_tolerance'],.1)
 def test_diagonal_interval_and_original_arithmetic_order(self):
  p=Projection439([[0,0],[20,20],[0,40],[-20,20]],math.sqrt(800)*4,.1);a=dict(pos=[5.,5.2],vel=[1.,1.]);b=dict(pos=[6.,6.2],vel=[1.,1.]);t=p.transition(a,b,a,dict(pos=[6.03,6.18],vel=[1.,1.]),'FIRST_LAP','FIRST_LAP');self.assertTrue(p.progress_interval(Interval.point(1e6),t).contains(p.progress(1e6,t,'model')))
 def test_segment_transition_and_interior_vertex_unproved_stop(self):
  p=Projection439([[0,0],[20,0],[20,20],[0,20]],80.,.1)
  for a,m in [([19.99,.001],[20.001,.01]),([19.99,0.],[20.,-.01])]:
   with self.assertRaises(GeometryStop439):p.pair(a,m,[1.,0.],[1.,0.],'FIRST_LAP')
 def test_same_vertex_has_proven_constant_arc(self):
  p=Projection439([[0,0],[20,0],[20,20],[0,20]],80.,.1);x=p.pair([20.01,-.01],[20.02,-.02],[1.,0.],[1.,0.],'FIRST_LAP');self.assertEqual(x['branch'],'SAME_CANONICAL_VERTEX_CONSTANT');self.assertEqual(x['actual']['arc'],x['model']['arc'])
 def test_ambiguous_distinct_projection_rejected(self):
  p=Projection439([[0,0],[20,0],[20,20],[0,20]],80.,.1)
  with self.assertRaises(GeometryStop439):p.pair([10.,10.],[10.,10.],[1.,0.],[1.,0.],'FIRST_LAP')
 def test_halfperiod_cut_and_outside_position_bound_stop(self):
  p=Projection439([[0,0],[20,0],[20,20],[0,20]],80.,.1)
  with self.assertRaises(GeometryStop439):p.pair([5.,.2],[5.2,.2],[1.,0.],[1.,0.],'FIRST_LAP')
  a=dict(pos=[5.,.2],vel=[1.,0.]);b=dict(pos=[15.,19.8],vel=[-1.,0.])
  with self.assertRaises(GeometryStop439):p.transition(a,b,a,b,'FIRST_LAP','FIRST_LAP')
 def test_memory_stays_exact_for_identical_current_inputs(self):
  old,f,r,fixed=stored();x=copy.deepcopy(f);x['memory_after']['C']['s']+=1e-10
  with self.assertRaisesRegex(LedgerStop439,'MEMORY_AFTER'):compare_first(old,x,r,fixed)
 def test_restore_pre_state_copy_drift_is_not_future_physics_tolerance(self):
  old,f,r,fixed=stored();x=copy.deepcopy(f);x['raw_hull'][0]['origin_position'][0]+=.000001
  with self.assertRaisesRegex(LedgerStop439,'CURRENT_RESTORE_INPUT_DRIFT'):compare_first(old,x,r,fixed)
 def test_model_cannot_be_actual_ledger_or_advance_actual_channel(self):
  g=GoalLedger.start(1.,50)
  with self.assertRaises(Exception):g.advance_actual(ModelPrediction(2.,54,True))
  with self.assertRaises(LedgerStop439):NativeAuthority439(object(),object(),ForecastLedger.fork(g),dict(line=[],free_profile={}))
 def test_default_authority_cannot_dispatch_in_static_scope(self):
  old,f,r,fixed=stored();full=read(R/'stage437/actual_C0/final-private.json');env=stored_env(full);ctrl=SimpleNamespace(phase=lambda:'FIRST_LAP',memory=lambda:copy.deepcopy(r['memory_before']));a=NativeAuthority439(env,ctrl,old,fixed);a.prepare_before_nominal()
  with self.assertRaisesRegex(LedgerStop439,'NO_NATIVE_AUTHORIZATION'):a.dispatch(f['command'],None)
  self.assertIsNone(a.ticket);self.assertEqual(a.ledger,old)
  with self.assertRaises(AttributeError):a.ledger=ForecastLedger.fork(old)
 def test_forecast_or_other_env_ticket_cannot_commit(self):
  old,f,r,fixed=stored()
  for fake in [None,dict(model_confirmation_qualified=True),SimpleNamespace(owner=object(),env=object(),success=True)]:
   a=NativeAuthority439(object(),object(),old,fixed);a.ticket=fake
   with self.assertRaises(LedgerStop439):a.commit(f)
   self.assertEqual(a.ledger,old)
 def test_unchanged_physical_safety_and_clipping_not_waived(self):
  old,f,r,fixed=stored()
  for which in ['model','actual']:
   x=copy.deepcopy(f);y=copy.deepcopy(r)
   if which=='model':x['tires'][0]['clipped']=not x['tires'][0]['clipped']
   else:y['damage']=1.
   with self.assertRaises(LedgerStop439):compare_first(old,x,y,fixed)

 def test_command_identity_is_an_input_copy_condition(self):
  old,f,r,fixed=stored();x=copy.deepcopy(f);x['command'][0]+=.01
  with self.assertRaisesRegex(LedgerStop439,'DISPATCH_COMMAND'):compare_first(old,x,r,fixed)
 def test_synthetic_recorded_native_commit_uses_actual_not_model(self):
  # A recorded-data stand-in exercises the commit method only. No call to
  # dispatch(), env.step, model.step or world construction occurs here.
  a,old,f,r,fixed=recorded_authority()
  proof=a.commit(f);self.assertEqual(a.ledger.progress_m,r['progress_after']);self.assertNotEqual(a.ledger.progress_m,f['model_progress']);self.assertTrue(proof['actual_committed_from_native_only']);self.assertFalse(proof['model_values_committed']);self.assertIsNone(a.ticket)
  with self.assertRaises(LedgerStop439):a.commit(f)

 def test_telescoping_shared_arcs_does_not_accumulate_position_box_width(self):
  p=Projection439([[0,0],[1000,0],[1000,1000],[0,1000]],4000.,.1);bounder=Telescope439(p);actual=model=10.
  for i in range(30):
   apre=dict(pos=[10.+i,.2],vel=[1.,0.]);apost=dict(pos=[11.+i,.2],vel=[1.,0.]);mpre=dict(pos=[10.+i+(.02 if i else 0.),.2],vel=[1.,0.]);mpost=dict(pos=[11.+i+.02,.2],vel=[1.,0.]);t=p.transition(apre,apost,mpre,mpost,'FIRST_LAP','FIRST_LAP');an=p.progress(actual,t,'actual');mn=p.progress(model,t,'model');interval=bounder.advance(actual,model,an,mn,t);self.assertLess(interval.hi-interval.lo,.21);actual,model=an,mn

 def test_numeric_goal_boundary_reversal_is_not_masked_by_both_done(self):
  old=GoalLedger(4.,5.,12,50);a=old.advance_actual(ActualObservation(5.01,54,True));m=ForecastLedger.fork(old).advance_prediction(ModelPrediction(4.99,54,True))
  with self.assertRaisesRegex(LedgerStop439,'NUMERIC_GOAL_BOUNDARY'):compare_ledgers(old,a,ForecastLedger.fork(old),m,True,True,Interval(4.8,5.2),Interval.point(5.))
 def test_failed_comparison_latches_but_retains_actual_observation(self):
  a,old,f,r,fixed=recorded_authority();bad=copy.deepcopy(f);bad['model_progress']+=.001
  with self.assertRaises(LedgerStop439):a.commit(bad)
  self.assertTrue(a.halted);self.assertEqual(a.ledger.progress_m,r['progress_after']);self.assertNotEqual(a.ledger.progress_m,bad['model_progress']);self.assertFalse(a.last_verification['passed']);self.assertTrue(a.last_verification['actual_fact_retained']);self.assertEqual(len(a.rows),1)
  with self.assertRaisesRegex(LedgerStop439,'AUTHORITY_HALTED'):a.commit(f)
  self.assertEqual(len(a.rows),1)
 def test_active_deadline_exhausted_root_cannot_be_prepared(self):
  with self.assertRaises(LedgerStop439):NativeAuthority439(object(),object(),GoalLedger(1.,5.,13,50),dict())

 def test_native_fact_commit_precedes_and_does_not_require_forecast(self):
  a,old,f,r,fixed=recorded_authority();fact=a.commit_native_observation();self.assertEqual(a.ledger.progress_m,r['progress_after']);self.assertTrue(fact['native_fact_committed']);self.assertTrue(a.awaiting_verification);self.assertFalse(fact['overall_verification_success']);proof=a.verify_forecast(f);self.assertTrue(proof['overall_verification_success']);self.assertFalse(a.awaiting_verification);self.assertEqual(len(a.rows),1)
