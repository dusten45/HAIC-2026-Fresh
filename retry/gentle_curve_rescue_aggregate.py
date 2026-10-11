"""Two-arm saved DEV audit; damaged completion is still native completion.

Retains reported outcomes when evidence is missing/invalid, explicitly without
verification. Immediate target shadows and cap dwell are not lap-time causes.
No environment, policy, renderer or model execution occurs here.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np

from retry.dev_lap_bottleneck import target_limits, weighted
from retry.gentle_curve_patch import gate
from retry.gentle_curve_limit_segments import summarize
from retry.road_keep_saved_records import verify_records


def _per_action(rows, coefficient, completed):
    if not rows:
        raise ValueError('no successful trace rows to audit')
    finish = rows[-1]['info']['finish_time_s'] if completed else rows[-1]['truth_after']['time']
    dt = np.array([max(0., min(r['truth_after']['time'], finish)-r['truth_before']['time']) for r in rows])
    active, delta, pedals = np.zeros(len(rows), bool), np.zeros(len(rows)), np.zeros((len(rows), 2))
    for i, row in enumerate(rows):
        response, actual = row['policy_response'], np.asarray(row['action'], np.float32)
        telemetry, diag = response['route_telemetry'], response['curve_diagnostic']
        assert np.array_equal(actual, np.asarray(response['action'], np.float32))
        if telemetry['actual_fallback_called']:
            assert diag is None
            continue
        expected = target_limits(telemetry, response['cap_diagnostic'])
        base = expected['final']
        steer = float(.8*np.clip(np.arctan(3.24*expected['curvature']), -.4, .4)
                      + .2*telemetry['previous_steer_before'])
        assert steer == response['previous_steer_after'] == diag['existing_smoothed_steer']
        assert expected['near'] == diag['near'] and abs(base-diag['baseline_final_target']) < 1e-10
        active[i] = gate(expected['curvature'], steer, expected['near'])
        assert bool(active[i]) == diag['gate'] and coefficient == diag['coefficient']
        target = min(28., math.sqrt(coefficient/(abs(expected['curvature'])+.003)), expected['distance']) if active[i] and coefficient != 7 else base
        assert abs(target-diag['applied_final_target']) < 1e-10
        speed = telemetry['speed_estimate']
        action = lambda t: np.asarray([steer, np.clip(.08*(t-speed), 0., .5),
                                      np.clip(.04*(speed-t), 0., .5)], np.float32)
        original = np.asarray(diag['baseline_action'], np.float32)
        assert np.array_equal(original, action(base)) and np.array_equal(actual, action(target))
        assert original[0] == actual[0] and diag['steering_unchanged']
        delta[i], pedals[i] = target-base, actual[1:].astype(float)-original[1:].astype(float)
        assert abs(delta[i]-diag['target_delta']) < 1e-10
        assert abs(pedals[i, 0]-diag['throttle_delta']) < 1e-10
        assert abs(pedals[i, 1]-diag['brake_delta']) < 1e-10
    limits = summarize(rows, dt)
    return {'official_or_observed_sim_s': float(dt.sum()), 'gate_actions': int(active.sum()),
            'gate_seconds': float(dt[active].sum()), 'target_raised_seconds': float(dt[delta > 1e-9].sum()),
            'pedal_changed_seconds': float(dt[np.any(pedals != 0, axis=1)].sum()),
            'target_increase_mean_on_gate_m_s': weighted(delta, dt*active),
            'target_increase_max_m_s': float(delta.max()),
            'actual_limit_segments': limits, 'action_formula_max_abs_error': 0.,
            'same_input_pedal_deltas_are_not_causal_lap_effects': True}


def _verify_case(directory, case, native):
    saved = json.loads((directory/case['id']/'result.json').read_text())
    assert saved == json.loads((directory/case['id']/'student-result.json').read_text())
    for key in ('status', 'completed', 'official_lap_ms', 'damage', 'charged_wrapper_actions'):
        assert saved.get(key) == native.get(key)
    assert saved['status'] in ('COMPLETE', 'DNF', 'RESOURCE_CENSORED', 'TECHNICAL_ERROR')
    assert bool(saved.get('completed')) == (saved['status'] == 'COMPLETE')
    verified = verify_records(directory, case['id'])
    started = json.loads((directory/case['id']/'started.json').read_text())
    assert started['initial'] == case['baseline_initial_truth']
    assert started['initial_observation_sha256'] == case['baseline_initial_observation_sha256']
    assert started['geometry_sha256'] == case['road_geometry_sha256']
    assert started['obstacles_sha256'] == case['expected_physical_obstacles_sha256']
    assert saved['student_model_sha256'] == json.loads((directory/'plan.json').read_text())['student_model_sha256']
    assert saved['worker_reaping']['process_reaped'] and saved['worker_reaping']['actor_pids_absent']
    rows = [json.loads(s) for s in (directory/(case['id']+'-trace.jsonl')).read_text().splitlines()]
    assert len(rows) == verified['actions'] == saved['successful_wrapper_steps']
    metrics = _per_action(rows, case['coefficient'], bool(saved['completed']))
    if saved['completed']:
        assert abs(metrics['official_or_observed_sim_s']-saved['official_lap_ms']/1000) < 1e-8
    metrics.update(record_verification=verified, verification_pass=True)
    segments = metrics['actual_limit_segments']['segments']
    for segment in segments:
        first, last = rows[segment['start_step']-1], rows[segment['end_step']-1]
        segment.update(start_progress_tiles=first['truth_before']['unique_tiles'],
                       end_progress_tiles=last['truth_after']['unique_tiles'],
                       total_tiles=saved['total_tiles'],
                       lap_time_start_s=segment['start_time_s']-rows[0]['truth_before']['time'],
                       lap_time_end_s=segment['end_time_s']-rows[0]['truth_before']['time'])
    exits = {'curvature_fast7':0, 'global28':0, 'age0distance':0,
             'curvature_safe5':0, 'fallback':0, 'tie_or_other':0}
    for before, after in zip(segments[:-1], segments[1:]):
        if (before['curvature_subtype'] != 'gate14' or after['curvature_subtype'] == 'gate14'
                or abs(before['end_time_s']-after['start_time_s']) > 1e-10):
            continue
        label = ('curvature_' + after['curvature_subtype']
                 if after['class'] == 'curvature' else after['class'])
        exits[label if label in exits else 'tie_or_other'] += 1
    metrics['gate14_exit_counts'] = exits
    metrics['segment_progress_is_wrapper_after_not_exact_finish_tick_bitmap'] = True
    if saved['status'] == 'DNF':
        metrics['native_failure_endpoint'] = {'step':rows[-1]['step'],
            'position':rows[-1]['truth_after']['position'],
            'retire_reason':rows[-1]['info']['retire_reason'],
            'unique_tiles':saved['unique_tiles'], 'total_tiles':saved['total_tiles']}
    elif not saved['completed']:
        metrics['interrupted_observation_endpoint'] = {'step':rows[-1]['step'],
            'position':rows[-1]['truth_after']['position'], 'kind':saved['status']}
    return metrics, rows


def analyze(directory):
    directory = Path(directory)
    plan = json.loads((directory/'plan.json').read_text())
    cohort = json.loads((directory/'cohort-results.json').read_text())
    ledger = json.loads((directory/'budget.json').read_text())
    if (len(plan['cases']) != 2 or [c['coefficient'] for c in plan['cases']] != [7, 14]
            or plan['max_actions'] != 4000 or len(cohort['results']) != 2
            or len(plan['stage_budgets']) != 2 or any(v != 2000 for v in plan['stage_budgets'].values())):
        raise ValueError('exactly two ordered 7/14 arms and 4000/2000 ceilings required')
    assert set(plan['stage_budgets']) == {c['id'] for c in plan['cases']}
    for key in ('condition', 'seed', 'road_geometry_sha256', 'expected_physical_obstacles_sha256',
                'baseline_initial_truth', 'baseline_initial_observation_sha256'):
        if key in plan['cases'][0] or key in plan['cases'][1]:
            assert plan['cases'][0][key] == plan['cases'][1][key], 'paired condition: '+key
    results, traces, errors = [], {}, []
    for case, native in zip(plan['cases'], cohort['results']):
        assert case['id'] == native['id'] and case['coefficient'] == native['coefficient']
        item = {k:native.get(k) for k in ('coefficient','status','completed','official_lap_ms',
            'damage','unique_tiles','total_tiles','charged_wrapper_actions','successful_wrapper_steps',
            'raw_step_ticks','raw_reset_ticks','wall_s','sum_sim_step_wall_s','actor_CPU_s',
            'max_act_including_IPC_ms','peak_actor_RSS_MiB','error','reason','failure_type')}
        item['verification_pass'] = False
        if native['status'] == 'UNEXECUTED':
            item['verification_status'] = 'NOT_EXECUTED'
        else:
            try:
                metrics, rows = _verify_case(directory, case, native)
                item.update(metrics, verification_status='PASS')
                traces[case['coefficient']] = rows
            except Exception as error:
                item['verification_status'] = 'MISSING_OR_INVALID_EVIDENCE'
                item['verification_error'] = type(error).__name__+': '+str(error)
                errors.append({'coefficient':case['coefficient'], 'error':item['verification_error']})
        results.append(item)
    baseline, candidate = results
    mechanical = all(r['verification_pass'] for r in results)
    counts = {status:sum(r['status'] == status for r in results)
              for status in ('COMPLETE','DNF','RESOURCE_CENSORED','TECHNICAL_ERROR','UNEXECUTED')}
    claimed = sum(r['charged_wrapper_actions'] or 0 for r in results)
    cost_valid = claimed == ledger['actions'] and 0 <= ledger['actions'] <= 4000
    expected_ids = {c['id'] for c in plan['cases']}
    cost_valid = (cost_valid and set(ledger.get('stages', {})) <= expected_ids
        and all(isinstance(r['charged_wrapper_actions'], int)
                and 0 <= r['charged_wrapper_actions'] <= 2000
                and ledger.get('stages', {}).get(c['id'], 0) == r['charged_wrapper_actions']
                for c, r in zip(plan['cases'], results)))
    if not cost_valid:
        errors.append({'kind':'BUDGET_LEDGER_MISMATCH_OR_CAP','reported_sum':claimed,'ledger_actions':ledger['actions']})
    reproduction_path = directory/'baseline-reproduction.json'
    reproduction = json.loads(reproduction_path.read_text()) if reproduction_path.exists() else None
    qualified = bool(reproduction and reproduction.get('status') == 'PASS')
    if qualified:
        try:
            assert reproduction == cohort['baseline_qualification']
            assert reproduction['official_lap_ms'] == baseline['official_lap_ms'] == plan['cases'][0]['expected_baseline_lap_ms']
            assert reproduction['damage'] == baseline['damage'] == plan['cases'][0]['expected_baseline_damage']
            assert all(reproduction[name] is True for name in ('frames_exact','actions_exact','masks_exact'))
        except Exception as error:
            qualified = False
            errors.append({'kind':'BASELINE_QUALIFICATION_MISMATCH', 'error':type(error).__name__+': '+str(error)})
    else:
        errors.append({'kind':'BASELINE_QUALIFICATION_MISSING_OR_FAILED'})
    common = mechanical and qualified and cost_valid and baseline.get('completed') is True and candidate.get('completed') is True
    pair = {'baseline_reproduction_pass':qualified, 'both_records_verified':mechanical,
        'both_completed_verified':common,
        'common_completed_lap_delta_ms':candidate['official_lap_ms']-baseline['official_lap_ms'] if common else None,
        'native_completion_lost_verified':mechanical and qualified and baseline.get('completed') is True and candidate['status'] == 'DNF',
        'candidate_status':candidate['status'],'candidate_resource_censored':candidate['status']=='RESOURCE_CENSORED',
        'candidate_technical_or_missing_evidence':candidate['status']=='TECHNICAL_ERROR' or bool(errors),
        'baseline_damage':baseline['damage'],'candidate_damage':candidate['damage'],
        'damage_delta':candidate['damage']-baseline['damage'] if mechanical else None,
        'damage_is_separate_warning_not_completion_definition':True}
    if 7 in traces and 14 in traces:
        first = next((i for i,(b,c) in enumerate(zip(traces[7],traces[14])) if b['action'] != c['action']), None)
        pair['first_action_difference'] = None if first is None else {'step':first+1,
            'same_pre_observation':traces[7][first]['observation_sha256_before']==traces[14][first]['observation_sha256_before'],
            'same_pre_truth':traces[7][first]['truth_before']==traces[14][first]['truth_before']}
    return {'stage':93,'results':results,'pair':pair,'reported_status_counts':counts,
        'all_required_evidence_verified':mechanical and qualified and cost_valid,
        'verification_errors':errors,'new_wrapper_actions':ledger['actions'],
        'reported_charged_sum':claimed,'budget_ledger_pass':cost_valid,'stop_reason':cohort.get('stop_reason'),
        'interpretation':'One previously observed DEV rescue condition, one run per arm; preservation and lap differences are conditional evidence, not generalization or safety guarantees.',
        'champion_promotion':False,'analysis_environment_policy_model_renderer_calls':0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, type=Path)
    args = parser.parse_args()
    started = time.perf_counter()
    report = analyze(args.directory)
    report['analysis_wall_s'] = time.perf_counter()-started
    (args.directory/'comparison.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'actions':report['new_wrapper_actions'],'pair':report['pair'],
                      'verification_pass':report['all_required_evidence_verified']}))


if __name__ == '__main__':
    main()
