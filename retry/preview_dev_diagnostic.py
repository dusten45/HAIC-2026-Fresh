"""Bounded diagnostics for the single frozen visible-curvature preview.

Observe actual calls without changing policy inputs/actions or invoking perception.
The same-input nominal pedal comparison is arithmetic, not a policy replay.
"""
import hashlib
import time

import numpy as np

from retry.compact_dev_diagnostic import ScalarStats, scalar_row, window_summary
from retry.visible_curvature_preview import visible_curvature_preview


def preview_episode(plan_path, plan, case, initial_pairs, arm='A'):
    from retry import diagnose, frozen_composite_runtime as runtime
    from retry.frozen_paired_evaluation import episode, write
    from retry.full_route_reproduction import truth

    original_factory, original_prepare = diagnose.make_env, runtime.prepare
    stats, state = ScalarStats(), {}
    observation_hash, action_hash = hashlib.sha256(), hashlib.sha256()
    law = dict(rows=0, target_lowered_rows=0, pedal_changed_rows=0,
               outside_near_changes=0, target_drop_sum_m_s=0.0,
               max_target_drop_m_s=0.0, all_source_steering_and_P_checks_pass=True)
    started = time.perf_counter()

    def factory(*args, **kwargs):
        env = original_factory(*args, **kwargs)
        original_reset, original_step = env.reset, env.step

        def reset(*args, **kwargs):
            output = original_reset(*args, **kwargs)
            state['obs'] = output[0]
            observation_hash.update(output[0].tobytes())
            return output

        def step(action):
            before = truth(env)
            response = state['response']
            assert state['input_sha'] == hashlib.sha256(state['obs'].tobytes()).hexdigest()
            saved = np.asarray(action, dtype=np.float32).copy()
            assert saved.tobytes() == np.asarray(response['action'], np.float32).tobytes()
            output = original_step(action)
            after = truth(env)
            assert np.array_equal(saved, action)
            trace = dict(step=stats.rows+1, truth_before=before, truth_after=after,
                         action=saved.tolist(), collision=bool(output[4]['collision']))
            stats.add(scalar_row(trace, response['contact_probe'], stats.elapsed))
            action_hash.update(saved.tobytes())
            observation_hash.update(output[0].tobytes())
            state['obs'] = output[0]
            return output

        env.reset, env.step = reset, step
        return env

    def prepare(*args, **kwargs):
        worker = original_prepare(*args, **kwargs)
        original_call = worker.call

        def call(operation, obs):
            response, elapsed = original_call(operation, obs)
            if operation == 'act':
                cp = response['contact_probe']
                assert response['observer_extra_policy_calls'] == 0
                before = cp['controller_before']
                assert before['lateral_acceleration'] == (8.0 if cp['near'] else 24.0)
                assert before['speed_cap'] == 45.0
                target = cp['target_speed_m_s']
                law['rows'] += 1
                if target is not None:
                    k = cp['curvature']
                    nominal = min(45.0, float(np.sqrt(before['lateral_acceleration']/max(abs(k), 1e-6))))
                    path = response['speed_constraint_probe']['selected_path_body']
                    preview = (visible_curvature_preview(path, cp['old_HUD_speed_m_s'], 8.0)['speed_limit_m_s']
                               if cp['near'] else None)
                    assert preview == cp['preview_speed_m_s']
                    assert nominal == cp['nominal_target_speed_m_s']
                    assert target == (min(nominal, preview) if preview is not None else nominal)

                    def pedals(value):
                        feedback = cp['actual_feedback_speed_m_s']
                        return np.asarray([np.clip(.08*(value-feedback), 0, .5),
                                           np.clip(.04*(feedback-value), 0, .5)], np.float32).tolist()

                    steer = .8*float(np.clip(np.arctan(3.24*k), -.4, .4)) + .2*before['previous_steer']
                    assert response['action'] == [float(np.float32(steer)), *pedals(target)]
                    drop = nominal-target
                    changed = response['action'][1:] != pedals(nominal)
                    assert cp['near'] or (drop == 0 and not changed)
                    law['target_lowered_rows'] += drop > 1e-12
                    law['pedal_changed_rows'] += changed
                    law['target_drop_sum_m_s'] += drop
                    law['max_target_drop_m_s'] = max(law['max_target_drop_m_s'], drop)
                state.update(response=response, input_sha=hashlib.sha256(obs.tobytes()).hexdigest())
            return response, elapsed

        worker.call = call
        return worker

    diagnose.make_env, runtime.prepare = factory, prepare
    try:
        result = episode(plan_path, plan, case, arm, initial_pairs)
    finally:
        diagnose.make_env, runtime.prepare = original_factory, original_prepare
    if 'error' not in result:
        assert stats.rows == result['successful_wrapper_steps']
        assert action_hash.hexdigest() == result['action_sequence_sha256']
        assert observation_hash.hexdigest() == result['observation_sequence_sha256']
    diagnostic = stats.summary(result['completed'])
    diagnostic.pop('near5_rows')
    diagnostic.update(near_mode_rows=stats.near, selected_near_budget=8.0,
        actual_intervention=law, official_lap_ms=result.get('lap_ms'),
        terminal_actual_action=stats.last,
        terminal_previous_at_most20_summary=window_summary(stats.before_last),
        full_frame_GT_policy_streams_saved=0, extra_environment_policy_model_calls=0,
        actual_stream_hashes_match='error' not in result,
        wall_including_short_record_s=time.perf_counter()-started)
    write(plan_path.parent/'runs'/(case['id']+'__'+arm)/'compact-diagnostic.json', diagnostic, exclusive=True)
    return result
