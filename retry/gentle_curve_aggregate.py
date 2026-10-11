"""Audit saved scalar-probe output without policy, inference or environment calls."""
import argparse
import json
import math
from pathlib import Path
import time

import numpy as np

from retry.dev_lap_bottleneck import target_limits, weighted
from retry.gentle_curve_patch import gate
from retry.road_keep_saved_records import verify_records


def analyze(directory):
    directory = Path(directory)
    plan = json.loads((directory/'plan.json').read_text())
    cohort = json.loads((directory/'cohort-results.json').read_text())
    ledger = json.loads((directory/'budget.json').read_text())
    results, baseline_rows = [], None
    for case, native in zip(plan['cases'], cohort['results']):
        assert case['id'] == native['id'] and case['coefficient'] == native['coefficient']
        output = {key:native.get(key) for key in ['coefficient','status','completed','official_lap_ms',
            'damage','unique_tiles','total_tiles','official_progress','failure_type','charged_wrapper_actions',
            'raw_step_ticks','raw_reset_ticks','wall_s','sum_sim_step_wall_s','actor_CPU_s','max_act_including_IPC_ms',
            'peak_actor_RSS_MiB','error','reason']}
        if native['status'] == 'UNEXECUTED':
            results.append(output)
            continue
        verified = verify_records(directory, case['id'])
        assert native['worker_reaping']['process_reaped'] and native['worker_reaping']['actor_pids_absent']
        rows = [json.loads(s) for s in (directory/(case['id']+'-trace.jsonl')).read_text().splitlines()]
        assert native['initial_historical_receipts_exact'] and native['student_model_sha256'] == plan['student_model_sha256']
        initial = json.loads((directory/case['id']/'started.json').read_text())
        assert initial['initial_observation_sha256'] == case['baseline_initial_observation_sha256']
        assert initial['initial'] == case['baseline_initial_truth']
        assert initial['geometry_sha256'] == case['road_geometry_sha256']
        assert initial['obstacles_sha256'] == case['expected_physical_obstacles_sha256']
        if case['coefficient'] == 7:
            baseline_rows = rows
        before = np.array([r['truth_before']['time'] for r in rows])
        after = np.array([r['truth_after']['time'] for r in rows])
        finish = rows[-1]['info']['finish_time_s'] if native['completed'] else after[-1]
        dt = np.maximum(0., np.minimum(after, finish)-before)
        active = np.zeros(len(rows), bool)
        delta = np.zeros(len(rows))
        pedal_delta = np.zeros((len(rows), 2))
        targets = np.full(len(rows), np.nan)
        error_max = 0.
        for i, row in enumerate(rows):
            response = row['policy_response']
            telemetry = response['route_telemetry']
            actual = np.asarray(row['action'], dtype=np.float32)
            assert np.array_equal(actual, np.asarray(response['action'], dtype=np.float32))
            diag = response['curve_diagnostic']
            if telemetry['actual_fallback_called']:
                assert diag is None
                continue
            expected = target_limits(telemetry, response['cap_diagnostic'])
            original = np.asarray(diag['baseline_action'], dtype=np.float32)
            base_target = expected['final']
            assert abs(base_target-diag['baseline_final_target']) < 1e-10
            steer = float(.8*np.clip(np.arctan(3.24*expected['curvature']), -.4, .4)
                          + .2*telemetry['previous_steer_before'])
            assert steer == response['previous_steer_after'] == diag['existing_smoothed_steer']
            assert diag['near'] == expected['near']
            active[i] = gate(expected['curvature'], steer, expected['near'])
            assert diag['gate'] == bool(active[i]) and diag['coefficient'] == case['coefficient']
            target = min(28., math.sqrt(case['coefficient']/(abs(expected['curvature'])+.003)),
                         expected['distance']) if active[i] and case['coefficient'] != 7 else base_target
            assert abs(diag['applied_final_target']-target) < 1e-10
            speed = telemetry['speed_estimate']
            expected_base = np.asarray([steer, np.clip(.08*(base_target-speed), 0., .5),
                                       np.clip(.04*(speed-base_target), 0., .5)], dtype=np.float32)
            assert np.array_equal(original, expected_base)
            expected_action = np.asarray([steer, np.clip(.08*(target-speed), 0., .5),
                                          np.clip(.04*(speed-target), 0., .5)], dtype=np.float32)
            assert np.array_equal(actual, expected_action)
            if not active[i] or case['coefficient'] == 7:
                assert np.array_equal(actual, original)
            assert actual[0] == original[0] and diag['steering_unchanged']
            targets[i] = target
            delta[i] = target-base_target
            pedal_delta[i] = actual[1:].astype(float)-original[1:].astype(float)
            assert abs(diag['target_delta']-delta[i]) < 1e-10
            assert abs(diag['throttle_delta']-pedal_delta[i, 0]) < 1e-10
            assert abs(diag['brake_delta']-pedal_delta[i, 1]) < 1e-10
            error_max = max(error_max, float(np.max(abs(actual-expected_action))))
        actions = np.asarray([r['action'] for r in rows])
        target_known = np.isfinite(targets)
        raised = delta > 1e-9
        changed = np.any(pedal_delta != 0, axis=1)
        first_action = first_input = None
        for i, (reference, current) in enumerate(zip(baseline_rows, rows)):
            if first_input is None and current['observation_sha256_before'] != reference['observation_sha256_before']:
                first_input = i+1
            if first_action is None and current['action'] != reference['action']:
                first_action = {'step':i+1, 'same_input':current['observation_sha256_before'] == reference['observation_sha256_before'],
                                'baseline_action':reference['action'], 'candidate_action':current['action']}
        output.update(record_verification=verified, initial_geometry_obstacles_exact=True,
            action_formula_max_abs_error=error_max,
            official_or_observed_sim_s=float(dt.sum()), gate_seconds=float(dt[active].sum()),
            gate_actions=int(active.sum()), target_raised_seconds=float(dt[raised].sum()),
            target_increase_mean_on_gate_m_s=weighted(delta, dt*active),
            target_increase_max_m_s=float(delta.max()),
            applied_target_mean_m_s=weighted(targets[target_known], dt[target_known]),
            pedal_changed_seconds=float(dt[changed].sum()),
            throttle_delta_mean_on_gate=weighted(pedal_delta[:,0], dt*active),
            brake_delta_mean_on_gate=weighted(pedal_delta[:,1], dt*active),
            throttle_mean_whole=weighted(actions[:,1], dt), brake_mean_whole=weighted(actions[:,2], dt),
            throttle_on_seconds=float(dt[actions[:,1] > 1e-6].sum()),
            brake_on_seconds=float(dt[actions[:,2] > 1e-6].sum()),
            contact_actions=len(verified['contact_events']),
            first_action_difference_vs_fresh_baseline=first_action,
            first_input_difference_vs_fresh_baseline=first_input,
            lap_delta_ms_vs_fresh_baseline=native['official_lap_ms']-results[0]['official_lap_ms']
                if results and native['completed'] and results[0]['completed'] else (0 if case['coefficient'] == 7 else None),
            same_input_pedal_deltas_are_not_paired_lap_effects=True)
        if not native['completed']:
            output['failure_location'] = {'step':rows[-1]['step'], 'position':rows[-1]['truth_after']['position'],
                'unique_tiles':native['unique_tiles'], 'total_tiles':native['total_tiles'],
                'first_contact':verified['contact_events'][0] if verified['contact_events'] else None,
                'retire_reason':rows[-1]['info']['retire_reason']}
        results.append(output)
    assert sum(r['charged_wrapper_actions'] for r in results) == ledger['actions'] <= 8000
    assert len(results) == 4
    executed = [r for r in results if r['status'] != 'UNEXECUTED']
    return {'stage':91, 'results':results, 'stop_reason':cohort['stop_reason'],
        'new_wrapper_actions':ledger['actions'], 'native_episodes':len(executed),
        'native_and_recording_wall_s':sum(r['wall_s'] for r in executed),
        'supervisor_execution_wall_s':cohort['execution_and_recording_wall_s'],
        'env_step_wall_s':sum(r['sum_sim_step_wall_s'] for r in executed),
        'actor_CPU_s':sum(r['actor_CPU_s'] or 0 for r in executed),
        'raw_step_ticks':sum(r['raw_step_ticks'] for r in executed),
        'raw_reset_ticks':sum(r['raw_reset_ticks'] for r in executed),
        'champion_promotion':False, 'analysis_new_environment_policy_model_calls':0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, type=Path)
    args = parser.parse_args()
    start = time.perf_counter()
    report = analyze(args.directory)
    report['analysis_wall_s'] = time.perf_counter()-start
    (args.directory/'comparison.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'actions':report['new_wrapper_actions'], 'native_wall_s':report['native_and_recording_wall_s'],
          'results':[{k:r.get(k) for k in ['coefficient','status','official_lap_ms','lap_delta_ms_vs_fresh_baseline',
                    'damage','contact_actions','gate_seconds','target_increase_mean_on_gate_m_s']} for r in report['results']]}))


if __name__ == '__main__':
    main()
