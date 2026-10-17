"""Stored435 current-pending algebra and causal routing controls; no model world."""
import copy,json,hashlib,unittest
from dataclasses import replace,asdict
from pathlib import Path
from types import SimpleNamespace
from core.finish_line import FinishLineTracker
from retry.parent436 import *
from retry.qualify_parent436 import saved_history
from retry.receipt421_io import load_receipt
from retry.preflight421 import restore_typed
from retry.receipt435 import choose
from retry.observer435 import current_rng
from retry.early429 import GateProofs,ProtocolStop
R=Path('/workspace/haic-private-retry-20261009');PROOFS=GateProofs(True,True,True,True,True,True,True)

def stored_parent():
 stop,h=saved_history(R);x=stop['context'];ctx=Current(**{**x,'parent':Parent(**x['parent']),'ledger':GoalLedger(**x['ledger']),'nominal':tuple(x['nominal'])});plan=json.loads((R/'stage435/plan.json').read_text());fixed=json.loads(Path(plan['fixed_plan']).read_text());ledger=json.loads((R/'stage435/parent_P-private.json').read_text())['model_ledger'];a=Authority434(tuple(sorted(plan['semantic_sources'].items())),sum(fixed['free_profile']['ds']),'LIVE_MODEL_POST_TICK_OBSERVER')
 return PendingParent436('STATIC436_STORED435_PARENT',encoded(json_ready(asdict(ctx))),encoded(stop['live_parent']),encoded(stop['memory_before_nominal']),encoded(stop['memory_after_nominal']),encoded(json_ready(stop['RNG'])),encoded(ledger),encoded(h['root']),encoded(h['ledger']),encoded(h['posts']),encoded(h['actions']),encoded(fixed['line']),a,PROOFS,'STORED435_STATIC_ONLY_NO_OLD_COMPLETION')

def synthetic_guard(p):
 # Explicit synthetic straight extrapolation for tracker algebra, not physics.
 ctx=p.context();root=decode(p.snapshot_bytes);h=root['physical']['hull'];time=root['physical']['actual_time']+1/50;pos=[h['position'][i]+h['velocity'][i]/50 for i in range(2)];tracker=FinishLineTracker(**root['finish_tracker']);tracker.update(tuple(pos),tuple(h['velocity']),root['physical']['unique_tiles']/root['physical']['road_count'],time);final=copy.deepcopy(root);final['physical']['actual_time']=time;final['physical']['hull']['position']=pos;final['finish_tracker']=asdict(tracker);final['elapsed_raw_steps']+=1
 post=dict(raw_clock=ctx.parent.raw_clock_tick+1,time=time,position=pos,velocity=h['velocity'],progress=root['physical']['unique_tiles']/root['physical']['road_count'],tracker_after=asdict(tracker),phase='FINISH_CONFIRM',damage=0.,collision=False,grass=False,wheel_road_contacts=4,path_error_m=.5)
 q=dict(position=pos,velocity=h['velocity'],angle=h['angle'],damage=0.,collision=False,contact_obstacle_ids=[],wheel_road_contacts=4,raw_ticks=1,finished=tracker.finish_time_s is not None,terminal=tracker.finish_time_s is not None,time=time,finish_time_s=tracker.finish_time_s);before=decode(p.memory_before_bytes);after=decode(p.memory_after_nominal_bytes);tires=[dict(grass=False) for _ in range(4)];hulls=[dict(origin_position=h['position'],origin_linear_velocity=h['velocity'])];row=dict(command=list(ctx.nominal),memory_before=before,memory_after=after,predicted=q,tires=tires,raw_hull=hulls,safety=[],model_progress=ctx.ledger.progress_m+1.)
 cert=guardian_finish(root,'FINISH_CONFIRM',q,asdict(tracker),{})
 return PendingGuardian436(p.key(),p.parent_token,'SYNTHETIC_GUARDIAN','nominal',legacy_digest(root),legacy_digest(before),ctx.ledger.digest(),restore_bytes(decode(p.RNG_bytes))['digest'],p.authority.source_versions,encoded([post]),encoded([row]),encoded(final),encoded(cert),True)

class ParentControls(unittest.TestCase):
 def test_stored435_pending_is_guardian_only_not_general_Current(self):
  p=stored_parent();info=p.validate(p.parent_token);self.assertEqual(info['gate'],'REGISTERED_PENDING_GUARDIAN_ONLY');self.assertFalse(p.planner_ranking_eligible);self.assertFalse(p.parent_done);self.assertFalse(p.actual_DONE_allowed);self.assertIsNone(p.finish_ticks)
  with self.assertRaises(Exception):p.context().validate()
 def test_same_candidate_guardian_prediction_does_not_finish_parent(self):
  p=stored_parent();g=synthetic_guard(p);g.validate(p,g.child_token);self.assertFalse(g.parent_done_allowed);self.assertFalse(g.planner_ranking_eligible);self.assertFalse(g.actual_DONE_allowed);self.assertFalse(p.parent_done);self.assertFalse(ForecastLedger(**decode(p.forecast_ledger_bytes)).done)
 def test_other_root_child_context_source_and_RNG_rejected(self):
  p=stored_parent()
  with self.assertRaises(ProtocolStop):p.validate('OTHER_PARENT')
  with self.assertRaises(ProtocolStop):p.validate(p.parent_token,replace(p.context(),policy_digest='other'))
  g=synthetic_guard(p)
  for change in [dict(parent_token='other'),dict(child_token='other'),dict(pending_key='other'),dict(root_state_digest='other'),dict(root_memory_digest='other'),dict(root_RNG_digest='other'),dict(source_versions=(('other','0'*64),))]:
   with self.assertRaises(ProtocolStop):replace(g,**change).validate(p,g.child_token)
 def test_missing_unregistered_old_completed_cancelled_or_replaced(self):
  p=stored_parent()
  for field,value in [('candidate_crossing_time_s',None),('candidate_crossing_time_s',0.),('candidate_crossing_time_s',decode(p.snapshot_bytes)['physical']['actual_time']+.02),('finish_time_s',decode(p.snapshot_bytes)['physical']['actual_time']),('crossing_from_back',False),('departed_start_area',False),('qualified_time_s',None)]:
   s=decode(p.snapshot_bytes);s['finish_tracker'][field]=value
   with self.subTest(field=field),self.assertRaises(ProtocolStop):replace(p,snapshot_bytes=encoded(s)).validate(p.parent_token)
  h=decode(p.history_root_bytes);h['finish_tracker']['candidate_crossing_time_s']=h['physical']['actual_time']
  with self.assertRaises(ProtocolStop):replace(p,history_root_bytes=encoded(h)).validate(p.parent_token)
  posts=decode(p.history_posts_bytes);posts[-1]['tracker_after']['candidate_crossing_time_s']=None
  with self.assertRaises(ProtocolStop):replace(p,history_posts_bytes=encoded(posts)).validate(p.parent_token)
 def test_negative_value_alone_does_not_create_pending(self):
  p=stored_parent();s=decode(p.snapshot_bytes);s['finish_tracker']['candidate_crossing_time_s']=None;ctx=p.context();src,mem,rng=ctx.parent.fork_inputs();src['terminal_model']=s;ctx=replace(ctx,parent=Parent.current(src,mem,rng,ctx.parent.raw_clock_tick));bad=replace(p,context_bytes=encoded(json_ready(asdict(ctx))),snapshot_bytes=encoded(s))
  with self.assertRaises(ProtocolStop):bad.validate(p.parent_token)
 def test_wrong_phase_unsafe_snapshot_history_and_proofs_rejected(self):
  p=stored_parent()
  for phase in ['FIRST_LAP','DONE','STOP','LAUNCH']:
   after=decode(p.memory_after_nominal_bytes);after['C']['phase']=phase
   with self.assertRaises(ProtocolStop):replace(p,memory_after_nominal_bytes=encoded(after)).validate(p.parent_token)
  for field,value in [('damage',1.),('path_error_m',3.01),('grass',True),('collision',True)]:
   posts=decode(p.history_posts_bytes);posts[-1][field]=value
   with self.assertRaises(ProtocolStop):replace(p,history_posts_bytes=encoded(posts)).validate(p.parent_token)
  with self.assertRaises(ProtocolStop):replace(p,proofs=replace(PROOFS,parent_unchanged=None)).validate(p.parent_token)
 def test_guardian_other_event_phase_unsafe_and_fake_confirmation(self):
  p=stored_parent();g=synthetic_guard(p)
  for field,value in [('event_time_s',0.),('kind','BEFORE_ROOT_CONFIRMED_IN_MODEL'),('actual_done_allowed',True)]:
   cert=decode(g.certificate_bytes);cert[field]=value
   with self.assertRaises(Exception):replace(g,certificate_bytes=encoded(cert)).validate(p,g.child_token)
  rows=decode(g.rows_bytes);rows[0]['safety']=['damage_increase']
  with self.assertRaises(ProtocolStop):replace(g,rows_bytes=encoded(rows)).validate(p,g.child_token)
  rows=decode(g.rows_bytes);rows[0]['predicted']['damage']=1.
  with self.assertRaises(ProtocolStop):replace(g,rows_bytes=encoded(rows)).validate(p,g.child_token)
 def test_parent_own_step_required_before_model_DONE(self):
  p=stored_parent();fake=SimpleNamespace(stream=SimpleNamespace(child_id=p.parent_token,require_owner=lambda x:None),m=SimpleNamespace(native_ticks=3),rows=[dict(predicted=dict(raw_ticks=1))])
  with self.assertRaisesRegex(ProtocolStop,'parent_own_integration_required'):verify_parent_step(p,fake,3)
 def test_normal_Current_and_existing54choices_memory_ledger_unchanged(self):
  count=0
  for path in (R/'stage435').glob('P_decision*-evidence-private.json'):
   payload=load_receipt(path);ctx,ev=restore_typed(copy.deepcopy(payload));from retry.audit431 import from_wire;from retry.receipt435 import runtime_restore
   ev.update({r:from_wire(w) for r,w in payload['early_evidence'].items()});ev.update({r:runtime_restore(w) for r,w in payload['runtime_evidence'].items()});old=(ctx.parent.stamp(),ctx.ledger.digest());self.assertEqual(json_ready(asdict(choose(ctx,ev))),payload['decision']);self.assertEqual(old,(ctx.parent.stamp(),ctx.ledger.digest()));count+=1
  self.assertEqual(count,54)
 def test_extra_pending_worst_case_fits_total_caps(self):
  from retry.proposal429 import bounds
  b=bounds();self.assertEqual((b['total_tick_cap_required']+108,b['total_world_cap_required']+3),(519146,885));self.assertLessEqual(519146,524288);self.assertLessEqual(885,1024)
