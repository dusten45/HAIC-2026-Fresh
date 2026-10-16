"""Static logic + existing412/414/418 fixtures; synthetic scores are not physics evidence."""
import ast,copy,hashlib,json,math,os,unittest
from dataclasses import replace
from pathlib import Path
from retry.planner419 import *
ROOT=Path(os.environ.get('HAIC_RESEARCH_ROOT','/workspace/haic-private-retry-20261009'))

def sample_context(**changes):
 parent=Parent.current({'current_body':[1.,2.],'speed':2.},{'C':'memory_before_nominal'},{'opaque_rng':'unchanged'},100)
 ctx=Current(parent,GoalLedger.start(0.,100),'frozen-signed-C',(0.1,0.,BRAKE_03_F32),'FIRST_LAP',2.,2.,2.,200.)
 return replace(ctx,**changes)
def terminal(**changes):return replace(TerminalVector(2.,.2,.5,(1.,2.,3.,4.),(.1,.1),(.8,.9,1.248,1.1),100.,'end-body-tires','end-controller'),**changes)
def checkpoints(n):return tuple([H]*(n//H)+([n%H] if n%H else []))
def evidence(ctx,name,score=(100,101),**changes):
 finish=TickBracket(*score) if score is not None else None;actions=math.ceil(finish.hi/4) if finish else H;initial=min(H,actions);tail=max(0,actions-initial)
 x=Evidence(name,ctx.parent.stamp(),ctx.ledger.digest(),ctx.policy_digest,ctx.command(name),initial,True,True,True,True,True,True,terminal(),tail_status='FINISHED' if finish else 'UNQUERIED',finish_ticks=finish,official_finish_qualified=finish is not None,tail_actions_integrated=tail,checkpoint_actions=checkpoints(tail))
 return replace(x,**changes)
def all_receipts(ctx,scores=((100,101),(94,95),(105,106))):return {k:evidence(ctx,k,v) for k,v in zip(RECIPES,scores)}

class PlannerLogic(unittest.TestCase):
 def test_any_strict_raw_tick_gain_not_universal_08(self):
  ctx=sample_context();ev=all_receipts(ctx,((100,101),(98,99),(105,106)));p=choose(ctx,ev);self.assertEqual(p.recipe,'fullgas');self.assertEqual(p.gain_rawticks,(1,3));self.assertFalse(p.actual_execution_allowed)
 def test_overlap_and_touch_do_not_manufacture_gain(self):
  ctx=sample_context()
  for score in [(99,100),(100,101),(101,102)]:self.assertEqual(choose(ctx,all_receipts(ctx,((100,101),score,(110,111)))).recipe,'nominal')
 def test_locally_slower_neutral_can_win_finished_continuation(self):
  ctx=sample_context();ev=all_receipts(ctx,((100,101),(105,106),(94,95)))
  for k,p in zip(RECIPES,[(25,26),(22,23),(40,41)]):ev[k]=replace(ev[k],local_exit_ticks=TickBracket(*p))
  self.assertEqual(choose(ctx,ev).recipe,'neutralbrake')
 def test_no_terminal_weight_overrides_finish(self):
  ctx=sample_context();ev=all_receipts(ctx);ev['fullgas']=replace(ev['fullgas'],end13=terminal(speed=1.,yaw=3.,path_error=2.9,last_raw_force_ratio=(2.,2.,2.,2.)))
  self.assertEqual(choose(ctx,ev).recipe,'fullgas')
 def test_missing_tail_cannot_rank_local_pulse(self):
  ctx=sample_context();ev={k:evidence(ctx,k,None) for k in RECIPES};ev['fullgas']=replace(ev['fullgas'],local_exit_ticks=TickBracket(22,23));self.assertEqual(choose(ctx,ev).status,'NEED_C_CONTINUATION')
 def test_pending_slow_recipe_not_pruned_by_local_rank(self):
  ctx=sample_context();ev=all_receipts(ctx);ev['neutralbrake']=evidence(ctx,'neutralbrake',None);self.assertEqual(choose(ctx,ev).status,'NEED_C_CONTINUATION')
 def test_censored_tail_has_no_finish_score(self):
  ctx=sample_context();ev=all_receipts(ctx);ev['fullgas']=evidence(ctx,'fullgas',None,tail_status='CENSORED');self.assertEqual(choose(ctx,ev).recipe,'nominal')
  with self.assertRaises(ContractError):choose(ctx,{**ev,'fullgas':replace(ev['fullgas'],finish_ticks=TickBracket(1,2))})
 def test_both_guardian_recipes_invalid_stop_even_gas_finished(self):
  ctx=sample_context();ev=all_receipts(ctx)
  for k in ['nominal','neutralbrake']:ev[k]=replace(ev[k],safety_ok=False)
  self.assertEqual(choose(ctx,ev).status,'STOP_GUARDIAN_BOTH_INFEASIBLE')
 def test_neutral_guardian_can_be_baseline(self):
  ctx=sample_context();ev=all_receipts(ctx,((120,121),(94,95),(100,101)));ev['nominal']=replace(ev['nominal'],safety_ok=False);self.assertEqual(choose(ctx,ev).recipe,'fullgas')
 def test_restore_repeat_parent_fidelity_fail_closed(self):
  ctx=sample_context()
  for k in ['restore_ok','independent_repeat_ok','parent_unchanged','numerical_fidelity_ok']:
   ev=all_receipts(ctx);ev['fullgas']=replace(ev['fullgas'],**{k:False})
   with self.assertRaises(ContractError):choose(ctx,ev)
 def test_stale_root_memory_rng_clock_ledger_rejected(self):
  ctx=sample_context();ev=all_receipts(ctx)
  for stamp in [replace(ev['fullgas'].root,state='foreign'),replace(ev['fullgas'].root,memory_before_nominal='foreign'),replace(ev['fullgas'].root,rng='foreign'),replace(ev['fullgas'].root,raw_clock_tick=104)]:
   with self.assertRaises(ContractError):choose(ctx,{**ev,'fullgas':replace(ev['fullgas'],root=stamp)})
  with self.assertRaises(ContractError):choose(ctx,{**ev,'fullgas':replace(ev['fullgas'],ledger_digest='forecast_reset_goal')})
 def test_new_pedal_steer_and_foreign_tail_rejected(self):
  ctx=sample_context();ev=all_receipts(ctx)
  for patch in [dict(first_command=(0.,.8,0.)),dict(tail_policy='O'),dict(tail_time_provenance='PROFILE_REFERENCE_CLOCK'),dict(max_tail_actions=1000)]:
   with self.assertRaises(ContractError):choose(ctx,{**ev,'fullgas':replace(ev['fullgas'],**patch)})
 def test_past_future_input_separation(self):
  for key in FORBIDDEN_CURRENT_KEYS:
   with self.assertRaises(ContractError):Parent.current({'nested':{key:123}},{},{},100)
 def test_fork_memory_independence_no_end_memory_commit(self):
  ctx=sample_context();a=ctx.parent.fork_inputs();b=ctx.parent.fork_inputs();a[0]['speed']=99;a[1]['C']='mutated';self.assertEqual(b[0]['speed'],2.);self.assertEqual(ctx.parent.fork_inputs()[1]['C'],'memory_before_nominal');self.assertNotIn('memory',choose(ctx,all_receipts(ctx)).__dict__)
 def test_goal_persists_until_actual_hit(self):
  ledger=GoalLedger.start(0.,100)
  for j in range(1,13):ledger=ledger.advance_actual(ActualObservation(j*.1,100+4*j));self.assertEqual(ledger.goal_m,3.24)
  ledger=ledger.advance_actual(ActualObservation(1.3,152));self.assertTrue(ledger.deadline_missed)
 def test_goal_renews_after_actual_hit_not_forecast(self):
  ledger=GoalLedger.start(0.,100)
  with self.assertRaises(ContractError):ledger.advance_actual(ActualObservation(9.,104,provenance='MODEL_FORECAST'))
  updated=ledger.advance_actual(ActualObservation(3.24,104));self.assertEqual(updated.goal_m,6.48);self.assertEqual(updated.age_actions,0);self.assertEqual(ledger.goal_m,3.24)
 def test_partial_official_finish_and_done(self):
  ledger=GoalLedger.start(0.,100);done=ledger.advance_actual(ActualObservation(.1,101,official_finished=True));self.assertTrue(done.done)
  ctx=sample_context(official_finished=True,remaining_path_m=-.1);self.assertEqual(query_schedule(ctx,Budget(0,0)).mode,'DONE_NO_ACTION')
 def test_official_finish_inside_initial13_preserves_partial_contract(self):
  ctx=sample_context();ev={k:evidence(ctx,k,score) for k,score in zip(RECIPES,[(6,7),(2,3),(10,11)])};ev['fullgas']=replace(ev['fullgas'],end13=terminal(remaining_path_m=-.1));self.assertEqual(choose(ctx,ev).recipe,'fullgas');self.assertFalse(choose(ctx,ev).actual_execution_allowed)
 def test_budget_only_uses_current_guardian_reference(self):
  ctx=sample_context();ev={k:evidence(ctx,k,None) for k in RECIPES};self.assertEqual(choose(ctx,ev,optimize=False).status,'GUARDIAN_REFERENCE_ONLY')
 def test_stop_zero_micro_reverse_phase_vertex_domains(self):
  ctx=sample_context()
  for sigma in [0.,2.**-40,-2.**-40,-3.2834064722633844e-16]:self.assertEqual(replace(ctx,sigma=sigma,body_forward=sigma).gate(),'QUERY_CURRENT')
  self.assertEqual(replace(ctx,sigma=-1).gate(),'STOP_CURRENT_SAFETY');self.assertEqual(replace(ctx,body_forward=-1).gate(),'STOP_CURRENT_SAFETY');self.assertEqual(replace(ctx,target_r=0.).gate(),'STOP_POSITIVE_TARGET_DOMAIN');self.assertEqual(replace(ctx,projection_qualified=False).gate(),'STOP_PROJECTION_NO_EPSILON')
  for phase in ['LAUNCH','STOP','FINISH_CONFIRM']:self.assertEqual(replace(ctx,phase=phase,target_r=0).gate(),'EXISTING_PHASE_ONLY_NOT_A_NEW_FALLBACK')
 def test_zero_target_receipt_not_used_and_restore_block(self):
  self.assertEqual(replace(sample_context(),input_restore_qualified=False).gate(),'STOP_RESTORE')
 def test_query_budget_dedup_and_no_verified_fallback(self):
  ctx=sample_context();q=query_schedule(ctx,Budget(7704,6));self.assertEqual((q.essential_ticks_cap,q.qualification_extra_ticks_cap),(3852,3852));self.assertEqual(query_schedule(ctx,Budget(208,4)).mode,'CURRENT_GUARDIAN_ONLY_NO_TIME_OPTIMIZATION');self.assertEqual(query_schedule(ctx,Budget(1,1)).mode,'STOP_QUERY_BUDGET_NO_VERIFIED_FALLBACK')
  ctx=replace(ctx,nominal=(.1,1.,0.));q=query_schedule(ctx,Budget(10000,10));self.assertEqual(len(q.recipes),2)
 def test_dedup_cannot_fake_a_faster_identical_recipe(self):
  ctx=sample_context(nominal=(.1,1.,0.))
  with self.assertRaises(ContractError):choose(ctx,all_receipts(ctx))
 def test_time_unit_cannot_silently_mix_seconds(self):
  with self.assertRaises(ContractError):TickBracket(.50,.52)
  self.assertEqual(TickBracket(25,26).seconds(),(.50,.52));self.assertEqual(TickBracket(22,23).gain_over(TickBracket(25,26)),(2,4))
 def test_no_absolute_action_arc_seed_trigger(self):
  ctx=sample_context();q=query_schedule(ctx,Budget(10000,10));shifted=replace(ctx,ledger=replace(ctx.ledger,progress_m=500.,goal_m=503.24));self.assertEqual(query_schedule(shifted,Budget(10000,10)),q)
  self.assertNotIn('seed',Current.__dataclass_fields__);self.assertNotIn('absolute_action',Current.__dataclass_fields__);self.assertNotIn('arc_zone',Current.__dataclass_fields__)
 def test_no_model_or_execution_import(self):
  tree=ast.parse(Path(__file__).with_name('planner419.py').read_text());mods=[]
  for node in ast.walk(tree):
   if isinstance(node,ast.Import):mods +=[x.name for x in node.names]
   elif isinstance(node,ast.ImportFrom):mods.append(node.module or '')
  self.assertFalse(any('core' in x or 'model' in x or 'executor' in x for x in mods))

class StoredCases(unittest.TestCase):
 def test_412_reference_clock_is_not_a_finish_receipt(self):
  design=json.loads((ROOT/'stage412/design.json').read_text());self.assertEqual(design['status'],'PROPOSALS_ONLY_NO_EXECUTION_NO_RESERVATION');ctx=sample_context();ev=all_receipts(ctx);ev['fullgas']=replace(ev['fullgas'],tail_time_provenance='PROFILE_REFERENCE_CLOCK')
  with self.assertRaises(ContractError):choose(ctx,ev)
 def test_414_local_gain_and_late_censor_not_C_evidence(self):
  a=json.loads((ROOT/'stage414/analysis.json').read_text());self.assertFalse(a['official_finish_qualified']);self.assertIsNone(a['official_lap']);self.assertLess(a['first_certain_loss_marker']['gain_bracket_s'][1],0);self.assertGreater(next(x for x in a['milestones'] if x['label']=='H1_exit')['gain_bracket_s'][0],0)
  # O historical tail is a counterexample, never relabeled a C continuation.
  ctx=sample_context();ev=all_receipts(ctx);ev['fullgas']=evidence(ctx,'fullgas',None,tail_status='CENSORED',tail_policy='O')
  with self.assertRaises(ContractError):choose(ctx,ev)
 def test_418_calibrated_13_and_clipping_still_need_C_tail(self):
  a=json.loads((ROOT/'stage418/analysis.json').read_text());self.assertEqual(a['arms']['B']['actual_clip_samples'],26);self.assertEqual(a['arms']['B']['clip_flag_mismatches'],0);self.assertFalse(a['promotion']);ctx=sample_context();ev={k:evidence(ctx,k,None) for k in RECIPES}
  for name in ['A','B']:
   key='nominal' if name=='A' else 'fullgas';ticks=a['arms'][name]['cached_source_arrival']['rawtick_bracket'];ev[key]=replace(ev[key],local_exit_ticks=TickBracket(*ticks),end13=terminal(last_raw_force_ratio=(.9,.9,1.2478,1.1)))
  self.assertEqual(choose(ctx,ev).status,'NEED_C_CONTINUATION');self.assertFalse(choose(ctx,ev).actual_execution_allowed)
 def test_418_actual_goal_updates_use_only_committed_observations(self):
  rows=[json.loads(x) for x in (ROOT/'stage418/actual_B/trace-private.jsonl').read_text().splitlines()];ledger=GoalLedger.start(rows[0]['progress_before'],51)
  for row in rows:
   ledger=ledger.advance_actual(ActualObservation(row['progress_after'],ledger.last_clock_tick+row['raw_ticks'],row['completed']));self.assertFalse(ledger.deadline_missed)
  self.assertEqual(ledger.progress_m,rows[-1]['progress_after'])
 def test_418_real_current_context_schedules_without_action_or_arc_trigger(self):
  # Pure geometry evaluation; no controller.act/world/step is called.
  import numpy as np
  from retry.executor397 import canonical_projection
  fork=json.loads((ROOT/'stage418/actual_A/fork-private.json').read_text());fixed=json.loads((ROOT/'stage269/N1-plan-private.json').read_text());pace=np.asarray(json.loads((ROOT/'stage404/profiles-private.json').read_text())['frozen268']);line=np.asarray(fixed['line']);h=fork['physical']['hull'];q=canonical_projection(line,h['position'],h['velocity'],'FIRST_LAP');nodes=np.asarray(fixed['free_profile']['speed'])*pace;r=float(np.sqrt((1-q['u'])*nodes[q['index']]**2+q['u']*nodes[q['index']+1]**2));row=json.loads((ROOT/'stage418/actual_A/trace-private.jsonl').read_text().splitlines()[118]);clock=round(fork['physical']['actual_time']*50);root=Parent.current({'physical':fork['physical'],'wrapper':fork['wrapper']},fork['controller']['before'],fork['RNG'],clock);ledger=GoalLedger(row['progress_before'],row['goal_before'],H-(row['deadline_before']-(row['step']-1)),clock);vel=np.asarray(h['velocity']);forward=float(vel@np.asarray([-math.sin(h['angle']),math.cos(h['angle'])]));ctx=Current(root,ledger,'frozen-signed-C',tuple(fork['controller']['nominal']),'FIRST_LAP',r,q['sigma'],forward,sum(fixed['free_profile']['ds'])-q['arc']);schedule=query_schedule(ctx,Budget(7704,6));self.assertEqual(schedule.mode,'STATE_QUERY_LONG_C_WITNESSES');self.assertEqual(schedule.recipes,RECIPES);self.assertGreater(r,0);self.assertEqual(ctx.parent.fork_inputs()[1],fork['controller']['before'])
 def test_418_current_fork_roundtrip_no_parent_future_or_memory_mutation(self):
  fork=json.loads((ROOT/'stage418/actual_A/fork-private.json').read_text());root=Parent.current({'physical':fork['physical'],'wrapper':fork['wrapper']},fork['controller']['before'],fork['RNG'],523);stamp=root.stamp();a=root.fork_inputs();b=root.fork_inputs();a[1]['C']['last_time']=999.;self.assertNotEqual(a[1],b[1]);self.assertEqual(root.stamp(),stamp);self.assertNotIn('future_trace',json.loads(root.state_bytes))

if __name__=='__main__':unittest.main()
