"""Strict exact physical reason sets; stored traces only, no integration."""
import copy,json
from pathlib import Path
import numpy as np
from retry.early429 import *
from retry.executor397 import canonical_projection
from retry.headroom413_run import metrics
from retry.planner419 import Parent,GoalLedger,Current
from retry.paired417_common import policy

def physical_tokens(value, *, allow_empty=False):
 if type(value) is str:
  values=value.split(',')
 elif type(value) in (tuple,list):
  values=list(value)
 else:raise ProtocolStop('invalid_reason_container')
 if not values and allow_empty:return frozenset()
 if not values or any(type(x) is not str or not x or x not in PHYSICAL_REASONS for x in values):raise ProtocolStop('unknown_empty_or_nonphysical_reason_token')
 if len(values)!=len(set(values)):raise ProtocolStop('duplicate_physical_reason_token')
 return frozenset(values)

def validate_early(record):
 record.validate_record();reasons=physical_tokens(record.stop_reasons)
 for i,row in enumerate(decode(record.trace_bytes)):
  flags=physical_tokens(row['safety'],allow_empty=True)
  if (i<record.observed_actions-1 and flags) or (i==record.observed_actions-1 and flags!=reasons):raise ProtocolStop('reason_set_not_exact_first_stop')
 return record

def pair_signature(child):return digest({k:v for k,v in child.items() if k!='telemetry'})

def audit_pair(first,repeat,line,input_state,input_memory,input_clock,source_hashes):
 # Validate all numeric evidence before asking whether the failure is physical.
 encoded(first);encoded(repeat);encoded(input_state);encoded(input_memory)
 for c in [first,repeat]:
  if any(c.get(k) not in [None,False,'',[]] for k in ['technical_error','exception','restore_error','domain_error']):raise ProtocolStop('technical_exception_not_physical')
  if c['status']!='UNSAFE':raise ProtocolStop('only_explicit_physical_stop_can_be_ineligible')
  reasons=physical_tokens(c['error'])
  if c['tail_actions']!=0 or c['finish_ticks'] is not None or not 1<=c['initial_actions']<H or len(c['rows'])!=c['initial_actions']:raise ProtocolStop('not_early_initial_stop')
  if c['model_ledger']['deadline_missed'] or c['model_ledger']['done']:raise ProtocolStop('progress_or_DONE_not_early_physical')
  phase=None
  for row in c['rows']:
   current=row['memory_after']['C']['phase']
   if current not in ['FIRST_LAP','FINISH_CONFIRM'] or row['memory_before']['C']['phase'] not in ['FIRST_LAP','FINISH_CONFIRM']:raise ProtocolStop('phase_or_domain_failure')
   if phase is not None and row['memory_before']['C']['phase']!=phase:raise ProtocolStop('phase_discontinuity')
   phase=current;projected,flags=metrics(row['predicted'],row['tires'],row['raw_hull'],line,current)
   if physical_tokens(flags,allow_empty=True)!=physical_tokens(row['safety'],allow_empty=True):raise ProtocolStop('physical_reason_not_supported_by_raw')
  if physical_tokens(c['rows'][-1]['safety'])!=reasons:raise ProtocolStop('stop_reason_not_exact_last_physical_condition')
 if pair_signature(first)!=pair_signature(repeat):raise ProtocolStop('independent_repeat_mismatch')
 before=first['rows'][0]['memory_before']
 if before!=input_memory or input_state['terminal_model']['physical']['actual_time']!=first['rows'][0]['raw_hull'][0]['time']:raise ProtocolStop('input_state_memory_clock_mismatch')
 n=first['initial_actions'];ticks=sum(row['predicted']['raw_ticks'] for row in first['rows'])
 proofs=GateProofs(None,True,None,None,None,True,True)
 return validate_early(EarlyPhysicalIneligible(first['recipe'],tuple(first['rows'][0]['command']),n,tuple(first['rows'][-1]['safety']),encoded(first['rows']),encoded(first['final_state']),encoded(first['controller_memory']),ObservedCost(n,n,ticks,ticks),proofs,digest(input_state),digest(input_memory),input_clock,tuple(source_hashes)))


def choose(ctx,receipts,optimize=True):
 for e in receipts.values():
  if type(e) is EarlyPhysicalIneligible:validate_early(e)
 from retry.early429 import choose as original
 return original(ctx,receipts,optimize)

def to_wire(record):
 from retry.early429 import to_wire as original
 return original(validate_early(record))

def from_wire(payload):
 from retry.early429 import from_wire as original
 return validate_early(original(payload))
