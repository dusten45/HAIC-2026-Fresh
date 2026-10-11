"""Verify saved grayscale-student records without policy or simulator calls."""
import hashlib
import json
from pathlib import Path

import numpy as np


def array_sha(value):
    return hashlib.sha256(value.tobytes()).hexdigest()


def verify_records(directory, case_id):
    directory = Path(directory)
    result = json.loads((directory / case_id / 'student-result.json').read_text())
    rows = [json.loads(line) for line in (directory / (case_id + '-trace.jsonl')).read_text().splitlines()]
    receipts = json.loads((directory / (case_id + '-student-receipts.json')).read_text())
    with np.load(directory / (case_id + '-pixels-actions.npz'), allow_pickle=False) as saved:
        frames, actions = saved['frames'].copy(), saved['actions'].copy()
    with np.load(directory / (case_id + '-student-masks.npz'), allow_pickle=False) as saved:
        masks = saved['masks'].copy()
    count = len(rows)
    assert count == len(actions) == result['successful_wrapper_steps']
    assert frames.dtype == np.uint8 and frames.shape == (count + 1, 84, 84)
    assert actions.dtype == np.float32 and actions.shape == (count, 3)
    assert masks.dtype == np.uint8 and masks.shape == frames.shape
    assert len(receipts) == count + 1
    if 'action_sequence_sha256' in result:
        assert array_sha(actions) == result['action_sequence_sha256']
    for j, receipt in enumerate(receipts):
        index = max(0, j - 1)
        observation = frames[np.maximum(0, np.arange(index - 3, index + 1))].astype(np.float32) / 255
        original = ((observation[-1] > .32) & (observation[-1] < .47)).astype(np.uint8)
        mask = masks[j]
        assert receipt['operation'] == ('reset' if j == 0 else 'act')
        assert receipt['observation_sha256'] == array_sha(observation)
        assert np.isin(mask, [0, 1]).all() and np.all(mask <= original)
        assert receipt['original_P_sha256'] == array_sha(original)
        assert receipt['student_mask_sha256'] == array_sha(mask)
        assert receipt['original_P_cells'] == int(original.sum())
        assert receipt['kept_cells'] == int(mask.sum())
        assert receipt['deleted_cells'] == int((original - mask).sum())
        assert receipt['added_cells'] == 0
    contacts = []
    for index, row in enumerate(rows):
        before = frames[np.maximum(0, np.arange(index - 3, index + 1))].astype(np.float32) / 255
        after = frames[np.maximum(0, np.arange(index - 2, index + 2))].astype(np.float32) / 255
        assert row['step'] == index + 1
        assert row['observation_sha256_before'] == array_sha(before)
        assert row['observation_sha256_after'] == array_sha(after)
        assert np.array_equal(actions[index], np.asarray(row['action'], dtype=np.float32))
        expected = {k: v for k, v in receipts[index + 1].items()
                    if k not in ['operation', 'observation_sha256']}
        assert row['policy_response']['student_receipt'] == expected
        if index:
            assert row['truth_before'] == rows[index - 1]['truth_after']
        calls = row['policy_response']['original_calls']
        assert all(calls[k] == 1 for k in ['detection', 'tracker', 'ridge', 'route', 'target'])
        assert calls.get('action_target', 0) + calls.get('fallback_action', 0) == 1
        if row['info']['collision']:
            contacts.append({'step': index + 1, 'damage': row['truth_after']['damage'],
                             'time_s': row['truth_after']['time'],
                             'progress_tiles': row['truth_after']['unique_tiles']})
    endpoints = sum(row['terminated'] or row['truncated'] for row in rows)
    if result['status'] in ['COMPLETE', 'DNF']:
        assert count > 0 and endpoints == 1
        assert rows[-1]['terminated'] or rows[-1]['truncated']
        finish = rows[-1]['info']['finish_time_s']
        assert (finish is not None) == result['completed']
        if result['completed']:
            assert round((finish - 1.02) * 1000) == result['official_lap_ms']
    else:
        assert endpoints == 0
    if rows:
        assert round((rows[-1]['truth_after']['time'] - rows[0]['truth_before']['time']) * 50) == result['raw_step_ticks']
    details = receipts[1:]
    means = np.asarray([r['feature_mean_on_P'] for r in details], dtype=float)
    if count:
        assert means.shape == (count, 21) and np.isfinite(means).all()
    inference = [r['inference_ms'] for r in details]
    latency = [row['act_including_IPC_ms'] for row in rows]
    return {'actions': count, 'frames': len(frames), 'mask_calls': len(masks),
            'all_observation_action_mask_receipts_exact': True, 'raw_added_cells': 0,
            'single_component_calls_each_action': True, 'native_endpoints': endpoints,
            'contact_events': contacts,
            'student_delete_fraction_on_P': sum(r['deleted_cells'] for r in details) / sum(r['original_P_cells'] for r in details) if count else None,
            'feature_mean_across_frames': means.mean(axis=0).tolist() if count else None,
            'student_inference_ms_median': float(np.median(inference)) if count else None,
            'student_inference_ms_max': max(inference, default=None),
            'action_including_IPC_ms_median': float(np.median(latency)) if count else None,
            'action_including_IPC_ms_max': max(latency, default=None),
            'verification_policy_env_renderer_or_prediction_calls': 0}
