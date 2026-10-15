"""One fresh frozen349 episode; exact historical340prefix within2000cap."""
import hashlib
import json
import random
import time
from pathlib import Path
import sys
import numpy as np
from retry.path271_run import read,save,sha
from retry.pedal331_run import plain,rng,physical
from retry.episode337_run import json_default,finish_record,compact
from retry.episode350_stage import verify
from retry.package349_run import cached,projection,rows
from retry.probe338_stage import stack


def charge(D,key):
    b=read(D/'native-budget.json')
    cap=dict(actions=min(b['total_cap'],b['episode_cap']),resets=b['reset_cap'],actor_act_calls=b['actor_act_cap'],actor_resets=1)[key]
    assert b[key]<cap;b[key]+=1;save(D/'native-budget.json',b)


def run(R):
    from retry.frozen_composite_runtime import prepare,validate_response
    from retry.diagnose import make_env
    from retry.full_route_reproduction import truth
    from retry.source_vehicle_transition import obstacle_contact_pair
    D=R/'stage350';p=verify(R,True);assert not (D/'episode-opening.json').exists();save(D/'episode-opening.json',dict(epoch=time.time(),runner_sha256=sha(Path(__file__))))
    F=D/'B';F.mkdir(mode=0o700);z=np.load(R/'stage340/B/frames-actions-private.npz');old=rows(R/'stage340/B/trace-private.jsonl');replay=cached(R/'stage349/candidate/records-private.jsonl');reset_ref=read(R/'stage349/candidate/reset-private.json');reference_rng=read(R/'stage335/B/first-divergence-private.json')['accessible_RNG']
    random.seed(p['observer_rng_seed']);np.random.seed(p['observer_rng_seed']);w=env=j=policy_j=None;frames=[];actions=[];events=[];steps=rawticks=reset_ticks=prefix=0;actorcpu=0.;error=None;ended=truncated=complete=False;info={};start_time=initial_counter=final_finish=None
    start,cpu=time.perf_counter(),time.process_time();capture_wall=reset_wall=raw_step_wall=raw_observer_wall=journal_wall=artifact_wall=0.;policy_ms=[];raw_records=[]
    def frame(obs):
        f=np.rint(obs[-1]*255).astype(np.uint8);assert np.array_equal(f.astype(np.float32)/255,obs[-1]);frames.append(f);assert np.array_equal(stack(np.asarray(frames),len(frames)-1),obs)
    try:
        w=prepare(p['config'],F/'cpu',p['sandbox_path']);save(F/'ready-private.json',w.ready);save(F/'configuration-ready.json',w.configuration_ready_receipt)
        env=make_env();charge(D,'resets');t=time.perf_counter();obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});reset_wall=time.perf_counter()-t;raw=env.unwrapped;reset_ticks=round(raw.t*50);start_time=float(raw.t);initial_counter=env.env._elapsed_steps
        assert initial_counter==50 and reset_ticks==51 and env.env._max_episode_steps==8200 and env._skip_frames==4
        assert hashlib.sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest()==p['case']['road_geometry_sha256'];initial=physical(env);initial_rng=rng(env);assert initial==read(R/'stage340/B/initial-scene-private.json') and initial_rng==reference_rng
        save(F/'initial-scene-private.json',initial);save(F/'initial-RNG-private.json',initial_rng)
        charge(D,'actor_resets');policy,_=w.call('reset',obs);validate_response(policy,p['config'],obs,'reset');assert policy['state']==reset_ref['state'];assert policy['packaged_support_state']==[] and policy['packaged_support_step']==0 and policy['support_record'] is None
        save(F/'reset-policy-private.json',policy);frame(obs);assert np.array_equal(obs,stack(z['frames_uint8'],0))
        save(D/'actual-reset-contract.json',dict(raw_limit=8200,elapsed_after_reset=50,frame_skip=4,underlying_postreset_action_cap=2038,registered_actual_episode_cap=2000,total_accounting_cap=2038,raw_reset_ticks=51,postreset_start_time=start_time,no_new_cached_actor_replay=True))
        original_step=raw.step
        def observed_step(*args,**kwargs):
            nonlocal raw_step_wall,raw_observer_wall
            t=time.perf_counter();out=original_step(*args,**kwargs);raw_step_wall+=time.perf_counter()-t;t=time.perf_counter()
            contacts=sorted(list(pair) for c in raw.world.contacts if c.touching and (pair:=obstacle_contact_pair(c,raw.car,raw.obstacles)) is not None)
            raw_records.append(dict(raw_time=float(raw.t),pairs=contacts,hit_objects=[i for i,o in enumerate(raw.obstacles) if o.userData.hit],collision=bool(out[4].get('collision',False)),position=list(raw.car.hull.position),speed_m_s=float(np.hypot(*raw.car.hull.linearVelocity)),unique_tiles=int(raw.tile_visited_count)))
            raw_observer_wall+=time.perf_counter()-t;return out
        raw.step=observed_step
        j=(F/'trace-private.jsonl').open('x');(F/'trace-private.jsonl').chmod(0o600);policy_j=(F/'policy-responses-private.jsonl').open('x');(F/'policy-responses-private.jsonl').chmod(0o600)
        for i in range(p['episode_cap']):
            verify(R);pre=plain(truth(env));t=time.perf_counter();full_before=physical(env);before=full_before if i<72 else compact(full_before);before_rng=rng(env);capture_wall+=time.perf_counter()-t;timer=env.env._elapsed_steps;matching=i<233
            if matching:
                assert np.array_equal(obs,stack(z['frames_uint8'],i)) and pre==old[i]['pre'] and before==old[i]['pre_physical'],('pre',i+1)
                assert before_rng==reference_rng,('live no-draw RNG invariant',i+1)
                expected=reset_ref['state'] if i==0 else replay[i-1]['commit']['state'];assert policy['state']==expected
                if i:assert projection(policy['state'])==projection(old[i-1]['policy'])
            charge(D,'actor_act_calls');r,ms=w.call('act',obs);policy_ms.append(ms);actorcpu=r['actor_cumulative_CPU_s'];policy_j.write(json.dumps(dict(step=i+1,response=r),allow_nan=False)+'\n');policy_j.flush()
            command=validate_response(r,p['config'],obs,'act');assert r['delta_audit']['action']==command.tolist();e=r['routing_evidence'];assert e['tracker_preserved'] and e['full_hazards']==r['tracker_record']['after'];assert r['features'][11]==len(e['full_hazards'])
            assert r['packaged_support_step']==i+1 and r['packaged_support_state']==r['support_record']['after'];assert e['removed_indices']==[j for j,x in enumerate(r['packaged_support_state']) if x['low']]
            if matching:
                for key,ref in [('action','returned_action'),('features','features'),('pixel_path','pixel_path'),('tracker_record','tracker'),('delta_audit','audit')]:assert r[key]==old[i][ref],(i+1,key)
                for key in ['state','support_record','routing_evidence']:assert r[key]==replay[i]['response'][key],(i+1,key)
            c,_=w.call('commit',command);policy=c;actorcpu=c['actor_cumulative_CPU_s'];assert not c['python_audit_denied_events'];assert c['memory']==c['nominal_memory']==r['state']['previous_steer'] and np.float32(c['memory'])==command[0] and c['history'][-1]==command.tolist()
            if matching:assert c['state']==replay[i]['commit']['state'] and projection(c['state'])==projection(old[i]['policy']) and c['memory']==old[i]['nominal_memory']
            charge(D,'actions');steps+=1;raw_records=[];t0=raw.t;obs,_,ended,truncated,info=env.step(command);ticks=round((raw.t-t0)*50);rawticks+=ticks;assert env.env._elapsed_steps-timer==ticks==len(raw_records);complete=raw.finish_time_s is not None;frame(obs);actions.append(command.copy());post=plain(truth(env));t=time.perf_counter();full_after=physical(env);after=full_after if i<72 else compact(full_after);after_rng=rng(env);capture_wall+=time.perf_counter()-t;final_finish=finish_record(raw)
            row=dict(step=i+1,executed=command.tolist(),returned_action=r['action'],features=r['features'],audit=r['delta_audit'],tracker=r['tracker_record'],support_record=r['support_record'],routing_evidence=e,pixel_path=r['pixel_path'],actor_state=r['state'],nominal_memory=c['memory'],policy=c['state'],pre=pre,post=post,pre_physical=before,post_physical=after,pre_RNG=before_rng,post_RNG=after_rng,raw_observations=raw_records,collision=bool(info['collision']),damage=float(env.damage.damage),terminated=bool(ended),truncated=bool(truncated),completed=complete,finish=final_finish,retire_reason=info.get('retire_reason'),elapsed_raw_counter=env.env._elapsed_steps,raw_ticks=ticks,info=plain(info))
            t=time.perf_counter();j.write(json.dumps(row,default=json_default,allow_nan=False)+'\n');j.flush();journal_wall+=time.perf_counter()-t;events.append(row)
            if matching:
                assert np.array_equal(obs,stack(z['frames_uint8'],i+1)) and post==old[i]['post'] and after==old[i]['post_physical'] and after_rng==reference_rng,(i+1,'post')
                for key in ['collision','damage','terminated','truncated','raw_ticks','elapsed_raw_counter']:assert row[key]==old[i][key],(i+1,key)
                prefix+=1
                if prefix==233:
                    save(D/'prefix233-qualification.json',dict(passed=True,actual_prefix_actions=233,matched_input_stacks=234,commands_pixels_tracker_features_path_audit_physics_exact=True,original_policy_projection_and_nominal_memory_exact=True,full_packaged349_replay_state_exact=True,actor_accessible_RNG_exact233=True,evaluator_accessible_RNG='Live constant reference validated by historical340through127; source no-draw invariant thereafter, not historical per-step snapshots.',hidden_solver_OpenCV_RNG_not_directly_captured=True,old340_reused_not_new=True))
                    print('350 actual prefix233 qualified; continuing own observations under2000cap.',flush=True)
            if ended or truncated:break
        verify(R,True)
    except BaseException as e:
        error=type(e).__name__+': '+str(e);save(F/'error-private.json',dict(error=error,traceback=__import__('traceback').format_exc(),charged_budget=read(D/'native-budget.json')))
    finally:
        if j:j.close()
        if policy_j:policy_j.close()
        elapsed=env.env._elapsed_steps if env else None;reaping=w.close() if w else None
        if env:env.close()
    if frames:
        t=time.perf_counter();f=F/'frames-actions-private.npz';np.savez_compressed(f,frames_uint8=np.asarray(frames,np.uint8),actions=np.asarray(actions,np.float32));f.chmod(0o600);artifact_wall+=time.perf_counter()-t
    result=dict(native_actions=steps,native_cap=2000,total_accounting_cap=2038,technical_error=error,terminated=bool(ended),truncated=bool(truncated),completed=bool(complete),actual_DNF=bool(ended and not complete),censored=bool(error or not complete and not ended),protocol_stop=bool(not error and not ended and not truncated and steps==2000),retire_reason=info.get('retire_reason'),finish=final_finish,postreset_start_time=start_time,stop_reason='technical_stop' if error else 'official_finish' if complete else 'actual_retirement' if ended else 'other_official_truncation' if truncated else 'default2000_protocol_cap',lap_ms=round((final_finish['finish_time_s']-start_time)*1000) if complete else None,first_contact=next((r['step'] for r in events if r['collision']),None),collision_actions=[r['step'] for r in events if r['collision']],damage=events[-1]['damage'] if events else None,unique_tiles=events[-1]['post']['unique_tiles'] if events else None,total_tiles=p['case']['road_point_count'],comparison_valid=bool(not error and prefix==233),prefix_actions_verified=prefix,raw_step_ticks=rawticks,raw_reset_ticks=reset_ticks,raw_counter_after_reset=initial_counter,raw_counter_at_stop=elapsed,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=actorcpu,reset_wall_s=reset_wall,raw_step_render_wall_s=raw_step_wall,raw_contact_observer_wall_s=raw_observer_wall,capture_wall_s=capture_wall,journal_wall_s=journal_wall,artifact_wall_s=artifact_wall,policy_IPC_max_ms=max(policy_ms) if policy_ms else None,reaping=reaping)
    save(F/'result.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]).resolve())
