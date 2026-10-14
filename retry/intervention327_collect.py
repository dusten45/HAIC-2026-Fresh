"""Fixed64-prefix, one-action matched native experiment; no full-lap evaluation."""
import argparse
import datetime
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from retry.path271_run import read,save,sha


def digest(data):return hashlib.sha256(data).hexdigest()


def command(base,arm):
    action=np.array(base,np.float32).copy()
    if arm in ['steer_plus','steer_minus']:
        action[0]=np.float32(np.clip(float(action[0])+(.08 if arm=='steer_plus' else -.08),-.4,.4))
    elif arm=='pedal':action[1]=0.;action[2]=max(float(action[2]),.5)
    else:assert arm=='baseline'
    return action


def verify(D):
    p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for q,h in p['input_hashes'].items():assert sha(q)==h,q
    return p


def preflight(R):
    from retry.frozen_composite_runtime import prepare
    D=R/'stage327';p=verify(D);assert not (D/'preflight.json').exists()
    start,cpu=time.perf_counter(),time.process_time();F=R/'stage306/collection/O0'
    z=np.load(F/'observations-actions-private.npz');trace=[json.loads(s) for s in (F/'trace-private.jsonl').read_text().splitlines()]
    receipts=[];actorcpu=0.
    for repeat in range(2):
        worker=prepare(p['config'],D/'preflight'/str(repeat),p['sandbox_path']);states=[]
        try:
            worker.call('reset',z['observations'][0])
            for i in range(65):
                r,_=worker.call('act',z['observations'][i]);assert r['features']==trace[i]['features']
                action=np.array(r['action'],np.float32);assert np.array_equal(action,z['actions'][i]);states.append(r['state'])
                c,_=worker.call('commit',action);actorcpu=c['actor_cumulative_CPU_s']
            peek,_=worker.call('peek',z['observations'][65]);assert peek['peek_state_preserved']
            receipts.append(states)
        finally:reaped=worker.close()
        assert reaped['process_reaped'] and reaped['actor_pids_absent']
    assert receipts[0]==receipts[1]
    for base in [[.39,.7,.02],[-.39,.2,.7],[0.,.4,.03]]:
        for arm in p['arms']:
            out=command(base,arm)
            if arm.startswith('steer'):assert np.array_equal(out[1:],np.array(base,np.float32)[1:])
            if arm=='pedal':assert out[0]==np.float32(base[0]) and out[1]==0 and out[2]==np.float32(max(base[2],.5))
    save(D/'preflight.json',dict(OFF_cached_actions_features_exact=130,crossprocess_full_policy_receipts_exact=True,pure_post_peek=True,command_channel_clip_checks=True,
                                new_native=0,new_fits=0,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu,last_actor_CPU_s=actorcpu))
    print('327 preflight passed: OFF130, full policy hash crossprocess exact, purepostpeek, native0',flush=True)


def arm_run(R,p,item):
    from retry.frozen_composite_runtime import prepare
    from retry.diagnose import make_env
    D=R/'stage327';road,arm=item['road'],item['arm'];F=D/'runs'/(road+'_'+arm)
    assert not F.exists();F.mkdir(parents=True,mode=0o700);save(F/'opening.json',dict(epoch=time.time()))
    worker=env=None;frames=[];actions=[];bases=[];times=[];events=[];rawticks=0;steps=0;actorcpu=0.;terminal=complete=False;error=None;boundary=None;post=None;reaping=None;reset_ticks=0
    start,cpu=time.perf_counter(),time.process_time();prefix=hashlib.sha256()
    try:
        worker=prepare(p['config'],F/'cpu',p['sandbox_path']);env=make_env();case=p['cases'][road]
        obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});raw=env.unwrapped
        assert digest(obs.tobytes())==p['initial_observations'][road]
        assert digest(np.asarray(raw.track,dtype='<f8').tobytes())==case['road_geometry_sha256']
        reset_ticks=round(raw.t*50);reset,_=worker.call('reset',obs);previous_state=reset['state'];frames.append(obs.copy());times.append(float(raw.t))
        journal=(F/'trace-private.jsonl').open('x');(F/'trace-private.jsonl').chmod(0o600)
        try:
            for step in range(1,66):
                assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
                state_before=previous_state
                r,ms=worker.call('act',obs);assert ms<=5000 and not r['python_audit_denied_events'];base=np.array(r['action'],np.float32)
                action=base.copy()
                if step==65:
                    boundary=dict(road=road,arm=arm,prefix_actions=64,action_step=65,prefix_sha256=prefix.hexdigest(),pre_pixel_sha256=digest(obs.tobytes()),
                                  state_before=state_before,state_after_baseline_act=r['state'],features=r['features'],base_action=base.tolist(),actual_time=float(raw.t))
                    if arm!='baseline':
                        reference=read(D/'runs'/(road+'_baseline')/'boundary-private.json')
                        for k in ['prefix_sha256','pre_pixel_sha256','state_before','state_after_baseline_act','features','base_action','actual_time']:assert boundary[k]==reference[k],k
                    save(F/'boundary-private.json',boundary);action=command(base,arm)
                c,_=worker.call('commit',action);assert np.float32(c['memory'])==action[0] and c['history'][-1]==action.tolist();previous_state=c['state'];actorcpu=c['actor_cumulative_CPU_s']
                b=read(D/'budget.json');assert b['actions']<p['native_cap'];b['actions']+=1;save(D/'budget.json',b)
                before=float(raw.t);obs,_,ended,truncated,info=env.step(action);steps=step
                ticks=round((raw.t-before)*50);rawticks+=ticks;terminal=bool(ended or truncated);complete=raw.finish_time_s is not None
                frames.append(obs.copy());times.append(float(raw.t));actions.append(action.copy());bases.append(base.copy())
                row=dict(step=step,action=action.tolist(),base=base.tolist(),features=r['features'],state_before=state_before,state_after_act=r['state'],state_after_commit=c['state'],
                         pre_pixel_sha256=digest(frames[-2].tobytes()),post_pixel_sha256=digest(obs.tobytes()),raw_ticks=ticks,
                         collision_flag_present='collision' in info,collision=bool(info['collision']) if 'collision' in info else None,official_ended=bool(ended),official_truncated=bool(truncated),retire_reason=info.get('retire_reason'))
                journal.write(json.dumps(row,allow_nan=False)+'\n');journal.flush();events.append(row)
                if step<=64:
                    prefix.update(frames[-2].tobytes());prefix.update(obs.tobytes());prefix.update(json.dumps(row,sort_keys=True,separators=(',',':')).encode())
                if terminal:break
        finally:journal.close()
        if steps==65:
            peek,_=worker.call('peek',obs);assert peek['peek_state_preserved']
            post=dict(pixel_sha256=digest(obs.tobytes()),features=peek['features'],state_after_commit=previous_state,actual_time=float(raw.t),
                      pure_post_peek=True,official_terminal=terminal,completed=complete,collision=events[-1]['collision'],collision_flag_present=events[-1]['collision_flag_present'])
            save(F/'post-private.json',post)
    except BaseException as exception:
        error=type(exception).__name__+': '+str(exception);save(F/'error-private.json',dict(error=error,traceback=__import__('traceback').format_exc()))
    finally:
        if worker:reaping=worker.close()
        if env:env.close()
    if frames:
        q=F/'raw-pixels-actions-private.npz';np.savez_compressed(q,observations=np.array(frames,np.float32),actions=np.array(actions,np.float32),base_actions=np.array(bases,np.float32),actual_times=np.array(times));q.chmod(0o600)
    result=dict(road=road,arm=arm,native_actions=steps,charged_total=read(D/'budget.json')['actions'],reached_endpoint=steps==65 and post is not None,
                protocol_stop=steps==65 and not terminal and error is None,official_terminal=terminal,completed=complete,actual_DNF=bool(terminal and not complete),
                endpoint_missing=post is None,official_terminal_before_target=bool(terminal and steps<65),retire_reason=events[-1]['retire_reason'] if events else None,
                technical_error=error,raw_step_ticks=rawticks,raw_reset_ticks=reset_ticks,actor_CPU_s=actorcpu,runner_CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,
                reaping=reaping,new_source_physics_ticks=0,GT_runtime_policy=False)
    save(F/'result.json',result);return result


def run(R):
    D=R/'stage327';p=verify(D);assert read(D/'preflight.json')['crossprocess_full_policy_receipts_exact']
    assert not (D/'opening.json').exists();save(D/'opening.json',dict(epoch=time.time(),code_sha256=sha(Path(__file__))))
    results=[]
    for item in p['order']:
        if p['native_cap']-read(D/'budget.json')['actions']<65:break
        result=arm_run(R,p,item);results.append(result);save(D/'partial-private.json',results)
        print(json.dumps({k:result[k] for k in ['road','arm','native_actions','reached_endpoint','protocol_stop','official_terminal','technical_error']}),flush=True)
        if result['technical_error'] or not result['reached_endpoint']:break
    save(D/'outcome-private.json',dict(results=results,wall_s=time.time()-read(D/'opening.json')['epoch'],all_planned=len(results)==12))
    print('327 fixed collection ended; no full-episode continuation',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['preflight','run']);parser.add_argument('--private-root',type=Path,required=True)
    args=parser.parse_args();globals()[args.phase](args.private_root.resolve())
