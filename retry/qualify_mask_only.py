"""Qualify a frozen mask-only worker using existing DEV observations, no simulator."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from retry.frozen_composite_runtime import prepare, validate_response
from retry.frozen_paired_evaluation import sha, verify_files, write


def run(contract_path):
    contract_path = Path(contract_path).resolve()
    contract = json.loads(contract_path.read_text())
    directory = contract_path.parent / 'qualification'
    verify_files(contract['source_sha256'])
    verify_files(contract['runtime_sha256'])
    configs = json.loads(Path(contract['configuration_manifest_path']).read_text())['configs']
    claim = directory / 'opening.json'
    write(claim, {'contract_sha256': sha(contract_path), 'started_epoch': time.time()}, exclusive=True)
    started = time.perf_counter()
    counts = {'cold_starts': 0, 'reset_attempts': 0, 'act_attempts': 0,
              'reset_responses': 0, 'act_responses': 0, 'student_model_responses': 0}
    cases, workers = [], []
    report = {'status': 'INCOMPLETE', 'new_native_resets': 0, 'new_native_steps': 0,
              'new_training': False, 'contract_sha256': sha(contract_path)}
    try:
        for case in contract['cases']:
            data = np.load(case['frames'], allow_pickle=False)
            frames, expected_actions = data['frames'], data['actions']
            saved = [json.loads(line) for line in Path(case['trace']).read_text().splitlines()]
            initial = json.loads(Path(case['started']).read_text())['initial_observation_sha256']
            observations = []
            for index in range(case['actions']):
                obs = frames[np.maximum(0, np.arange(index - 3, index + 1))].astype(np.float32) / 255
                wanted = initial if index == 0 else saved[index - 1]['observation_sha256_after']
                assert hashlib.sha256(obs.tobytes()).hexdigest() == wanted
                observations.append(obs)
            records = {}
            for mode in contract['modes']:
                assert time.perf_counter() - started < contract['max_wall_s']
                counts['cold_starts'] += 1
                assert counts['cold_starts'] <= contract['max_cold_starts']
                worker = prepare(configs[mode], directory / (case['id'] + '-' + mode), contract['sandbox_path'])
                worker_record = {'case': case['id'], 'mode': mode, 'cold_start_ms': worker.cold_start_ms,
                                 'ready': worker.ready}
                workers.append(worker_record)
                records[mode] = []
                try:
                    counts['reset_attempts'] += 1
                    assert counts['reset_attempts'] <= contract['max_actor_reset_calls']
                    response, reset_ms = worker.call('reset', observations[0])
                    counts['reset_responses'] += 1
                    counts['student_model_responses'] += int(mode == 'student')
                    validate_response(response, configs[mode], observations[0], 'reset')
                    worker_record['reset_ms'] = reset_ms
                    for index, obs in enumerate(observations):
                        assert time.perf_counter() - started < contract['max_wall_s']
                        counts['act_attempts'] += 1
                        assert counts['act_attempts'] <= contract['max_actor_act_calls']
                        response, elapsed = worker.call('act', obs)
                        counts['act_responses'] += 1
                        counts['student_model_responses'] += int(mode == 'student')
                        assert counts['student_model_responses'] <= contract['max_student_model_calls']
                        action = validate_response(response, configs[mode], obs, 'act')
                        if mode == 'original':
                            assert np.array_equal(action, expected_actions[index]), f'Original control changed at {case["id"]}:{index + 1}'
                        records[mode].append({'step': index + 1, 'observation_sha256': hashlib.sha256(obs.tobytes()).hexdigest(),
                                              'response': response, 'IPC_ms': elapsed})
                finally:
                    worker_record['reaping'] = worker.close()
                    worker_record['observed_peak_RSS_bytes'] = worker.observed_peak_rss_bytes
                    assert worker_record['reaping']['process_reaped'] and worker_record['reaping']['actor_pids_absent']
                    with (directory / (case['id'] + '-' + mode + '.jsonl')).open('x') as stream:
                        for row in records[mode]:
                            stream.write(json.dumps(row, allow_nan=False) + '\n')
                    (directory / (case['id'] + '-' + mode + '.jsonl')).chmod(0o600)
            first_action = first_path = first_target = None
            for index, (left, right) in enumerate(zip(records['original'], records['student'])):
                a, b = left['response'], right['response']
                at, bt = a['route_telemetry'], b['route_telemetry']
                assert left['observation_sha256'] == right['observation_sha256']
                # Same recorded input must preserve the original detector and tracker.
                for field in ('current_detections', 'memory_hazards_before_tracker',
                              'memory_hazards_after_tracker', 'route_obstacle_inputs', 'speed_estimate'):
                    assert at[field] == bt[field], field
                if first_path is None and at['selected_path'] != bt['selected_path']:
                    first_path = index + 1
                if first_target is None and at['selected_target'] != bt['selected_target']:
                    first_target = index + 1
                if first_action is None and a['action'] != b['action']:
                    first_action = {'step': index + 1, 'observation_sha256': left['observation_sha256'],
                                    'original_action': a['action'], 'student_action': b['action'],
                                    'original_target': at['selected_target'], 'student_target': bt['selected_target'],
                                    'original_controller_before': at['controller_before'],
                                    'student_controller_before': bt['controller_before'],
                                    'student_receipt': b['student_receipt']}
            cases.append({'case': case['id'], 'original_actions_bit_exact': len(observations),
                          'full4_observations_hash_exact': len(observations),
                          'same_detector_tracker_speed_on_all_recorded_inputs': True,
                          'first_path_difference_step': first_path, 'first_target_difference_step': first_target,
                          'first_action_difference': first_action,
                          'output_difference_is_not_a_performance_improvement_claim': True})
        report['status'] = 'PASS'
    except Exception as error:
        report['error'] = type(error).__name__ + ': ' + str(error)
    finally:
        report.update(counts=counts, cases=cases, workers=workers, wall_s=time.perf_counter() - started,
                      new_native_resets=0, new_native_steps=0,
                      configuration_manifest_sha256=sha(contract['configuration_manifest_path']),
                      qualification_script_sha256=sha(__file__), retry=False,
                      official_submission_equivalence='UNVERIFIED')
        write(directory / 'qualification-report.json', report, exclusive=True)
    print(json.dumps({key: report[key] for key in ('status', 'counts', 'cases', 'wall_s')}), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', required=True, type=Path)
    result = run(parser.parse_args().contract)
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
