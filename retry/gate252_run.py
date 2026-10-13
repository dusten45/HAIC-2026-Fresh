"""Evaluate one frozen 3/12 gated correction on exactly six DEV plus two reused screens.

No decoder/teacher data collection, learning, policy selection or failure pruning.
Only official endpoints, legal features and cost are retained.
"""
import argparse,json,time,datetime,hashlib
from pathlib import Path
import numpy as np


def run(path):
    from retry.frozen_composite_runtime import prepare
    from retry.diagnose import make_env
    p=json.loads(path.read_text());D=path.parent
    def sha(q):return hashlib.sha256(Path(q).read_bytes()).hexdigest()
    def read(q):return json.loads(q.read_text())
    def save(q,x):
        tmp=q.with_name(q.name+'.tmp');tmp.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');tmp.chmod(0o600);tmp.replace(q)
    assert sha(path)==path.with_suffix('.sha256').read_text().strip()
    for q,h in p['hashes'].items():assert sha(q)==h
    if not (D/'opening.json').exists():save(D/'opening.json',dict(start_epoch=time.time()))
    records=read(D/'records.json') if (D/'records.json').exists() else [];error=None;cpu=time.process_time()
    try:
        for label in p['order']:
            folder=D/'runs'/label
            if folder.exists():
                assert (folder/'result.json').exists(),'Unfinished native run: no automatic replay'
                r=read(folder/'result.json')
                if not any(x['label']==label for x in records):records.append(r);save(D/'records.json',records)
                continue
            remain=4000-read(D/'budget.json')['actions']
            if remain<=0:break
            folder.mkdir(parents=True,mode=0o700);worker=env=None;feature=[];hud=[];actions=[];timings=[];compute=[];ticks=0;start=time.perf_counter();case=p['cases'][label];gate_count=0;first_contact=None;first_zero_wheels=None;gate_flags=[]
            try:
                worker=prepare(p['candidate'],folder/'cpu',p['sandbox_path']);env=make_env();ob,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});start_t=env.unwrapped.t;reset_ticks=round(start_t*50);initial=hashlib.sha256(ob.tobytes()).hexdigest();geometry=hashlib.sha256(np.asarray(env.unwrapped.track,dtype='<f8').tobytes()).hexdigest();assert geometry==case['road_geometry_sha256'];worker.call('reset',ob)
                for step in range(1,min(2000,remain)+1):
                    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp()
                    response,ms=worker.call('act',ob);action=np.asarray(response['action'],np.float32);assert ms<=5000;assert response['scale_audit']['nominal_memory_preserved'] and response['scale_audit']['steering_unchanged'];assert response['scale_audit']['scales']==p['global_scales']
                    flag=response['gate252_enabled'];assert flag==(step>=13 and (step-13)%12<3) and response['gate252_count']==step;gate_count+=int(flag);gate_flags.append(flag);feature.append(response['legal_feature_audit']['features']);actions.append(action);timings.append(ms);compute.append(response['act_compute_ms']);b=read(D/'budget.json');assert b['actions']<4000;b['actions']+=1;b['phases']['evaluation']=b['phases'].get('evaluation',0)+1;save(D/'budget.json',b)
                    old_t=env.unwrapped.t;ob,_,ended,truncated,info=env.step(action);ticks+=round((env.unwrapped.t-old_t)*50);complete=env.unwrapped.finish_time_s is not None;official_limit=step>=2000 and not complete;terminal=bool(ended or truncated or official_limit)
                    if first_contact is None and info['collision']:first_contact=step
                    if first_zero_wheels is None and sum(bool(w.tiles) for w in env.unwrapped.car.wheels)==0:first_zero_wheels=step
                    if terminal or step==min(2000,remain):break
                r=dict(label=label,gate_on_actions=gate_count,first_collision_action=first_contact,first_zero_road_wheels_action=first_zero_wheels,native_actions=step,completed=complete,actual_DNF=terminal and not complete,censored=not terminal,lap_ms=round((env.unwrapped.finish_time_s-start_t)*1000) if complete else None,damage=env.damage.damage,visited=env.unwrapped.tile_visited_count,total_tiles=len(env.unwrapped.track),retire_reason=info.get('retire_reason') or ('max_steps' if official_limit else 'budget_cut' if not terminal else None),raw_step_ticks=ticks,raw_reset_ticks=reset_ticks,initial_observation_sha256=initial,geometry_sha256=geometry,base_actor_CPU_s=response['actor_cumulative_CPU_s'],full_Agent_compute_ms=dict(median=float(np.median(compute)),p95=float(np.percentile(compute,95)),max=float(max(compute))),policy_IPC_ms=dict(median=float(np.median(timings)),p95=float(np.percentile(timings,95)),max=float(max(timings))),wall_s=time.perf_counter()-start,archive_sha256=p['candidate']['archive_sha256'])
            finally:
                if worker:reaping=worker.close()
                if env:env.close()
            r['reaping']=reaping;cache=folder/'legal-cache-private.npz';np.savez_compressed(cache,features16=np.asarray(feature),actions=np.asarray(actions),gate_enabled=np.asarray(gate_flags),compute_ms=np.asarray(compute),IPC_ms=np.asarray(timings));cache.chmod(0o600);save(folder/'result.json',r);records.append(r);save(D/'records.json',records);print(json.dumps({k:r[k] for k in ['label','completed','actual_DNF','censored','lap_ms','damage','native_actions']}),flush=True)
    except Exception as e:error=type(e).__name__+': '+str(e)
    save(D/'outcome.json',dict(stage=252,records=records,unexecuted=[k for k in p['order'] if not any(r['label']==k for r in records)],technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(D/'opening.json')['start_epoch'],CPU_this_process_s=time.process_time()-cpu,champion_changed=False,HOLDOUT_opened=False,SEALED_opened=False,automatic_next_experiment=False))

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
