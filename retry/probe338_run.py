"""One executed steering intervention; original tracker and nominal memory kept."""
import argparse
import json
import random
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.pedal331_run import plain,rng,physical
from retry.episode337_run import json_default,finish_record,compact
from retry.probe338_stage import verify,stack


def run(R):
    from retry.frozen_composite_runtime import prepare
    from retry.diagnose import make_env
    from retry.full_route_reproduction import truth
    D=R/'stage338';p=verify(R,True);assert read(D/'cache-receipt.json')['passed'];assert not (D/'episode-opening.json').exists();save(D/'episode-opening.json',dict(epoch=time.time(),runner_sha256=sha(Path(__file__))))
    F=D/'B';F.mkdir(mode=0o700);z=np.load(R/'stage337/B/frames-actions-private.npz');old=[json.loads(s) for s in (R/'stage337/B/trace-private.jsonl').read_text().splitlines()];cached=read(D/'cache/records-private.json');expected_probe=read(D/'cache/probes-private.json')[-1]['probe'];reference_rng=read(R/'stage335/B/first-divergence-private.json')['accessible_RNG']
    random.seed(p['observer_rng_seed']);np.random.seed(p['observer_rng_seed']);w=env=None;frames=[];actions=[];events=[];steps=rawticks=reset_ticks=0;actorcpu=0.;error=None;ended=truncated=complete=False;info={};prefix_verified=0;probe=None;start_time=None;final_finish=None;start,cpu=time.perf_counter(),time.process_time();capture_wall=0.;policy_ms=[];initial_counter=None
    def record_frame(obs):
        frame=np.rint(obs[-1]*255).astype(np.uint8);assert np.array_equal(frame.astype(np.float32)/255,obs[-1]);frames.append(frame);assert np.array_equal(stack(np.array(frames),len(frames)-1),obs)
    try:
        w=prepare(p['config'],F/'cpu',p['sandbox_path']);env=make_env();obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});raw=env.unwrapped;reset_ticks=round(raw.t*50);start_time=float(raw.t);initial_counter=env.env._elapsed_steps;assert initial_counter==50 and env.env._max_episode_steps==8200 and env._skip_frames==4
        assert np.array_equal(obs,stack(z['frames_uint8'],0));assert __import__('hashlib').sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest()==p['case']['road_geometry_sha256'];assert physical(env)==read(R/'stage337/B/initial-scene-private.json');policy,_=w.call('reset',obs);assert policy['state']==read(D/'cache/reset-private.json')['state'];record_frame(obs)
        journal=(F/'trace-private.jsonl').open('x');(F/'trace-private.jsonl').chmod(0o600)
        try:
            for i in range(p['cap']):
                verify(R);pre=plain(truth(env));tick=time.perf_counter();before=physical(env);capture_wall+=time.perf_counter()-tick;timer_before=env.env._elapsed_steps
                if i<=127:
                    assert np.array_equal(obs,stack(z['frames_uint8'],i));assert pre==old[i]['pre'];assert (before if i<72 else compact(before))==old[i]['pre_physical'];assert rng(env)==reference_rng
                    previous=read(D/'cache/reset-private.json')['state'] if i==0 else cached[i-1]['commit']['state'];assert policy['state']==previous
                r,ms=w.call('act',obs);policy_ms.append(ms);assert not r['python_audit_denied_events'];original=np.asarray(r['action'],np.float32);command=original.copy();assert r['delta_audit']['action']==original.tolist()
                if i<=127:assert r['action']==old[i]['returned_action'] and r['features']==old[i]['features'] and r['state']==cached[i]['response']['state'] and r['tracker_record']==old[i]['tracker'] and r['delta_audit']==old[i]['audit']
                if i==127:
                    assert prefix_verified==127;probe,_=w.call('direct_probe',obs);assert probe['state_preserved'] and probe['tracker_unchanged'] and probe['state']==r['state'];assert probe['variants']==expected_probe['variants'];assert np.float32(probe['variants']['original']['steering'])==original[0];command[0]=np.float32(probe['variants']['direct']['steering']);assert command[0]!=original[0]
                    save(D/'preprobe127-qualification.json',dict(passed=True,prefix_actions=127,input_stacks=128,actor_tracker_memory_physics_accessible_RNG_exact=True,original128dtype_output_exact=True,probe_tracker_state_preserved=True))
                assert np.array_equal(command[1:],original[1:]);assert i==127 or np.array_equal(command,original)
                c,_=w.call('commit',command);policy=c;actorcpu=c['actor_cumulative_CPU_s'];assert c['memory']==c['nominal_memory']==r['state']['previous_steer'] and c['history'][-1]==command.tolist();assert np.float32(c['memory'])==original[0]
                if i<127:assert c['state']==old[i]['policy'] and c['memory']==old[i]['nominal_memory']
                if i==127:assert c['memory']==old[i]['nominal_memory']
                budget=read(D/'native-budget.json');assert budget['actions']<budget['cap'];budget['actions']+=1;save(D/'native-budget.json',budget);steps+=1
                t=raw.t;obs,_,ended,truncated,info=env.step(command);ticks=round((raw.t-t)*50);rawticks+=ticks;assert env.env._elapsed_steps-timer_before==ticks;complete=raw.finish_time_s is not None;record_frame(obs);actions.append(command.copy());post=plain(truth(env));tick=time.perf_counter();after=physical(env);capture_wall+=time.perf_counter()-tick;final_finish=finish_record(raw)
                row=dict(step=i+1,executed=command.tolist(),returned_action=r['action'],probe=probe if i==127 else None,features=r['features'],audit=r['delta_audit'],tracker=r['tracker_record'],pixel_path=r['pixel_path'],nominal_memory=c['memory'],policy=c['state'],pre=pre,post=post,pre_physical=before if i<72 else compact(before),post_physical=after if i<72 else compact(after),collision=bool(info['collision']),damage=float(env.damage.damage),damage_increase=float(env.damage.damage)-pre['damage'],terminated=bool(ended),truncated=bool(truncated),completed=complete,finish=final_finish,retire_reason=info.get('retire_reason'),elapsed_raw_counter=env.env._elapsed_steps,raw_ticks=ticks,contact_interval_s=[t,float(raw.t)] if info['collision'] else None,info=plain(info))
                if i<127:
                    assert np.array_equal(obs,stack(z['frames_uint8'],i+1)) and post==old[i]['post'] and row['post_physical']==old[i]['post_physical'];assert row['collision']==old[i]['collision'] and row['damage']==old[i]['damage'] and bool(ended or truncated)==bool(old[i]['terminated'] or old[i]['truncated']);prefix_verified+=1
                journal.write(json.dumps(row,default=json_default,allow_nan=False)+'\n');journal.flush();events.append(row)
                if ended or truncated:break
        finally:journal.close()
        verify(R,True)
    except BaseException as e:
        error=type(e).__name__+': '+str(e);save(F/'error-private.json',dict(error=error,traceback=__import__('traceback').format_exc()))
    finally:
        elapsed=env.env._elapsed_steps if env else None
        if w:reaping=w.close()
        else:reaping=None
        if env:env.close()
    if frames:
        f=F/'frames-actions-private.npz';np.savez_compressed(f,frames_uint8=np.array(frames,np.uint8),actions=np.array(actions,np.float32));f.chmod(0o600)
    if probe:save(F/'probe-private.json',probe)
    result=dict(native_actions=steps,native_cap=233,prefix127_verified=prefix_verified,comparison_valid=bool(not error and probe is not None),technical_error=error,terminated=bool(ended),truncated=bool(truncated),completed=bool(complete),actual_DNF=bool(ended and not complete),censored=bool(error or (not ended and not truncated)),protocol_stop=bool(not error and not ended and not truncated and steps==233),retire_reason=info.get('retire_reason'),finish=final_finish,postreset_start_time=start_time,lap_ms=round((final_finish['finish_time_s']-start_time)*1000) if complete else None,first_contact=next((r['step'] for r in events if r['collision']),None),contact_actions=[r['step'] for r in events if r['collision']],damage=events[-1]['damage'] if events else None,unique_tiles=events[-1]['post']['unique_tiles'] if events else None,total_tiles=p['case']['road_point_count'],raw_step_ticks=rawticks,raw_reset_ticks=reset_ticks,raw_counter_after_reset=initial_counter,raw_counter_at_stop=elapsed,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=actorcpu,wall_s=time.perf_counter()-start,capture_wall_s=capture_wall,policy_IPC_max_ms=max(policy_ms) if policy_ms else None,reaping=reaping)
    save(F/'result.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',required=True,type=Path);run(p.parse_args().private_root)
