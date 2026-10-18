"""Read-only551 full-path distributions, finish-tracker replay and budget audit."""
import hashlib,json,math,subprocess,time
from pathlib import Path
import numpy as np
from retry.plan513_model import load_root
from retry.lap518_finish import hull_pose,tracker_for
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response551-private')
def finite(x):
 if isinstance(x,float):return math.isfinite(x)
 if isinstance(x,list):return all(finite(a) for a in x)
 if isinstance(x,dict):return all(finite(a) for a in x.values())
 return True

def quantiles(values):
 a=np.asarray(values,float)
 return dict(samples=len(values),**{key:float(np.quantile(a,q)) if len(a) else None for key,q in [('min',0),('p01',.01),('p05',.05),('p25',.25),('median',.5),('p75',.75),('p95',.95),('p99',.99),('max',1)]})

def describe(data,static,ledger,kind,path):
 rows=data['trace'];case=data['summary'];completed=0 if kind=='cold' else ledger['completed_actions'];initial=static['root'] if kind=='cold' else json.loads(Path(ledger['checkpoint']).read_text())['before_root_without_roads'];root=load_root(dict(initial,roads=static['root']['roads']));visited=set(ledger['initial_visited'] if kind=='cold' else ledger['carry_visited']);tracker=tracker_for(static,root,visited,completed>0,1.02+.08*completed);margins=[];body=[];forces={'launch':[],'running':[]};overs=[];ratios=[];clipped=0;samples=0 if kind=='cold' else 352;launch_clips=launch_samples=0;maxclip=0.;finals=[];balance=0.;first_min=None;before=root
 for j,row in enumerate(rows):
  state=load_root(dict(row['root_without_roads'],roads=static['root']['roads']));v=max(math.hypot(*hull_pose(state)[1]),*(math.hypot(*(state.planar.linear.velocity[k]+w.offset[k] for k in range(2))) for w in state.planar.linear.wheels));body.append(v);margins.append(row['margin']);group='launch' if row['index']<=24 else 'running';f=max(x['ratio'] for x in row['forces']);forces[group].append(f)
  if group=='running':
   clipped+=sum(x['clipped'] for x in row['forces']);samples+=4;maxclip=max(maxclip,clipped/samples);ratios.append(clipped/samples);overs.append(math.hypot(*state.planar.linear.velocity)-row['target'])
  else:launch_clips+=sum(x['clipped'] for x in row['forces']);launch_samples+=4
  torque=sum(r[0]*f['vector'][1]-r[1]*f['vector'][0] for r,f in zip(before.planar.levers,row['forces']));M=before.planar.angular_momentum+.02*torque;yaw=(M-sum(I*q for I,q in zip(state.planar.wheel_inertias,state.planar.rates)))/state.planar.inertia;balance=max(balance,abs(M-state.planar.angular_momentum),abs(yaw-state.planar.yaw));before=state
  for ids in state.current_contacts:visited.update(ids)
  pose,velocity=hull_pose(state);tracker.update(pose,velocity,len(visited)/len(static['track']),1.02+.08*completed+.02*(j+1))
  if first_min is None or row['margin']<first_min['margin_m']:first_min=dict(action=row['index'],raw=row['raw'],margin_m=row['margin'],episode_s=.08*completed+.02*(j+1),station_fraction=row['progress']/path['length'])
 for command in data['commands']:
  detail=command['detail']
  for r in detail.get('reports',[]):
   if r['mode']=='FINAL':finals.append(dict(index=command['index'],ok=r['ok'],margin=r['min_footprint_margin_m'],source_mode=detail['mode']))
 finish=tracker.finish_time_s-1.02 if tracker.finish_time_s is not None else None;rawsafe=bool(rows and min(margins)>=.5 and max(body)<100 and max(forces['running'],default=0.)<=1.059 and max(overs,default=0.)<=4.85 and maxclip<=.1 and max(r['path_error'] for r in rows)<=3 and max(forces['launch'],default=0.)<=2.5 and (not launch_samples or (len(forces['launch'])<96 or launch_clips/launch_samples<=.15)))
 return dict(label=case['label'],coverage='whole_source_finish' if finish is not None else 'observed_prefix_only',raw_ticks=len(rows),actions=len(data['commands']),margin_m=quantiles(margins),margin_tail_counts={str(t):sum(x<t for x in margins) for t in [.5,.5251524480367317,.55,.6,1.]},min_margin_location=first_min,body_speed_m_s=quantiles(body),running_force_ratio=quantiles(forces['running']),launch_force_ratio=quantiles(forces['launch']),running_reference_overspeed_m_s=quantiles(overs),max_cumulative_running_clipping=maxclip,launch_clipped=launch_clips,launch_samples=launch_samples,selected_FINAL_margin_m=quantiles([x['margin'] for x in finals]),selected_FINAL_count=len(finals),selected_FINAL_all_ok=all(x['ok'] and x['margin']>=.5 for x in finals),raw_bounds_pass=rawsafe,source_finish_replayed_s=finish,source_torque_yaw_balance_max_error=balance,finite=finite(data))

def run():
 cpu=time.process_time();wall=time.perf_counter();read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();c=read(G/'retry/whole551_contract.json');static=read(Path('/workspace/haic-response515-private/collected-map-state-private.json'));ledger=read(Path('/workspace/haic-response519-private/model-ledger-private.json'));paths=read(D/'frozen-paths-private.json');checks=dict(source_pins=all(sha(G/p)==h for p,h in c['source_sha256'].items()),private_input_pins=all(sha(Path(p))==h for p,h in c['private_inputs_sha256'].items()),fixed549_profile=sha(D/'frozen-paths-private.json')==c['fixed_path_sha256'],original549_failure_preserved=not read(G/'retry/retime549_pilot_result.json')['passed'],original550_failure_preserved=not read(G/'retry/yaw550_completion_result.json')['passed']);descriptions={};phases={};total=dict(model_ticks=0,force=0,geometry=0,CPU_s=0.,wall_s=0.)
 for kind in ['cold','carry']:
  baseline=read(Path('/workspace/haic-response541-private')/(kind+'-candidate-private.json'));descriptions['baseline541-'+kind]=describe(baseline,static,ledger,kind,paths['baseline']);p=G/('retry/whole551_'+kind+'_result.json')
  if not p.exists():continue
  r=read(p);phases[kind]=dict(passed=r['passed'],technical_error=r.get('technical_error'),model_ticks=r['model_integrator_ticks'],CPU_s=r['CPU_s']);lim=c['phase_caps'][kind];checks[kind+'_STARTED_pin']=read(D/(kind+'-STARTED.json'))['contract_sha256']==sha(G/'retry/whole551_contract.json');checks[kind+'_caps']=r['model_integrator_ticks']<=lim['model_ticks'] and r['explicit_force_evaluations']<=lim['force'] and r['planner_cost']['geometry_checks']<=lim['geometry'] and r['CPU_s']<=lim['CPU_s'] and r['wall_s']<=lim['wall_s'];checks[kind+'_all_model_body_checked']=r['planner_cost']['model_body_checks']==r['model_integrator_ticks'] and r['planner_cost']['max_all_model_body_speed_m_s']<100;checks[kind+'_actual0']=r['native_actions']==r['native_resets']==0
  total['model_ticks']+=r['model_integrator_ticks'];total['force']+=r['explicit_force_evaluations'];total['geometry']+=r['planner_cost']['geometry_checks'];total['CPU_s']+=r['CPU_s'];total['wall_s']+=r['wall_s']
  for case in r['cases']:
   data=read(D/(case['label']+'-private.json'));d=describe(data,static,ledger,kind,paths['candidate']);descriptions['candidate551-'+kind]=d;checks[kind+'_saved_summary']=case==data['summary'];checks[kind+'_finite']=d['finite'];checks[kind+'_force_balance']=d['source_torque_yaw_balance_max_error']<1e-10;checks[kind+'_FINALs']=d['selected_FINAL_all_ok'];checks[kind+'_raw_report_consistent']=case['min_margin_m']<=d['margin_m']['min']+1e-12 and abs(case['max_cumulative_clipping_fraction']-d['max_cumulative_running_clipping'])<1e-12
   finish=d['source_finish_replayed_s'];checks[kind+'_finish_replay']=finish is None if case['model_finish_episode_s'] is None else finish is not None and abs(finish-case['model_finish_episode_s'])<1e-10;checks[kind+'_safe_finish_flag']=case['pass_safety']==bool(d['raw_bounds_pass'] and finish is not None and case['first_failure'] is None)
   if case['pass_safety']:
    base=descriptions['baseline541-'+kind]['source_finish_replayed_s'];ms=round(base*1000)-round(finish*1000);checks[kind+'_effect_gate']=r['passed']==(ms>=(500 if kind=='cold' else 0)) and r['gain_vs541_ms']==ms
   else:checks[kind+'_stopped_not_promoted']=not r['passed']
 checks['aggregate_caps']=all(total[k]<=c['aggregate_caps'][k] for k in total);cold=read(G/'retry/whole551_cold_result.json');checks['carry_condition']=cold['passed'] or not (D/'carry-STARTED.json').exists();checks['no_actual_execution']=not any((D/(p+'-STARTED.json')).exists() for p in ['native','actual']);checks['main_preserved']=subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31';out=dict(passed=all(checks.values()),checks=checks,phases=phases,distributions=descriptions,total_new_scientific_cost=total,baseline_model_ticks_recomputed=0,new_model_ticks_in_audit=0,new_native_actions=0,research_remaining=22758,reserve=84000,reserve_used=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 with (G/'retry/whole551_audit.json').open('x') as f:json.dump(out,f,indent=2,allow_nan=False)
 print(json.dumps({k:out[k] for k in ['passed','checks','phases','total_new_scientific_cost','CPU_s']},indent=2));assert out['passed']
if __name__=='__main__':run()
