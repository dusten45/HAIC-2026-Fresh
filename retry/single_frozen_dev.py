"""One preregistered missing DEV reference, using a previously qualified actor.

The optional passive evaluator record preserves pixels/actions and physical
states for DEV analysis. It never alters an action or passes truth to the actor.
Existing qualified paired-episode code enforces the pixel/resource boundary.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time

import numpy as np

from retry.frozen_paired_evaluation import episode, sha, verify_files, write
from retry.paired_audit_gate import claim_once


def run(plan_path):
    plan_path = Path(plan_path).resolve()
    directory = plan_path.parent
    plan = json.loads(plan_path.read_text())
    assert sha(plan_path) == plan_path.with_suffix('.sha256').read_text().split()[0]
    assert plan['split_kind'] == 'DEV' and plan['only_missing_reference'] is True
    assert plan['max_actions'] == plan['max_steps'] == 2000
    assert list(plan['arms']) == ['A'] and plan['arms']['A']['type'] == 'champion'
    assert len(plan['cases']) == 1
    case = plan['cases'][0]
    role = case['id'] + '__A'
    assert plan['stage_budgets'] == {role: 2000}
    assert sha(plan['inventory_path']) == plan['inventory_sha256']
    inventory = json.loads(Path(plan['inventory_path']).read_text())
    assert inventory['direct_formal_vs_candidate_reusable_pairs'] == 0
    matching = [row for row in inventory['cases_in_requested_order']
                if row['original_DEV_id'] == case['id']]
    assert len(matching) == 1
    prior = matching[0]
    assert prior['formal_champion_record'] is None
    assert prior['formal_direct_pair_reusable'] is False and prior['candidate_reusable'] is True
    assert inventory['formal_champion_archive_sha256'] == plan['arms']['A']['archive_sha256']
    assert sha(plan['initial_reference_path']) == plan['initial_reference_sha256']
    assert sha(plan['configuration_manifest_path']) == plan['configuration_manifest_sha256']
    frozen = json.loads(Path(plan['configuration_manifest_path']).read_text())
    assert plan['arms']['A'] == frozen['arms']['A']
    assert sha(plan['project_budget_path']) == plan['project_budget_sha256']
    budget = json.loads(Path(plan['project_budget_path']).read_text())
    assert budget['research_remaining'] >= 2000
    assert budget['final_reserved_actions'] == 84000 and budget['final_reserve_used'] == 0
    assert shutil.disk_usage(directory).free >= plan['minimum_free_disk_bytes']
    verify_files(plan['source_sha256'])
    verify_files(plan['runtime_sha256'])
    assert str(Path(__file__).resolve()) in plan['source_sha256']
    claim_once(plan_path)
    write(directory / 'budget.json', {'started_epoch': time.time(), 'actions': 0, 'stages': {}}, exclusive=True)

    from retry import diagnose
    from retry.full_route_reproduction import truth
    original_factory = diagnose.make_env
    frames, actions, rows = [], [], []
    reset_record = {}

    def observer_factory(*args, **kwargs):
        env = original_factory(*args, **kwargs)
        original_reset, original_step = env.reset, env.step

        def reset(*args, **kwargs):
            result = original_reset(*args, **kwargs)
            obs = result[0]
            assert not frames and not rows
            frames.append(np.rint(obs[-1] * 255).astype(np.uint8))
            reset_record.update(initial=truth(env), initial_observation_sha256=hashlib.sha256(obs.tobytes()).hexdigest())
            return result

        def step(action):
            before = truth(env)
            frozen_action = np.asarray(action, dtype=np.float32).copy()
            result = original_step(action)
            obs, reward, ended, truncated, info = result
            # Read/copy only after the unchanged official step returns.
            assert np.array_equal(action, frozen_action)
            actions.append(frozen_action)
            frames.append(np.rint(obs[-1] * 255).astype(np.uint8))
            rows.append({'step': len(actions), 'truth_before': before, 'truth_after': truth(env),
                         'action': frozen_action.tolist(), 'reward': float(reward),
                         'observation_sha256_after': hashlib.sha256(obs.tobytes()).hexdigest(),
                         'collision': bool(info.get('collision', False)),
                         'terminated': bool(ended), 'truncated': bool(truncated),
                         'retire_reason': info['retire_reason'], 'finish_time_s': info['finish_time_s']})
            return result

        env.reset, env.step = reset, step
        return env

    initial = plan['expected_initial_identity']
    previous = json.loads(Path(plan['initial_reference_path']).read_text())
    assert initial == {
        'road_geometry_sha256': previous['geometry_sha256'],
        'physical_obstacles_sha256': previous['obstacles_sha256'],
        'state_sha256': hashlib.sha256(json.dumps(previous['initial'], sort_keys=True,
                                                allow_nan=False).encode()).hexdigest(),
        'observation_sha256': previous['initial_observation_sha256'],
    }
    assert initial['road_geometry_sha256'] == case['road_geometry_sha256']
    assert initial['physical_obstacles_sha256'] == case['expected_physical_obstacles_sha256']
    diagnose.make_env = observer_factory
    started = time.perf_counter()
    try:
        result = episode(plan_path, plan, case, 'A', {case['id']: initial})
    finally:
        diagnose.make_env = original_factory
    # The reused endpoint function itself stores no trajectory. This separate
    # DEV-only observer and its resource costs are declared in the private plan.
    archive = directory / 'dev-pixels-actions.npz'
    frame_array = np.asarray(frames, dtype=np.uint8)
    action_array = np.asarray(actions, dtype=np.float32).reshape(-1, 3)
    assert len(rows) == len(action_array) == result['successful_wrapper_steps']
    if 'error' not in result:
        assert len(frame_array) == len(action_array) + 1
        assert hashlib.sha256(action_array.tobytes()).hexdigest() == result['action_sequence_sha256']
        sequence = hashlib.sha256()
        for index in range(len(frame_array)):
            obs = frame_array[np.maximum(0, np.arange(index - 3, index + 1))].astype(np.float32) / 255
            sequence.update(obs.tobytes())
            expected = reset_record['initial_observation_sha256'] if index == 0 else rows[index - 1]['observation_sha256_after']
            assert hashlib.sha256(obs.tobytes()).hexdigest() == expected
        assert sequence.hexdigest() == result['observation_sequence_sha256']
    np.savez_compressed(archive, frames=frame_array, actions=action_array)
    archive.chmod(0o600)
    with (directory / 'dev-trace.jsonl').open('x') as stream:
        for row in rows:
            stream.write(json.dumps(row, allow_nan=False) + '\n')
    (directory / 'dev-trace.jsonl').chmod(0o600)
    write(directory / 'dev-started.json', reset_record, exclusive=True)
    report = {'status': 'PASS' if 'error' not in result and result['terminal_observed'] else 'INCONCLUSIVE',
              'plan_sha256': sha(plan_path), 'endpoint_path': str(directory / 'runs' / role / 'result.json'),
              'endpoint_sha256': sha(directory / 'runs' / role / 'result.json'),
              'charged_wrapper_actions': result['charged_wrapper_actions'],
              'completed': result['completed'], 'lap_ms': result['lap_ms'], 'damage': result['damage'],
              'wall_including_record_write_s': time.perf_counter() - started,
              'DEV_frames_saved': len(frames), 'DEV_trace_rows_saved': len(rows),
              'policy_config_changed': False, 'extra_policy_model_calls': 0,
              'GT_passed_to_actor': False, 'action_observation_record_hashes_exact': 'error' not in result,
              'no_automatic_retry': True, 'SEALED_or_HOLDOUT_details_read': False,
              'record_sha256': {path.name: sha(path) for path in
                               (archive, directory / 'dev-trace.jsonl', directory / 'dev-started.json')},
              'error': result.get('error')}
    write(directory / 'single-reference-result.json', report, exclusive=True)
    print(json.dumps(report))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    result = run(parser.parse_args().plan)
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
