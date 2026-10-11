"""Frozen HUD-feedback generalization on two new paired DEV conditions.

The participant receives only reset/act and official pixels. The clean worker provides actions only;
this recorder makes no extra policy/model calls. Configuration type champion
selects the standalone archive adapter and does not mean candidate adoption.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import time

import numpy as np

from retry.completion_first_aggregate import summarize
from retry.frozen_paired_evaluation import (
    episode, native_window, performance_verdict, sha, verify_files, write,
)
from retry.paired_audit_gate import claim_once, verify_readiness
from retry.near_curvature_dev import action_dwell, finalize_action_dwell


def _hash(array):
    return hashlib.sha256(array.tobytes()).hexdigest()


def recorded_episode(plan_path, plan, case, arm, initial_pairs):
    """Record the actual paired episode without changing actions or inputs."""
    from retry import diagnose, frozen_composite_runtime as runtime
    from retry.full_route_reproduction import truth

    original_factory, original_prepare = diagnose.make_env, runtime.prepare
    frames, actions, trace, policy = [], [], [], []
    initial_record = {}
    result = None
    directory = plan_path.parent / 'runs' / (case['id'] + '__' + arm)
    started = time.perf_counter()

    def factory(*args, **kwargs):
        env = original_factory(*args, **kwargs)
        original_reset, original_step = env.reset, env.step

        def reset(*args, **kwargs):
            output = original_reset(*args, **kwargs)
            obs = output[0]
            assert not frames
            frame = np.rint(obs[-1] * 255).astype(np.uint8)
            assert np.array_equal(obs, np.repeat(frame[None], 4, axis=0).astype(np.float32) / 255)
            frames.append(frame)
            initial_record.update(initial=truth(env), initial_observation_sha256=_hash(obs))
            return output

        def step(action):
            before = truth(env)
            index = len(actions)
            obs_before = np.stack([frames[max(0, j)] for j in range(index - 3, index + 1)]).astype(np.float32) / 255
            assert policy and policy[-1]['operation'] == 'act'
            current = policy[-1]
            assert current['input_observation_sha256'] == _hash(obs_before)
            saved = np.asarray(action, dtype=np.float32).copy()
            assert saved.tobytes() == np.asarray(current['response']['action'], np.float32).tobytes()
            output = original_step(action)
            obs, reward, ended, truncated, info = output
            assert np.array_equal(action, saved)
            after = truth(env)
            actions.append(saved)
            frames.append(np.rint(obs[-1] * 255).astype(np.uint8))
            finish = info['finish_time_s']
            trace.append({
                'step': len(actions), 'truth_before': before, 'truth_after': after,
                'action': saved.tolist(), 'observation_sha256_before': _hash(obs_before),
                'observation_sha256_after': _hash(obs), 'reward': float(reward),
                'collision': bool(info['collision']), 'terminated': bool(ended),
                'truncated': bool(truncated), 'retire_reason': info['retire_reason'],
                'finish_time_s': finish,
                'raw_duration_s': after['time'] - before['time'],
                'action_dwell_s': action_dwell(before['time'], after['time'], finish),
                'act_including_IPC_ms': current['IPC_ms'],
            })
            return output

        env.reset, env.step = reset, step
        return env

    def prepare(*args, **kwargs):
        worker = original_prepare(*args, **kwargs)
        original_call = worker.call

        def call(operation, obs):
            response, elapsed = original_call(operation, obs)
            policy.append({'operation': operation, 'input_observation_sha256': _hash(obs),
                           'response': response, 'IPC_ms': elapsed})
            return response, elapsed

        worker.call = call
        return worker

    diagnose.make_env, runtime.prepare = factory, prepare
    validation_error = None
    try:
        result = episode(plan_path, plan, case, arm, initial_pairs)
    finally:
        diagnose.make_env, runtime.prepare = original_factory, original_prepare
        # Preserve available evidence even after a technical exception. The
        # episode owns worker/environment cleanup and the charged-step ledger.
        if directory.exists():
            frame_array = np.asarray(frames, dtype=np.uint8).reshape(-1, 84, 84)
            action_array = np.asarray(actions, dtype=np.float32).reshape(-1, 3)
            exact = False
            if result is not None and 'error' not in result:
                try:
                    finalize_action_dwell(trace, result)
                    assert len(frames) == len(actions) + 1
                    assert len(actions) == result['successful_wrapper_steps'] == len(trace)
                    assert len(policy) == len(actions) + 1 and policy[0]['operation'] == 'reset'
                    assert _hash(action_array) == result['action_sequence_sha256']
                    sequence = hashlib.sha256()
                    for i in range(len(frames)):
                        obs = frame_array[np.maximum(0, np.arange(i - 3, i + 1))].astype(np.float32) / 255
                        digest = _hash(obs)
                        sequence.update(obs.tobytes())
                        expected = initial_record['initial_observation_sha256'] if i == 0 else trace[i - 1]['observation_sha256_after']
                        assert digest == expected
                        if i < len(actions):
                            assert policy[i + 1]['input_observation_sha256'] == digest
                    assert sequence.hexdigest() == result['observation_sequence_sha256']
                    exact = True
                except Exception as error:
                    validation_error = type(error).__name__ + ': ' + str(error)
            target = directory / 'dev-pixels-actions.npz'
            with target.open('xb') as stream:
                np.savez_compressed(stream, frames=frame_array, actions=action_array)
            target.chmod(0o600)
            for name, rows in [('dev-trace.jsonl', trace), ('dev-policy.jsonl', policy)]:
                with (directory / name).open('x') as stream:
                    for row in rows:
                        stream.write(json.dumps(row, allow_nan=False) + '\n')
                (directory / name).chmod(0o600)
            write(directory / 'dev-started.json', initial_record, exclusive=True)
            write(directory / 'record-receipt.json', {
                'wall_including_record_write_s': time.perf_counter() - started,
                'frames': len(frames), 'steps': len(actions), 'policy_responses': len(policy),
                'extra_env_policy_model_calls': 0, 'GT_sent_to_policy': False,
                'stream_hashes_exact': exact, 'record_validation_error': validation_error,
                'raw_duration_sum_s': sum(row['raw_duration_s'] for row in trace),
                'finish_clipped_action_dwell_sum_s': sum(row['action_dwell_s'] for row in trace),
                'record_sha256': {name: sha(directory / name) for name in (
                    'dev-pixels-actions.npz', 'dev-trace.jsonl', 'dev-policy.jsonl', 'dev-started.json')},
            }, exclusive=True)
    if validation_error is not None:
        raise RuntimeError('Saved DEV record validation failed: ' + validation_error)
    return result


def _capacity(plan, directory, remaining_episodes):
    native_window(plan)
    remaining = (dt.datetime.fromisoformat(plan['simulation_deadline_utc'])
                 - dt.datetime.now(dt.timezone.utc)).total_seconds()
    assert plan['conservative_episode_wall_s'] > 0
    assert remaining >= remaining_episodes * plan['conservative_episode_wall_s']
    assert shutil.disk_usage(directory).free >= plan['minimum_free_disk_bytes']


def run(plan_path):
    plan_path = Path(plan_path).resolve()
    directory = plan_path.parent
    plan = json.loads(plan_path.read_text())
    assert sha(plan_path) == plan_path.with_suffix('.sha256').read_text().split()[0]
    assert plan['experiment_kind'] == 'hud_feedback_generalization' and plan['split_kind'] == 'DEV'
    assert plan['no_promotion'] is True
    assert plan['max_actions'] == 8000 and plan['max_steps'] == 2000
    assert len(plan['cases']) == 2 and len({case['id'] for case in plan['cases']}) == 2
    assert list(plan['arms']) == ['A', 'B']
    assert all(config['type'] == 'champion' for config in plan['arms'].values())
    assert plan['arms']['A']['archive_sha256'] == '6d162d961041333eeddfbb8fc749a5cbeb3e562c96b93144c2aa2816e3b7ea22'
    assert plan['arms']['B']['archive_sha256'] == 'b8c40bcff8ad9eea60e21755950b77235c22a0d7df89eb74f08148bbb0c9890c'
    assert all(not config.get('assets') and not config.get('constants') for config in plan['arms'].values())
    clean_worker = Path(__file__).resolve().with_name('clean_pixel_worker.py')
    assert all(Path(config['worker_path']).resolve() == clean_worker and config['worker_sha256'] == sha(clean_worker)
               for config in plan['arms'].values())
    assert [case['arm_order'] for case in plan['cases']] == [['A', 'B'], ['B', 'A']]
    roles = [case['id'] + '__' + arm for case in plan['cases'] for arm in case['arm_order']]
    assert plan['stage_budgets'] == {role: 2000 for role in roles}
    assert plan['ledger_relative_path'] == 'budget.json'
    assert plan['deadline_utc'] == plan['simulation_deadline_utc'] == plan['authorization_end_utc']
    authorized_seconds = (dt.datetime.fromisoformat(plan['authorization_end_utc'])
                          - dt.datetime.now(dt.timezone.utc)).total_seconds()
    assert plan['max_experiment_wall_s'] >= authorized_seconds > 0
    verify_files(plan['source_sha256'])
    verify_files(plan['runtime_sha256'])
    assert plan['source_sha256'][str(Path(__file__).resolve())] == sha(__file__)
    manifest = str(Path(plan['champion_manifest_path']).resolve())
    assert plan['source_sha256'][manifest] == sha(manifest)
    assert sha(plan['selection_path']) == plan['selection_sha256']
    selection = json.loads(Path(plan['selection_path']).read_text())
    assert selection['status'] == 'PASS' and selection['all_lineages_unseen'] is True
    assert selection['ordered_case_ids'] == [case['id'] for case in plan['cases']]
    assert selection['road_geometry_sha256'] == [case['road_geometry_sha256'] for case in plan['cases']]
    assert selection['physical_obstacles_sha256'] == [case['expected_physical_obstacles_sha256'] for case in plan['cases']]
    assert len(set(selection['road_geometry_sha256'])) == len(set(selection['physical_obstacles_sha256'])) == 2
    assert sha(plan['allocation_path']) == plan['allocation_sha256']
    allocation = json.loads(Path(plan['allocation_path']).read_text())
    assert allocation['B_operating_cap'] == plan['B_operating_cap'] == 682000
    assert allocation['research_remaining'] >= 8000 and allocation['final_reserve_used'] == 0
    assert allocation['final_reserved_actions'] == plan['reserved_actions'] == 84000
    assert sha(plan['qualification_path']) == plan['qualification_sha256']
    qualification = json.loads(Path(plan['qualification_path']).read_text())
    assert qualification['status'] == 'PASS'
    assert qualification['arm_configuration_sha256'] == {arm: hashlib.sha256(
        json.dumps(config, sort_keys=True).encode()).hexdigest() for arm, config in plan['arms'].items()}
    verify_readiness(plan_path)
    _capacity(plan, directory, 4)
    assert not (directory / 'budget.json').exists()
    claim_once(plan_path)
    write(directory / 'budget.json', {'started_epoch': time.time(), 'actions': 0, 'stages': {}}, exclusive=True)
    results, launched, initial_pairs, records = [], [], {}, {}
    termination = None
    run_started, run_CPU_started = time.perf_counter(), time.process_time()
    try:
        for case in plan['cases']:
            for arm in case['arm_order']:
                _capacity(plan, directory, 4 - len(launched))
                role = case['id'] + '__' + arm
                launched.append(role)
                result = recorded_episode(plan_path, plan, case, arm, initial_pairs)
                results.append(result)
                records[(case['id'], arm)] = result
                assert result['arm'] == arm
                if 'error' not in result:
                    assert result['reaping']['process_reaped'] and result['reaping']['actor_pids_absent']
                write(directory / 'progress.json', {'finished': len(results),
                      'actions': sum(row['charged_wrapper_actions'] for row in results)})
                print(json.dumps({'finished': len(results), 'planned': 4,
                                  'charged_actions': result['charged_wrapper_actions'],
                                  'technical_error': 'error' in result}), flush=True)
                if 'error' in result:
                    raise RuntimeError('Technical failure; remaining roles not executed')
                # Normal DNF and a declared action-cap censor do not stop collection.
    except Exception as error:
        termination = type(error).__name__ + ': ' + str(error)
    ledger = json.loads((directory / 'budget.json').read_text())
    assert 0 <= ledger['actions'] <= 8000 and set(ledger['stages']) <= set(roles)
    assert all(0 <= used <= 2000 for used in ledger['stages'].values())
    assert sum(ledger['stages'].values()) == ledger['actions']
    returned = sum(row['charged_wrapper_actions'] for row in results)
    if returned != ledger['actions']:
        termination = termination or 'Ledger includes actions without a returned episode record'
    try:
        verify_files(plan['source_sha256'])
        verify_files(plan['runtime_sha256'])
        assert sha(plan['allocation_path']) == plan['allocation_sha256']
        assert sha(plan['selection_path']) == plan['selection_sha256']
        assert sha(plan['qualification_path']) == plan['qualification_sha256']
    except Exception as error:
        termination = termination or 'Preservation: ' + type(error).__name__ + ': ' + str(error)
    pairs = [{'case': case['id'], 'baseline': records.get((case['id'], 'A')),
              'candidate': records.get((case['id'], 'B'))} for case in plan['cases']]
    summary = summarize(pairs, [case['id'] for case in plan['cases']])
    verdict = performance_verdict(summary)
    if termination is not None:
        verdict = 'KEEP_CHAMPION_INCONCLUSIVE_COHORT'
    report = {'status': 'PASS' if len(results) == 4 and termination is None else 'INCOMPLETE',
              'experiment_kind': 'hud_feedback_generalization', 'episodes': results,
              'actions': ledger['actions'], 'returned_episode_record_actions': returned,
              'launched_roles': launched, 'unexecuted_roles': [role for role in roles if role not in launched],
              'termination': termination, 'summary': summary,
              'descriptive_performance_verdict': verdict, 'descriptive_only': True,
              'no_promotion': True, 'performance_promotion': False, 'automatic_retry': False,
              'baseline_native_runs': sum(row['arm'] == 'A' for row in results),
              'candidate_native_runs': sum(row['arm'] == 'B' for row in results),
              'wall_including_records_s': time.perf_counter() - run_started,
              'evaluator_CPU_including_records_s': time.process_time() - run_CPU_started,
              'configuration_type_champion_means_adoption': False}
    write(directory / 'paired-dev-result.json', report, exclusive=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    result = run(parser.parse_args().plan)
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
