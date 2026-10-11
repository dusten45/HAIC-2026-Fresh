"""One frozen native episode against a qualified historical pixel baseline.

All reference metadata and receipts stay in a private plan directory. Observer
hooks preserve the native wrapper and make no extra policy or simulator calls.
A planned action ceiling without a native endpoint remains resource censored.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

from retry import fresh_dev_distribution as native
from retry.full_route_reproduction import sha, truth


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', type=Path, required=True)
    path = parser.parse_args().plan.resolve()
    directory = path.parent
    plan = json.loads(path.read_text())
    assert sha(path) == (directory/'plan.sha256').read_text().split()[0]
    for name, expected in plan['source_sha256'].items():
        assert sha(Path(name)) == expected, name
    for name, expected in plan['reference_sha256'].items():
        assert sha(Path(name)) == expected, name
    case = plan['case']
    reference = [json.loads(line) for line in Path(plan['reference_trace']).read_text().splitlines()]
    with np.load(plan['reference_pixels_actions']) as saved:
        old_actions = saved['actions'].copy()
        old_frames = saved['frames'].copy()
    assert len(reference) == len(old_actions) == plan['reference_actions']
    assert len(old_frames) == len(old_actions)+1
    assert old_frames.dtype == np.uint8 and old_actions.dtype == np.float32
    for i, row in enumerate(reference):
        indices = np.maximum(0, np.arange(i-2, i+2))
        obs = old_frames[indices].astype(np.float32)/255
        assert native.sha_bytes(obs) == row['observation_sha256_after']
        assert np.array_equal(old_actions[i], np.asarray(row['action'], dtype=np.float32))

    frames, actions = [], []
    latest = {}
    diagnostics = {'first_action_difference': None, 'first_input_observation_difference': None,
                   'initial_full4_and_truth_exact': False, 'module_hashes_exact': False,
                   'observer_extra_policy_calls': 0, 'observer_extra_simulator_steps': 0}
    original_worker, original_factory = native.PipeWorker, native.make_env
    trace_path = directory/'full-trace.jsonl'
    trace = trace_path.open('x'); trace_path.chmod(0o600)

    class RecordedWorker(original_worker):
        def __init__(self, command, clean, runtime):
            super().__init__(command, clean, runtime)
            expected = {name: plan['candidate']['members_sha256'][
                'retry/__init__.py' if name == 'retry' else name.replace('.', '/')+'.py']
                for name in self.ready['module_sha256']}
            assert self.ready['module_sha256'] == expected
            assert len(expected) == 14 and self.ready['observer_additional_policy_calls'] == 0
            assert len(self.ready['CPU_affinity']) == 1
            diagnostics['module_hashes_exact'] = True

        def call(self, operation, observation):
            response, duration = super().call(operation, observation)
            if operation == 'act':
                latest.update(response=response, act_including_IPC_ms=duration)
            return response, duration

    def recorded_factory():
        env = original_factory()
        original_reset, original_step = env.reset, env.step

        def reset(*args, **kwargs):
            observation, info = original_reset(*args, **kwargs)
            assert native.sha_bytes(observation) == case['baseline_initial_observation_sha256']
            initial = truth(env)
            assert {key: initial[key] for key in case['baseline_initial_truth']} == case['baseline_initial_truth']
            assert np.array_equal(observation, np.repeat(old_frames[:1], 4, axis=0).astype(np.float32)/255)
            frames.append(old_frames[0].copy())
            diagnostics['initial_full4_and_truth_exact'] = True
            return observation, info

        def step(action):
            index = len(actions)
            before = truth(env)
            input_obs = np.stack([frames[max(0,j)] for j in range(index-3,index+1)]).astype(np.float32)/255
            if index < len(old_actions):
                old_obs = old_frames[np.maximum(0,np.arange(index-3,index+1))].astype(np.float32)/255
                if diagnostics['first_input_observation_difference'] is None and not np.array_equal(input_obs, old_obs):
                    diagnostics['first_input_observation_difference'] = index+1
                if diagnostics['first_action_difference'] is None and not np.array_equal(action, old_actions[index]):
                    diagnostics['first_action_difference'] = {
                        'step':index+1, 'same_input_observation':bool(np.array_equal(input_obs,old_obs)),
                        'historical_action':old_actions[index].tolist(), 'candidate_action':action.tolist()}
            output = original_step(action)
            observation, reward, terminated, truncated, info = output
            assert np.array_equal(observation[:3], input_obs[1:])
            frame = np.rint(observation[-1]*255).astype(np.uint8)
            assert np.array_equal(frame.astype(np.float32)/255, observation[-1])
            frames.append(frame); actions.append(np.asarray(action,dtype=np.float32).copy())
            row = {'step':len(actions), 'action':actions[-1].tolist(),
                   'observation_sha256_before':native.sha_bytes(input_obs),
                   'observation_sha256_after':native.sha_bytes(observation),
                   'truth_before':before,'truth_after':truth(env), 'reward':float(reward),
                   'terminated':bool(terminated),'truncated':bool(truncated),
                   'info':{key:value for key,value in info.items()
                           if value is None or isinstance(value,(bool,int,float,str))},
                   'policy_response':latest['response'], 'act_including_IPC_ms':latest['act_including_IPC_ms']}
            trace.write(json.dumps(row,allow_nan=False)+'\n'); trace.flush()
            return output

        env.reset, env.step = reset, step
        return env

    native.PipeWorker, native.make_env = RecordedWorker, recorded_factory
    try:
        execution = native.clone(plan, directory)
        result, stopped = native.episode(case, plan, path, execution)
    finally:
        native.PipeWorker, native.make_env = original_worker, original_factory
        trace.close()
        if frames:
            target = directory/'pixels-actions.npz'
            np.savez_compressed(target, frames=np.asarray(frames,dtype=np.uint8),
                                actions=np.asarray(actions,dtype=np.float32).reshape(-1,3))
            target.chmod(0o600)
        native.write(directory/'paired-diagnostics.json', diagnostics)
    result.update(historical_baseline_reused=True, historical_baseline_new_actions=0,
                  full_recorded_actions=len(actions), full_recorded_frames=len(frames),
                  full_trace_sha256=sha(trace_path), paired_diagnostics=diagnostics)
    native.write(directory/'paired-result.json', result)
    print(json.dumps({key:result.get(key) for key in (
        'status','completed','unique_tiles','total_tiles','official_progress','official_lap_ms',
        'damage','failure_type','charged_wrapper_actions','error','paired_diagnostics')}),flush=True)
    return int(stopped)


if __name__ == '__main__':
    sys.exit(main())
