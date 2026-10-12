"""Compare privileged short-horizon predictions with actual candidate futures."""
import itertools
import time
import datetime as dt

import numpy as np

from retry.frozen_paired_evaluation import write, sha
from retry.short_sequence_probe import sequence_episode, digest
from retry.source_vehicle_transition import capture, predict


def predict_before_suffix(plan_path, plan, case, arm, initial_pairs, destination,
                          specifications, prefix_reference=None):
    """Freeze predictions from current state before the first actual suffix step."""
    from retry import diagnose, frozen_composite_runtime as runtime
    old_factory, old_prepare = diagnose.make_env, runtime.prepare
    start = plan['arms'][arm]['constants']['sequence-config.json']['start_step']
    state = dict(steps=0, suffix_step_wall_s=0., prediction=None)

    def factory(*args, **kwargs):
        env = old_factory(*args, **kwargs)
        old_step = env.step

        def step(action):
            index = state['steps'] + 1
            if index == start and destination is not None:
                capture_start = time.perf_counter()
                snapshot = capture(env)
                capture_wall = time.perf_counter() - capture_start
                anchor = state['response']['sequence_probe']['anchor_action']
                assert anchor is not None
                destination.mkdir(mode=0o700)
                write(destination / 'input.json', dict(snapshot=snapshot, anchor=anchor), exclusive=True)
                prediction = predict(snapshot, anchor, specifications)
                assert snapshot == capture(env), 'Prediction modified the actual source environment'
                prediction.update(initial_state_digest=digest(snapshot),
                    snapshot_capture_wall_s=capture_wall,
                    frozen_before_actual_suffix_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                    available_actual_suffix_steps=0)
                write(destination / 'prediction.json', prediction, exclusive=True)
                write(destination / 'seal.json', dict(prediction_sha256=sha(destination / 'prediction.json'),
                    input_sha256=sha(destination / 'input.json'), before_actual_suffix=True), exclusive=True)
                state['prediction'] = prediction
            before = time.perf_counter()
            output = old_step(action)
            if index >= start:
                state['suffix_step_wall_s'] += time.perf_counter() - before
            state['steps'] = index
            return output

        env.step = step
        return env

    def prepare(*args, **kwargs):
        worker = old_prepare(*args, **kwargs)
        old_call = worker.call

        def call(*args, **kwargs):
            response, latency = old_call(*args, **kwargs)
            state['response'] = response
            return response, latency

        worker.call = call
        return worker

    diagnose.make_env, runtime.prepare = factory, prepare
    try:
        result, diagnostic = sequence_episode(plan_path, plan, case, arm, initial_pairs, prefix_reference)
    finally:
        diagnose.make_env, runtime.prepare = old_factory, old_prepare
    return result, diagnostic, dict(actual_suffix_env_step_wall_s=state['suffix_step_wall_s'],
                                   prediction=state['prediction'])


def actual_rows(diagnostic, horizon=12):
    rows = []
    for item in diagnostic['suffix'][:horizon]:
        row = dict(item['state'])
        row.update(wheel_road_contacts=item['wheel_road_contacts'], collision=item['collision'],
                   contact_obstacle_ids=item['contact_obstacle_ids'], terminal=item['terminal'])
        rows.append(row)
    return rows


def endpoint(rows, horizon, initial_tiles):
    observed = rows[:horizon]
    assert observed
    end = observed[-1]
    return dict(risk=any(r['collision'] or r['contact_obstacle_ids'] for r in observed),
        terminal=bool(end['terminal']), new_tiles=end['unique_tiles'] - initial_tiles,
        speed_m_s=end['speed_m_s'], road_wheels=end['wheel_road_contacts'],
        maximum_off_track_counter=max(r['off_track_counter'] for r in observed),
        observed_actions=len(observed), position=end['position'], angle=end['angle'], damage=end['damage'])


def select(scores, specifications):
    eligible = [name for name, s in scores.items() if not s['risk'] and not s['terminal']
                and s['new_tiles'] >= 1 and s['maximum_off_track_counter'] <= 5 and s['road_wheels'] >= 2]
    eligible.sort(key=lambda name: (-scores[name]['new_tiles'], -scores[name]['speed_m_s'],
        sum(abs(v) for v in specifications[name]['steer_offsets']),
        int(specifications[name]['brake_first_block']), name))
    return eligible


def compare(predictions, actual, specifications, initial_tiles, horizons=(1, 3, 6, 9, 12)):
    """P4 decisions use cumulative contact and actual candidate order, not MSE."""
    assert set(predictions['candidates']) == set(actual) == set(specifications)
    reports = []
    for horizon in horizons:
        ps = {name: endpoint(v['rows'], horizon, initial_tiles) for name, v in predictions['candidates'].items()}
        ac = {name: endpoint(rows, horizon, initial_tiles) for name, rows in actual.items()}
        false_negative = [n for n in ac if ac[n]['risk'] and not ps[n]['risk']]
        false_positive = [n for n in ac if ps[n]['risk'] and not ac[n]['risk']]
        admitted, actual_eligible = select(ps, specifications), select(ac, specifications)
        correct, inversions, missed_ties = [], [], []
        joint = [n for n in actual_eligible if n in admitted]
        for left, right in itertools.combinations(joint, 2):
            delta = ac[left]['new_tiles'] - ac[right]['new_tiles']
            if delta == 0:
                continue
            predicted = ps[left]['new_tiles'] - ps[right]['new_tiles']
            (missed_ties if predicted == 0 else correct if delta * predicted > 0 else inversions).append([left, right])
        chosen = admitted[0] if admitted else None
        regret = (max(ac[n]['new_tiles'] for n in actual_eligible) - ac[chosen]['new_tiles']
                  if chosen in actual_eligible else None)
        errors = []
        for name in ac:
            if ac[name]['observed_actions'] == ps[name]['observed_actions'] == horizon:
                errors.append(float(np.linalg.norm(np.asarray(ac[name]['position']) - ps[name]['position'])))
        reports.append(dict(horizon_actions=horizon, seconds=.08 * horizon,
            actual_risky=[n for n, s in ac.items() if s['risk']], false_negatives=false_negative,
            false_positives=false_positive, predicted_eligible=admitted, actual_eligible=actual_eligible,
            predicted_selected=chosen, actual_selected=actual_eligible[0] if actual_eligible else None,
            selected_is_actually_eligible=chosen in actual_eligible,
            selected_new_tile_regret=regret, correctly_ordered_pairs=correct,
            inverted_pairs=inversions, strict_pairs_predicted_tied=missed_ties,
            secondary_position_error_m=dict(count=len(errors), mean=float(np.mean(errors)) if errors else None,
                                            max=max(errors) if errors else None),
            predicted=ps, actual=ac))
    final = reports[-1]
    pair_count = sum(len(final[k]) for k in ('correctly_ordered_pairs', 'inverted_pairs', 'strict_pairs_predicted_tied'))
    reasons = []
    if not all(all(v['initialization'].values()) for v in predictions['candidates'].values()):
        reasons.append('OBSERVABLE_INITIAL_STATE_NOT_EXACT')
    if any(r['false_negatives'] for r in reports):
        reasons.append('RISK_OMISSION_AT_REGISTERED_HORIZON')
    if not final['actual_risky'] or len(final['actual_eligible']) < 2:
        reasons.append('INSUFFICIENT_ACTUAL_RISK_OR_SAFE_COVERAGE')
    if len(final['predicted_eligible']) < 2 or not final['selected_is_actually_eligible']:
        reasons.append('INSUFFICIENT_PREDICTED_COVERAGE_OR_UNSAFE_SELECTION')
    if final['selected_new_tile_regret'] != 0:
        reasons.append('SELECTED_PROGRESS_REGRET')
    if final['inverted_pairs'] or pair_count == 0 or len(final['correctly_ordered_pairs']) < .8 * pair_count:
        reasons.append('PROGRESS_ORDER_FAILURE_OR_NO_INFORMATIVE_PAIRS')
    return dict(status='PASS_P4_LOCAL_RANK' if not reasons else 'STOP_P4_LOCAL_RANK', reasons=reasons,
        horizons=reports, conditional_state_transfer_allowed=not reasons,
        boundary='Only common supplied-control intervention. Later return to the pixel policy is not predicted. Pairs/horizons share one initial state and are not independent validation samples.')
