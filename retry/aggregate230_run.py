"""Four frozen229 aggregate pedal runs on DEV, shared2000cap, no retraining.

--plan supplies private DEV cases and immutable model-only assets. The unchanged
default evaluator enforces reset/act 5s. Endpoint truth is diagnosis only and
never sent to the student. Historical controls are never rerun here.
"""
import argparse
import json
from pathlib import Path
import time
import numpy as np


def run(path):
    from retry import diagnose
    import retry.frozen_composite_runtime as runtime
    from retry.frozen_paired_evaluation import episode,write,sha,verify_files,native_window
    from retry.full_route_reproduction import truth
    from core.finish_line import FinishLineTracker
    p=json.loads(path.read_text());assert sha(path)==path.with_suffix('.sha256').read_text().strip()
    verify_files(p['source_sha256']);verify_files(p['runtime_sha256']);native_window(p)
    write(path.parent/'opening.json',dict(stage=230,native_cap=2000,one_use=True),exclusive=True)
    records=[];start=time.perf_counter();error=None;cap_unexecuted=[]
    for label,case in zip(p['labels'],p['cases']):
        remaining=2000-json.loads((path.parent/'budget.json').read_text())['actions']
        if remaining<=0:cap_unexecuted=p['labels'][len(records):];break
        nominal=[];actual=[];features=[];lat=[];headlat=[];rows=[];state_rows=[];crossings=[]
        tracker_update=FinishLineTracker.update;context={'action':0}
        def update(tracker,position,velocity,progress,physics_time_s):
            before=vars(tracker).copy();returned=tracker_update(tracker,position,velocity,progress,physics_time_s)
            fx,fy=tracker.forward;fs=velocity[0]*fx+velocity[1]*fy
            lateral=tracker.previous_lateral;longitudinal=tracker.previous_longitudinal
            if abs(lateral)<=tracker.half_width and abs(before['previous_lateral'])<=tracker.half_width and ((before['previous_longitudinal']<0<=longitudinal) or (before['previous_longitudinal']>=0>longitudinal)):
                crossings.append(dict(action=context['action'],physics_time_s=physics_time_s,progress=progress,forward_speed=fs,direction='forward' if longitudinal>=0 else 'reverse',qualified=progress>=tracker.qualification_ratio))
            return returned
        FinishLineTracker.update=update
        old_factory,old_prepare=diagnose.make_env,runtime.prepare
        observer_cpu=observer_wall=0.
        def factory(*a,**k):
            env=old_factory(*a,**k);old_step=env.step
            def step(command):
                nonlocal observer_cpu,observer_wall
                context['action']=len(rows)+1
                output=old_step(command);wall,cpu=time.perf_counter(),time.process_time()
                t=truth(env);_,_,ended,truncated,info=output
                visited={int(tile.idx) for tile in env.unwrapped.road if tile.road_visited}
                prefix=next((i for i in range(len(env.unwrapped.road)) if i not in visited),len(visited))
                track=np.asarray(env.unwrapped.track)
                nearest=int(np.argmin(np.sum((track[:,2:4]-np.asarray(t['position']))**2,axis=1)))
                beta=float(track[nearest,1])
                tangent_speed=float(np.dot(t['velocity'],[-np.sin(beta),np.cos(beta)]))
                rows.append(dict(step=len(rows)+1,command=np.asarray(command,np.float32).tolist(),
                    speed_m_s=t['speed_m_s'],damage=t['damage'],unique_tiles=t['unique_tiles'],
                    off_track_counter=t['off_track_counter'],position=t['position'],
                    collision=bool(info['collision']),terminal=bool(ended or truncated),
                    finish_tracker=vars(env.unwrapped.finish_line_tracker).copy(),
                    nearest_road_tangent_speed=tangent_speed,
                    contiguous_tiles=prefix,wheel_road_contacts=sum(bool(w.tiles) for w in env.unwrapped.car.wheels)))
                observer_cpu+=time.process_time()-cpu;observer_wall+=time.perf_counter()-wall
                if len(rows)%100==0:print(json.dumps(dict(road=label,native=len(rows),visited=t['unique_tiles'],damage=t['damage'])),flush=True)
                return output
            env.step=step
            return env
        def prepare(*a,**k):
            worker=old_prepare(*a,**k);call=worker.call
            def observed(operation,observation):
                response,ms=call(operation,observation)
                if operation=='act':
                    assert response['nominal_memory_preserved']
                    nominal.append(response['nominal_action']);actual.append(response['action'])
                    features.append(response['shadow_features']);lat.append(response['student_total_compute_ms']);headlat.append(response['head_inference_ms'])
                    state_rows.append(dict(before=response['shadow_controller_before'],after=response['shadow_state_after'],memory=response['memory']))
                return response,ms
            worker.call=observed
            return worker
        diagnose.make_env,runtime.prepare=factory,prepare
        cp=dict(p,arms={'S':p['student_by_road'][label]},max_steps=remaining)
        try:r=episode(path,cp,case,'S',{})
        finally:
            diagnose.make_env,runtime.prepare=old_factory,old_prepare
            FinishLineTracker.update=tracker_update
        folder=path.parent/'runs'/(case['id']+'__S')
        write(folder/'diagnostic.json',dict(actual_steps=rows,student_compute_ms=lat,head_inference_ms=headlat,
            pixel_state_rows=state_rows,finish_crossings=crossings,observer_GT_CPU_s=observer_cpu,observer_GT_wall_s=observer_wall,
            GT_inputs_to_student=False,model_queries=0),exclusive=True)
        cache=folder/'commands-features.npz';np.savez_compressed(cache,nominal=np.asarray(nominal,np.float32),
            executed=np.asarray(actual,np.float32),features=np.asarray(features,np.float64));cache.chmod(0o600)
        records.append(dict(road=label,result=r,observer_GT_CPU_s=observer_cpu,observer_GT_wall_s=observer_wall))
        print(json.dumps(dict(road=label,completed=r['completed'],lap_ms=r['lap_ms'],native=r['charged_wrapper_actions'],reason=r['retire_reason'],error=r.get('error'))),flush=True)
        if r.get('error'):error=r['error'];break
    ledger=json.loads((path.parent/'budget.json').read_text())
    assert ledger['actions']==sum(x['result']['charged_wrapper_actions'] for x in records)<=2000
    write(path.parent/'outcome.json',dict(stage=230,records=records,native_actions=ledger['actions'],wall_s=time.perf_counter()-start,
        technical_error=error,unexecuted_roads=p['labels'][len(records):],cap_unexecuted=cap_unexecuted,model_queries=0,model_physics_ticks=0,
        all_workers_reaped=all(x['result']['reaping']['process_reaped'] and x['result']['reaping']['actor_pids_absent'] for x in records),
        champion_changed=False,HOLDOUT_used=False,SEALED_opened=False,automatic_next_experiment=False),exclusive=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--plan',type=Path,required=True);run(ap.parse_args().plan.resolve())
