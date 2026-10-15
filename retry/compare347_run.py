"""One new baseline, exact345Aprefix, paired with existing actual346B."""
import argparse
import hashlib
import json
import random
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save
from retry.pedal331_run import plain,rng,physical
from retry.episode337_run import json_default,finish_record,compact
from retry.probe338_stage import stack
from retry.compare347_stage import verify


def charge(D,arm,kind):
    b=read(D/'native-budget.json')
    if kind=='reset':assert b['resets']<b['reset_cap'];b['resets']+=1
    else:
        assert b['actions']<b['total_cap'] and b['arms'][arm]<300;b['actions']+=1;b['arms'][arm]+=1
    save(D/'native-budget.json',b)


def run_arm(R,arm):
    from retry.frozen_composite_runtime import prepare
    from retry.diagnose import make_env
    from retry.full_route_reproduction import truth
    from retry.source_vehicle_transition import obstacle_contact_pair
    D=R/'stage347';p=verify(R);F=D/arm;assert arm in p['order'] and not F.exists();F.mkdir(mode=0o700);save(F/'opening.json',dict(epoch=time.time()))
    assert arm=='A'
    old=[json.loads(s) for s in (R/'stage345/A/trace-private.jsonl').read_text().splitlines()];z=np.load(R/'stage345/A/frames-actions-private.npz')
    assert len(old)==160 and read(R/'stage345/A/result.json')['technical_error'] is None
    paired=[json.loads(t) for t in (R/'stage346/B/trace-private.jsonl').read_text().splitlines()];paired_frames=np.load(R/'stage346/B/frames-actions-private.npz')
    random.seed(p['observer_rng_seed']);np.random.seed(p['observer_rng_seed']);w=env=None;j=None;frames=[];actions=[];events=[];steps=rawticks=reset_ticks=0;actorcpu=0.;error=None;ended=truncated=complete=False;info={};policy=None;prefix=0;first_difference=None;raw_records=[];start_time=None;final_finish=None;initial_counter=None
    start,cpu=time.perf_counter(),time.process_time();capture_wall=reset_wall=raw_step_wall=raw_observer_wall=journal_wall=artifact_wall=0.;policy_ms=[]
    def frame(obs):
        f=np.rint(obs[-1]*255).astype(np.uint8);assert np.array_equal(f.astype(np.float32)/255,obs[-1]);frames.append(f);assert np.array_equal(stack(np.asarray(frames),len(frames)-1),obs)
    try:
        w=prepare(p['configs'][arm],F/'cpu',p['sandbox_path']);env=make_env();charge(D,arm,'reset');tick=time.perf_counter();obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});reset_wall=time.perf_counter()-tick;raw=env.unwrapped;reset_ticks=round(raw.t*50);start_time=float(raw.t);initial_counter=env.env._elapsed_steps
        assert initial_counter==50 and reset_ticks==51 and env.env._max_episode_steps==8200 and env._skip_frames==4
        assert hashlib.sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest()==p['case']['road_geometry_sha256'];initial=physical(env);initial_rng=rng(env);save(F/'initial-scene-private.json',initial);save(F/'initial-RNG-private.json',initial_rng)
        policy,_=w.call('reset',obs);save(F/'reset-policy-private.json',policy);frame(obs)
        if arm=='A':assert initial==read(R/'stage345/A/initial-scene-private.json') and initial_rng==read(R/'stage345/A/initial-RNG-private.json') and policy['state']==read(R/'stage345/A/reset-policy-private.json')['state'] and np.array_equal(frames[0],z['frames_uint8'][0])
        assert initial==read(R/'stage346/B/initial-scene-private.json') and initial_rng==read(R/'stage346/B/initial-RNG-private.json') and policy['state']==read(R/'stage346/B/reset-policy-private.json')['state'] and np.array_equal(frames[0],paired_frames['frames_uint8'][0])
        original_raw_step=raw.step
        def observed_raw_step(*args,**kwargs):
            nonlocal raw_step_wall,raw_observer_wall
            tick=time.perf_counter();out=original_raw_step(*args,**kwargs);raw_step_wall+=time.perf_counter()-tick;tick=time.perf_counter()
            contacts=sorted(list(pair) for c in raw.world.contacts if c.touching and (pair:=obstacle_contact_pair(c,raw.car,raw.obstacles)) is not None)
            raw_records.append(dict(raw_time=float(raw.t),pairs=contacts,hit_objects=[i for i,o in enumerate(raw.obstacles) if o.userData.hit],collision=bool(out[4].get('collision',False)),position=list(raw.car.hull.position),speed_m_s=float(np.hypot(*raw.car.hull.linearVelocity)),unique_tiles=int(raw.tile_visited_count)))
            raw_observer_wall+=time.perf_counter()-tick;return out
        raw.step=observed_raw_step
        j=(F/'trace-private.jsonl').open('x');(F/'trace-private.jsonl').chmod(0o600)
        for i in range(p['per_arm_cap']):
            verify(R);pre=plain(truth(env));tick=time.perf_counter();before=compact(physical(env));before_rng=rng(env);capture_wall+=time.perf_counter()-tick;timer=env.env._elapsed_steps;prior_state=policy['state'];matching=i<160
            if matching:
                assert i<len(old) and np.array_equal(obs,stack(z['frames_uint8'],i));assert pre==old[i]['pre'] and before==old[i]['pre_physical'] and before_rng==old[i]['pre_RNG'];expected=read(R/'stage345/A/reset-policy-private.json')['state'] if i==0 else old[i-1]['policy'];assert prior_state==expected
            if i<=145:
                assert np.array_equal(obs,stack(paired_frames['frames_uint8'],i)) and pre==paired[i]['pre'] and before==paired[i]['pre_physical'] and before_rng==paired[i]['pre_RNG']
                expected_pair=read(R/'stage346/B/reset-policy-private.json')['state'] if i==0 else paired[i-1]['policy'];assert prior_state==expected_pair
            r,ms=w.call('act',obs);policy_ms.append(ms);assert not r['python_audit_denied_events'];command=np.asarray(r['action'],np.float32);assert r['delta_audit'] is None and r['final_action_audit']['after']==command.tolist();evidence=r['routing_evidence'];assert evidence['tracker_preserved'] and evidence['full_hazards']==r['tracker_record']['after'];assert r['features'][11]==len(evidence['full_hazards'])
            if matching:
                assert r['action']==old[i]['returned_action'] and r['features']==old[i]['features'] and r['tracker_record']==old[i]['tracker'] and r['support_record']==old[i]['support_record'] and r['routing_evidence']==old[i]['routing_evidence']
                assert r['pixel_path']==old[i]['pixel_path'] and r['state']==old[i]['actor_state'] and r['delta_audit']==old[i]['audit']
            if i<145:
                assert r['action']==paired[i]['returned_action'] and r['features']==paired[i]['features'] and r['state']==paired[i]['actor_state'] and r['tracker_record']==paired[i]['tracker'] and r['support_record']==paired[i]['support_record'] and r['pixel_path']==paired[i]['pixel_path']
            if i==145:
                assert r['action']!=paired[i]['returned_action'] and r['tracker_record']==paired[i]['tracker'] and r['support_record']==paired[i]['support_record']
                save(D/'paired-prefix-qualification.json',dict(passed=True,existing_B_stage=346,new_A_only=True,common_prefix_actions=145,common_input_stacks=146,environment_rng_code_initialization_actor_tracker_physics_exact=True,first_natural_full_control_difference=146,no_existingB_charged_again=True))
            c,_=w.call('commit',command);policy=c;actorcpu=c['actor_cumulative_CPU_s'];assert c['memory']==c['nominal_memory']==r['state']['previous_steer'] and np.float32(c['memory'])==command[0] and c['history'][-1]==command.tolist()
            if matching:assert c['state']==old[i]['policy']
            charge(D,arm,'act');steps+=1;raw_records=[];t0=raw.t;obs,_,ended,truncated,info=env.step(command);ticks=round((raw.t-t0)*50);rawticks+=ticks;assert env.env._elapsed_steps-timer==ticks==len(raw_records);complete=raw.finish_time_s is not None;frame(obs);actions.append(command.copy());post=plain(truth(env));tick=time.perf_counter();after=compact(physical(env));after_rng=rng(env);capture_wall+=time.perf_counter()-tick;final_finish=finish_record(raw)
            row=dict(step=i+1,executed=command.tolist(),returned_action=r['action'],features=r['features'],audit=r['delta_audit'],tracker=r['tracker_record'],support_record=r['support_record'],routing_evidence=evidence,pixel_path=r['pixel_path'],actor_state=r['state'],nominal_memory=c['memory'],policy=c['state'],pre=pre,post=post,pre_physical=before,post_physical=after,pre_RNG=before_rng,post_RNG=after_rng,raw_observations=raw_records,collision=bool(info['collision']),damage=float(env.damage.damage),terminated=bool(ended),truncated=bool(truncated),completed=complete,finish=final_finish,retire_reason=info.get('retire_reason'),elapsed_raw_counter=env.env._elapsed_steps,raw_ticks=ticks,info=plain(info))
            if matching:
                assert np.array_equal(obs,stack(z['frames_uint8'],i+1)) and post==old[i]['post'] and after==old[i]['post_physical'] and after_rng==old[i]['post_RNG'] and raw_records==old[i]['raw_observations'];assert row['collision']==old[i]['collision'] and row['damage']==old[i]['damage'] and row['terminated']==old[i]['terminated'] and row['truncated']==old[i]['truncated'];prefix+=1
                if prefix==160:save(D/'prefix160-qualification.json',dict(passed=True,actual_actions=160,input_stacks=161,commands_observations_actor_tracker_physics_accessRNG_exact=True,normal_candidate_memory=True,no_post160_stored_control=True))
            tick=time.perf_counter();j.write(json.dumps(row,default=json_default,allow_nan=False)+'\n');j.flush();journal_wall+=time.perf_counter()-tick;events.append(row)
            if ended or truncated:break
        verify(R)
    except BaseException as e:
        error=type(e).__name__+': '+str(e);save(F/'error-private.json',dict(error=error,traceback=__import__('traceback').format_exc()))
    finally:
        if j:j.close()
        elapsed=env.env._elapsed_steps if env else None;reaping=w.close() if w else None
        if env:env.close()
    if frames:
        tick=time.perf_counter();f=F/'frames-actions-private.npz';np.savez_compressed(f,frames_uint8=np.asarray(frames,np.uint8),actions=np.asarray(actions,np.float32));f.chmod(0o600);artifact_wall+=time.perf_counter()-tick
    result=dict(arm=arm,native_actions=steps,native_cap=300,technical_error=error,terminated=bool(ended),truncated=bool(truncated),completed=bool(complete),actual_DNF=bool(ended and not complete),censored=bool(error or not complete and not ended),protocol_stop=bool(not error and not ended and not truncated and steps==300),retire_reason=info.get('retire_reason'),finish=final_finish,postreset_start_time=start_time,stop_reason='official_finish' if complete else 'actual_retirement' if ended else 'technical_stop' if error else 'other_truncation' if truncated else 'protocol_cap',lap_ms=round((final_finish['finish_time_s']-start_time)*1000) if complete else None,first_contact=next((r['step'] for r in events if r['collision']),None),collision_actions=[r['step'] for r in events if r['collision']],damage=events[-1]['damage'] if events else None,unique_tiles=events[-1]['post']['unique_tiles'] if events else None,total_tiles=p['case']['road_point_count'],comparison_valid=bool(not error and prefix==160),prefix_actions_verified=prefix,raw_step_ticks=rawticks,raw_reset_ticks=reset_ticks,raw_counter_after_reset=initial_counter,raw_counter_at_stop=elapsed,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=actorcpu,reset_wall_s=reset_wall,raw_step_render_wall_s=raw_step_wall,raw_contact_observer_wall_s=raw_observer_wall,capture_wall_s=capture_wall,journal_wall_s=journal_wall,artifact_wall_s=artifact_wall,policy_IPC_max_ms=max(policy_ms) if policy_ms else None,reaping=reaping)
    save(F/'result.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('arm',choices=['A']);a.add_argument('--private-root',required=True,type=Path);args=a.parse_args();run_arm(args.private_root,args.arm)
