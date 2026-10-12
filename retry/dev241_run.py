"""Four once-only newDEV241 runs of unchanged240, privatepixels/features cache."""
import argparse
import json
from pathlib import Path
import time
import numpy as np


def run(path):
    from retry import diagnose,frozen_composite_runtime as runtime
    from retry.frozen_paired_evaluation import episode,sha,verify_files,write
    from retry.full_route_reproduction import truth
    from core.finish_line import FinishLineTracker
    p=json.loads(path.read_text());assert sha(path)==path.with_suffix('.sha256').read_text().strip();verify_files(p['source_sha256']);verify_files(p['runtime_sha256'])
    write(path.parent/'opening.json',dict(stage=241,native_cap=2200,one_use=True,declared_split='DEV_241'),exclusive=True)
    records=[];start=time.perf_counter();error=None
    for label,case in zip(p['labels'],p['cases']):
        remaining=2200-json.loads((path.parent/'budget.json').read_text())['actions']
        if remaining<=0:break
        observations=[];features=[];nominal=[];base=[];executed=[];compute=[];rows=[];memory=[];crossings=[];scene={}
        factory,preparer=diagnose.make_env,runtime.prepare;tracker_update=FinishLineTracker.update;context={'action':0}
        def update(tracker,position,velocity,progress,physics_time_s):
            before=vars(tracker).copy();returned=tracker_update(tracker,position,velocity,progress,physics_time_s)
            long,lat=tracker.previous_longitudinal,tracker.previous_lateral
            if abs(lat)<=tracker.half_width and abs(before['previous_lateral'])<=tracker.half_width and ((before['previous_longitudinal']<0<=long) or (before['previous_longitudinal']>=0>long)):
                crossings.append(dict(action=context['action'],direction='forward' if long>=0 else 'reverse',qualified=progress>=.95,physics_time_s=physics_time_s))
            return returned
        FinishLineTracker.update=update
        def observed_factory(*a,**kw):
            env=factory(*a,**kw);reset,step=env.reset,env.step
            def observed_reset(*a,**kw):
                output=reset(*a,**kw);scene.update(track=np.asarray(env.unwrapped.track).tolist(),initial=truth(env));return output
            def observed_step(action):
                context['action']=len(rows)+1;before_time=env.unwrapped.t;output=step(action);t=truth(env);observations.append(output[0].copy())
                track=np.asarray(env.unwrapped.track);i=int(np.argmin(np.sum((track[:,2:4]-np.asarray(t['position']))**2,axis=1)));beta=float(track[i,1]);tangent=float(np.dot(t['velocity'],[-np.sin(beta),np.cos(beta)]))
                rows.append(dict(action=len(rows)+1,speed_m_s=t['speed_m_s'],damage=t['damage'],visited=t['unique_tiles'],off_track_counter=t['off_track_counter'],collision=bool(output[4]['collision']),position=t['position'],velocity=t['velocity'],nearest_road_tangent_speed=tangent,wheel_road_contacts=sum(bool(w.tiles) for w in env.unwrapped.car.wheels),raw_ticks=round((env.unwrapped.t-before_time)*50),terminal=bool(output[2] or output[3])))
                if len(rows)%100==0:print(json.dumps(dict(road=label,native=len(rows),visited=t['unique_tiles'],damage=t['damage'])),flush=True)
                return output
            env.reset,env.step=observed_reset,observed_step;return env
        def observed_prepare(*a,**kw):
            actor=preparer(*a,**kw);call=actor.call
            def observed_call(op,observation):
                if op=='reset':observations.append(observation.copy())
                response,ms=call(op,observation)
                if op=='act':
                    assert np.array_equal(observation,observations[-1]);f=response['legal_feature_audit'];s=response['scale_audit'];assert len(f['features'])==16 and s['nominal_memory_preserved'] and s['steering_unchanged']
                    features.append(f['features']);nominal.append(f['nominal_action']);base.append(f['base232_action']);executed.append(response['action']);memory.append(f['nominal_memory_after']);compute.append(response['act_compute_ms'])
                return response,ms
            actor.call=observed_call;return actor
        diagnose.make_env,runtime.prepare=observed_factory,observed_prepare
        try:r=episode(path,dict(p,max_steps=remaining),case,'C',{})
        finally:
            diagnose.make_env,runtime.prepare=factory,preparer;FinishLineTracker.update=tracker_update
        folder=path.parent/'runs'/(case['id']+'__C')
        cache=folder/'legal-cache.npz';np.savez_compressed(cache,observations=np.asarray(observations,np.float32),features=np.asarray(features,np.float64),nominal=np.asarray(nominal,np.float32),base232=np.asarray(base,np.float32),executed=np.asarray(executed,np.float32),nominal_memory_after=np.asarray(memory,np.float64));cache.chmod(0o600)
        assert len(observations)==len(features)+1==len(rows)+1
        write(folder/'diagnostic.json',dict(actual_steps=rows,source_startline_crossings=crossings,full_Agent_compute_ms=compute,GT_to_policy=False,features_are_prestep_legal=True),exclusive=True);write(folder/'scene-private.json',scene,exclusive=True)
        records.append(dict(road=label,result=r,cache_bytes=cache.stat().st_size));print(json.dumps(dict(road=label,completed=r['completed'],lap_ms=r['lap_ms'],native=r['charged_wrapper_actions'],reason=r['retire_reason'],damage=r['damage'],error=r.get('error'))),flush=True)
        if r.get('error'):error=r['error'];break
    ledger=json.loads((path.parent/'budget.json').read_text());assert ledger['actions']==sum(x['result']['charged_wrapper_actions'] for x in records)<=2200
    write(path.parent/'outcome.json',dict(stage=241,records=records,native_actions=ledger['actions'],wall_s=time.perf_counter()-start,technical_error=error,unexecuted=p['labels'][len(records):],all_workers_reaped=all(x['result']['reaping']['process_reaped'] and x['result']['reaping']['actor_pids_absent'] for x in records),champion_changed=False,HOLDOUT_opened=False,SEALED_opened=False,automatic_next_experiment=False),exclusive=True)


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
