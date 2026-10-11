"""Saved-record audits and identity-free paired summaries; no runtime policy calls.

``aggregate(directory, cases)`` returns ``aggregate`` and ``mechanical_receipt``.
Cases carry only id/pair_id/arm (v2 or student). Per-case records never appear in
the return value. Resource-censored and unexecuted pairs leave the 2x2 table.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np


def _read(path):
    return json.loads(path.read_text())


def _sha(array):
    return hashlib.sha256(array.tobytes()).hexdigest()


def _stats(values):
    values = np.asarray(values, dtype=float)
    assert np.isfinite(values).all()
    return {'count': len(values), 'sum': float(values.sum()),
            'mean': float(values.mean()) if len(values) else None,
            'median': float(np.median(values)) if len(values) else None,
            'min': float(values.min()) if len(values) else None,
            'max': float(values.max()) if len(values) else None}


def _damage_summary(pairs):
    deltas = [b['damage'] - a['damage'] for a, b in pairs]
    return {'pairs': len(pairs),
            'student_higher': sum(d > 0 for d in deltas),
            'v2_higher': sum(d < 0 for d in deltas),
            'equal': sum(d == 0 for d in deltas),
            'student_minus_v2': _stats(deltas),
            'scope': 'Diagnostic only; episode exposure may differ.'}


def _progress_summary(pairs):
    for a, b in pairs:
        assert a['total_tiles'] == b['total_tiles'] and a['total_tiles'] > 0
    return {'pairs': len(pairs),
            'student_minus_v2_unique_tiles': _stats([b['unique_tiles'] - a['unique_tiles'] for a, b in pairs]),
            'student_minus_v2_unique_progress': _stats([(b['unique_tiles'] - a['unique_tiles']) / a['total_tiles'] for a, b in pairs])}


def _verify(directory, case, result):
    name = case['id']
    rows = [_read_line(line) for line in
            (directory / (name + '-trace.jsonl')).read_text().splitlines()]
    with np.load(directory / (name + '-pixels-actions.npz'), allow_pickle=False) as z:
        frames, actions = z['frames'], z['actions']
        n = len(rows)
        assert frames.dtype == np.uint8 and frames.shape == (n + 1, 84, 84)
        assert actions.dtype == np.float32 and actions.shape == (n, 3)
        assert n == result['successful_wrapper_steps']
        assert result['charged_wrapper_actions'] >= n
        assert result.get('id', name) == name
        assert np.isfinite(actions).all()
        assert np.all(actions >= [-1, 0, 0]) and np.all(actions <= [1, 1, 1])
        if result.get('action_sequence_sha256') is not None:
            assert _sha(actions) == result['action_sequence_sha256']
        endpoints = 0
        for i, row in enumerate(rows):
            before = frames[np.maximum(0, np.arange(i - 3, i + 1))].astype(np.float32) / 255
            after = frames[np.maximum(0, np.arange(i - 2, i + 2))].astype(np.float32) / 255
            assert row['step'] == i + 1
            assert row['observation_sha256_before'] == _sha(before)
            assert row['observation_sha256_after'] == _sha(after)
            assert actions[i].tobytes() == np.asarray(row['action'], np.float32).tobytes()
            assert actions[i].tobytes() == np.asarray(row['policy_response']['action'], np.float32).tobytes()
            assert row['truth_after']['time'] > row['truth_before']['time']
            tick_count = round((row['truth_after']['time'] - row['truth_before']['time']) * 50)
            assert 1 <= tick_count <= 4
            if i:
                assert row['truth_before'] == rows[i - 1]['truth_after']
            calls = row.get('policy_response', {}).get('original_calls', row.get('original_calls'))
            assert calls is not None
            assert all(calls[k] == 1 for k in ['detection', 'tracker', 'ridge', 'route', 'target'])
            assert calls.get('action_target', 0) + calls.get('fallback_action', 0) == 1
            endpoints += int(row['terminated'] or row['truncated'])
            assert 0 <= row['act_including_IPC_ms'] <= 5000
        status = result['status']
        normal = status in ('COMPLETE', 'DNF')
        assert endpoints == (1 if normal else 0)
        if normal:
            assert n and (rows[-1]['terminated'] or rows[-1]['truncated'])
            assert result['completed'] == (status == 'COMPLETE')
            finish = rows[-1]['info']['finish_time_s']
            assert (finish is not None) == result['completed']
            if finish is not None:
                assert round((finish - 1.02) * 1000) == result['official_lap_ms']
            for key, field in [('native_terminated', 'terminated'), ('native_truncated', 'truncated')]:
                if key in result:
                    assert bool(result[key]) == bool(rows[-1][field])
        elif status == 'RESOURCE_CENSORED':
            assert not result.get('completed', False)
        else:
            raise ValueError('Unsupported saved status')
        started = _read(directory / name / 'started.json')
        initial = np.repeat(frames[:1], 4, axis=0).astype(np.float32) / 255
        assert started['initial_observation_sha256'] == _sha(initial)
        if 'road_geometry_sha256' in result:
            assert result['road_geometry_sha256'] == started['geometry_sha256']
        if n:
            assert rows[0]['truth_before'] == started['initial']
            final = rows[-1]['truth_after']
            assert final['unique_tiles'] == result['unique_tiles']
            assert final['damage'] == result['damage']
            ticks = round((final['time'] - rows[0]['truth_before']['time']) * 50)
            assert ticks == result['raw_step_ticks']
        assert result['raw_reset_ticks'] == 51
        if case['arm'] == 'student':
            mask_path = directory / (name + '-student-masks.npz')
            receipt_path = directory / (name + '-student-receipts.json')
            assert mask_path.exists() and receipt_path.exists()
            from retry.road_keep_saved_records import verify_records
            checked = verify_records(directory, name)
            assert checked['actions'] == n
        if 'worker_reaping' in result:
            assert result['worker_reaping']['process_reaped']
        if result.get('peak_actor_RSS_MiB') is not None:
            assert 0 <= result['peak_actor_RSS_MiB'] * 1024 * 1024 <= 1_024_000_000
        return started, {'rows': n, 'frames': n + 1, 'native_endpoints': endpoints,
                         'mask_records_verified': int(case['arm'] == 'student' and mask_path.exists()),
                         'latency': [r['act_including_IPC_ms'] for r in rows]}


def _read_line(line):
    return json.loads(line)


def aggregate(directory, cases):
    """Audit supplied records, returning no IDs, individual results or traces.

    Executed students require masks, receipts and identical result.json and
    student-result.json. Audit failures suppress all protected details.
    """
    try:
        return _aggregate(Path(directory), cases)
    except Exception:
        raise ValueError('Saved paired-record verification failed; aggregate withheld') from None


def _aggregate(directory, cases):
    assert cases and len({c['id'] for c in cases}) == len(cases)
    grouped = {}
    records = {'v2': [], 'student': []}
    audited = []
    starts = {}
    for case in cases:
        name, pair, arm = case['id'], case['pair_id'], case['arm']
        assert isinstance(name, str) and Path(name).name == name and name not in ('', '.', '..')
        assert arm in records
        assert arm not in grouped.setdefault(pair, {})
        result = _read(directory / name / 'result.json')
        assert result['status'] in ('COMPLETE', 'DNF', 'RESOURCE_CENSORED', 'UNEXECUTED')
        never_started = result['status'] == 'UNEXECUTED' or result.get('episode_count') == 0
        if not never_started:
            if arm == 'student':
                assert _read(directory / name / 'student-result.json') == result
            started, audit = _verify(directory, case, result)
            starts[(pair, arm)] = started
            audit['arm'] = arm
            audited.append(audit)
        else:
            assert result['status'] in ('UNEXECUTED', 'RESOURCE_CENSORED')
            assert not result.get('completed', False) and result.get('successful_wrapper_steps', 0) == 0
            if result['status'] == 'UNEXECUTED':
                assert result['charged_wrapper_actions'] == 0
        grouped[pair][arm] = result
        records[arm].append(result)
    table = Counter(dict.fromkeys(['both', 'student_only', 'v2_only', 'neither'], 0))
    deltas, ratios, unknown = [], [], 0
    native_pairs, common_pairs, both_failed_pairs = [], [], []
    for pair, arms in grouped.items():
        assert set(arms) == {'v2', 'student'}
        if (pair, 'v2') in starts and (pair, 'student') in starts:
            a, b = starts[(pair, 'v2')], starts[(pair, 'student')]
            for key in ['initial', 'initial_observation_sha256', 'geometry_sha256', 'obstacles_sha256']:
                assert a[key] == b[key]
        a, b = arms['v2'], arms['student']
        if not all(x['status'] in ('COMPLETE', 'DNF') for x in (a, b)):
            unknown += 1
            continue
        ca, cb = a['completed'], b['completed']
        native_pairs.append((a, b))
        if not ca and not cb:
            both_failed_pairs.append((a, b))
        table['both' if ca and cb else 'student_only' if cb else 'v2_only' if ca else 'neither'] += 1
        if ca and cb:
            common_pairs.append((a, b))
            assert a['official_lap_ms'] > 0 and b['official_lap_ms'] > 0
            deltas.append(b['official_lap_ms'] - a['official_lap_ms'])
            ratios.append(b['official_lap_ms'] / a['official_lap_ms'])
    arms_summary = {}
    for arm, values in records.items():
        failed = [x for x in values if x['status'] == 'DNF']
        done = [x for x in values if x['status'] in ('COMPLETE', 'DNF')]
        laps = [x['official_lap_ms'] for x in values if x['status'] == 'COMPLETE']
        censored = [x for x in values if x['status'] == 'RESOURCE_CENSORED']
        gaps = [x['charged_wrapper_actions'] - x.get('successful_wrapper_steps', 0) for x in values]
        assert all(g >= 0 for g in gaps)
        def measured(key):
            return _stats([x[key] for x in values if x.get(key) is not None])
        arms_summary[arm] = {
            'status_counts': dict(Counter(x['status'] for x in values)),
            'native_failure_count': len(failed),
            'native_failure_types': dict(Counter(x.get('failure_type') or 'unspecified' for x in failed)),
            'censored_count': sum(x['status'] == 'RESOURCE_CENSORED' for x in values),
            'unexecuted_count': sum(x['status'] == 'UNEXECUTED' for x in values),
            'completed_lap_ms': _stats(laps),
            'failed_unique_tiles': _stats([x['unique_tiles'] for x in failed]),
            'failed_unique_progress': _stats([x['unique_tiles'] / x['total_tiles'] for x in failed]),
            'censored_observed_unique_progress': _stats([x['unique_tiles'] / x['total_tiles'] for x in censored
                                                        if x.get('unique_tiles') is not None and x.get('total_tiles', 0) > 0]),
            'censored_observed_unique_tiles': _stats([x['unique_tiles'] for x in censored if x.get('unique_tiles') is not None]),
            'damage_native_endpoints': _stats([x['damage'] for x in done]),
            'damage_all_observed': _stats([x['damage'] for x in values if x.get('damage') is not None]),
            'charged_actions': sum(x['charged_wrapper_actions'] for x in values),
            'successful_steps': sum(x.get('successful_wrapper_steps', 0) for x in values),
            'charged_minus_successful_steps': sum(gaps),
            'incomplete_charged_action_count': sum(gaps),
            'runs_with_incomplete_charged_actions': sum(g > 0 for g in gaps),
            'charged_minus_successful_step_summary': _stats(gaps),
            'raw_step_ticks': sum(x.get('raw_step_ticks', 0) for x in values),
            'raw_reset_ticks': sum(x.get('raw_reset_ticks', 0) for x in values),
            'actor_CPU_s': sum(x.get('actor_CPU_s') or 0 for x in values),
            'actor_CPU_measured_runs': sum(x.get('actor_CPU_s') is not None for x in values),
            'sim_step_wall_s': sum(x.get('sum_sim_step_wall_s') or 0 for x in values),
            'sim_step_wall_measured_runs': sum(x.get('sum_sim_step_wall_s') is not None for x in values),
            'episode_wall_s': sum(x.get('wall_s') or 0 for x in values),
            'episode_wall_measured_runs': sum(x.get('wall_s') is not None for x in values),
            'action_including_IPC_ms': _stats([x for a in audited if a['arm'] == arm for x in a['latency']]),
            'cold_start_ms': measured('cold_start_ms'),
            'reset_including_IPC_ms': measured('reset_including_IPC_ms'),
            'reset_environment_wall_s': measured('reset_environment_wall_s'),
            'package_initialization_ms': _stats([x['worker_ready']['package_init_ms'] for x in values
                                                if (x.get('worker_ready') or {}).get('package_init_ms') is not None]),
            'closing_ms': _stats([x['worker_reaping']['close_ms'] for x in values
                                  if (x.get('worker_reaping') or {}).get('close_ms') is not None]),
            'supervisor_peak_RSS_bytes': measured('supervisor_peak_rss_bytes'),
            'actor_peak_RSS_MiB': measured('peak_actor_RSS_MiB'),
            'peak_actor_RSS_MiB': max((x.get('peak_actor_RSS_MiB') or 0 for x in values), default=0)}
    return {'aggregate': {'registered_pairs': len(grouped),
                         'normal_endpoint_pairs': sum(table.values()),
                         'indeterminate_pairs': unknown, 'completion_2x2': dict(table),
                         'common_completed_lap_delta_summary_ms': _stats(deltas),
                         'common_completed_lap_ratio_summary': _stats(ratios),
                         'common_completed_absolute_lap_ms': {
                             'v2': _stats([a['official_lap_ms'] for a, _ in common_pairs]),
                             'student': _stats([b['official_lap_ms'] for _, b in common_pairs])},
                         'paired_native_endpoint_damage_warnings': _damage_summary(native_pairs),
                         'common_completed_damage_warnings': _damage_summary(common_pairs),
                         'paired_native_endpoint_unique_progress_delta': _progress_summary(native_pairs),
                         'both_failed_unique_progress_delta': _progress_summary(both_failed_pairs),
                         'arms': arms_summary,
                         'action_including_IPC_ms': _stats([x for a in audited for x in a['latency']]),
                         'interpretation': 'Descriptive paired outcomes; damage exposure unequal; censoring is not DNF.'},
            'mechanical_receipt': {'pass': True, 'registered_runs': len(cases),
                                   'audited_runs': len(audited),
                                   'verified_rows': sum(a['rows'] for a in audited),
                                   'verified_frames': sum(a['frames'] for a in audited),
                                   'native_endpoints': sum(a['native_endpoints'] for a in audited),
                                   'verified_student_mask_records': sum(a['mask_records_verified'] for a in audited),
                                   'paired_reset_records': sum(all((p, a) in starts for a in records) for p in grouped),
                                   'new_policy_environment_renderer_model_calls': 0}}
