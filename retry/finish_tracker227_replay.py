"""Replay saved F1 pedal-arm controls once and observe official tracker ticks.

No policy, head or planner is called. Private plan/reference paths are supplied
by --plan. A mismatch stops execution and disqualifies the diagnosis. The
original record has reset and complete rolling observation hashes only.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import time
import numpy as np


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    path.chmod(0o600)


def replay(path):
    from core.finish_line import FinishLineTracker,MIN_FORWARD_CROSSING_SPEED,MAX_LATERAL_TO_FORWARD_RATIO
    from retry.diagnose import Budget,make_env
    from retry.evaluate import observation_contract
    from retry.frozen_paired_evaluation import verify_files,native_window
    from retry.full_route_reproduction import truth
    p=json.loads(path.read_text());assert sha(path)==path.with_suffix('.sha256').read_text().strip()
    verify_files(p['source_sha256']);verify_files(p['runtime_sha256']);native_window(p)
    root=path.parent;ref=Path(p['reference']);old=json.loads((ref/'result.json').read_text())
    oldrows=json.loads((ref/'diagnostic.json').read_text())['actual_steps']
    commands=np.load(ref/'commands-features.npz',allow_pickle=False)['executed']
    assert commands.dtype==np.float32 and commands.shape==(494,3)
    assert sha(ref/'commands-features.npz')==p['commands_file_sha256']
    assert hashlib.sha256(commands.tobytes()).hexdigest()==old['action_sequence_sha256']
    write(root/'opening.json',dict(at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),native_cap=500,commands=494))
    ctx=dict(action=0);raw=[];endpoint=[];original=FinishLineTracker.update;env=None;used=0;qualified=False;error=None;digest=hashlib.sha256();start=time.perf_counter();cpu=time.process_time();observerCPU=observerWall=0.
    def observed(self,position,velocity,progress,physics_time_s):
        nonlocal observerCPU,observerWall
        t,c=time.perf_counter(),time.process_time();before=vars(self).copy()
        result=original(self,position,velocity,progress,physics_time_s)
        after=vars(self).copy();fx,fy=self.forward;lx,ly=fy,-fx;rx,ry=position[0]-self.center[0],position[1]-self.center[1]
        longitudinal=rx*fx+ry*fy;lateral=rx*lx+ry*ly;fs=velocity[0]*fx+velocity[1]*fy;ls=velocity[0]*lx+velocity[1]*ly
        inside=abs(lateral)<=self.half_width;previnside=abs(before['previous_lateral'])<=self.half_width
        q=progress>=self.qualification_ratio
        back_transition=previnside and inside and before['previous_longitudinal']<=-self.half_depth and longitudinal>-self.half_depth
        direction=bool(np.isfinite(fs) and np.isfinite(ls) and fs>MIN_FORWARD_CROSSING_SPEED and abs(ls)<=fs*MAX_LATERAL_TO_FORWARD_RATIO)
        raw.append(dict(tick=len(raw)+1,action=ctx['action'],physics_time_s=physics_time_s,progress=progress,
            position=list(position),velocity=list(velocity),longitudinal=longitudinal,lateral=lateral,
            forward_speed=fs,lateral_speed=ls,before=before,after=after,finished_return=bool(result),
            conditions=dict(qualified=q,inside_width=inside,previous_inside_width=previnside,
                back_boundary_transition=back_transition,entered_from_back=q and back_transition,
                direction_valid=direction,centerline_forward_transition=before['previous_longitudinal']<0<=longitudinal)))
        observerCPU+=time.process_time()-c;observerWall+=time.perf_counter()-t
        return result
    FinishLineTracker.update=observed
    try:
        env=make_env();budget=Budget(path,'F1_fixed_replay');case=p['case']
        obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});observation_contract(obs)
        assert hashlib.sha256(obs.tobytes()).hexdigest()==old['initial']['observation_sha256'],'reset_observation_mismatch'
        assert hashlib.sha256(json.dumps(truth(env),sort_keys=True,allow_nan=False).encode()).hexdigest()==old['initial']['state_sha256'],'reset_state_mismatch'
        assert hashlib.sha256(np.asarray(env.unwrapped.track,dtype='<f8').tobytes()).hexdigest()==old['initial']['road_geometry_sha256']
        obstacles=[[*map(float,item.position),float(item.fixtures[0].shape.radius)] for item in env.unwrapped.obstacles]
        assert hashlib.sha256(np.asarray(obstacles,dtype='<f8').tobytes()).hexdigest()==old['initial']['physical_obstacles_sha256']
        assert round(env.unwrapped.t*50)==51
        digest.update(obs.tobytes())
        for i,command in enumerate(commands):
            native_window(p);ctx['action']=i+1;previous=obs;oldtime=env.unwrapped.t
            obs,_,ended,truncated,info=budget.step(env,command);used+=1;observation_contract(obs)
            assert np.array_equal(obs[:3],previous[1:]),'frame_stack_mismatch';digest.update(obs.tobytes())
            actual=truth(env);expected=oldrows[i]
            for key in ['position','speed_m_s','damage','unique_tiles','off_track_counter']:
                assert actual[key]==expected[key],f'endpoint_mismatch_action_{i+1}_{key}'
            assert bool(info['collision'])==expected['collision'];assert bool(ended or truncated)==expected['terminal']
            visited={int(t.idx) for t in env.unwrapped.road if t.road_visited};prefix=next((j for j in range(len(env.unwrapped.road)) if j not in visited),len(visited))
            assert prefix==expected['contiguous_tiles']
            assert sum(bool(w.tiles) for w in env.unwrapped.car.wheels)==expected['wheel_road_contacts']
            endpoint.append(dict(action=i+1,raw_ticks=round((env.unwrapped.t-oldtime)*50),state=actual,tracker=vars(env.unwrapped.finish_line_tracker).copy(),finish_qualified=info['finish_qualified'],finished=info['finished'],retire_reason=info['retire_reason']))
            if used%100==0:print(json.dumps(dict(native=used,visited=actual['unique_tiles'],qualified=info['finish_qualified'],finished=info['finished'])),flush=True)
            if ended or truncated:assert i==len(commands)-1,'early_terminal'
        assert digest.hexdigest()==old['observation_sequence_sha256'],'rolling_observation_sequence_mismatch'
        assert len(raw)==old['raw_reset_ticks']+old['raw_step_ticks']
        assert endpoint[-1]['retire_reason']==old['retire_reason'] and not endpoint[-1]['finished']
        qualified=True
    except Exception as exc:error=type(exc).__name__+': '+str(exc)
    finally:
        FinishLineTracker.update=original
        if env is not None:env.close()
        ledger=json.loads((root/'budget.json').read_text());assert ledger['actions']==used<=500
        write(root/'tracker-private.json',dict(raw_ticks=raw,endpoints=endpoint))
        write(root/'outcome.json',dict(stage=227,qualified=qualified,error=error,native_actions=used,wall_s=time.perf_counter()-start,evaluator_CPU_s=time.process_time()-cpu,observer_CPU_s=observerCPU,observer_wall_s=observerWall,raw_ticks=len(raw),complete_observation_hash_matches=qualified,recorded_endpoint_fields_match=qualified,student_or_teacher_calls=0,model_queries=0,commands_changed=False,HOLDOUT_used=False,SEALED_opened=False))


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--plan',type=Path,required=True);replay(ap.parse_args().plan.resolve())
