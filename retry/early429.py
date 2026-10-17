"""Pure typed early physical ineligibility; unchanged419 ranking and baseline rules."""
from dataclasses import dataclass,replace,asdict
import base64,hashlib,json,math
from typing import Mapping
from retry.planner419 import Current,Evidence,Stamp,Proposal,ContractError,H,STEER_LIMIT_F32,RECIPES,choose as choose419

class ProtocolStop(ContractError):pass
PHYSICAL_REASONS=frozenset({'path_error_over3m','damage_increase','collision_or_obstacle','road_loss_or_grass'})
def encoded(value):
 try:return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
 except (ValueError,TypeError,OverflowError) as e:raise ProtocolStop('invalid_or_nonfinite_evidence') from e
def digest(value):return hashlib.sha256(encoded(value)).hexdigest()
def decode(value):
 try:return json.loads(value,parse_constant=lambda x:(_ for _ in ()).throw(ProtocolStop('nonfinite_json')))
 except (ValueError,TypeError) as e:raise ProtocolStop('invalid_json_record') from e

@dataclass(frozen=True)
class GateProofs:
 restore_ok:bool|None
 independent_repeat_ok:bool|None
 parent_unchanged:bool|None
 RNG_unchanged:bool|None
 numerical_fidelity_ok:bool|None
 phase_ok:bool|None
 domain_ok:bool|None
 technical_errors:tuple[str,...]=()
 def require(self):
  if self.technical_errors or any(v is not True for k,v in self.__dict__.items() if k!='technical_errors'):raise ProtocolStop('technical_or_unverified_gate_not_physical_rejection')

@dataclass(frozen=True)
class ObservedCost:
 required_actions:int
 repeat_actions:int
 required_raw_ticks:int
 repeat_raw_ticks:int
 model_worlds:int=2
 required_CPU_s:float|None=None
 repeat_CPU_s:float|None=None
 required_wall_s:float|None=None
 repeat_wall_s:float|None=None

@dataclass(frozen=True)
class EarlyPhysicalIneligible:
 recipe:str
 first_command:tuple[float,float,float]
 observed_actions:int
 stop_reasons:tuple[str,...]
 trace_bytes:bytes
 stop_state_bytes:bytes
 stop_memory_bytes:bytes
 cost:ObservedCost
 proofs:GateProofs
 input_state_digest:str
 input_memory_digest:str
 input_clock_tick:int
 source_sha256:tuple[str,...]
 root:Stamp|None=None
 ledger_digest:str|None=None
 policy_digest:str|None=None
 binding_scope:str='UNBOUND_RECORDED_DATA'
 requested_initial_actions:int=H
 @property
 def initial_actions(self):return self.observed_actions
 @property
 def tail_status(self):return 'EARLY_PHYSICAL_INELIGIBLE'
 @property
 def finish_ticks(self):return None
 @property
 def official_finish_qualified(self):return False
 @property
 def tail_actions_integrated(self):return 0
 @property
 def actual_execution_allowed(self):return False
 @property
 def actual_DONE_allowed(self):return False
 @property
 def promotion_allowed(self):return False
 def admissible13(self):return False
 def finished_witness(self):return False
 def validate_record(self):
  if type(self.proofs) is not GateProofs or type(self.cost) is not ObservedCost or self.recipe not in RECIPES:raise ProtocolStop('unknown_proof_cost_or_recipe_type')
  if self.requested_initial_actions!=H or type(self.observed_actions) is not int or not 1<=self.observed_actions<H:raise ProtocolStop('not_early_H13_record')
  if not self.stop_reasons or set(self.stop_reasons)-PHYSICAL_REASONS:raise ProtocolStop('nonphysical_or_domain_stop_not_ineligible')
  if self.proofs.technical_errors or any(v is False for k,v in self.proofs.__dict__.items() if k!='technical_errors'):raise ProtocolStop('failed_gate_not_ineligible')
  trace=decode(self.trace_bytes);state=decode(self.stop_state_bytes);memory=decode(self.stop_memory_bytes);encoded(trace);encoded(state);encoded(memory)
  if len(trace)!=self.observed_actions or tuple(trace[0]['command'])!=self.first_command:raise ProtocolStop('trace_count_or_command_mismatch')
  if state['finish_tracker']['finish_time_s'] is not None or any(r['predicted']['finished'] or r['predicted']['finish_time_s'] is not None for r in trace):raise ProtocolStop('official_finish_requires_normal_receipt')
  if set(trace[-1]['safety'])!=set(self.stop_reasons) or any(r['safety'] for r in trace[:-1]):raise ProtocolStop('not_first_explicit_physical_stop')
  raw=0
  for i,row in enumerate(trace):
   q=row['predicted'];n=q['raw_ticks']
   command=row['command']
   if len(command)!=3 or not(-STEER_LIMIT_F32<=command[0]<=STEER_LIMIT_F32 and 0<=command[1]<=1 and 0<=command[2]<=1):raise ProtocolStop('new_action_domain')
   if type(n) is not int or not 1<=n<=4 or (n<4 and not q['terminal']):raise ProtocolStop('invalid_raw_tick_contract')
   if row['offset']!=i+1 or len(row['tires'])!=4*n or len(row['raw_hull'])!=n:raise ProtocolStop('incomplete_measurement')
   if [(t['raw_tick'],t['wheel']) for t in row['tires']]!=[(t,w) for t in range(1,n+1) for w in range(4)]:raise ProtocolStop('measurement_phase_mismatch')
   if abs(q['time']-row['raw_hull'][0]['time']-n/50)>1e-8:raise ProtocolStop('measurement_clock_mismatch')
   if i and abs(row['raw_hull'][0]['time']-trace[i-1]['predicted']['time'])>1e-8:raise ProtocolStop('discontinuous_trace')
   raw+=n
  if state['physical']['actual_time']!=trace[-1]['predicted']['time'] or memory!=trace[-1]['memory_after']:raise ProtocolStop('stop_snapshot_memory_not_last_observation')
  c=self.cost
  if any(type(v) is not int for v in [c.required_actions,c.repeat_actions,c.required_raw_ticks,c.repeat_raw_ticks,c.model_worlds]) or (c.required_actions,c.repeat_actions,c.required_raw_ticks,c.repeat_raw_ticks,c.model_worlds)!=(self.observed_actions,self.observed_actions,raw,raw,2):raise ProtocolStop('lost_or_padded_cost')
  if any(v is not None and (not math.isfinite(v) or v<0) for v in [c.required_CPU_s,c.repeat_CPU_s,c.required_wall_s,c.repeat_wall_s]):raise ProtocolStop('invalid_measured_cost')
  if not all([self.input_state_digest,self.input_memory_digest,self.source_sha256]) or type(self.input_clock_tick) is not int:raise ProtocolStop('missing_input_identity')
  if self.input_clock_tick!=round(trace[0]['raw_hull'][0]['time']*50):raise ProtocolStop('input_clock_not_observed_root')
  return self
 def authenticate(self,ctx:Current):
  self.validate_record();self.proofs.require()
  if self.root is None or self.binding_scope not in ['LIVE_BEFORE_QUERY_CAPTURE','SYNTHETIC_STATIC_CONTEXT']:raise ProtocolStop('original_context_or_RNG_stamp_missing')
  if self.root!=ctx.parent.stamp() or self.ledger_digest!=ctx.ledger.digest() or self.policy_digest!=ctx.policy_digest:raise ProtocolStop('stale_or_foreign_early_receipt')
  if self.input_state_digest!=self.root.state or self.input_memory_digest!=self.root.memory_before_nominal or self.input_clock_tick!=self.root.raw_clock_tick:raise ProtocolStop('observed_input_does_not_match_binding')
  if self.recipe not in ctx.distinct_recipes().values() or self.first_command!=ctx.command(self.recipe):raise ProtocolStop('new_or_aliased_recipe_command')

def bind_before_query_proof(record,ctx,proofs,scope='LIVE_BEFORE_QUERY_CAPTURE'):
 """Caller must supply preintegration root and verified gates; never infers old RNG."""
 if scope not in ['LIVE_BEFORE_QUERY_CAPTURE','SYNTHETIC_STATIC_CONTEXT']:raise ProtocolStop('invalid_binding_scope')
 return replace(record,root=ctx.parent.stamp(),ledger_digest=ctx.ledger.digest(),policy_digest=ctx.policy_digest,proofs=proofs,binding_scope=scope).validate_record()

def choose(ctx:Current,receipts:Mapping[str,Evidence|EarlyPhysicalIneligible],optimize=True)->Proposal:
 if any(type(e) not in [Evidence,EarlyPhysicalIneligible] for e in receipts.values()):raise ProtocolStop('unknown_receipt_type')
 # The original baseline, guardian, missing-evidence and strict dominance logic
 # consume the typed inadmissible object directly; no synthetic13 Evidence.
 return choose419(ctx,receipts,optimize)

def to_wire(record):
 record.validate_record();d=asdict(record)
 for name in ['trace_bytes','stop_state_bytes','stop_memory_bytes']:d[name]=base64.b64encode(d[name]).decode('ascii')
 return {'schema':'early-physical-ineligible429-v1','record':d}
def from_wire(payload):
 try:
  if set(payload)!={'schema','record'} or payload['schema']!='early-physical-ineligible429-v1' or set(payload['record'])!=set(EarlyPhysicalIneligible.__dataclass_fields__):raise ProtocolStop('unknown_or_authority_added_wire_field')
  d=dict(payload['record'])
  for name in ['trace_bytes','stop_state_bytes','stop_memory_bytes']:d[name]=base64.b64decode(d[name],validate=True)
  d['first_command']=tuple(d['first_command']);d['stop_reasons']=tuple(d['stop_reasons']);d['source_sha256']=tuple(d['source_sha256']);proofs=dict(d['proofs']);proofs['technical_errors']=tuple(proofs['technical_errors']);d['proofs']=GateProofs(**proofs);d['cost']=ObservedCost(**d['cost']);d['root']=None if d['root'] is None else Stamp(**d['root'])
  return EarlyPhysicalIneligible(**d).validate_record()
 except (TypeError,ValueError,KeyError) as e:raise ProtocolStop('invalid_early_wire_record') from e
