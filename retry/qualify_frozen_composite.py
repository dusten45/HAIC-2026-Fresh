"""Qualify frozen research actors using short saved DEV prefixes only.

No environment, renderer, teacher, fitting or training is called. Real actor
reset/act calls and two supervisor faults are reported separately from physics.
"""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback

import numpy as np

from retry.frozen_composite_runtime import prepare, sha, validate_response


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    path.chmod(0o600)


def stopped_state(pid):
    """Read the stop acknowledgement; no actor request or policy call."""
    text = (Path('/proc') / str(pid) / 'status').read_text()
    return next(line.split()[1] for line in text.splitlines() if line.startswith('State:'))


def wait_stopped(pid):
    deadline = time.monotonic() + 1
    while time.monotonic() < deadline:
        state = stopped_state(pid)
        if state in ('T', 't'):
            return state
        time.sleep(.005)
    raise RuntimeError('SIGSTOP was not acknowledged')


def run(manifest_path, contract_path, output):
    manifest = json.loads(manifest_path.read_text())
    contract = json.loads(contract_path.read_text())
    assert np.__version__ == contract['numpy_version'] == '1.26.0'
    assert sha(manifest_path) == contract['configuration_manifest_sha256']
    assert not output.exists()
    start, cpu = time.perf_counter(), time.process_time()
    directory = output.parent
    assert directory.is_dir()
    claim = directory / 'qualification-execution-claim.json'
    with claim.open('x') as stream:
        json.dump({'at_utc': datetime.now(timezone.utc).isoformat(),
                   'manifest_sha256': sha(manifest_path),
                   'contract_sha256': sha(contract_path)}, stream)
    claim.chmod(0o600)

    def guard(check_sources=False):
        assert datetime.now(timezone.utc) < datetime.fromisoformat(contract['deadline_utc'])
        assert time.perf_counter() - start < contract['max_wall_s']
        if check_sources:
            for path, expected in contract['source_sha256'].items():
                assert sha(path) == expected, path

    guard(True)
    reports = {}
    counters = dict(cold_starts=0, reset_requests=0, act_requests=0,
                    successful_reset_responses=0, successful_act_responses=0,
                    forced_fault_requests=0, forced_fault_successful_responses=0,
                    successful_student_mask_receipts=0)
    sessions = []
    error = None
    try:
        for arm, config in manifest['arms'].items():
            ref = contract['references'][arm]
            with np.load(ref['pixels_actions_path'], allow_pickle=False) as saved:
                frames, expected = saved['frames'], saved['actions']
            assert frames.dtype == np.uint8 and expected.dtype == np.float32
            assert frames.shape == (len(expected) + 1, 84, 84)
            assert expected.shape == (len(expected), 3)
            masks = None
            if config['type'] == 'student':
                with np.load(ref['masks_path'], allow_pickle=False) as saved:
                    masks = saved['masks']
                assert masks.shape == frames.shape and masks.dtype == np.uint8
            assert len(expected) >= contract['initial_prefix_actions']
            observation = lambda i: frames[np.maximum(0, np.arange(i - 3, i + 1))].astype(np.float32) / 255
            arm_report = {'sessions': [], 'action_matches': 0, 'mask_matches': 0,
                          'faults': [], 'configuration_type': config['type']}
            reports[arm] = arm_report
            current = None
            session = None

            def open_session(label):
                nonlocal current, session
                guard()
                counters['cold_starts'] += 1
                current = prepare(config, directory / ('runtime-' + arm + '-' + label),
                                  contract['sandbox_path'])
                session = {'arm': arm, 'label': label, 'cold_start_ms': current.cold_start_ms,
                           'ready': current.ready, 'ready_checks': current.configuration_ready_receipt,
                           'reset_ms': [], 'act_ms': [], 'action_matches': 0, 'mask_matches': 0}
                sessions.append(session); arm_report['sessions'].append(session)

            def request(operation, i):
                guard()
                obs = observation(i)
                counters[operation + '_requests'] += 1
                response, elapsed = current.call(operation, obs)
                action = validate_response(response, config, obs, operation)
                assert elapsed <= 5000
                counters['successful_' + operation + '_responses'] += 1
                session[operation + '_ms'].append(elapsed)
                session['actor_CPU_s'] = response['actor_cumulative_CPU_s']
                if masks is not None:
                    mask = np.frombuffer(base64.b64decode(response['student_mask_base64']),
                                         np.uint8).reshape(84, 84)
                    # Reset uses mask0; act i uses receipt i+1 for frame i.
                    expected_mask = masks[0 if operation == 'reset' else i + 1]
                    assert mask.tobytes() == expected_mask.tobytes(), (arm, operation, i, 'mask')
                    counters['successful_student_mask_receipts'] += 1
                    session['mask_matches'] += 1; arm_report['mask_matches'] += 1
                if operation == 'act':
                    assert action.tobytes() == expected[i].tobytes(), (arm, i, 'action')
                    session['action_matches'] += 1; arm_report['action_matches'] += 1
                return response

            def close_session():
                nonlocal current
                if current is not None:
                    session['observed_peak_RSS_bytes'] = current.observed_peak_rss_bytes
                    session['reaping'] = current.close()
                    assert session['reaping']['process_reaped'] is True
                    current = None

            try:
                open_session('normal')
                request('reset', 0)
                for i in range(contract['initial_prefix_actions']):
                    request('act', i)
                request('reset', 0)
                for i in range(contract['same_process_reset_actions']):
                    request('act', i)
                close_session()

                open_session('cold-timeout')
                request('reset', 0)
                for i in range(contract['second_cold_prefix_actions']):
                    request('act', i)
                actor_pid = next(iter(current.actor_pids))
                fault = {'kind': 'actual_actor_SIGSTOP', 'policy_source_modified': False,
                         'expected_deadline_s': 5, 'actual_policy_calls_in_fault': None,
                         'native_tracer_paused_to_hold_actor_stop': True}
                try:
                    # A live ptrace tracer can resume a SIGSTOP delivery-stop.
                    # Pause that tracer first, then acknowledge the actual
                    # actor's stop before issuing the one timeout request.
                    os.kill(current.process.pid, signal.SIGSTOP)
                    fault['tracer_pre_request_state'] = wait_stopped(current.process.pid)
                    os.kill(actor_pid, signal.SIGSTOP)
                    fault['actor_pre_request_state'] = wait_stopped(actor_pid)
                    counters['forced_fault_requests'] += 1
                    before = time.perf_counter()
                    try:
                        current.call('act', observation(contract['second_cold_prefix_actions']))
                        counters['forced_fault_successful_responses'] += 1
                        raise AssertionError('Stopped actor unexpectedly responded')
                    except TimeoutError as exc:
                        fault.update(detected=True, error=repr(exc),
                                     detection_ms=(time.perf_counter() - before) * 1000,
                                     actor_post_timeout_state=stopped_state(actor_pid),
                                     tracer_post_timeout_state=stopped_state(current.process.pid))
                finally:
                    os.kill(actor_pid, signal.SIGCONT)
                    os.kill(current.process.pid, signal.SIGCONT)
                    fault['SIGCONT_sent'] = True
                # A timed-out partial IPC request is never resumed as trusted work.
                close_session()
                fault['reaping'] = session['reaping']
                arm_report['faults'].append(fault)

                open_session('crash')
                request('reset', 0); request('act', 0)
                actor_pid = next(iter(current.actor_pids))
                os.kill(actor_pid, signal.SIGKILL)
                counters['forced_fault_requests'] += 1
                fault = {'kind': 'actual_actor_SIGKILL', 'policy_source_modified': False,
                         'actual_policy_calls_in_fault': None}
                before = time.perf_counter()
                try:
                    current.call('act', observation(1))
                    counters['forced_fault_successful_responses'] += 1
                    raise AssertionError('Killed actor unexpectedly responded')
                except (RuntimeError, BrokenPipeError, ConnectionResetError) as exc:
                    fault.update(detected=True, error=repr(exc),
                                 detection_ms=(time.perf_counter() - before) * 1000)
                close_session()
                fault['reaping'] = session['reaping']
                arm_report['faults'].append(fault)

                open_session('recovery')
                request('reset', 0)
                for i in range(contract['post_fault_recovery_actions']):
                    request('act', i)
                close_session()
                arm_report['passed'] = True
            finally:
                close_session()
    except BaseException as exc:
        error = {'error': repr(exc), 'traceback': traceback.format_exc()}
    try:
        guard(True)
    except BaseException as exc:
        error = {'error': repr(exc), 'traceback': traceback.format_exc(),
                 'additional_prior_error': error}
    report = {'status': 'PASS' if error is None and len(reports) == len(manifest['arms'])
              and all(r.get('passed') for r in reports.values()) else 'FAIL',
              'scope': 'same-host frozen composite research runtime qualification only',
              'configuration_manifest_sha256': sha(manifest_path),
              'contract_sha256': sha(contract_path), 'arms': reports,
              'request_counts': counters, 'new_environment_actions': 0,
              'new_environment_reset_or_step_calls': 0, 'new_training_or_fit': 0,
              'protected_data_read': False, 'SEALED_opened': False,
              'official_submission_qualification': False, 'fresh_machine_parity': False,
              'official_server_parity': False, 'all_input_resource_guarantee': False,
              'wall_s': time.perf_counter() - start, 'supervisor_CPU_s': time.process_time() - cpu,
              'participant_CPU_s': sum(s.get('actor_CPU_s', 0) for s in sessions),
              'max_cold_start_ms': max((s['cold_start_ms'] for s in sessions), default=None),
              'max_reset_ms': max((x for s in sessions for x in s['reset_ms']), default=None),
              'max_successful_act_ms': max((x for s in sessions for x in s['act_ms']), default=None),
              'max_participant_RSS_bytes': max((s.get('observed_peak_RSS_bytes', 0) for s in sessions), default=0),
              'all_workers_reaped': all(s.get('reaping', {}).get('process_reaped') for s in sessions),
              'timeout_requests_are_not_normal_act_latency_samples': True,
              'partial_timeout_stream_reused': False, 'error': error}
    write(output, report)
    print(json.dumps({k: report[k] for k in ('status', 'request_counts', 'wall_s',
                                           'max_successful_act_ms', 'all_workers_reaped', 'error')}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--contract', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.manifest.resolve(), args.contract.resolve(), args.output.resolve())
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
