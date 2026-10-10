"""One charged frozen-policy reproduction, stopping at the first difference.

Privileged geometry is recorded only by the evaluator. The policy sees pixels.
Every selected action and observation is compared with the saved reference.
"""
import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import time
import traceback
import zipfile

import numpy as np
from retry.diagnose import Budget, make_env
from retry.evaluate import check_window, observation_contract
from retry.qualify_pixel_package import PipeWorker


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def array_sha(value):
    return hashlib.sha256(np.asarray(value,dtype='<f8').tobytes()).hexdigest()


def truth(env):
    raw = env.unwrapped
    hull = raw.car.hull
    return {'position':list(hull.position),'speed_m_s':math.hypot(*hull.linearVelocity),
            'velocity':list(hull.linearVelocity),'angle':float(hull.angle),'angular_velocity':float(hull.angularVelocity),
            'time':raw.t,'unique_tiles':raw.tile_visited_count,'damage':env.damage.damage,
            'off_track_counter':env.off_track_counter,
            'wheels':[{'position':list(w.position),'angle':float(w.angle),'joint_angle':float(w.joint.angle),
                       'steer':float(w.steer),'gas':float(w.gas),'brake':float(w.brake),'omega':float(w.omega)}
                      for w in raw.car.wheels]}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--plan',required=True,type=Path)
    args = parser.parse_args(); plan_path = args.plan.resolve(); D = plan_path.parent
    p = json.loads(plan_path.read_text()); started = time.perf_counter()
    env = child = None; used = raw_ticks = reset_ticks = 0; matches = 0
    act_ms = []; rss = []; sim_wall = 0.; first_difference = None
    report = {'new_learning':0,'policy_changed':False,'first_difference':None,'diagnosis_allowed':False}
    def difference(where,index,actual,wanted):
        nonlocal first_difference
        first_difference = {'where':where,'action_index':index,'actual':actual,'expected':wanted}
        raise RuntimeError('First reference difference: '+where)
    try:
        check_window(p)
        assert sha(plan_path) == (D/'plan.sha256').read_text().split()[0]
        for name,wanted in p['source_sha256'].items():assert sha(Path(name)) == wanted,name
        for name,wanted in p['reference_source_sha256'].items():assert sha(Path(name)) == wanted,name
        config = p['candidate'];assert sha(Path(config['archive_path'])) == config['archive_sha256']
        clean = D/'policy-cpu'; clean.mkdir(mode=0o700,exist_ok=False)
        package = clean/'package';package.mkdir()
        with zipfile.ZipFile(config['archive_path']) as zipped:
            assert set(zipped.namelist()) == set(config['members_sha256'])
            for name,wanted in config['members_sha256'].items():
                relative=Path(name);assert not relative.is_absolute() and '..' not in relative.parts
                data=zipped.read(name);assert hashlib.sha256(data).hexdigest() == wanted
                target=package/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);target.chmod(0o444)
        for f in sorted(package.rglob('*'),reverse=True):
            if f.is_dir():f.chmod(0o555)
        package.chmod(0o555)
        worker_path=clean/'worker.py';shutil.copyfile(p['worker_path'],worker_path);worker_path.chmod(0o444)
        (clean/'home').mkdir();(clean/'tmp').mkdir()
        runtime={'PATH':str(Path(sys.executable).parent)+':/usr/bin:/bin','HOME':str(clean/'home'),'TMPDIR':str(clean/'tmp'),
                 'LANG':'C.UTF-8','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1',
                 'CUDA_VISIBLE_DEVICES':'','SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'}
        child = PipeWorker([sys.executable,'-I','-B',str(worker_path),str(package)],clean,runtime)
        assert child.cold_start_ms <= 10000
        report.update(worker_ready=child.ready,cold_start_ms=child.cold_start_ms)
        reference=[json.loads(line) for line in Path(p['reference_trace']).read_text().splitlines()]
        old_start=json.loads(Path(p['reference_started']).read_text())
        old_result=json.loads(Path(p['reference_result']).read_text())
        saved=np.load(p['reference_pixels_actions']);actions=saved['actions']
        assert actions.dtype == np.float32 and len(actions) == len(reference) == p['expected_actions']
        budget=Budget(plan_path,'single_reproduction')
        check_window(p);env=make_env();before_reset=time.perf_counter()
        obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']})
        report['reset_environment_wall_s']=time.perf_counter()-before_reset
        reset_ticks=round(env.unwrapped.t*50);assert reset_ticks == 51
        observation_contract(obs)
        initial_hash=hashlib.sha256(obs.tobytes()).hexdigest()
        if initial_hash != old_start['initial_observation_sha256']:
            difference('reset_observation',0,initial_hash,old_start['initial_observation_sha256'])
        initial=truth(env)
        if {k:initial[k] for k in old_start['initial']} != old_start['initial']:
            difference('reset_truth',0,{k:initial[k] for k in old_start['initial']},old_start['initial'])
        geometry=array_sha(env.unwrapped.track)
        obstacles=[{'id':i,'position':list(o.position),'radius':float(o.fixtures[0].shape.radius)}
                   for i,o in enumerate(env.unwrapped.obstacles)]
        obstacle_hash=array_sha([[*o['position'],o['radius']] for o in obstacles])
        assert geometry == old_start['geometry_sha256'] == p['case']['road_geometry_sha256']
        assert obstacle_hash == old_start['obstacles_sha256']
        hull=env.unwrapped.car.hull
        scene={'track':env.unwrapped.track,'obstacles':obstacles,
               'hull_fixture_local_vertices':[[list(v) for v in f.shape.vertices] for f in hull.fixtures],
               'hull_fixture_skin_radii':[float(f.shape.radius) for f in hull.fixtures],
               'wheel_fixture_local_vertices':[[[list(v) for v in f.shape.vertices] for f in w.fixtures] for w in env.unwrapped.car.wheels],
               'wheel_fixture_skin_radii':[[float(f.shape.radius) for f in w.fixtures] for w in env.unwrapped.car.wheels],
               'wheel_local_anchors':[list(hull.GetLocalPoint(w.joint.anchorA)) for w in env.unwrapped.car.wheels],
               'frame':'world metres plus hull-local x-right,y-forward; world=position+R(hull.angle)*local',
               'geometry_sha256':geometry,'physical_obstacle_sha256':obstacle_hash}
        (D/'scene.json').write_text(json.dumps(scene,indent=2)+'\n')
        reset,reset_ms=child.call('reset',obs);assert reset['ok'] and reset_ms <= 5000
        report['reset_including_IPC_ms']=reset_ms
        (D/'started.json').write_text(json.dumps({'initial':initial,'initial_observation_sha256':initial_hash,
                                                 'geometry_sha256':geometry,'obstacles_sha256':obstacle_hash,'plan_sha256':sha(plan_path)},indent=2)+'\n')
        raw_records=[]
        original_raw_step=env.env.step
        def raw_observer(action):
            before=truth(env);hits=[o.userData.hit for o in env.unwrapped.obstacles]
            result=original_raw_step(action)
            after=truth(env)
            raw_records.append({'before_time':before['time'],'after_time':after['time'],
                                'before':before,'after':after,'collision':bool(result[4].get('collision',False)),
                                'new_hit_obstacle_ids':[i for i,o in enumerate(env.unwrapped.obstacles) if not hits[i] and o.userData.hit]})
            return result
        env.env.step=raw_observer
        sequence=hashlib.sha256()
        with (D/'trace.jsonl').open('w') as output:
            for index,old in enumerate(reference):
                check_window(p)
                before=truth(env);input_hash=hashlib.sha256(obs.tobytes()).hexdigest()
                wanted=old_start['initial_observation_sha256'] if index == 0 else reference[index-1]['observation_sha256_after']
                if input_hash != wanted:difference('before_observation',index+1,input_hash,wanted)
                legacy={k:before[k] for k in old['truth_before']}
                if legacy != old['truth_before']:difference('before_truth',index+1,legacy,old['truth_before'])
                response,duration=child.call('act',obs);actual=np.asarray(response['action'],dtype=np.float32)
                assert actual.shape == (3,) and np.isfinite(actual).all() and np.all(actual >= [-1,0,0]) and np.all(actual <= [1,1,1])
                if actual.tobytes() != actions[index].tobytes():difference('action_before_step',index+1,actual.tolist(),actions[index].tolist())
                assert duration <= 5000 and response['rss_mib']*1024*1024 <= 1_024_000_000
                act_ms.append(duration);rss.append(response['rss_mib']);raw_records.clear()
                sim_start=time.perf_counter();obs,_,ended,truncated,info=budget.step(env,actual);sim_wall+=time.perf_counter()-sim_start;used+=1
                after=truth(env);raw_ticks+=len(raw_records);observation_contract(obs)
                output_hash=hashlib.sha256(obs.tobytes()).hexdigest()
                if output_hash != old['observation_sha256_after']:difference('after_observation',index+1,output_hash,old['observation_sha256_after'])
                legacy={k:after[k] for k in old['truth_after']}
                if legacy != old['truth_after']:difference('after_truth',index+1,legacy,old['truth_after'])
                if (bool(ended),bool(truncated),info['retire_reason']) != (old['terminated'],old['truncated'],old['retire_reason']):
                    difference('endpoint_flags',index+1,[bool(ended),bool(truncated),info['retire_reason']],[old['terminated'],old['truncated'],old['retire_reason']])
                matches+=1;sequence.update(actual.tobytes())
                row={'step':index+1,'before_time':before['time'],'after_time':after['time'],
                     'observation_sha256_before':input_hash,'observation_sha256_after':output_hash,
                     'action':actual.tolist(),'action_sha256':hashlib.sha256(actual.tobytes()).hexdigest(),
                     'route_telemetry':response['route_telemetry'],'cap_diagnostic':response['cap_diagnostic'],
                     'previous_steer_after':response['previous_steer_after'],'original_calls':response['original_calls'],
                     'truth_before':before,'truth_after':after,'raw_intervals':list(raw_records),
                     'collision':bool(info['collision']),'terminated':bool(ended),'truncated':bool(truncated),
                     'retire_reason':info['retire_reason'],'act_including_IPC_ms':duration,'rss_mib':response['rss_mib']}
                output.write(json.dumps(row)+'\n');output.flush()
                if ended or truncated:
                    assert index == len(reference)-1
                    break
            else:
                difference('missing_reference_endpoint',used,False,True)
        assert matches == len(reference) and env.unwrapped.tile_visited_count == old_result['unique_tiles']
        report.update(verdict='PASS_IDENTICAL_INSTRUMENTED_REPRODUCTION',diagnosis_allowed=True,
                      matched_actions=matches,matched_observation_hashes=matches+1,
                      action_sequence_sha256=sequence.hexdigest(),completed=env.unwrapped.finish_time_s is not None,
                      unique_tiles=env.unwrapped.tile_visited_count,total_tiles=len(env.unwrapped.track),
                      damage=env.damage.damage,retire_reason=info['retire_reason'],actor_CPU_s=response['actor_cumulative_CPU_s'])
    except Exception as error:
        report.update(verdict='STOP_FIRST_DIFFERENCE_OR_TECHNICAL_RESOURCE_FAILURE',error=repr(error),
                      first_difference=first_difference,traceback=traceback.format_exc(),diagnosis_allowed=False)
    finally:
        if child:
            report['worker_reaping']=child.close()
            report['supervisor_peak_rss_bytes']=child.observed_peak_rss_bytes
            if not report['worker_reaping']['process_reaped']:
                report.update(verdict='STOP_PROCESS_REAPING_FAILURE',diagnosis_allowed=False)
        if env:env.close()
        ledger=json.loads((D/'budget.json').read_text())
        report.update(charged_wrapper_actions=ledger['actions'],successful_wrapper_steps=used,raw_step_ticks=raw_ticks,raw_reset_ticks=reset_ticks,
                      max_act_including_IPC_ms=max(act_ms,default=None),peak_actor_RSS_MiB=max(rss,default=None),
                      sum_sim_step_wall_s=sim_wall,wall_s=time.perf_counter()-started,additional_runs_or_retries=0,
                      expected_actions=p['expected_actions'],plan_sha256=sha(plan_path),archive_sha256=p['candidate']['archive_sha256'])
        (D/'reproduction-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report.get(k) for k in ('verdict','diagnosis_allowed','charged_wrapper_actions','matched_actions',
                                              'matched_observation_hashes','first_difference','max_act_including_IPC_ms','peak_actor_RSS_MiB','wall_s','error')}),flush=True)
    return int(not report['diagnosis_allowed'])


if __name__ == '__main__':
    sys.exit(main())
