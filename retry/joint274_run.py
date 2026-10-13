"""Six DEV transfers of one frozen273 pixel policy; no reselection or fit."""
import argparse,datetime,hashlib,time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha

def run(path):
    from retry.frozen_composite_runtime import prepare
    from retry.diagnose import make_env
    D=path.parent;p=read(path)
    assert sha(path)==path.with_suffix('.sha256').read_text().strip()
    for q,h in p['hashes'].items():assert sha(Path(q))==h
    assert not (D/'opening.json').exists(),'No replay of started native evaluations'
    save(D/'opening.json',dict(epoch=time.time()));results=[];error=None;cpu=time.process_time()
    try:
        for road in p['order']:
            remaining=p['native_cap']-read(D/'budget.json')['actions']
            if remaining<=0:
                results.append(dict(road=road,completed=False,actual_DNF=False,censored=False,unexecuted=True,native_actions=0,reason='global_budget',lap_ms=None));continue
            folder=D/road;folder.mkdir(mode=0o700);worker=env=None;rows=[];compute=[];ipc=[];ticks=0;started=time.perf_counter()
            try:
                worker=prepare(p['candidate'],folder/'cpu',p['sandbox_path']);save(folder/'ready-private.json',worker.ready)
                env=make_env();c=p['cases'][road];obs,_=env.reset(seed=c['seed'],options={'track_id':c['track_id']});raw=env.unwrapped;start_t=raw.t;reset=round(start_t*50)
                assert hashlib.sha256(obs.tobytes()).hexdigest()==p['initial_observations'][road]
                assert hashlib.sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest()==c['road_geometry_sha256'];worker.call('reset',obs)
                cap=min(2000,remaining)
                for step in range(1,cap+1):
                    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp()
                    response,ms=worker.call('act',obs);assert not response['python_audit_denied_events'];action=np.array(response['action'],np.float32)
                    assert response['nominal_state']['previous_steer']==float(action[0])
                    if rows:assert response['features'][7]==rows[-1]['nominal_state']['previous_steer']
                    compute.append(response['act_compute_ms']);ipc.append(ms)
                    b=read(D/'budget.json');assert b['actions']<p['native_cap'];b['actions']+=1;save(D/'budget.json',b)
                    before=raw.t;obs,_,ended,truncated,info=env.step(action);ticks+=round((raw.t-before)*50)
                    complete=raw.finish_time_s is not None;terminal=bool(ended or truncated or step>=2000)
                    rows.append(dict(step=step,action=action.tolist(),features=response['features'],nominal_state=response['nominal_state'],damage=env.damage.damage,collision=bool(info['collision']),visited=raw.tile_visited_count,terminal=terminal,compute_ms=response['act_compute_ms'],IPC_ms=ms))
                    if terminal or step==cap:break
                r=dict(road=road,completed=complete,actual_DNF=terminal and not complete,censored=not terminal,unexecuted=False,native_actions=step,
                    lap_ms=round((raw.finish_time_s-start_t)*1000) if complete else None,damage=env.damage.damage,
                    retire_reason=None if complete else info.get('retire_reason') or ('max_steps' if step>=2000 else 'budget_cut'),visited=raw.tile_visited_count,total_tiles=len(raw.track),
                    first_collision=next((x['step'] for x in rows if x['collision']),None),raw_step_ticks=ticks,raw_reset_ticks=reset,wall_s=time.perf_counter()-started,
                    actor_CPU_s=response['actor_cumulative_CPU_s'],Agent_ms=dict(median=float(np.median(compute)),p95=float(np.percentile(compute,95)),max=float(max(compute))),
                    IPC_ms=dict(median=float(np.median(ipc)),p95=float(np.percentile(ipc,95)),max=float(max(ipc))),pixel_only=True,GT_runtime_inputs=False,archive_sha256=p['candidate']['archive_sha256'])
            finally:
                if worker:reaping=worker.close()
                if env:env.close()
            r['reaping']=reaping;save(folder/'trajectory-private.json',rows);save(folder/'result.json',r);results.append(r);save(D/'results-private.json',results)
            print(str({k:r[k] for k in ['road','completed','actual_DNF','censored','lap_ms','native_actions','damage']}),flush=True)
    except Exception as e:error=type(e).__name__+': '+str(e)
    save(D/'outcome-private.json',dict(stage=274,results=results,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(D/'opening.json')['epoch'],CPU_s=time.process_time()-cpu))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
