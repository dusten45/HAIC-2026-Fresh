"""Pure state-based planning protocol. No simulator, model integration or actuator.

Long C nominal continuations are model-only witnesses, never actual safety proof.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from enum import Enum
import hashlib,json,math
from typing import Mapping

H=13
TAIL_ACTION_CAP=308  # Existing411 computational cap, not a physical horizon guarantee.
RAW_HZ=50
PROGRESS_GOAL_M=3.24
BRAKE_03_F32=0.30000001192092896
STEER_LIMIT_F32=0.4000000059604645
RECIPES=('nominal','fullgas','neutralbrake')
FORBIDDEN_CURRENT_KEYS=frozenset({'future_trace','future_observation','future_result','next_actual_state','tail_outcomes','lap_ms'})
class ContractError(ValueError):pass

def _encoded(value):
 def check(z):
  if isinstance(z,dict):
   if FORBIDDEN_CURRENT_KEYS.intersection(z):raise ContractError('future_or_outcome_in_current_input')
   for v in z.values():check(v)
  elif isinstance(z,(list,tuple)):
   for v in z:check(v)
 check(value)
 return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _hash(value):return hashlib.sha256(value).hexdigest()
@dataclass(frozen=True)
class Stamp:
 state:str
 memory_before_nominal:str
 rng:str
 raw_clock_tick:int
@dataclass(frozen=True)
class Parent:
 state_bytes:bytes
 memory_bytes:bytes
 rng_bytes:bytes
 raw_clock_tick:int
 @classmethod
 def current(cls,state,memory_before_nominal,rng,raw_clock_tick):
  if type(raw_clock_tick) is not int or raw_clock_tick<0:raise ContractError('integer_current_clock_required')
  return cls(_encoded(state),_encoded(memory_before_nominal),_encoded(rng),raw_clock_tick)
 def stamp(self):return Stamp(_hash(self.state_bytes),_hash(self.memory_bytes),_hash(self.rng_bytes),self.raw_clock_tick)
 def fork_inputs(self):return tuple(json.loads(x) for x in (self.state_bytes,self.memory_bytes,self.rng_bytes))
@dataclass(frozen=True)
class ActualObservation:
 progress_m:float
 raw_clock_tick:int
 official_finished:bool=False
 provenance:str='ACTUAL_COMMITTED'
@dataclass(frozen=True)
class GoalLedger:
 progress_m:float
 goal_m:float
 age_actions:int
 last_clock_tick:int
 deadline_missed:bool=False
 done:bool=False
 def __post_init__(self):
  if not all(math.isfinite(x) for x in (self.progress_m,self.goal_m)) or type(self.age_actions) is not int or not 0<=self.age_actions<=H or type(self.last_clock_tick) is not int or self.last_clock_tick<0:raise ContractError('invalid_actual_ledger')
 @classmethod
 def start(cls,progress_m,raw_clock_tick):return cls(progress_m,progress_m+PROGRESS_GOAL_M,0,raw_clock_tick)
 def digest(self):return _hash(_encoded(self.__dict__))
 def advance_actual(self,observed:ActualObservation):
  if observed.provenance!='ACTUAL_COMMITTED':raise ContractError('forecast_cannot_advance_actual_ledger')
  if self.done or self.deadline_missed:raise ContractError('advance_after_done_or_missed_deadline')
  if type(observed.raw_clock_tick) is not int or not 1<=observed.raw_clock_tick-self.last_clock_tick<=4:raise ContractError('normal_actual_1_to_4_tick_contract')
  if not math.isfinite(observed.progress_m):raise ContractError('nonfinite_progress')
  age=self.age_actions+1
  if observed.official_finished:return replace(self,progress_m=observed.progress_m,last_clock_tick=observed.raw_clock_tick,done=True)
  if observed.progress_m>=self.goal_m:return GoalLedger.start(observed.progress_m,observed.raw_clock_tick)
  return replace(self,progress_m=observed.progress_m,age_actions=age,last_clock_tick=observed.raw_clock_tick,deadline_missed=age>=H)
@dataclass(frozen=True)
class Current:
 parent:Parent
 ledger:GoalLedger
 policy_digest:str
 nominal:tuple[float,float,float]
 phase:str
 target_r:float
 sigma:float
 body_forward:float
 remaining_path_m:float
 projection_qualified:bool=True
 input_restore_qualified:bool=True
 current_safety_qualified:bool=True
 official_finished:bool=False
 def validate(self):
  if self.parent.raw_clock_tick!=self.ledger.last_clock_tick:raise ContractError('parent_and_actual_ledger_clock_mismatch')
  if len(self.nominal)!=3 or not all(math.isfinite(x) for x in self.nominal):raise ContractError('nominal_nonfinite')
  if not(-STEER_LIMIT_F32<=self.nominal[0]<=STEER_LIMIT_F32 and 0<=self.nominal[1]<=1 and 0<=self.nominal[2]<=1):raise ContractError('nominal_outside_frozen_domain')
  if not all(math.isfinite(x) for x in (self.target_r,self.sigma,self.body_forward,self.remaining_path_m)):raise ContractError('nonfinite_context')
  if self.remaining_path_m<0 and not(self.official_finished or self.ledger.done):raise ContractError('past_first_lap_path_domain')
 def gate(self):
  self.validate()
  if self.official_finished or self.ledger.done:return 'DONE_NO_ACTION'
  if self.ledger.deadline_missed:return 'STOP_PROGRESS_DEADLINE'
  if not self.input_restore_qualified:return 'STOP_RESTORE'
  if not self.projection_qualified:return 'STOP_PROJECTION_NO_EPSILON'
  if not self.current_safety_qualified or self.sigma<-.1 or self.body_forward<-.1:return 'STOP_CURRENT_SAFETY'
  if self.phase!='FIRST_LAP':return 'EXISTING_PHASE_ONLY_NOT_A_NEW_FALLBACK'
  if self.target_r<=0:return 'STOP_POSITIVE_TARGET_DOMAIN'
  if self.remaining_path_m==0:return 'STOP_FIRST_LAP_PATH_DOMAIN'
  return 'QUERY_CURRENT'
 def command(self,recipe):
  if recipe=='nominal':return self.nominal
  if recipe=='fullgas':return(self.nominal[0],1.,0.)
  if recipe=='neutralbrake':return(0.,0.,BRAKE_03_F32)
  raise ContractError('recipe_not_in_frozen_three')
 def distinct_recipes(self):
  commands={};aliases={}
  for name in RECIPES:
   command=self.command(name)
   if command not in commands:commands[command]=name
   aliases[name]=commands[command]
  return aliases
@dataclass(frozen=True)
class TickBracket:
 lo:int
 hi:int
 def __post_init__(self):
  if type(self.lo) is not int or type(self.hi) is not int or self.lo<0 or self.hi<self.lo:raise ContractError('integer_raw_tick_bracket_required')
 def seconds(self):return(self.lo/RAW_HZ,self.hi/RAW_HZ)
 def gain_over(self,other):return(other.lo-self.hi,other.hi-self.lo)
@dataclass(frozen=True)
class TerminalVector:
 speed:float
 yaw:float
 path_error:float
 wheel_omega:tuple[float,float,float,float]
 steering_joint:tuple[float,float]
 last_raw_force_ratio:tuple[float,float,float,float]
 remaining_path_m:float
 state_digest:str
 memory_digest:str
 tire_phase:str='LAST_PRECLIP_PREWORLD_DIAGNOSTIC'
 def validate(self,allow_finished=False):
  vals=(self.speed,self.yaw,self.path_error,self.remaining_path_m,*self.wheel_omega,*self.steering_joint,*self.last_raw_force_ratio)
  if not all(math.isfinite(x) for x in vals) or self.speed<0 or self.path_error<0 or (self.remaining_path_m<0 and not allow_finished):raise ContractError('invalid_terminal_vector')
  if len(self.wheel_omega)!=4 or len(self.steering_joint)!=2 or len(self.last_raw_force_ratio)!=4:raise ContractError('tire_joint_coverage')
  if not self.state_digest or not self.memory_digest:raise ContractError('full_end_snapshot_and_memory_required')
  if any(x<0 for x in self.last_raw_force_ratio):raise ContractError('negative_force_magnitude_ratio')
  # q>1 is allowed; clipping is not an independent veto.
@dataclass(frozen=True)
class Evidence:
 recipe:str
 root:Stamp
 ledger_digest:str
 policy_digest:str
 first_command:tuple[float,float,float]
 initial_actions:int
 restore_ok:bool
 independent_repeat_ok:bool
 parent_unchanged:bool
 numerical_fidelity_ok:bool
 safety_ok:bool
 progress_deadline_ok:bool
 end13:TerminalVector
 tail_status:str='UNQUERIED'  # FINISHED, CENSORED, UNSAFE, INFEASIBLE or UNQUERIED.
 finish_ticks:TickBracket|None=None
 official_finish_qualified:bool=False
 tail_policy:str='SIGNED_C_NOMINAL'
 tail_time_provenance:str='SOURCE_RAW_CLOCK'
 max_tail_actions:int=TAIL_ACTION_CAP
 tail_actions_integrated:int=0
 checkpoint_actions:tuple[int,...]=()
 long_tail_physics_qualified:bool=False
 local_exit_ticks:TickBracket|None=None
 def authenticate(self,ctx:Current):
  if self.recipe not in RECIPES or self.root!=ctx.parent.stamp() or self.ledger_digest!=ctx.ledger.digest() or self.policy_digest!=ctx.policy_digest:raise ContractError('stale_or_foreign_branch_evidence')
  if self.first_command!=ctx.command(self.recipe):raise ContractError('wrong_recipe_or_new_steering_pedal')
  if type(self.initial_actions) is not int or not 1<=self.initial_actions<=H:raise ContractError('changed_initial_horizon')
  if self.initial_actions<H and not(self.tail_status=='FINISHED' and self.official_finish_qualified):raise ContractError('partial_initial_requires_official_finish')
  if not all((self.restore_ok,self.independent_repeat_ok,self.parent_unchanged,self.numerical_fidelity_ok)):raise ContractError('restore_repeat_parent_or_fidelity_failure')
  self.end13.validate(allow_finished=self.tail_status=='FINISHED' and self.official_finish_qualified and self.tail_actions_integrated==0)
  if self.tail_status not in {'FINISHED','CENSORED','UNSAFE','INFEASIBLE','UNQUERIED','DOMAIN_STOP'}:raise ContractError('unknown_tail_outcome')
  if self.tail_status!='FINISHED' and self.finish_ticks is not None:raise ContractError('failed_tail_time_imputation')
  if type(self.tail_actions_integrated) is not int or not 0<=self.tail_actions_integrated<=TAIL_ACTION_CAP:raise ContractError('tail_action_cap')
  if sum(self.checkpoint_actions)!=self.tail_actions_integrated or any(type(n) is not int or not 1<=n<=H for n in self.checkpoint_actions):raise ContractError('tail_checkpoint_coverage')
  if self.finish_ticks is not None and not 0<self.finish_ticks.hi<=(self.initial_actions+self.tail_actions_integrated)*4:raise ContractError('official_finish_clock_outside_recorded_trajectory')
  if self.tail_policy!='SIGNED_C_NOMINAL' or self.tail_time_provenance!='SOURCE_RAW_CLOCK':raise ContractError('foreign_tail_or_profile_clock')
  if self.max_tail_actions!=TAIL_ACTION_CAP:raise ContractError('tail_horizon_search_forbidden')
 def admissible13(self):return self.safety_ok and self.progress_deadline_ok
 def finished_witness(self):
  return self.admissible13() and self.tail_status=='FINISHED' and self.official_finish_qualified and self.finish_ticks is not None and (self.tail_actions_integrated==0 or bool(self.checkpoint_actions))
@dataclass(frozen=True)
class Budget:
 ticks:int
 worlds:int
 def __post_init__(self):
  if type(self.ticks) is not int or type(self.worlds) is not int or self.ticks<0 or self.worlds<0:raise ContractError('nonnegative_integer_budget_required')
@dataclass(frozen=True)
class QuerySchedule:
 mode:str
 recipes:tuple[str,...]
 essential_ticks_cap:int
 qualification_extra_ticks_cap:int
 essential_worlds:int
 qualification_extra_worlds:int
 stages:tuple[str,...]
 raw_tick_unit_seconds:float=.02
@dataclass(frozen=True)
class Proposal:
 status:str
 recipe:str|None
 reason:str
 gain_rawticks:tuple[int,int]|None=None
 continuation_qualification:str='MODEL_ONLY_NOT_LONG_HORIZON_PHYSICS_PROOF'
 actual_execution_allowed:bool=False
 # Deliberately no branch end memory or actuator connection.

def query_schedule(ctx:Current,budget:Budget,qualification_duplicates=True):
 gate=ctx.gate()
 if gate!='QUERY_CURRENT':return QuerySchedule(gate,(),0,0,0,0,())
 aliases=ctx.distinct_recipes();names=tuple(dict.fromkeys(aliases.values()));n=len(names);essential=n*(H+TAIL_ACTION_CAP)*4;extra=essential if qualification_duplicates else 0;worldextra=n if qualification_duplicates else 0
 if budget.ticks>=essential+extra and budget.worlds>=n+worldextra:
  return QuerySchedule('STATE_QUERY_LONG_C_WITNESSES',names,essential,extra,n,worldextra,('CURRENT_GUARDIAN13','ALL_DISTINCT_ADMISSIBLE13','CONTINUE_EACH_LIVE_CHILD_C_TO_OFFICIAL_FINISH_OR_STOP','COMPARE_FINISH_BRACKETS'))
 # Existing guardian needs nominal plus neutral if nominal fails; no gas escape.
 guardian_names=tuple(dict.fromkeys([aliases['nominal'],aliases['neutralbrake']]));g=len(guardian_names);cost=g*H*4;dup=cost if qualification_duplicates else 0;worlddup=g if qualification_duplicates else 0
 if budget.ticks>=cost+dup and budget.worlds>=g+worlddup:return QuerySchedule('CURRENT_GUARDIAN_ONLY_NO_TIME_OPTIMIZATION',guardian_names,cost,dup,g,worlddup,('CURRENT_GUARDIAN13',))
 return QuerySchedule('STOP_QUERY_BUDGET_NO_VERIFIED_FALLBACK',(),0,0,0,0,())

def choose(ctx:Current,receipts:Mapping[str,Evidence],optimize=True):
 gate=ctx.gate()
 if gate!='QUERY_CURRENT':return Proposal(gate,None,'No new time-planner action is qualified.')
 ev=dict(receipts)
 for key,e in ev.items():
  if key!=e.recipe:raise ContractError('receipt_key_mismatch')
  e.authenticate(ctx)
 aliases=ctx.distinct_recipes()
 if any(key not in set(aliases.values()) for key in ev):raise ContractError('duplicate_semantically_identical_recipe_receipt')
 def get(name):return ev.get(name) or ev.get(aliases[name])
 nominal=get('nominal');neutral=get('neutralbrake')
 if nominal is None:return Proposal('NEED_GUARDIAN13',None,'Current nominal evidence missing, not replaced by an alternative.')
 if nominal.admissible13():baseline=nominal
 elif neutral is not None and neutral.admissible13():baseline=neutral
 elif neutral is None:return Proposal('NEED_GUARDIAN_NEUTRAL13',None,'Nominal infeasible; current neutral must be checked.')
 else:return Proposal('STOP_GUARDIAN_BOTH_INFEASIBLE',None,'Even a fast gas receipt cannot bypass current guardian infeasibility.')
 if not optimize:return Proposal('GUARDIAN_REFERENCE_ONLY',baseline.recipe,'Optional planning disabled or budget unavailable; current model-guardian reference only.')
 if not baseline.finished_witness():
  if baseline.tail_status=='UNQUERIED':return Proposal('NEED_C_CONTINUATION',baseline.recipe,'Current13 alone does not establish downstream finish cost.')
  return Proposal('GUARDIAN_REFERENCE_ONLY',baseline.recipe,'No completed nominal-C continuation witness; no remaining-time estimate.')
 # Everydistinct13-admissible alternative must receive its C tail, including locallyslowneutral.
 for name in dict.fromkeys(aliases.values()):
  e=ev.get(name)
  if e is None:return Proposal('NEED_OTHER_DISTINCT_RECIPE13',baseline.recipe,'No local speed trigger is used to discard a recipe.')
  if e.admissible13() and e.tail_status=='UNQUERIED':return Proposal('NEED_C_CONTINUATION',baseline.recipe,'Local exit/terminal vector is insufficient to rank.')
 eligible=[e for e in ev.values() if e.finished_witness()]
 alternatives=[e for e in eligible if e.recipe!=baseline.recipe and e.finish_ticks.hi<baseline.finish_ticks.lo]
 if not alternatives:return Proposal('GUARDIAN_REFERENCE_ONLY',baseline.recipe,'No strict positive guaranteed finish-time gain; overlap/tie keeps guardian.')
 # Minimize pessimistic finish among robustlybetteralternatives; no global optimum claim.
 order={name:i for i,name in enumerate(RECIPES)};best=min(alternatives,key=lambda e:(e.finish_ticks.hi,e.finish_ticks.lo,order[e.recipe]))
 return Proposal('MODEL_TIME_CHOICE',best.recipe,'Strict finish bracket dominance; finite recipe set only.',best.finish_ticks.gain_over(baseline.finish_ticks))
