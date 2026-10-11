"""Evaluate a frozen historical HUD reader on saved official observations.

No environment, policy, model or renderer is imported. Truth supplies offline
error labels only. Pedal comparisons hold the saved final target fixed; they
are not safe-action labels or a closed-loop counterfactual. Detailed inputs
and outputs must remain in the caller's private research directory.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time
from types import SimpleNamespace

import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_speed(image, integrals, speeds):
    """Exact historical current-frame ROI and interpolation, without fitting."""
    integral = float(image[74:83, 11:13].sum())
    return float(np.interp(integral, integrals, speeds)), integral


def pedals(target, speed):
    return np.asarray([np.clip(.08 * (target - speed), 0., .5),
                       np.clip(.04 * (speed - target), 0., .5)], np.float32)


def longest_run(steps):
    longest = current = 0
    previous = None
    for step in steps:
        current = current + 1 if previous is not None and step == previous + 1 else 1
        longest = max(longest, current)
        previous = step
    return longest


def error_summary(values):
    values = np.asarray(values, float)
    if not len(values):
        return None
    return dict(mae=float(np.mean(values)), p95=float(np.percentile(values, 95)),
                p99=float(np.percentile(values, 99)), maximum=float(np.max(values)))


def summarize(rows):
    output = {'n': len(rows), 'fallback_n': sum(r['fallback'] for r in rows)}
    for name in ('old', 'bar'):
        item = {'speed_error': error_summary([r[name + '_error'] for r in rows])}
        for direction in ('wrong_brake', 'wrong_gas'):
            selected = [r['step'] for r in rows if r[name + '_' + direction]]
            item[direction] = {'count': len(selected), 'longest_run': longest_run(selected)}
        item['pedal_error'] = error_summary([r[name + '_pedal_error'] for r in rows
                                             if not r['fallback']])
        output[name] = item
    output['corrected_wrong_brakes'] = sum(r['old_wrong_brake'] and not r['bar_wrong_brake'] for r in rows)
    output['introduced_wrong_brakes'] = sum(not r['old_wrong_brake'] and r['bar_wrong_brake'] for r in rows)
    output['corrected_wrong_gas'] = sum(r['old_wrong_gas'] and not r['bar_wrong_gas'] for r in rows)
    output['introduced_wrong_gas'] = sum(not r['old_wrong_gas'] and r['bar_wrong_gas'] for r in rows)
    output['changed_pedals'] = sum(r['changed_pedals'] for r in rows)
    output['distance_cap_binding'] = sum(r['distance_cap_binding'] for r in rows)
    output['first_step'] = rows[0]['step'] if rows else None
    output['last_step'] = rows[-1]['step'] if rows else None
    return output


def gate_group(summary, epsilon=1e-6, minimum_n=5, strict_mae=False):
    if summary['n'] < minimum_n:
        return {'status': 'INSUFFICIENT_SUPPORT', 'checks': {}}
    old, bar = summary['old'], summary['bar']
    checks = {'error_' + metric: bar['speed_error'][metric] <= old['speed_error'][metric] + epsilon
              for metric in ('mae', 'p95', 'p99', 'maximum')}
    if strict_mae:
        checks['strict_mae_reduction'] = bar['speed_error']['mae'] < old['speed_error']['mae'] - epsilon
    for direction in ('wrong_brake', 'wrong_gas'):
        for metric in ('count', 'longest_run'):
            checks[direction + '_' + metric] = bar[direction][metric] <= old[direction][metric]
    return {'status': 'PASS' if all(checks.values()) else 'FAIL', 'checks': checks}


def historical_reader_method(path):
    """Load only the reviewed pure method, without importing its policy class."""
    tree = ast.parse(Path(path).read_text())
    methods = [member for node in tree.body if isinstance(node, ast.ClassDef)
               for member in node.body if isinstance(member, ast.FunctionDef)
               and member.name == 'read_bar_speed']
    assert len(methods) == 1
    namespace = {'np': np}
    exec(compile(ast.Module(body=methods, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace['read_bar_speed']


def inspect_stream(spec, spatial, table, old_method, epsilon):
    files = spec['files']
    rows = [json.loads(line) for line in Path(files['trace']).read_text().splitlines()]
    result = json.loads(Path(files['result']).read_text())
    with np.load(files['pixels_actions'], allow_pickle=False) as saved:
        frames, actions = saved['frames'], saved['actions']
    assert frames.dtype == np.uint8 and actions.dtype == np.float32
    assert frames.shape == (len(rows) + 1, 84, 84)
    assert len(rows) == len(actions) == len(spatial['records']) == result['charged_wrapper_actions']
    integrals, speeds = np.asarray(table['integrals']), np.asarray(table['speeds'])
    old_self = SimpleNamespace(bar_integrals=integrals, bar_speeds=speeds)
    contact = next((row['step'] for row in rows if row['info']['collision']), None)
    records = []
    for i, (row, aligned) in enumerate(zip(rows, spatial['records'])):
        step = i + 1
        assert row['step'] == aligned['step'] == step
        observation = frames[np.maximum(0, np.arange(i - 3, i + 1))].astype(np.float32) / 255
        assert hashlib.sha256(observation.tobytes()).hexdigest() == row['observation_sha256_before']
        assert np.array_equal(actions[i], np.asarray(row['action'], np.float32))
        if i:
            assert rows[i - 1]['truth_after'] == row['truth_before']
        image = observation[-1]
        bar, integral = read_speed(image, integrals, speeds)
        assert bar == old_method(old_self, image)
        old = max(0., 11.4142485314592 * float(image[74:83, 9:14].sum()) - 6.545558315185489)
        telemetry = row['policy_response']['route_telemetry']
        curve = row['policy_response']['curve_diagnostic']
        cap = row['policy_response']['cap_diagnostic']
        assert old == telemetry['speed_estimate'] == aligned['HUD_speed_m_s']
        truth = row['truth_before']['speed_m_s']
        assert abs(truth - math.hypot(*row['truth_before']['velocity'])) <= 1e-10
        assert truth == aligned['actual_speed_m_s']
        fallback = telemetry['actual_fallback_called']
        target = None if fallback else curve['applied_final_target']
        r = {'step': step, 'pre_time_s': row['truth_before']['time'],
             'arc_m': aligned['arc_m'], 'precontact': contact is None or step < contact,
             'fallback': fallback, 'truth_speed_offline_only': truth, 'old_speed': old,
             'bar_speed': bar, 'bar_integral': integral, 'old_error': abs(old - truth),
             'bar_error': abs(bar - truth), 'target_speed': target,
             'distance_cap_binding': False, 'changed_pedals': False,
             'outside_table_intensity': not integrals[0] <= integral <= integrals[-1],
             'outside_source_speed_domain': not 0 <= truth <= 60,
             'hull_angular_velocity_rad_s': row['truth_before']['angular_velocity'],
             # Historical source warning, not a proof of full resize support
             # separation or invariance to arbitrary other HUD indicators.
             'possible_angular_HUD_overlap': row['truth_before']['angular_velocity'] >= 30.20833333333333}
        for name in ('old', 'bar'):
            r.update({name + '_wrong_brake': False, name + '_wrong_gas': False,
                      name + '_pedal_error': None})
        if not fallback:
            assert target == aligned['target_speed_m_s']
            assert target <= cap['distance_cap'] + 1e-10
            original, changed, label = (pedals(target, value) for value in (old, bar, truth))
            assert np.array_equal(original, actions[i, 1:])
            r['distance_cap_binding'] = abs(target - cap['distance_cap']) <= 1e-10 and cap['cap_active']
            r['changed_pedals'] = not np.array_equal(changed, original)
            r['old_pedals'], r['bar_pedals'], r['truth_label_pedals'] = [x.tolist() for x in (original, changed, label)]
            for name, action in [('old', original), ('bar', changed)]:
                r[name + '_wrong_brake'] = bool(action[1] > epsilon and truth < target - epsilon)
                r[name + '_wrong_gas'] = bool(action[0] > epsilon and truth > target + epsilon)
                r[name + '_pedal_error'] = float(np.max(np.abs(action - label)))
        records.append(r)
    return records, {'status': result['status'], 'completed': result['completed'],
                     'first_contact_step': contact, 'rows': len(rows),
                     'pixel_stack_action_and_time_alignment_exact': True,
                     'historical_method_output_exact': True,
                     'original_final_target_pedals_exact': True}


def audit(contract):
    epsilon = contract['error_gates']['epsilon_for_arithmetic_only']
    minimum = contract['groups']['required_minimum_n_each']
    table = json.loads(Path(contract['historical_table_path']).read_text())
    assert table['ROI'] == dict(row_start=74, row_stop=83, col_start=11, col_stop=13)
    assert np.array_equal(table['integrals'], table['intensities'])
    assert np.array_equal(table['speeds'], table['inverse_speed_m_s'])
    old_paths = [p for p in contract['source_sha256'] if p.endswith('/stage15/sources/bar_feedback_agent.py')]
    assert len(old_paths) == 1
    old_method = historical_reader_method(old_paths[0])
    spatial = json.loads(Path(contract['spatial_records_path']).read_text())
    summaries, detailed, checks, missing = {}, {}, {}, []
    for name, spec in contract['runs'].items():
        rows, integrity = inspect_stream(spec, spatial['runs'][name], table, old_method, epsilon)
        precontact = [r for r in rows if r['precontact']]
        selected = {'whole': rows, 'precontact': precontact,
                    'precursor': [r for r in precontact if 430 <= r['arc_m'] < 445],
                    'recovery': [r for r in precontact if 445 <= r['arc_m'] < 455]}
        groups = {}
        for group_name, group in selected.items():
            summary = summarize(group)
            decision = gate_group(summary, epsilon, minimum, group_name == 'whole')
            key = name + '/' + group_name
            if decision['status'] == 'INSUFFICIENT_SUPPORT':
                missing.append(key)
            checks.update({key + '/' + k: v for k, v in decision['checks'].items()})
            strata = []
            for lo, hi in zip(contract['groups']['speed_strata_m_s'][:-1],
                              contract['groups']['speed_strata_m_s'][1:]):
                subset = [r for r in group if lo <= r['truth_speed_offline_only'] < hi
                          or hi == 60 and r['truth_speed_offline_only'] == 60]
                stats = summarize(subset)
                result = gate_group(stats, epsilon, minimum)
                # Frozen strata gate tests errors; pedal counts are required on
                # each complete group, not additionally in sparse speed strata.
                result['checks'] = {k: v for k, v in result['checks'].items() if k.startswith('error_')}
                if stats['n'] >= minimum:
                    result['status'] = 'PASS' if all(result['checks'].values()) else 'FAIL'
                    checks.update({key + '/speed_' + str(lo) + '_' + str(hi) + '/' + k: v
                                   for k, v in result['checks'].items()})
                elif name == 'k14-cap40' and group_name in ('whole', 'recovery') and lo == 0:
                    missing.append(key + '/required_low_speed')
                strata.append({'range_m_s': [lo, hi], 'summary': stats, 'gate': result})
            groups[group_name] = {'summary': summary, 'gate': decision, 'speed_strata': strata}
        checks[name + '/source_speed_domain'] = all(not r['outside_source_speed_domain'] for r in rows)
        checks[name + '/source_intensity_domain'] = all(not r['outside_table_intensity'] for r in rows)
        checks[name + '/HUD_angular_warning_not_triggered'] = all(not r['possible_angular_HUD_overlap'] for r in rows)
        summaries[name] = {'integrity': integrity, 'groups': groups,
                          'hull_angular_velocity_range_rad_s': [min(r['hull_angular_velocity_rad_s'] for r in rows),
                                                                 max(r['hull_angular_velocity_rad_s'] for r in rows)],
                          'domain_counts': {k: sum(r[k] for r in rows) for k in
                                            ('outside_source_speed_domain', 'outside_table_intensity', 'possible_angular_HUD_overlap')}}
        detailed[name] = rows
    primary = [r for r in detailed['k14-cap40'] if r['precontact'] and 445 <= r['arc_m'] < 455 and r['step'] > 251]
    critical = summarize(primary)
    checks['primary_recovery/strict_false_brake_reduction'] = critical['bar']['wrong_brake']['count'] < critical['old']['wrong_brake']['count']
    checks['primary_recovery/corrected_original_false_brake'] = critical['corrected_wrong_brakes'] > 0
    checks['distinct_context/current_distance_cap_binds_in_precontact_recovery'] = critical['distance_cap_binding'] > 0
    failed = [name for name, passed in checks.items() if not passed]
    status = 'FAIL' if failed else 'INCONCLUSIVE' if missing else 'PASS'
    return {'gate_status': status, 'native102_admitted_by_saved_gate': status == 'PASS',
            'checks': checks, 'failed_checks': failed, 'insufficient_required_support': missing,
            'streams': summaries, 'primary_recovery_after_prefix': critical,
            'distinct_context_is_new_method': False,
            'prior_stage16_and19_rejections_retained': True,
            'offline_truth_is_safe_action_label': False}, detailed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', type=Path, required=True)
    parser.add_argument('--preflight', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert np.__version__ == '1.26.0'
    assert not args.output.exists()
    contract = json.loads(args.contract.read_text())
    preflight = json.loads(args.preflight.read_text())
    assert preflight['review_pass'] and preflight['contract_sha256'] == sha(args.contract)
    assert preflight['analysis_code_sha256'] == sha(__file__)
    assert datetime.now(timezone.utc) < datetime.fromisoformat(contract['authorization_end_utc'])
    for path, expected in contract['source_sha256'].items():
        assert sha(path) == expected, path
    claim = args.output.with_name('execution-claim.json')
    with claim.open('x') as output:
        json.dump({'at_utc': datetime.now(timezone.utc).isoformat(),
                   'contract_sha256': sha(args.contract), 'analysis_code_sha256': sha(__file__)}, output)
    claim.chmod(0o600)
    started, cpu = time.perf_counter(), time.process_time()
    result, detailed = audit(contract)
    result.update(evaluated_at_utc=datetime.now(timezone.utc).isoformat(),
                  contract_sha256=sha(args.contract), analysis_code_sha256=sha(__file__),
                  saved_evaluation_wall_s=time.perf_counter() - started,
                  saved_evaluation_CPU_s=time.process_time() - cpu,
                  new_wrapper_actions=0, environment_policy_model_renderer_fit_calls=0,
                  frame_count=sum(len(rows) for rows in detailed.values()),
                  candidate_reader_calls=sum(len(rows) for rows in detailed.values()),
                  historical_pure_reader_parity_calls=sum(len(rows) for rows in detailed.values()))
    for path, expected in contract['source_sha256'].items():
        assert sha(path) == expected, path
    result['source_guards_unchanged'] = len(contract['source_sha256'])
    detail_path = args.output.with_name('frame-diagnostics.json')
    assert not detail_path.exists()
    for path, data in [(detail_path, detailed), (args.output, result)]:
        path.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
        path.chmod(0o600)
    print(json.dumps({k: result[k] for k in ('gate_status', 'failed_checks',
          'insufficient_required_support', 'frame_count', 'saved_evaluation_wall_s',
          'saved_evaluation_CPU_s', 'new_wrapper_actions')}))


if __name__ == '__main__':
    main()
