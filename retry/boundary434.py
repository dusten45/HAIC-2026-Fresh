"""Pure prospective H13 pending/certified completion protocol. No integrator.

Geometry stays signed. Source tracker replay, not the sign of geometry, proves
registration and confirmation. Caller supplies verified physical/fidelity gates;
static source replay cannot authenticate the physics that produced its samples.
"""
import hashlib,json,math
from dataclasses import dataclass,asdict
from core.finish_line import FinishLineTracker,MIN_FORWARD_CROSSING_SPEED,MAX_LATERAL_TO_FORWARD_RATIO
from retry.planner419 import Current,Parent,GoalLedger,Evidence,Stamp,TerminalVector,TickBracket,H,TAIL_ACTION_CAP,STEER_LIMIT_F32,choose as choose419
from retry.planner419_model_ledger import ForecastLedger,ModelPrediction
from retry.early429 import GateProofs,EarlyPhysicalIneligible,encoded,decode,digest,ProtocolStop
from retry.audit431 import validate_early

class BoundaryStop(ProtocolStop):pass
PHASES=('FIRST_LAP','FINISH_CONFIRM')
def require(value,reason):
 if not value:raise BoundaryStop(reason)
def legacy_digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False).encode()).hexdigest()
def command(value):
 require(type(value) in (list,tuple) and len(value)==3,'command_shape')
 require(all(type(x) in (int,float) and math.isfinite(x) for x in value),'command_numeric')
 require(-STEER_LIMIT_F32<=value[0]<=STEER_LIMIT_F32 and 0<=value[1]<=1 and 0<=value[2]<=1,'command_domain')
 return tuple(value)
def tracker_config(value):return {k:value[k] for k in ['center','forward','half_width','half_depth','qualification_ratio']}
def safe_tick(row):
 require(row['phase'] in PHASES,'raw_controller_phase')
 require(row['damage']==0 and not row['collision'] and not row['grass'] and row['wheel_road_contacts']==4 and row['path_error_m']<=3 and row['path_error_m']>=0,'raw_safety_violation')
 require(0<=row['progress']<=1,'raw_progress_domain')

def replay(root_tracker,rows,start_clock,start_time,*,pending_event=None):
 """Replay official tracker algebra on observed POST-world samples; never physics."""
 encoded(rows);tracker=FinishLineTracker(**decode(encoded(root_tracker)));times={};clock=start_clock;t=start_time;event=pending_event
 for index,row in enumerate(rows):
  require(type(row['raw_clock']) is int and row['raw_clock']==clock+1,'raw_clock_gap')
  require(row['time']==t+1/50,'raw_time_not_exact_source_increment')
  safe_tick(row);require(tracker.finish_time_s is None,'raw_after_official_finish')
  tracker.update(tuple(row['position']),tuple(row['velocity']),row['progress'],row['time'])
  require(encoded(asdict(tracker))==encoded(row['tracker_after']),'raw_tracker_replay_mismatch')
  if event is not None:
   require(tracker.candidate_crossing_time_s==event or tracker.finish_time_s==event,'pending_cancelled_or_replaced')
  elif tracker.candidate_crossing_time_s is not None:event=tracker.candidate_crossing_time_s
  times[row['time']]=row['raw_clock'];clock=row['raw_clock'];t=row['time']
  if tracker.finish_time_s is not None:require(index==len(rows)-1,'confirmation_not_last_raw_tick')
 return asdict(tracker),times

def ledger_chain(initial,actions,posts,start_action=1,start_memory=None,first_command=None,start_tracker=None):
 ledger=initial;memory=start_memory;previous_clock=initial.last_clock_tick
 for index,a in enumerate(actions,start_action):
  require(a['action_index']==index and a['memory_before']==memory,'action_memory_chain')
  act=command(a['command']);nominal=command(a['nominal'])
  require(act==(first_command if index==1 else nominal),'foreign_recipe_or_tail_command')
  selected=[p for p in posts if previous_clock<p['raw_clock']<=a['raw_end_clock']]
  require(1<=len(selected)<=4 and selected[-1]['raw_clock']==a['raw_end_clock'],'action_raw_coverage')
  if len(selected)<4:require(selected[-1]['tracker_after']['finish_time_s'] is not None,'partial_nonterminal_action')
  require(a['memory_after']['C']['phase'] in PHASES,'action_controller_phase')
  before_tracker=start_tracker if index==start_action else next(p['tracker_after'] for p in posts if p['raw_clock']==previous_clock)
  before_phase=a['memory_before']['C']['phase'];has_pending=before_tracker['candidate_crossing_time_s'] is not None
  require(before_phase in PHASES and (before_phase!='FINISH_CONFIRM' or has_pending),'confirmation_phase_without_pending')
  require(a['memory_after']['C']['phase']==('FINISH_CONFIRM' if has_pending else before_phase),'controller_phase_not_source_act_order')
  require(all(p['phase']==a['memory_after']['C']['phase'] for p in selected),'raw_action_phase_mismatch')
  ledger=ledger.advance_prediction(ModelPrediction(a['model_progress_m'],a['raw_end_clock'],selected[-1]['tracker_after']['finish_time_s'] is not None))
  require(encoded(asdict(ledger))==encoded(a['ledger_after']),'forecast_ledger_chain')
  memory=a['memory_after'];previous_clock=a['raw_end_clock']
 require(posts and previous_clock==posts[-1]['raw_clock'],'unaccounted_raw_tail')
 return ledger,memory

@dataclass(frozen=True)
class Authority434:
 source_versions:tuple[tuple[str,str],...]
 geometry_total_length_m:float
 scope:str
 def validate(self):
  require(self.scope in ('SYNTHETIC_STATIC_ONLY','LIVE_MODEL_POST_TICK_OBSERVER'),'authority_scope')
  require(math.isfinite(self.geometry_total_length_m) and self.geometry_total_length_m>0,'geometry_length')
  require(len(self.source_versions)>0 and len(dict(self.source_versions))==len(self.source_versions),'source_version_keys')
  require(all(len(v)==64 and all(c in '0123456789abcdef' for c in v) for k,v in self.source_versions),'source_version_hash')

@dataclass(frozen=True)
class H13Boundary:
 child_id:str
 recipe:str
 context_bytes:bytes
 snapshot_bytes:bytes
 memory_bytes:bytes
 RNG_bytes:bytes
 ledger_bytes:bytes
 posts_bytes:bytes
 actions_bytes:bytes
 vector:TerminalVector
 controller_phase:str
 source_versions:tuple[tuple[str,str],...]
 proofs:GateProofs
 observer_scope:str
 def payload(self):
  # Lossless bytes codec is provided by the private receipt store, not public JSON.
  return asdict(self)
 def key(self):
  from retry.pilot420_json import json_ready
  return digest(json_ready(self.payload()))
 def context(self):
  from retry.pilot420_json import restore_bytes
  x=restore_bytes(decode(self.context_bytes));return Current(**{**x,'parent':Parent(**x['parent']),'ledger':GoalLedger(**x['ledger']),'nominal':tuple(x['nominal'])})
 def validate(self,ctx,authority,*,pending_only=True):
  authority.validate();self.proofs.require();require(self.child_id and self.source_versions==authority.source_versions and self.observer_scope==authority.scope,'child_or_source_authority')
  from retry.pilot420_json import json_ready
  require(self.context_bytes==encoded(json_ready(asdict(ctx))),'boundary_context_mismatch')
  require(ctx.gate()=='QUERY_CURRENT','current_contract_not_relaxed')
  snapshot=decode(self.snapshot_bytes);memory=decode(self.memory_bytes);ledgerdata=decode(self.ledger_bytes);posts=decode(self.posts_bytes);actions=decode(self.actions_bytes);rng=decode(self.RNG_bytes)
  require(rng and self.recipe in ctx.distinct_recipes().values(),'RNG_or_recipe_missing')
  from retry.pilot420_json import restore_bytes
  raw_rng=restore_bytes(rng);require(set(raw_rng)=={'global_pickle','digest'} and type(raw_rng['global_pickle']) is bytes and hashlib.sha256(raw_rng['global_pickle']).hexdigest()==raw_rng['digest'],'RNG_payload_hash')
  require(ctx.parent.fork_inputs()[2]['model_global_rng_digest']==raw_rng['digest'],'RNG_not_current_root')
  root_state,root_memory,_=ctx.parent.fork_inputs();root=root_state['terminal_model'];clock=ctx.parent.raw_clock_tick
  require(set(snapshot)=={'physical','finish_tracker','elapsed_raw_steps'},'full_terminal_snapshot_missing')
  require(set(snapshot['physical'])==set(root['physical']),'full_physical_schema_missing')
  require(len(snapshot['physical']['wheels'])==4,'four_wheel_snapshot_missing')
  require(len(actions)==H and len(posts)==H*4,'exact_H13_capture_required')
  require(root['finish_tracker']['finish_time_s'] is None and root['finish_tracker']['candidate_crossing_time_s'] is None,'old_root_event_not_query_witness')
  require(snapshot['elapsed_raw_steps']==root['elapsed_raw_steps']+len(posts),'elapsed_raw_steps')
  tracker,times=replay(root['finish_tracker'],posts,clock,root['physical']['actual_time'])
  require(encoded(tracker)==encoded(snapshot['finish_tracker']),'snapshot_tracker_forged')
  last=posts[-1];physical=snapshot['physical'];require(physical['actual_time']==last['time'] and physical['hull']['position']==last['position'] and physical['hull']['velocity']==last['velocity'],'snapshot_hull_clock_mismatch')
  require(physical['damage']==0 and physical['unique_tiles']/physical['road_count']==last['progress'],'snapshot_damage_progress')
  require(legacy_digest(snapshot)==self.vector.state_digest and legacy_digest(memory)==self.vector.memory_digest,'end13_snapshot_digest_mismatch')
  vals=(self.vector.speed,self.vector.yaw,self.vector.path_error,self.vector.remaining_path_m,*self.vector.wheel_omega,*self.vector.steering_joint,*self.vector.last_raw_force_ratio)
  require(all(math.isfinite(x) for x in vals) and self.vector.speed>=0 and self.vector.path_error>=0 and self.vector.path_error<=3,'terminal_kinematics')
  require(len(self.vector.wheel_omega)==4 and len(self.vector.steering_joint)==2 and len(self.vector.last_raw_force_ratio)==4 and all(x>=0 for x in self.vector.last_raw_force_ratio),'terminal_wheel_coverage')
  require(self.vector.tire_phase=='LAST_PRECLIP_PREWORLD_DIAGNOSTIC','terminal_tire_phase')
  require(self.controller_phase in PHASES and self.controller_phase==memory['C']['phase'],'observed_controller_phase')
  initial=ForecastLedger.fork(ctx.ledger);ledger,observed_memory=ledger_chain(initial,actions,posts,start_memory=root_memory,first_command=ctx.command(self.recipe),start_tracker=root['finish_tracker'])
  require(actions[0]['nominal']==list(ctx.nominal),'root_nominal_command')
  require(encoded(observed_memory)==self.memory_bytes and encoded(asdict(ledger))==self.ledger_bytes,'boundary_memory_ledger')
  require(ledger.progress_qualified() and not ledger.done and not ledger.deadline_missed,'initial_progress_not_retrospective')
  L=authority.geometry_total_length_m;require(L-ctx.ledger.progress_m==ctx.remaining_path_m and L-ledger.progress_m==self.vector.remaining_path_m,'signed_geometry_value_changed')
  if not pending_only:return tracker,times,ledger
  # Geometry does not certify finish. A registered pending crossing is necessary
  # even when remaining_path is negative, zero, or positive.
  event=tracker['candidate_crossing_time_s'];qualified=tracker['qualified_time_s']
  require(tracker['finish_time_s'] is None and event is not None and qualified is not None and tracker['departed_start_area'] and tracker['crossing_from_back'],'no_registered_pending_event')
  require(event in times and clock<times[event]<=clock+H*4 and qualified<=event<=last['time'],'pending_event_not_current_raw_tick')
  h=physical['hull'];f=tracker['forward'];right=(f[1],-f[0]);off=[h['position'][i]-tracker['center'][i] for i in range(2)];lon=sum(off[i]*f[i] for i in range(2));lat=sum(off[i]*right[i] for i in range(2));vf=sum(h['velocity'][i]*f[i] for i in range(2));vs=sum(h['velocity'][i]*right[i] for i in range(2))
  require(0<=lon<tracker['half_depth'] and abs(lat)<=tracker['half_width'] and vf>MIN_FORWARD_CROSSING_SPEED and abs(vs)<=MAX_LATERAL_TO_FORWARD_RATIO*vf,'source_pending_corridor_velocity')
  return tracker,times,ledger
 @property
 def finish_ticks(self):return None
 @property
 def actual_DONE_allowed(self):return False
 @property
 def actual_execution_allowed(self):return False
 @property
 def promotion_allowed(self):return False

def capture_h13(ctx,authority,*,child_id,recipe,snapshot,memory,rng,ledger,posts,actions,vector,proofs):
 from retry.pilot420_json import json_ready
 result=H13Boundary(child_id,recipe,encoded(json_ready(asdict(ctx))),encoded(snapshot),encoded(memory),encoded(json_ready(rng)),encoded(asdict(ledger)),encoded(posts),encoded(actions),vector,memory['C']['phase'],authority.source_versions,proofs,authority.scope)
 result.validate(ctx,authority,pending_only=False);return result

@dataclass(frozen=True)
class TailRecord:
 child_id:str
 boundary_key:str
 source_versions:tuple[tuple[str,str],...]
 posts_bytes:bytes
 actions_bytes:bytes
 snapshot_bytes:bytes
 memory_bytes:bytes
 RNG_bytes:bytes
 ledger_bytes:bytes
 proofs:GateProofs
 policy:str='SIGNED_C_NOMINAL'
 outcome:str='FINISHED'

@dataclass(frozen=True)
class Completion434:
 boundary:H13Boundary
 tail:TailRecord
 authority:Authority434
 commit_path:str
 commit_digest:str
 def __post_init__(self):self.authenticate(self.boundary.context())
 @property
 def recipe(self):return self.boundary.recipe
 @property
 def tail_status(self):return 'FINISHED'
 @property
 def actual_DONE_allowed(self):return False
 @property
 def actual_execution_allowed(self):return False
 @property
 def promotion_allowed(self):return False
 @property
 def finish_ticks(self):
  root=decode(self.boundary.context_bytes)['parent']['raw_clock_tick'];posts=decode(self.boundary.posts_bytes);event=decode(self.boundary.snapshot_bytes)['finish_tracker']['candidate_crossing_time_s'];tick=next(p['raw_clock'] for p in posts if p['time']==event)-root;return TickBracket(tick-1,tick)
 def admissible13(self):return True
 def finished_witness(self):return True
 def authenticate(self,ctx):
  from retry.receipt421_io import load_receipt,receipt_digest
  sealed=load_receipt(self.commit_path);require(receipt_digest(sealed)==self.commit_digest,'H13_commit_modified')
  from retry.pilot420_json import json_ready
  require(encoded(json_ready(sealed))==encoded(json_ready(self.boundary.payload())),'H13_not_sealed_before_continuation')
  tracker,times,ledger=self.boundary.validate(ctx,self.authority);self.tail.proofs.require();require(self.tail.outcome=='FINISHED','unsafe_or_censored_tail_not_completion')
  require(self.tail.child_id==self.boundary.child_id and self.tail.boundary_key==self.boundary.key() and self.tail.source_versions==self.authority.source_versions and self.tail.policy=='SIGNED_C_NOMINAL','tail_different_child_boundary_source_or_policy')
  posts=decode(self.tail.posts_bytes);actions=decode(self.tail.actions_bytes);snapshot=decode(self.tail.snapshot_bytes);memory=decode(self.tail.memory_bytes);rng=decode(self.tail.RNG_bytes)
  require(0<len(actions)<=TAIL_ACTION_CAP and 0<len(posts)<=4*len(actions),'tail_cap_or_missing')
  require(encoded(rng)==self.boundary.RNG_bytes,'tail_RNG_changed')
  old=decode(self.boundary.snapshot_bytes);last_initial=decode(self.boundary.posts_bytes)[-1];event=tracker['candidate_crossing_time_s']
  final,_=replay(tracker,posts,last_initial['raw_clock'],last_initial['time'],pending_event=event)
  require(final['finish_time_s']==event and final['candidate_crossing_time_s'] is None and not final['crossing_from_back'],'official_confirmation_missing_or_other_event')
  require(tracker_config(final)==tracker_config(tracker),'finish_tracker_geometry_changed')
  require(snapshot['finish_tracker']==final and snapshot['physical']['actual_time']==posts[-1]['time'] and snapshot['physical']['hull']['position']==posts[-1]['position'] and snapshot['physical']['hull']['velocity']==posts[-1]['velocity'],'confirmation_snapshot_mismatch')
  require(snapshot['elapsed_raw_steps']==old['elapsed_raw_steps']+len(posts) and set(snapshot['physical'])==set(old['physical']) and snapshot['physical']['damage']==0,'confirmation_full_state_or_damage')
  final_ledger,mem=ledger_chain(ledger,actions,posts,start_action=H+1,start_memory=decode(self.boundary.memory_bytes),start_tracker=tracker)
  require(encoded(asdict(final_ledger))==self.tail.ledger_bytes and final_ledger.done and encoded(mem)==self.tail.memory_bytes and memory['C']['phase'] in PHASES,'confirmation_memory_ledger')
  return self

def choose(ctx,receipts,optimize=True):
 for e in receipts.values():
  if type(e) is EarlyPhysicalIneligible:validate_early(e)
  elif type(e) not in (Evidence,Completion434):raise BoundaryStop('unknown_completion_type')
 return choose419(ctx,receipts,optimize)
