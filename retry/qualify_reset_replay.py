"""Replay an exact frozen artifact, then verify warm and cold reset prefixes.

This uses saved DEV pixels without a simulator. Reused supervisor fault evidence
must be separately hash-bound; a fresh launch does not establish server parity.
"""
import argparse
import datetime as dt
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
    verify_files(contract['source_sha256'])
    verify_files(contract['runtime_sha256'])
    assert contract['source_sha256'][str(Path(__file__).resolve())] == sha(__file__)
    config = contract['configuration']
    assert config['type'] == 'champion' and not config.get('assets') and not config.get('constants')
    directory = Path(contract['output_directory'])
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    start = time.perf_counter()
    counts = {'cold_starts': 0, 'reset_attempts': 0, 'reset_responses': 0,
              'act_attempts': 0, 'act_responses': 0, 'model_calls': 0}
    sessions = []
    report = {'status': 'FAIL', 'contract_sha256': sha(contract_path)}

    def guard():
        now = dt.datetime.now(dt.timezone.utc)
        assert now < dt.datetime.fromisoformat(contract['deadline_utc'])
        assert now < dt.datetime.fromisoformat(contract['authorization_end_utc'])
        assert time.perf_counter() - start < contract['max_wall_s']

    try:
        guard()
        data = np.load(contract['frames_path'], allow_pickle=False)
        frames, actions = data['frames'], data['actions']
        assert len(actions) == contract['full_replay_actions']
        assert frames.shape == (len(actions) + 1, 84, 84) and frames.dtype == np.uint8
        trace = [json.loads(line) for line in Path(contract['trace_path']).read_text().splitlines()]
        initial = json.loads(Path(contract['started_path']).read_text())['initial_observation_sha256']
        observations = []
        for i in range(len(frames)):
            obs = frames[np.maximum(0, np.arange(i - 3, i + 1))].astype(np.float32) / 255
            expected = initial if i == 0 else trace[i - 1]['observation_sha256_after']
            assert hashlib.sha256(obs.tobytes()).hexdigest() == expected
            observations.append(obs)
        lengths = [[len(actions), contract['warm_reset_actions']], [contract['second_cold_actions']]]
        for index, prefixes in enumerate(lengths):
            guard()
            counts['cold_starts'] += 1
            assert counts['cold_starts'] <= contract['max_cold_starts']
            worker = prepare(config, directory / str(index), contract['sandbox_path'])
            session = {'cold_start_ms': worker.cold_start_ms, 'ready': worker.ready,
                       'passes': [], 'reset_ms': [], 'act_ms': [], 'actor_CPU_s': 0.0}
            sessions.append(session)
            try:
                for length in prefixes:
                    guard()
                    assert 0 < length <= len(actions)
                    counts['reset_attempts'] += 1
                    assert counts['reset_attempts'] <= contract['max_reset_calls']
                    response, elapsed = worker.call('reset', observations[0])
                    counts['reset_responses'] += 1
                    validate_response(response, config, observations[0], 'reset')
                    session['reset_ms'].append(elapsed)
                    sequence = hashlib.sha256()
                    for i in range(length):
                        guard()
                        counts['act_attempts'] += 1
                        assert counts['act_attempts'] <= contract['max_act_calls']
                        response, elapsed = worker.call('act', observations[i])
                        counts['act_responses'] += 1
                        action = validate_response(response, config, observations[i], 'act')
                        assert np.array_equal(action, actions[i]), f'Replay differs at {i + 1}'
                        sequence.update(action.tobytes())
                        session['act_ms'].append(elapsed)
                        session['actor_CPU_s'] = response['actor_cumulative_CPU_s']
                    session['passes'].append({'actions_exact': length,
                                              'action_sequence_sha256': sequence.hexdigest()})
            finally:
                session['reaping'] = worker.close()
                session['peak_RSS_bytes'] = worker.observed_peak_rss_bytes
                assert session['reaping']['process_reaped'] and session['reaping']['actor_pids_absent']
        guard()
        verify_files(contract['source_sha256'])
        verify_files(contract['runtime_sha256'])
        report['status'] = 'PASS'
    except Exception as error:
        report['error'] = type(error).__name__ + ': ' + str(error)
    finally:
        report.update(counts=counts, sessions=sessions, wall_s=time.perf_counter() - start,
                      participant_CPU_s=sum(s['actor_CPU_s'] for s in sessions),
                      max_cold_ms=max((s['cold_start_ms'] for s in sessions), default=0),
                      max_reset_ms=max((v for s in sessions for v in s['reset_ms']), default=0),
                      max_act_ms=max((v for s in sessions for v in s['act_ms']), default=0),
                      max_RSS_bytes=max((s.get('peak_RSS_bytes', 0) for s in sessions), default=0),
                      new_native_reset_or_step_calls=0, model_calls=0, automatic_retry=False,
                      archive_sha256=config['archive_sha256'],
                      official_server_or_fresh_machine_equivalence='UNVERIFIED')
        write(directory / 'qualification-report.json', report, exclusive=True)
    print(json.dumps({k: v for k, v in report.items() if k != 'sessions'}), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', type=Path, required=True)
    result = run(parser.parse_args().contract)
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
