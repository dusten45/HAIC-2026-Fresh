"""Saved-only 433 receipt, early-binding, clipping, censoring and cost readout."""
import copy,json,sys,time
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.preflight421 import restore_typed
from retry.receipt421_io import load_receipt,receipt_digest
from retry.audit431 import choose,from_wire
from retry.pilot420_json import json_ready
from retry.executor397 import canonical_projection
from retry.paired417_common import arrival

def run(root):
 d=root/'stage433';assert not(d/'analysis.json').exists();cpu=time.process_time();wall=time.perf_counter();p=read(d/'plan.json');result=read(d/'result.json');records=read(d/'decisions-private.json') if (d/'decisions-private.json').exists() else [];checks=[];early=[];statuses={};roots=[]
 for path in sorted(d.glob('P_decision*-evidence-private.json'),key=lambda x:int(x.name.split('decision')[1].split('-')[0])):
  payload=load_receipt(path);ctx,ev=restore_typed(copy.deepcopy(payload));ee={r:from_wire(x) for r,x in payload['early_evidence'].items()};ev.update(ee);decision=choose(ctx,ev);assert json_ready(asdict(decision))==payload['decision'];digest=read(d/(path.name.replace('-evidence-private.json','-receipt-digest.json')));assert receipt_digest(payload)==digest['digest'] and digest['parent_unchanged'] and digest['RNG_unchanged'];proof=payload['preintegration'];assert sha(proof['path'])==proof['sha256'];before=load_receipt(proof['path']);assert before['context']==payload['context'];assert before['qualification_passed'];roots.append(ctx.parent.fork_inputs()[0]['immutable_actual_root_digest'])
  for r,e in ev.items():
   statuses[e.tail_status]=statuses.get(e.tail_status,0)+1
   if r in ee:
    e.authenticate(ctx);assert e.binding_scope=='LIVE_BEFORE_QUERY_CAPTURE' and e.root==ctx.parent.stamp() and e.finish_ticks is None and not e.admissible13() and not e.actual_execution_allowed
    early.append(dict(query=path.name.split('-')[0],recipe=r,observed_actions=e.observed_actions,reasons=list(e.stop_reasons),cost=asdict(e.cost),authenticated=True,finish_ticks=None))
   if e.tail_status!='FINISHED':assert e.finish_ticks is None
  checks.append(dict(query=path.name.split('-')[0],selected_recipe=decision.recipe,status=decision.status,receipt_and_choice_verified=True,early_count=len(ee),actual_execution_allowed=decision.actual_execution_allowed))
 assert len(set(roots))<=1
 policies={};fixed=read(Path(p['fixed_plan']));line=np.asarray(fixed['line']);L=sum(fixed['free_profile']['ds']);markers={}
 for name in ['C0','P']:
  f=d/('parent_'+name+'-private.json')
  if not f.exists():continue
  parent=read(f);rows=parent['rows'];ts=[t for z in rows for t in z['tires']];steps=[x for x in records if x['policy']==name];rr=next((x for x in result['policies'] if x['policy']==name),{})
  policies[name]=dict(**rr,saved_status=parent['status'],observed_actions=len(rows),confirmed_raw_ticks=sum(z['predicted']['raw_ticks'] for z in rows),selected_recipes=[x['selected_recipe'] for x in steps],planner_decisions_observed=sum(x['planner_used'] for x in steps),guardian_decisions_observed=sum(not x['planner_used'] for x in steps),selected_first_all_passed=all(x['selected_first_check']['passed'] and x['selected_first_check']['wheel']['clipped_flag_mismatches']==0 for x in steps),damage=parent['final_state']['physical']['damage'] if 'damage' in parent['final_state']['physical'] else None,max_post_path_error_m=max((z['path_error_m'] for z in rows),default=None),max_force_ratio=max((t['force_ratio'] for t in ts),default=None),clipped_wheel_samples=sum(t['clipped'] for t in ts),wheel_samples=len(ts),new_states_actual_qualified=False,query_CPU_max_s=max((x['query_CPU_s'] for x in steps),default=None),query_wall_max_s=max((x['query_wall_s'] for x in steps),default=None))
  if rows:
   h=rows[0]['raw_hull'][0];start=canonical_projection(line,h['origin_position'],h['COM_linear_velocity'],'FIRST_LAP')['arc'];markers[name]={str(frac):arrival(rows,line,start,frac*L) for frac in [.70,.75,.80,.85,.90,.95] if frac*L>start}
 gains={}
 if all(x in markers for x in ['C0','P']):
  for key,x in markers['C0'].items():
   y=markers['P'].get(key);u=x.get('rawtick_bracket');v=y.get('rawtick_bracket') if y else None;gains[key]=[(u[0]-v[1])/50,(u[1]-v[0])/50] if x['reached'] and y and y['reached'] else None
 for f,h in read(d/'prior-preservation-manifest.json').items():assert sha(f)==h,f
 q=dict(stage=433,status=result['status'],error=result['error'],policies=policies,runtime_receipts=checks,authenticated_early_records=early,candidate_status_counts=statuses,model_gain_bracket_s=result['model_remaining_finish_gain_bracket_s'],strict_model_gain=result['strict_model_gain'],observed_model_arc_gain_brackets_s=gains,cache_hits=0,new_actual_calls=0,new_states_actual_qualified=False,actual_gate_opened=False,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall);save(d/'analysis.json',q);print(json.dumps(dict(status=q['status'],receipts=len(checks),early=len(early),policies={k:dict(status=v.get('status',v['saved_status']),actions=v['observed_actions']) for k,v in policies.items()},gain=q['model_gain_bracket_s'],CPU_s=q['CPU_s'])))
if __name__=='__main__':run(Path(sys.argv[1]))
