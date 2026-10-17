"""Stored-only verification/aggregation of completed421; no physics world or actuator."""
import json,sys,time
from dataclasses import asdict
from pathlib import Path
from retry.loss389_analyze import read,save,sha
from retry.receipt421_io import load_receipt,receipt_digest
from retry.preflight421 import restore_typed
from retry.planner419 import choose
from retry.pilot420_json import json_ready

def prepare(root):
 d=root/'stage421';assert not(d/'analysis-plan.json').exists();p=read(d/'plan.json');files=[Path(__file__),d/'plan.json',d/'result.json',d/'qualification.json',d/'decisions-private.json',d/'parent_C0-private.json',d/'parent_P-private.json',d/'preflight-result.json',d/'original420-manifest.json']+list(d.glob('P_decision*-evidence-private.json'))+list(d.glob('P_decision*-receipt-digest.json'))
 q=dict(stage=421,scope='Storedonly: verifyallruntimefullreceiptdigests/typedselector, currentscope/provenance,6parenttransitions, clipping+costscopes. Nointegration/refit/actual. Completed421comparisonkeptseparatefrom420singlewitness.',sources={str(f):sha(f) for f in files},protected=p['protected'],original408_preserve=p['original408_preserve']);save(d/'analysis-plan.json',q);(d/'analysis-plan.sha256').write_text(sha(d/'analysis-plan.json')+'\n');print('421 storedanalysis frozen')
def run(root):
 d=root/'stage421';p=read(d/'analysis-plan.json');assert not(d/'analysis.json').exists()
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h
 for f,h in read(d/'original420-manifest.json').items():assert sha(f)==h
 cpu=time.process_time();wall=time.perf_counter();result=read(d/'result.json');assert result['status']=='MODEL_CLOSEDLOOP_PILOT_COMPLETED' and result['decision_count']==6;dec=read(d/'decisions-private.json');receipt_checks=[];policy={};actualdigests=[]
 for n in range(1,4):
  path=d/('P_decision'+str(n)+'-evidence-private.json');payload=load_receipt(path);expected=read(d/('P_decision'+str(n)+'-receipt-digest.json'));digest=receipt_digest(payload);assert digest==expected['digest'] and expected['readback_verified'] and expected['parent_unchanged'];ctx,ev=restore_typed(payload);proposal=choose(ctx,ev);assert json_ready(asdict(proposal))==payload['decision'];assert not proposal.actual_execution_allowed;assert not any(e.long_tail_physics_qualified for e in ev.values());state,mem,rng=ctx.parent.fork_inputs();actualdigests.append(state['immutable_actual_root_digest']);receipt_checks.append(dict(relative_decision=n,receipt_digest_verified=True,typed_selector_equal=True,parent_root_current_clock=ctx.parent.raw_clock_tick,chosen_recipe=proposal.recipe,status=proposal.status,local_query_gain_rawticks=proposal.gain_rawticks,full_receipt_bytes=path.stat().st_size,long_tail_physics_qualified=False))
 assert len(set(actualdigests))==1
 for name in ['C0','P']:
  parent=read(d/('parent_'+name+'-private.json'));rows=parent['rows'];ts=[z for row in rows for z in row['tires']];pol=next(x for x in result['policies'] if x['policy']==name);assert pol['decisions']==3 and pol['official_finish'] and pol['predicted_progress_goal_ok'];steps=[x for x in dec if x['policy']==name];assert len(steps)==3 and all(x['selected_first_check']['passed'] for x in steps)
  policy[name]=dict(**pol,selected_recipes=[x['selected_recipe'] for x in steps],model_parent_first_transitions_passed=True,max_force_ratio=max(z['force_ratio'] for z in ts),clipped_wheel_samples=sum(z['clipped'] for z in ts),total_wheel_samples=len(ts),confirmed_raw_ticks=sum(z['predicted']['raw_ticks'] for z in rows),current_input_model_clock_ticks=[x['parent_model_clock']-4 for x in steps])
 qual=read(d/'qualification.json');qualmax={label:dict(passed=all(z['passed'] for z in checks),max_body_position_m=max(z['body']['errors']['position_m'] for z in checks),max_body_speed_m_s=max(z['body']['errors']['speed_m_s'] for z in checks),max_wheel_omega_rad_s=max(z['wheel']['max_errors']['omega'] for z in checks),max_force_ratio_error=max(z['wheel']['max_errors']['force_ratio'] for z in checks),max_raw_hull_origin_error_m=max(z['hull']['max_errors']['origin_position_m'] for z in checks)) for label,checks in qual['actual13_checks'].items()};q=dict(stage=421,status='COMPLETED_MODEL_CLOSEDLOOP_COMPARISON',policies=policy,model_gain_bracket_s=result['model_remaining_finish_gain_bracket_s'],strict_model_gain=result['model_strict_gain'],runtime_receipts=receipt_checks,immutable_actual_root_digest_constant=True,qualification_actual13_passed=qual['passed'],qualification_actual13_max=qualmax,initial_parent_gate=qual['parent_first_step']['passed'],prior420_preserved=True,actual_opened=False,new_model_or_actual_calls=0,new_states_and_long_tail_actual_physics_qualified=False,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall);save(d/'analysis.json',q);print(json.dumps({k:v for k,v in q.items() if k not in ['qualification_actual13_max']}))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
