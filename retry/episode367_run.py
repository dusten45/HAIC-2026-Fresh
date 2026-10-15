"""One new365closedloop; compare natural outputs with historical359T29510only."""
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
from retry.episode367_stage import verify,legacy_support
from retry.package349_run import projection
from retry.probe338_stage import stack


def rows(path):return [json.loads(s) for s in Path(path).read_text().splitlines()]


def charge(D,key):
    b=read(D/'native-budget.json');cap=b['reset_cap'] if key in ['resets','actor_resets'] else b['total_cap'];assert b[key]<cap;b[key]+=1;save(D/'native-budget.json',b)


def run(R):
    from retry.frozen_composite_runtime import prepare,validate_response
    from retry.diagnose import make_env
    from retry.full_route_reproduction import truth
    from retry.source_vehicle_transition import obstacle_contact_pair
    D=R/'stage367';p=verify(R,True);assert not (D/'episode-opening.json').exists();save(D/'episode-opening.json',dict(epoch=time.time(),runner_sha256=sha(Path(__file__))))
    F=D/'B';F.mkdir(mode=0o700);old=rows(R/'stage359/B/trace-private.jsonl');z=np.load(R/'stage359/B/frames-actions-private.npz');old_reset=read(R/'stage359/B/reset-policy-private.json');old_ready=read(R/'stage359/B/ready-private.json')
    random.seed(p['observer_rng_seed']);np.random.seed(p['observer_rng_seed']);w=env=j=pj=None;frames=[];actions=[];events=[];steps=rawticks=reset_ticks=0;actorcpu=0.;error=None;ended=truncated=complete=False;info={};start_time=initial_counter=final_finish=None;reset_qualified=False
    common=True;common_actions=common_commands=common_inputs=0;first_branch=first_action=first_routing=None;branch_fields=[];start,cpu=time.perf_counter(),time.process_time();capture_wall=reset_wall=raw_step_wall=raw_observer_wall=journal_wall=artifact_wall=0.;policy_ms=[];raw_records=[]
    def frame(obs):
        f=np.rint(obs[-1]*255).astype(np.uint8);assert np.array_equal(f.astype(np.float32)/255,obs[-1]);frames.append(f);assert np.array_equal(stack(np.asarray(frames),len(frames)-1),obs)
    try:
        w=prepare(p['config'],F/'cpu',p['sandbox_path']);save(F/'ready-private.json',w.ready);save(F/'configuration-ready.json',w.configuration_ready_receipt)
        for key in ['python_version','numpy_version','opencv_version']:assert w.ready[key]==old_ready[key],key
        env=make_env();charge(D,'resets');t=time.perf_counter();obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});reset_wall=time.perf_counter()-t;raw=env.unwrapped;reset_ticks=round(raw.t*50);start_time=float(raw.t);initial_counter=env.env._elapsed_steps
        assert initial_counter==50 and reset_ticks==51 and env.env._max_episode_steps==8200 and env._skip_frames==4
        geometry=hashlib.sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest();obstacles=hashlib.sha256(np.asarray([[*map(float,o.position),float(o.fixtures[0].shape.radius)] for o in raw.obstacles],dtype='<f8').tobytes()).hexdigest();obs_hash=hashlib.sha256(obs.tobytes()).hexdigest()
        assert geometry==p['case']['road_geometry_sha256'] and obstacles==p['case']['expected_physical_obstacles_sha256'] and obs_hash==p['expected_initial_observation_sha256']
        initial=physical(env);initial_rng=rng(env);save(F/'initial-scene-private.json',initial);save(F/'initial-RNG-private.json',initial_rng);assert initial==read(R/'stage359/B/initial-scene-private.json') and initial_rng==read(R/'stage359/B/initial-RNG-private.json') and np.array_equal(obs,stack(z['frames_uint8'],0))
        charge(D,'actor_resets');policy,_=w.call('reset',obs);validate_response(policy,p['config'],obs,'reset');assert projection(policy['state'])==projection(old_reset['state']) and policy['packaged_support_state']==[] and policy['packaged_support_step']==0 and policy['support_record'] is None
        save(F/'reset-policy-private.json',policy);frame(obs);reset_qualified=True;save(D/'reset-qualification.json',dict(passed=True,case_initialpixels_geometry_obstacles_fullphysics_evaluatorRNG_originalresetprojection_exact=True,runtime_versions_match_historical359=True,policy_members_only_history_metadata_and_routing=True,same_passive_observer=True,historical359_not_new=True))
        save(D/'actual-reset-contract.json',dict(raw_limit=8200,elapsed_after_reset=50,frame_skip=4,underlying_cap=2038,normal_default_cap=2000,registered_research_cap=2000,raw_reset_ticks=51,postreset_start_time=start_time,no_extra_cached_actor=True))
        original_step=raw.step
        def observed_step(*args,**kwargs):
            nonlocal raw_step_wall,raw_observer_wall
            t=time.perf_counter();out=original_step(*args,**kwargs);raw_step_wall+=time.perf_counter()-t;t=time.perf_counter()
            contacts=sorted(list(pair) for c in raw.world.contacts if c.touching and (pair:=obstacle_contact_pair(c,raw.car,raw.obstacles)) is not None)
            raw_records.append(dict(raw_time=float(raw.t),pairs=contacts,hit_objects=[i for i,o in enumerate(raw.obstacles) if o.userData.hit],collision=bool(out[4].get('collision',False)),position=list(raw.car.hull.position),speed_m_s=float(np.hypot(*raw.car.hull.linearVelocity)),unique_tiles=int(raw.tile_visited_count)))
            raw_observer_wall+=time.perf_counter()-t;return out
        raw.step=observed_step;j=(F/'trace-private.jsonl').open('x');(F/'trace-private.jsonl').chmod(0o600);pj=(F/'policy-responses-private.jsonl').open('x');(F/'policy-responses-private.jsonl').chmod(0o600)
        for i in range(p['episode_cap']):
            verify(R);pre=plain(truth(env));t=time.perf_counter();full_before=physical(env);before=full_before if i<72 else compact(full_before);before_rng=rng(env);capture_wall+=time.perf_counter()-t;timer=env.env._elapsed_steps;checking=common
            if checking:
                assert i<len(old),'sharedstate cannot outlast historicalofficialterminal';h=old[i];expected=old_reset['state'] if i==0 else old[i-1]['policy']
                assert np.array_equal(obs,stack(z['frames_uint8'],i)) and pre==h['pre'] and before==h['pre_physical'] and before_rng==h['pre_RNG'] and projection(policy['state'])==projection(expected),(i+1,'commonpre')
                common_inputs=i+1
            charge(D,'actor_act_calls');r,ms=w.call('act',obs);actorcpu=r['actor_cumulative_CPU_s'];policy_ms.append(ms);pj.write(json.dumps(dict(step=i+1,response=r),allow_nan=False)+'\n');pj.flush();command=validate_response(r,p['config'],obs,'act')
            assert r['delta_audit']['action']==command.tolist();e=r['routing_evidence'];assert e['tracker_preserved'] and e['full_hazards']==r['tracker_record']['after'] and r['features'][11]==len(e['full_hazards']);assert r['packaged_support_step']==i+1 and r['packaged_support_state']==r['support_record']['after']
            assert e['removed_indices']==[k for k,(point,item) in enumerate(zip(e['full_hazards'],r['support_record']['after'])) if item['low'] and point[3]>0 and not item['positive_history']]
            charge(D,'actor_commit_calls');c,_=w.call('commit',command);policy=c;actorcpu=c['actor_cumulative_CPU_s'];assert not c['python_audit_denied_events'] and c['memory']==c['nominal_memory']==r['state']['previous_steer'] and np.float32(c['memory'])==command[0] and c['history'][-1]==command.tolist()
            same_command=False
            if i<len(old):
                if first_action is None and r['action']!=old[i]['returned_action']:first_action=i+1
                if first_routing is None and e['removed_indices']!=old[i]['routing_evidence']['removed_indices']:first_routing=i+1
            if checking:
                assert r['tracker_record']==h['tracker'] and legacy_support(r['support_record'])==h['support_record']
                for key in ['RNG_python_sha256','RNG_numpy_sha256','cv2_seed_calls']:assert r['state'][key]==h['actor_state'][key]
                fields=[]
                for key,refkey in [('action','returned_action'),('features','features'),('pixel_path','pixel_path'),('delta_audit','audit')]:
                    if r[key]!=h[refkey]:fields.append(key)
                if projection(c['state'])!=projection(h['policy']):fields.append('original_policy_state_projection')
                same_command=r['action']==h['returned_action']
                if fields:
                    assert e['removed_indices']!=h['routing_evidence']['removed_indices'],'firstsemanticbranch lacksselectionchange';common=False;first_branch=i+1;branch_fields=fields
                else:common_actions+=1
            charge(D,'actions');steps+=1;raw_records=[];t0=raw.t;obs,_,ended,truncated,info=env.step(command);ticks=round((raw.t-t0)*50);rawticks+=ticks;assert env.env._elapsed_steps-timer==ticks==len(raw_records);complete=raw.finish_time_s is not None;frame(obs);actions.append(command.copy());post=plain(truth(env));t=time.perf_counter();full_after=physical(env);after=full_after if i<72 else compact(full_after);after_rng=rng(env);capture_wall+=time.perf_counter()-t;final_finish=finish_record(raw)
            row=dict(step=i+1,executed=command.tolist(),returned_action=r['action'],features=r['features'],audit=r['delta_audit'],tracker=r['tracker_record'],support_record=r['support_record'],routing_evidence=e,pixel_path=r['pixel_path'],actor_state=r['state'],nominal_memory=c['memory'],policy=c['state'],pre=pre,post=post,pre_physical=before,post_physical=after,pre_RNG=before_rng,post_RNG=after_rng,raw_observations=raw_records,collision=bool(info['collision']),damage=float(env.damage.damage),terminated=bool(ended),truncated=bool(truncated),completed=complete,finish=final_finish,retire_reason=info.get('retire_reason'),elapsed_raw_counter=env.env._elapsed_steps,raw_ticks=ticks,info=plain(info))
            t=time.perf_counter();j.write(json.dumps(row,default=json_default,allow_nan=False)+'\n');j.flush();journal_wall+=time.perf_counter()-t;events.append(row)
            if checking and same_command:
                assert np.array_equal(obs,stack(z['frames_uint8'],i+1)) and post==h['post'] and after==h['post_physical'] and after_rng==h['post_RNG'] and raw_records==h['raw_observations'] and final_finish==h['finish'],(i+1,'commonpost')
                for key in ['collision','damage','terminated','truncated','raw_ticks']:assert row[key]==h[key],(i+1,key)
                common_commands+=1
                if common:common_inputs=i+2
            if steps%200==0:print(json.dumps(dict(stage=367,actions=steps,common_actions=common_actions,first_semantic_branch=first_branch,unique_tiles=post['unique_tiles'],official_finish=complete)),flush=True)
            if ended or truncated:break
        verify(R,True);save(D/'historical-comparison-qualification.json',dict(passed=True,historical_source='359N2/357notnewcontrol',fresh_reset_same=True,common_semantic_actions=common_actions,common_fullcommands=common_commands,common_qualified_input_stacks=common_inputs,first_routing_membership_difference=first_routing,first_semantic_output_difference=first_branch,first_semantic_fields=branch_fields,first_full_control_difference=first_action,no_semantic_branch=first_branch is None,original_state_projection_pixels_physics_accessRNG_rawticks_exact_wherecommon=True,passive_observer_version_diff=False,ownobservations_controls_normalmemory=True))
    except BaseException as e:
        error=type(e).__name__+': '+str(e);save(F/'error-private.json',dict(error=error,traceback=__import__('traceback').format_exc(),budget=read(D/'native-budget.json')))
    finally:
        if j:j.close()
        if pj:pj.close()
        elapsed=env.env._elapsed_steps if env else None;reaping=w.close() if w else None
        if env:env.close()
    if frames:
        t=time.perf_counter();f=F/'frames-actions-private.npz';np.savez_compressed(f,frames_uint8=np.asarray(frames,np.uint8),actions=np.asarray(actions,np.float32));f.chmod(0o600);artifact_wall+=time.perf_counter()-t
    result=dict(native_actions=steps,native_cap=p['episode_cap'],total_accounting_cap=p['total_native_cap'],technical_error=error,reset_qualified=reset_qualified,terminated=bool(ended),truncated=bool(truncated),completed=bool(complete),actual_DNF=bool(ended and not complete),censored=bool(error or not complete and not ended),protocol_stop=bool(not error and not ended and not truncated and steps==p['episode_cap']),retire_reason=info.get('retire_reason'),finish=final_finish,postreset_start_time=start_time,stop_reason='technical_stop' if error else 'official_finish' if complete else 'actual_retirement' if ended else 'other_official_truncation' if truncated else 'research2000_budget_protocol_cap',lap_ms=round((final_finish['finish_time_s']-start_time)*1000) if complete else None,first_contact=next((r['step'] for r in events if r['collision']),None),collision_actions=[r['step'] for r in events if r['collision']],damage=events[-1]['damage'] if events else None,unique_tiles=events[-1]['post']['unique_tiles'] if events else None,total_tiles=p['case']['road_point_count'],comparison_valid=bool(not error and reset_qualified),common_semantic_actions=common_actions,first_semantic_output_difference=first_branch,first_full_control_difference=first_action,first_routing_membership_difference=first_routing,raw_step_ticks=rawticks,raw_reset_ticks=reset_ticks,raw_counter_after_reset=initial_counter,raw_counter_at_stop=elapsed,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=actorcpu,reset_wall_s=reset_wall,raw_step_render_wall_s=raw_step_wall,raw_contact_observer_wall_s=raw_observer_wall,capture_wall_s=capture_wall,journal_wall_s=journal_wall,artifact_wall_s=artifact_wall,policy_IPC_max_ms=max(policy_ms) if policy_ms else None,reaping=reaping)
    save(F/'result.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]).resolve())
