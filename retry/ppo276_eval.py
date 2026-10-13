"""Final276checkpoint only: six TRAIN and two freshDEVpaired240 screens."""
import argparse,time,datetime,hashlib
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha

def evaluate(path):
    from retry.frozen_composite_runtime import prepare
    from retry.diagnose import make_env
    D=path.parent;p=read(path);training=read(D/'training-plan.json')
    assert sha(path)==path.with_suffix('.sha256').read_text().strip()
    for q,h in p['hashes'].items():assert sha(Path(q))==h
    assert read(D/'state.json')['last_committed_batch']==64 and read(D/'state.json')['valid_training_total']==65536
    assert not (D/'evaluation-opening.json').exists(),'No replay or reselection of finalscreen runs'
    assert sha(Path(training['screen_registration']))==training['screen_registration_sha256']
    save(D/'evaluation-opening.json',dict(epoch=time.time(),checkpoint_sha256=p['final_checkpoint_sha256']))
    seal=read(D/'screen-seal.json');seal['opened_for_policy_evaluation']=True;save(D/'screen-seal.json',seal)
    save(D/'screen-opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),final_checkpoint=64,registration_sha256=training['screen_registration_sha256'],opened_after_training=True,training_or_selection_use=False))
    results=[];initials={};error=None;cpu=time.process_time()
    try:
        for item in p['order']:
            assert time.time()<datetime.datetime.fromisoformat(training['deadline_utc']).timestamp()
            road,arm=item['road'],item['arm'];b=read(D/'budget.json');remaining=min(training['native_cap']-b['actions'],training['final_eval_cap']-b['evaluation'])
            if remaining<=0:
                results.append(dict(road=road,arm=arm,unexecuted=True,completed=False,actual_DNF=False,censored=False,native_actions=0,lap_ms=None,reason='global_or_eval_cap'));continue
            folder=D/'evaluation'/(road+'_'+arm);folder.mkdir(parents=True,mode=0o700);worker=env=None;rows=[];compute=[];ipc=[];ticks=0;start=time.perf_counter()
            try:
                worker=prepare(p[arm],folder/'cpu',p['sandbox_path']);save(folder/'ready-private.json',worker.ready)
                env=make_env();case=p['cases'][road];obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});raw=env.unwrapped;start_t=raw.t;reset=round(start_t*50)
                assert hashlib.sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest()==case['road_geometry_sha256'];obs_sha=hashlib.sha256(obs.tobytes()).hexdigest()
                if road in p['initial_observations']:assert obs_sha==p['initial_observations'][road]
                if road in initials:assert obs_sha==initials[road]
                else:initials[road]=obs_sha
                worker.call('reset',obs);cap=min(650,remaining)
                for step in range(1,cap+1):
                    assert time.time()<datetime.datetime.fromisoformat(training['deadline_utc']).timestamp()
                    response,ms=worker.call('act',obs);assert not response['python_audit_denied_events'];action=np.array(response['action'],np.float32)
                    if arm=='candidate':assert np.float32(response['nominal_state']['previous_steer'])==action[0]
                    compute.append(response['act_compute_ms']);ipc.append(ms)
                    b=read(D/'budget.json');assert b['actions']<training['native_cap'] and b['evaluation']<training['final_eval_cap'];b['actions']+=1;b['evaluation']+=1;save(D/'budget.json',b)
                    before=raw.t;obs,_,ended,truncated,info=env.step(action);ticks+=round((raw.t-before)*50)
                    complete=raw.finish_time_s is not None;terminal=bool(ended or truncated)
                    rows.append(dict(step=step,action=action.tolist(),features=response['features'],nominal_state=response['nominal_state'],collision=bool(info['collision']),damage=env.damage.damage,visited=raw.tile_visited_count,compute_ms=response['act_compute_ms'],IPC_ms=ms))
                    if terminal or step==cap:break
                r=dict(road=road,arm=arm,cohort=p['cohorts'][road],native_actions=step,completed=complete,actual_DNF=terminal and not complete,censored=not terminal,unexecuted=False,
                    lap_ms=round((raw.finish_time_s-start_t)*1000) if complete else None,retire_reason=None if complete else info.get('retire_reason') or 'budget_cut',damage=env.damage.damage,
                    visited=raw.tile_visited_count,total_tiles=len(raw.track),first_collision=next((x['step'] for x in rows if x['collision']),None),raw_step_ticks=ticks,raw_reset_ticks=reset,wall_s=time.perf_counter()-start,
                    actor_CPU_s=response['actor_cumulative_CPU_s'],Agent_ms=dict(median=float(np.median(compute)),p95=float(np.percentile(compute,95)),max=float(max(compute))),
                    IPC_ms=dict(median=float(np.median(ipc)),p95=float(np.percentile(ipc,95)),max=float(max(ipc))),archive_sha256=p[arm]['archive_sha256'],pixel_only=True,GT_runtime_inputs=False)
            finally:
                if worker:reaping=worker.close()
                if env:env.close()
            r['reaping']=reaping;save(folder/'result.json',r);save(folder/'trajectory-private.json',rows);results.append(r);save(D/'evaluation-results-private.json',results)
            print(str({k:r[k] for k in ['road','arm','completed','actual_DNF','censored','lap_ms','native_actions']}),flush=True)
    except Exception as e:error=type(e).__name__+': '+str(e)
    save(D/'evaluation-outcome-private.json',dict(results=results,technical_error=error,wall_s=time.time()-read(D/'evaluation-opening.json')['epoch'],CPU_s=time.process_time()-cpu,budget=read(D/'budget.json')))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--plan',type=Path,required=True);evaluate(a.parse_args().plan.resolve())
