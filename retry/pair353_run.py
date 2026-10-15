"""Two fresh closed loops with natural common-prefix qualification."""
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
from retry.pair353_stage import verify
from retry.package349_run import rows,projection
from retry.probe338_stage import stack


def charge(D,arm,key):
    b=read(D/'native-budget.json')
    if key in ['resets','actor_resets']:assert b[key]<2;b[key]+=1
    else:
        field='arms' if key=='actions' else 'actor_arms';assert b[key]<800 and b[field][arm]<400;b[key]+=1;b[field][arm]+=1
    save(D/'native-budget.json',b)


def run_arm(R,arm):
    from retry.frozen_composite_runtime import prepare,validate_response
    from retry.diagnose import make_env
    from retry.full_route_reproduction import truth
    from retry.source_vehicle_transition import obstacle_contact_pair
    D=R/'stage353';p=verify(R,True);F=D/arm;assert not F.exists();F.mkdir(mode=0o700);save(F/'opening.json',dict(epoch=time.time(),runner_sha256=sha(Path(__file__))))
    historical=rows(R/f'stage343/{arm}/trace-private.jsonl');hz=np.load(R/f'stage343/{arm}/frames-actions-private.npz');prefix160=0
    paired=pairz=None
    if arm=='B':
        ar=read(D/'A/result.json');assert ar['technical_error'] is None;paired=rows(D/'A/trace-private.jsonl');pairz=np.load(D/'A/frames-actions-private.npz')
    random.seed(p['observer_rng_seed']);np.random.seed(p['observer_rng_seed']);w=env=j=pj=None;frames=[];actions=[];events=[];steps=rawticks=reset_ticks=0;actorcpu=0.;error=None;ended=truncated=complete=False;info={};start_time=initial_counter=final_finish=None
    common=True;common_actions=0;common_input_stacks=0;first_branch=None;first_branch_fields=[];first_control=None
    start,cpu=time.perf_counter(),time.process_time();capture_wall=reset_wall=raw_step_wall=raw_observer_wall=journal_wall=artifact_wall=0.;policy_ms=[];raw_records=[]
    def frame(obs):
        f=np.rint(obs[-1]*255).astype(np.uint8);assert np.array_equal(f.astype(np.float32)/255,obs[-1]);frames.append(f);assert np.array_equal(stack(np.asarray(frames),len(frames)-1),obs)
    try:
        w=prepare(p['configs'][arm],F/'cpu',p['sandbox_path']);save(F/'ready-private.json',w.ready);save(F/'configuration-ready.json',w.configuration_ready_receipt)
        env=make_env();charge(D,arm,'resets');t=time.perf_counter();obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});reset_wall=time.perf_counter()-t;raw=env.unwrapped;reset_ticks=round(raw.t*50);start_time=float(raw.t);initial_counter=env.env._elapsed_steps
        assert initial_counter==50 and reset_ticks==51 and env.env._max_episode_steps==8200 and env._skip_frames==4
        assert hashlib.sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest()==p['case']['road_geometry_sha256'];initial=physical(env);initial_rng=rng(env);save(F/'initial-scene-private.json',initial);save(F/'initial-RNG-private.json',initial_rng)
        charge(D,arm,'actor_resets');policy,_=w.call('reset',obs);validate_response(policy,p['configs'][arm],obs,'reset');save(F/'reset-policy-private.json',policy);frame(obs)
        assert initial==read(R/f'stage343/{arm}/initial-scene-private.json') and initial_rng==read(R/f'stage343/{arm}/initial-RNG-private.json') and projection(policy['state'])==projection(read(R/f'stage343/{arm}/reset-policy-private.json')['state']) and np.array_equal(obs,stack(hz['frames_uint8'],0))
        source=np.load(R/'stage306/collection/O2/observations-actions-private.npz')['observations'];assert np.array_equal(obs,source[0]);del source
        if arm=='B':
            assert initial==read(D/'A/initial-scene-private.json') and initial_rng==read(D/'A/initial-RNG-private.json') and projection(policy['state'])==projection(read(D/'A/reset-policy-private.json')['state']) and np.array_equal(obs,stack(pairz['frames_uint8'],0))
            assert policy['packaged_support_state']==[] and policy['packaged_support_step']==0 and policy['support_record'] is None
            save(D/'paired-reset-qualification.json',dict(passed=True,independent_resets=2,initial_pixels_fullphysics_accessRNG_originalpolicystateprojection_exact=True,fullpickle_excluded_expected_metadata_addition=True))
        original_step=raw.step
        def observed_step(*args,**kwargs):
            nonlocal raw_step_wall,raw_observer_wall
            t=time.perf_counter();out=original_step(*args,**kwargs);raw_step_wall+=time.perf_counter()-t;t=time.perf_counter()
            contacts=sorted(list(pair) for c in raw.world.contacts if c.touching and (pair:=obstacle_contact_pair(c,raw.car,raw.obstacles)) is not None)
            raw_records.append(dict(raw_time=float(raw.t),pairs=contacts,hit_objects=[i for i,o in enumerate(raw.obstacles) if o.userData.hit],collision=bool(out[4].get('collision',False)),position=list(raw.car.hull.position),speed_m_s=float(np.hypot(*raw.car.hull.linearVelocity)),unique_tiles=int(raw.tile_visited_count)))
            raw_observer_wall+=time.perf_counter()-t;return out
        raw.step=observed_step;j=(F/'trace-private.jsonl').open('x');(F/'trace-private.jsonl').chmod(0o600);pj=(F/'policy-responses-private.jsonl').open('x');(F/'policy-responses-private.jsonl').chmod(0o600)
        for i in range(400):
            verify(R);pre=plain(truth(env));t=time.perf_counter();before=compact(physical(env));before_rng=rng(env);capture_wall+=time.perf_counter()-t;timer=env.env._elapsed_steps;checking=arm=='B' and common
            if i<160:
                h=historical[i];expected_h=read(R/f'stage343/{arm}/reset-policy-private.json')['state'] if i==0 else historical[i-1]['policy']
                assert np.array_equal(obs,stack(hz['frames_uint8'],i)) and pre==h['pre'] and before==h['pre_physical'] and before_rng==h['pre_RNG'] and projection(policy['state'])==projection(expected_h),(arm,i+1,'historicalpre')
            if checking:
                assert i<len(paired),'commonprefix exceeded prior A withoutsame terminal'
                ref=paired[i];expected=read(D/'A/reset-policy-private.json')['state'] if i==0 else paired[i-1]['policy']
                assert np.array_equal(obs,stack(pairz['frames_uint8'],i)) and pre==ref['pre'] and before==ref['pre_physical'] and before_rng==ref['pre_RNG'] and projection(policy['state'])==projection(expected),(i+1,'commonpre')
                common_input_stacks=i+1
            charge(D,arm,'actor_act_calls');r,ms=w.call('act',obs);actorcpu=r['actor_cumulative_CPU_s'];policy_ms.append(ms);pj.write(json.dumps(dict(step=i+1,response=r),allow_nan=False)+'\n');pj.flush();command=validate_response(r,p['configs'][arm],obs,'act')
            assert r['delta_audit']['action']==command.tolist();e=r['routing_evidence'];assert e['tracker_preserved'] and e['full_hazards']==r['tracker_record']['after'] and r['features'][11]==len(e['full_hazards'])
            if arm=='A':assert not e['removed_indices'] and r['packaged_support_state'] is None
            else:assert r['packaged_support_step']==i+1 and r['packaged_support_state']==r['support_record']['after'] and e['removed_indices']==[j for j,x in enumerate(r['packaged_support_state']) if x['low']]
            c,_=w.call('commit',command);policy=c;actorcpu=c['actor_cumulative_CPU_s'];assert not c['python_audit_denied_events'] and c['memory']==c['nominal_memory']==r['state']['previous_steer'] and np.float32(c['memory'])==command[0] and c['history'][-1]==command.tolist()
            if i<160:
                for key,refkey in [('action','returned_action'),('features','features'),('pixel_path','pixel_path'),('tracker_record','tracker'),('delta_audit','audit')]:assert r[key]==h[refkey],(arm,i+1,key)
                assert projection(r['state'])==projection(h['actor_state']) and projection(c['state'])==projection(h['policy']) and c['memory']==h['nominal_memory']
                for key in ['full_hazards','routing_hazards','removed_indices','removed_evidence']:assert e[key]==h['routing_evidence'][key],(arm,i+1,key)
                if arm=='B':assert r['support_record']==h['support_record']
            same_command=False
            if checking:
                assert r['tracker_record']==ref['tracker']
                for key in ['RNG_python_sha256','RNG_numpy_sha256','cv2_seed_calls']:assert r['state'][key]==ref['actor_state'][key]
                same_command=r['action']==ref['returned_action'];fields=[]
                for key,rkey in [('action','returned_action'),('features','features'),('pixel_path','pixel_path')]:
                    if r[key]!=ref[rkey]:fields.append(key)
                if projection(c['state'])!=projection(ref['policy']):fields.append('original_policy_state_projection')
                if fields:
                    assert e['removed_indices'],'firstsemanticbranch without activefixedrule'
                    common=False;first_branch=i+1;first_branch_fields=fields
                else:common_actions+=1
            if arm=='B' and i<len(paired) and first_control is None and r['action']!=paired[i]['returned_action']:first_control=i+1
            charge(D,arm,'actions');steps+=1;raw_records=[];t0=raw.t;obs,_,ended,truncated,info=env.step(command);ticks=round((raw.t-t0)*50);rawticks+=ticks;assert env.env._elapsed_steps-timer==ticks==len(raw_records);complete=raw.finish_time_s is not None;frame(obs);actions.append(command.copy());post=plain(truth(env));t=time.perf_counter();after=compact(physical(env));after_rng=rng(env);capture_wall+=time.perf_counter()-t;final_finish=finish_record(raw)
            row=dict(step=i+1,executed=command.tolist(),returned_action=r['action'],features=r['features'],audit=r['delta_audit'],tracker=r['tracker_record'],support_record=r['support_record'],routing_evidence=e,pixel_path=r['pixel_path'],actor_state=r['state'],nominal_memory=c['memory'],policy=c['state'],pre=pre,post=post,pre_physical=before,post_physical=after,pre_RNG=before_rng,post_RNG=after_rng,raw_observations=raw_records,collision=bool(info['collision']),damage=float(env.damage.damage),terminated=bool(ended),truncated=bool(truncated),completed=complete,finish=final_finish,retire_reason=info.get('retire_reason'),elapsed_raw_counter=env.env._elapsed_steps,raw_ticks=ticks,info=plain(info))
            t=time.perf_counter();j.write(json.dumps(row,default=json_default,allow_nan=False)+'\n');j.flush();journal_wall+=time.perf_counter()-t;events.append(row)
            if i<160:
                assert np.array_equal(obs,stack(hz['frames_uint8'],i+1)) and post==h['post'] and after==h['post_physical'] and after_rng==h['post_RNG'] and raw_records==h['raw_observations'],(arm,i+1,'historicalpost')
                for key in ['collision','damage','terminated','truncated','raw_ticks']:assert row[key]==h[key],(arm,i+1,key)
                prefix160+=1
                if prefix160==160:
                    save(F/'historical343-prefix160-qualified.json',dict(passed=True,actual_actions=160,input_stacks=161,commands_pixels_originalstateprojection_physics_accessRNG_rawticks_exact=True,old343_not_new_or_recounted=True))
                    print('353 '+arm+' historical343prefix160qualified; continuing ownclosedloop.',flush=True)
            if checking and same_command:
                assert np.array_equal(obs,stack(pairz['frames_uint8'],i+1)) and post==ref['post'] and after==ref['post_physical'] and after_rng==ref['post_RNG'] and raw_records==ref['raw_observations'],(i+1,'commonpost')
                for key in ['collision','damage','terminated','truncated','raw_ticks']:assert row[key]==ref[key],(i+1,key)
                if common:common_input_stacks=i+2
            if ended or truncated:break
        verify(R,True)
        if arm=='B':save(D/'natural-prefix-qualification.json',dict(passed=True,common_actual_actions=common_actions,common_input_stacks=common_input_stacks,first_semantic_branch_action=first_branch,first_semantic_branch_fields=first_branch_fields,first_full_control_difference=first_control,no_semantic_branch=first_branch is None,natural_unforced=True,original_state_projection_physics_accessRNG_rawticks_verified=True,full_agent_pickle_excluded_for_expected_metadata=True))
    except BaseException as e:
        error=type(e).__name__+': '+str(e);save(F/'error-private.json',dict(error=error,traceback=__import__('traceback').format_exc(),budget=read(D/'native-budget.json')))
    finally:
        if j:j.close()
        if pj:pj.close()
        elapsed=env.env._elapsed_steps if env else None;reaping=w.close() if w else None
        if env:env.close()
    if frames:
        t=time.perf_counter();f=F/'frames-actions-private.npz';np.savez_compressed(f,frames_uint8=np.asarray(frames,np.uint8),actions=np.asarray(actions,np.float32));f.chmod(0o600);artifact_wall+=time.perf_counter()-t
    result=dict(arm=arm,native_actions=steps,native_cap=400,technical_error=error,historical343_prefix_actions_verified=prefix160,terminated=bool(ended),truncated=bool(truncated),completed=bool(complete),actual_DNF=bool(ended and not complete),censored=bool(error or not complete and not ended),protocol_stop=bool(not error and not ended and not truncated and steps==400),retire_reason=info.get('retire_reason'),finish=final_finish,postreset_start_time=start_time,stop_reason='technical_stop' if error else 'official_finish' if complete else 'actual_retirement' if ended else 'other_official_truncation' if truncated else 'protocol400_cap',lap_ms=round((final_finish['finish_time_s']-start_time)*1000) if complete else None,first_contact=next((r['step'] for r in events if r['collision']),None),collision_actions=[r['step'] for r in events if r['collision']],damage=events[-1]['damage'] if events else None,unique_tiles=events[-1]['post']['unique_tiles'] if events else None,total_tiles=p['case']['road_point_count'],raw_step_ticks=rawticks,raw_reset_ticks=reset_ticks,raw_counter_after_reset=initial_counter,raw_counter_at_stop=elapsed,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=actorcpu,reset_wall_s=reset_wall,raw_step_render_wall_s=raw_step_wall,raw_contact_observer_wall_s=raw_observer_wall,capture_wall_s=capture_wall,journal_wall_s=journal_wall,artifact_wall_s=artifact_wall,policy_IPC_max_ms=max(policy_ms) if policy_ms else None,reaping=reaping)
    save(F/'result.json',result);print(json.dumps(result),flush=True)
    return result


def run(R):
    a=run_arm(R,'A')
    if a['technical_error'] is None:run_arm(R,'B')
    else:print('353 Atechnicalstop; noB orautomaticretry.',flush=True)


if __name__=='__main__':run(Path(sys.argv[1]).resolve())
