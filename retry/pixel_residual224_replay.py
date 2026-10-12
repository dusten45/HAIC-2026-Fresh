"""One-use fixed-command DEV replay with a causally independent pixel shadow.

--plan supplies private frozen cases, references, budget and archive configuration.
No teacher planner is imported/called. GT endpoint checks are evaluator-only.
Stored 221 has reset and final rolling observation hashes, not per-act hashes;
the whole road is quarantined until its final hash and clean shadow check pass.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import resource
import time
import numpy as np


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dump(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
    p.chmod(0o600)


def replay(plan_path):
    from retry.diagnose import Budget,make_env
    from retry.evaluate import observation_contract
    from retry.frozen_composite_runtime import prepare,validate_response
    from retry.frozen_paired_evaluation import native_window,verify_files
    from retry.full_route_reproduction import truth
    plan=json.loads(plan_path.read_text());assert sha(plan_path)==plan_path.with_suffix('.sha256').read_text().strip()
    verify_files(plan['source_sha256']);verify_files(plan['runtime_sha256'])
    root=plan_path.parent;dump(root/'opening.json',dict(at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),native_cap=1600))
    start,cpu=time.perf_counter(),time.process_time();results=[]
    for label,case in zip(plan['labels'],plan['cases']):
        native_window(plan)
        run=root/label;run.mkdir(mode=0o700)
        ref=Path(plan['reference_runs'])/(case['id']+'__C')
        old=json.loads((ref/'result.json').read_text());rows=json.loads((ref/'oracle-diagnostic.json').read_text())['actual_steps']
        teacher=np.asarray([r['action'] for r in rows],np.float32)
        assert teacher.shape==(old['charged_wrapper_actions'],3)
        assert hashlib.sha256(teacher.tobytes()).hexdigest()==old['action_sequence_sha256']
        worker=clean=env=None;used=0;rawticks=0;obslist=[];shadow=[];lat=[];simwall=0.;actorcpu=0.;cleanCPU=0.;cleanlat=[]
        qualified=False;error=None;obs_hash=hashlib.sha256();hash_match=False;reset_match=False
        record=dict(road=label,recorded_commands=len(rows),qualified=False)
        st=time.perf_counter();scpu=time.process_time()
        try:
            worker=prepare(plan['shadow'],run/'shadow',plan['sandbox_path'])
            env=make_env();budget=Budget(plan_path,label)
            obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']})
            observation_contract(obs)
            reset_match=hashlib.sha256(obs.tobytes()).hexdigest()==old['initial']['observation_sha256']
            assert reset_match,'reset_observation_hash_mismatch'
            assert hashlib.sha256(json.dumps(truth(env),sort_keys=True,allow_nan=False).encode()).hexdigest()==old['initial']['state_sha256'],'reset_state_mismatch'
            response,_=worker.call('reset',obs);validate_response(response,plan['shadow'],obs,'reset')
            obslist.append(obs.copy());obs_hash.update(obs.tobytes());start_t=env.unwrapped.t
            for i,(command,expected) in enumerate(zip(teacher,rows)):
                native_window(plan)
                response,ms=worker.call('act',obs);validate_response(response,plan['shadow'],obs,'act')
                assert ms<=5000 and len(response['shadow_features'])==16
                shadow.append(response);lat.append(ms);actorcpu=max(actorcpu,response['actor_cumulative_CPU_s'])
                previous=obs;before=env.unwrapped.t;t=time.perf_counter()
                obs,_,ended,truncated,info=budget.step(env,command);simwall+=time.perf_counter()-t;used+=1
                ticks=round((env.unwrapped.t-before)*50);rawticks+=ticks
                observation_contract(obs);assert np.array_equal(obs[:3],previous[1:]),'frame_stack_timing_mismatch'
                obslist.append(obs.copy());obs_hash.update(obs.tobytes())
                actual=truth(env)
                for key in ['position','velocity','angle','speed_m_s','damage','unique_tiles','off_track_counter']:
                    assert actual[key]==expected[key],f'endpoint_mismatch_action_{i+1}_{key}'
                assert ticks==expected['raw_ticks'],f'partial_tick_mismatch_action_{i+1}'
                assert bool(ended or truncated)==expected['terminal'],f'terminal_mismatch_action_{i+1}'
                assert bool(info['collision'])==expected['collision'],f'collision_mismatch_action_{i+1}'
                if ended or truncated:assert i==len(rows)-1,'early_terminal'
                if used%100==0:print(json.dumps(dict(road=label,native=used)),flush=True)
            hash_match=obs_hash.hexdigest()==old['observation_sequence_sha256']
            assert hash_match,'final_rolling_observation_hash_mismatch_entire_road_quarantined'
            assert rawticks==old['raw_step_ticks']
            assert round((env.unwrapped.finish_time_s-start_t)*1000)==old['lap_ms']
            record['finish_partial_ticks']=rows[-1]['raw_ticks']
            # Separate pristine champion run on cached observations, no env.step.
            clean=prepare(plan['champion'],run/'clean',plan['sandbox_path'])
            response,_=clean.call('reset',obslist[0]);validate_response(response,plan['champion'],obslist[0],'reset')
            for observation,response_shadow in zip(obslist[:-1],shadow):
                response,ms=clean.call('act',observation);action=validate_response(response,plan['champion'],observation,'act')
                assert ms<=5000 and np.array_equal(action,np.asarray(response_shadow['action'],np.float32)),'shadow_vs_clean_champion_command_mismatch'
                cleanCPU=max(cleanCPU,response['actor_cumulative_CPU_s']);cleanlat.append(ms)
            base=np.asarray([x['action'] for x in shadow],np.float32)
            previous=np.concatenate(([0.],teacher[:-1,0]))
            # Mask retained solely for evaluation; not appended to features.
            state_diff=np.asarray([x['shadow_controller_before']['previous_steer'] for x in shadow])!=previous
            features=np.asarray([x['shadow_features'] for x in shadow],np.float64)
            assert np.array_equal(features[:,-3:].astype(np.float32),base)
            cache=run/'cache.npz';np.savez_compressed(cache,observations=np.asarray(obslist,np.float32),
                features=features,champion=base,teacher=teacher,previous_control_different=state_diff);cache.chmod(0o600)
            dump(run/'shadow-state.json',shadow)
            qualified=True
        except Exception as exc:
            error=type(exc).__name__+': '+str(exc)
            # No training cache is written until ALL exact replay checks pass.
        finally:
            for name,actor in [('shadow',worker),('clean',clean)]:
                if actor is not None:record[name+'_reaping']=actor.close()
            if env is not None:env.close()
            ledger=json.loads((root/'budget.json').read_text());charged=ledger['stages'].get(label,0)
            record.update(qualified=qualified,error=error,native_actions=charged,successful_steps=used,
                reset_hash_match=reset_match,rolling_observation_hash_match=hash_match,
                raw_step_ticks=rawticks,shadow_CPU_s=actorcpu,clean_check_CPU_s=cleanCPU,
                shadow_IPC_wall_s=sum(lat)/1000,clean_check_IPC_wall_s=sum(cleanlat)/1000,
                simulator_step_wall_s=simwall,episode_wall_s=time.perf_counter()-st,
                evaluator_CPU_s=time.process_time()-scpu,
                shadow_act_ms=dict(count=len(lat),median=float(np.median(lat)) if lat else None,
                    p95=float(np.percentile(lat,95)) if lat else None,max=max(lat,default=None)),
                stored_cache_bytes=(run/'cache.npz').stat().st_size if (run/'cache.npz').exists() else 0,
                stored_shadow_state_bytes=(run/'shadow-state.json').stat().st_size if (run/'shadow-state.json').exists() else 0)
            dump(run/'result.json',record);results.append(record);print(json.dumps(record),flush=True)
    ledger=json.loads((root/'budget.json').read_text())
    assert ledger['actions']==sum(r['native_actions'] for r in results)<=1600
    output=dict(stage=224,roads=results,native_actions=ledger['actions'],model_queries=0,
                wall_s=time.perf_counter()-start,evaluator_CPU_s=time.process_time()-cpu,
                evaluator_peak_RSS_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                all_workers_reaped=all(v['process_reaped'] and v['actor_pids_absent']
                  for r in results for k,v in r.items() if k.endswith('_reaping')),
                hash_scope='221reset hash + complete reset/post-step rolling hash; per-act reference hashes absent',
                teacher_recalled=False,student_closed_loop_runs=0,HOLDOUT_used=False,SEALED_opened=False)
    dump(root/'outcome.json',output)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--plan',type=Path,required=True)
    replay(ap.parse_args().plan.resolve())
