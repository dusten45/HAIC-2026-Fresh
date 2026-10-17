"""Explicit receipt IO injection fixture; no production meter/observer activation.

The constructor proof is synthetic metadata, never a claim of a constructed
physics world. All stored reads, including restore/factual readers, use IO.
"""
from dataclasses import asdict,dataclass
from retry.boundary434 import *
from retry.receipt421_io import receipt_digest
from retry.pilot420_json import json_ready,restore_bytes


@dataclass(frozen=True)
class Completion467:
 boundary:H13Boundary
 tail:TailRecord
 authority:Authority434
 io:object
 commit_descriptor:dict
 commit_digest:str
 def __post_init__(self):self.authenticate(self.boundary.context())
 @property
 def actual_DONE_allowed(self):return False
 @property
 def actual_execution_allowed(self):return False
 @property
 def promotion_allowed(self):return False
 @property
 def finish_ticks(self):return Completion434.finish_ticks.fget(self)
 def authenticate(self,ctx):
  sealed=self.io.read_receipt(self.commit_descriptor);require(receipt_digest(sealed)==self.commit_digest,'H13_commit_modified')
  require(encoded(json_ready(sealed))==encoded(json_ready(self.boundary.payload())),'H13_not_sealed_before_continuation')
  # Semantic block is an exact copy of434, tested by AST parity. Only the
  # explicit injected receipt read above replaces its plaintext reader.
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


class IOCapture467:
 """Single source→constructor-proof→runtime→seal→tail chain in a new IO root."""
 def __init__(self,io):
  self.io=io;self.source=None;self.constructor=None;self.runtime=None;self.pending={};self.started=set();self.closed=set()
 def source_record(self,authority):
  require(self.source is None and authority.scope=='SYNTHETIC_STATIC_ONLY','467_source_scope_or_duplicate');authority.validate()
  value=dict(source_versions=authority.source_versions,scope=authority.scope,synthetic=True,actual_execution_allowed=False)
  self.source=self.io.write_receipt('source467',value);require(self.io.read_receipt(self.source)==restore_bytes(json_ready(value)),'467_source_readback');return self.source
 def constructor_proof(self,ctx,authority):
  require(self.source is not None and self.constructor is None,'467_source_before_constructor_proof')
  source=self.io.read_receipt(self.source);require(source['source_versions']==[list(x) for x in authority.source_versions] and source['scope']==authority.scope,'467_source_binding')
  state,memory,rng=ctx.parent.fork_inputs();value=dict(source_descriptor=self.source,state=state,memory=memory,rng=rng,ledger=asdict(ctx.ledger),constructor_executed=False,synthetic_metadata_only=True)
  self.constructor=self.io.write_receipt('constructor467',value);self.restore_inputs(self.constructor);return self.constructor
 def restore_inputs(self,descriptor):
  value=self.io.read_receipt(descriptor)
  require(value['constructor_executed'] is False and value['source_descriptor']==self.source,'467_restore_source')
  source=self.io.read_receipt(value['source_descriptor'])
  require(source['scope']=='SYNTHETIC_STATIC_ONLY' and source['actual_execution_allowed'] is False,'467_restore_source_scope')
  return dict(state=value['state'],memory=value['memory'],rng=value['rng'],ledger=GoalLedger(**value['ledger']))
 def verified_runtime(self):
  runtime=self.io.read_receipt(self.runtime)
  require(runtime['constructor_descriptor']==self.constructor,'467_runtime_constructor_link')
  self.restore_inputs(runtime['constructor_descriptor'])
  return runtime
 def runtime_link(self,boundary):
  require(self.constructor is not None and self.runtime is None,'467_constructor_before_runtime')
  restored=self.restore_inputs(self.constructor);ctx=boundary.context();state,memory,rng=ctx.parent.fork_inputs()
  require(restored['state']==state and restored['memory']==memory and restored['rng']==rng and restored['ledger']==ctx.ledger,'467_runtime_restored_inputs')
  value=dict(constructor_descriptor=self.constructor,child_id=boundary.child_id,boundary_key=boundary.key(),context_bytes=boundary.context_bytes,actual_execution_allowed=False)
  self.runtime=self.io.write_receipt('runtime467',value);require(self.io.read_receipt(self.runtime)==restore_bytes(json_ready(value)),'467_runtime_readback');return self.runtime
 def seal(self,boundary,ctx,authority):
  require(self.runtime is not None and boundary.child_id not in self.pending,'467_runtime_before_unique_seal')
  runtime=self.verified_runtime();require(runtime['boundary_key']==boundary.key() and runtime['child_id']==boundary.child_id and runtime['constructor_descriptor']==self.constructor,'467_runtime_boundary_link')
  boundary.validate(ctx,authority,pending_only=False)
  if decode(boundary.snapshot_bytes)['finish_tracker']['candidate_crossing_time_s'] is not None:boundary.validate(ctx,authority)
  descriptor=self.io.write_receipt(boundary.child_id+'-H13',boundary.payload());sealed=self.io.read_receipt(descriptor)
  require(encoded(json_ready(sealed))==encoded(json_ready(boundary.payload())),'467_seal_readback')
  self.pending[boundary.child_id]=(boundary.key(),descriptor,receipt_digest(sealed));return boundary.key()
 def begin_continuation(self,child,key):
  require(child in self.pending and self.pending[child][0]==key and child not in self.started,'continuation_before_seal_or_wrong_child')
  runtime=self.verified_runtime();require(runtime['child_id']==child and runtime['boundary_key']==key,'467_continuation_runtime_binding')
  sealed=self.io.read_receipt(self.pending[child][1]);snapshot=decode(sealed['snapshot_bytes'])
  require(not(sealed['vector']['remaining_path_m']<0 and snapshot['finish_tracker']['candidate_crossing_time_s'] is None),'negative_geometry_without_registered_pending')
  self.started.add(child);return key
 def factual_rows(self,descriptor):
  """Read recorded post-world/action JSON through injected IO, never physics."""
  value=self.io.read_receipt(descriptor)
  return dict(posts=decode(value['posts_bytes']),actions=decode(value['actions_bytes']),snapshot=decode(value['snapshot_bytes']),memory=decode(value['memory_bytes']),rng=restore_bytes(decode(value['RNG_bytes'])))
 def write_factual_jsonl(self,name,rows):
  """Explicit recorded-row writer adapter; preserves bytes and row order."""
  require(type(rows) is list and all(type(row) is dict for row in rows),'467_factual_row_schema')
  descriptor=self.io.write_jsonl(name,rows)
  require(self.read_factual_jsonl(descriptor)==restore_bytes(json_ready(rows)),'467_factual_JSONL_readback')
  return descriptor
 def read_factual_jsonl(self,descriptor):
  rows=self.io.read_jsonl(descriptor)
  require(type(rows) is list and all(type(row) is dict for row in rows),'467_factual_row_schema')
  encoded(json_ready(rows));return rows
 def complete(self,boundary,tail,ctx,authority):
  require(boundary.child_id in self.started and boundary.child_id not in self.closed and tail.boundary_key==boundary.key(),'continuation_not_started_with_seal_or_duplicate')
  runtime=self.verified_runtime();require(runtime['boundary_key']==boundary.key(),'467_closure_runtime_binding')
  descriptor=self.io.write_receipt(boundary.child_id+'-tail',asdict(tail));require(self.io.read_receipt(descriptor)==restore_bytes(json_ready(asdict(tail))),'467_tail_readback')
  key,sealed,digest=self.pending[boundary.child_id];require(key==boundary.key(),'boundary_replaced')
  completion=Completion467(boundary,tail,authority,self.io,sealed,digest)
  self.closed.add(boundary.child_id);return completion
