"""Bounded fixed-action replay and isolated road-input shadow capture."""
import argparse
import base64
from collections import deque
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

from retry import fresh_dev_distribution as cohort
from retry.diagnose import Budget
from retry.evaluate import check_window
from retry.full_route_reproduction import array_sha,truth
from retry.qualify_pixel_package import PipeWorker
from retry.current_view_road_oracle import camera,road_mask
from retry.visible_road_occlusion import occlusion_stencil,visible_road_mask


def sha_bytes(a):return hashlib.sha256(a.tobytes()).hexdigest()
def decoded(a):return np.frombuffer(base64.b64decode(a['base64']),dtype=a['dtype']).reshape(a['shape']).copy()


def regions(env):
    raw=env.unwrapped;s=truth(env);cam=camera(raw)
    objects=[{'transform':o.transform,'fixtures':[list(f.shape.vertices) for f in o.fixtures],'phase':getattr(o,'phase',None)} for o in raw.car.drawlist]
    obs=[(*map(float,o.position),float(o.fixtures[0].shape.radius)) for o in raw.obstacles]
    layers=[(p,tuple(c) in ((255,255,255),(255,0,0))) for p,c in raw.road_poly]
    H,_=occlusion_stencil([],[],[],s,*cam);C,_=occlusion_stencil([],[],objects,s,*cam);O,_=occlusion_stencil([],obs,[],s,*cam);K,_=occlusion_stencil(layers,[],[],s,*cam)
    return dict(HUD=H,car=C*(1-H),obstacles=O*(1-H),curb=K*(1-H))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plan',type=Path,required=True)
    path=parser.parse_args().plan.resolve();D=path.parent;p=json.loads(path.read_text());check_window(p)
    assert cohort.sha(path)==path.with_suffix('.sha256').read_text().split()[0]
    for n,h in p['source_sha256'].items():assert cohort.sha(Path(n))==h,n
    clone_dir=D/p['clone_directory'];clone_dir.mkdir(mode=0o700);execution=cohort.clone(p,clone_dir);clean,package,worker,runtime=execution
    helper=clean/'boundary.py';helper.write_bytes(Path(p['boundary_path']).read_bytes());helper.chmod(0o444)
    results=[]
    for c in p['cases']:
        if c['action_mode']=='UNAVAILABLE':
            results.append({'id':c['id'],'status':'DATA_UNAVAILABLE','reason':c['reason'],'charged_wrapper_actions':0});continue
        out=D/c['id'];out.mkdir(mode=0o700);env=child=None;used=raw=reset_ticks=0;sim_wall=mask_wall=0.;started=time.perf_counter();rows=[];captures=[];sequence=hashlib.sha256();match_rows=0
        result={'id':c['id'],'status':'RESOURCE_CENSORED','same_state_comparison_qualified':False,'episode_count':1,'action_mode':c['action_mode']}
        try:
            if c['action_mode']=='RECORDED':
                stored=np.load(c['pixels_actions_path']);frames=stored['frames'].astype(np.float32)/np.float32(255);actions=stored['actions'];references={r['step']:r for r in (json.loads(x) for x in Path(c['trace_path']).read_text().splitlines())}
            else:
                actions=None;frames=None;references={int(k):v for k,v in c['retained_reference_rows'].items()}
            env=cohort.make_env();reset_start=time.perf_counter();obs,_=env.reset(seed=c['seed'],options={'track_id':c['track_id']});result['reset_wall_s']=time.perf_counter()-reset_start
            reset_ticks=round(env.unwrapped.t*50);assert reset_ticks==51
            assert sha_bytes(obs)==c['baseline_initial_observation_sha256']
            actual=truth(env);assert {k:actual[k] for k in c['baseline_initial_truth']}==c['baseline_initial_truth']
            assert array_sha(env.unwrapped.track)==c['road_geometry_sha256']
            obstacles=[[*map(float,o.position),float(o.fixtures[0].shape.radius)] for o in env.unwrapped.obstacles];assert array_sha(obstacles)==c['expected_physical_obstacles_sha256']
            cohort.write(out/'started.json',{'initial':actual,'observation_sha256':sha_bytes(obs),'plan_sha256':cohort.sha(path)})
            child=PipeWorker([sys.executable,'-I','-B',str(worker),str(package)],clean,runtime)
            initial=np.concatenate([obs,np.zeros((1,84,84),np.float32)]);child.call('reset',initial);budget=Budget(path,c['id'])
            for step in range(1,c['stop_step']+1):
                check_window(p);assert dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(p['simulation_deadline_utc'])
                before=truth(env);expected=references.get(step)
                if frames is not None:
                    indices=[max(0,step-4+j) for j in range(4)];saved=frames[indices];assert sha_bytes(obs)==sha_bytes(saved);obs=saved.copy()
                if expected:
                    ref_before=expected['truth_before'];assert {k:before[k] for k in ref_before}==ref_before
                    wanted=expected.get('observation_sha256_before')
                    if wanted:assert sha_bytes(obs)==wanted
                t=time.perf_counter();mask,receipt=visible_road_mask(env);mask_wall+=time.perf_counter()-t
                keep=step in c['capture_steps'];reply,duration=child.call('capture' if keep else 'act',np.concatenate([obs,mask[None].astype(np.float32)]))
                generated=np.asarray(reply['action'],np.float32)
                if actions is not None:fixed=actions[step-1];assert generated.tobytes()==fixed.tobytes()
                elif expected:fixed=np.asarray(expected['action'],np.float32);assert generated.tobytes()==fixed.tobytes()
                else:fixed=generated.copy()
                sequence.update(fixed.tobytes())
                arrays={}
                if keep:
                    A,_=road_mask(env);arrays.update(observation=np.rint(obs*255).astype(np.uint8),full_GT=A,visible_GT=mask,executed_action=fixed,**regions(env))
                    for arm in ['pixel','visible_GT_shadow']:
                        for k,v in reply[arm].pop('arrays').items():arrays[arm+'_'+k]=decoded(v)
                    arrays['pre_memory_pickle']=np.frombuffer(base64.b64decode(reply.pop('pre_memory_pickle_base64')),np.uint8).copy()
                t=time.perf_counter();next_obs,_,ended,truncated,info=budget.step(env,fixed);sim_wall+=time.perf_counter()-t;used+=1;raw+=round((env.unwrapped.t-before['time'])*50)
                after=truth(env)
                if expected:
                    ref_after=expected['truth_after'];assert {k:after[k] for k in ref_after}==ref_after
                    assert sha_bytes(next_obs)==expected['observation_sha256_after'];match_rows+=1
                if frames is not None:
                    indices=[max(0,step-3+j) for j in range(4)];assert sha_bytes(next_obs)==sha_bytes(frames[indices])
                row={'step':step,'before_time':before['time'],'after_time':after['time'],'truth_before':before,'truth_after':after,'observation_sha256_before':sha_bytes(obs),'observation_sha256_after':sha_bytes(next_obs),'executed_action':fixed.tolist(),'collision_after_action':bool(info['collision']),'retire_reason':info['retire_reason'],'pixel':reply['pixel'],'visible_GT_shadow':reply['visible_GT_shadow'],'memory_receipt':{k:reply[k] for k in ['actual_pre_memory_sha256','shadow_pre_memory_sha256','actual_post_memory_sha256','actual_post_unchanged_by_shadow','shared_tracker_calls']},'metrics':{k:reply[k] for k in ['false_road_cells','missing_road_cells','closed_road_difference_cells','allowed_difference_cells','action_delta']},'mask_receipt':receipt,'act_including_IPC_ms':duration}
                rows.append(row)
                if keep:
                    arrays['observation_after']=np.rint(next_obs*255).astype(np.uint8);arrays['truth_before_json']=np.frombuffer(json.dumps(before).encode(),np.uint8);arrays['truth_after_json']=np.frombuffer(json.dumps(after).encode(),np.uint8)
                    capture_path=out/f'paired-step-{step:04d}.npz';np.savez_compressed(capture_path,**arrays);capture_path.chmod(0o600);captures.append({'step':step,'path':str(capture_path),'sha256':cohort.sha(capture_path),'observation_time':'before executed fixed action; after observation stored separately'})
                obs=next_obs
                if ended or truncated:assert step==c['stop_step'];break
            if actions is None:assert sequence.hexdigest()==c['full_action_sequence_sha256']
            result.update(status='CAPTURED',same_state_comparison_qualified=True,initial_pixels_and_recorded_truth_exact=True,action_sequence_sha256=sequence.hexdigest(),retained_reference_rows_matched=match_rows,all_original_pixel_actions_exact=True,observed_prefix_end_step=used,first_damage_step=next((x['step'] for x in rows if x['truth_after']['damage']>x['truth_before']['damage']),None),comparability_limit=c['comparability_limit'])
        except Exception as exc:
            result.update(error=repr(exc),status='INCONCLUSIVE_MISMATCH_OR_RESOURCE',same_state_comparison_qualified=False)
        finally:
            if env:env.close()
            if child:result.update(worker_reaping=child.close(),worker_ready=child.ready,actor_CPU_s=reply.get('actor_cumulative_CPU_s') if 'reply' in locals() else None)
            ledger=json.loads((D/'budget.json').read_text());result.update(charged_wrapper_actions=ledger['stages'].get(c['id'],0),successful_wrapper_steps=used,raw_step_ticks=raw,raw_reset_ticks=reset_ticks,sim_step_wall_s=sim_wall,mask_generation_wall_s=mask_wall,wall_s=time.perf_counter()-started,captures=captures,rows=len(rows))
            if rows:
                trace=out/'paired-trace.jsonl';trace.write_text(''.join(json.dumps(x,allow_nan=False)+'\n' for x in rows));trace.chmod(0o600)
                action_path=out/'fixed-actions.npy';np.save(action_path,np.asarray([x['executed_action'] for x in rows],np.float32));action_path.chmod(0o600)
            cohort.write(out/'result.json',result)
        results.append(result);cohort.write(D/p['report_name'],{'results':results,'plan_sha256':cohort.sha(path),'new_policy_change':0,'GT_actions_executed':0,'HOLDOUT_or_SEALED':0})
        print(json.dumps({k:result.get(k) for k in ['id','status','charged_wrapper_actions','same_state_comparison_qualified','first_damage_step','error']}),flush=True)
        if result['status']!='CAPTURED':break
    cohort.write(D/p['report_name'],{'results':results,'plan_sha256':cohort.sha(path),'charged_wrapper_actions':sum(x['charged_wrapper_actions'] for x in results),'new_policy_change':0,'GT_actions_executed':0,'HOLDOUT_or_SEALED':0})


if __name__=='__main__':main()
