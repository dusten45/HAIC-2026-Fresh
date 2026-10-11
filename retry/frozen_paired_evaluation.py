"""One-use, completion-first paired evaluation of frozen pixel workers.

The private plan supplies immutable configurations and a fresh registered split.
Only endpoint aggregates, resource measurements and rolling hashes are retained.
Normal driving failures never change the predeclared order or remaining cases.
"""
import argparse
import base64
import datetime as dt
import hashlib
import json
from pathlib import Path
import resource
import shutil
import sys
import time

from retry.completion_first_aggregate import summarize
from retry.paired_audit_gate import claim_once


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value, *, exclusive=False):
    with Path(path).open('x' if exclusive else 'w') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')
    Path(path).chmod(0o600)


def performance_verdict(summary):
    """Apply the frozen directional rule, without a minimum improvement percent."""
    if not summary['cohort_complete']:
        return 'KEEP_CHAMPION_INCONCLUSIVE_COHORT'
    if summary['counts']['lost_completion']:
        return 'KEEP_CHAMPION_COMPLETION_LOSS'
    if summary['counts']['new_completion']:
        return 'COMPARISON_PASS_COMPLETION_GAIN'
    if summary['counts']['common_completed'] < 2:
        return 'KEEP_CHAMPION_INSUFFICIENT_COMMON_COMPLETIONS'
    if (summary['common_completion_median_lap_delta_ms'] < 0
            and summary['common_completion_mean_lap_ratio'] < 1):
        return 'COMPARISON_PASS_PAIRED_LAP_GAIN'
    return 'KEEP_CHAMPION_MIXED_OR_NO_LAP_GAIN'


def verify_files(mapping):
    for name, wanted in mapping.items():
        assert sha(name) == wanted, 'Frozen file changed: ' + name


def native_window(plan):
    now = dt.datetime.now(dt.timezone.utc)
    assert dt.datetime.fromisoformat(plan['start_utc']) <= now
    assert now < dt.datetime.fromisoformat(plan['simulation_deadline_utc'])
    assert now < dt.datetime.fromisoformat(plan['deadline_utc'])


def episode(plan_path, plan, case, arm, initial_pairs):
    # The simulator is imported only by the evaluator, never by an actor.
    import numpy as np
    from retry.diagnose import Budget, make_env
    from retry.evaluate import observation_contract
    from retry.frozen_composite_runtime import prepare, validate_response
    from retry.full_route_reproduction import truth

    role = case['id'] + '__' + arm
    directory = plan_path.parent / 'runs' / role
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    config = plan['arms'][arm]
    started = time.perf_counter()
    cpu_start = time.process_time()
    worker = env = None
    used = raw_ticks = reset_ticks = 0
    reset_calls = act_calls = 0
    ended = truncated = False
    action_hash, observation_hash, mask_hash = (hashlib.sha256() for _ in range(3))
    latencies, actor_cpu, sim_wall = [], 0.0, 0.0
    result = {'case': case['id'], 'arm': arm, 'role': role,
              'completed': False, 'terminal_observed': False, 'censored': True,
              'lap_ms': None, 'unique_tiles': 0, 'total_tiles': 0, 'damage': 0,
              'retire_reason': 'technical_or_resource_stop',
              'saved_video_frames': 0, 'saved_trajectory_rows': 0,
              'saved_policy_telemetry_rows': 0, 'oracle_inputs_to_policy': False}
    try:
        native_window(plan)
        verify_files(plan['source_sha256'])
        verify_files(plan['runtime_sha256'])
        worker = prepare(config, directory / 'cpu', plan['sandbox_path'])
        assert worker.cold_start_ms <= 10000
        budget = Budget(plan_path, role)
        native_window(plan)
        env = make_env()
        before = time.perf_counter()
        obs, _ = env.reset(seed=case['seed'], options={'track_id': case['track_id']})
        result['environment_reset_wall_s'] = time.perf_counter() - before
        observation_contract(obs)
        assert all(np.array_equal(obs[0], frame) for frame in obs[1:])
        reset_ticks = round(env.unwrapped.t * 50)
        assert reset_ticks == 51
        start_time = env.unwrapped.t
        geometry = hashlib.sha256(np.asarray(env.unwrapped.track, dtype='<f8').tobytes()).hexdigest()
        obstacles = [[*map(float, item.position), float(item.fixtures[0].shape.radius)]
                     for item in env.unwrapped.obstacles]
        obstacles_hash = hashlib.sha256(np.asarray(obstacles, dtype='<f8').tobytes()).hexdigest()
        assert geometry == case['road_geometry_sha256']
        assert obstacles_hash == case['expected_physical_obstacles_sha256']
        initial = {'road_geometry_sha256': geometry, 'physical_obstacles_sha256': obstacles_hash,
                   'state_sha256': hashlib.sha256(json.dumps(truth(env), sort_keys=True,
                                                            allow_nan=False).encode()).hexdigest(),
                   'observation_sha256': hashlib.sha256(obs.tobytes()).hexdigest()}
        if case['id'] in initial_pairs:
            assert initial == initial_pairs[case['id']], 'Paired reset differs'
        else:
            initial_pairs[case['id']] = initial
        response, reset_ms = worker.call('reset', obs)
        reset_calls += 1
        actor_cpu = max(actor_cpu, response['actor_cumulative_CPU_s'])
        validate_response(response, config, obs, 'reset')
        assert reset_ms <= 5000
        if config['type'] == 'student':
            mask_hash.update(base64.b64decode(response['student_mask_base64']))
        observation_hash.update(obs.tobytes())
        result.update(initial=initial, actor_reset_including_IPC_ms=reset_ms,
                      cold_start_ms=worker.cold_start_ms, worker_ready=worker.ready)
        reason = 'resource_action_cap_censored'
        for _ in range(plan['max_steps']):
            native_window(plan)
            response, act_ms = worker.call('act', obs)
            act_calls += 1
            actor_cpu = max(actor_cpu, response['actor_cumulative_CPU_s'])
            action = validate_response(response, config, obs, 'act')
            assert act_ms <= 5000
            if config['type'] == 'student':
                mask_hash.update(base64.b64decode(response['student_mask_base64']))
            previous = obs
            old_time = env.unwrapped.t
            before = time.perf_counter()
            native_window(plan)
            obs, _, ended, truncated, info = budget.step(env, action)
            sim_wall += time.perf_counter() - before
            used += 1
            ticks = round((env.unwrapped.t - old_time) * 50)
            assert 1 <= ticks <= 4 and (ticks == 4 or ended or truncated)
            raw_ticks += ticks
            observation_contract(obs)
            assert np.array_equal(obs[:3], previous[1:])
            observation_hash.update(obs.tobytes())
            action_hash.update(action.tobytes())
            latencies.append(act_ms)
            if ended or truncated:
                reason = info['retire_reason']
                break
        finish = env.unwrapped.finish_time_s
        terminal = bool(ended or truncated)
        assert finish is None or terminal
        result.update(completed=finish is not None, terminal_observed=terminal,
                      censored=not terminal, evaluation_endpoint_observed=terminal,
                      terminated=bool(ended), truncated=bool(truncated), finish_time_s=finish,
                      lap_ms=round((finish - start_time) * 1000) if finish is not None else None,
                      unique_tiles=env.unwrapped.tile_visited_count,
                      total_tiles=len(env.unwrapped.track), damage=env.damage.damage,
                      retire_reason=reason,
                      act_including_IPC_ms={'count': len(latencies),
                                            'median': float(np.median(latencies)),
                                            'p95': float(np.percentile(latencies, 95)),
                                            'max': max(latencies)})
    except Exception as error:
        # Error messages describe execution only; no failed scene is dumped.
        result['error'] = type(error).__name__ + ': ' + str(error)
    finally:
        if worker is not None:
            try:
                result['reaping'] = worker.close()
                if not result['reaping']['process_reaped']:
                    result['error'] = 'Worker process was not reaped'
            except Exception as error:
                result['error'] = 'Reaping: ' + repr(error)
            result['actor_observed_peak_RSS_bytes'] = worker.observed_peak_rss_bytes
        if env is not None:
            env.close()
        ledger = json.loads((plan_path.parent / 'budget.json').read_text())
        charged = ledger['stages'].get(role, 0)
        if charged != used:
            result['error'] = 'Charged actions differ from successful wrapper steps'
        if 'error' in result:
            result.update(completed=False, terminal_observed=False, censored=True)
        result.update(charged_wrapper_actions=charged, successful_wrapper_steps=used,
                      raw_step_ticks=raw_ticks, raw_reset_ticks=reset_ticks,
                      actor_reset_calls=reset_calls, actor_act_calls=act_calls,
                      student_model_calls=reset_calls + act_calls if config['type'] == 'student' else 0,
                      action_sequence_sha256=action_hash.hexdigest(),
                      observation_sequence_sha256=observation_hash.hexdigest(),
                      student_mask_sequence_sha256=mask_hash.hexdigest() if config['type'] == 'student' else None,
                      actor_cumulative_CPU_s=actor_cpu, sum_sim_step_wall_s=sim_wall,
                      evaluator_CPU_s=time.process_time() - cpu_start,
                      evaluator_peak_RSS_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
                      wall_s=time.perf_counter() - started,
                      archive_sha256=config['archive_sha256'],
                      configuration_sha256=hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest())
        write(directory / 'result.json', result, exclusive=True)
    return result


def run(plan_path):
    plan_path = Path(plan_path).resolve()
    directory = plan_path.parent
    plan = json.loads(plan_path.read_text())
    assert sha(plan_path) == plan_path.with_suffix('.sha256').read_text().split()[0]
    assert list(plan['arms']) == ['A', 'B'] and plan['max_steps'] == 2000
    assert plan['max_actions'] == 16000 and len(plan['cases']) == 4
    assert len({case['id'] for case in plan['cases']}) == 4
    roles = {case['id'] + '__' + arm for case in plan['cases'] for arm in ('A', 'B')}
    assert plan['stage_budgets'] == {role: 2000 for role in roles}
    assert [case['arm_order'] for case in plan['cases']] == [['A', 'B'], ['B', 'A'], ['A', 'B'], ['B', 'A']]
    assert plan['source_sha256'][str(Path(__file__).resolve())] == sha(__file__)
    verify_files(plan['source_sha256'])
    verify_files(plan['runtime_sha256'])
    assert sha(plan['allocation_path']) == plan['allocation_sha256']
    allocation = json.loads(Path(plan['allocation_path']).read_text())
    assert allocation['B_operating_cap'] == 666000
    assert allocation['research_remaining'] >= plan['max_actions']
    assert allocation['final_reserved_actions'] == 84000 and allocation['final_reserve_used'] == 0
    assert shutil.disk_usage(directory).free >= plan['minimum_free_disk_bytes']
    claim_once(plan_path)
    started = time.perf_counter()
    write(directory / 'budget.json', {'started_epoch': time.time(), 'actions': 0, 'stages': {}}, exclusive=True)
    launched, records, initial_pairs = [], {}, {}
    termination = None
    try:
        for case in plan['cases']:
            for arm in case['arm_order']:
                native_window(plan)
                remaining_episodes = 8 - len(launched)
                required = remaining_episodes * plan['conservative_episode_wall_s']
                left = (dt.datetime.fromisoformat(plan['simulation_deadline_utc'])
                        - dt.datetime.now(dt.timezone.utc)).total_seconds()
                assert left >= required, 'Remaining batch no longer fits native window'
                assert shutil.disk_usage(directory).free >= plan['minimum_free_disk_bytes']
                role = case['id'] + '__' + arm
                launched.append(role)
                write(directory / 'query-ledger.json', {'state': 'RUNNING_AGGREGATE_UNOPENED',
                                                       'launched_roles': launched, 'final_aggregate_looks': 0})
                record = episode(plan_path, plan, case, arm, initial_pairs)
                records[(case['id'], arm)] = record
                write(directory / 'progress.json', {'episodes_finished': len(records),
                                                    'episodes_launched': len(launched),
                                                    'charged_wrapper_actions': sum(r['charged_wrapper_actions'] for r in records.values()),
                                                    'wall_s': time.perf_counter() - started,
                                                    'lap_damage_completion_inspections': 0})
                print(json.dumps({'episodes_finished': len(records), 'episodes_planned': 8,
                                  'charged_wrapper_actions': record['charged_wrapper_actions']}), flush=True)
                if 'error' in record:
                    raise RuntimeError('Technical failure; no automatic retry: ' + role)
                # A declared per-episode action cap is an observed censor, not a
                # technical fault and not permission to select another condition.
    except Exception as error:
        termination = type(error).__name__ + ': ' + str(error)
    expected_roles = [c['id'] + '__' + a for c in plan['cases'] for a in c['arm_order']]
    pairs = [{'case': case['id'], 'baseline': records.get((case['id'], 'A')),
              'candidate': records.get((case['id'], 'B'))} for case in plan['cases']]
    summary = summarize(pairs, [case['id'] for case in plan['cases']])
    summary.update(performance_verdict=performance_verdict(summary),
                   formal_champion_is_arm='A', frozen_candidate_is_arm='B',
                   promotion_requires_separate_G4_and_artifact_review=True,
                   paired_reset_identity_matches=all(
                       records.get((case['id'], 'A'), {}).get('initial') is not None
                       and records.get((case['id'], 'A'), {}).get('initial')
                       == records.get((case['id'], 'B'), {}).get('initial')
                       for case in plan['cases']),
                   termination=termination, episodes_launched=len(launched),
                   episodes_recorded=len(records), unexecuted_roles=[r for r in expected_roles if r not in launched],
                   actual_wrapper_actions=sum(r['charged_wrapper_actions'] for r in records.values()),
                   raw_step_ticks=sum(r['raw_step_ticks'] for r in records.values()),
                   raw_reset_ticks=sum(r['raw_reset_ticks'] for r in records.values()),
                   wall_s=time.perf_counter() - started,
                   actor_CPU_s=sum(r['actor_cumulative_CPU_s'] for r in records.values()),
                   evaluator_CPU_s=sum(r['evaluator_CPU_s'] for r in records.values()),
                   all_actors_reaped=all(r.get('reaping', {}).get('process_reaped', False) for r in records.values()),
                   simulator_concurrency=1, automatic_retries=0, saved_failure_trace_rows=0,
                   final_aggregate_looks=1, SEALED_opened=False,
                   result_sha256={role: sha(directory / 'runs' / role / 'result.json') for role in launched
                                  if (directory / 'runs' / role / 'result.json').exists()},
                   plan_sha256=sha(plan_path))
    write(directory / 'aggregate.json', summary, exclusive=True)
    write(directory / 'query-ledger.json', {'state': 'CLOSED_SINGLE_AGGREGATE', 'launched_roles': launched,
                                           'final_aggregate_looks': 1, 'aggregate_sha256': sha(directory / 'aggregate.json'),
                                           'detailed_failure_traces_saved': 0, 'retuning_authorized': False})
    print(json.dumps({'closed': True, 'episodes_recorded': len(records),
                      'actual_wrapper_actions': summary['actual_wrapper_actions'],
                      'technical_termination': termination is not None}), flush=True)
    return 1 if termination else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    sys.exit(run(parser.parse_args().plan))
