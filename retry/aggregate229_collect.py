"""Known DEV affine-pedal collection/replay with independent privileged labels.

Pixel workers receive only observations. Nominal32 sees every real observation
and acknowledges the actual executed control after each step. GT targets never
drive the environment. F1/F2 repeat saved controls, not learned decisions.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import resource
import numpy as np


def dump(path,x):
    with path.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
    path.chmod(0o600)


def collect(path):
    from retry.diagnose import make_env,Budget
    from retry.frozen_composite_runtime import prepare,validate_response
    from retry.frozen_paired_evaluation import sha,verify_files,native_window
    from retry.evaluate import observation_contract
    from retry.full_route_reproduction import truth
    from retry.source_vehicle_transition import capture
    from retry.aggregate229_teacher import query
    p=json.loads(path.read_text());assert sha(path)==path.with_suffix('.sha256').read_text().strip()
    verify_files(p['source_sha256']);verify_files(p['runtime_sha256']);native_window(p)
    root=path.parent;dump(root/'opening.json',dict(stage=229,native_cap=2400,one_use=True));records=[];start=time.perf_counter();error=None
    for job in p['jobs']:
        remaining=2400-json.loads((root/'budget.json').read_text())['actions']
        if remaining<=0:break
        label=job['road'];folder=root/label;folder.mkdir(mode=0o700)
        legal=teacher=env=None;used=0;queries=[];data=[];observations=[];endpoints=[];legal_ms=[];teacher_ms=[];feedback_ms=[];capturewall=0.;previous=None;actual_previous_steer=0.;acthash=hashlib.sha256();obshash=hashlib.sha256();qualified=True;r={};oldrows=None;oldfeatures=None;initial=None;legalcpu=teachercpu=0.
        wall,cpu=time.perf_counter(),time.process_time()
        try:
            legal=prepare(job['policy'],folder/'legal',p['sandbox_path']);teacher=prepare(p['teacher'],folder/'teacher',p['sandbox_path'])
            env=make_env();case=job['case'];native_window(p);obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});observation_contract(obs)
            initial=dict(observation_sha256=hashlib.sha256(obs.tobytes()).hexdigest(),state_sha256=hashlib.sha256(json.dumps(truth(env),sort_keys=True,allow_nan=False).encode()).hexdigest(),road_geometry_sha256=hashlib.sha256(np.asarray(env.unwrapped.track,dtype='<f8').tobytes()).hexdigest(),physical_obstacles_sha256=hashlib.sha256(np.asarray([[*map(float,o.position),float(o.fixtures[0].shape.radius)] for o in env.unwrapped.obstacles],dtype='<f8').tobytes()).hexdigest())
            old=json.loads(Path(job['initial_reference']).read_text());assert initial==old['initial'],'initial mismatch'
            for worker,config in [(legal,job['policy']),(teacher,p['teacher'])]:
                response,ms=worker.call('reset',obs);validate_response(response,config,obs,'reset');assert ms<=5000
            observations.append(obs.copy());obshash.update(obs.tobytes());starttime=env.unwrapped.t;track=[list(map(float,x)) for x in env.unwrapped.track];budget=Budget(path,label)
            if job.get('replay'):
                ref=Path(job['replay']);saved=np.load(ref/'commands-features.npz');commands=saved['executed'];oldfeatures=saved['features'];oldrows=json.loads((ref/'diagnostic.json').read_text())['actual_steps'];old=json.loads((ref/'result.json').read_text());assert hashlib.sha256(commands.tobytes()).hexdigest()==old['action_sequence_sha256'];limit=min(remaining,len(commands))
            else:limit=remaining
            for step in range(1,limit+1):
                native_window(p);response,ms=legal.call('act',obs);nominal_or_policy=validate_response(response,job['policy'],obs,'act');assert ms<=5000;legal_ms.append(ms)
                legalcpu=max(legalcpu,response['actor_cumulative_CPU_s'])
                features=np.asarray(response['shadow_features'],np.float64)
                nominal=np.asarray(response.get('nominal_action',response['action']),np.float32)
                action=commands[step-1].copy() if job.get('replay') else nominal_or_policy
                if oldfeatures is not None:assert np.array_equal(features,oldfeatures[step-1]),'legal features replay mismatch'
                assert action[0]==nominal[0]
                tr,tms=teacher.call('act',obs);teacher_nominal=validate_response(tr,p['teacher'],obs,'act');assert tms<=5000;teacher_ms.append(tms);teachercpu=max(teachercpu,tr['actor_cumulative_CPU_s'])
                if (step-1)%3==0:
                    t=time.perf_counter();snapshot=capture(env);capturewall+=time.perf_counter()-t
                    target,previous,receipt=query(snapshot,teacher_nominal,p['oracle'],step,previous,track,actual_previous_steer)
                    # Only this actual state's first control has a training target.
                    data.append(dict(action=step,features=features.tolist(),nominal=nominal.tolist(),executed=action.tolist(),teacher=target.tolist()))
                    receipt['snapshot']=snapshot;queries.append(receipt)
                    if receipt['wall_s']>5:print(json.dumps(dict(privileged_query_slow=True,road=label,action=step,wall=receipt['wall_s'])),flush=True)
                oldtime=env.unwrapped.t;obs,_,ended,truncated,info=budget.step(env,action);used+=1;observation_contract(obs);observations.append(obs.copy());acthash.update(action.tobytes());obshash.update(obs.tobytes())
                actual=truth(env);visited={int(t.idx) for t in env.unwrapped.road if t.road_visited};prefix=next((i for i in range(len(track)) if i not in visited),len(visited));row=dict(action=step,state=actual,contiguous_tiles=prefix,terminal=bool(ended or truncated),collision=bool(info['collision']),raw_ticks=round((env.unwrapped.t-oldtime)*50));endpoints.append(row)
                if oldrows is not None:
                    expected=oldrows[step-1]
                    for key in ['position','speed_m_s','damage','unique_tiles','off_track_counter']:assert actual[key]==expected[key],f'endpoint mismatch{step}:{key}'
                    assert prefix==expected['contiguous_tiles'] and bool(ended or truncated)==expected['terminal'] and bool(info['collision'])==expected['collision']
                    assert sum(bool(w.tiles) for w in env.unwrapped.car.wheels)==expected['wheel_road_contacts']
                ack,ms=teacher.call('feedback',action);feedback_ms.append(ms);assert ack['previous_steer']==float(action[0]) and np.array_equal(ack['executed_action'],action)
                teachercpu=max(teachercpu,ack['actor_cumulative_CPU_s']);actual_previous_steer=float(action[0])
                if step%30==0:print(json.dumps(dict(road=label,native=used,queries=len(queries),visited=actual['unique_tiles'],damage=actual['damage'])),flush=True)
                if ended or truncated:break
            if job.get('replay'):
                assert used==len(commands) and obshash.hexdigest()==old['observation_sequence_sha256'],'incomplete/mismatched replay'
                assert sum(x['raw_ticks'] for x in endpoints)==old['raw_step_ticks']
            finish=env.unwrapped.finish_time_s
            r.update(completed=finish is not None,censored=not bool(ended or truncated),lap_ms=round((finish-starttime)*1000) if finish is not None else None,retire_reason=info['retire_reason'] if ended or truncated else 'global_cap_censored',damage=env.damage.damage,unique_tiles=env.unwrapped.tile_visited_count,total_tiles=len(track))
        except Exception as exc:qualified=False;error=type(exc).__name__+': '+str(exc);r['error']=error
        finally:
            for name,worker in [('legal',legal),('teacher',teacher)]:
                if worker is not None:r[name+'_reaping']=worker.close();r[name+'_peak_RSS_mib']=worker.observed_peak_rss_bytes/1048576
            if env is not None:env.close()
            charged=json.loads((root/'budget.json').read_text())['stages'].get(label,0);assert charged==used
            dump(folder/'queries-private.json',queries);dump(folder/'endpoints-private.json',endpoints)
            if qualified:
                cache=folder/'cache.npz';np.savez_compressed(cache,observations=np.asarray(observations,np.float32),actions=np.asarray([x['action'] for x in data],int),features=np.asarray([x['features'] for x in data],float),nominal=np.asarray([x['nominal'] for x in data],np.float32),executed=np.asarray([x['executed'] for x in data],np.float32),teacher=np.asarray([x['teacher'] for x in data],np.float32));cache.chmod(0o600)
            r.update(road=label,qualified=qualified,native_actions=used,target_rows=len(data),replay=bool(job.get('replay')),initial=initial,legal_CPU_s=legalcpu,teacher_CPU_s=teachercpu,wall_s=time.perf_counter()-wall,evaluator_CPU_s=time.process_time()-cpu,legal_call_ms=legal_ms,teacher_nominal_call_ms=teacher_ms,teacher_feedback_ms=feedback_ms,capture_wall_s=capturewall,model_queries=sum(x['model_queries'] for x in queries),model_physics_ticks=sum(x['model_physics_ticks'] for x in queries),model_CPU_s=sum(x['CPU_s'] for x in queries),query_wall_s=sum(x['wall_s'] for x in queries),action_sequence_sha256=acthash.hexdigest(),observation_sequence_sha256=obshash.hexdigest())
            dump(folder/'result.json',r);records.append(r);print(json.dumps(dict(road=label,native=used,targets=len(data),completed=r.get('completed'),error=r.get('error'))),flush=True)
        if error:break
    native=json.loads((root/'budget.json').read_text())['actions'];assert native==sum(r['native_actions'] for r in records)<=2400
    dump(root/'outcome.json',dict(stage=229,records=records,native_actions=native,wall_s=time.perf_counter()-start,error=error,unexecuted_roads=[j['road'] for j in p['jobs'][len(records):]],evaluator_peak_RSS_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,all_workers_reaped=all(r[k]['process_reaped'] and r[k]['actor_pids_absent'] for r in records for k in ['legal_reaping','teacher_reaping']),aggregated_head_closed_loop_runs=0))


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True);collect(a.parse_args().plan.resolve())
