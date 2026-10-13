"""Four finalmodel TRAIN diagnostic runs, no policy selection or new screen."""
import argparse,time,datetime,hashlib
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha

def run(path):
    from retry.frozen_composite_runtime import prepare
    from retry.diagnose import make_env
    D=path.parent;p=read(path);assert sha(path)==path.with_suffix('.sha256').read_text().strip()
    for q,h in p['hashes'].items():assert sha(Path(q))==h
    assert not (D/'evaluation-opening.json').exists(),'No replay of finalmodels'
    save(D/'evaluation-opening.json',dict(epoch=time.time()));results=[];error=None;cpu=time.process_time()
    try:
        for item in p['order']:
            deadline=datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();assert time.time()<deadline
            arm,road=item['arm'],item['road'];b=read(D/'budget.json');remaining=min(18984-b['actions'],2600-b['evaluation'])
            if remaining<=0:results.append(dict(arm=arm,road=road,unexecuted=True,native_actions=0,completed=False,actual_DNF=False,censored=False,lap_ms=None));continue
            folder=D/'evaluation'/(arm+'_'+road);folder.mkdir(parents=True,mode=0o700);worker=env=None;rows=[];compute=[];ipc=[];ticks=0;start=time.perf_counter()
            try:
                worker=prepare(p['candidates'][arm],folder/'cpu',p['sandbox_path']);env=make_env();case=p['cases'][road];obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});raw=env.unwrapped;start_t=raw.t;reset=round(start_t*50)
                assert hashlib.sha256(obs.tobytes()).hexdigest()==p['initial_observations'][road];worker.call('reset',obs)
                cap=min(650,remaining)
                for step in range(1,cap+1):
                    assert time.time()<deadline;response,ms=worker.call('act',obs);assert not response['python_audit_denied_events'];action=np.array(response['action'],np.float32);assert np.float32(response['nominal_state']['previous_steer'])==action[0]
                    compute.append(response['act_compute_ms']);ipc.append(ms);b=read(D/'budget.json');assert b['actions']<18984 and b['evaluation']<2600;b['actions']+=1;b['evaluation']+=1;save(D/'budget.json',b)
                    before=raw.t;obs,_,ended,truncated,info=env.step(action);ticks+=round((raw.t-before)*50);complete=raw.finish_time_s is not None;terminal=bool(ended or truncated)
                    rows.append(dict(step=step,action=action.tolist(),features=response['features'],memory=response['nominal_state'],damage=env.damage.damage,collision=bool(info['collision']),compute_ms=response['act_compute_ms'],IPC_ms=ms))
                    if terminal or step==cap:break
                r=dict(arm=arm,road=road,native_actions=step,completed=complete,actual_DNF=terminal and not complete,censored=not terminal,unexecuted=False,lap_ms=round((raw.finish_time_s-start_t)*1000) if complete else None,
                    retire_reason=None if complete else info.get('retire_reason') or 'budget_cut',damage=env.damage.damage,visited=raw.tile_visited_count,total_tiles=len(raw.track),raw_step_ticks=ticks,raw_reset_ticks=reset,wall_s=time.perf_counter()-start,
                    actor_CPU_s=response['actor_cumulative_CPU_s'],Agent_ms=dict(median=float(np.median(compute)),p95=float(np.percentile(compute,95)),max=float(max(compute))),IPC_ms=dict(median=float(np.median(ipc)),max=float(max(ipc))),pixel_only=True,GT_runtime_inputs=False)
            finally:
                if worker:reaping=worker.close()
                if env:env.close()
            r['reaping']=reaping;save(folder/'result.json',r);save(folder/'trajectory-private.json',rows);results.append(r);save(D/'evaluation-results-private.json',results);print(str(r),flush=True)
    except Exception as e:error=type(e).__name__+': '+str(e)
    save(D/'evaluation-outcome-private.json',dict(results=results,technical_error=error,wall_s=time.time()-read(D/'evaluation-opening.json')['epoch'],CPU_s=time.process_time()-cpu,budget=read(D/'budget.json')))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
