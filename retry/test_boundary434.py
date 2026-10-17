"""Source tracker algebra only: synthetic pending paths are not physics runs."""
import copy,hashlib,json,tempfile,unittest
from dataclasses import asdict,replace
from pathlib import Path
from core.finish_line import FinishLineTracker
from retry.boundary434 import *
from retry.capture434 import CaptureBarrier,PostTrackerTap,seal_live_child
from retry.receipt421_io import load_receipt
from retry.pilot420_json import json_ready
from retry.preflight421 import restore_typed
from retry.test_planner419 import evidence
from retry.audit431 import choose as choose431,from_wire
R=Path('/workspace/haic-private-retry-20261009')
PROOFS=GateProofs(True,True,True,True,True,True,True)

def fixture(event_tick=52,child='synthetic-required'):
 tracker=FinishLineTracker((0.,0.),(1.,0.),4.,1.,departed_start_area=True,previous_longitudinal=-2.)
 phys=dict(hull=dict(position=[-2.,0.],velocity=[2.,0.],angle=0.,angular_velocity=0.,flags={}),wheels=[dict(body={},tiles=[],dynamics={'omega':1.},joint={'angle':0.}) for _ in range(4)],roads=[],obstacles=[],touching_obstacle_contacts=[],world_flags={},grass_friction_multiplier=1.,damage=0.,off_track_counter=0,unique_tiles=96,road_count=100,actual_time=10.,source_world_contacts=[],omitted=[])
 root=dict(physical=copy.deepcopy(phys),finish_tracker=asdict(tracker),elapsed_raw_steps=500);mem={'index':0,'laststeer':.1,'C':{'phase':'FIRST_LAP'}};rng={'global_pickle':b'SYNTHETIC_STATIC_GLOBAL_RNG','digest':hashlib.sha256(b'SYNTHETIC_STATIC_GLOBAL_RNG').hexdigest()};ledger=__import__('retry.planner419',fromlist=['GoalLedger']).GoalLedger.start(0.,500)
 parent=__import__('retry.planner419',fromlist=['Parent']).Parent.current({'terminal_model':root,'provenance':'CURRENT_MODEL_PARENT','immutable_actual_root_digest':ledger.digest()},mem,{'model_global_rng_digest':rng['digest']},500)
 ctx=Current(parent,ledger,'synthetic-policy',(.1,.3,0.),'FIRST_LAP',20.,1.,2.,25.82);authority=Authority434((('synthetic-source',hashlib.sha256(b'SOURCE_VERSION').hexdigest()),),25.82,'SYNTHETIC_STATIC_ONLY');fl=ForecastLedger.fork(ledger);posts=[];actions=[];time=10.
 for k in range(1,14):
  before=copy.deepcopy(mem);phase='FINISH_CONFIRM' if tracker.candidate_crossing_time_s is not None else mem['C']['phase'];mem=copy.deepcopy(mem);mem['index']=k;mem['C']['phase']=phase
  for j in range(4):
   tick=(k-1)*4+j+1;time+=1/50;pos=[-2.+2.*tick/event_tick,0.];vel=[2.,0.];tracker.update(tuple(pos),tuple(vel),.96,time)
   posts.append(dict(raw_clock=500+tick,time=time,position=pos,velocity=vel,progress=.96,tracker_after=asdict(tracker),phase=phase,damage=0.,collision=False,grass=False,wheel_road_contacts=4,path_error_m=.1))
  fl=fl.advance_prediction(ModelPrediction(k*2.,500+k*4,tracker.finish_time_s is not None));actions.append(dict(action_index=k,raw_end_clock=500+k*4,memory_before=before,memory_after=copy.deepcopy(mem),command=list(ctx.nominal),nominal=list(ctx.nominal),model_progress_m=k*2.,ledger_after=asdict(fl)))
 phys['hull']['position']=posts[-1]['position'];phys['actual_time']=time;snapshot=dict(physical=phys,finish_tracker=asdict(tracker),elapsed_raw_steps=552);vector=TerminalVector(2.,0.,.1,(1.,)*4,(0.,0.),(.5,)*4,authority.geometry_total_length_m-fl.progress_m,legacy_digest(snapshot),legacy_digest(mem))
 boundary=capture_h13(ctx,authority,child_id=child,recipe='nominal',snapshot=snapshot,memory=mem,rng=rng,ledger=fl,posts=posts,actions=actions,vector=vector,proofs=PROOFS)
 # Exactly one post-world tick confirms the already registered crossing.
 before=copy.deepcopy(mem);mem=copy.deepcopy(mem);mem['index']=14;mem['C']['phase']='FINISH_CONFIRM';time+=1/50;pos=[1.2,0.];tracker.update(tuple(pos),(2.,0.),.96,time);tailposts=[dict(raw_clock=553,time=time,position=pos,velocity=[2.,0.],progress=.96,tracker_after=asdict(tracker),phase='FINISH_CONFIRM',damage=0.,collision=False,grass=False,wheel_road_contacts=4,path_error_m=.1)];fl=fl.advance_prediction(ModelPrediction(28.,553,True));tailactions=[dict(action_index=14,raw_end_clock=553,memory_before=before,memory_after=mem,command=list(ctx.nominal),nominal=list(ctx.nominal),model_progress_m=28.,ledger_after=asdict(fl))];end=copy.deepcopy(snapshot);end['physical']['hull']['position']=pos;end['physical']['actual_time']=time;end['finish_tracker']=asdict(tracker);end['elapsed_raw_steps']=553
 tail=TailRecord(child,boundary.key(),authority.source_versions,encoded(tailposts),encoded(tailactions),encoded(end),encoded(mem),boundary.RNG_bytes,encoded(asdict(fl)),PROOFS)
 return ctx,authority,boundary,tail

class BoundaryTests(unittest.TestCase):
 def complete(self,ctx,authority,boundary,tail):
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);store=CaptureBarrier(td.name);key=store.seal(boundary,ctx,authority);store.begin_continuation(boundary.child_id,key);return store.complete(boundary,tail,ctx,authority),store
 def reject_boundary(self,boundary,ctx,authority):
  with self.assertRaises((ProtocolStop,ValueError,KeyError)):boundary.validate(ctx,authority)
 def test_exact_H13_boundary_event_then_confirmation(self):
  ctx,a,b,t=fixture(52);self.assertIsNone(b.finish_ticks);self.assertEqual(b.controller_phase,'FIRST_LAP');w,store=self.complete(ctx,a,b,t);self.assertEqual(w.finish_ticks,TickBracket(51,52));self.assertFalse(w.actual_DONE_allowed);self.assertFalse(w.actual_execution_allowed);self.assertFalse(w.promotion_allowed)
  initial=Path(w.commit_path).read_bytes();self.assertTrue((Path(w.commit_path).parent/(b.child_id+'-continuation-final-private.json')).exists());self.assertEqual(initial,Path(w.commit_path).read_bytes())
 def test_pending_inside_H13_and_observed_phase_not_overwritten(self):
  for event in [50,40]:
   ctx,a,b,t=fixture(event);w,_=self.complete(ctx,a,b,t);self.assertEqual(w.finish_ticks,TickBracket(event-1,event));self.assertEqual(b.controller_phase,'FIRST_LAP' if event==50 else 'FINISH_CONFIRM')
 def test_negative_geometry_without_crossing_never_witness(self):
  ctx,a,b,t=fixture();snapshot=decode(b.snapshot_bytes);snapshot['finish_tracker']['candidate_crossing_time_s']=None;snapshot['finish_tracker']['crossing_from_back']=False
  self.reject_boundary(replace(b,snapshot_bytes=encoded(snapshot),vector=replace(b.vector,state_digest=legacy_digest(snapshot))),ctx,a)
 def test_wrong_phase_and_phase_tamper(self):
  ctx,a,b,t=fixture()
  for phase in ['STOP','DONE','LAUNCH','FINISH_CONFIRM']:
   mem=decode(b.memory_bytes);mem['C']['phase']=phase;self.reject_boundary(replace(b,controller_phase=phase,memory_bytes=encoded(mem),vector=replace(b.vector,memory_digest=legacy_digest(mem))),ctx,a)
 def test_pre_root_event_and_missing_full_snapshot(self):
  ctx,a,b,t=fixture();s=decode(b.snapshot_bytes);s['finish_tracker']['candidate_crossing_time_s']=10.;self.reject_boundary(replace(b,snapshot_bytes=encoded(s),vector=replace(b.vector,state_digest=legacy_digest(s))),ctx,a)
  for snapshot in [{},{'physical':s['physical']},{**s,'physical':{'hull':s['physical']['hull']}}]:self.reject_boundary(replace(b,snapshot_bytes=encoded(snapshot)),ctx,a)
 def test_unsafe_initial_never_retroactively_certified(self):
  ctx,a,b,t=fixture()
  for field,value in [('damage',1.),('path_error_m',3.01),('collision',True),('grass',True),('wheel_road_contacts',3)]:
   rows=decode(b.posts_bytes);rows[10][field]=value;self.reject_boundary(replace(b,posts_bytes=encoded(rows)),ctx,a)
 def test_times_snapshot_digest_memory_RNG_ledger_and_source_tamper(self):
  ctx,a,b,t=fixture()
  for index,field,value in [(0,'time',10.03),(1,'raw_clock',999),(3,'path_error_m',float('nan'))]:
   posts=decode(b.posts_bytes);posts[index][field]=value
   with self.assertRaises(ProtocolStop):encoded(posts) if not math.isfinite(value) else replace(b,posts_bytes=encoded(posts)).validate(ctx,a)
  s=decode(b.snapshot_bytes);s['physical']['hull']['position'][0]+=.1;self.reject_boundary(replace(b,snapshot_bytes=encoded(s)),ctx,a)
  self.reject_boundary(replace(b,vector=replace(b.vector,state_digest='forged')),ctx,a);self.reject_boundary(replace(b,RNG_bytes=encoded({'digest':'forged'})),ctx,a);self.reject_boundary(replace(b,source_versions=(('other','0'*64),)),ctx,a)
  l=decode(b.ledger_bytes);l['progress_m']+=1.;self.reject_boundary(replace(b,ledger_bytes=encoded(l)),ctx,a)
  self.reject_boundary(replace(b,proofs=replace(PROOFS,parent_unchanged=None)),ctx,a)
 def test_future_goal_or_finish_cannot_rescue_initial_progress(self):
  ctx,a,b,t=fixture();self.reject_boundary(replace(b,proofs=replace(PROOFS,domain_ok=False)),ctx,a)
  l=decode(b.ledger_bytes);l['actual_root_goal_reached']=False;self.reject_boundary(replace(b,ledger_bytes=encoded(l)),ctx,a)
 def test_same_child_source_command_and_confirmation_required(self):
  ctx,a,b,t=fixture()
  for bad in [replace(t,child_id='other-child'),replace(t,boundary_key='other-boundary'),replace(t,source_versions=(('other','0'*64),)),replace(t,policy='OTHER'),replace(t,outcome='UNSAFE'),replace(t,outcome='CENSORED')]:
   with self.assertRaises(ProtocolStop):self.complete(ctx,a,b,bad)
  acts=decode(t.actions_bytes);acts[0]['command']=[0.,1.,0.]
  with self.assertRaises(ProtocolStop):self.complete(ctx,a,b,replace(t,actions_bytes=encoded(acts)))
 def test_confirmation_failure_different_crossing_or_clock(self):
  ctx,a,b,t=fixture()
  for change in ['unconfirmed','other_event','cancel','clock','phase']:
   posts=decode(t.posts_bytes)
   if change=='unconfirmed':posts[-1]['tracker_after']['finish_time_s']=None
   elif change=='other_event':posts[-1]['tracker_after']['finish_time_s']=posts[-1]['time']
   elif change=='cancel':posts[-1]['position']=[-2.,0.]
   elif change=='clock':posts[-1]['time']+=.02
   else:posts[-1]['phase']='FIRST_LAP'
   with self.subTest(change=change),self.assertRaises(ProtocolStop):self.complete(ctx,a,b,replace(t,posts_bytes=encoded(posts)))
 def test_unsafe_continuation_keeps_pending_time_null_and_final_record(self):
  ctx,a,b,t=fixture();posts=decode(t.posts_bytes);posts[-1]['damage']=1.;td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);store=CaptureBarrier(td.name);key=store.seal(b,ctx,a);store.begin_continuation(b.child_id,key)
  with self.assertRaises(ProtocolStop):store.complete(b,replace(t,posts_bytes=encoded(posts),outcome='UNSAFE'),ctx,a)
  self.assertIsNone(b.finish_ticks);self.assertTrue((Path(td.name)/(b.child_id+'-continuation-final-private.json')).exists())
 def test_barrier_before_tail_repeat_and_forged_seal(self):
  ctx,a,b,t=fixture();td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);store=CaptureBarrier(td.name)
  with self.assertRaises(ProtocolStop):store.begin_continuation(b.child_id,b.key())
  key=store.seal(b,ctx,a)
  with self.assertRaises(ProtocolStop):store.seal(b,ctx,a)
  store.begin_continuation(b.child_id,key)
  with self.assertRaises(ProtocolStop):store.begin_continuation(b.child_id,key)
  w=store.complete(b,t,ctx,a);Path(w.commit_path).write_text('{}')
  with self.assertRaises(ProtocolStop):w.authenticate(ctx)
 def test_required_repeat_initial_and_final_files_distinct(self):
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);store=CaptureBarrier(td.name)
  for child in ['synthetic-required','synthetic-repeat']:
   ctx,a,b,t=fixture(child=child);key=store.seal(b,ctx,a);store.begin_continuation(child,key);store.complete(b,t,ctx,a)
  self.assertEqual(len(list(Path(td.name).glob('*-private.json'))),4)
 def test_normal_positive_choice_bracket_memory_and_ledger_unchanged(self):
  count=0
  for p in (R/'stage433').glob('P_decision*-evidence-private.json'):
   payload=load_receipt(p);ctx,ev=restore_typed(copy.deepcopy(payload));ev.update({k:from_wire(x) for k,x in payload['early_evidence'].items()});before=(ctx.parent.stamp(),ctx.ledger.digest());brackets={r:e.finish_ticks for r,e in ev.items()};old=choose431(ctx,ev);new=choose(ctx,ev);self.assertEqual(new,old);self.assertEqual(before,(ctx.parent.stamp(),ctx.ledger.digest()));self.assertEqual({r:e.finish_ticks for r,e in ev.items()},brackets);count+=1
  self.assertEqual(count,41)
 def test_completed_pending_uses_same_strict_ranking_no_parent_DONE(self):
  ctx,a,b,t=fixture();w,_=self.complete(ctx,a,b,t);ev={'nominal':w,'neutralbrake':evidence(ctx,'neutralbrake',(60,61)),'fullgas':evidence(ctx,'fullgas',(49,50))};before=(ctx.parent.stamp(),ctx.ledger.digest());decision=choose(ctx,ev);self.assertEqual(decision.recipe,'fullgas');self.assertEqual(decision.gain_rawticks,(1,3));self.assertFalse(decision.actual_execution_allowed);self.assertEqual(before,(ctx.parent.stamp(),ctx.ledger.digest()))
 def test_Current_and_parent_pending_domain_not_relaxed(self):
  ctx,a,b,t=fixture()
  with self.assertRaises(Exception):choose(replace(ctx,remaining_path_m=-.1,phase='FINISH_CONFIRM'),{})
 def test_tracker_tap_preserves_original_output_and_instance_schema(self):
  target=FinishLineTracker((0.,0.),(1.,0.),4.,1.);control=copy.deepcopy(target);events=[];original=FinishLineTracker.update
  with PostTrackerTap(target,events.append):
   for i,pos in enumerate([(-2.,0.),(-.5,0.),(.2,0.),(1.2,0.)],1):self.assertEqual(target.update(pos,(2.,0.),.96,i/50),control.update(pos,(2.,0.),.96,i/50));self.assertEqual(asdict(target),asdict(control))
  self.assertIs(FinishLineTracker.update,original);self.assertEqual(len(events),4);self.assertNotIn('update',target.__dict__)
 def test_433_missing_H13_cannot_be_backfilled(self):
  failure=json.loads((R/'stage433/failure-diagnosis.json').read_text());self.assertFalse(failure['initial13_full_snapshot_retained']);self.assertFalse((R/'stage433/P_decision42_nominal_1-initial-boundary-private.json').exists());self.assertEqual(json.loads((R/'stage433/result.json').read_text())['status'],'MODEL_PILOT_STOP')

 def test_original_confirmed_at_H13_bracket_stays_event_based(self):
  ctx,a,b,t=fixture();ev={'nominal':evidence(ctx,'nominal',(49,50)),'neutralbrake':evidence(ctx,'neutralbrake',(60,61)),'fullgas':evidence(ctx,'fullgas',(51,52))};ev['nominal']=replace(ev['nominal'],end13=replace(ev['nominal'].end13,remaining_path_m=-.2));self.assertEqual(ev['nominal'].tail_actions_integrated,0);self.assertEqual(choose(ctx,ev),choose431(ctx,ev));self.assertEqual(ev['nominal'].finish_ticks,TickBracket(49,50))
 def test_valid_unconfirmed_tail_cannot_manufacture_completion(self):
  ctx,a,b,t=fixture();old=decode(b.snapshot_bytes);tracker=FinishLineTracker(**old['finish_tracker']);posts=decode(t.posts_bytes);posts[0]['position']=[.5,0.];tracker.update((.5,0.),(2.,0.),.96,posts[0]['time']);posts[0]['tracker_after']=asdict(tracker);snapshot=decode(t.snapshot_bytes);snapshot['physical']['hull']['position']=[.5,0.];snapshot['finish_tracker']=asdict(tracker);ledger=ForecastLedger(**decode(b.ledger_bytes)).advance_prediction(ModelPrediction(28.,553,False));actions=decode(t.actions_bytes);actions[0]['ledger_after']=asdict(ledger);bad=replace(t,posts_bytes=encoded(posts),actions_bytes=encoded(actions),snapshot_bytes=encoded(snapshot),ledger_bytes=encoded(asdict(ledger)),outcome='CENSORED')
  with self.assertRaises(ProtocolStop):self.complete(ctx,a,b,bad)
  self.assertIsNone(b.finish_ticks)
 def test_live_capture_connection_pauses_before_continuation_without_act_or_step(self):
  from types import SimpleNamespace
  ctx,a,b,t=fixture();state=decode(b.snapshot_bytes);mem=decode(b.memory_bytes);ledger=ForecastLedger(**decode(b.ledger_bytes));rng=__import__('retry.pilot420_json',fromlist=['restore_bytes']).restore_bytes(decode(b.RNG_bytes));fake=SimpleNamespace(initial_count=13,tail_count=0,status='ACTIVE',m=object(),ctrl=SimpleNamespace(memory=lambda:copy.deepcopy(mem)),label=b.child_id,recipe=b.recipe,ledger=ledger,end13=b.vector)
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);store=CaptureBarrier(td.name);saved,key=seal_live_child(store,fake,ctx,a,decode(b.posts_bytes),decode(b.actions_bytes),rng,PROOFS,lambda m:copy.deepcopy(state));self.assertEqual(saved,b);self.assertEqual(key,b.key());self.assertNotIn(b.child_id,store.started)
  fake.tail_count=1
  with self.assertRaises(ProtocolStop):seal_live_child(store,fake,ctx,a,decode(b.posts_bytes),decode(b.actions_bytes),rng,PROOFS,lambda m:state)
 def test_direct_invalid_completion_object_never_has_authority(self):
  ctx,a,b,t=fixture();td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);store=CaptureBarrier(td.name);key=store.seal(b,ctx,a);_,path,dig=store.pending[b.child_id]
  with self.assertRaises(ProtocolStop):Completion434(b,replace(t,outcome='CENSORED'),a,path,dig)

 def test_unsafe_raw_continuation_cannot_claim_FINISHED(self):
  ctx,a,b,t=fixture()
  for field,value in [('damage',1.),('path_error_m',3.01),('collision',True),('grass',True),('wheel_road_contacts',3)]:
   posts=decode(t.posts_bytes);posts[-1][field]=value
   with self.subTest(field=field),self.assertRaises(ProtocolStop):self.complete(ctx,a,b,replace(t,posts_bytes=encoded(posts)))
