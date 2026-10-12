"""Evaluate a frozen target rule with only the original stacked pixel input.

The archive can be reused from a component oracle experiment. Its evaluator
and worker must now use original pixel perception/memory with no oracle packet.
"""
from pathlib import Path

import numpy as np


def legal_episode(plan_path, plan, case, arm='L'):
    from retry import frozen_composite_runtime as runtime
    from retry.frozen_paired_evaluation import write
    from retry.path_envelope_candidate import target_episode

    original_prepare = runtime.prepare
    counts = dict(reset_calls=0,act_calls=0,pixel_bytes_per_call=4*84*84*4,
        oracle_packets=0,ego_responses=0,center_replacement_responses=0)
    def prepare(*args, **kwargs):
        worker = original_prepare(*args, **kwargs)
        assert not worker.ready.get('privileged_diagnostic',False)
        assert 'ego_boundary' not in worker.ready
        original_call = worker.call
        def call(operation, obs):
            assert operation in ('reset','act')
            assert isinstance(obs,np.ndarray) and obs.dtype==np.float32 and obs.shape==(4,84,84)
            assert obs.nbytes==counts['pixel_bytes_per_call']
            response,elapsed = original_call(operation,obs)
            counts[operation+'_calls']+=1
            assert 'ego_motion_probe' not in response
            assert 'applied_detected_obstacles_xyr' not in response.get('contact_probe',{})
            return response,elapsed
        worker.call=call
        return worker
    runtime.prepare=prepare
    try:
        result=target_episode(plan_path,plan,case,arm,oracle=False)
    finally:
        runtime.prepare=original_prepare
    if not result.get('error'):
        assert counts['act_calls']==result['successful_wrapper_steps']
        assert counts['reset_calls']==1
    result.update(oracle_inputs_to_policy=False,privileged_diagnostic=False,
        input_boundary='Original float32(4,84,84) pixels only; original pixel detector and tracker.',
        frozen_target_rule=True,champion_promotion=False)
    directory=Path(plan_path).parent/'runs'/(case['id']+'__'+arm)
    write(directory/'result.json',result)
    write(directory/'pixel-boundary.json',dict(counts=counts,
        validated_every_actual_call=True,extra_policy_calls=0,oracle_adapter_calls=0),exclusive=True)
    return result
