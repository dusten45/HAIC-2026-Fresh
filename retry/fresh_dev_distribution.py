"""One frozen-policy episode per prospectively registered fresh DEV condition.

Only bounded event windows are retained. Privileged evaluator state never enters
the pixel worker. Native termination and resource censoring remain distinct.
"""
import argparse
from collections import Counter, deque
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
import traceback
import zipfile

import numpy as np
from retry.diagnose import Budget
from retry.evaluate import check_window, observation_contract
from retry.full_route_reproduction import array_sha, make_env, sha, truth
from retry.qualify_pixel_package import PipeWorker


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    path.chmod(0o600)


def clone(plan, directory):
    config = plan['candidate']
    assert sha(Path(config['archive_path'])) == config['archive_sha256']
    clean = directory/'policy-cpu'; clean.mkdir(mode=0o700)
    package = clean/'package'; package.mkdir()
    with zipfile.ZipFile(config['archive_path']) as zipped:
        assert set(zipped.namelist()) == set(config['members_sha256'])
        for name, wanted in config['members_sha256'].items():
            relative = Path(name)
            assert not relative.is_absolute() and '..' not in relative.parts
            data = zipped.read(name)
            assert hashlib.sha256(data).hexdigest() == wanted
            target = package/relative; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data); target.chmod(0o444)
    for path in sorted(package.rglob('*'), reverse=True):
        if path.is_dir(): path.chmod(0o555)
    package.chmod(0o555)
    worker = clean/'worker.py'; shutil.copyfile(plan['worker_path'], worker)
    assert sha(worker) == sha(Path(plan['worker_path']))
    worker.chmod(0o444)
    (clean/'home').mkdir(); (clean/'tmp').mkdir()
    runtime = {'PATH':str(Path(sys.executable).parent)+':/usr/bin:/bin',
               'HOME':str(clean/'home'), 'TMPDIR':str(clean/'tmp'), 'LANG':'C.UTF-8',
               'OPENBLAS_NUM_THREADS':'1', 'OMP_NUM_THREADS':'1', 'MKL_NUM_THREADS':'1',
               'CUDA_VISIBLE_DEVICES':'', 'SDL_VIDEODRIVER':'dummy', 'SDL_AUDIODRIVER':'dummy'}
    return clean, package, worker, runtime


def available(plan, directory):
    check_window(plan)
    if dt.datetime.now(dt.timezone.utc) >= dt.datetime.fromisoformat(plan['simulation_deadline_utc']):
        raise RuntimeError('Simulation deadline reached')
    if json.loads((directory/'budget.json').read_text())['actions'] >= plan['max_actions']:
        raise RuntimeError('Cohort action cap reached')


def episode(case, plan, plan_path, execution):
    directory = plan_path.parent
    out = directory/case['id']; out.mkdir(mode=0o700)
    clean, package, worker, runtime = execution
    started = time.perf_counter(); child = env = None
    used = raw_ticks = reset_ticks = stagnation = 0
    act_ms = []; rss = []; sim_wall = 0.; events = []; pending = []
    history = deque(maxlen=plan['pre_event_steps']+plan['stagnation_steps'])
    counters = Counter(); response = {}; info = {}; stop = False
    result = {'id':case['id'], 'stratum':case['stratum'], 'track_id':case['track_id'],
              'status':'RESOURCE_CENSORED', 'failure_type':None, 'events':[],
              'road_geometry_sha256':case['road_geometry_sha256'], 'policy_changed':False,
              'episode_count':1, 'retries':0}

    def event(kind, onset, trigger):
        rows = [r for r in history if r['step'] >= onset-plan['pre_event_steps']]
        record = {'kind':kind, 'onset_step':onset, 'trigger_step':trigger,
                  'pre_event_steps_requested':plan['pre_event_steps'],
                  'post_trigger_steps_requested':plan['post_event_steps'], 'rows':rows,
                  'pre_event_steps_saved':sum(r['step'] < onset for r in rows),
                  'post_trigger_steps_saved':0}
        events.append(record); pending.append(record)

    try:
        available(plan, directory)
        child = PipeWorker([sys.executable, '-I', '-B', str(worker), str(package)], clean, runtime)
        result.update(worker_ready=child.ready, cold_start_ms=child.cold_start_ms)
        available(plan, directory); env = make_env(); reset_start = time.perf_counter()
        obs, _ = env.reset(seed=case['seed'], options={'track_id':case['track_id']})
        result['reset_environment_wall_s'] = time.perf_counter()-reset_start
        reset_ticks = round(env.unwrapped.t*50); assert reset_ticks == 51
        observation_contract(obs)
        geometry = array_sha(env.unwrapped.track)
        obstacles = [{'id':i, 'position':list(o.position), 'radius':float(o.fixtures[0].shape.radius)}
                     for i, o in enumerate(env.unwrapped.obstacles)]
        physical = array_sha([[*o['position'], o['radius']] for o in obstacles])
        assert geometry == case['road_geometry_sha256']
        assert physical == case['expected_physical_obstacles_sha256']
        write(out/'scene.json', {'track':env.unwrapped.track, 'obstacles':obstacles,
                                'geometry_sha256':geometry, 'physical_obstacle_sha256':physical,
                                'frame':'world metres; body x-right,y-forward'})
        write(out/'started.json', {'initial':truth(env), 'initial_observation_sha256':sha_bytes(obs),
                                  'geometry_sha256':geometry, 'obstacles_sha256':physical,
                                  'plan_sha256':sha(plan_path)})
        reset, reset_ms = child.call('reset', obs)
        assert reset['ok'] and reset_ms <= 5000
        result['reset_including_IPC_ms'] = reset_ms
        raw_records = []; original_step = env.env.step

        def observer(action):
            before = truth(env); hits = [o.userData.hit for o in env.unwrapped.obstacles]
            value = original_step(action); after = truth(env)
            raw_records.append({'before_time':before['time'], 'after_time':after['time'],
                                'before':before, 'after':after, 'collision':bool(value[4].get('collision', False)),
                                'new_hit_obstacle_ids':[i for i, o in enumerate(env.unwrapped.obstacles)
                                                        if not hits[i] and o.userData.hit]})
            return value

        env.env.step = observer
        budget = Budget(plan_path, case['id']); sequence = hashlib.sha256()
        for _ in range(plan['stage_budgets'][case['id']]):
            available(plan, directory)
            before = truth(env); input_sha = sha_bytes(obs)
            response, duration = child.call('act', obs)
            action = np.asarray(response['action'], dtype=np.float32)
            assert action.shape == (3,) and np.isfinite(action).all()
            assert np.all(action >= [-1,0,0]) and np.all(action <= [1,1,1])
            assert duration <= 5000 and response['rss_mib']*1024*1024 <= 1_024_000_000
            available(plan, directory); raw_records.clear(); sim_start = time.perf_counter()
            obs, _, ended, truncated, info = budget.step(env, action)
            sim_wall += time.perf_counter()-sim_start; used += 1; raw_ticks += len(raw_records)
            observation_contract(obs); after = truth(env); sequence.update(action.tobytes())
            act_ms.append(duration); rss.append(response['rss_mib'])
            telemetry = response['route_telemetry']
            row = {'step':used, 'before_time':before['time'], 'after_time':after['time'],
                   'observation_sha256_before':input_sha, 'observation_sha256_after':sha_bytes(obs),
                   'action':action.tolist(), 'route_telemetry':telemetry,
                   'cap_diagnostic':response['cap_diagnostic'], 'original_calls':response['original_calls'],
                   'previous_steer_after':response['previous_steer_after'],
                   'truth_before':before, 'truth_after':after, 'raw_intervals':list(raw_records),
                   'collision':bool(info['collision']), 'terminated':bool(ended), 'truncated':bool(truncated),
                   'retire_reason':info['retire_reason'], 'act_including_IPC_ms':duration, 'rss_mib':response['rss_mib']}
            for saved in list(pending):
                saved['rows'].append(row); saved['post_trigger_steps_saved'] += 1
                if saved['post_trigger_steps_saved'] == plan['post_event_steps']: pending.remove(saved)
            history.append(row)
            stagnation = stagnation+1 if after['unique_tiles'] == before['unique_tiles'] else 0
            if info['collision'] and not any(e['kind'] == 'first_contact' for e in events):
                event('first_contact', used, used)
            if stagnation == plan['stagnation_steps'] and not any(e['kind'] == 'first_progress_stagnation' for e in events):
                event('first_progress_stagnation', used-plan['stagnation_steps']+1, used)
            counters['collision_steps'] += int(info['collision'])
            counters['no_new_tile_steps'] += int(after['unique_tiles'] == before['unique_tiles'])
            counters['stagnation_episode_onsets'] += int(stagnation == plan['stagnation_steps'])
            counters['fallback_steps'] += int(telemetry['actual_fallback_called'])
            counters['empty_current_detection_steps'] += int(not telemetry['current_detections'])
            counters['max_no_new_tile_streak'] = max(counters['max_no_new_tile_streak'], stagnation)
            if ended or truncated:
                completed = env.unwrapped.finish_time_s is not None
                result.update(status='COMPLETE' if completed else 'DNF', completed=completed,
                              native_terminated=bool(ended), native_truncated=bool(truncated),
                              failure_type=None if completed else (info['retire_reason'] or ('native_full_horizon' if truncated else 'native_terminal')),
                              official_lap_ms=round((env.unwrapped.finish_time_s-1.02)*1000) if completed else None)
                break
        else:
            raise RuntimeError('Per-case ceiling without native endpoint')
        result['action_sequence_sha256'] = sequence.hexdigest()
    except Exception as error:
        stop = True
        result.update(status='RESOURCE_CENSORED', completed=False, failure_type='technical_or_budget_boundary',
                      error=repr(error), traceback=traceback.format_exc(), official_lap_ms=None)
    finally:
        for saved in events:
            saved['post_window_complete'] = saved['post_trigger_steps_saved'] == plan['post_event_steps']
            saved['pre_window_complete'] = saved['pre_event_steps_saved'] == plan['pre_event_steps']
            target = out/(saved['kind']+'.json'); write(target, saved)
            result['events'].append({k:v for k,v in saved.items() if k != 'rows'} | {'relative_path':str(target.relative_to(directory)), 'sha256':sha(target)})
        if history: write(out/'endpoint-window.json', {'rows':list(history)[-plan['pre_event_steps']:], 'purpose':'supplement only; earliest event windows remain separate'})
        if env:
            raw = env.unwrapped
            result.update(unique_tiles=raw.tile_visited_count, total_tiles=len(raw.track),
                          official_progress=float(info.get('progress', raw.tile_visited_count/len(raw.track))),
                          damage=env.damage.damage, final_time_s=raw.t, endpoint=truth(env))
            env.close()
        if child:
            result['worker_reaping'] = child.close()
            result['supervisor_peak_rss_bytes'] = child.observed_peak_rss_bytes
            if not result['worker_reaping']['process_reaped']:
                result.update(status='RESOURCE_CENSORED', completed=False, failure_type='worker_reaping_failure'); stop = True
        ledger = json.loads((directory/'budget.json').read_text())
        result.update(charged_wrapper_actions=ledger['stages'].get(case['id'],0), successful_wrapper_steps=used,
                      raw_step_ticks=raw_ticks, raw_reset_ticks=reset_ticks, sum_sim_step_wall_s=sim_wall,
                      max_act_including_IPC_ms=max(act_ms, default=None), peak_actor_RSS_MiB=max(rss, default=None),
                      actor_CPU_s=response.get('actor_cumulative_CPU_s'), counters=dict(counters), wall_s=time.perf_counter()-started)
        write(out/'result.json', result)
    return result, stop


def sha_bytes(array):
    return hashlib.sha256(array.tobytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args(); path = args.plan.resolve(); directory = path.parent
    plan = json.loads(path.read_text()); started = time.perf_counter()
    assert sha(path) == (directory/'plan.sha256').read_text().split()[0]
    for source, expected in plan['source_sha256'].items(): assert sha(Path(source)) == expected, source
    split = json.loads(Path(plan['split_path']).read_text())
    cases = split['cases']; assert [c['id'] for c in cases] == split['ordered_cases']
    assert len(cases) == plan['expected_conditions'] and len({c['seed'] for c in cases}) == len(cases)
    execution = clone(plan, directory); results = []; stop_reason = None
    for case in cases:
        if stop_reason is None:
            try: available(plan, directory)
            except Exception as error: stop_reason = repr(error)
        if stop_reason is not None:
            result = {'id':case['id'], 'stratum':case['stratum'], 'track_id':case['track_id'],
                      'status':'UNEXECUTED', 'failure_type':None, 'official_lap_ms':None,
                      'official_progress':None, 'unique_tiles':None, 'total_tiles':case['road_point_count'],
                      'charged_wrapper_actions':0, 'episode_count':0, 'retries':0, 'reason':stop_reason}
        else:
            result, stop = episode(case, plan, path, execution)
            if stop: stop_reason = result.get('error', result['failure_type'])
        results.append(result)
        write(directory/'cohort-results.json', {'results':results, 'stop_reason':stop_reason,
                                               'status_counts':dict(Counter(r['status'] for r in results)),
                                               'plan_sha256':sha(path), 'wall_s':time.perf_counter()-started})
        print(json.dumps({k:result.get(k) for k in ('id','status','failure_type','official_lap_ms','official_progress','charged_wrapper_actions','error')}), flush=True)
    return int(stop_reason is not None)


if __name__ == '__main__': sys.exit(main())
