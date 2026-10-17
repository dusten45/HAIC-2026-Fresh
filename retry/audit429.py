"""Stored raw trace auditing only; creates no worlds and performs no integration."""
import copy,json
from pathlib import Path
import numpy as np
from retry.early429 import *
from retry.executor397 import canonical_projection
from retry.headroom413_run import metrics
from retry.planner419 import Parent,GoalLedger,Current
from retry.paired417_common import policy

def pair_signature(child):return digest({k:v for k,v in child.items() if k!='telemetry'})

def audit_pair(first,repeat,line,input_state,input_memory,input_clock,source_hashes):
 # Validate all numeric evidence before asking whether the failure is physical.
 encoded(first);encoded(repeat);encoded(input_state);encoded(input_memory)
 for c in [first,repeat]:
  if any(c.get(k) not in [None,False,'',[]] for k in ['technical_error','exception','restore_error','domain_error']):raise ProtocolStop('technical_exception_not_physical')
  if c['status']!='UNSAFE' or c['error'] not in PHYSICAL_REASONS:raise ProtocolStop('only_explicit_physical_stop_can_be_ineligible')
  if c['tail_actions']!=0 or c['finish_ticks'] is not None or not 1<=c['initial_actions']<H or len(c['rows'])!=c['initial_actions']:raise ProtocolStop('not_early_initial_stop')
  if c['model_ledger']['deadline_missed'] or c['model_ledger']['done']:raise ProtocolStop('progress_or_DONE_not_early_physical')
  phase=None
  for row in c['rows']:
   current=row['memory_after']['C']['phase']
   if current not in ['FIRST_LAP','FINISH_CONFIRM'] or row['memory_before']['C']['phase'] not in ['FIRST_LAP','FINISH_CONFIRM']:raise ProtocolStop('phase_or_domain_failure')
   if phase is not None and row['memory_before']['C']['phase']!=phase:raise ProtocolStop('phase_discontinuity')
   phase=current;projected,flags=metrics(row['predicted'],row['tires'],row['raw_hull'],line,current)
   if set(flags)!=set(row['safety']) or set(flags)-PHYSICAL_REASONS:raise ProtocolStop('physical_reason_not_supported_by_raw')
  if set(c['rows'][-1]['safety'])!={c['error']}:raise ProtocolStop('stop_reason_not_exact_last_physical_condition')
 if pair_signature(first)!=pair_signature(repeat):raise ProtocolStop('independent_repeat_mismatch')
 before=first['rows'][0]['memory_before']
 if before!=input_memory or input_state['terminal_model']['physical']['actual_time']!=first['rows'][0]['raw_hull'][0]['time']:raise ProtocolStop('input_state_memory_clock_mismatch')
 n=first['initial_actions'];ticks=sum(row['predicted']['raw_ticks'] for row in first['rows'])
 proofs=GateProofs(None,True,None,None,None,True,True)
 return EarlyPhysicalIneligible(first['recipe'],tuple(first['rows'][0]['command']),n,tuple(first['rows'][-1]['safety']),encoded(first['rows']),encoded(first['final_state']),encoded(first['controller_memory']),ObservedCost(n,n,ticks,ticks),proofs,digest(input_state),digest(input_memory),input_clock,tuple(source_hashes)).validate_record()

def saved36_fixture(root):
 root=Path(root);d=root/'stage428';parent=json.loads((d/'parent_P-private.json').read_text());a=json.loads((d/'P_decision36_fullgas_1-private.json').read_text());b=json.loads((d/'P_decision36_fullgas_2-private.json').read_text());fixed=json.loads((root/'stage269/N1-plan-private.json').read_text());line=np.asarray(fixed['line']);memory=a['rows'][0]['memory_before'];ledgerdata=parent['model_ledger'];state=dict(terminal_model=parent['final_state'],provenance='CURRENT_MODEL_PARENT',immutable_actual_root_digest=ledgerdata['actual_root_digest']);clock=ledgerdata['last_clock_tick'];ledger=GoalLedger(ledgerdata['progress_m'],ledgerdata['goal_m'],ledgerdata['age_actions'],clock,ledgerdata['deadline_missed'],ledgerdata['done']);from retry.preflight421 import restore_typed
 from retry.receipt421_io import load_receipt
 previous,_=restore_typed(copy.deepcopy(load_receipt(d/'P_decision35-evidence-private.json')))
 # The original36 RNG stamp was not saved; this is explicitly a new static
 # context for type/logic controls, never an authenticated original query36.
 p=Parent.current(state,memory,{'SYNTHETIC_STATIC_ONLY':'original_query36_context_RNG_stamp_not_saved'},clock);h=state['terminal_model']['physical']['hull'];q=canonical_projection(line,h['position'],h['velocity'],'FIRST_LAP');pace=np.asarray(json.loads((root/'stage404/profiles-private.json').read_text())['frozen268']);target,_=policy(fixed,pace)._reference(q);forward=float(np.asarray(h['velocity'])@np.asarray([-np.sin(h['angle']),np.cos(h['angle'])]));nominal=json.loads((d/'P_decision36_nominal_1-private.json').read_text())['rows'][0]['command'];ctx=Current(p,ledger,previous.policy_digest,tuple(nominal),'FIRST_LAP',target,q['sigma'],forward,sum(fixed['free_profile']['ds'])-ledger.progress_m)
 import hashlib
 hashes=[hashlib.sha256((d/n).read_bytes()).hexdigest() for n in ['P_decision36_fullgas_1-private.json','P_decision36_fullgas_2-private.json','parent_P-private.json']]
 receipt=audit_pair(a,b,line,state,memory,clock,hashes)
 return ctx,receipt,(a,b,line,state,memory,clock,hashes)
