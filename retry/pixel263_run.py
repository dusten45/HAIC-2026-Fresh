"""One legal pixel local-profile pilot on the two previously used DEV roads."""
import argparse,json,time,hashlib,datetime
from pathlib import Path
import numpy as np

def run(path):
 from retry.frozen_composite_runtime import prepare
 from retry.diagnose import make_env
 D=path.parent;p=json.loads(path.read_text())
 def read(q):return json.loads(q.read_text())
 def sha(q):return hashlib.sha256(Path(q).read_bytes()).hexdigest()
 def save(q,x):
  t=q.with_name(q.name+'.tmp');t.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');t.chmod(0o600);t.replace(q)
 assert sha(path)==path.with_suffix('.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(q)==h
 assert not (D/'opening.json').exists(),'No replay of started evaluations'
 save(D/'opening.json',dict(epoch=time.time()));results=[];error=None;cpu=time.process_time()
 try:
  for road in ['O0','N0']:
   folder=D/road;assert not folder.exists();folder.mkdir(mode=0o700);env=worker=None;records=[];compute=[];ipc=[];planning=[];ticks=0;start=time.perf_counter();remaining=2072-read(D/'budget.json')['actions'];assert remaining>0
   try:
    worker=prepare(p['candidate'],folder/'cpu',p['sandbox_path']);save(folder/'ready-private.json',worker.ready);env=make_env();case=p['cases'][road];obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});assert hashlib.sha256(obs.tobytes()).hexdigest()==p['initial_observations'][road];start_t=env.unwrapped.t;resetticks=round(start_t*50);worker.call('reset',obs)
    for step in range(1,min(2000,remaining)+1):
     assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();response,ms=worker.call('act',obs);assert ms<=5000;assert not response['python_audit_denied_events'];audit=response['planner_audit'];assert audit['steering_unchanged'] and audit['nominal_memory_preserved'];action=np.asarray(response['action'],np.float32);compute.append(response['act_compute_ms']);ipc.append(ms);planning.append(audit['planner_ms']);b=read(D/'budget.json');assert b['actions']<2072;b['actions']+=1;save(D/'budget.json',b);before=env.unwrapped.t;obs,_,ended,truncated,info=env.step(action);ticks+=round((env.unwrapped.t-before)*50);complete=env.unwrapped.finish_time_s is not None;terminal=bool(ended or truncated or step>=2000);records.append(dict(step=step,action=action.tolist(),planner=audit,damage=env.damage.damage,collision=bool(info['collision']),visited=env.unwrapped.tile_visited_count,features=response['features'],nominal_state=response['nominal_state']))
     if terminal or step==min(2000,remaining):break
    active=[r for r in records if r['planner']['active']];r=dict(road=road,completed=complete,actual_DNF=terminal and not complete,censored=not terminal,lap_ms=round((env.unwrapped.finish_time_s-start_t)*1000) if complete else None,native_actions=step,retire_reason=info.get('retire_reason') or ('max_steps' if step>=2000 else 'budget_cut' if not terminal else None),damage=env.damage.damage,visited=env.unwrapped.tile_visited_count,total_tiles=len(env.unwrapped.track),planner_active_actions=len(active),fallback_actions=len(records)-len(active),first_collision=next((x['step'] for x in records if x['collision']),None),raw_step_ticks=ticks,raw_reset_ticks=resetticks,wall_s=time.perf_counter()-start,planning_ms=dict(median=float(np.median(planning)),p95=float(np.percentile(planning,95)),max=float(max(planning)),sum=float(sum(planning))),full_Agent_compute_ms=dict(median=float(np.median(compute)),p95=float(np.percentile(compute,95)),max=float(max(compute))),IPC_ms=dict(median=float(np.median(ipc)),p95=float(np.percentile(ipc,95)),max=float(max(ipc))),actor_CPU_s=response['actor_cumulative_CPU_s'],pixel_only=True,privileged_policy_inputs=False,archive_sha256=p['candidate']['archive_sha256'])
   finally:
    if worker:reaping=worker.close()
    if env:env.close()
   r['reaping']=reaping;save(folder/'trajectory-private.json',records);save(folder/'result.json',r);results.append(r);save(D/'results-private.json',results);print(json.dumps(r),flush=True)
 except Exception as e:error=type(e).__name__+': '+str(e)
 save(D/'outcome-private.json',dict(stage=263,results=results,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(D/'opening.json')['epoch'],CPU_s=time.process_time()-cpu))

if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
