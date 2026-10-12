"""Actual-call route-tie diagnostics; GT remains evaluator-only.

Reuse the compact evaluator for the unchanged speed/steering/pedal laws. Keep
bounded prefix rows and small tie-event samples, with full-episode aggregates.
"""
import hashlib
import json
from collections import deque

import numpy as np

from retry.route_tie_continuity import crossing_side


def tie_episode(plan_path, plan, case, initial_pairs, prefix_reference=None):
    from retry import diagnose, frozen_composite_runtime as runtime
    from retry.compact_dev_diagnostic import compact_episode
    from retry.frozen_paired_evaluation import write
    from retry.full_route_reproduction import truth

    original_factory, original_prepare = diagnose.make_env, runtime.prepare
    state = dict(index=0)
    counts = dict(rows=0, tie_rows=0, changed_selection_rows=0,
                  max_selected_score_excess_m=0.0, max_joint_residual_rad=0.0)
    samples, prefix_rows, recent = [], [], deque(maxlen=20)
    first_contact = None
    first_contact_pre = None
    expected = prefix_reference

    def factory(*args, **kwargs):
        env = original_factory(*args, **kwargs)
        old_step = env.step

        def step(action):
            nonlocal first_contact, first_contact_pre
            index = state['index'] + 1
            before = truth(env)
            response = state['response']
            cp, selection = response['contact_probe'], response['connection_selection']
            assert np.asarray(action, np.float32).tobytes() == np.asarray(response['action'], np.float32).tobytes()
            if expected is not None and index == 112:
                assert before == expected['branch']['before']
                assert selection['tie_continuity']['tie_held']
                old = expected['branch']['response']['contact_probe']
                for name in ['old_HUD_speed_m_s', 'actual_feedback_speed_m_s',
                             'near', 'detected_obstacles_xyr', 'tracker_hazards_after']:
                    assert cp[name] == old[name]
            focus_side = None
            if expected is not None and 85 <= index <= 157:
                obstacle = env.unwrapped.obstacles[expected['focus_obstacle_id']]
                current_body = env.unwrapped.car.hull.GetLocalPoint(tuple(obstacle.position))
                if current_body[1] > 0:
                    focus_side = crossing_side(response['speed_constraint_probe']['selected_path_body'], current_body)
            out = old_step(action)
            after = truth(env)
            joint = max(abs(w['joint_angle'] + float(action[0])) for w in after['wheels'][:2])
            counts['rows'] += 1
            counts['max_joint_residual_rad'] = max(counts['max_joint_residual_rad'], joint)
            tie = selection.get('tie_continuity')
            if tie is not None:
                counts['tie_rows'] += 1
                excess = tie['selected_score_excess_m']
                assert 0 <= excess <= 0.05
                counts['max_selected_score_excess_m'] = max(counts['max_selected_score_excess_m'], excess)
                if tie['tie_held']:
                    counts['changed_selection_rows'] += 1
                    if len(samples) < 8:
                        samples.append(dict(step=index, **tie))
            if cp['curvature'] is not None:
                raw = float(np.clip(np.arctan(3.24 * cp['curvature']), -0.4, 0.4))
                steer = np.float32(.8 * raw + .2 * cp['controller_before']['previous_steer'])
                assert float(steer) == float(action[0])
            row = dict(step=index, focus_side=focus_side, steer=float(action[0]),
                       joint_residual_after_rad=joint, damage_before=before['damage'],
                       damage_after=after['damage'], collision=bool(out[4]['collision']),
                       speed_after_m_s=after['speed_m_s'], tie=tie)
            if first_contact is None and (out[4]['collision'] or after['damage'] > before['damage']):
                first_contact, first_contact_pre = dict(row), list(recent)
            recent.append(row)
            if expected is not None and 85 <= index <= 157:
                prefix_rows.append(row)
            state['index'] = index
            return out

        env.step = step
        return env

    def prepare(*args, **kwargs):
        worker = original_prepare(*args, **kwargs)
        old_call = worker.call

        def call(operation, observation):
            response, elapsed = old_call(operation, observation)
            if operation == 'act':
                index = state['index'] + 1
                if expected is not None and index <= 112:
                    assert hashlib.sha256(observation.tobytes()).hexdigest() == expected['replay']['observation_sha256'][index - 1]
                    if index <= 111:
                        assert np.asarray(response['action'], np.float32).tobytes() == np.asarray(expected['replay']['actions'][index - 1], np.float32).tobytes()
                    else:
                        assert response['action'] != expected['replay']['actions'][index - 1]
                state['response'] = response
            return response, elapsed

        worker.call = call
        return worker

    diagnose.make_env, runtime.prepare = factory, prepare
    try:
        result = compact_episode(plan_path, plan, case, initial_pairs, [])
    finally:
        diagnose.make_env, runtime.prepare = original_factory, original_prepare
    diagnostic = dict(**counts, tie_event_samples=samples, first_contact=first_contact,
                      first_contact_pre_window=first_contact_pre, prefix_rows=prefix_rows,
                      exact_original111_prefix=expected is not None and 'error' not in result,
                      source_steering_and_P_unchanged='error' not in result,
                      oracle_inputs_to_actor=False, extra_policy_or_perception_calls=0)
    write(plan_path.parent / 'runs' / result['role'] / 'tie-diagnostic.json', diagnostic, exclusive=True)
    return result
