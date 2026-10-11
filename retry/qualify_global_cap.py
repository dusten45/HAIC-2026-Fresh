"""Bounded pixel replay of a no-op control and one frozen cap intervention.

Recorded observations are evaluator-only. Each isolated actor receives only the
ordinary reset/act operation and official grayscale stack. No simulator runs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from retry.frozen_composite_runtime import prepare, validate_response
from retry.frozen_paired_evaluation import sha, verify_files, write


def run(contract_path):
    contract = json.loads(contract_path.read_text())
    verify_files(contract['source_sha256'])
    verify_files(contract['runtime_sha256'])
    assert contract['source_sha256'][str(Path(__file__).resolve())] == sha(__file__)
    configs = json.loads(Path(contract['configuration_manifest_path']).read_text())
    assert list(configs) == ['A', 'B']
    assert all(c['type'] == 'champion' and not c.get('assets') and not c.get('constants')
               for c in configs.values())
    directory = Path(contract['output_directory'])
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    started = time.perf_counter()
    counts = dict(cold_starts=0, reset_attempts=0, reset_responses=0,
                  act_attempts=0, act_responses=0, model_calls=0)
    records, workers = {}, []
    report = {'status': 'FAIL', 'contract_sha256': sha(contract_path)}
    try:
        data = np.load(contract['frames_path'], allow_pickle=False)
        frames, expected_actions = data['frames'], data['actions']
        saved = [json.loads(line) for line in Path(contract['trace_path']).read_text().splitlines()]
        initial = json.loads(Path(contract['started_path']).read_text())['initial_observation_sha256']
        observations = []
        for index in range(contract['actions']):
            obs = frames[np.maximum(0, np.arange(index - 3, index + 1))].astype(np.float32) / 255
            expected = initial if index == 0 else saved[index - 1]['observation_sha256_after']
            assert hashlib.sha256(obs.tobytes()).hexdigest() == expected
            observations.append(obs)
        for arm, config in configs.items():
            assert time.perf_counter() - started < contract['max_wall_s']
            counts['cold_starts'] += 1
            assert counts['cold_starts'] <= contract['max_cold_starts']
            worker = prepare(config, directory / arm, contract['sandbox_path'])
            record = {'arm': arm, 'ready': worker.ready, 'cold_start_ms': worker.cold_start_ms}
            workers.append(record)
            records[arm] = []
            try:
                counts['reset_attempts'] += 1
                assert counts['reset_attempts'] <= contract['max_actor_reset_calls']
                response, elapsed = worker.call('reset', observations[0])
                counts['reset_responses'] += 1
                validate_response(response, config, observations[0], 'reset')
                record['reset_ms'] = elapsed
                for index, obs in enumerate(observations):
                    assert time.perf_counter() - started < contract['max_wall_s']
                    counts['act_attempts'] += 1
                    assert counts['act_attempts'] <= contract['max_actor_act_calls']
                    response, elapsed = worker.call('act', obs)
                    counts['act_responses'] += 1
                    action = validate_response(response, config, obs, 'act')
                    if arm == 'A':
                        assert np.array_equal(action, expected_actions[index]), f'No-op differs at {index + 1}'
                    records[arm].append({'step': index + 1,
                                         'observation_sha256': hashlib.sha256(obs.tobytes()).hexdigest(),
                                         'response': response, 'IPC_ms': elapsed})
            finally:
                record['reaping'] = worker.close()
                record['observed_peak_RSS_bytes'] = worker.observed_peak_rss_bytes
                assert record['reaping']['process_reaped'] and record['reaping']['actor_pids_absent']
                path = directory / (arm + '.jsonl')
                with path.open('x') as stream:
                    for row in records[arm]:
                        stream.write(json.dumps(row, allow_nan=False) + '\n')
                path.chmod(0o600)
        first = None
        different = 0
        for a, b in zip(records['A'], records['B']):
            assert a['observation_sha256'] == b['observation_sha256']
            left, right = a['response']['action'], b['response']['action']
            assert left[0] == right[0], 'Steering changed on identical pixels and history'
            if left != right:
                different += 1
                if first is None:
                    first = {'step': a['step'], 'observation_sha256': a['observation_sha256'],
                             'original_action': left, 'candidate_action': right}
        assert first is not None, 'No observed cap intervention in the frozen replay'
        report.update(status='PASS', no_op_actions_bit_exact=len(observations),
                      full4_observation_hashes_exact=len(observations),
                      steering_exact_on_same_recorded_input=True,
                      different_action_steps=different, first_action_difference=first,
                      difference_is_not_performance_evidence=True)
    except Exception as error:
        report['error'] = type(error).__name__ + ': ' + str(error)
    finally:
        report.update(counts=counts, workers=workers, wall_s=time.perf_counter() - started,
                      new_native_resets=0, new_native_steps=0, retry=False,
                      configuration_manifest_sha256=sha(contract['configuration_manifest_path']),
                      qualification_script_sha256=sha(__file__),
                      official_submission_equivalence='UNVERIFIED')
        write(directory / 'qualification-report.json', report, exclusive=True)
    print(json.dumps({k: v for k, v in report.items() if k != 'workers'}), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', required=True, type=Path)
    result = run(parser.parse_args().contract)
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
