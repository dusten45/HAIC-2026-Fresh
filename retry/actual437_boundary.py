"""Actual dispatch authority is separate from pending routing/model confirmation."""
import copy,math
from dataclasses import dataclass,asdict
from types import SimpleNamespace
import numpy as np
from retry.parent436 import PendingParent436,Authority434,encoded,decode,require
from retry.pilot420_json import json_ready
from retry.planner419 import GoalLedger,ActualObservation
from retry.planner419_model_ledger import ForecastLedger,ModelPrediction
from retry.observer435 import current_rng
from retry.capture434 import PostTrackerTap
from retry.terminal410_model import from_actual_full,snapshot
from retry.fork394_run import complete_state
from retry.branch401_gate import fingerprint
from retry.terminal409_contract import validate
from retry.early429 import GateProofs
from retry.headroom413_run import metrics
from retry.executor397 import canonical_projection
from retry.receipt421_io import save_receipt

class ActualAuthority437(Authority434):
 def validate(self):
  require(self.scope=='LIVE_ACTUAL_POST_TICK_OBSERVER437','actual_observer_scope')
  # Reuse only the source-hash/geometry checks; do not label actual posts models.
  Authority434(self.source_versions,self.geometry_total_length_m,'LIVE_MODEL_POST_TICK_OBSERVER').validate()

def live_proxy(env):
 r=env.unwrapped
 return SimpleNamespace(car=r.car,world=r.world,roads=r.road,obstacles=r.obstacles,track=r.track,tile_visited_count=r.tile_visited_count,t=r.t,damage=env.damage,off_track_counter=env.off_track_counter,finish_line_tracker=r.finish_line_tracker,elapsed_raw_steps=env.env._elapsed_steps)

@dataclass(frozen=True)
class ActualPending437:
 bridge:PendingParent436
 actual_token:str
 dispatch_count:int
 full_current_digest:str
 actual_ledger_bytes:bytes
 actual_execution_allowed:bool=False
 actual_DONE_allowed:bool=False
 def validate(self,owner,ctx):
  owner.require_live();require(self.actual_token==owner.token and self.dispatch_count==owner.dispatcher.calls and self.full_current_digest==fingerprint(complete_state(owner.env,owner.obs,owner.ctrl.memory())),'pending_actual_live_identity_or_clock')
  require(self.actual_ledger_bytes==encoded(asdict(owner.ledger)) and not self.actual_execution_allowed and not self.actual_DONE_allowed,'pending_no_actual_ledger_authority')
  require(type(self.bridge.authority) is ActualAuthority437 and self.bridge.history_provenance=='OBSERVED437_NATIVE_HISTORY_AS_ROUTING_ONLY','model_history_cannot_claim_actual_pending')
  require(len(owner.actions)==self.dispatch_count-owner.root_dispatch and owner.actual_commits==len(owner.actions),'pending_actual_history_dispatch_coverage')
  return self.bridge.validate(owner.token,ctx)

class Dispatch437:
 def __init__(self,env,token):self.env=env;self.token=token;self.calls=0;self.ticket=None
 def call(self,command,trace):
  require(self.ticket is None,'previous_actual_dispatch_unconsumed');self.calls+=1;r=self.env.unwrapped;ticket=SimpleNamespace(owner=self,env=self.env,number=self.calls,start=float(r.t),command=np.asarray(command).tolist(),posts=[],success=False)
  self.ticket=ticket
  def observed(p):
   p=copy.deepcopy(p);p['collision']=bool(r._collision_this_step);p['wheel_road_contacts']=sum(bool(w.tiles) for w in r.car.wheels);ticket.posts.append(p)
  trace.reset();trace.enable()
  try:
   with PostTrackerTap(r.finish_line_tracker,observed):out=self.env.step(command)
   ticket.success=True;ticket.end=float(r.t);return out,ticket
  finally:trace.disable()
 def check(self,ticket,row):
  require(ticket is self.ticket and ticket.owner is self and ticket.env is self.env and ticket.number==self.calls and ticket.success,'actual_dispatch_ticket_required')
  require(row['command']==ticket.command and row['pre']['time']==ticket.start and row['post']['time']==ticket.end==self.env.unwrapped.t and round((ticket.end-ticket.start)*50)==row['raw_ticks']==len(ticket.posts),'actual_dispatch_time_or_command')
  require(validate(row)['passed'],'actual_terminal_raw_contract')
  official=self.env.unwrapped.finish_time_s;tracker=self.env.unwrapped.finish_line_tracker
  require(row['completed']==(official is not None) and row['finish_time_s']==official==tracker.finish_time_s and ticket.posts[-1]['tracker_after']==tracker.__dict__,'actual_official_tracker_only')
 def consume(self,ticket):require(ticket is self.ticket,'actual_ticket_replaced');self.ticket=None

class ActualHistory437:
 def __init__(self,env,obs,ctrl,ledger,fixed,dispatcher,arm):
  self.env=env;self.obs=obs;self.ctrl=ctrl;self.ledger=ledger;self.fixed=fixed;self.dispatcher=dispatcher;self.token='ACTUAL437_'+arm+'_'+str(id(env));self.bound_env=env;self.bound_ctrl=ctrl;self.root=from_actual_full(complete_state(env,obs,ctrl.memory()));self.initial=ForecastLedger.fork(ledger);self.forecast=self.initial;self.posts=[];self.actions=[];self.root_dispatch=dispatcher.calls;self.actual_commits=0
 def require_live(self):require(self.env is self.bound_env and self.ctrl is self.bound_ctrl and self.dispatcher.env is self.env,'actual_owner_changed')
 def pending(self,ctx,before,sources):
  self.require_live();a=ActualAuthority437(tuple(sorted(sources.items())),sum(self.fixed['free_profile']['ds']),'LIVE_ACTUAL_POST_TICK_OBSERVER437')
  b=PendingParent436(self.token,encoded(json_ready(asdict(ctx))),encoded(from_actual_full(complete_state(self.env,self.obs,self.ctrl.memory()))),encoded(before),encoded(self.ctrl.memory()),encoded(json_ready(current_rng())),encoded(asdict(self.forecast)),encoded(self.root),encoded(asdict(self.initial)),encoded(self.posts),encoded(self.actions),encoded(self.fixed['line']),a,GateProofs(True,True,True,True,True,True,True),'OBSERVED437_NATIVE_HISTORY_AS_ROUTING_ONLY')
  result=ActualPending437(b,self.token,self.dispatcher.calls,fingerprint(complete_state(self.env,self.obs,self.ctrl.memory())),encoded(asdict(self.ledger)));result.validate(self,ctx);return result
 def commit(self,ticket,row,obs,frame,pending=None):
  self.require_live();self.dispatcher.check(ticket,row);old=self.ledger;clock=round(row['post']['time']*50)
  require(row['memory_before']==frame['memory_before'] and row['nominal_memory_after']==frame['memory_after']==self.ctrl.memory(),'actual_model_memory_exact')
  forecast=ForecastLedger.fork(old).advance_prediction(ModelPrediction(frame['model_progress'],old.last_clock_tick+frame['predicted']['raw_ticks'],frame['predicted']['finished']))
  require(frame['actual_root_ledger_digest']==old.digest() and frame['model_goal']==forecast.goal_m and frame['model_age']==forecast.age_actions,'selected_first_forecast_ledger_fields')
  nextledger=old.advance_actual(ActualObservation(row['progress_after'],clock,row['completed']))
  require(GoalLedger(forecast.progress_m,forecast.goal_m,forecast.age_actions,forecast.last_clock_tick,forecast.deadline_missed,forecast.done)==nextledger,'selected_first_actual_ledger_mismatch')
  require(not nextledger.deadline_missed and not row['safety'],'actual_committed_safety_or_progress')
  if pending is not None:
   require(pending.actual_token==self.token and pending.dispatch_count+1==self.dispatcher.calls and pending.actual_ledger_bytes==encoded(asdict(old)),'actual_pending_step_identity')
   event=decode(pending.bridge.snapshot_bytes)['finish_tracker']['candidate_crossing_time_s'];tracker=self.env.unwrapped.finish_line_tracker
   require((tracker.finish_time_s==event if row['completed'] else tracker.candidate_crossing_time_s==event and tracker.finish_time_s is None),'actual_pending_event_cancelled_or_changed')
  posts=[];line=np.asarray(self.fixed['line']);phase=self.ctrl.phase()
  for i,p in enumerate(ticket.posts):
   p=copy.deepcopy(p);tires=row['raw_tire_samples'][4*i:4*i+4];pre=row['raw_hull'][i];pp=canonical_projection(line,p['position'],p['velocity'],phase);pr=canonical_projection(line,pre['origin_position'],pre['origin_linear_velocity'],phase);p.update(raw_clock=old.last_clock_tick+i+1,phase=phase,damage=row['damage'],grass=any(t['grass'] for t in tires),path_error_m=max(pp['path_error_m'],pr['path_error_m']),preclip=tires,pre_hull=pre);posts.append(p)
  require(all(p['damage']==0 and not p['collision'] and not p['grass'] and p['wheel_road_contacts']==4 and p['path_error_m']<=3 for p in posts),'actual_raw_post_safety')
  self.forecast=self.forecast.advance_prediction(ModelPrediction(row['progress_after'],clock,row['completed']))
  self.posts.extend(posts);self.actions.append(dict(action_index=len(self.actions)+1,raw_end_clock=clock,memory_before=copy.deepcopy(row['memory_before']),memory_after=copy.deepcopy(row['nominal_memory_after']),command=row['command'],nominal=row['nominal'],model_progress_m=row['progress_after'],ledger_after=asdict(self.forecast),frozen_row=copy.deepcopy(frame),outcome_after='FINISHED' if row['completed'] else 'ACTIVE'))
  self.ledger=nextledger;self.obs=obs;self.actual_commits+=1;self.dispatcher.consume(ticket)
  return dict(actual_native_dispatch_verified=True,actual_commits=self.actual_commits,actual_raw_ticks=row['raw_ticks'],official_finish=nextledger.done,model_prediction_committed=False,pending_route=pending is not None,event_time_s=row['finish_time_s'],confirmation_time_s=row['post']['time'] if row['completed'] else None)
