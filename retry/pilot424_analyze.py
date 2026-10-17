"""Saved-only twelve-decision readout; fresh model result vs historical actual kept apart."""
import copy,json,sys,time
from dataclasses import asdict
from pathlib import Path
from retry.loss389_analyze import read,save,sha
from retry.receipt421_io import load_receipt,receipt_digest
from retry.preflight421 import restore_typed
from retry.planner419 import choose
from retry.pilot420_json import json_ready

def prepare(root):
 d=root/'stage424';assert not(d/'analysis-plan.json').exists();p=read(d/'plan.json');files=[Path(__file__),d/'plan.json',d/'result.json',d/'budget.json',d/'static-result.json']+[f for f in d.glob('*.json') if f.name not in ['analysis-plan.json','analysis.json','prior-preservation-manifest.json']]
 save(d/'analysis-plan.json',dict(scope='Savedonly. Everyproposal/digest/currentstamp, modelparentclipping/progress/officialeventandperdecisionrootprojectedbrackets. Failedtailtimeneverimputed. Historical423notnewactual.',sources={str(f):sha(f) for f in files},protected=p['protected'],original408_preserve=p['original408_preserve']));(d/'analysis-plan.sha256').write_text(sha(d/'analysis-plan.json')+'\n')

def run(root):
 d=root/'stage424';p=read(d/'analysis-plan.json');assert not(d/'analysis.json').exists();cpu=time.process_time();wall=time.perf_counter()
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 result=read(d/'result.json');decisions=read(d/'decisions-private.json') if (d/'decisions-private.json').exists() else [];policies={};runtime=[];allcandidate_force=0.;candidate_status={};rootdigests=[]
 for record in result['policies']:
  name=record['policy'];parent=read(d/('parent_'+name+'-private.json'));rows=parent['rows'];tires=[t for row in rows for t in row['tires']];steps=[x for x in decisions if x['policy']==name];policies[name]=dict(**record,selected_recipes=[x['selected_recipe'] for x in steps],selected_first_transition_all_passed=all(x['selected_first_check']['passed'] and x['selected_first_check']['wheel']['clipped_flag_mismatches']==0 for x in steps),max_force_ratio=max((t['force_ratio'] for t in tires),default=None),clipped_wheel_samples=sum(t['clipped'] for t in tires),wheel_samples=len(tires),confirmed_raw_ticks=sum(row['predicted']['raw_ticks'] for row in rows),new_states_actual_qualified=False)
 for path in sorted(d.glob('P_decision*-evidence-private.json'),key=lambda p:int(p.name.split('decision')[1].split('-')[0])):
  n=int(path.name.split('decision')[1].split('-')[0]);payload=load_receipt(path);ctx,ev=restore_typed(copy.deepcopy(payload));decision=choose(ctx,ev);expected=read(d/('P_decision'+str(n)+'-receipt-digest.json'));assert receipt_digest(payload)==expected['digest'] and expected['readback_verified'] and expected['parent_unchanged'];assert json_ready(asdict(decision))==payload['decision'] and not decision.actual_execution_allowed;state,mem,rng=ctx.parent.fork_inputs();assert state['provenance']=='CURRENT_MODEL_PARENT';rootdigests.append(state['immutable_actual_root_digest']);record=next((x for x in decisions if x['policy']=='P' and x['relative_decision']==n),None);elapsed=(n-1)*4;recipes={}
  for recipe,e in ev.items():
   key=e.tail_status;candidate_status[key]=candidate_status.get(key,0)+1
   assert (e.finish_ticks is None)==(e.tail_status!='FINISHED')
   recipes[recipe]=dict(status=e.tail_status,initial_actions=e.initial_actions,tail_actions=e.tail_actions_integrated,finish_ticks=None if e.finish_ticks is None else asdict(e.finish_ticks),root_projected_finish_ticks=None if e.finish_ticks is None else [e.finish_ticks.lo+elapsed,e.finish_ticks.hi+elapsed],safety13=e.safety_ok,progress13=e.progress_deadline_ok,actual_physics_qualified=False)
   full=read(d/('P_decision'+str(n)+'_'+recipe+'_1-private.json'));allcandidate_force=max(allcandidate_force,max((t['force_ratio'] for row in full['rows'] for t in row['tires']),default=0.))
  chosen=recipes[decision.recipe] if decision.recipe else None;runtime.append(dict(relative_decision=n,current_model_clock=ctx.parent.raw_clock_tick,receipt_digest_verified=True,typed_selector_equal=True,immutable_actual_root_digest_same=True,status=decision.status,chosen_recipe=decision.recipe,local_query_gain_rawticks=decision.gain_rawticks,root_projected_chosen_finish_ticks=None if chosen is None else chosen['root_projected_finish_ticks'],model_parent_action_committed=record is not None,recipes=recipes,actual_execution_allowed=False))
 if rootdigests:assert len(set(rootdigests))==1
 qualification=read(d/'qualification.json') if (d/'qualification.json').exists() else None
 cancellation=None
 if 'P' in policies and policies['P']['official_finish'] and runtime:
  first=runtime[0]['root_projected_chosen_finish_ticks'];last=runtime[-1]['root_projected_chosen_finish_ticks'];final=policies['P']['finish_ticks'];cancellation=dict(first_selected_witness_ticks=first,last_selected_witness_ticks=last,realized_model_finish_ticks=[final['lo'],final['hi']],first_witness_to_final_gain_bracket_s=None if first is None else [(first[0]-final['hi'])/50,(first[1]-final['lo'])/50],last_witness_to_final_gain_bracket_s=None if last is None else [(last[0]-final['hi'])/50,(last[1]-final['lo'])/50],overlapping_query_gains_not_summed=True)
 for f,h in read(d/'prior-preservation-manifest.json').items():assert sha(f)==h,f
 q=dict(stage=424,status=result['status'],error=result['error'],qualification=qualification,policies=policies,model_gain_bracket_s=result['model_remaining_finish_gain_bracket_s'],strict_model_gain=result['strict_model_gain'],runtime_receipts=runtime,distinct_candidate_status_counts=candidate_status,all_candidate_max_force_ratio=allcandidate_force,subsequent_cancellation=cancellation,cache_hits=0,new_actual_calls=0,new_states_actual_qualified=False,actual_gate_opened=False,historical423=dict(C0_actual_lap_ms=15080,P_three_decision_actual_lap_ms=14440,paired_actual_gain_s=.64,new424_actual_runs=0),budget=result['budget'],CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall);save(d/'analysis.json',q);print(json.dumps(dict(status=q['status'],model_gain=q['model_gain_bracket_s'],receipts=len(runtime),choices=[x['chosen_recipe'] for x in runtime],candidate_status=candidate_status,CPU_s=q['CPU_s'])))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
