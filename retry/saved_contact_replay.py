"""One-use saved-DEV observer replay; execute only after explicit ROOT GO.

No simulator is imported. Saved truth is evaluator-only and is never sent to the
actor. Each original reset and saved input is replayed once; actions must match byte for byte.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import time

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
import numpy as np
from retry.frozen_composite_runtime import prepare, validate_response
from retry.frozen_paired_evaluation import sha, verify_files, write


def run(contract_path, *, execute=False):
    assert execute, 'Explicit --execute after ROOT GO is required'
    contract_path = Path(contract_path).resolve()
    assert contract_path.with_suffix('.sha256').read_text().strip() == sha(contract_path)
    contract = json.loads(contract_path.read_text())
    n_total = contract['max_actor_act_calls']
    n_datasets = len(contract['datasets'])
    assert n_total > 0 and n_datasets == contract['max_cold_starts'] == contract['max_reset_calls']
    configurations = contract['configurations']
    assert all(c['type'] == 'champion' and not c.get('assets') and not c.get('constants')
               for c in configurations.values())
    verify_files(contract['source_sha256'])
    assert contract['source_sha256'][str(Path(__file__).resolve())] == sha(__file__)
    assert sum(item['actions'] for item in contract['datasets']) == n_total
    labels = [item['label'] for item in contract['datasets']]
    assert len(set(labels)) == n_datasets and all(Path(label).name == label and label not in ('.', '..') for label in labels)
    directory = Path(contract['output_directory'])
    assert not directory.exists()
    deadline = dt.datetime.fromisoformat(contract['authorization_end_utc'])
    assert deadline.tzinfo is not None and dt.datetime.now(dt.timezone.utc) < deadline
    write(contract_path.parent / 'probe-execution-claim.json', {
        'contract_sha256': sha(contract_path), 'claimed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'one_use': True, 'automatic_retry': False,
    }, exclusive=True)
    directory.mkdir(mode=0o700)
    start = time.perf_counter()
    evaluator_CPU_start = time.process_time()
    counts = {'cold_start_attempts': 0, 'cold_starts': 0, 'reset_attempts': 0,
              'reset_responses': 0, 'act_attempts': 0, 'act_responses': 0,
              'actions_exact': 0, 'model_calls': 0}
    sessions = []
    report = {'status': 'FAIL', 'contract_sha256': sha(contract_path)}

    def guard():
        assert dt.datetime.now(dt.timezone.utc) < deadline

    try:
        for item in contract['datasets']:
            guard()
            config = configurations[item['arm']]
            verify_files(item['input_sha256'])
            with np.load(item['frames_path'], allow_pickle=False) as cached:
                frames, expected_actions = cached['frames'], cached['actions']
            endpoint = json.loads(Path(item['result_path']).read_text())
            initial = json.loads(Path(item['started_path']).read_text())['initial_observation_sha256']
            trace = [json.loads(line) for line in Path(item['trace_path']).read_text().splitlines()]
            n = item['actions']
            assert expected_actions.shape == (n, 3) and expected_actions.dtype == np.float32
            assert frames.shape == (n + 1, 84, 84) and frames.dtype == np.uint8 and len(trace) == n
            assert endpoint['archive_sha256'] == config['archive_sha256']
            assert endpoint['successful_wrapper_steps'] == n
            assert hashlib.sha256(expected_actions.tobytes()).hexdigest() == endpoint['action_sequence_sha256']
            observations = []
            for i in range(n + 1):
                obs = frames[np.maximum(0, np.arange(i - 3, i + 1))].astype(np.float32) / 255
                expected_hash = initial if i == 0 else trace[i - 1]['observation_sha256_after']
                assert hashlib.sha256(obs.tobytes()).hexdigest() == expected_hash
                observations.append(obs)
            session_dir = directory / item['label']
            session_dir.mkdir(mode=0o700)
            path = session_dir / 'probe.jsonl'
            stream = path.open('x'); path.chmod(0o600)
            worker = None
            session = {'label': item['label'], 'expected_actions': n, 'actions_exact': 0,
                       'actor_CPU_s': 0.0, 'act_IPC_ms': [], 'input_hashes_exact': n + 1}
            sessions.append(session)
            session_start = time.perf_counter()
            try:
                counts['cold_start_attempts'] += 1
                assert counts['cold_start_attempts'] <= contract['max_cold_starts']
                worker = prepare(config, session_dir / 'cpu', contract['sandbox_path'])
                counts['cold_starts'] += 1
                session.update(ready=worker.ready, cold_start_ms=worker.cold_start_ms)
                assert worker.ready['observer_extra_policy_calls'] == 0
                assert worker.ready['observer_extra_vision_calls'] == 0
                assert worker.ready['observer_model_calls'] == 0
                guard()
                counts['reset_attempts'] += 1
                assert counts['reset_attempts'] <= contract['max_reset_calls']
                response, elapsed = worker.call('reset', observations[0])
                counts['reset_responses'] += 1
                validate_response(response, config, observations[0], 'reset')
                session['reset_IPC_ms'] = elapsed
                session['actor_CPU_s'] = response['actor_cumulative_CPU_s']
                stream.write(json.dumps({'operation': 'reset', 'response': response,
                                        'input_observation_sha256': initial, 'IPC_ms': elapsed}, allow_nan=False) + '\n')
                stream.flush()
                for i, obs in enumerate(observations[:-1]):
                    guard()
                    counts['act_attempts'] += 1
                    assert counts['act_attempts'] <= contract['max_actor_act_calls']
                    response, elapsed = worker.call('act', obs)
                    counts['act_responses'] += 1
                    session['actor_CPU_s'] = response['actor_cumulative_CPU_s']
                    action = validate_response(response, config, obs, 'act')
                    probe = response['speed_constraint_probe']
                    assert all(probe['actual_calls'][name] == 1 for name in ('tracker', 'route', 'target', 'ridge'))
                    assert response['observer_extra_policy_calls'] == 0
                    exact = action.tobytes() == expected_actions[i].tobytes()
                    before, after = trace[i]['truth_before']['time'], trace[i]['truth_after']['time']
                    finish = endpoint.get('finish_time_s')
                    dwell = max(0.0, (after if finish is None else min(after, finish)) - before)
                    row = {'operation': 'act', 'step': i + 1,
                           'input_observation_sha256': hashlib.sha256(obs.tobytes()).hexdigest(),
                           'response': response, 'IPC_ms': elapsed, 'saved_action_exact': exact,
                           'saved_action_dwell_s': dwell}
                    stream.write(json.dumps(row, allow_nan=False) + '\n'); stream.flush()
                    assert exact, 'Read-only observer changed saved action'
                    counts['actions_exact'] += 1
                    session['actions_exact'] += 1
                    session['act_IPC_ms'].append(elapsed)
            finally:
                stream.close()
                if worker is not None:
                    session['reaping'] = worker.close()
                    session['peak_RSS_bytes'] = worker.observed_peak_rss_bytes
                    assert session['reaping']['process_reaped'] and session['reaping']['actor_pids_absent']
                session['wall_s'] = time.perf_counter() - session_start
                session['records_sha256'] = sha(path)
        guard()
        assert counts['actions_exact'] == counts['act_responses'] == n_total
        assert counts['cold_starts'] == counts['reset_responses'] == n_datasets
        report['status'] = 'PASS'
    except Exception as error:
        report['error'] = type(error).__name__ + ': ' + str(error)
    finally:
        report.update(counts=counts, sessions=sessions, wall_s=time.perf_counter() - start,
            evaluator_CPU_s=time.process_time() - evaluator_CPU_start,
            actor_CPU_s=sum(s['actor_CPU_s'] for s in sessions),
            max_cold_ms=max((s.get('cold_start_ms', 0) for s in sessions), default=0),
            max_reset_ms=max((s.get('reset_IPC_ms', 0) for s in sessions), default=0),
            max_act_ms=max((x for s in sessions for x in s['act_IPC_ms']), default=0),
            max_RSS_bytes=max((s.get('peak_RSS_bytes', 0) for s in sessions), default=0),
            actor_CPU_scope='Latest successful response per process; cleanup CPU excluded',
            new_native_reset_or_step_calls=0, new_model_calls=0, automatic_retry=False,
            archive_sha256={arm: c['archive_sha256'] for arm, c in configurations.items()}, policy_changed=False,
            input_scope='Official grayscale4 stack plus reset/act only; no saved truth sent to actor',
            interpretation='Saved inputs reconstruct each original policy history; causal comparisons require spatial alignment and pre-contact filtering',
            verification_scope='Changed observer and replay sources, loaded archives and exact saved inputs/actions; prior host qualification reused')
        write(directory / 'probe-report.json', report, exclusive=True)
    print(json.dumps({k: v for k, v in report.items() if k != 'sessions'}), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', type=Path, required=True)
    parser.add_argument('--execute', action='store_true', help='Use only after ROOT GO')
    args = parser.parse_args()
    result = run(args.contract, execute=args.execute)
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
