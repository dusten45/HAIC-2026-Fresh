"""Static exact-set, genuine430 regression and explicit synthetic flag controls."""
import copy,itertools,json,os,unittest
from dataclasses import replace,asdict
from pathlib import Path
import numpy as np
from retry.audit431 import *
from retry.audit429 import audit_pair as audit429
from retry.receipt421_io import load_receipt
from retry.preflight421 import restore_typed
from retry.test_planner419 import evidence
from retry.early429 import choose as choose429,from_wire as old_from_wire
ROOT=Path(os.environ.get('HAIC_RESEARCH_ROOT','/workspace/haic-private-retry-20261009'))

class ExactReasons(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  d=ROOT/'stage430';payload=load_receipt(d/'P_decision38_query-before-integration-private.json');p=payload['context'];parent=Parent(**p['parent']);ledger=GoalLedger(**p['ledger']);cls.ctx=Current(**{**p,'parent':parent,'ledger':ledger,'nominal':tuple(p['nominal'])});cls.state,cls.memory,_=parent.fork_inputs();cls.a=json.loads((d/'P_decision38_fullgas_1-private.json').read_text());cls.b=json.loads((d/'P_decision38_fullgas_2-private.json').read_text());cls.line=np.asarray(json.loads((ROOT/'stage269/N1-plan-private.json').read_text())['line']);cls.hashes=('STATIC_SOURCE_FIRST','STATIC_SOURCE_REPEAT');cls.proofs=GateProofs(True,True,True,True,True,True,True)
 def audit(self,a=None,b=None):return audit_pair(self.a if a is None else a,self.b if b is None else b,self.line,self.state,self.memory,self.ctx.parent.raw_clock_tick,self.hashes)
 def test_all_15_sets_and_64_orderings(self):
  count=0
  for n in range(1,5):
   for combo in itertools.combinations(sorted(PHYSICAL_REASONS),n):
    for order in itertools.permutations(combo):self.assertEqual(physical_tokens(','.join(order)),frozenset(combo));count+=1
  self.assertEqual(count,64)
 def test_genuine430_query38_passes_without_model_or_original_choice_claim(self):
  e=self.audit();self.assertEqual(e.observed_actions,7);self.assertEqual(set(e.stop_reasons),{'path_error_over3m','road_loss_or_grass'});self.assertEqual((e.cost.required_raw_ticks,e.cost.repeat_raw_ticks),(28,28));self.assertIsNone(e.root);self.assertIsNone(e.finish_ticks)
  with self.assertRaises(ProtocolStop):audit429(self.a,self.b,self.line,self.state,self.memory,self.ctx.parent.raw_clock_tick,self.hashes)
 def synthetic(self,combo):
  # Only flag classification controls. Altered sensor rows are not real physical
  # trajectories, have no verified gates, and never feed a model or promotion.
  a=copy.deepcopy(self.a);last=a['rows'][-1];q=last['predicted'];safe=a['rows'][-2]
  q['position']=copy.deepcopy(safe['predicted']['position']);q['velocity']=copy.deepcopy(safe['predicted']['velocity']);q['angle']=safe['predicted']['angle']
  for h in last['raw_hull']:h['origin_position']=copy.deepcopy(safe['raw_hull'][-1]['origin_position']);h['origin_linear_velocity']=copy.deepcopy(safe['raw_hull'][-1]['origin_linear_velocity'])
  if 'path_error_over3m' in combo:q['position']=copy.deepcopy(self.a['rows'][-1]['predicted']['position'])
  q['damage']=1. if 'damage_increase' in combo else 0.;q['collision']='collision_or_obstacle' in combo;q['contact_obstacle_ids']=[];q['wheel_road_contacts']=3 if 'road_loss_or_grass' in combo else 4
  for t in last['tires']:t['grass']=False
  _,flags=metrics(q,last['tires'],last['raw_hull'],self.line,last['memory_after']['C']['phase']);self.assertEqual(set(flags),set(combo));last['safety']=flags;a['error']=','.join(flags)
  return a,copy.deepcopy(a)
 def test_all_15_raw_flag_combinations_recomputed(self):
  count=0
  for n in range(1,5):
   for combo in itertools.combinations(sorted(PHYSICAL_REASONS),n):
    a,b=self.synthetic(combo);e=self.audit(a,b);self.assertEqual(set(e.stop_reasons),set(combo));self.assertIsNone(e.root);self.assertFalse(e.admissible13());self.assertIsNone(e.finish_ticks);count+=1
  self.assertEqual(count,15)
 def test_malformed_partial_duplicate_and_nonphysical_tokens_rejected(self):
  valid='path_error_over3m'
  for x in ['',[],(),None,123,valid+',',','+valid,valid+',,'+valid,valid+','+valid,' '+valid,valid+' ',valid+';road_loss_or_grass','path_error','path_error_over3m_extra',valid+'\n']:
   with self.subTest(x=x),self.assertRaises(ProtocolStop):physical_tokens(x)
  for bad in ['unknown','reverse','pre_meaningful_reverse','domain','technical_error','restore_error','NaN']:
   with self.subTest(bad=bad),self.assertRaises(ProtocolStop):physical_tokens(valid+','+bad)
 def test_bad_error_and_flags_are_rejected_in_raw_audit(self):
  for error in ['',self.a['error']+',reverse',self.a['error']+',',self.a['error']+',path_error_over3m','path_error_over3m','damage_increase']:
   a,b=copy.deepcopy((self.a,self.b));a['error']=b['error']=error
   with self.assertRaises(ProtocolStop):self.audit(a,b)
  for flags in [[],['path_error_over3m'],['path_error_over3m','road_loss_or_grass','road_loss_or_grass'],['path_error_over3m','road_loss_or_grass','technical_error']]:
   a,b=copy.deepcopy((self.a,self.b));a['rows'][-1]['safety']=b['rows'][-1]['safety']=flags
   with self.assertRaises(ProtocolStop):self.audit(a,b)
 def test_nonfinite_technical_repeat_and_measurement_tamper(self):
  for number in [float('nan'),float('inf'),-float('inf')]:
   a,b=copy.deepcopy((self.a,self.b));a['final_state']['physical']['hull']['velocity'][0]=number
   with self.assertRaises(ProtocolStop):self.audit(a,b)
  for key in ['exception','technical_error','restore_error','domain_error']:
   a,b=copy.deepcopy((self.a,self.b));a[key]=b[key]='injected'
   with self.assertRaises(ProtocolStop):self.audit(a,b)
  a,b=copy.deepcopy((self.a,self.b));b['rows'][0]['predicted']['speed_m_s']+=.01
  with self.assertRaises(ProtocolStop):self.audit(a,b)
  for field in ['sample','clock','count','snapshot','memory']:
   a,b=copy.deepcopy((self.a,self.b))
   for c in [a,b]:
    if field=='sample':c['rows'][-1]['tires'].pop()
    elif field=='clock':c['rows'][-1]['predicted']['time']+=.02
    elif field=='count':c['initial_actions']+=1
    elif field=='snapshot':c['final_state']['physical']['actual_time']+=.02
    else:c['controller_memory']['C']['last_time']+=.02
   with self.subTest(field=field),self.assertRaises(ProtocolStop):self.audit(a,b)
 def test_proof_restore_parent_RNG_and_cost_tamper_global_stop(self):
  e=bind_before_query_proof(self.audit(),self.ctx,self.proofs,'SYNTHETIC_STATIC_CONTEXT');base={'nominal':evidence(self.ctx,'nominal',(100,101)),'neutralbrake':evidence(self.ctx,'neutralbrake',(110,111))}
  for key in self.proofs.__dict__:
   if key=='technical_errors':continue
   for value in [False,None]:
    with self.assertRaises(ProtocolStop):choose(self.ctx,{**base,'fullgas':replace(e,proofs=replace(self.proofs,**{key:value}))})
  for c in [replace(e.cost,required_raw_ticks=52),replace(e.cost,model_worlds=1),replace(e.cost,required_actions=13),replace(e.cost,repeat_raw_ticks=0),replace(e.cost,required_CPU_s=float('nan'))]:
   with self.assertRaises(ProtocolStop):choose(self.ctx,{**base,'fullgas':replace(e,cost=c)})
  for patch in [dict(root=replace(e.root,rng='foreign')),dict(root=replace(e.root,state='foreign')),dict(ledger_digest='foreign'),dict(policy_digest='foreign')]:
   with self.assertRaises(ProtocolStop):choose(self.ctx,{**base,'fullgas':replace(e,**patch)})
 def test_wire_duplicate_or_unknown_reasons_never_bypass_audit(self):
  e=self.audit();w=to_wire(e);self.assertEqual(from_wire(w),e)
  for reasons in [['path_error_over3m','road_loss_or_grass','road_loss_or_grass'],['path_error_over3m','reverse'],[]]:
   payload=copy.deepcopy(w);payload['record']['stop_reasons']=reasons
   with self.assertRaises(ProtocolStop):from_wire(payload)
 def test_all_existing_normal_and_single_reason_choices_unchanged(self):
  count=0;single=0
  for path in (ROOT/'stage430').glob('P_decision*-evidence-private.json'):
   payload=load_receipt(path);ctx,ev=restore_typed(copy.deepcopy(payload));ev.update({k:from_wire(v) for k,v in payload['early_evidence'].items()});self.assertEqual(choose(ctx,ev),choose429(ctx,ev));count+=1
   for r,w in payload['early_evidence'].items():
    e=from_wire(w);self.assertEqual(e,old_from_wire(w));single+=1
  self.assertEqual((count,single),(37,2))
 def test_early_type_duplicate_raw_flags_rejected_at_choice(self):
  e=self.audit();trace=decode(e.trace_bytes);trace[-1]['safety'].append(trace[-1]['safety'][0])
  with self.assertRaises(ProtocolStop):validate_early(replace(e,trace_bytes=encoded(trace)))
