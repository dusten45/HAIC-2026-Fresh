"""Stored-only carry accounting; no trajectory extrapolation or new model calls."""
import datetime,json,math,sys,time,signal
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.executor397 import canonical_projection
G=Path(__file__).resolve().parent.parent

def run(root):
 d=root/'stage414';assert not(d/'analysis.json').exists();files=[Path(__file__),d/'plan.json',d/'result.json',d/'trace-private.jsonl',d/'final-private.json',root/'stage404/O_268/trace-private.jsonl',root/'stage404/O_268/final-full-private.json',root/'stage413/actual_A/trace-private.jsonl',root/'stage413/actual_B/trace-private.jsonl',root/'stage413/source-anchor-private.json'];save(d/'analysis-plan.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Savedactual/rawwheel/hull andhistoricalOonly; sameoriginalarccrossingbrackets, fixedbins+allbaselinepostarcs, controlatstall algebra; no sourcecall/remaininglapimputation/newcontrol/tuning.',sources={str(f):sha(f) for f in files},new_native_model_actor_learning_SEALED=0));cpu=time.process_time();wall=time.perf_counter();r=read(d/'result.json');p=read(d/'plan.json');fixed=read(Path(p['fixed_plan']));line=np.asarray(fixed['line']);L=sum(fixed['free_profile']['ds']);new=[json.loads(s) for s in (d/'trace-private.jsonl').read_text().splitlines()];old=[json.loads(s) for s in (root/'stage404/O_268/trace-private.jsonl').read_text().splitlines()];oldraw=[json.loads(s) for s in (root/'stage413/actual_A/trace-private.jsonl').read_text().splitlines()];oldft=read(root/'stage404/O_268/final-full-private.json')['wrapper']['finish_time_s'];assert all(a['post']==b['post'] and a['command']==b['command'] for a,b in zip(oldraw,old));anchor=read(root/'stage413/source-anchor-private.json')
 def samples(rows,raw_until,finish=None):
  t0=rows[0]['pre']['time'];out=[];s=0.;prev=None
  for row in rows:
   points=[]
   if row['step']<=raw_until:
    points += [(h['time'],h['origin_position'],h['origin_linear_velocity'],math.hypot(*h['COM_linear_velocity']),h['yaw']) for h in row['raw_hull']]
   points.append((row['post']['time'],row['post']['pos'],row['post']['vel'],row['post']['speed'],row['post']['yaw']))
   for t,pos,vel,v,yaw in points:
    if finish is not None and t>finish+1e-8:continue
    q=canonical_projection(line,pos,vel,'FIRST_LAP');a=q['arc']
    if prev is None:prev=a
    s+=(a-prev+L/2)%L-L/2;prev=a
    z=dict(t=t-t0,s=s,speed=v,yaw=yaw,path_error=q['path_error_m'],step=row['step'])
    if out and abs(out[-1]['t']-z['t'])<1e-8:
     assert abs(out[-1]['s']-z['s'])<1e-6;out[-1]=z
    else:out.append(z)
  return out
 # Fill only baseline raw-prefix129; later baseline remains wrapperresolution.
 baseline=[dict(z,raw_hull=oldraw[i]['raw_hull'] if i<129 else []) for i,z in enumerate(old)];B=samples(baseline,129,oldft);N=samples(new,310,None)
 def cross(data,target):
  for a,b in zip(data,data[1:]):
   if a['s']<target<=b['s']:return dict(reached=True,time_bracket_s=[a['t'],b['t']],before_step=a['step'],after_step=b['step'],before_speed=a['speed'],after_speed=b['speed'],before_yaw=a['yaw'],after_yaw=b['yaw'],before_path_error=a['path_error'],after_path_error=b['path_error'],overshoot_m=b['s']-target)
  return dict(reached=False,time_bracket_s=None)
 def comparepoint(label,target):
  b=cross(B,target);n=cross(N,target);gain=None
  if b['reached'] and n['reached']:gain=[b['time_bracket_s'][0]-n['time_bracket_s'][1],b['time_bracket_s'][1]-n['time_bracket_s'][0]]
  return dict(label=label,reference_fraction=target/L,baseline=b,new=n,gain_bracket_s=gain)
 targets=[('fraction_'+str(j),L*j/10) for j in range(1,10)];targets += [('H1_exit',anchor['start_arc']+30),('413_suffix_end',anchor['start_arc']+read(root/'stage413/actual_B/result.json')['arrival']['progress_m'])];milestones=[comparepoint(label,target) for label,target in targets]
 carry=[]
 for z in B:
  if anchor['start_arc']+30<=z['s']<=N[-1]['s'] and z['step']>129:
   # One point per old wrapper endpoint, not an optimizer-selected sample.
   if abs(z['t']-old[z['step']-1]['post']['time']+old[0]['pre']['time'])<1e-8:carry.append(comparepoint('oldpost_'+str(z['step']),z['s']))
 def agg(rows,lo,hi,finish):
  dt=brake=gas=coast=below=front=rear=0.;frontmax=rearmax=slipmax=0.;vtotal=0.;selected=[]
  for row in rows:
   phase='FIRST_LAP';q=canonical_projection(line,row['pre']['pos'],row['pre']['vel'],phase);a=q['arc']
   if row['step']==1 and a==L:a=0.
   if not lo<=a<hi:continue
   w=max(0,min(row['post']['time'],finish)-row['pre']['time']);ts=row['raw_tire_samples'];ff=[z for z in ts if z['wheel']<2];rr=[z for z in ts if z['wheel']>=2];dt+=w;brake+=w*(row['command'][2]>0);gas+=w*(row['command'][1]>0);coast+=w*(row['command'][1]==row['command'][2]==0);target=row.get('cursor',{}).get('target',row.get('reference',{}).get('r'));below+=w*(target is not None and row['pre']['speed']<target and row['command'][2]>0);front+=w*sum(z['clipped'] for z in ff)/len(ff);rear+=w*sum(z['clipped'] for z in rr)/len(rr);frontmax=max(frontmax,max(z['force_ratio'] for z in ff));rearmax=max(rearmax,max(z['force_ratio'] for z in rr));slipmax=max(slipmax,max(abs(z['lateral_slip_m_s']) for z in rr));vtotal+=w*row['pre']['speed'];selected.append(row['step'])
  return dict(actions=len(selected),time_prearc_attributed_s=dt,brake_s=brake,gas_s=gas,coast_s=coast,braking_below_target_s=below,front_clip_weighted_s=front,rear_clip_weighted_s=rear,front_qmax=frontmax,rear_qmax=rearmax,rear_lateral_slip_max_m_s=slipmax,mean_pre_speed=vtotal/dt if dt else None,first_action=selected[0] if selected else None,last_action=selected[-1] if selected else None)
 end=new[-1]['post']['time'];bins=[dict(reference_fraction=[j/10,(j+1)/10],baseline=agg(old,L*j/10,L*(j+1)/10,oldft),new=agg(new,L*j/10,L*(j+1)/10,end)) for j in range(10)]
 last=new[-1];c=last['cursor'];raw_zero=c['feed']+1.5*c['target'];goal_relative=last['goal_before']-new[0]['progress_before'];gap=last['goal_before']-last['progress_after'];stallfirst=next((z for z in new if z['step']>129 and z['post']['speed']<1e-3),None);brake_start=last['step']
 for z in reversed(new):
  if z['command'][1]==0 and z['command'][2]>0:brake_start=z['step']
  else:break
 first_certain_loss=next((z for z in carry if z['gain_bracket_s'] is not None and z['gain_bracket_s'][1]<-1e-8),None)
 out=dict(stage=414,status='COMPLETED_STORED_CARRY_ANALYSIS',actual_run_status=r['status'],derived_stop_category='PROGRESS_DEADLINE_CENSORED',official_lap=None,remaining_lap_imputed=False,source_long_fidelity_claim=False,reference_O_historical_lap_s=14.78,observed_elapsed_s=end-new[0]['pre']['time'],max_recorded_progress_m=N[-1]['s'],last_reference_fraction=N[-1]['s']/L,milestones=milestones,all_baseline_postarc_carry_points=carry,first_certain_loss_marker=first_certain_loss,spatial_bins=bins,bin_attribution='prearc assignment fullactionofficialscoredtime, notexactcrossingsegmentation; sameforboth. Stop/repeatedarc time keptinbin.',raw_crossing='New20ms, baseline413Arawthrough129then40480msboundary, nointerpolatedarrival. Sameoriginalreferenceprogressnotidenticalpose/velocity.',stop_state=dict(step=196,elapsed_s=end-new[0]['pre']['time'],speed_m_s=last['post']['speed'],path_error_m=last['post_projection']['path_error_m'],damage=last['damage'],goal_reference_fraction=goal_relative/L,goal_distance_remaining_m=gap,goal_deadline_action=last['deadline_before'],brake_burst_start_step=brake_start,near_rest_first_step=stallfirst['step'] if stallfirst else None,target_speed=c['target'],feed=c['feed'],clamped_accel=c['clamped_accel'],command_brake=last['command'][2],raw_request_if_speed_zero=raw_zero,algebra_scope='Observedfixedcursor/target/feed law atnearrest, notnewforwardrollout ornewparameterproposal.'),actual_progress_violation=True,physical_safety_flags=sum(bool(z['safety']) for z in new),official_finish_qualified=read(d/'final-private.json')['wrapper']['finish_qualified_time_s'] is not None,new_model_actor_native_learning_SEALED_during_analysis=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall);assert r['reproduced_prefix_rows']==116 and r['reproduced_suffix_rows']==13 and r['existing13_model_fidelity_pass'] and not r['official_finish_observed'];save(d/'analysis.json',out);save(d/'crossing-samples-private.json',dict(baseline=B,new=N));print(json.dumps({k:v for k,v in out.items() if k not in ['all_baseline_postarc_carry_points','spatial_bins']},ensure_ascii=False));print(json.dumps(dict(spatial_bins=bins),ensure_ascii=False))
if __name__=='__main__':run(Path(sys.argv[1]))
