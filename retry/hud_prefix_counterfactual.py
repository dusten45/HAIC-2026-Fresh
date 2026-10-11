"""One exact-prefix DEV fork changing only a frozen policy's pedal feedback.

Existing records validate the unchanged control and both pre-fork histories.
World state is evaluator-only. Actors start from reset, never a restored snapshot.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from retry.frozen_paired_evaluation import native_window, sha, verify_files, write
from retry.hud_feedback_generalization import recorded_episode


def run(plan_path):
    from retry import diagnose
    from retry.full_route_reproduction import truth

    plan_path = Path(plan_path).resolve()
    directory = plan_path.parent
    plan = json.loads(plan_path.read_text())
    assert sha(plan_path) == plan_path.with_suffix('.sha256').read_text().strip()
    assert plan['experiment_kind'] == 'one_local_pedal_counterfactual'
    assert len(plan['cases']) == 1 and list(plan['arms']) == ['control', 'old_feedback']
    assert plan['max_actions'] == 2 * plan['max_steps'] <= 3000
    assert plan['no_promotion'] and plan['split_kind'] == 'existing_DEV'
    assert plan['arms']['control']['archive_sha256'] == plan['arms']['old_feedback']['archive_sha256']
    start_step = plan['intervention_start_step']
    assert plan['arms']['control']['constants'] == {'constants.json': {'start_step': 0}}
    assert plan['arms']['old_feedback']['constants'] == {'constants.json': {'start_step': start_step}}
    assert 1 < start_step < plan['max_steps']
    verify_files(plan['source_sha256'])
    assert plan['source_sha256'][str(Path(__file__).resolve())] == sha(__file__)
    source = Path(plan['saved_trace_path'])
    assert sha(source) == plan['saved_trace_sha256']
    saved = [json.loads(line) for line in source.read_text().splitlines()]
    assert len(saved) >= plan['max_steps']
    native_window(plan)
    write(directory / 'execution-claim.json', {'plan_sha256': sha(plan_path),
          'started_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
          'one_use': True, 'automatic_retry': False}, exclusive=True)
    write(directory / 'budget.json', {'started_epoch': time.time(), 'actions': 0, 'stages': {}}, exclusive=True)
    started, cpu = time.perf_counter(), time.process_time()
    original_factory = diagnose.make_env
    results, checks, initial_pairs = [], {}, {}
    failure = None
    try:
        for arm in plan['arms']:
            check = {'matched_actions': 0, 'matched_before_states': 0,
                     'matched_after_states': 0, 'matched_observations': 0}
            checks[arm] = check
            native_window(plan)

            def factory(*args, **kwargs):
                env = original_factory(*args, **kwargs)
                original_reset, original_step = env.reset, env.step
                step_number = 0

                def reset(*args, **kwargs):
                    output = original_reset(*args, **kwargs)
                    assert hashlib.sha256(output[0].tobytes()).hexdigest() == saved[0]['observation_sha256_before']
                    assert truth(env) == saved[0]['truth_before']
                    check['initial_exact'] = True
                    return output

                def step(action):
                    nonlocal step_number
                    step_number += 1
                    row = saved[step_number - 1]
                    unchanged = arm == 'control' or step_number < start_step
                    if unchanged or step_number == start_step:
                        assert truth(env) == row['truth_before'], 'Pre-fork physical state differs'
                        check['matched_before_states'] += 1
                    if unchanged:
                        assert np.asarray(action, np.float32).tobytes() == np.asarray(row['action'], np.float32).tobytes(), 'Prefix/control action differs'
                        check['matched_actions'] += 1
                    output = original_step(action)
                    if unchanged:
                        assert truth(env) == row['truth_after'], 'Prefix/control after-state differs'
                        assert hashlib.sha256(output[0].tobytes()).hexdigest() == row['observation_sha256_after'], 'Prefix/control observation differs'
                        check['matched_after_states'] += 1
                        check['matched_observations'] += 1
                    return output

                env.reset, env.step = reset, step
                return env

            diagnose.make_env = factory
            result = recorded_episode(plan_path, plan, plan['cases'][0], arm, initial_pairs)
            results.append(result)
            diagnose.make_env = original_factory
            if 'error' in result:
                raise RuntimeError(result['error'])
            assert check['matched_actions'] == (plan['max_steps'] if arm == 'control' else start_step - 1)
            assert check['matched_before_states'] == (plan['max_steps'] if arm == 'control' else start_step)
            print(json.dumps({'arm': arm, 'native_actions': result['charged_wrapper_actions'],
                              'exact_prefix_actions': check['matched_actions']}), flush=True)
    except Exception as error:
        failure = type(error).__name__ + ': ' + str(error)
    finally:
        diagnose.make_env = original_factory
    ledger = json.loads((directory / 'budget.json').read_text())
    summary = {'status': 'PASS' if failure is None and len(results) == 2 else 'FAIL',
               'failure': failure, 'plan_sha256': sha(plan_path),
               'prefix_checks': checks, 'native_actions': ledger['actions'],
               'raw_step_ticks': sum(r['raw_step_ticks'] for r in results),
               'raw_reset_ticks': sum(r['raw_reset_ticks'] for r in results),
               'wall_s': time.perf_counter() - started,
               'evaluator_CPU_s': time.process_time() - cpu,
               'actor_CPU_s': sum(r['actor_cumulative_CPU_s'] for r in results),
               'all_actors_reaped': all(r.get('reaping', {}).get('actor_pids_absent') for r in results),
               'roles': [r['role'] for r in results], 'new_seeds': 0,
               'automatic_retry': False, 'no_promotion': True,
               'interpretation': 'One local pedal-feedback fork. Changes to later observations/path are downstream effects; no isolated path-planner claim.'}
    write(directory / 'execution-result.json', summary, exclusive=True)
    print(json.dumps(summary), flush=True)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.plan)
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
