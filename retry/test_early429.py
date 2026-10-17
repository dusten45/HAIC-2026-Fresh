"""Static protocol controls. Synthetic binding is never the lost original36 context."""
import ast,copy,os,unittest
from dataclasses import replace,asdict
from pathlib import Path
from retry.early429 import *
from retry.audit429 import saved36_fixture,audit_pair
from retry.test_planner419 import evidence,all_receipts
from retry.planner419 import TickBracket
from retry.receipt421_io import load_receipt
from retry.preflight421 import restore_typed

ROOT=Path(os.environ.get('HAIC_RESEARCH_ROOT','/workspace/haic-private-retry-20261009'))
PROOFS=GateProofs(True,True,True,True,True,True,True)

class EarlyProtocol(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ctx,cls.unbound,cls.raw=saved36_fixture(ROOT)
 def bound(self):return bind_before_query_proof(self.unbound,self.ctx,PROOFS,'SYNTHETIC_STATIC_CONTEXT')
 def baseline(self):return {k:evidence(self.ctx,k,score) for k,score in [('nominal',(100,101)),('neutralbrake',(110,111))]}
 def synthetic_for_recipe(self,name):
  x=self.bound();trace=decode(x.trace_bytes);trace[0]['command']=list(self.ctx.command(name));return replace(x,recipe=name,first_command=self.ctx.command(name),trace_bytes=encoded(trace))
 def test_recorded8_state_reason_cost_and_gap(self):
  r=self.unbound;self.assertEqual((r.observed_actions,r.requested_initial_actions,r.cost.required_raw_ticks,r.cost.repeat_raw_ticks),(8,13,32,32));self.assertEqual(r.stop_reasons,('path_error_over3m',));self.assertIsNone(r.root);self.assertIsNone(r.cost.required_CPU_s);self.assertIsNone(r.proofs.parent_unchanged)
  with self.assertRaises(ProtocolStop):choose(self.ctx,{**self.baseline(),'fullgas':r})
 def test_synthetic_binding_never_finishes_or_promotes(self):
  r=self.bound();r.authenticate(self.ctx);self.assertFalse(r.admissible13());self.assertFalse(r.finished_witness());self.assertIsNone(r.finish_ticks);self.assertFalse(r.promotion_allowed);self.assertFalse(r.actual_DONE_allowed);self.assertFalse(r.actual_execution_allowed)
  p=choose(self.ctx,{**self.baseline(),'fullgas':r});self.assertEqual((p.recipe,p.status),('nominal','GUARDIAN_REFERENCE_ONLY'));self.assertFalse(p.actual_execution_allowed);self.assertNotIn('memory',asdict(p))
 def test_observed_count_not_padded(self):
  for patch in [dict(observed_actions=13),dict(requested_initial_actions=12),dict(cost=replace(self.bound().cost,required_raw_ticks=52))]:
   with self.assertRaises(ProtocolStop):choose(self.ctx,{**self.baseline(),'fullgas':replace(self.bound(),**patch)})
 def test_cannot_add_finish_time_or_tail_to_early_type(self):
  for patch in [dict(finish_ticks=TickBracket(1,2)),dict(official_finish_qualified=True),dict(tail_actions_integrated=1)]:
   with self.assertRaises(TypeError):replace(self.bound(),**patch)
 def test_each_gate_false_or_unknown_remains_global_stop(self):
  for name in PROOFS.__dict__:
   if name=='technical_errors':continue
   for bad in [False,None]:
    with self.assertRaises(ProtocolStop):choose(self.ctx,{**self.baseline(),'fullgas':replace(self.bound(),proofs=replace(PROOFS,**{name:bad}))})
  with self.assertRaises(ProtocolStop):choose(self.ctx,{**self.baseline(),'fullgas':replace(self.bound(),proofs=replace(PROOFS,technical_errors=('definition_error',)))})
 def test_unknown_technical_or_domain_reason_not_safety(self):
  for reason in ['reverse','pre_meaningful_reverse','zero_target','numeric_error','restore_body_tile_progress_finish']:
   with self.assertRaises(ProtocolStop):replace(self.bound(),stop_reasons=(reason,)).validate_record()
 def test_raw_technical_exceptions_not_relabelled(self):
  for field in ['technical_error','exception','restore_error','domain_error']:
   a,b,*rest=copy.deepcopy(self.raw);a[field]='injected';b[field]='injected'
   with self.assertRaises(ProtocolStop):audit_pair(a,b,*rest)
 def test_raw_nonfinite_is_not_safety(self):
  for number in [float('nan'),float('inf'),-float('inf')]:
   a,b,*rest=copy.deepcopy(self.raw);a['final_state']['physical']['hull']['velocity'][0]=number
   with self.assertRaises(ProtocolStop):audit_pair(a,b,*rest)
 def test_independent_repeat_mismatch_is_global_stop(self):
  a,b,*rest=copy.deepcopy(self.raw);b['rows'][0]['predicted']['speed_m_s']+=.001
  with self.assertRaises(ProtocolStop):audit_pair(a,b,*rest)
 def test_missing_raw_or_clock_is_global_stop(self):
  for change in ['sample','clock','state','memory']:
   a,b,*rest=copy.deepcopy(self.raw)
   for x in [a,b]:
    if change=='sample':x['rows'][-1]['tires'].pop()
    elif change=='clock':x['rows'][-1]['predicted']['time']+=.02
    elif change=='state':x['final_state']['physical']['actual_time']+=.02
    else:x['controller_memory']['C']['last_time']+=.02
   with self.assertRaises(ProtocolStop):audit_pair(a,b,*rest)
 def test_flag_without_physical_threshold_is_rejected(self):
  a,b,line,state,memory,clock,hashes=copy.deepcopy(self.raw)
  for x in [a,b]:x['error']='damage_increase';x['rows'][-1]['safety']=['damage_increase']
  with self.assertRaises(ProtocolStop):audit_pair(a,b,line,state,memory,clock,hashes)
 def test_later_stop_after_first_unsafe_rejected(self):
  a,b,*rest=copy.deepcopy(self.raw)
  for x in [a,b]:x['rows'][0]['safety']=['path_error_over3m']
  with self.assertRaises(ProtocolStop):audit_pair(a,b,*rest)
 def test_root_ledger_policy_memory_RNG_clock_mismatches(self):
  r=self.bound()
  for name in ['state','memory_before_nominal','rng','raw_clock_tick']:
   value=r.root.raw_clock_tick+4 if name=='raw_clock_tick' else 'foreign'
   with self.assertRaises(ProtocolStop):choose(self.ctx,{**self.baseline(),'fullgas':replace(r,root=replace(r.root,**{name:value}))})
  for patch in [dict(ledger_digest='foreign'),dict(policy_digest='foreign'),dict(input_state_digest='foreign'),dict(input_memory_digest='foreign')]:
   with self.assertRaises(ProtocolStop):choose(self.ctx,{**self.baseline(),'fullgas':replace(r,**patch)})
 def test_wrong_recipe_or_pedal_rejected(self):
  r=self.bound()
  for patch in [dict(recipe='fourth'),dict(first_command=(0.,.8,0.))]:
   with self.assertRaises(ContractError):choose(self.ctx,{**self.baseline(),'fullgas':replace(r,**patch)})
 def test_nominal_ineligible_existing_neutral_baseline(self):
  ev={'nominal':self.synthetic_for_recipe('nominal'),'neutralbrake':evidence(self.ctx,'neutralbrake',(100,101)),'fullgas':evidence(self.ctx,'fullgas',(94,95))};self.assertEqual(choose(self.ctx,ev).recipe,choose419(self.ctx,ev).recipe);self.assertEqual(choose(self.ctx,ev).recipe,'fullgas')
 def test_both_guardian_ineligible_stop_gas_cannot_rescue(self):
  ev={k:self.synthetic_for_recipe(k) for k in ['nominal','neutralbrake']};ev['fullgas']=evidence(self.ctx,'fullgas',(1,2));self.assertEqual(choose(self.ctx,ev).status,'STOP_GUARDIAN_BOTH_INFEASIBLE')
 def test_missing_neutral_after_nominal_stop_unchanged(self):
  self.assertEqual(choose(self.ctx,{'nominal':self.synthetic_for_recipe('nominal')}).status,'NEED_GUARDIAN_NEUTRAL13')
 def test_normal_tail_unsafe_and_finish_receipts_unchanged(self):
  count=0;unsafe=0
  for path in sorted((ROOT/'stage428').glob('P_decision*-evidence-private.json')):
   ctx,ev=restore_typed(copy.deepcopy(load_receipt(path)));self.assertEqual(choose(ctx,ev),choose419(ctx,ev));count+=1;unsafe+=sum(x.tail_status=='UNSAFE' for x in ev.values())
  self.assertEqual((count,unsafe),(35,4))
 def test_official_partial_finish_keeps_normal_receipt(self):
  ctx=self.ctx;ev={k:evidence(ctx,k,s) for k,s in [('nominal',(6,7)),('fullgas',(2,3)),('neutralbrake',(10,11))]};self.assertEqual(choose(ctx,ev),choose419(ctx,ev));self.assertTrue(ev['fullgas'].initial_actions<13)
  a,b,*rest=copy.deepcopy(self.raw)
  for x in [a,b]:x['status']='FINISHED';x['finish_ticks']={'lo':1,'hi':2}
  with self.assertRaises(ProtocolStop):audit_pair(a,b,*rest)
 def test_stored_native_partial_finish_and_done_rights_unchanged(self):
  from retry.guardian426_confirmed import actual_done_eligible
  import json
  for folder,n in [('stage423/actual_C0',3),('stage427/actual_P',1)]:
   row=json.loads((ROOT/folder/'trace-private.jsonl').read_text().splitlines()[-1]);self.assertEqual(row['raw_ticks'],n);self.assertTrue(actual_done_eligible(row,True));self.assertFalse(actual_done_eligible(row,False))
 def test_context_and_actual_ledger_are_immutable(self):
  before=self.ctx.parent.stamp(),self.ctx.ledger.digest();choose(self.ctx,{**self.baseline(),'fullgas':self.bound()});self.assertEqual(before,(self.ctx.parent.stamp(),self.ctx.ledger.digest()))
 def test_early_type_has_no_end13_or_execution_payload(self):
  r=self.bound();self.assertNotIn('end13',r.__dataclass_fields__);self.assertFalse(r.actual_execution_allowed);self.assertFalse(r.actual_DONE_allowed)
 def test_pure_protocol_has_no_world_or_actuator_import(self):
  tree=ast.parse(Path(__file__).with_name('early429.py').read_text());imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)];self.assertEqual([m for m in imports if m and m.startswith('retry.')],['retry.planner419'])
 def test_wire_roundtrip_keeps_observations_gap_and_no_authority(self):
  import json
  for original in [self.unbound,self.bound()]:
   restored=from_wire(json.loads(json.dumps(to_wire(original))));self.assertEqual(restored,original);self.assertIsNone(restored.finish_ticks);self.assertFalse(restored.promotion_allowed)
  self.assertEqual(choose(self.ctx,{**self.baseline(),'fullgas':from_wire(to_wire(self.bound()))}),choose(self.ctx,{**self.baseline(),'fullgas':self.bound()}))
 def test_wire_cannot_smuggle_completion_or_memory_commit(self):
  for name in ['finish_ticks','actual_DONE_allowed','promotion_allowed','end13']:
   payload=to_wire(self.bound());payload['record'][name]=True
   with self.assertRaises(ProtocolStop):from_wire(payload)
 def test_future_scope_bounds_and_no_execution(self):
  from retry.proposal429 import bounds
  p=bounds();self.assertEqual((p['total_tick_cap_required'],p['total_world_cap_required']),(519038,882));self.assertLessEqual(p['total_tick_cap_required'],p['proposed_model_cap_ticks']);self.assertLessEqual(p['total_world_cap_required'],p['proposed_model_cap_worlds']);self.assertEqual((p['C0_max_suffix_decisions'],p['P_max_eligible_FIRST_LAP_planner_decisions'],p['P_max_total_suffix_decisions']),(80,64,100));self.assertEqual(p['new_actual_calls'],0)
  for args in [dict(p_planner=101),dict(c0_suffix=-1),dict(p_total_suffix=0)]:
   with self.assertRaises(ValueError):bounds(**args)

if __name__=='__main__':unittest.main()
