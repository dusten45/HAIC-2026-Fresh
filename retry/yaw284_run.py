"""Two frozen GT-yaw-only steering feedback diagnostics on currentpixel240."""
import argparse,time,datetime
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha

def command(base,features,right_yaw,L=3.24):
 action=np.array(base,np.float32);f=np.array(features,float);v=f[4];valid=f[0]==0 and f[2]>0 and v>0 and np.isfinite(f).all() and np.isfinite(action).all() and np.isfinite(right_yaw)
 if not valid:return action,dict(applied=False)
 k=np.tan(float(action[0]))/L;error=k-right_yaw/v;steer=float(np.clip(np.arctan(L*(k+error)),-.4,.4));action[0]=np.float32(steer)
 return action,dict(applied=True,v_HUD=float(v),k_command=float(k),k_error=float(error),r_target=float(v*k),yaw_error_pre=float(v*k-right_yaw),steering_clip=abs(steer)==.4)
def run(path):
 from retry.frozen_composite_runtime import prepare
 from retry.diagnose import make_env
 p=read(path);D=path.parent;assert sha(path)==path.with_suffix('.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(Path(q))==h
 assert not (D/'opening.json').exists();save(D/'opening.json',dict(epoch=time.time()));results=[];error=None;cpu=time.process_time()
 try:
  for road in ['O0','N0']:
   F=D/road;assert not F.exists();F.mkdir(mode=0o700);worker=env=None;rows=[];start=time.perf_counter();rawticks=0;actwall=commitwall=simwall=0.
   try:
    worker=prepare(p['base'],F/'cpu',p['sandbox_path']);case=p['cases'][road];env=make_env();obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});raw=env.unwrapped;t0=raw.t;reset=round(t0*50);worker.call('reset',obs);cap=min(2000,4000-read(D/'budget.json')['actions']);assert cap>0
    for step in range(1,cap+1):
     assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();response,ms=worker.call('act',obs);actwall+=ms/1000;base=np.array(response['action'],np.float32);r=-float(raw.car.hull.angularVelocity)
     action,audit=command(base,response['features'],r);assert np.array_equal(action[1:],base[1:]);angle=float(raw.car.hull.angle);vel=np.array(raw.car.hull.linearVelocity);lateral=float(np.dot(vel,[np.cos(angle),np.sin(angle)]));forward=float(np.dot(vel,[-np.sin(angle),np.cos(angle)]))
     committed,cms=worker.call('commit',action);commitwall+=cms/1000;assert np.float32(committed['memory'])==action[0] and committed['history'][-1]==action.tolist()
     b=read(D/'budget.json');assert b['actions']<4000;b['actions']+=1;save(D/'budget.json',b);before=raw.t;tic=time.perf_counter();obs,_,ended,truncated,info=env.step(action);simwall+=time.perf_counter()-tic;rawticks+=round((raw.t-before)*50);complete=raw.finish_time_s is not None;official_limit=step==2000 and not complete;terminal=bool(ended or truncated or official_limit);postr=-float(raw.car.hull.angularVelocity)
     if audit['applied']:audit['yaw_error_after_same_precommand']=audit['r_target']-postr
     rows.append(dict(step=step,base=base.tolist(),action=action.tolist(),features=response['features'],audit=audit,right_yaw_pre=r,right_yaw_post=postr,lateral_velocity_diagnostic_only=lateral,forward_velocity_diagnostic_only=forward,memory=committed['state'],damage=env.damage.damage,collision=bool(info['collision']),terminal=terminal))
     if terminal:break
    applied=[row for row in rows if row['audit']['applied']];pre=np.array([row['audit']['yaw_error_pre'] for row in applied]);post=np.array([row['audit']['yaw_error_after_same_precommand'] for row in applied]);kerr=np.array([row['audit']['k_error'] for row in applied]);lap=round((raw.finish_time_s-t0)*1000) if complete else None
    out=dict(road=road,native_actions=step,completed=complete,actual_DNF=terminal and not complete,censored=not terminal,lap_ms=lap,baseline_lap_ms=p['baseline_lap_ms'][road],lap_delta_ms=lap-p['baseline_lap_ms'][road] if complete else None,retire_reason=None if complete else info.get('retire_reason') or ('max_steps' if official_limit else 'budget_cut'),damage=env.damage.damage,visited=raw.tile_visited_count,total_tiles=len(raw.track),yaw_feedback_actions=len(applied),fallback_actions=len(rows)-len(applied),steering_clip_actions=sum(row['audit'].get('steering_clip',False) for row in rows),current_call_pedals_exact_actions=len(rows),memory_verified_actions=len(rows),yaw_error_rad_s=dict(pre_RMSE=float(np.sqrt(np.mean(pre**2))) if len(pre) else None,after_same_precommand_RMSE=float(np.sqrt(np.mean(post**2))) if len(post) else None,pre_MAE=float(np.mean(abs(pre))) if len(pre) else None,pre_max_abs=float(max(abs(pre))) if len(pre) else None),k_error_RMSE_per_m=float(np.sqrt(np.mean(kerr**2))) if len(kerr) else None,max_abs_lateral_velocity_diagnostic=float(max(abs(row['lateral_velocity_diagnostic_only']) for row in rows)),raw_step_ticks=rawticks,raw_reset_ticks=reset,wall_s=time.perf_counter()-start,env_step_wall_s=simwall,act_IPC_wall_s=actwall,commit_IPC_wall_s=commitwall,actor_CPU_s=committed['actor_cumulative_CPU_s'],extra_GT_control='right_yaw=-hull.angularVelocity only',GT_diagnostic_not_legal_candidate=True,path_error_computed=False)
   finally:
    if worker:reaped=worker.close()
    if env:env.close()
   out['reaping']=reaped;save(F/'trace-private.json',rows);save(F/'result.json',out);results.append(out);save(D/'results-private.json',results);print(str(out),flush=True)
 except Exception as e:error=type(e).__name__+': '+str(e)
 save(D/'outcome-private.json',dict(results=results,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(D/'opening.json')['epoch'],CPU_s=time.process_time()-cpu))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
