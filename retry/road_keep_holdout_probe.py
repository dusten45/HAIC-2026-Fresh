"""One-use paired pixel-policy HOLDOUT recorder with aggregate-only output.

The supervisor alone handles condition identities and saved evaluation records.
Each independent actor receives only reset/act and the official observation.
"""
import argparse
import base64
import json
from pathlib import Path
import sys
import signal
import time
import numpy as np
from retry import fresh_dev_distribution as native
from retry.full_route_reproduction import truth
from retry.pixel_sandbox_runtime import SandboxWorker
from retry.paired_audit_gate import verify_readiness, claim_once


def episode(case, plan, path, initial_pairs):
    directory = path.parent
    frames, actions, masks, receipts = [], [], [], []
    latest = {}
    original_worker, original_factory = native.PipeWorker, native.make_env
    trace_path = directory / (case['id'] + '-trace.jsonl')
    trace = trace_path.open('x'); trace_path.chmod(0o600)

    class RecordedWorker(SandboxWorker):
        def __init__(self, command, clean, environment):
            super().__init__(command, clean, environment, sandbox=plan['sandbox_binary'])
            expected = {name: plan['candidate']['members_sha256'][
                'retry/__init__.py' if name == 'retry' else name.replace('.', '/') + '.py']
                for name in self.ready['module_sha256']}
            assert self.ready['module_sha256'] == expected and len(expected) == 14
            assert self.ready['observer_additional_policy_calls'] == 0
            assert len(self.ready['CPU_affinity']) == 1
            if case['arm'] == 'student':
                assert self.ready['student_model_sha256'] == plan['student_model_sha256']
                assert not self.ready['privileged_diagnostic']
                assert self.ready['input_contract'] == 'float32(4,84,84) grayscale only'

        def call(self, operation, observation):
            assert observation.shape == (4,84,84) and observation.dtype == np.float32
            response, duration = super().call(operation, observation)
            if case['arm'] == 'student':
                mask = np.frombuffer(base64.b64decode(response.pop('student_mask_base64')),
                                     dtype=np.uint8).reshape(84,84).copy()
                original = ((observation[-1] > .32) & (observation[-1] < .47)).astype(np.uint8)
                detail = response['student_receipt']
                assert np.isin(mask,[0,1]).all() and np.all(mask <= original)
                assert native.sha_bytes(mask) == detail['student_mask_sha256']
                assert native.sha_bytes(original) == detail['original_P_sha256']
                assert detail['added_cells'] == 0
                masks.append(mask)
                receipts.append({'operation':operation,'observation_sha256':native.sha_bytes(observation),**detail})
            if operation == 'act':
                latest.update(response=response, act_including_IPC_ms=duration)
            return response, duration

    def factory():
        env = original_factory()
        original_reset, original_step = env.reset, env.step
        def reset(*args, **kwargs):
            observation, info = original_reset(*args, **kwargs)
            initial = {'observation':native.sha_bytes(observation),'state':truth(env)}
            pair = case['pair_id']
            if pair in initial_pairs:
                assert initial_pairs[pair] == initial
            else:
                initial_pairs[pair] = initial
            frame = np.rint(observation[-1]*255).astype(np.uint8)
            assert np.array_equal(observation,np.repeat(frame[None],4,axis=0).astype(np.float32)/255)
            frames.append(frame)
            return observation, info
        def step(action):
            index = len(actions); before = truth(env)
            input_obs = np.stack([frames[max(0,j)] for j in range(index-3,index+1)]).astype(np.float32)/255
            output = original_step(action)
            observation, reward, terminated, truncated, info = output
            assert np.array_equal(observation[:3],input_obs[1:])
            frame = np.rint(observation[-1]*255).astype(np.uint8)
            assert np.array_equal(frame.astype(np.float32)/255,observation[-1])
            frames.append(frame); actions.append(np.asarray(action,dtype=np.float32).copy())
            row = {'step':len(actions),'action':actions[-1].tolist(),
                'observation_sha256_before':native.sha_bytes(input_obs),
                'observation_sha256_after':native.sha_bytes(observation),
                'truth_before':before,'truth_after':truth(env),'reward':float(reward),
                'terminated':bool(terminated),'truncated':bool(truncated),
                'info':{k:v for k,v in info.items() if v is None or isinstance(v,(bool,int,float,str))},
                'policy_response':latest['response'],'act_including_IPC_ms':latest['act_including_IPC_ms']}
            trace.write(json.dumps(row,allow_nan=False)+'\n'); trace.flush()
            return output
        env.reset, env.step = reset, step
        return env

    native.PipeWorker, native.make_env = RecordedWorker, factory
    try:
        clean = Path(plan['qualified_runtime'])
        worker = clean / ('worker.py' if case['arm'] == 'student' else 'v2_worker.py')
        execution = (clean, clean/'package', worker, plan['runtime_environment'])
        result, stopped = native.episode(case, plan, path, execution)
    finally:
        native.PipeWorker, native.make_env = original_worker, original_factory
        trace.close()
        target = directory/(case['id']+'-pixels-actions.npz')
        np.savez_compressed(target,frames=np.asarray(frames,dtype=np.uint8),
                            actions=np.asarray(actions,dtype=np.float32).reshape(-1,3));target.chmod(0o600)
        if case['arm'] == 'student':
            target = directory/(case['id']+'-student-masks.npz')
            np.savez_compressed(target,masks=np.asarray(masks,dtype=np.uint8));target.chmod(0o600)
            native.write(directory/(case['id']+'-student-receipts.json'),receipts)
    if stopped and result.get('error') == "RuntimeError('Per-case ceiling without native endpoint')":
        result['failure_type'] = 'per_case_action_cap'; stopped = False
    result.update(pair_id=case['pair_id'],arm=case['arm'],full_recorded_actions=len(actions),
                  full_recorded_frames=len(frames),full_trace_sha256=native.sha(trace_path),
                  student_mask_calls=len(masks),privileged_runtime_input=False,
                  extra_teacher_or_renderer_calls=0,policy_changed_since_training=False,
                  policy_changed_relative_to_original_v2=case['arm']=='student',champion_promotion=False)
    native.write(directory/case['id']/'result.json',result)
    if case['arm'] == 'student':
        native.write(directory/case['id']/'student-result.json',result)
    return result, stopped


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plan',type=Path,required=True)
    path=parser.parse_args().plan.resolve()
    verify_readiness(path)  # A plan alone cannot authorize native execution.
    plan=json.loads(path.read_text());start=time.perf_counter()
    assert native.sha(path)==(path.parent/'plan.sha256').read_text().split()[0]
    for group in ['source_sha256','runtime_sha256']:
        for name,wanted in plan[group].items():assert native.sha(Path(name))==wanted
    qualification=json.loads(Path(plan['qualification_path']).read_text())
    assert qualification['status']=='PASS'
    assert native.sha(Path(plan['qualification_path']))==plan['qualification_sha256']
    claim_once(path)  # Recheck after source hashing; exclusive one-use claim.
    def interrupted(signum, frame):
        raise RuntimeError('Supervisor termination requested')
    signal.signal(signal.SIGTERM, interrupted)
    results=[];initial={};stop_reason=None
    for case in plan['cases']:
        if stop_reason is None:
            result,stopped=episode(case,plan,path,initial)
            if stopped:stop_reason='technical_or_global_resource_boundary'
        else:
            result={'id':case['id'],'pair_id':case['pair_id'],'arm':case['arm'],'status':'UNEXECUTED',
                    'episode_count':0,'charged_wrapper_actions':0,'reason':stop_reason}
            (path.parent/case['id']).mkdir(mode=0o700)
            native.write(path.parent/case['id']/'result.json',result)
        results.append(result)
        native.write(path.parent/'cohort-results.json',{'results':results,'stop_reason':stop_reason})
        print(json.dumps({'processed_episodes':len(results),'total_episodes':8,
                          'native_wall_s':time.perf_counter()-start,'technical_stop':bool(stop_reason)}),flush=True)
    from retry.road_keep_holdout_aggregate import aggregate
    report=aggregate(path.parent,plan['cases'])
    native.write(path.parent.parent/'aggregate.json',report['aggregate'])
    native.write(path.parent.parent/'mechanical-receipt.json',report['mechanical_receipt'])
    return int(stop_reason is not None)

if __name__=='__main__':raise SystemExit(main())
