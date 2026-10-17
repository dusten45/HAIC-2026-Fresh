"""Runtime endpoint receipts; failed/censored pending continuations have no time."""
import json,hashlib
from dataclasses import dataclass,asdict
import numpy as np
from core.finish_line import FinishLineTracker
from retry.boundary434 import *
from retry.audit431 import validate_early
from retry.pilot420_json import json_ready
from retry.receipt421_io import load_receipt,receipt_digest
from retry.headroom413_run import metrics

@dataclass(frozen=True)
class UnfinishedPending435:
 boundary:H13Boundary
 tail:TailRecord
 authority:Authority434
 commit_path:str
 commit_digest:str
 line_bytes:bytes
 def __post_init__(self):self.authenticate(self.boundary.context())
 @property
 def recipe(self):return self.boundary.recipe
 @property
 def tail_status(self):return self.tail.outcome
 @property
 def finish_ticks(self):return None
 @property
 def actual_execution_allowed(self):return False
 @property
 def actual_DONE_allowed(self):return False
 @property
 def promotion_allowed(self):return False
 def admissible13(self):return True
 def finished_witness(self):return False
 def authenticate(self,ctx):
  sealed=load_receipt(self.commit_path);require(receipt_digest(sealed)==self.commit_digest and encoded(json_ready(sealed))==encoded(json_ready(self.boundary.payload())),'unfinished_H13_seal_changed')
  initial,_,ledger=self.boundary.validate(ctx,self.authority);self.tail.proofs.require();require(self.tail.outcome in ['UNSAFE','CENSORED','INFEASIBLE'],'unfinished_outcome')
  require(self.tail.child_id==self.boundary.child_id and self.tail.boundary_key==self.boundary.key() and self.tail.source_versions==self.authority.source_versions and self.tail.policy=='SIGNED_C_NOMINAL','unfinished_foreign_stream')
  require(dict(self.authority.source_versions)['geometry_line_json']==hashlib.sha256(self.line_bytes).hexdigest(),'unfinished_geometry_source')
  posts=decode(self.tail.posts_bytes);actions=decode(self.tail.actions_bytes);require(0<len(actions)<=TAIL_ACTION_CAP and 0<len(posts)<=4*len(actions),'unfinished_cost_coverage');require(self.tail.RNG_bytes==self.boundary.RNG_bytes,'unfinished_RNG_change')
  tracker=FinishLineTracker(**initial);clock=ledger.last_clock_tick;time=decode(self.boundary.snapshot_bytes)['physical']['actual_time'];mem=decode(self.boundary.memory_bytes);line=np.asarray(decode(self.line_bytes));offset=0
  for k,a in enumerate(actions,14):
   row=a['frozen_row'];require(a['action_index']==k and a['memory_before']==mem and command(a['command'])==command(a['nominal']) and row['command']==a['command'],'unfinished_command_memory')
   count=row['predicted']['raw_ticks'];chunk=posts[offset:offset+count];require(1<=count<=4 and len(chunk)==count and (count==4 or row['predicted']['terminal']),'unfinished_raw_phase')
   for p in chunk:
    require(p['raw_clock']==clock+1 and p['time']==time+1/50,'unfinished_clock');tracker.update(tuple(p['position']),tuple(p['velocity']),p['progress'],p['time']);require(encoded(asdict(tracker))==encoded(p['tracker_after']),'unfinished_tracker_replay');clock=p['raw_clock'];time=p['time']
   _,flags=metrics(row['predicted'],row['tires'],row['raw_hull'],line,row['memory_after']['C']['phase']);require(set(flags)==set(row['safety']),'unfinished_frozen_safety')
   from retry.audit431 import physical_tokens
   physical_tokens(flags,allow_empty=True)
   if k<13+len(actions):require(not flags,'unfinished_after_first_unsafe')
   ledger=ledger.advance_prediction(ModelPrediction(a['model_progress_m'],clock,row['predicted']['finished']));require(encoded(asdict(ledger))==encoded(a['ledger_after']),'unfinished_ledger_chain');mem=a['memory_after'];offset+=count
  require(offset==len(posts) and encoded(mem)==self.tail.memory_bytes and encoded(asdict(ledger))==self.tail.ledger_bytes,'unfinished_final_memory_ledger')
  final=decode(self.tail.snapshot_bytes);require(final['finish_tracker']==asdict(tracker) and final['physical']['actual_time']==time and final['physical']['hull']['position']==posts[-1]['position'] and final['physical']['hull']['velocity']==posts[-1]['velocity'] and final['physical']['damage']==actions[-1]['frozen_row']['predicted']['damage'] and final['elapsed_raw_steps']==decode(self.boundary.snapshot_bytes)['elapsed_raw_steps']+len(posts),'unfinished_final_snapshot')
  if self.tail.outcome=='UNSAFE':require(bool(actions[-1]['frozen_row']['safety']),'unfinished_missing_physical_reason')
  else:require(not any(a['frozen_row']['safety'] for a in actions),'unfinished_unreported_unsafe')
  return self

def choose(ctx,receipts,optimize=True):
 for e in receipts.values():
  if type(e) is EarlyPhysicalIneligible:validate_early(e)
  elif type(e) not in [Evidence,Completion434,UnfinishedPending435]:raise BoundaryStop('435_unknown_receipt')
 return choose419(ctx,receipts,optimize)

def runtime_wire(e):
 require(type(e) in [Completion434,UnfinishedPending435],'runtime_wire_type');return dict(schema='runtime435-v1',kind=type(e).__name__,value=asdict(e))
def runtime_restore(wire):
 require(set(wire)=={'schema','kind','value'} and wire['schema']=='runtime435-v1','runtime_wire_schema');d=dict(wire['value']);b=dict(d['boundary']);v=dict(b['vector'])
 for key in ['wheel_omega','steering_joint','last_raw_force_ratio']:v[key]=tuple(v[key])
 b['vector']=TerminalVector(**v);b['source_versions']=tuple(tuple(x) for x in b['source_versions']);pr=dict(b['proofs']);pr['technical_errors']=tuple(pr['technical_errors']);b['proofs']=GateProofs(**pr);d['boundary']=H13Boundary(**b)
 t=dict(d['tail']);t['source_versions']=tuple(tuple(x) for x in t['source_versions']);pr=dict(t['proofs']);pr['technical_errors']=tuple(pr['technical_errors']);t['proofs']=GateProofs(**pr);d['tail']=TailRecord(**t);a=dict(d['authority']);a['source_versions']=tuple(tuple(x) for x in a['source_versions']);d['authority']=Authority434(**a)
 require(wire['kind'] in ['Completion434','UnfinishedPending435'],'runtime_wire_kind');return (Completion434 if wire['kind']=='Completion434' else UnfinishedPending435)(**d)
