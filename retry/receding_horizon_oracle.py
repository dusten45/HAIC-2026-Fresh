"""Privileged DEV-only receding-horizon diagnostic, not a submission policy.

The pixel worker stays on the frozen nominal archive. The evaluator reads full
current GT and selects source-model futures; only the executed action is sent
back to the worker. Candidate generation is unchanged; an optional visited-prefix
gain precedes the original ranking without changing candidate eligibility.
"""
import copy
from pathlib import Path
import time

import numpy as np

from retry.short_sequence_probe import digest
from retry.source_vehicle_transition import SourceVehicleTransition, capture, controls, predict
from retry.transition_ranking_probe import endpoint, select
from retry.track_feedback_candidate import predict_track_feedback


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


def predict_actions(snapshot, actions, record_road_visits=False):
    """Run explicit controls through the unchanged source transition model."""
    before = time.perf_counter()
    model = SourceVehicleTransition(snapshot)
    reconstruction_wall = time.perf_counter() - before
    restored = dict(tiles=model.initial_tiles_exact, progress=model.initial_progress_exact,
                    bodies=model.initial_bodies_exact)
    rows = []
    initially_visited = {road['idx'] for road in snapshot['roads'] if road['visited']}
    integration_start = time.perf_counter()
    try:
        for action in actions:
            row = model.step(np.asarray(action, np.float32))
            if record_road_visits:
                row['newly_visited_tile_ids'] = sorted(
                    int(road.idx) for road in model.roads if road.road_visited and road.idx not in initially_visited)
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
    preserves the old constant steering offset, or uses block mean absolute
    offsets for a feedback-generated sequence. Final ties still use names.
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
    offset = float(actions[0][0])-float(nominal[0])
    offsets = ([offset, offset] if all(float(a[0]) == float(actions[0][0]) for a in actions) else
        [float(np.mean([abs(float(a[0])-float(nominal[0])) for a in block]))
         for block in (actions[:horizon//2], actions[horizon//2:])])
    rank_spec = dict(steer_offsets=offsets,
                     brake_first_block=any(a[2] > 0 for a in actions[:horizon//2]))
    return dict(actions=actions, rank_spec=rank_spec, remaining_actions=len(suffix),
                origin_step=previous['start_step'], expires_before=previous['start_step']+horizon)


class DiagnosticStop(RuntimeError):
    """A preregistered local gate stopped without another native action."""


def relaxed_selection(scores, specifications, filter_contact=True):
    """Remove both progress tests, keeping contact, terminal, wheels and rank.

    maximum_off_track_counter measures consecutive actions without new tiles,
    not geometric road departure. Dropping only new_tiles>=1 would be redundant
    at a complete 12-action horizon while retaining the <=5 stagnation limit.
    """
    eligible = [name for name, s in scores.items()
                if (not filter_contact or not s['risk']) and not s['terminal'] and s['road_wheels'] >= 2]
    return sorted(eligible, key=lambda name: (-scores[name]['new_tiles'], -scores[name]['speed_m_s'],
        sum(abs(v) for v in specifications[name]['steer_offsets']),
        int(specifications[name]['brake_first_block']), name))


def contiguous_visited_tiles(visited, road_count):
    """One forward prefix in source order 0,1,...,N-1, capped at one lap.

    Tile i spans track[i-1] to track[i]. Reset visits on the back side of
    tile 0 keep their IDs; they cannot bridge an earlier unvisited tile.
    This is a ranking surrogate, never the official finish qualification.
    """
    return next((i for i in range(road_count) if i not in visited), road_count)


def add_contiguous_scores(snapshot, predictions, scores):
    visited = {r['idx'] for r in snapshot['roads'] if r['visited']}
    count = snapshot['road_count']
    before = contiguous_visited_tiles(visited, count)
    for name, prediction in predictions.items():
        for row in prediction['rows']:
            row['contiguous_visited_tiles'] = contiguous_visited_tiles(
                visited | set(row['newly_visited_tile_ids']), count)
        after = prediction['rows'][-1]['contiguous_visited_tiles']
        scores[name].update(contiguous_before_tiles=before,
            contiguous_after_tiles=after, contiguous_gain_tiles=after-before)


def add_new_gap_scores(snapshot, predictions, scores):
    """Count holes only beyond the current frontier in the same tile order."""
    visited = {r['idx'] for r in snapshot['roads'] if r['visited']}
    frontier = max(visited, default=-1)
    for name, prediction in predictions.items():
        after = visited | set(prediction['rows'][-1]['newly_visited_tile_ids'])
        extended = max(after, default=frontier)
        scores[name]['new_internal_gap_tiles'] = sum(
            i not in after for i in range(frontier+1, extended+1))


def forward_track_projection(track, position, velocity, road_indices=None):
    """Nearest source-tile tangent, using the direction reviewed in207.

    Tile i runs track[i-1] to track[i]. The nonadjacent distance gap is
    diagnostic only and never changes eligibility or the binary rank key.
    """
    points = np.asarray(track, dtype=np.float64)[:, -2:]
    starts = np.roll(points, 1, axis=0)
    vectors = points-starts
    squared = np.sum(vectors*vectors, axis=1)
    assert np.all(squared > 0)
    fractions = np.clip(np.sum((np.asarray(position)-starts)*vectors, axis=1)/squared, 0., 1.)
    distances = np.linalg.norm(starts+fractions[:, None]*vectors-position, axis=1)
    indices = np.asarray(road_indices, dtype=int) if road_indices is not None and len(road_indices) else np.arange(len(points))
    index = int(indices[np.argmin(distances[indices])])
    offsets = (np.arange(len(points))-index) % len(points)
    nonadjacent = np.minimum(offsets, len(points)-offsets) > 2
    return dict(road_tile_index=index, distance_m=float(distances[index]),
        nonadjacent_distance_gap_m=float(np.min(distances[nonadjacent])-distances[index]),
        forward_velocity_m_s=float(np.asarray(velocity) @ (vectors[index]/np.sqrt(squared[index]))))


def add_forward_scores(track, predictions, scores):
    for name, prediction in predictions.items():
        end = prediction['rows'][-1]
        projection = forward_track_projection(track, end['position'], end['velocity'])
        scores[name].update(forward_velocity_m_s=projection['forward_velocity_m_s'],
                            forward_projection_gap_m=projection['nonadjacent_distance_gap_m'])


def choose_with_fallback(scores, specifications, enabled, contiguous_rank=False, filter_contact=True, forward_rank=False, new_gap_rank=False):
    original = select({n: s for n, s in scores.items() if not n.startswith('E')}, specifications, filter_contact)
    relaxed = relaxed_selection(scores, specifications, filter_contact) if enabled and not original else []
    if new_gap_rank:
        original.sort(key=lambda n: scores[n]['new_internal_gap_tiles'])
        relaxed.sort(key=lambda n: scores[n]['new_internal_gap_tiles'])
    if contiguous_rank:
        # Stable sorting prepends exactly one key to each unchanged old order.
        original.sort(key=lambda n: -scores[n]['contiguous_gain_tiles'])
        relaxed.sort(key=lambda n: -scores[n]['contiguous_gain_tiles'])
    if forward_rank:
        # Stable binary preference; no magnitude key or new eligibility test.
        original.sort(key=lambda n: scores[n]['forward_velocity_m_s'] < 0.)
        relaxed.sort(key=lambda n: scores[n]['forward_velocity_m_s'] < 0.)
    return original, relaxed, original or relaxed


def forecast_pool(snapshot, nominal, oracle, step, previous_plan, track, previous_steer,
                  record_road_visits=False):
    """Existing pool plus optional frozen controls or model-feedback T."""
    specs, horizon = oracle['specifications'], oracle['horizon_actions']
    if oracle.get('contiguous_forward_rank', False):
        record_road_visits = True
    if record_road_visits:
        candidates = {n: predict_actions(snapshot, controls(nominal, s), True) for n,s in specs.items()}
        predicted = dict(candidates=candidates, model_physics_ticks=sum(q['model_physics_ticks'] for q in candidates.values()))
    else:
        predicted = predict(snapshot, nominal, specs)
    actions = {n: controls(nominal, s) for n,s in specs.items()}
    active_specs = dict(specs)
    if oracle.get('include_nominal_hold', False):
        assert np.isfinite(nominal).all() and np.all(nominal >= [-1,0,0]) and np.all(nominal <= [1,1,1])
        actions['N'] = [nominal.copy() for _ in range(horizon)]
        predicted['candidates']['N'] = predict_actions(snapshot, actions['N'], record_road_visits)
        predicted['model_physics_ticks'] += predicted['candidates']['N']['model_physics_ticks']
        active_specs['N'] = dict(steer_offsets=[0.,0.], brake_first_block=bool(nominal[2]>0))
    retained = retained_candidate(previous_plan, step, nominal, horizon) if oracle.get('retain_suffix', False) else None
    if retained is not None:
        actions['R'] = retained['actions']
        predicted['candidates']['R'] = predict_actions(snapshot, actions['R'], record_road_visits)
        predicted['model_physics_ticks'] += predicted['candidates']['R']['model_physics_ticks']
        active_specs['R'] = retained['rank_spec']
    for name, frozen in oracle.get('fixed_shooting_actions', {}).items():
        assert name.startswith('S') and name not in active_specs
        array = np.asarray(frozen, dtype=np.float32)
        assert array.shape == (horizon, 3) and np.isfinite(array).all()
        assert np.all(array >= [-1., 0., 0.]) and np.all(array <= [1., 1., 1.])
        actions[name] = [row.copy() for row in array]
        predicted['candidates'][name] = predict_actions(snapshot, actions[name], record_road_visits)
        predicted['model_physics_ticks'] += predicted['candidates'][name]['model_physics_ticks']
        active_specs[name] = dict(
            steer_offsets=[float(np.mean(np.abs(block[:, 0]-float(nominal[0]))))
                           for block in (array[:horizon//2], array[horizon//2:])],
            brake_first_block=bool(np.any(array[:horizon//2, 2] > 0)))
    if oracle.get('track_feedback'):
        query = predict_track_feedback(snapshot, track, nominal, previous_steer, oracle['track_feedback'], horizon)
        predicted['candidates']['T'] = query
        predicted['model_physics_ticks'] += query['model_physics_ticks']
        actions['T'] = [np.asarray(a,np.float32) for a in query['actions']]
        active_specs['T'] = query['rank_spec']
    return predicted, active_specs, retained, actions


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
                 previous_plan=None, mode='nominal_fallback', progress_fallback_active=False)
    decisions, rows = [], []
    counterfactual = {}
    latencies, nominal_latencies, feedback_latencies = [], [], []
    old_factory, old_prepare, old_write = diagnose.make_env, runtime.prepare, paired.write

    def mark_result(result):
        result.update(privileged_diagnostic=True, legal_policy_performance=False,
            oracle_inputs_to_policy=True, GT_inputs_to_pixel_actor=False,
            GT_inputs_to_action_selector=True, future_actor_calls=0,
            own_action_feedback_calls=state['feedback_calls'], champion_promotion_allowed=False)
        result['nominal_policy_calls'] = state['calls']
        result['actor_cumulative_CPU_s'] = max(result.get('actor_cumulative_CPU_s', 0.), state.get('last_actor_CPU_s', 0.))
        if state.get('diagnostic_stop') and result.get('error', '').startswith('DiagnosticStop:'):
            result.pop('error')
            result.update(diagnostic_stop=state['diagnostic_stop'], retire_reason=state['diagnostic_stop'],
                completed=False, terminal_observed=False, censored=True,
                unique_tiles=rows[-1]['unique_tiles'] if rows else 0,
                damage=rows[-1]['damage'] if rows else 0, total_tiles=state.get('road_count', 0))
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
            if oracle.get('track_feedback') or oracle.get('forward_direction_rank', False):
                state['track'] = [list(map(float, point)) for point in env.unwrapped.track]
            if oracle.get('contiguous_forward_rank', False):
                road = env.unwrapped.road
                assert [int(t.idx) for t in road] == list(range(len(road)))
                state['reset_visited_tiles'] = sorted(int(t.idx) for t in road if t.road_visited)
                assert 0 in state['reset_visited_tiles'], 'Expected reset contact at source start tile'
            if oracle.get('record_track_diagnostic', False):
                directory = plan_path.parent / 'runs' / (case['id']+'__'+arm)
                old_write(directory / 'track-diagnostic.json', dict(
                    track=[list(map(float, point)) for point in env.unwrapped.track],
                    reset_visited_tiles=state.get('reset_visited_tiles'),
                    initial_finish_tracker=vars(env.unwrapped.finish_line_tracker)), exclusive=True)
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
                mode=state['mode'], progress_fallback_intervention=state['progress_fallback_active'],
                selected=state['selection'], collision=bool(info['collision']),
                contact_obstacle_ids=sorted(state['contact_ids']), damage=after['damage'],
                unique_tiles=after['unique_tiles'], speed_m_s=after['speed_m_s'],
                off_track_counter=after['off_track_counter'],
                wheel_road_contacts=sum(bool(w.tiles) for w in env.unwrapped.car.wheels),
                raw_ticks=round((env.unwrapped.t-before_time)*50), terminal=bool(ended or truncated))
            if oracle.get('record_track_diagnostic', False):
                tracker = env.unwrapped.finish_line_tracker
                row.update(position=after['position'], velocity=after['velocity'], angle=after['angle'],
                    wheel_tile_ids=sorted({int(t.idx) for w in env.unwrapped.car.wheels for t in w.tiles}),
                    unvisited_tiles=[int(t.idx) for t in env.unwrapped.road if not t.road_visited],
                    finish_tracker={key: getattr(tracker, key) for key in (
                        'departed_start_area', 'crossing_from_back', 'previous_longitudinal',
                        'previous_lateral', 'qualified_time_s', 'candidate_crossing_time_s', 'finish_time_s')})
            if oracle.get('contiguous_forward_rank', False):
                row['contiguous_visited_tiles'] = contiguous_visited_tiles(
                    {int(t.idx) for t in env.unwrapped.road if t.road_visited}, len(env.unwrapped.road))
            if state['selection'] is not None:
                predicted = (state['prediction_rows'][state['selection_offset']]
                             if state['selection_offset'] < len(state['prediction_rows']) else None)
                row.update(predicted_collision=(bool(predicted['collision'] or predicted['contact_obstacle_ids']) if predicted else None),
                    predicted_unique_tiles=predicted['unique_tiles'] if predicted else None,
                    predicted_damage=predicted['damage'] if predicted else None,
                    predicted_road_wheels=predicted['wheel_road_contacts'] if predicted else None,
                    predicted_no_new_tile_actions=predicted['off_track_counter'] if predicted else None,
                    predicted_terminal=predicted['terminal'] if predicted else None,
                    predicted_contiguous_visited_tiles=predicted.get('contiguous_visited_tiles') if predicted else None,
                    angle_error_rad=(abs(predicted['angle']-after['angle'])
                                     if predicted and row['raw_ticks'] == 4 else None),
                    speed_error_m_s=(abs(predicted['speed_m_s']-after['speed_m_s'])
                                     if predicted and row['raw_ticks'] == 4 else None),
                    position_error_m=(float(np.linalg.norm(np.asarray(predicted['position'])-after['position']))
                                      if predicted and row['raw_ticks'] == 4 else None))
                state['selection_offset'] += 1
            if replay is not None and state['steps'] <= len(replay['prefix_rows']):
                reference = replay['prefix_rows'][state['steps']-1]
                assert all(row[k] == reference[k] for k in
                    ('action','nominal_action','collision','contact_obstacle_ids','damage','unique_tiles',
                     'speed_m_s','off_track_counter','wheel_road_contacts','raw_ticks','terminal')), 'Replay prefix differs'
            rows.append(row)
            if replay is not None and replay.get('intervention') and row['mode'] == 'local_intervention':
                local = [r for r in rows if r['mode'] == 'local_intervention']
                if len(local) == replay['suffix_length'] or ended or truncated:
                    completed = env.unwrapped.finish_time_s is not None
                    risk = any(r['collision'] or r['contact_obstacle_ids'] for r in local)
                    valid = (not risk and (completed or (len(local) == replay['suffix_length']
                             and not ended and not truncated and row['wheel_road_contacts'] >= 2)))
                    gate = dict(valid=valid, observed_actions=len(local), actual_contact=risk,
                        actual_contact_steps=sum(bool(r['collision'] or r['contact_obstacle_ids']) for r in local),
                        actual_completed=completed, actual_terminal=bool(ended or truncated),
                        actual_new_tiles=row['unique_tiles']-counterfactual['snapshot']['unique_tiles'],
                        actual_damage=row['damage'], actual_speed_m_s=row['speed_m_s'],
                        actual_road_wheels=row['wheel_road_contacts'],
                        actual_maximum_no_new_tile_actions=max(r['off_track_counter'] for r in local),
                        predicted=counterfactual['scores'][counterfactual['selected']],
                        tile_mismatch_steps=sum(r['unique_tiles'] != r['predicted_unique_tiles'] for r in local),
                        speed_error_m_s=distribution([r['speed_error_m_s'] for r in local if r['speed_error_m_s'] is not None]),
                        position_error_m=distribution([r['position_error_m'] for r in local if r['position_error_m'] is not None]))
                    if replay.get('allow_predicted_contact'):
                        # Explicit diagnostic confirmation of a frozen candidate.
                        # Contact and damage are compared with the sealed forecast;
                        # this does not alter the regular 194 candidate selector.
                        limits = replay['match_limits']
                        gate.update(
                            contact_mismatch_steps=sum(bool(r['collision'] or r['contact_obstacle_ids']) != r['predicted_collision'] for r in local),
                            damage_error=distribution([abs(r['damage']-r['predicted_damage']) for r in local]),
                            road_wheel_mismatch_steps=sum(r['wheel_road_contacts'] != r['predicted_road_wheels'] for r in local),
                            no_new_tile_counter_mismatch_steps=sum(r['off_track_counter'] != r['predicted_no_new_tile_actions'] for r in local),
                            terminal_mismatch_steps=sum(r['terminal'] != r['predicted_terminal'] for r in local),
                            angle_error_rad=distribution([r['angle_error_rad'] for r in local if r['angle_error_rad'] is not None]),
                            actual_first_contact_action=next((i+1 for i,r in enumerate(local) if r['collision'] or r['contact_obstacle_ids']), None),
                            predicted_contact_allowed=True,
                        )
                        valid = (len(local) == replay['suffix_length'] and not ended and not truncated
                                 and gate['actual_new_tiles'] >= 1 and gate['tile_mismatch_steps'] == 0
                                 and all(gate[k] == 0 for k in ['contact_mismatch_steps', 'road_wheel_mismatch_steps',
                                     'no_new_tile_counter_mismatch_steps', 'terminal_mismatch_steps'])
                                 and all(gate[k]['max'] is not None and gate[k]['max'] <= tolerance
                                     for k,tolerance in limits.items()))
                        gate['valid'] = valid
                    if replay.get('require_progress_match'):
                        valid = (valid and gate['actual_new_tiles'] >= 1 and gate['tile_mismatch_steps'] == 0
                                 and gate['position_error_m']['max'] is not None
                                 and gate['position_error_m']['max'] <= .001
                                 and gate['speed_error_m_s']['max'] <= .01)
                        gate['valid'] = valid
                    if replay.get('required_tile_ids'):
                        initially_visited = {t['idx'] for t in counterfactual['snapshot']['roads'] if t['visited']}
                        predicted_rows = counterfactual['prediction'][counterfactual['selected']]['rows']
                        all_tiles = set(range(counterfactual['snapshot']['road_count']))
                        gate['required_tiles_visited'] = all(t not in row['unvisited_tiles'] for t in replay['required_tile_ids'])
                        gate['visited_tile_set_mismatch_steps'] = sum(
                            sorted(all_tiles-set(actual['unvisited_tiles'])-initially_visited) != prediction['newly_visited_tile_ids']
                            for actual,prediction in zip(local,predicted_rows))
                        valid = valid and gate['required_tiles_visited'] and gate['visited_tile_set_mismatch_steps'] == 0
                        gate['valid'] = valid
                    state['local_gate'] = gate
                    if replay.get('require_contiguous_match'):
                        gate.update(
                            contiguous_mismatch_steps=sum(r['contiguous_visited_tiles'] != r['predicted_contiguous_visited_tiles'] for r in local),
                            contact_mismatch_steps=sum(bool(r['collision'] or r['contact_obstacle_ids']) != r['predicted_collision'] for r in local),
                            road_wheel_mismatch_steps=sum(r['wheel_road_contacts'] != r['predicted_road_wheels'] for r in local),
                            no_new_tile_counter_mismatch_steps=sum(r['off_track_counter'] != r['predicted_no_new_tile_actions'] for r in local),
                            terminal_mismatch_steps=sum(r['terminal'] != r['predicted_terminal'] for r in local),
                            actual_contiguous_gain_tiles=row['contiguous_visited_tiles']-gate['predicted']['contiguous_before_tiles'])
                        valid = valid and all(gate[k] == 0 for k in ('contiguous_mismatch_steps', 'contact_mismatch_steps',
                            'road_wheel_mismatch_steps', 'no_new_tile_counter_mismatch_steps', 'terminal_mismatch_steps'))
                        gate['valid'] = valid
                    directory = plan_path.parent / 'runs' / (case['id']+'__'+arm)
                    old_write(directory / 'local-intervention-result.json', gate, exclusive=True)
                    if valid:
                        state['replay_complete'] = True
                        if replay.get('restart_probe'):
                            # The one-off 24-action maneuver is not installed as
                            # a recurring recovery mode or renewed retained plan.
                            state['previous_plan'] = None
                    else:
                        state['diagnostic_stop'] = ('frozen_contact_probe_mismatch' if replay.get('allow_predicted_contact') else
                            'local_predicted_safe_contact' if risk else
                            'restart_progress_or_state_mismatch' if replay.get('require_progress_match') else 'local_safety_filter_mismatch')
                    print('Local intervention gate: ' + str(dict(valid=valid, actions=len(local), contact=risk,
                          new_tiles=gate['actual_new_tiles'], speed=gate['actual_speed_m_s'])), flush=True)
            return result

        env.reset, env.step = reset, step
        return env

    def prepare(*args, **kwargs):
        worker = old_prepare(*args, **kwargs)
        old_call = worker.call

        def call(operation, observation):
            assert operation in ('reset', 'act')
            assert observation.shape == (4, 84, 84) and observation.dtype == np.float32
            if operation == 'act' and state.get('diagnostic_stop'):
                raise DiagnosticStop(state['diagnostic_stop'])
            before = time.perf_counter()
            response, nominal_ms = old_call(operation, observation)
            state['last_actor_CPU_s'] = response['actor_cumulative_CPU_s']
            if operation == 'reset':
                return response, nominal_ms
            nominal = runtime.validate_response(response, plan['arms'][arm], observation, 'act')
            state['calls'] += 1
            assert state['calls'] == state['steps'] + 1
            nominal_latencies.append(nominal_ms)
            state['nominal'] = nominal
            if state['calls'] in oracle.get('capture_before_actions', []):
                snapshot = capture(state['env'])
                directory = plan_path.parent / 'runs' / (case['id']+'__'+arm)
                old_write(directory / ('pre-action-'+str(state['calls'])+'.json'), dict(
                    snapshot=snapshot, initial_state_digest=digest(snapshot), nominal=nominal.tolist(),
                    finish_tracker=vars(state['env'].unwrapped.finish_line_tracker)), exclusive=True)
            active_replay = replay is not None and not state.get('replay_complete', False)
            replan = not active_replay and (state['calls'] - 1) % interval == 0
            if active_replay:
                prefix_length = len(replay['prefix_rows'])
                if state['calls'] <= prefix_length:
                    reference = replay['prefix_rows'][state['calls']-1]
                    assert np.array_equal(nominal, np.asarray(reference['nominal_action'], np.float32))
                    state['pending'] = [np.asarray(reference['action'], np.float32)]
                    state['mode'] = 'replay_prefix'
                elif state['calls'] == prefix_length+1 and not replay.get('intervention'):
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
            if active_replay and replay.get('restart_probe') and state['calls'] == prefix_length+1:
                t = time.perf_counter()
                snapshot = capture(state['env'])
                capture_wall = time.perf_counter()-t
                assert digest(snapshot) == replay['snapshot_digest'], 'Restart GT boundary differs'
                assert np.array_equal(nominal, np.asarray(replay['boundary_nominal'], np.float32))
                state['road_count'] = snapshot['road_count']
                if replay['restart_probe'] == 'query':
                    cpu, wall = time.process_time(), time.perf_counter()
                    queries = {n: predict_actions(snapshot, v['actions']) for n,v in replay['candidates'].items()}
                    model_cpu, model_wall = time.process_time()-cpu, time.perf_counter()-wall
                    assert all(all(q['initialization'].values()) for q in queries.values())
                    scores12 = {n: endpoint(q['rows'], 12, snapshot['unique_tiles']) for n,q in queries.items()}
                    scores24 = {n: endpoint(q['rows'], 24, snapshot['unique_tiles']) for n,q in queries.items()}
                    assert {n:scores12[n] for n in replay['boundary_scores']} == replay['boundary_scores']
                    rank_specs = {n:v['rank_spec'] for n,v in replay['candidates'].items()}
                    eligible = relaxed_selection({n:s for n,s in scores24.items() if s['new_tiles'] >= 1}, rank_specs)
                    chosen = eligible[0] if eligible else None
                    counterfactual.update(snapshot=snapshot, initial_state_digest=digest(snapshot), prefix_actions=prefix_length,
                        original_scores_identical=True, prediction=queries, scores12=scores12, scores=scores24,
                        eligible=eligible, selected=chosen, candidate_controls=replay['candidates'],
                        frozen_before_actual_suffix=True, native_actual_candidate_steps=0)
                    decisions.append(dict(step=state['calls'], selected=chosen, eligible=eligible,
                        capture_wall_s=capture_wall, model_CPU_s=model_cpu, model_batch_wall_s=model_wall,
                        reconstruction_wall_s=sum(q['reconstruction_wall_s'] for q in queries.values()),
                        integration_wall_s=sum(q['integration_wall_s'] for q in queries.values()),
                        model_physics_ticks=sum(q['model_physics_ticks'] for q in queries.values()), model_queries=len(queries),
                        full_decision_wall_ms=(time.perf_counter()-before)*1000))
                    directory = plan_path.parent / 'runs' / (case['id']+'__'+arm)
                    old_write(directory / 'restart-prediction.json', counterfactual, exclusive=True)
                    state['diagnostic_stop'] = 'restart_prediction_sealed'
                    raise DiagnosticStop(state['diagnostic_stop'])
                assert replay['restart_probe'] == 'confirm'
                frozen = replay['frozen_prediction']
                assert frozen['initial_state_digest'] == digest(snapshot)
                diagnostic_candidate = replay.get('diagnostic_candidate')
                if diagnostic_candidate is not None:
                    assert ((replay.get('allow_predicted_contact') and not replay.get('require_progress_match'))
                            or (replay.get('require_progress_match') and not frozen['scores'][diagnostic_candidate]['risk']))
                    chosen = diagnostic_candidate
                    assert chosen in frozen['candidate_controls'] and chosen in frozen['prediction']
                else:
                    chosen = frozen['selected']
                    assert chosen is not None and chosen == frozen['eligible'][0]
                counterfactual.update(frozen)
                counterfactual['selected'] = chosen
                actions = [np.asarray(a, np.float32) for a in frozen['candidate_controls'][chosen]['actions']]
                assert len(actions) == replay['suffix_length'] and len(actions) in (12,24)
                state.update(pending=actions, selection=chosen, prediction_rows=frozen['prediction'][chosen]['rows'],
                    selection_offset=0, mode='local_intervention', progress_fallback_active=True, previous_plan=None)
                decisions.append(dict(step=state['calls'], selected=chosen, eligible=frozen['eligible'],
                    selection_reason='preregistered_diagnostic_candidate' if diagnostic_candidate else 'frozen_eligible_rank',
                    capture_wall_s=capture_wall, model_CPU_s=0., model_batch_wall_s=0.,
                    reconstruction_wall_s=0., integration_wall_s=0., model_physics_ticks=0, model_queries=0))
                directory = plan_path.parent / 'runs' / (case['id']+'__'+arm)
                old_write(directory / 'restart-confirmation-boundary.json', dict(initial_state_digest=digest(snapshot),
                    selected=chosen, frozen_prediction_digest=digest(frozen), before_actual_suffix=True,
                    predicted_contact_allowed=bool(replay.get('allow_predicted_contact'))), exclusive=True)
            if active_replay and replay.get('track_probe') == 'query' and state['calls'] == prefix_length+1:
                t = time.perf_counter()
                snapshot = capture(state['env'])
                capture_wall = time.perf_counter()-t
                assert digest(snapshot) == replay['snapshot_digest']
                assert np.array_equal(nominal,np.asarray(replay['boundary_nominal'],np.float32))
                state['road_count'] = snapshot['road_count']
                cpu, wall = time.process_time(), time.perf_counter()
                predicted, active_specs, retained, commands = forecast_pool(snapshot, nominal, oracle, state['calls'],
                    replay['previous_plan'], state['track'], float(state['executed'][0]), True)
                model_cpu, model_wall = time.process_time()-cpu, time.perf_counter()-wall
                scores = {n:endpoint(q['rows'],horizon,snapshot['unique_tiles']) for n,q in predicted['candidates'].items()}
                assert {n:s for n,s in scores.items() if n!='T'} == replay['boundary_scores']
                assert all(all(q['initialization'].values()) for q in predicted['candidates'].values())
                base_scores = {n:s for n,s in scores.items() if n!='T'}
                _,_,old_eligible = choose_with_fallback(base_scores,active_specs,True)
                original,relaxed,eligible = choose_with_fallback(scores,active_specs,True)
                target = set(replay['required_tile_ids'])
                covers = {n:target.issubset(q['rows'][-1]['newly_visited_tile_ids']) for n,q in predicted['candidates'].items()}
                old_covering = [n for n in old_eligible if covers[n]]
                supplements = 'T' in eligible and covers['T'] and not old_covering
                frozen = dict(snapshot=snapshot,initial_state_digest=digest(snapshot),prefix_actions=prefix_length,
                    prediction=predicted['candidates'],scores=scores,eligible=eligible,selected=eligible[0] if eligible else None,
                    original_eligible=original,relaxed_eligible=relaxed,existing_eligible=old_eligible,
                    existing_covering_candidates=old_covering,target_covered=covers,supplements_missing_path=supplements,
                    candidate_controls={n:dict(actions=[a.tolist() for a in commands[n]],rank_spec=active_specs[n]) for n in commands},
                    original_scores_identical=True,frozen_before_actual_suffix=True,native_actual_candidate_steps=0)
                query = predicted['candidates']['T']
                decisions.append(dict(step=state['calls'],selected=frozen['selected'],eligible=eligible,capture_wall_s=capture_wall,
                    model_CPU_s=model_cpu,model_batch_wall_s=model_wall,model_physics_ticks=predicted['model_physics_ticks'],
                    model_queries=len(scores),reconstruction_wall_s=sum(q['reconstruction_wall_s'] for q in predicted['candidates'].values()),
                    integration_wall_s=sum(q['integration_wall_s'] for q in predicted['candidates'].values()),
                    T_control_CPU_s=query['control_CPU_s'],T_control_wall_s=query['control_wall_s'],T_total_wall_s=query['wall_s'],
                    T_reconstruction_wall_s=query['reconstruction_wall_s'],T_integration_wall_s=query['integration_wall_s'],
                    full_decision_wall_ms=(time.perf_counter()-before)*1000))
                directory = plan_path.parent / 'runs' / (case['id']+'__'+arm)
                old_write(directory/'track-candidate-prediction.json',frozen,exclusive=True)
                state['diagnostic_stop'] = 'track_candidate_prediction_sealed'
                raise DiagnosticStop(state['diagnostic_stop'])
            if active_replay and replay.get('intervention') and not replay.get('restart_probe') and state['calls'] == prefix_length+1:
                t = time.perf_counter()
                snapshot = capture(state['env'])
                capture_wall = time.perf_counter()-t
                assert digest(snapshot) == replay['snapshot_digest'], 'Local intervention GT boundary differs'
                assert np.array_equal(nominal, np.asarray(replay['boundary_nominal'], np.float32))
                state['road_count'] = snapshot['road_count']
                cpu = time.process_time()
                predicted = predict(snapshot, nominal, specs)
                model_cpu = time.process_time()-cpu
                scores = {n: endpoint(v['rows'], horizon, snapshot['unique_tiles']) for n,v in predicted['candidates'].items()}
                assert {n:s for n,s in scores.items() if not n.startswith('E')} == replay['boundary_scores']
                assert all(all(v['initialization'].values()) for v in predicted['candidates'].values())
                original, relaxed, eligible = choose_with_fallback(scores, specs, True)
                chosen = eligible[0] if eligible else None
                counterfactual.update(snapshot=snapshot, initial_state_digest=digest(snapshot), prefix_actions=prefix_length,
                    original_scores_identical=True, prediction=predicted, scores=scores, selected=chosen,
                    original_eligible=original, relaxed_existing=relaxed_selection({n:s for n,s in scores.items() if not n.startswith('E')}, specs),
                    relaxed_all=relaxed, frozen_before_actual_suffix=True)
                decisions.append(dict(step=state['calls'], selected=chosen, eligible=eligible, original_eligible=original,
                    progress_fallback_intervention=bool(not original and eligible), scores=scores, invalid_initializations=[],
                    capture_wall_s=capture_wall, model_CPU_s=model_cpu, model_batch_wall_s=predicted['batch_wall_s'],
                    reconstruction_wall_s=sum(v['reconstruction_wall_s'] for v in predicted['candidates'].values()),
                    integration_wall_s=sum(v['integration_wall_s'] for v in predicted['candidates'].values()),
                    model_physics_ticks=predicted['model_physics_ticks'], model_queries=len(predicted['candidates'])))
                directory = plan_path.parent / 'runs' / (case['id']+'__'+arm)
                old_write(directory / 'counterfactual-prediction.json', counterfactual, exclusive=True)
                if chosen is None:
                    state['diagnostic_stop'] = 'no_local_admissible_candidate'
                    raise DiagnosticStop(state['diagnostic_stop'])
                actions = controls(nominal, specs[chosen])
                state.update(pending=actions[:replay['suffix_length']], selection=chosen, prediction_rows=predicted['candidates'][chosen]['rows'],
                    selection_offset=0, mode='local_intervention', progress_fallback_active=not bool(original),
                    previous_plan=dict(start_step=state['calls'], actions=actions))
            if replan:
                t = time.perf_counter()
                snapshot = capture(state['env'])
                capture_wall = time.perf_counter() - t
                cpu, wall = time.process_time(), time.perf_counter()
                predicted, active_specs, retained, all_commands = forecast_pool(
                    snapshot, nominal, oracle, state['calls'], state['previous_plan'], state.get('track'),
                    float(state['executed'][0]) if 'executed' in state else 0.)
                model_cpu = time.process_time() - cpu
                predicted['batch_wall_s'] = time.perf_counter() - wall
                scores = {name: endpoint(v['rows'], horizon, snapshot['unique_tiles'])
                          for name, v in predicted['candidates'].items()}
                rank_cpu, rank_wall = time.process_time(), time.perf_counter()
                contiguous_rank = oracle.get('contiguous_forward_rank', False)
                if contiguous_rank:
                    add_contiguous_scores(snapshot, predicted['candidates'], scores)
                forward_rank = oracle.get('forward_direction_rank', False)
                if forward_rank:
                    add_forward_scores(state['track'], predicted['candidates'], scores)
                new_gap_rank = oracle.get('new_internal_gap_rank', False)
                if new_gap_rank:
                    add_new_gap_scores(snapshot, predicted['candidates'], scores)
                invalid = [name for name, v in predicted['candidates'].items()
                           if not all(v['initialization'].values())]
                _, _, old_order = choose_with_fallback(
                    {n: s for n, s in scores.items() if n not in invalid}, active_specs,
                    oracle.get('relax_progress_fallback', False), filter_contact=oracle.get('filter_predicted_contact', True))
                original, relaxed, eligible = choose_with_fallback(
                    {n: s for n, s in scores.items() if n not in invalid}, active_specs,
                    oracle.get('relax_progress_fallback', False), contiguous_rank, oracle.get('filter_predicted_contact', True))
                before_direction = eligible[0] if eligible else None
                if forward_rank:
                    original, relaxed, eligible = choose_with_fallback(
                        {n: s for n, s in scores.items() if n not in invalid}, active_specs,
                        oracle.get('relax_progress_fallback', False), contiguous_rank,
                        oracle.get('filter_predicted_contact', True), True)
                before_gap = eligible[0] if eligible else None
                if new_gap_rank:
                    original, relaxed, eligible = choose_with_fallback(
                        {n: s for n, s in scores.items() if n not in invalid}, active_specs,
                        oracle.get('relax_progress_fallback', False), contiguous_rank,
                        oracle.get('filter_predicted_contact', True), forward_rank, True)
                rank_cpu, rank_wall = time.process_time()-rank_cpu, time.perf_counter()-rank_wall
                state['progress_fallback_active'] = bool(not original and eligible)
                chosen = eligible[0] if eligible else None
                state['selection'] = chosen
                if chosen == 'R':
                    assert retained['remaining_actions'] >= interval
                    selected_actions = retained['actions']
                elif chosen is not None:
                    selected_actions = all_commands[chosen]
                    if oracle.get('retain_suffix', False):
                        state['previous_plan'] = dict(start_step=state['calls'], actions=selected_actions, origin_candidate=chosen)
                else:
                    selected_actions = []
                state['pending'] = selected_actions[:interval]
                state['mode'] = 'selected' if chosen is not None else 'nominal_fallback'
                state['prediction_rows'] = predicted['candidates'][chosen]['rows'] if chosen else []
                state['selection_offset'] = 0
                decisions.append(dict(step=state['calls'], anchor=nominal.tolist(),
                    initial_state_digest=digest(snapshot), current_damage=snapshot['damage'],
                    eligible=eligible, invalid_initializations=invalid, selected=chosen,
                    old_rank_selected=old_order[0] if old_order else None,
                    contiguous_rank_enabled=contiguous_rank,
                    forward_direction_rank_enabled=forward_rank,
                    before_direction_selected=before_direction,
                    new_internal_gap_rank_enabled=new_gap_rank,
                    before_gap_selected=before_gap,
                    continuity_rank_CPU_s=rank_cpu if contiguous_rank else 0.,
                    continuity_rank_wall_s=rank_wall if contiguous_rank else 0.,
                    original_eligible=original, progress_fallback_intervention=state['progress_fallback_active'],
                    nominal_hold_eligible_primary='N' in original,
                    nominal_hold_eligible_relaxed=bool(relaxed_selection(
                        {'N': scores['N']}, active_specs, oracle.get('filter_predicted_contact', True))) if 'N' in scores and 'N' not in invalid else False,
                    retained_remaining_actions=retained['remaining_actions'] if retained else 0,
                    retained_origin_step=retained['origin_step'] if retained else None,
                    retained_origin_candidate=state['previous_plan'].get('origin_candidate')
                        if chosen == 'R' else None,
                    fallback_reason=None if chosen else 'no_admissible_valid_candidate',
                    scores=scores, capture_wall_s=capture_wall, model_CPU_s=model_cpu,
                    model_batch_wall_s=predicted['batch_wall_s'],
                    reconstruction_wall_s=sum(v['reconstruction_wall_s'] for v in predicted['candidates'].values()),
                    integration_wall_s=sum(v['integration_wall_s'] for v in predicted['candidates'].values()),
                    model_physics_ticks=predicted['model_physics_ticks'], model_queries=len(predicted['candidates']),
                    T_control_CPU_s=predicted['candidates'].get('T',{}).get('control_CPU_s',0.),
                    T_control_wall_s=predicted['candidates'].get('T',{}).get('control_wall_s',0.),
                    T_total_wall_s=predicted['candidates'].get('T',{}).get('wall_s',0.),
                    T_reconstruction_wall_s=predicted['candidates'].get('T',{}).get('reconstruction_wall_s',0.),
                    T_integration_wall_s=predicted['candidates'].get('T',{}).get('integration_wall_s',0.)))
            executed = state['pending'].pop(0) if state['pending'] else nominal.copy()
            executed = np.asarray(executed, dtype=np.float32)
            feedback, feedback_ms = old_call('feedback', executed)
            assert feedback['ok'] and feedback['previous_steer'] == float(executed[0])
            assert np.array_equal(np.asarray(feedback['executed_action'], np.float32), executed)
            assert not feedback['python_audit_denied_events']
            state.update(executed=executed, feedback=feedback)
            state['last_actor_CPU_s'] = feedback['actor_cumulative_CPU_s']
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
        local_gate=state.get('local_gate'), diagnostic_stop=state.get('diagnostic_stop'),
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
        selected_prefix_contiguous_mismatch_steps=sum(r.get('contiguous_visited_tiles') != r['predicted_contiguous_visited_tiles']
            for r in selected_rows if r.get('predicted_contiguous_visited_tiles') is not None and r['raw_ticks'] == 4),
        selected_prefix_position_error_m=distribution([r['position_error_m'] for r in selected_rows if r['position_error_m'] is not None]),
        GT_scope='Full current hull/wheels/actuators, damage, road fixture geometry/friction/visited state, obstacles and current wheel tile membership.',
        policy_scope='Frozen original normal32 archive sees actual pixels plus own executed action; only previous_steer command memory is replaced with actual float32 steering.',
        boundary='Privileged controller. Fresh source-physics worlds each query, no rendering, no arbitrary solver snapshots, no future pixel-policy calls, no safety guarantee or promotion.')
    directory = plan_path.parent / 'runs' / (case['id'] + '__' + arm)
    old_write(directory / 'oracle-diagnostic.json', diagnostics, exclusive=True)
    return result, diagnostics
