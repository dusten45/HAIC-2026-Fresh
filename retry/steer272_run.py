"""Two one-shot258 steering-target substitutions;271 path and240 longitudinal preserved."""
import argparse, datetime, hashlib, json, time
from pathlib import Path
import numpy as np
from retry.path271_geometry import local_path
from retry.steer272_target import target, pack

def read(q): return json.loads(Path(q).read_text())
def sha(q): return hashlib.sha256(Path(q).read_bytes()).hexdigest()
def save(q, x):
    q=Path(q); tmp=q.with_name(q.name+'.tmp')
    tmp.write_text(json.dumps(x, indent=2, allow_nan=False)+'\n'); tmp.chmod(0o600); tmp.replace(q)

def run(path):
    from retry.frozen_composite_runtime import prepare
    from retry.diagnose import make_env
    p=read(path); D=path.parent
    assert sha(path)==path.with_suffix('.sha256').read_text().strip()
    for q,h in p['hashes'].items(): assert sha(q)==h
    assert read(D/'preflight.json')['passed']
    assert not (D/'opening.json').exists(), 'Started episode cannot be replayed'
    save(D/'opening.json',dict(epoch=time.time())); results=[]; error=None; cpu=time.process_time()
    try:
        for road in p['order']:
            folder=D/road; assert not folder.exists(); folder.mkdir(mode=0o700)
            frozen=read(p['frozen_paths'][road]); line=np.asarray(frozen['line']); ds=np.asarray(frozen['free_profile']['ds']); index=0
            env=worker=None; rows=[]; rawticks=0; timings=[]; ipc=[]; geometry=[]; started=time.perf_counter()
            try:
                worker=prepare(p['candidate'],folder/'cpu',p['sandbox_path'])
                save(folder/'ready-private.json',worker.ready)
                env=make_env(); case=p['cases'][road]
                obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']})
                assert hashlib.sha256(obs.tobytes()).hexdigest()==p['initial_observations'][road]
                assert hashlib.sha256(np.asarray(env.unwrapped.track,dtype='<f8').tobytes()).hexdigest()==case['road_geometry_sha256']
                raw=env.unwrapped; start_t=raw.t; resetticks=round(start_t*50)
                worker.call('reset',pack(obs)); remaining=p['max_actions']-read(D/'budget.json')['actions']
                cap=min(p['per_case_cap'],remaining); assert cap>0
                for step in range(1,cap+1):
                    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp()
                    tic=time.perf_counter(); path_input,index,detail=local_path(line,np.asarray(raw.car.hull.position),float(raw.car.hull.angle),index)
                    steering,steering_detail=target(line,ds,np.asarray(raw.car.hull.position),float(raw.car.hull.angle),float(np.linalg.norm(raw.car.hull.linearVelocity)),index,detail['projection_fraction'])
                    geometry.append((time.perf_counter()-tic)*1000)
                    response,ms=worker.call('act',pack(obs,2,path_input,steering)); ipc.append(ms)
                    assert not response['python_audit_denied_events']; assert response['path_calls']==1 and response['input_mode']==2
                    action=np.asarray(response['action'],np.float32); timings.append(response['act_compute_ms'])
                    b=read(D/'budget.json'); assert b['actions']<p['max_actions']; b['actions']+=1; save(D/'budget.json',b)
                    before=raw.t; obs,_,ended,truncated,info=env.step(action); rawticks+=round((raw.t-before)*50)
                    complete=raw.finish_time_s is not None; terminal=bool(ended or truncated or step>=2000)
                    rows.append(dict(step=step,**detail,**steering_detail,steering_audit=response['steering_audit'],position=list(raw.car.hull.position),angle=float(raw.car.hull.angle),
                        action=action.tolist(),features=response['features'],path=path_input,damage=env.damage.damage,
                        collision=bool(info['collision']),visited=raw.tile_visited_count,terminal=terminal))
                    if terminal or step==cap: break
                errors=[x['path_error_m'] for x in rows]
                r=dict(road=road,completed=complete,actual_DNF=terminal and not complete,censored=not terminal,
                    lap_ms=round((raw.finish_time_s-start_t)*1000) if complete else None,native_actions=step,
                    retire_reason=None if complete else (info.get('retire_reason') or ('budget_cut' if not terminal else 'max_steps')),damage=env.damage.damage,
                    visited=raw.tile_visited_count,total_tiles=len(raw.track),first_collision=next((x['step'] for x in rows if x['collision']),None),
                    first_error_over3m=next((x['step'] for x in rows if x['path_error_m']>3),None),
                    tracking_error_m=dict(mean=float(np.mean(errors)),p95=float(np.percentile(errors,95)),max=float(max(errors))),
                    empty_path_actions=sum(not x['path'] for x in rows),steering_active_actions=sum(x['steering_audit']['active'] for x in rows),raw_step_ticks=rawticks,raw_reset_ticks=resetticks,
                    wall_s=time.perf_counter()-started,actor_CPU_s=response['actor_cumulative_CPU_s'],
                    full_agent_compute_ms=dict(median=float(np.median(timings)),max=float(max(timings))),
                    geometry_compute_ms=dict(median=float(np.median(geometry)),max=float(max(geometry)),sum=float(sum(geometry))),
                    IPC_ms=dict(median=float(np.median(ipc)),max=float(max(ipc))),
                    privileged_GT=True,whole_map_foresight=True,legal_pixel_candidate=False)
            finally:
                if worker: reaping=worker.close()
                if env: env.close()
            r['reaping']=reaping; save(folder/'trajectory-private.json',rows); save(folder/'result.json',r)
            results.append(r); save(D/'results-private.json',results); print(json.dumps(r),flush=True)
    except Exception as e: error=type(e).__name__+': '+str(e)
    save(D/'outcome-private.json',dict(stage=272,results=results,technical_error=error,budget=read(D/'budget.json'),
        wall_s=time.time()-read(D/'opening.json')['epoch'],CPU_s=time.process_time()-cpu))

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__); a.add_argument('--plan',type=Path,required=True); run(a.parse_args().plan.resolve())
