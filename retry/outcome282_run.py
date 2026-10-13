"""One actual runner per macro: own exact prefix then3actions then fullpixel240."""
import argparse,time,datetime,hashlib
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha

def run(path):
 from retry.frozen_composite_runtime import prepare
 from retry.diagnose import make_env
 from retry.source_vehicle_transition import capture
 D=path.parent;p=read(path);assert sha(path)==path.with_suffix('.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(Path(q))==h
 assert not (D/'opening.json').exists(),'No automatic replay after interruption'
 save(D/'opening.json',dict(epoch=time.time()));results=[];error=None;cpu=time.process_time();cache=np.load(p['cache']);ref=read(Path(p['materialized']))
 try:
  for job in p['jobs']:
   q,macro=job['anchor'],job['macro'];name=str(q)+'_'+macro;F=D/name;assert not F.exists();F.mkdir(mode=0o700);worker=env=None;rows=[];rawticks=0;prefix_ok=True;mismatch=None;phasecounts={};start=time.perf_counter();simwall=actwall=commitwall=0.;reset_ticks=0
   try:
    remaining=p['shard_native_cap']-read(D/'budget.json')['actions'];assert remaining>=650,'Insufficient cap to start new run'
    worker=prepare(p['base'],F/'cpu',p['sandbox_path']);env=make_env();obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});t0=env.unwrapped.t;reset_ticks=round(t0*50);worker.call('reset',obs)
    for step in range(1,651):
     assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();phase='prefix' if step<q else 'macro' if step<q+3 else 'continuation'
     if step<=q:
      match=np.array_equal(obs,cache['observations'][step-1]);prefix_ok &= match
      if not match and mismatch is None:mismatch=dict(step=step,field='observation')
     r,ms=worker.call('act',obs);actwall+=ms/1000;base=np.array(r['action'],np.float32);action=base.copy()
     if step<=q:
      match=np.array_equal(base,cache['commands'][step-1]);prefix_ok &= match
      if not match and mismatch is None:mismatch=dict(step=step,field='baseline_action')
     if step==q:
      boundary_ok=capture(env)==ref['snapshots'][str(q)];prefix_ok &= boundary_ok
      if not boundary_ok and mismatch is None:mismatch=dict(step=step,field='snapshot_boundary')
     if phase=='macro':
      if macro=='gas_upper':action[1]=np.float32(np.clip(np.clip(float(r['nominal'][1])+.5,0,1)*p['scales'][0],0,1))
      elif macro=='brake_lower':action[2]=np.float32(np.clip(np.clip(float(r['nominal'][2])-.5,0,1)*p['scales'][1],0,1))
      else:action[0]=np.float32(np.clip(float(base[0])+(.015 if macro=='steer_plus' else -.015),-.4,.4))
     c,cms=worker.call('commit',action);commitwall+=cms/1000;assert np.float32(c['memory'])==action[0] and c['history'][-1]==action.tolist()
     b=read(D/'budget.json');assert b['actions']<p['shard_native_cap'];b['actions']+=1;b['phases'][phase]=b['phases'].get(phase,0)+1;save(D/'budget.json',b);phasecounts[phase]=phasecounts.get(phase,0)+1
     old=env.unwrapped.t;tic=time.perf_counter();obs,_,ended,truncated,info=env.step(action);simwall+=time.perf_counter()-tic;rawticks+=round((env.unwrapped.t-old)*50);complete=env.unwrapped.finish_time_s is not None;terminal=bool(ended or truncated)
     rows.append(dict(step=step,phase=phase,base=base.tolist(),action=action.tolist(),nominal=r['nominal'],features=r['features'],memory=c['state'],history=c['history'],damage=env.damage.damage,collision=bool(info['collision']),obs_sha256=hashlib.sha256(obs.tobytes()).hexdigest(),terminal=terminal))
     if terminal:break
    lap=round((env.unwrapped.finish_time_s-t0)*1000) if complete else None
    out=dict(road=p['road'],name=name,anchor=q,macro=macro,native_actions=step,phase_actions=phasecounts,completed=complete,actual_DNF=terminal and not complete,censored=not terminal,lap_ms=lap,baseline_lap_ms=p['baseline_lap_ms'],lap_delta_ms=lap-p['baseline_lap_ms'] if complete else None,comparable=prefix_ok,first_prefix_mismatch=mismatch,snapshot_boundary_exact=boundary_ok if step>=q else None,improved=bool(prefix_ok and complete and lap<p['baseline_lap_ms']),damage=env.damage.damage,visited=env.unwrapped.tile_visited_count,total_tiles=len(env.unwrapped.track),retire_reason=None if complete else info.get('retire_reason') or 'budget_cut',raw_step_ticks=rawticks,raw_reset_ticks=reset_ticks,wall_s=time.perf_counter()-start,env_step_wall_s=simwall,act_IPC_wall_s=actwall,commit_IPC_wall_s=commitwall,actor_CPU_s=c['actor_cumulative_CPU_s'],memory_history_verified=True,current_pixel_commands=True)
   finally:
    if worker:reaped=worker.close()
    if env:env.close()
   out['reaping']=reaped;save(F/'trace-private.json',rows);save(F/'result.json',out);results.append(out);save(D/'results-private.json',results);print(str({k:out[k] for k in ['road','name','completed','actual_DNF','censored','lap_ms','lap_delta_ms','comparable','native_actions']}),flush=True)
 except Exception as e:error=type(e).__name__+': '+str(e)
 save(D/'outcome-private.json',dict(results=results,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(D/'opening.json')['epoch'],CPU_s=time.process_time()-cpu))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
