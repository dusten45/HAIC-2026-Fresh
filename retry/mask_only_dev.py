"""Two preregistered DEV questions for a frozen mask-only intervention.

Reuse verified historical champion endpoints; execute the candidate once per
condition. A normal driving failure never suppresses the second comparison.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import time

import numpy as np

from retry.frozen_paired_evaluation import episode, native_window, sha, verify_files, write
from retry.paired_audit_gate import claim_once


def recorded_episode(plan_path, plan, case):
    """Read-only evaluator records; neither observations nor actions are edited."""
    from retry import diagnose, frozen_composite_runtime as runtime
    from retry.full_route_reproduction import truth
    original_factory, original_prepare = diagnose.make_env, runtime.prepare
    frames, actions, trace, policy = [], [], [], []
    initial_record = {}
    reference = json.loads(Path(case['reference_started_path']).read_text())
    expected_truth = reference['initial']
    expected_obs = reference['initial_observation_sha256']

    def factory(*args, **kwargs):
        env = original_factory(*args, **kwargs)
        original_reset, original_step = env.reset, env.step

        def reset(*args, **kwargs):
            result = original_reset(*args, **kwargs)
            obs = result[0]
            current = truth(env)
            assert {key: current[key] for key in expected_truth} == expected_truth
            assert hashlib.sha256(obs.tobytes()).hexdigest() == expected_obs
            assert not frames
            frames.append(np.rint(obs[-1] * 255).astype(np.uint8))
            initial_record.update(initial=current, initial_observation_sha256=expected_obs,
                                  compared_prior_state_fields=sorted(expected_truth))
            return result

        def step(action):
            before = truth(env)
            saved = np.asarray(action, dtype=np.float32).copy()
            result = original_step(action)
            obs, reward, ended, truncated, info = result
            assert np.array_equal(action, saved)
            actions.append(saved)
            frames.append(np.rint(obs[-1] * 255).astype(np.uint8))
            trace.append({'step': len(actions), 'truth_before': before,
                          'truth_after': truth(env), 'action': saved.tolist(),
                          'observation_sha256_after': hashlib.sha256(obs.tobytes()).hexdigest(),
                          'reward': float(reward), 'collision': bool(info['collision']),
                          'terminated': bool(ended), 'truncated': bool(truncated),
                          'retire_reason': info['retire_reason'], 'finish_time_s': info['finish_time_s']})
            return result

        env.reset, env.step = reset, step
        return env

    def prepare(*args, **kwargs):
        worker = original_prepare(*args, **kwargs)
        original_call = worker.call

        def call(operation, obs):
            response, elapsed = original_call(operation, obs)
            policy.append({'operation': operation,
                           'input_observation_sha256': hashlib.sha256(obs.tobytes()).hexdigest(),
                           'response': response, 'IPC_ms': elapsed})
            return response, elapsed

        worker.call = call
        return worker

    diagnose.make_env, runtime.prepare = factory, prepare
    started = time.perf_counter()
    try:
        result = episode(plan_path, plan, case, 'B', {})
    finally:
        diagnose.make_env, runtime.prepare = original_factory, original_prepare
    directory = plan_path.parent / 'runs' / (case['id'] + '__B')
    frame_array = np.asarray(frames, dtype=np.uint8)
    action_array = np.asarray(actions, dtype=np.float32).reshape(-1, 3)
    if 'error' not in result:
        assert len(frames) == len(actions) + 1
        assert len(actions) == result['successful_wrapper_steps']
        assert hashlib.sha256(action_array.tobytes()).hexdigest() == result['action_sequence_sha256']
        sequence = hashlib.sha256()
        for index in range(len(frames)):
            obs = frame_array[np.maximum(0, np.arange(index - 3, index + 1))].astype(np.float32) / 255
            sequence.update(obs.tobytes())
            expected = expected_obs if index == 0 else trace[index - 1]['observation_sha256_after']
            assert hashlib.sha256(obs.tobytes()).hexdigest() == expected
        assert sequence.hexdigest() == result['observation_sequence_sha256']
    np.savez_compressed(directory / 'dev-pixels-actions.npz', frames=frame_array, actions=action_array)
    (directory / 'dev-pixels-actions.npz').chmod(0o600)
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
        'stream_hashes_exact': 'error' not in result,
        'initial_recorded_state_fields_compared': sorted(expected_truth),
        'record_sha256': {name: sha(directory / name) for name in
                          ('dev-pixels-actions.npz', 'dev-trace.jsonl', 'dev-policy.jsonl', 'dev-started.json')},
    }, exclusive=True)
    return result


def run(plan_path):
    plan_path = Path(plan_path).resolve()
    plan = json.loads(plan_path.read_text())
    assert sha(plan_path) == plan_path.with_suffix('.sha256').read_text().split()[0]
    assert plan['split_kind'] == 'DEV' and plan['max_actions'] == 4000 and plan['max_steps'] == 2000
    assert len(plan['cases']) == 2 and list(plan['arms']) == ['B']
    assert [case['stage'] for case in plan['cases']] == [106, 107]
    assert plan['arms']['B']['intervention'] == 'road_mask_only'
    assert plan['arms']['B']['constants']['mask-config.json']['source'] == 'student'
    assert plan['stage_budgets'] == {case['id'] + '__B': 2000 for case in plan['cases']}
    verify_files(plan['source_sha256'])
    verify_files(plan['runtime_sha256'])
    assert plan['source_sha256'][str(Path(__file__).resolve())] == sha(__file__)
    assert sha(plan['project_budget_path']) == plan['project_budget_sha256']
    budget = json.loads(Path(plan['project_budget_path']).read_text())
    assert budget['research_remaining'] >= 4000 and budget['final_reserve_used'] == 0
    assert budget['final_reserved_actions'] == plan['reserved_actions']
    assert shutil.disk_usage(plan_path.parent).free >= plan['minimum_free_disk_bytes']
    claim_once(plan_path)
    write(plan_path.parent / 'budget.json', {'started_epoch': time.time(), 'actions': 0, 'stages': {}}, exclusive=True)
    results = []
    for index, case in enumerate(plan['cases']):
        native_window(plan)
        remaining_s = (dt.datetime.fromisoformat(plan['simulation_deadline_utc'])
                       - dt.datetime.now(dt.timezone.utc)).total_seconds()
        assert remaining_s >= (len(plan['cases']) - index) * plan['conservative_episode_wall_s']
        assert shutil.disk_usage(plan_path.parent).free >= plan['minimum_free_disk_bytes']
        result = recorded_episode(plan_path, plan, case)
        results.append(result)
        write(plan_path.parent / 'progress.json', {'finished': len(results),
                                                  'actions': sum(r['charged_wrapper_actions'] for r in results)})
        print(json.dumps({'stage': case['stage'], 'finished': len(results),
                          'charged_actions': result['charged_wrapper_actions'],
                          'technical_error': result.get('error')}), flush=True)
        if 'error' in result:
            break
        # Normal DNF and a nonterminal action cap do not hide the next condition.
    report = {'status': 'PASS' if len(results) == 2 and not any('error' in r for r in results) else 'INCOMPLETE',
              'episodes': results, 'actions': sum(r['charged_wrapper_actions'] for r in results),
              'performance_promotion': False, 'baseline_native_runs': 0, 'automatic_retry': False}
    write(plan_path.parent / 'paired-dev-result.json', report, exclusive=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    result = run(parser.parse_args().plan)
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
