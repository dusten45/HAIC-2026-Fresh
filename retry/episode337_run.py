"""One actual episode, verified335prefix, finish-aware genuine termination."""
import argparse
from dataclasses import asdict,is_dataclass
import json
import random
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.pedal331_run import plain,rng,physical
from retry.episode337_stage import verify,register_actual


def json_default(value):
    """Diagnostic serialization only; unsupported objects remain hard errors."""
    if is_dataclass(value) and not isinstance(value,type):return asdict(value)
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,np.generic):return value.item()
    raise TypeError('Unsupported diagnostic type: '+type(value).__name__)


def finish_record(raw):
    tracker=raw.finish_line_tracker
    return plain(dict(finish_qualified_time_s=raw.finish_qualified_time_s,finish_time_s=raw.finish_time_s,tracker=dict(tracker.__dict__) if tracker else None,raw_time=raw.t))


def compact(snapshot):
    snapshot=dict(snapshot);roads=snapshot.pop('roads');snapshot['visited_tile_ids']=[r['idx'] for r in roads if r['visited']];snapshot['road_static_geometry']='Seeinitialfullscene; unchangedstaticbodycontract';return snapshot


def run(R):
    from retry.frozen_composite_runtime import prepare
    from retry.diagnose import make_env
    from retry.full_route_reproduction import truth
    D=R/'stage337';p=verify(R,True);assert read(D/'cache-receipt.json')['passed'];assert not (D/'episode-opening.json').exists();save(D/'episode-opening.json',dict(epoch=time.time(),runner_sha256=sha(Path(__file__))))
    F=D/'B';F.mkdir(mode=0o700);z=np.load(R/'stage335/B/raw-pixels-actions-private.npz');old=[json.loads(s) for s in (R/'stage335/B/trace-private.jsonl').read_text().splitlines()];cached=read(D/'cache/records-private.json');reference_rng=read(R/'stage335/B/first-divergence-private.json')['accessible_RNG']
    random.seed(p['observer_rng_seed']);np.random.seed(p['observer_rng_seed']);w=env=None;frames=[];prefix=[];actions=[];events=[];steps=rawticks=reset_ticks=0;actorcpu=0.;error=None;ended=truncated=complete=False;info={};cap=0;prefix_verified=0;start_time=None;final_finish=None;stop_reason=None;start,cpu=time.perf_counter(),time.process_time();capture_wall=0.;policy_ms=[];raw_counter_start=None
    def record_frame(obs):
        frame=np.rint(obs[-1]*255).astype(np.uint8);assert np.array_equal(frame.astype(np.float32)/255,obs[-1]);frames.append(frame)
        expected=np.array([frames[max(0,len(frames)-4+j)] for j in range(4)]) if len(frames)>=4 else np.array(([frames[0]]*(4-len(frames)))+frames)
        assert np.array_equal(expected.astype(np.float32)/255,obs)
        if len(prefix)<73:prefix.append(obs.copy())
    try:
        w=prepare(p['config'],F/'cpu',p['sandbox_path']);env=make_env();obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});raw=env.unwrapped;reset_ticks=round(raw.t*50);start_time=float(raw.t);raw_counter_start=env.env._elapsed_steps
        cap=register_actual(R,env);assert np.array_equal(obs,z['observations'][0]);assert __import__('hashlib').sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest()==p['case']['road_geometry_sha256'];save(F/'initial-scene-private.json',physical(env));policy,_=w.call('reset',obs);assert policy['state']==read(D/'cache/reset-private.json')['state'];record_frame(obs)
        journal=(F/'trace-private.jsonl').open('x');(F/'trace-private.jsonl').chmod(0o600)
        try:
            for i in range(cap):
                verify(R);pre=plain(truth(env));tick=time.perf_counter();before_physical=physical(env);capture_wall+=time.perf_counter()-tick;timer_before=env.env._elapsed_steps
                if i<72:
                    assert np.array_equal(obs,z['observations'][i]);assert pre==old[i]['pre'] and before_physical==old[i]['pre_physical'];assert rng(env)==reference_rng
                    expected=read(D/'cache/reset-private.json')['state'] if i==0 else cached[i-1]['commit']['state'];assert policy['state']==expected
                r,ms=w.call('act',obs);policy_ms.append(ms);assert not r['python_audit_denied_events'];command=np.asarray(r['action'],np.float32);assert r['delta_audit']['action']==command.tolist()
                if i<72:
                    assert r['action']==old[i]['returned_action'] and r['features']==old[i]['features'] and r['tracker_record']==old[i]['tracker'] and r['state']==cached[i]['response']['state'] and r['delta_audit']==old[i]['audit']
                c,_=w.call('commit',command);policy=c;actorcpu=c['actor_cumulative_CPU_s'];assert c['memory']==c['nominal_memory']==r['state']['previous_steer'] and c['history'][-1]==command.tolist() and np.float32(c['memory'])==command[0]
                if i<72:assert c['state']==old[i]['policy'] and c['memory']==old[i]['nominal_memory']
                budget=read(D/'native-budget.json');assert budget['actions']<budget['cap'];budget['actions']+=1;save(D/'native-budget.json',budget);steps+=1
                before=raw.t;obs,_,ended,truncated,info=env.step(command);ticks=round((raw.t-before)*50);rawticks+=ticks;assert env.env._elapsed_steps-timer_before==ticks and 1<=ticks<=env._skip_frames
                complete=raw.finish_time_s is not None;record_frame(obs);actions.append(command.copy());post=plain(truth(env));tick=time.perf_counter();after_physical=physical(env);capture_wall+=time.perf_counter()-tick;finish=finish_record(raw)
                row=dict(step=i+1,executed=command.tolist(),returned_action=r['action'],features=r['features'],audit=r['delta_audit'],tracker=r['tracker_record'],pixel_path=r['pixel_path'],nominal_memory=c['memory'],policy=c['state'],pre=pre,post=post,pre_physical=before_physical if i<72 else compact(before_physical),post_physical=after_physical if i<72 else compact(after_physical),collision=bool(info['collision']),damage=float(env.damage.damage),damage_increase=float(env.damage.damage)-pre['damage'],terminated=bool(ended),truncated=bool(truncated),completed=complete,finish=finish,retire_reason=info.get('retire_reason'),elapsed_raw_counter=env.env._elapsed_steps,raw_ticks=ticks,contact_interval_s=[before,float(raw.t)] if info['collision'] else None,info=plain(info))
                if i<72:
                    assert np.array_equal(obs,z['observations'][i+1]) and post==old[i]['post'] and after_physical==old[i]['post_physical'];assert row['collision']==old[i]['collision'] and row['damage']==old[i]['damage'] and bool(ended or truncated)==old[i]['terminal'];prefix_verified+=1
                    if i==71:save(D/'prefix72-qualification.json',dict(passed=True,actual_actions=72,actual_observation_stacks=73,commands_actor_state_memory_physics_accessible_RNG_exact=True,elapsed_raw_counter=env.env._elapsed_steps,raw_step_ticks=rawticks));verify(R,True)
                journal.write(json.dumps(row,allow_nan=False,default=json_default)+'\n');journal.flush();events.append(row);final_finish=finish
                if ended or truncated:stop_reason='official_finish' if complete else 'actual_retirement' if ended else 'time_limit_no_finish' if env.env._elapsed_steps>=env.env._max_episode_steps else 'other_truncation';break
            else:stop_reason='verified_action_cap_without_terminal'
        finally:journal.close()
        verify(R,True)
    except BaseException as e:
        error=type(e).__name__+': '+str(e);stop_reason='contract_or_authorization_stop';save(F/'error-private.json',dict(error=error,traceback=__import__('traceback').format_exc()))
    finally:
        actual_elapsed=env.env._elapsed_steps if env else None;max_elapsed=env.env._max_episode_steps if env else None
        if env and final_finish is None and hasattr(env.unwrapped,'finish_line_tracker'):final_finish=finish_record(env.unwrapped)
        reaping=w.close() if w else None
        if env:env.close()
    if frames:
        f=F/'frames-actions-private.npz';np.savez_compressed(f,frames_uint8=np.array(frames,np.uint8),actions=np.array(actions,np.float32),prefix_observations=np.array(prefix,np.float32));f.chmod(0o600)
    actual_retirement=bool(ended and not complete);timeout=bool(truncated and not complete and actual_elapsed is not None and max_elapsed is not None and actual_elapsed>=max_elapsed);forced=bool(error or (not ended and not truncated));finish_time=final_finish['finish_time_s'] if final_finish else None
    result=dict(native_actions=steps,registered_cap=cap,prefix72_verified=prefix_verified,comparison_valid=bool(not error and prefix_verified==72),technical_error=error,terminated=bool(ended),truncated=bool(truncated),completed=bool(complete),actual_DNF=actual_retirement,time_limit_no_finish=timeout,censored=forced or bool(truncated and not complete),stop_reason=stop_reason,retire_reason=info.get('retire_reason'),finish=final_finish,postreset_start_time=start_time,lap_ms=round((finish_time-start_time)*1000) if complete and finish_time is not None else None,first_contact=next((r['step'] for r in events if r['collision']),None),contact_actions=[r['step'] for r in events if r['collision']],damage=events[-1]['damage'] if events else None,unique_tiles=events[-1]['post']['unique_tiles'] if events else None,total_tiles=p['case'].get('road_point_count'),raw_step_ticks=rawticks,raw_reset_ticks=reset_ticks,raw_counter_after_reset=raw_counter_start,raw_counter_at_stop=actual_elapsed,raw_counter_limit=max_elapsed,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=actorcpu,wall_s=time.perf_counter()-start,capture_wall_s=capture_wall,policy_IPC_max_ms=max(policy_ms) if policy_ms else None,reaping=reaping,completed_within_default_CLI2000=bool(complete and steps<=2000))
    save(F/'result.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',required=True,type=Path);run(p.parse_args().private_root)
