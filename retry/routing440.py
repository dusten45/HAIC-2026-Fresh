"""Observed history in legacy routing-value schema; never actual authority."""
import copy
from dataclasses import dataclass,asdict,replace
import numpy as np
from retry.parent436 import PendingParent436,encoded
from retry.actual437_boundary import ActualAuthority437
from retry.observer435 import current_rng
from retry.pilot420_json import json_ready
from retry.early429 import GateProofs
from retry.ledger439 import require
from retry.planner419 import GoalLedger
from retry.executor397 import canonical_projection
from retry.fork394_run import complete_state
from retry.terminal410_model import from_actual_full
from retry.branch401_gate import fingerprint

@dataclass(frozen=True)
class ObservedRouteValues440:
 actual_root_digest:str
 actual_root_goal_m:float
 progress_m:float
 goal_m:float
 age_actions:int
 last_clock_tick:int
 actual_root_goal_reached:bool=False
 deadline_missed:bool=False
 done:bool=False
 @classmethod
 def from_actual_root(cls,g):return cls(g.digest(),g.goal_m,g.progress_m,g.goal_m,g.age_actions,g.last_clock_tick)
 def append_native(self,g):
  require(type(g) is GoalLedger,'ROUTING_REQUIRES_OBSERVED_ACTUAL_LEDGER');return replace(self,progress_m=g.progress_m,goal_m=g.goal_m,age_actions=g.age_actions,last_clock_tick=g.last_clock_tick,actual_root_goal_reached=self.actual_root_goal_reached or g.progress_m>=self.actual_root_goal_m or g.done,deadline_missed=g.deadline_missed,done=g.done)

@dataclass(frozen=True)
class ActualPending440:
 bridge:PendingParent436
 actual_token:str
 dispatch_count:int
 full_current_digest:str
 actual_ledger_bytes:bytes
 actual_execution_allowed:bool=False
 actual_DONE_allowed:bool=False
 def validate(self,owner,ctx):
  owner.require_live();require(self.actual_token==owner.token and self.dispatch_count==owner.native.dispatcher.calls and self.full_current_digest==fingerprint(complete_state(owner.env,owner.obs,owner.ctrl.memory())),'PENDING_LIVE_NATIVE_IDENTITY');require(self.actual_ledger_bytes==encoded(asdict(owner.ledger)) and not self.actual_execution_allowed and not self.actual_DONE_allowed,'PENDING_HAS_NO_ACTUAL_AUTHORITY');require(type(self.bridge.authority) is ActualAuthority437 and self.bridge.history_provenance=='OBSERVED440_NATIVE_ROUTING_ONLY','PENDING_NATIVE_OBSERVATION_PROVENANCE');require(len(owner.actions)==self.dispatch_count-owner.root_dispatch and owner.verified==len(owner.actions),'PENDING_VERIFIED_NATIVE_HISTORY_COVERAGE');return self.bridge.validate(owner.token,ctx)

class ObservedHistory440:
 def __init__(self,native,fixed,plan_sha,arm):
  self.native=native;self.fixed=fixed;self.bound_env=native.env;self.bound_ctrl=native.ctrl;self.token='ACTUAL440_'+plan_sha[:12]+'_'+arm;self.root=from_actual_full(complete_state(self.env,self.obs,self.ctrl.memory()));self.initial=ObservedRouteValues440.from_actual_root(self.ledger);self.values=self.initial;self.posts=[];self.actions=[];self.root_dispatch=native.dispatcher.calls;self.verified=0
 @property
 def ledger(self):return self.native.ledger
 @property
 def env(self):return self.native.env
 @property
 def ctrl(self):return self.native.ctrl
 @property
 def obs(self):return self.native.obs
 def require_live(self):
  require(self.env is self.bound_env and self.ctrl is self.bound_ctrl and not self.native.halted and not self.native.awaiting_verification and self.verified==len(self.actions),'NATIVE_HISTORY_NOT_QUALIFIED_FOR_QUERY')
 def append_native_fact(self,row,bundle):
  require(self.env is self.bound_env and self.ctrl is self.bound_ctrl and self.native.awaiting_verification,'OWN_NATIVE_FACT_AWAITING_VERIFICATION');line=np.asarray(self.fixed['line']);phase=row['nominal_memory_after']['C']['phase'];clock=bundle['ledger_before']['last_clock_tick'];posts=[]
  for i,p in enumerate(bundle['posts']):
   p=copy.deepcopy(p);tires=row['raw_tire_samples'][4*i:4*i+4];pre=row['raw_hull'][i];pp=canonical_projection(line,p['position'],p['velocity'],phase);pr=canonical_projection(line,pre['origin_position'],pre['origin_linear_velocity'],phase);p.update(raw_clock=clock+i+1,phase=phase,damage=row['damage'],grass=any(t['grass'] for t in tires),path_error_m=max(pp['path_error_m'],pr['path_error_m']),preclip=tires,pre_hull=pre);posts.append(p)
  self.values=self.values.append_native(self.ledger);post=row['post'];q=dict(position=post['pos'],velocity=post['vel'],angle=post['angle'],angular_velocity=post['yaw'],speed_m_s=post['speed'],damage=row['damage'],collision=row['collision'],contact_obstacle_ids=[],wheel_road_contacts=sum(n>0 for n in post['road_contacts']),raw_ticks=row['raw_ticks'],finished=row['completed'],terminal=row['ended'] or row['truncated'],time=post['time'],finish_time_s=row['finish_time_s']);frozen=dict(command=row['command'],memory_before=row['memory_before'],memory_after=row['nominal_memory_after'],predicted=q,tires=row['raw_tire_samples'],raw_hull=row['raw_hull'],safety=row['safety'],model_progress=self.ledger.progress_m,model_goal=self.ledger.goal_m,model_age=self.ledger.age_actions,scope='NATIVE_OBSERVATIONS_IN_LEGACY_ROUTING_SCHEMA_NOT_A_FORECAST');action=dict(action_index=len(self.actions)+1,raw_end_clock=self.ledger.last_clock_tick,memory_before=row['memory_before'],memory_after=row['nominal_memory_after'],command=row['command'],nominal=row['nominal'],model_progress_m=self.ledger.progress_m,ledger_after=asdict(self.values),frozen_row=frozen,outcome_after='NATIVE_FINISHED' if row['completed'] else 'NATIVE_FACT_PENDING_VERIFICATION');self.posts.extend(posts);self.actions.append(copy.deepcopy(action))
 def mark_verified(self):
  require(not self.native.halted and not self.native.awaiting_verification and self.verified+1==len(self.actions),'VERIFY_OBSERVED_HISTORY_SEQUENCE');self.verified+=1
 def pending(self,ctx,before,sources):
  self.require_live();a=ActualAuthority437(tuple(sorted(sources.items())),sum(self.fixed['free_profile']['ds']),'LIVE_ACTUAL_POST_TICK_OBSERVER437');bridge=PendingParent436(self.token,encoded(json_ready(asdict(ctx))),encoded(from_actual_full(complete_state(self.env,self.obs,self.ctrl.memory()))),encoded(before),encoded(self.ctrl.memory()),encoded(json_ready(current_rng())),encoded(asdict(self.values)),encoded(self.root),encoded(asdict(self.initial)),encoded(self.posts),encoded(self.actions),encoded(self.fixed['line']),a,GateProofs(True,True,True,True,True,True,True),'OBSERVED440_NATIVE_ROUTING_ONLY');p=ActualPending440(bridge,self.token,self.native.dispatcher.calls,fingerprint(complete_state(self.env,self.obs,self.ctrl.memory())),encoded(asdict(self.ledger)));p.validate(self,ctx);return p
