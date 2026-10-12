"""Privileged DEV-only receding-horizon diagnostic, not a submission policy.

The pixel worker stays on the frozen nominal archive. The evaluator reads full
current GT and selects source-model futures; only the executed action is sent
back to the worker. Candidate generation and ranking are imported unchanged.
"""
import copy
from pathlib import Path
import time

import numpy as np

from retry.short_sequence_probe import digest
from retry.source_vehicle_transition import SourceVehicleTransition, capture, controls, predict
from retry.transition_ranking_probe import endpoint, select


def build_feedback_worker(source, destination):
    """Add an own-action acknowledgement before the observer's pixel decoder."""
    text = Path(source).read_text()
    marker = "    assert set(request) == {'op','observation'}\n"
    branch = '''    if request['op'] == 'feedback':
        executed = np.frombuffer(base64.b64decode(request['observation']), dtype=np.float32)
        assert executed.shape == (3,) and np.isfinite(executed).all()
        assert np.all(executed >= [-1,0,0]) and np.all(executed <= [1,1,1])
        agent.controller.previous_steer = float(executed[0])
        print(json.dumps(dict(ok=True, executed_action=executed.tolist(),
            previous_steer=agent.controller.previous_steer,
            rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
            actor_cumulative_CPU_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,
            python_audit_denied_events=list(denied))), flush=True)
        continue
'''
    assert text.count(marker) == 1
    text = text.replace(marker, marker + branch)
    compile(text, str(destination), 'exec')
    Path(destination).write_text(text)
    Path(destination).chmod(0o600)


def distribution(values):
    return (dict(count=len(values), sum=float(sum(values)), median=float(np.median(values)),
                 p95=float(np.percentile(values, 95)), max=float(max(values)))
            if values else dict(count=0, sum=0., median=None, p95=None, max=None))


def predict_actions(snapshot, actions):
    """Run explicit controls through the unchanged source transition model."""
    before = time.perf_counter()
    model = SourceVehicleTransition(snapshot)
    reconstruction_wall = time.perf_counter() - before
    restored = dict(tiles=model.initial_tiles_exact, progress=model.initial_progress_exact,
                    bodies=model.initial_bodies_exact)
    rows = []
    integration_start = time.perf_counter()
    try:
        for action in actions:
            row = model.step(np.asarray(action, np.float32))
            rows.append(row)
            if row['terminal']:
                break
    finally:
        model.close()
    return dict(rows=rows, initialization=restored, wall_s=time.perf_counter()-before,
        reconstruction_wall_s=reconstruction_wall,
        integration_wall_s=time.perf_counter()-integration_start,
        event_initialization=model.initial_event_receipt,
        model_physics_ticks=model.native_ticks, zero_time_contact_initializations=1)


def retained_candidate(previous, step, nominal, horizon):
    """Shift by elapsed actions; repeat last command for forecast only.

    Selecting R does not renew the original plan's expiration. Its rank metadata
    measures the constant steering offset from today's nominal anchor. The
    unchanged selector sorts R after C names if every preceding key ties.
    """
    if previous is None:
        return None
    elapsed = step - previous['start_step']
    assert elapsed >= 0
    suffix = previous['actions'][elapsed:]
    if not suffix:
        return None
    assert len(suffix) <= horizon
    actions = [np.asarray(a, np.float32).copy() for a in suffix]
    actions.extend([actions[-1].copy() for _ in range(horizon-len(actions))])
    assert all(float(a[0]) == float(actions[0][0]) for a in actions)
    offset = float(actions[0][0])-float(nominal[0])
    rank_spec = dict(steer_offsets=[offset, offset],
                     brake_first_block=any(a[2] > 0 for a in actions[:horizon//2]))
    return dict(actions=actions, rank_spec=rank_spec, remaining_actions=len(suffix),
                origin_step=previous['start_step'], expires_before=previous['start_step']+horizon)


def oracle_episode(plan_path, plan, case, arm, initial_pairs, replay=None):
    from retry import diagnose, frozen_composite_runtime as runtime
    from retry import frozen_paired_evaluation as paired
    from retry.full_route_reproduction import truth

    oracle = plan['oracle']
    specs = oracle['specifications']
    horizon, interval = oracle['horizon_actions'], oracle['replan_interval_actions']
    assert 1 <= interval <= horizon
    assert all(len(controls([0., 0., 0.], s)) == horizon for s in specs.values())
    state = dict(calls=0, steps=0, feedback_calls=0, pending=[], selection=None,
                 contact_ids=set(), prediction_rows=[], selection_offset=0,
                 previous_plan=None, mode='nominal_fallback')
    decisions, rows = [], []
    counterfactual = {}
    latencies, nominal_latencies, feedback_latencies = [], [], []
    old_factory, old_prepare, old_write = diagnose.make_env, runtime.prepare, paired.write

    def mark_result(result):
        result.update(privileged_diagnostic=True, legal_policy_performance=False,
            oracle_inputs_to_policy=True, GT_inputs_to_pixel_actor=False,
            GT_inputs_to_action_selector=True, future_actor_calls=0,
            own_action_feedback_calls=state['feedback_calls'], champion_promotion_allowed=False)
        return result

    def write(path, value, **kwargs):
        if Path(path).name == 'result.json':
            mark_result(value)
        return old_write(path, value, **kwargs)

    def factory(*args, **kwargs):
        env = old_factory(*args, **kwargs)
        old_reset, old_step = env.reset, env.step

        def reset(*args, **kwargs):
            result = old_reset(*args, **kwargs)
            state['env'] = env
            listener = env.unwrapped.world.contactListener_bug_workaround
            original_contact = listener._contact

            def contact(c, begin):
                if begin:
                    body = listener._match_obstacle_contact(c)
                    if body is not None:
                        state['contact_ids'].update(i for i, o in enumerate(env.unwrapped.obstacles) if o == body)
                return original_contact(c, begin)

            listener._contact = contact
            return result

        def step(action):
            assert state['calls'] == state['steps'] + 1
            assert np.array_equal(action, state['executed'])
            assert state['feedback']['previous_steer'] == float(action[0])
            state['contact_ids'] = set()
            before_time = env.unwrapped.t
            result = old_step(action)
            state['steps'] += 1
            after = truth(env)
            _, _, ended, truncated, info = result
            row = dict(step=state['steps'], action=action.tolist(), nominal_action=state['nominal'].tolist(),
                mode=state['mode'],
                selected=state['selection'], collision=bool(info['collision']),
                contact_obstacle_ids=sorted(state['contact_ids']), damage=after['damage'],
                unique_tiles=after['unique_tiles'], speed_m_s=after['speed_m_s'],
                off_track_counter=after['off_track_counter'],
                wheel_road_contacts=sum(bool(w.tiles) for w in env.unwrapped.car.wheels),
                raw_ticks=round((env.unwrapped.t-before_time)*50), terminal=bool(ended or truncated))
            if state['selection'] is not None:
                predicted = (state['prediction_rows'][state['selection_offset']]
                             if state['selection_offset'] < len(state['prediction_rows']) else None)
                row.update(predicted_collision=(bool(predicted['collision'] or predicted['contact_obstacle_ids']) if predicted else None),
                    predicted_unique_tiles=predicted['unique_tiles'] if predicted else None,
                    predicted_damage=predicted['damage'] if predicted else None,
                    position_error_m=(float(np.linalg.norm(np.asarray(predicted['position'])-after['position']))
                                      if predicted and row['raw_ticks'] == 4 else None))
                state['selection_offset'] += 1
            if replay is not None and state['steps'] <= len(replay['prefix_rows']):
                reference = replay['prefix_rows'][state['steps']-1]
                assert all(row[k] == reference[k] for k in
                    ('action','nominal_action','collision','contact_obstacle_ids','damage','unique_tiles',
                     'speed_m_s','off_track_counter','wheel_road_contacts','raw_ticks','terminal')), 'Replay prefix differs'
            rows.append(row)
            return result

        env.reset, env.step = reset, step
        return env

    def prepare(*args, **kwargs):
        worker = old_prepare(*args, **kwargs)
        old_call = worker.call

        def call(operation, observation):
            assert operation in ('reset', 'act')
            assert observation.shape == (4, 84, 84) and observation.dtype == np.float32
            before = time.perf_counter()
            response, nominal_ms = old_call(operation, observation)
            if operation == 'reset':
                return response, nominal_ms
            nominal = runtime.validate_response(response, plan['arms'][arm], observation, 'act')
            state['calls'] += 1
            assert state['calls'] == state['steps'] + 1
            nominal_latencies.append(nominal_ms)
            state['nominal'] = nominal
            replan = replay is None and (state['calls'] - 1) % interval == 0
            if replay is not None:
                prefix_length = len(replay['prefix_rows'])
                if state['calls'] <= prefix_length:
                    reference = replay['prefix_rows'][state['calls']-1]
                    assert np.array_equal(nominal, np.asarray(reference['nominal_action'], np.float32))
                    state['pending'] = [np.asarray(reference['action'], np.float32)]
                    state['mode'] = 'replay_prefix'
                elif state['calls'] == prefix_length+1:
                    t = time.perf_counter()
                    snapshot = capture(state['env'])
                    capture_wall = time.perf_counter()-t
                    assert digest(snapshot) == replay['snapshot_digest'], 'Pre-suffix GT state differs'
                    assert np.array_equal(nominal, np.asarray(replay['boundary_nominal'], np.float32))
                    retained = retained_candidate(replay['previous_plan'], state['calls'], nominal, horizon)
                    assert retained is not None and retained['remaining_actions'] == replay['suffix_length']
                    cpu, wall = time.process_time(), time.perf_counter()
                    prediction = predict(snapshot, nominal, specs)
                    original_scores = {name: endpoint(v['rows'], horizon, snapshot['unique_tiles'])
                                       for name, v in prediction['candidates'].items()}
                    assert original_scores == replay['boundary_scores'], 'Frozen six-candidate forecast differs'
                    extra = predict_actions(snapshot, retained['actions'])
                    duplicate = predict_actions(snapshot, controls(nominal, specs['C08']))
                    model_cpu, batch_wall = time.process_time()-cpu, time.perf_counter()-wall
                    assert all(all(v['initialization'].values()) for v in
                               [*prediction['candidates'].values(), extra, duplicate])
                    assert endpoint(duplicate['rows'], horizon, snapshot['unique_tiles']) == original_scores['C08']
                    scores = dict(original_scores, R=endpoint(extra['rows'], horizon, snapshot['unique_tiles']))
                    with_suffix = select(scores, dict(specs, R=retained['rank_spec']))
                    with_duplicate = select(dict(original_scores, D=original_scores['C08']), dict(specs, D=specs['C08']))
                    counterfactual.update(prefix_actions=prefix_length, snapshot=snapshot,
                        prefix_scalar_and_action_identity=True, boundary_nominal_identity=True,
                        initial_state_digest=digest(snapshot), original_scores_identical=True,
                        suffix_actions=[a.tolist() for a in retained['actions'][:replay['suffix_length']]],
                        padded_forecast_actions=[a.tolist() for a in retained['actions']],
                        suffix_prediction=extra, equal_query_duplicate_prediction=duplicate,
                        original_six_prediction=prediction, original_six_selected=select(original_scores, specs),
                        seven_with_suffix_selected=with_suffix, seven_with_duplicate_selected=with_duplicate,
                        suffix_scores_9=endpoint(extra['rows'], replay['suffix_length'], snapshot['unique_tiles']),
                        padded_suffix_scores_12=scores['R'], frozen_before_actual_suffix=True)
                    all_queries = [*prediction['candidates'].values(), extra, duplicate]
                    decisions.append(dict(step=state['calls'], selected='R_CF', eligible=with_suffix,
                        scores=scores, invalid_initializations=[], capture_wall_s=capture_wall,
                        model_CPU_s=model_cpu, model_batch_wall_s=batch_wall,
                        reconstruction_wall_s=sum(v['reconstruction_wall_s'] for v in all_queries),
                        integration_wall_s=sum(v['integration_wall_s'] for v in all_queries),
                        model_physics_ticks=sum(v['model_physics_ticks'] for v in all_queries), model_queries=len(all_queries)))
                    state.update(pending=retained['actions'][:replay['suffix_length']], selection='R_CF',
                                 prediction_rows=extra['rows'], selection_offset=0, mode='counterfactual_suffix')
                    directory = plan_path.parent / 'runs' / (case['id']+'__'+arm)
                    old_write(directory / 'counterfactual-prediction.json', counterfactual, exclusive=True)
            if replan:
                t = time.perf_counter()
                snapshot = capture(state['env'])
                capture_wall = time.perf_counter() - t
                cpu, wall = time.process_time(), time.perf_counter()
                predicted = predict(snapshot, nominal, specs)
                active_specs = dict(specs)
                retained = (retained_candidate(state['previous_plan'], state['calls'], nominal, horizon)
                            if oracle.get('retain_suffix', False) else None)
                if retained is not None:
                    predicted['candidates']['R'] = predict_actions(snapshot, retained['actions'])
                    predicted['model_physics_ticks'] += predicted['candidates']['R']['model_physics_ticks']
                    active_specs['R'] = retained['rank_spec']
                model_cpu = time.process_time() - cpu
                predicted['batch_wall_s'] = time.perf_counter() - wall
                scores = {name: endpoint(v['rows'], horizon, snapshot['unique_tiles'])
                          for name, v in predicted['candidates'].items()}
                invalid = [name for name, v in predicted['candidates'].items()
                           if not all(v['initialization'].values())]
                eligible = select({n: s for n, s in scores.items() if n not in invalid}, active_specs)
                chosen = eligible[0] if eligible else None
                state['selection'] = chosen
                if chosen == 'R':
                    assert retained['remaining_actions'] >= interval
                    selected_actions = retained['actions']
                elif chosen is not None:
                    selected_actions = controls(nominal, specs[chosen])
                    if oracle.get('retain_suffix', False):
                        state['previous_plan'] = dict(start_step=state['calls'], actions=selected_actions)
                else:
                    selected_actions = []
                state['pending'] = selected_actions[:interval]
                state['mode'] = 'selected' if chosen is not None else 'nominal_fallback'
                state['prediction_rows'] = predicted['candidates'][chosen]['rows'] if chosen else []
                state['selection_offset'] = 0
                decisions.append(dict(step=state['calls'], anchor=nominal.tolist(),
                    initial_state_digest=digest(snapshot), current_damage=snapshot['damage'],
                    eligible=eligible, invalid_initializations=invalid, selected=chosen,
                    retained_remaining_actions=retained['remaining_actions'] if retained else 0,
                    retained_origin_step=retained['origin_step'] if retained else None,
                    fallback_reason=None if chosen else 'no_admissible_valid_candidate',
                    scores=scores, capture_wall_s=capture_wall, model_CPU_s=model_cpu,
                    model_batch_wall_s=predicted['batch_wall_s'],
                    reconstruction_wall_s=sum(v['reconstruction_wall_s'] for v in predicted['candidates'].values()),
                    integration_wall_s=sum(v['integration_wall_s'] for v in predicted['candidates'].values()),
                    model_physics_ticks=predicted['model_physics_ticks'], model_queries=len(predicted['candidates'])))
            executed = state['pending'].pop(0) if state['pending'] else nominal.copy()
            executed = np.asarray(executed, dtype=np.float32)
            feedback, feedback_ms = old_call('feedback', executed)
            assert feedback['ok'] and feedback['previous_steer'] == float(executed[0])
            assert np.array_equal(np.asarray(feedback['executed_action'], np.float32), executed)
            assert not feedback['python_audit_denied_events']
            state.update(executed=executed, feedback=feedback)
            state['feedback_calls'] += 1
            feedback_latencies.append(feedback_ms)
            response = copy.deepcopy(response)
            response.update(action=executed.tolist(), actor_cumulative_CPU_s=feedback['actor_cumulative_CPU_s'],
                            rss_mib=max(response['rss_mib'], feedback['rss_mib']))
            response['memory']['previous_steer'] = feedback['previous_steer']
            latency = (time.perf_counter() - before) * 1000
            latencies.append(latency)
            if replan or (replay is not None and state['calls'] == len(replay['prefix_rows'])+1):
                decisions[-1]['full_decision_wall_ms'] = latency
            return response, latency

        worker.call = call
        return worker

    diagnose.make_env, runtime.prepare, paired.write = factory, prepare, write
    try:
        result = paired.episode(plan_path, plan, case, arm, initial_pairs)
    finally:
        diagnose.make_env, runtime.prepare, paired.write = old_factory, old_prepare, old_write
    selected_rows = [r for r in rows if r['selected'] is not None]
    diagnostics = dict(decisions=decisions, actual_steps=rows,
        all_action_decision_ms=distribution(latencies), nominal_actor_IPC_ms=distribution(nominal_latencies),
        feedback_IPC_ms=distribution(feedback_latencies),
        replan_decision_ms=distribution([d['full_decision_wall_ms'] for d in decisions if 'full_decision_wall_ms' in d]),
        model_queries=sum(d['model_queries'] for d in decisions),
        model_physics_ticks=sum(d['model_physics_ticks'] for d in decisions),
        model_CPU_s=sum(d['model_CPU_s'] for d in decisions),
        selected_steps=len(selected_rows), fallback_steps=sum(r['mode']=='nominal_fallback' for r in rows),
        replayed_prefix_steps=sum(r['mode']=='replay_prefix' for r in rows),
        counterfactual_steps=sum(r['mode']=='counterfactual_suffix' for r in rows),
        selected_contact_steps=sum(bool(r['collision'] or r['contact_obstacle_ids']) for r in selected_rows),
        selected_prefix_false_negative_steps=sum(bool(r['collision'] or r['contact_obstacle_ids'])
                                                and r['predicted_collision'] is False for r in selected_rows),
        selected_prefix_tile_mismatch_steps=sum(r['unique_tiles'] != r['predicted_unique_tiles'] for r in selected_rows
                                               if r['predicted_unique_tiles'] is not None),
        selected_prefix_position_error_m=distribution([r['position_error_m'] for r in selected_rows if r['position_error_m'] is not None]),
        GT_scope='Full current hull/wheels/actuators, damage, road fixture geometry/friction/visited state, obstacles and current wheel tile membership.',
        policy_scope='Frozen original normal32 archive sees actual pixels plus own executed action; only previous_steer command memory is replaced with actual float32 steering.',
        boundary='Privileged controller. Fresh source-physics worlds each query, no rendering, no arbitrary solver snapshots, no future pixel-policy calls, no safety guarantee or promotion.')
    directory = plan_path.parent / 'runs' / (case['id'] + '__' + arm)
    old_write(directory / 'oracle-diagnostic.json', diagnostics, exclusive=True)
    return result, diagnostics
