"""Six independent actual pedal pulses, with current-pixel240 steering/continuation.

Pulse-channel values are fixed249 selections; other pedal and steering remain
current240. No state restore, fit, model query, goal-stop or repeated rollout.
"""
import argparse,json,time,datetime,hashlib
from pathlib import Path
import numpy as np


def run(path):
 from retry.frozen_composite_runtime import prepare
 from retry.diagnose import make_env
 from retry.full_route_reproduction import truth
 from retry.source_vehicle_transition import capture
 from retry.receding_horizon_oracle import contiguous_visited_tiles
 p=json.loads(path.read_text());D=path.parent
 def sha(q):return hashlib.sha256(Path(q).read_bytes()).hexdigest()
 def read(q):return json.loads(q.read_text())
 def save(q,x):
  t=q.with_name(q.name+'.tmp');t.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');t.chmod(0o600);t.replace(q)
 assert sha(path)==path.with_suffix('.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(q)==h
 if not (D/'opening.json').exists():save(D/'opening.json',dict(start_epoch=time.time()))
 records=read(D/'records-private.json') if (D/'records-private.json').exists() else [];error=None;cpu=time.process_time()
 try:
  for job in p['jobs']:
   name=job['road']+'_'+str(job['anchor']);folder=D/name
   if folder.exists():
    assert (folder/'result.json').exists(),'Unfinished native rollout: no automatic replay'
    r=read(folder/'result.json')
    if not any(x['name']==name for x in records):records.append(r);save(D/'records-private.json',records)
    continue
   remain=5912-read(D/'budget.json')['actions']
   if remain<=0:break
   folder.mkdir(mode=0o700);reference=read(Path(job['materialization']));anchor=job['anchor'];case=p['cases'][job['road']];commands=np.asarray(reference['commands'],np.float32);channel=job['channel'];pulse=np.asarray(job['pulse_values'],np.float32);worker=env=None;rows=[];raw=0;actms=[];start=time.perf_counter();prefix_exact=0;goalpass=None;snapshot_exact=False;phasecount={'prefix':0,'pulse':0,'continuation':0}
   try:
    worker=prepare(p['base'],folder/'cpu',p['sandbox_path']);env=make_env();obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});start_t=env.unwrapped.t;reset_ticks=round(start_t*50);worker.call('reset',obs)
    for step in range(1,min(2000,remain)+1):
     assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();response,ms=worker.call('act',obs);base=np.asarray(response['action'],np.float32);assert ms<=5000;action=base.copy();phase='prefix' if step<anchor else 'pulse' if step<anchor+3 else 'continuation'
     if phase=='prefix':assert np.array_equal(base,commands[step-1]);prefix_exact+=1
     if step==anchor:snapshot_exact=capture(env)==reference['snapshots'][str(anchor)];assert snapshot_exact,'Snapshot boundary differs from249actualbaseline'
     if phase=='pulse':action[channel]=pulse[step-anchor]
     assert action[0]==base[0] and action[3-channel]==base[3-channel];assert response['scale_audit']['nominal_memory_preserved']
     b=read(D/'budget.json');assert b['actions']<5912;b['actions']+=1;b['phases'][phase]=b['phases'].get(phase,0)+1;save(D/'budget.json',b);phasecount[phase]+=1;old_t=env.unwrapped.t;obs,_,ended,truncated,info=env.step(action);ticks=round((env.unwrapped.t-old_t)*50);raw+=ticks;t=truth(env);visited={int(tile.idx) for tile in env.unwrapped.road if tile.road_visited};front=contiguous_visited_tiles(visited,len(env.unwrapped.track));complete=env.unwrapped.finish_time_s is not None;official_limit=step>=2000 and not complete;terminal=bool(ended or truncated or official_limit)
     if phase=='prefix':
      saved=reference['rows'][step-1];assert t['unique_tiles']==saved['unique_tiles'] and t['damage']==saved['damage'] and abs(t['speed_m_s']-saved['speed_m_s'])<1e-10
     if step>=anchor and goalpass is None and front>=job['target_frontier']:goalpass=step-anchor+1
     nominal=np.asarray(response['legal_feature_audit']['nominal_action'],float);legal_lower=float(np.clip(np.clip(nominal[channel]-.5,0,1)*p['scales'][channel-1],0,1));legal_upper=float(np.clip(np.clip(nominal[channel]+.5,0,1)*p['scales'][channel-1],0,1))
     rows.append(dict(action=step,phase=phase,base=base.tolist(),executed=action.tolist(),contiguous=front,visited=t['unique_tiles'],speed_m_s=t['speed_m_s'],damage=t['damage'],collision=bool(info['collision']),raw_ticks=ticks,terminal=terminal,pulse_current_nominal_reachable=legal_lower-1e-7<=float(action[channel])<=legal_upper+1e-7 if phase=='pulse' else None));actms.append(ms)
     if terminal or step==min(2000,remain):break
    r=dict(name=name,road=job['road'],anchor=anchor,selected=job['selected'],native_actions=len(rows),phase_actions=phasecount,completed=complete,actual_DNF=terminal and not complete,censored=not terminal,lap_ms=round((env.unwrapped.finish_time_s-start_t)*1000) if complete else None,baseline_lap_ms=reference['lap_ms'],lap_delta_ms=round((env.unwrapped.finish_time_s-start_t)*1000)-reference['lap_ms'] if complete else None,damage=t['damage'],visited=t['unique_tiles'],total_tiles=len(env.unwrapped.track),retire_reason=info.get('retire_reason') or ('max_steps' if official_limit else 'budget_cut' if not terminal else None),goal_first_passage_actions=goalpass,baseline_goal_first_passage_actions=job['baseline_first_passage_actions'],goal_delta_actions=goalpass-job['baseline_first_passage_actions'] if goalpass is not None else None,model_predicted_delta_actions=-1,prefix_actions_exact=prefix_exact,snapshot_boundary_exact=snapshot_exact,pulse_values_exact=True,pulse_current_nominal_unreachable_actions=sum(x['phase']=='pulse' and not x['pulse_current_nominal_reachable'] for x in rows),steering_changed_vs_frozen_baseline_first12=sum(float(x['executed'][0])!=float(commands[x['action']-1,0]) for x in rows if anchor<=x['action']<anchor+12 and x['action']<=len(commands)),collision_actions=[x['action'] for x in rows if x['collision']],raw_step_ticks=raw,raw_reset_ticks=reset_ticks,base_actor_CPU_s=response['actor_cumulative_CPU_s'],max_policy_IPC_ms=max(actms),wall_s=time.perf_counter()-start)
   finally:
    if worker:reaping=worker.close()
    if env:env.close()
   r['reaping']=reaping;save(folder/'trace-private.json',rows);save(folder/'result.json',r);records.append(r);save(D/'records-private.json',records);print(json.dumps({k:r[k] for k in ['name','completed','actual_DNF','censored','lap_ms','lap_delta_ms','goal_delta_actions','native_actions']}),flush=True)
 except Exception as e:error=type(e).__name__+': '+str(e)
 save(D/'outcome-private.json',dict(stage=250,records=records,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(D/'opening.json')['start_epoch'],CPU_s=time.process_time()-cpu,unexecuted=[j['road']+'_'+str(j['anchor']) for j in p['jobs'] if not any(r['name']==j['road']+'_'+str(j['anchor']) for r in records)]))

if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
