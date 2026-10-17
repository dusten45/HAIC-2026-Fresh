"""Registered pending parent routing; never a planner receipt or actual DONE."""
import hashlib,math
from dataclasses import dataclass,asdict
import numpy as np
from retry.boundary434 import require,encoded,decode,digest,legacy_digest,replay,command,Authority434
from retry.planner419 import Current,Parent,GoalLedger,TickBracket
from retry.planner419_model_ledger import ForecastLedger,ModelPrediction
from retry.early429 import GateProofs
from retry.pilot420_json import json_ready,restore_bytes
from retry.headroom413_run import metrics
from retry.guardian426_confirmed import guardian_finish

@dataclass(frozen=True)
class PendingParent436:
 parent_token:str
 context_bytes:bytes
 snapshot_bytes:bytes
 memory_before_bytes:bytes
 memory_after_nominal_bytes:bytes
 RNG_bytes:bytes
 forecast_ledger_bytes:bytes
 history_root_bytes:bytes
 history_initial_ledger_bytes:bytes
 history_posts_bytes:bytes
 history_actions_bytes:bytes
 line_bytes:bytes
 authority:Authority434
 proofs:GateProofs
 history_provenance:str
 def key(self):return digest(json_ready(asdict(self)))
 def context(self):
  x=restore_bytes(decode(self.context_bytes));return Current(**{**x,'parent':Parent(**x['parent']),'ledger':GoalLedger(**x['ledger']),'nominal':tuple(x['nominal'])})
 @property
 def planner_ranking_eligible(self):return False
 @property
 def actual_execution_allowed(self):return False
 @property
 def actual_DONE_allowed(self):return False
 @property
 def parent_done(self):return False
 @property
 def finish_ticks(self):return None
 def validate(self,expected_parent_token,expected_ctx=None):
  self.proofs.require();self.authority.validate();require(self.parent_token==expected_parent_token and bool(expected_parent_token),'pending_parent_identity')
  ctx=self.context()
  if expected_ctx is not None:require(self.context_bytes==encoded(json_ready(asdict(expected_ctx))),'pending_other_current_context')
  command(ctx.nominal);require(ctx.phase=='FINISH_CONFIRM' and not ctx.official_finished and not ctx.ledger.done and not ctx.ledger.deadline_missed,'pending_current_phase_or_done')
  require(ctx.projection_qualified and ctx.input_restore_qualified and ctx.current_safety_qualified,'pending_current_gates')
  require(all(math.isfinite(x) for x in [ctx.remaining_path_m,ctx.sigma,ctx.target_r,ctx.body_forward]) and ctx.target_r>0 and ctx.body_forward>=-.1,'pending_current_numeric')
  state=decode(self.snapshot_bytes);before=decode(self.memory_before_bytes);after=decode(self.memory_after_nominal_bytes);ledger=ForecastLedger(**decode(self.forecast_ledger_bytes));root=decode(self.history_root_bytes);posts=decode(self.history_posts_bytes);actions=decode(self.history_actions_bytes);source,ctx_before,rng_ctx=ctx.parent.fork_inputs()
  require(encoded(source['terminal_model'])==self.snapshot_bytes and encoded(ctx_before)==self.memory_before_bytes,'pending_snapshot_or_before_memory_not_current')
  require(before['C']['phase'] in ['FIRST_LAP','FINISH_CONFIRM'] and after['C']['phase']=='FINISH_CONFIRM','pending_phase_manipulation')
  rng=restore_bytes(decode(self.RNG_bytes));require(type(rng['global_pickle']) is bytes and hashlib.sha256(rng['global_pickle']).hexdigest()==rng['digest']==rng_ctx['model_global_rng_digest'],'pending_RNG_binding')
  require(ledger.last_clock_tick==ctx.parent.raw_clock_tick==ctx.ledger.last_clock_tick and not ledger.done and not ledger.deadline_missed,'pending_clock_or_ledger_done')
  view=GoalLedger(ledger.progress_m,ledger.goal_m,ledger.age_actions,ledger.last_clock_tick,ledger.deadline_missed,ledger.done);require(view==ctx.ledger and ledger.actual_root_digest==source['immutable_actual_root_digest'],'pending_forecast_actual_root_binding')
  require(self.authority.geometry_total_length_m-ledger.progress_m==ctx.remaining_path_m,'pending_geometry_signed_value_changed')
  require(dict(self.authority.source_versions)['geometry_line_json']==hashlib.sha256(self.line_bytes).hexdigest(),'pending_geometry_source')
  initial=ForecastLedger(**decode(self.history_initial_ledger_bytes));require(initial.actual_root_digest==ledger.actual_root_digest and not initial.done and not initial.deadline_missed,'pending_history_root_ledger')
  require(root['finish_tracker']['candidate_crossing_time_s'] is None and root['finish_tracker']['finish_time_s'] is None,'pending_old_root_event_or_finish')
  require(posts and actions,'pending_missing_observed_history')
  final,times=replay(root['finish_tracker'],posts,initial.last_clock_tick,root['physical']['actual_time'])
  require(encoded(final)==encoded(state['finish_tracker']) and state['elapsed_raw_steps']==root['elapsed_raw_steps']+len(posts),'pending_full_tracker_or_elapsed_history')
  last=posts[-1];physical=state['physical'];require(physical['actual_time']==last['time'] and physical['hull']['position']==last['position'] and physical['hull']['velocity']==last['velocity'] and physical['damage']==0 and physical['unique_tiles']/physical['road_count']==last['progress'],'pending_full_physical_history')
  require(last['raw_clock']==ledger.last_clock_tick,'pending_last_raw_clock')
  memory=actions[0]['memory_before'];model=initial;clock=initial.last_clock_tick;offset=0;line=np.asarray(decode(self.line_bytes))
  for i,a in enumerate(actions,1):
   row=a['frozen_row'];require(a['action_index']==i and a['memory_before']==memory and a['command']==row['command'],'pending_history_command_memory_chain')
   nominal=command(a['nominal']);require(command(a['command']) in [nominal,(nominal[0],1.,0.),(0.,0.,0.30000001192092896)],'pending_foreign_recipe_history')
   n=row['predicted']['raw_ticks'];chunk=posts[offset:offset+n];require(len(chunk)==n and 1<=n<=4 and chunk[-1]['raw_clock']==a['raw_end_clock'],'pending_action_raw_join')
   require(row['memory_after']==a['memory_after'] and all(p['phase']==a['memory_after']['C']['phase'] for p in chunk),'pending_observed_phase_history')
   _,flags=metrics(row['predicted'],row['tires'],row['raw_hull'],line,row['memory_after']['C']['phase']);require(not flags and not row['safety'] and not row['predicted']['finished'],'pending_unsafe_or_already_finished_history')
   clock=a['raw_end_clock'];model=model.advance_prediction(ModelPrediction(a['model_progress_m'],clock,False));require(encoded(asdict(model))==encoded(a['ledger_after']),'pending_history_forecast_chain');memory=a['memory_after'];offset+=n
  require(offset==len(posts) and encoded(memory)==self.memory_before_bytes and encoded(asdict(model))==self.forecast_ledger_bytes,'pending_current_memory_ledger_not_last_action')
  event=final['candidate_crossing_time_s'];qualified=final['qualified_time_s'];require(final['finish_time_s'] is None and event is not None and qualified is not None and final['departed_start_area'] and final['crossing_from_back'],'pending_not_registered')
  require(event in times and initial.last_clock_tick<times[event]<=ledger.last_clock_tick and qualified<=event<=physical['actual_time'],'pending_event_not_recorded_or_qualified')
  h=physical['hull'];f=final['forward'];right=[f[1],-f[0]];off=[h['position'][i]-final['center'][i] for i in range(2)];lon=sum(off[i]*f[i] for i in range(2));lat=sum(off[i]*right[i] for i in range(2));vf=sum(h['velocity'][i]*f[i] for i in range(2));vs=sum(h['velocity'][i]*right[i] for i in range(2));require(0<=lon<final['half_depth'] and abs(lat)<=final['half_width'] and vf>1e-4 and abs(vs)<=4*vf,'pending_source_corridor_velocity')
  return dict(gate='REGISTERED_PENDING_GUARDIAN_ONLY',event_time_s=event,event_raw_clock=times[event],current_raw_clock=ledger.last_clock_tick,planner_ranking_eligible=False,parent_done=False,actual_DONE_allowed=False)


def capture_pending(parent,ctx,before,source_versions,provenance='CURRENT436_MODEL_PARENT',history=None):
 from retry.observer435 import current_rng
 from retry.pilot420_backend import snapshot
 stream=parent.stream;stream.require_owner(parent)
 if history is None:history=dict(root=stream.root_state,ledger=stream.root_ledger,posts=stream.posts,actions=stream.actions)
 a=Authority434(tuple(sorted(source_versions.items())),parent.L,'LIVE_MODEL_POST_TICK_OBSERVER')
 p=PendingParent436(stream.child_id,encoded(json_ready(asdict(ctx))),encoded(snapshot(parent.m)),encoded(before),encoded(parent.ctrl.memory()),encoded(json_ready(current_rng())),encoded(asdict(parent.ledger)),encoded(history['root']),encoded(history['ledger']),encoded(history['posts']),encoded(history['actions']),encoded(parent.fixed['line']),a,GateProofs(True,True,True,True,True,True,True),provenance)
 p.validate(stream.child_id,ctx);return p

@dataclass(frozen=True)
class PendingGuardian436:
 pending_key:str
 parent_token:str
 child_token:str
 recipe:str
 root_state_digest:str
 root_memory_digest:str
 root_ledger_digest:str
 root_RNG_digest:str
 source_versions:tuple[tuple[str,str],...]
 posts_bytes:bytes
 rows_bytes:bytes
 final_snapshot_bytes:bytes
 certificate_bytes:bytes
 valid:bool
 @property
 def planner_ranking_eligible(self):return False
 @property
 def parent_done_allowed(self):return False
 @property
 def actual_DONE_allowed(self):return False
 def validate(self,pending,expected_child_token):
  info=pending.validate(pending.parent_token);require(self.pending_key==pending.key() and self.parent_token==pending.parent_token and self.child_token==expected_child_token and bool(expected_child_token),'guardian_other_parent_child_or_pending')
  require(self.root_RNG_digest==restore_bytes(decode(pending.RNG_bytes))['digest'],'guardian_RNG_root')
  require(self.source_versions==pending.authority.source_versions and self.root_state_digest==legacy_digest(decode(pending.snapshot_bytes)) and self.root_memory_digest==legacy_digest(decode(pending.memory_before_bytes)) and self.root_ledger_digest==pending.context().ledger.digest(),'guardian_root_memory_ledger_source')
  rows=decode(self.rows_bytes);posts=decode(self.posts_bytes);state=decode(self.final_snapshot_bytes);ctx=pending.context();require(self.valid and rows and self.recipe in ['nominal','neutralbrake'] and command(rows[0]['command'])==ctx.command(self.recipe),'guardian_baseline_recipe')
  require(rows[0]['memory_before']==decode(pending.memory_before_bytes) and not any(r['safety'] for r in rows),'guardian_unsafe_or_foreign_memory')
  model=ForecastLedger.fork(ctx.ledger);clock=ctx.parent.raw_clock_tick;line=np.asarray(decode(pending.line_bytes))
  for row in rows:
   _,flags=metrics(row['predicted'],row['tires'],row['raw_hull'],line,row['memory_after']['C']['phase']);require(not flags,'guardian_raw_safety')
   clock+=row['predicted']['raw_ticks'];model=model.advance_prediction(ModelPrediction(row['model_progress'],clock,row['predicted']['finished']))
  require(model.progress_qualified() and (len(rows)==13 or rows[-1]['predicted']['finished']),'guardian_progress_or_partial')
  root=decode(pending.snapshot_bytes);tracker,times=replay(root['finish_tracker'],posts,ctx.parent.raw_clock_tick,root['physical']['actual_time'],pending_event=info['event_time_s']);require(encoded(tracker)==encoded(state['finish_tracker']) and state['physical']['actual_time']==posts[-1]['time']==rows[-1]['predicted']['time'] and state['physical']['hull']['position']==posts[-1]['position'] and state['physical']['hull']['velocity']==posts[-1]['velocity'] and state['physical']['damage']==0,'guardian_final_tracker')
  if tracker['finish_time_s'] is not None:
   clocks={p['time']:p['raw_clock']-ctx.parent.raw_clock_tick for p in posts};cert=guardian_finish(root,'FINISH_CONFIRM',rows[-1]['predicted'],tracker,clocks);require(encoded(cert)==self.certificate_bytes and cert['event_time_s']==info['event_time_s'] and not cert['actual_done_allowed'] and not cert['planner_ranking_eligible'],'guardian_future_confirmation_not_same_event')
  else:require(tracker['candidate_crossing_time_s']==info['event_time_s'] and decode(self.certificate_bytes) is None,'guardian_pending_cancelled_or_fake_certificate')
  return self

def guardian_proof(pending,child,valid):
 from retry.pilot420_backend import snapshot
 child.stream.require_owner(child)
 proof=PendingGuardian436(pending.key(),pending.parent_token,child.stream.child_id,child.recipe,child.root_state_digest,child.root_memory_digest,child.root_ledger.digest(),child.stream.root_rng['digest'],child.stream.authority.source_versions,encoded(child.stream.posts),encoded(child.rows),encoded(snapshot(child.m)),encoded(child.guardian_certificate),valid)
 proof.validate(pending,child.stream.child_id);return proof

def verify_parent_step(pending,parent,native_before,*,episode_bracket=True):
 from retry.pilot420_backend import snapshot
 parent.stream.require_owner(parent);pending.validate(parent.stream.child_id);require(parent.m.native_ticks-native_before==parent.rows[-1]['predicted']['raw_ticks'] and parent.m.native_ticks>native_before,'parent_own_integration_required')
 old=decode(pending.snapshot_bytes);row=parent.rows[-1];state=snapshot(parent.m);event=old['finish_tracker']['candidate_crossing_time_s'];q=row['predicted'];require(q['time']>old['physical']['actual_time'] and parent.ledger.last_clock_tick==pending.context().ledger.last_clock_tick+q['raw_ticks'],'parent_own_clock_advance')
 require(not row['safety'],'parent_own_step_unsafe')
 if q['finished']:
  require(parent.m.finished and parent.status=='FINISHED' and parent.ledger.done and state['finish_tracker']['finish_time_s']==event==q['finish_time_s'],'parent_own_official_confirmation')
  if episode_bracket:
   initial=ForecastLedger(**decode(pending.history_initial_ledger_bytes));times={p['time']:p['raw_clock'] for p in decode(pending.history_posts_bytes)};tick=times[event]-initial.last_clock_tick;require(parent.finish_ticks==TickBracket(tick-1,tick),'parent_official_event_bracket_changed')
  else:require(parent.finish_ticks is None,'qualification_must_not_recertify_old_lap')
 else:require(not parent.ledger.done and state['finish_tracker']['candidate_crossing_time_s']==event and state['finish_tracker']['finish_time_s'] is None,'parent_pending_cancelled_or_future_DONE')
 return dict(parent_own_raw_ticks=q['raw_ticks'],official_finished=bool(q['finished']),same_registered_event=True,model_parent_done=parent.ledger.done,guardian_prediction_did_not_commit=True,actual_DONE_allowed=False)
