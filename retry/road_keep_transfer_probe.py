"""Record a frozen student's ordered DEV episodes against historical outcomes.

Historical full action streams are optional evidence, never reconstructed here.
The initial observation/state and geometry receipts qualify each reused case.
The existing native evaluator and isolated grayscale worker remain unchanged.
"""
import argparse
import base64
import json
from pathlib import Path

import numpy as np

from retry import fresh_dev_distribution as native
from retry.full_route_reproduction import truth
from retry.road_keep_student_probe import copy_assets
from retry.qualify_pixel_package import PipeWorker


def recorded_episode(case, plan, path):
    directory = path.parent
    frames, actions, masks, receipts = [], [], [], []
    latest = {}
    initial_verified = False
    original_worker, original_factory = native.PipeWorker, native.make_env
    trace_path = directory / (case['id'] + '-trace.jsonl')
    trace = trace_path.open('x')
    trace_path.chmod(0o600)

    class RecordedStudent(PipeWorker):
        def __init__(self, *args):
            super().__init__(*args)
            assert self.ready['student_model_sha256'] == plan['student_model_sha256']
            assert self.ready['input_contract'] == 'float32(4,84,84) grayscale only'
            assert not self.ready['privileged_diagnostic']
            expected = {name: plan['candidate']['members_sha256'][
                'retry/__init__.py' if name == 'retry' else name.replace('.', '/') + '.py']
                for name in self.ready['module_sha256']}
            assert self.ready['module_sha256'] == expected and len(expected) == 14
            assert self.ready['observer_additional_policy_calls'] == 0
            assert len(self.ready['CPU_affinity']) == 1

        def call(self, operation, observation):
            assert observation.shape == (4, 84, 84) and observation.dtype == np.float32
            response, duration = super().call(operation, observation)
            mask = np.frombuffer(base64.b64decode(response.pop('student_mask_base64')),
                                 dtype=np.uint8).reshape(84, 84).copy()
            original = ((observation[-1] > .32) & (observation[-1] < .47)).astype(np.uint8)
            detail = response['student_receipt']
            assert np.isin(mask, [0, 1]).all() and np.all(mask <= original)
            assert native.sha_bytes(mask) == detail['student_mask_sha256']
            assert native.sha_bytes(original) == detail['original_P_sha256']
            assert detail['added_cells'] == 0
            masks.append(mask)
            receipts.append({'operation': operation,
                             'observation_sha256': native.sha_bytes(observation), **detail})
            if operation == 'act':
                latest.update(response=response, act_including_IPC_ms=duration)
            return response, duration

    def recorded_factory():
        env = original_factory()
        original_reset, original_step = env.reset, env.step

        def reset(*args, **kwargs):
            nonlocal initial_verified
            observation, info = original_reset(*args, **kwargs)
            assert native.sha_bytes(observation) == case['baseline_initial_observation_sha256']
            initial = truth(env)
            assert {k: initial[k] for k in case['baseline_initial_truth']} == case['baseline_initial_truth']
            frame = np.rint(observation[-1] * 255).astype(np.uint8)
            assert np.array_equal(observation, np.repeat(frame[None], 4, axis=0).astype(np.float32) / 255)
            frames.append(frame)
            initial_verified = True
            return observation, info

        def step(action):
            index = len(actions)
            before = truth(env)
            input_obs = np.stack([frames[max(0, j)] for j in range(index - 3, index + 1)]).astype(np.float32) / 255
            output = original_step(action)
            observation, reward, terminated, truncated, info = output
            assert np.array_equal(observation[:3], input_obs[1:])
            frame = np.rint(observation[-1] * 255).astype(np.uint8)
            assert np.array_equal(frame.astype(np.float32) / 255, observation[-1])
            frames.append(frame)
            actions.append(np.asarray(action, dtype=np.float32).copy())
            row = {'step': len(actions), 'action': actions[-1].tolist(),
                   'observation_sha256_before': native.sha_bytes(input_obs),
                   'observation_sha256_after': native.sha_bytes(observation),
                   'truth_before': before, 'truth_after': truth(env), 'reward': float(reward),
                   'terminated': bool(terminated), 'truncated': bool(truncated),
                   'info': {k: v for k, v in info.items() if v is None or isinstance(v, (bool, int, float, str))},
                   'policy_response': latest['response'], 'act_including_IPC_ms': latest['act_including_IPC_ms']}
            trace.write(json.dumps(row, allow_nan=False) + '\n')
            trace.flush()
            return output

        env.reset, env.step = reset, step
        return env

    native.PipeWorker, native.make_env = RecordedStudent, recorded_factory
    try:
        execution_directory = directory / 'workers' / case['id']
        execution_directory.mkdir(parents=True, mode=0o700)
        execution = copy_assets(plan, native.clone(plan, execution_directory))
        result, stopped = native.episode(case, plan, path, execution)
    finally:
        native.PipeWorker, native.make_env = original_worker, original_factory
        trace.close()
        target = directory / (case['id'] + '-pixels-actions.npz')
        np.savez_compressed(target, frames=np.asarray(frames, dtype=np.uint8),
                            actions=np.asarray(actions, dtype=np.float32).reshape(-1, 3))
        target.chmod(0o600)
        target = directory / (case['id'] + '-student-masks.npz')
        np.savez_compressed(target, masks=np.asarray(masks, dtype=np.uint8))
        target.chmod(0o600)
        native.write(directory / (case['id'] + '-student-receipts.json'), receipts)
    result.update(initial_historical_receipts_exact=initial_verified,
                  full_recorded_actions=len(actions), full_recorded_frames=len(frames),
                  full_trace_sha256=native.sha(trace_path), student_mask_calls=len(masks),
                  student_model_sha256=plan['student_model_sha256'],
                  policy_changed_relative_to_original_v2=True, policy_changed_since_training=False,
                  privileged_runtime_input=False, extra_teacher_or_renderer_calls=0,
                  historical_comparison_only=True, historical_reuse_new_actions=0,
                  historical_full_stream_reproduction=False, champion_promotion=False)
    native.write(directory / case['id'] / 'student-result.json', result)
    return result, stopped


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', type=Path, required=True)
    path = parser.parse_args().plan.resolve()
    plan = json.loads(path.read_text())
    assert native.sha(path) == (path.parent / 'plan.sha256').read_text().split()[0]
    for group in ['source_sha256', 'reference_sha256']:
        for name, expected in plan[group].items():
            assert native.sha(Path(name)) == expected, name
    assert native.sha(Path(plan['student_model_path'])) == plan['student_model_sha256']
    results, stop_reason = [], None
    for case in plan['cases']:
        if stop_reason is None:
            result, stopped = recorded_episode(case, plan, path)
            if stopped:
                stop_reason = result.get('error', result['failure_type'])
        else:
            result = {'id': case['id'], 'status': 'UNEXECUTED', 'charged_wrapper_actions': 0,
                      'episode_count': 0, 'reason': stop_reason}
        results.append(result)
        native.write(path.parent / 'cohort-results.json', {'results': results, 'stop_reason': stop_reason})
        print(json.dumps({k: result.get(k) for k in ['id', 'status', 'completed', 'official_lap_ms',
              'unique_tiles', 'total_tiles', 'damage', 'charged_wrapper_actions', 'error']}), flush=True)
    return int(stop_reason is not None)


if __name__ == '__main__':
    raise SystemExit(main())
