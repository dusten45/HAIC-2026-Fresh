"""One frozen champion on fresh DEV, with existing per-action recording.

Keep only diagnostic fields from the already-qualified observer. Geometry is
copied at the real reset; no additional policy, renderer or simulator calls.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
import shutil
import time

import numpy as np

from retry.frozen_paired_evaluation import native_window, sha, verify_files, write
from retry.hud_feedback_generalization import recorded_episode


def diagnostic_episode(plan_path, plan, case, initial_pairs):
    from retry import diagnose, frozen_composite_runtime as runtime

    original_factory, original_prepare = diagnose.make_env, runtime.prepare
    directory = plan_path.parent / 'runs' / (case['id'] + '__A')

    def factory(*args, **kwargs):
        env = original_factory(*args, **kwargs)
        original_reset = env.reset

        def reset(*args, **kwargs):
            output = original_reset(*args, **kwargs)
            road = np.asarray(env.unwrapped.track, dtype='<f8')
            obstacles = np.asarray([
                [*map(float, item.position), float(item.fixtures[0].shape.radius)]
                for item in env.unwrapped.obstacles], dtype='<f8').reshape(-1, 3)
            with (directory / 'geometry.npz').open('xb') as stream:
                np.savez_compressed(stream, road=road, obstacles=obstacles)
            (directory / 'geometry.npz').chmod(0o600)
            return output

        env.reset = reset
        return env

    def prepare(*args, **kwargs):
        worker = original_prepare(*args, **kwargs)
        original_call = worker.call

        def call(operation, obs):
            response, elapsed = original_call(operation, obs)
            if operation == 'act':
                # Evaluator-side projection only; action and validation fields
                # are retained verbatim. The frozen observer is unchanged.
                response = dict(response)
                response.pop('memory', None)
                response.pop('near_curvature_probe', None)
                keep = {
                    'contact_probe': ('old_HUD_speed_m_s', 'actual_feedback_speed_m_s',
                        'fixed_decoder_speed_m_s', 'decoder_exact_match',
                        'decoder_fallback_used', 'curvature', 'target_speed_m_s', 'near',
                        'gas', 'brake', 'controller_before', 'controller_after',
                        'detected_path_xy', 'detected_obstacles_xyr',
                        'tracker_hazards_after', 'actual_calls'),
                    'speed_constraint_probe': ('selected_path_body',
                        'ridge_centerline_body', 'tracked_obstacles_body',
                        'returned_target', 'desired_lookahead_m', 'route_empty',
                        'route_total_polyline_length_m', 'target_endpoint_truncated'),
                }
                for name, keys in keep.items():
                    response[name] = {k: response[name][k] for k in keys if k in response[name]}
            return response, elapsed

        worker.call = call
        return worker

    diagnose.make_env, runtime.prepare = factory, prepare
    try:
        return recorded_episode(plan_path, plan, case, 'A', initial_pairs)
    finally:
        diagnose.make_env, runtime.prepare = original_factory, original_prepare


def run(plan_path):
    plan_path = Path(plan_path).resolve()
    plan = json.loads(plan_path.read_text())
    assert sha(plan_path) == plan_path.with_suffix('.sha256').read_text().strip()
    assert plan['experiment_kind'] == 'frozen_champion_fresh_dev_survey'
    assert plan['split_kind'] == 'DEV' and plan['no_promotion']
    assert plan['max_actions'] == 8000 and plan['max_steps'] == 2000
    assert len(plan['cases']) == 4 and list(plan['arms']) == ['A']
    assert all(case['arm_order'] == ['A'] and case['split'] == plan['case_split'] for case in plan['cases'])
    assert len({case['id'] for case in plan['cases']}) == 4
    assert plan['stage_budgets'] == {c['id'] + '__A': 2000 for c in plan['cases']}
    verify_files(plan['source_sha256'])
    assert sha(plan['selection_path']) == plan['selection_sha256']
    selection = json.loads(Path(plan['selection_path']).read_text())
    assert selection['cases'] == plan['cases']
    assert selection['status'] == 'PASS_REGISTERED_NOT_OPENED'
    assert sha(plan['allocation_path']) == plan['allocation_sha256']
    allocation = json.loads(Path(plan['allocation_path']).read_text())
    assert allocation['research_remaining'] >= 8000
    assert allocation['final_reserved_actions'] == 84000 and allocation['final_reserve_used'] == 0
    manifest = json.loads(Path(plan['champion_manifest_path']).read_text())
    frozen = dict(manifest['configuration'])
    frozen.update(worker_path=plan['arms']['A']['worker_path'],
                  worker_sha256=plan['arms']['A']['worker_sha256'])
    assert frozen == plan['arms']['A']
    assert sha(plan['observer_qualification_path']) == plan['observer_qualification_sha256']
    qualification = json.loads(Path(plan['observer_qualification_path']).read_text())
    assert qualification['status'] == 'PASS'
    assert qualification['archive_sha256']['B'] == frozen['archive_sha256']
    native_window(plan)
    assert shutil.disk_usage(plan_path.parent).free >= 2_000_000_000
    remaining = (dt.datetime.fromisoformat(plan['deadline_utc']) - dt.datetime.now(dt.timezone.utc)).total_seconds()
    assert remaining >= plan['prospective_batch_wall_s']
    directory = plan_path.parent
    write(directory / 'execution-claim.json', {'plan_sha256': sha(plan_path),
          'started_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
          'one_use': True, 'automatic_retry': False}, exclusive=True)
    write(directory / 'budget.json', {'started_epoch': time.time(), 'actions': 0, 'stages': {}}, exclusive=True)
    start, cpu = time.perf_counter(), time.process_time()
    results, initial_pairs, failure = [], {}, None
    try:
        for case in plan['cases']:
            result = diagnostic_episode(plan_path, plan, case, initial_pairs)
            results.append(result)
            print(json.dumps({'finished': len(results), 'planned': 4,
                'completed': result['completed'], 'damage': result['damage'],
                'native_actions': result['charged_wrapper_actions'],
                'technical_error': result.get('error')}), flush=True)
            if 'error' in result:
                raise RuntimeError(result['error'])
            assert result['reaping']['process_reaped'] and result['reaping']['actor_pids_absent']
            # Normal DNF/censor never changes the remaining registered runs.
    except Exception as error:
        failure = type(error).__name__ + ': ' + str(error)
    ledger = json.loads((directory / 'budget.json').read_text())
    assert 0 <= ledger['actions'] <= 8000
    assert sum(ledger['stages'].values()) == ledger['actions']
    assert all(used <= 2000 for used in ledger['stages'].values())
    if sum(r['charged_wrapper_actions'] for r in results) != ledger['actions']:
        failure = failure or 'Charged actions include an unreturned episode'
    verify_files(plan['source_sha256'])
    report = {'status': 'PASS' if failure is None and len(results) == 4 else 'FAIL',
        'failure': failure, 'plan_sha256': sha(plan_path), 'results': results,
        'native_actions': ledger['actions'],
        'raw_step_ticks': sum(r['raw_step_ticks'] for r in results),
        'raw_reset_ticks': sum(r['raw_reset_ticks'] for r in results),
        'wall_s': time.perf_counter() - start, 'evaluator_CPU_s': time.process_time() - cpu,
        'actor_CPU_s': sum(r['actor_cumulative_CPU_s'] for r in results),
        'new_saved_policy_or_model_calls': 0, 'extra_native_calls': 0,
        'champion_changed': False, 'automatic_next_candidate': False}
    write(directory / 'report.json', report, exclusive=True)
    print(json.dumps({k: v for k, v in report.items() if k != 'results'}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', required=True)
    run(parser.parse_args().plan)
