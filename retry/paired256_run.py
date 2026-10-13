"""Four independent3-action source-ratio paired pulses using currentlegal240 inputs."""
import argparse,json,time,datetime,hashlib
from pathlib import Path
import numpy as np


def paired(action,speed):
    K=.06*(max(0.,float(speed))/.54+5);d=min(float(action[2]),float(action[1])/K);out=np.asarray(action,np.float32).copy();out[1:]=np.clip([float(action[1])-K*d,float(action[2])-d],0,1).astype(np.float32)
    return out,K,d


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
            name=job['road']+'_'+str(job['action']);folder=D/name
            if folder.exists():
                assert (folder/'result.json').exists(),'Unfinishednativepulse: neverreplay'
                r=read(folder/'result.json')
                if not any(x['name']==name for x in records):records.append(r);save(D/'records-private.json',records)
                continue
            remain=5045-read(D/'budget.json')['actions']
            if remain<=0:break
            folder.mkdir(mode=0o700);m=read(Path(job['materialization']));z=np.load(Path(job['materialization']).parent/'cache-private.npz');commands=z['commands'];a=job['action'];worker=env=None;rows=[];raw=0;lat=[];phasecount={'prefix':0,'pulse':0,'continuation':0};pulseend=None;start=time.perf_counter();boundary_exact=False
            try:
                worker=prepare(p['base'],folder/'cpu',p['sandbox_path']);env=make_env();case=p['cases'][job['road']];obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});start_t=env.unwrapped.t;reset_ticks=round(start_t*50);worker.call('reset',obs)
                for step in range(1,min(2000,remain)+1):
                    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();response,ms=worker.call('act',obs);base=np.asarray(response['action'],np.float32);features=np.asarray(response['legal_feature_audit']['features'],float);assert ms<=5000 and response['scale_audit']['nominal_memory_preserved'];phase='prefix' if step<a else 'pulse' if step<a+3 else 'continuation';action=base.copy();K=d=None;speed_proxy=float(features[4])
                    if phase=='prefix':assert np.array_equal(base,commands[step-1])
                    if step==a:boundary_exact=capture(env)==m['snapshots'][str(a)];assert boundary_exact,'Baseline actualboundary mismatch'
                    if phase=='pulse':action,K,d=paired(base,speed_proxy)
                    assert action[0]==base[0] and np.all(action[1:]<=base[1:]+1e-7);b=read(D/'budget.json');assert b['actions']<5045;b['actions']+=1;b['phases'][phase]=b['phases'].get(phase,0)+1;save(D/'budget.json',b);phasecount[phase]+=1;old_t=env.unwrapped.t;obs,_,ended,truncated,info=env.step(action);raw+=round((env.unwrapped.t-old_t)*50);t=truth(env);front=contiguous_visited_tiles({int(tile.idx) for tile in env.unwrapped.road if tile.road_visited},len(env.unwrapped.track));complete=env.unwrapped.finish_time_s is not None;official_limit=step>=2000 and not complete;terminal=bool(ended or truncated or official_limit)
                    if phase=='prefix':expected=m['actual'][step-1];assert t['unique_tiles']==expected['unique_tiles'] and t['damage']==expected['damage'] and abs(t['speed_m_s']-expected['speed_m_s'])<1e-10
                    if step==a+2:pulseend=dict(speed_m_s=t['speed_m_s'],visited=t['unique_tiles'],contiguous=front,damage=t['damage'])
                    rows.append(dict(action=step,phase=phase,base=base.tolist(),executed=action.tolist(),legal_speed_proxy=speed_proxy,K=K,d=d,speed_m_s=t['speed_m_s'],visited=t['unique_tiles'],contiguous=front,damage=t['damage'],collision=bool(info['collision']),terminal=terminal));lat.append(ms)
                    if terminal or step==min(2000,remain):break
                r=dict(name=name,road=job['road'],action=a,group=job['group'],native_actions=len(rows),phase_actions=phasecount,completed=complete,actual_DNF=terminal and not complete,censored=not terminal,lap_ms=round((env.unwrapped.finish_time_s-start_t)*1000) if complete else None,baseline_lap_ms=job['baseline_lap_ms'],lap_delta_ms=round((env.unwrapped.finish_time_s-start_t)*1000)-job['baseline_lap_ms'] if complete else None,retire_reason=info.get('retire_reason') or ('max_steps' if official_limit else 'budget_cut' if not terminal else None),damage=t['damage'],pulse_end=pulseend,baseline_pulse_end=job['baseline_pulse_end'],boundary_exact=boundary_exact,prefix_actions_exact=phasecount['prefix'],pulse_speed_delta_m_s=pulseend['speed_m_s']-job['baseline_pulse_end']['speed_m_s'] if pulseend else None,pulse_visited_delta=pulseend['visited']-job['baseline_pulse_end']['visited'] if pulseend else None,pulse_contiguous_delta=pulseend['contiguous']-job['baseline_pulse_end']['contiguous'] if pulseend else None,raw_step_ticks=raw,raw_reset_ticks=reset_ticks,base_actor_CPU_s=response['actor_cumulative_CPU_s'],max_policy_IPC_ms=max(lat),wall_s=time.perf_counter()-start,collision_actions=[x['action'] for x in rows if x['collision']],pulse_legal_speed_proxies=[x['legal_speed_proxy'] for x in rows if x['phase']=='pulse'],pulse_K_values=[x['K'] for x in rows if x['phase']=='pulse'])
            finally:
                if worker:reaping=worker.close()
                if env:env.close()
            r['reaping']=reaping;save(folder/'trace-private.json',rows);save(folder/'result.json',r);records.append(r);save(D/'records-private.json',records);print(json.dumps({k:r[k] for k in ['name','completed','actual_DNF','censored','lap_ms','lap_delta_ms','pulse_speed_delta_m_s','pulse_contiguous_delta','native_actions']}),flush=True)
    except Exception as e:error=type(e).__name__+': '+str(e)
    save(D/'outcome-private.json',dict(stage=256,records=records,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(D/'opening.json')['start_epoch'],CPU_s=time.process_time()-cpu,unexecuted=[j['road']+'_'+str(j['action']) for j in p['jobs'] if not any(r['name']==j['road']+'_'+str(j['action']) for r in records)]))

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
