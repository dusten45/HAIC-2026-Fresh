"""Legal pixel joint-action probe: matched executed/nominal steering memory."""
import argparse,datetime,time,hashlib
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha

def run(path):
    from retry.frozen_composite_runtime import prepare
    from retry.diagnose import make_env
    D=path.parent;p=read(path)
    assert sha(path)==path.with_suffix('.sha256').read_text().strip()
    for q,h in p['hashes'].items():assert sha(Path(q))==h
    assert read(D/'preflight.json')['passed'];assert not (D/'opening.json').exists(),'No replay of started native trials'
    save(D/'opening.json',dict(epoch=time.time()));records=[];error=None;cpu=time.process_time()
    try:
        for case in p['order']:
            road,policy=case['road'],case['policy'];folder=D/(road+'_'+policy);folder.mkdir(mode=0o700)
            env=worker=None;rows=[];compute=[];ipc=[];ticks=0;start=time.perf_counter()
            try:
                worker=prepare(p['configs'][policy],folder/'cpu',p['sandbox_path']);save(folder/'ready-private.json',worker.ready)
                env=make_env();c=p['cases'][road];obs,_=env.reset(seed=c['seed'],options={'track_id':c['track_id']});raw=env.unwrapped;start_t=raw.t;reset=round(start_t*50)
                assert hashlib.sha256(obs.tobytes()).hexdigest()==p['initial_observations'][road]
                assert hashlib.sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest()==c['road_geometry_sha256'];worker.call('reset',obs)
                cap=min(p['per_case_cap'],p['max_actions']-read(D/'budget.json')['actions']);assert cap>0
                for step in range(1,cap+1):
                    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp()
                    response,ms=worker.call('act',obs);assert not response['python_audit_denied_events'];action=np.array(response['action'],np.float32)
                    audit=response['joint_audit'];memory=response['nominal_state']['previous_steer'];expected=float(action[0]) if audit['mode']['feedback']=='executed' else audit['nominal_memory'];assert memory==expected
                    b=read(D/'budget.json');assert b['actions']<p['max_actions'];b['actions']+=1;save(D/'budget.json',b)
                    compute.append(response['act_compute_ms']);ipc.append(ms);before=raw.t;obs,_,ended,truncated,info=env.step(action);ticks+=round((raw.t-before)*50)
                    complete=raw.finish_time_s is not None;terminal=bool(ended or truncated or step>=2000)
                    rows.append(dict(step=step,action=action.tolist(),features=response['features'],joint_audit=audit,nominal_state=response['nominal_state'],damage=env.damage.damage,collision=bool(info['collision']),visited=raw.tile_visited_count,terminal=terminal))
                    if terminal or step==cap:break
                progress=raw.tile_visited_count/len(raw.track);lap=round((raw.finish_time_s-start_t)*1000) if complete else None
                r=dict(road=road,policy=policy,native_actions=step,completed=complete,actual_DNF=terminal and not complete,censored=not terminal,lap_ms=lap,
                    return_value=2-(raw.finish_time_s-start_t)/160 if complete else progress-1 if terminal else None,
                    retire_reason=None if complete else info.get('retire_reason') or ('budget_cut' if not terminal else 'max_steps'),damage=env.damage.damage,
                    first_collision=next((r['step'] for r in rows if r['collision']),None),visited=raw.tile_visited_count,total_tiles=len(raw.track),
                    raw_step_ticks=ticks,raw_reset_ticks=reset,wall_s=time.perf_counter()-start,actor_CPU_s=response['actor_cumulative_CPU_s'],
                    Agent_ms=dict(median=float(np.median(compute)),p95=float(np.percentile(compute,95)),max=float(max(compute))),
                    IPC_ms=dict(median=float(np.median(ipc)),max=float(max(ipc))),pixel_only=True,GT_runtime_inputs=False)
            finally:
                if worker:reaping=worker.close()
                if env:env.close()
            r['reaping']=reaping;save(folder/'trajectory-private.json',rows);save(folder/'result.json',r);records.append(r);save(D/'results-private.json',records);print(str({k:r[k] for k in ['road','policy','completed','actual_DNF','censored','lap_ms','native_actions']}),flush=True)
    except Exception as e:error=type(e).__name__+': '+str(e)
    save(D/'outcome-private.json',dict(stage=273,results=records,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(D/'opening.json')['epoch'],CPU_s=time.process_time()-cpu))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
