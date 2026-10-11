"""Saved-input cap dwell and segment arithmetic; no policy or simulator calls.

The duplicate 28 sentinel counts as one global cap. Joint minima remain ties,
not an arbitrarily selected cause. Caller supplies endpoint-clipped seconds.
Own-input 7/14 comparisons do not decompose closed-loop lap-time differences.
"""
import math


TOL = 1e-10
ORDER = ('global28', 'curvature', 'age0distance')


def _limits(row):
    response = row['policy_response']
    telemetry = response['route_telemetry']
    if telemetry['actual_fallback_called']:
        assert response['curve_diagnostic'] is None
        return {'label': 'fallback', 'subtype': None, 'active': ['fallback']}, None
    diag = response['curve_diagnostic']
    cap = response['cap_diagnostic']
    assert cap.get('cap_input_scope', 'age_zero') == 'age_zero'
    x, y = telemetry['controller_target']
    k = 2 * x / max(x*x + y*y, 1e-6)
    assert abs(k - diag['curvature']) <= TOL
    near, gate = bool(diag['near']), bool(diag['gate'])
    assert gate == (not near and .015 <= abs(k) <= .05
                    and abs(diag['existing_smoothed_steer']) <= .18)
    baseline_coef = 5. if near else 7.
    coef = float(diag['coefficient']) if gate else baseline_coef
    raw_distance = min((max(4., math.sqrt(10 * d))
                        for d in cap['radial_clearances']), default=math.inf)
    limits = {'global28': 28., 'curvature': math.sqrt(coef / (abs(k) + .003)),
              'age0distance': raw_distance}
    target = min(limits.values())
    baseline = min(28., math.sqrt(baseline_coef / (abs(k) + .003)), raw_distance)
    assert abs(target - diag['applied_final_target']) <= TOL
    assert abs(baseline - diag['baseline_final_target']) <= TOL
    active = [name for name in ORDER if abs(limits[name] - target) <= TOL]
    label = active[0] if len(active) == 1 else 'tie:' + '+'.join(active)
    subtype = ('safe5' if near else ('gate' + str(int(coef)) if gate and coef != 7. else 'fast7'))
    item = {'label': label, 'active': active,
            'subtype': subtype if 'curvature' in active else None}
    shadow = None
    if gate:
        curve7 = math.sqrt(7. / (abs(k) + .003))
        curve14 = math.sqrt(14. / (abs(k) + .003))
        t7, t14 = min(28., curve7, raw_distance), min(28., curve14, raw_distance)
        speed = telemetry['speed_estimate']
        pedals = lambda t: (min(.5, max(0., .08*(t-speed))),
                            min(.5, max(0., .04*(speed-t))))
        # float32 output equality includes clipping and output quantization.
        import struct
        shadow = {'delta': t14-t7, 'partly_masked': t14 < curve14-TOL,
                  'pedals_equal': struct.pack('ff', *pedals(t7)) == struct.pack('ff', *pedals(t14)),
                  'mask_label': '+'.join(n for n, v in [('global28', 28.),
                        ('age0distance', raw_distance)] if v <= curve14+TOL)}
    return item, shadow


def summarize(rows, dt):
    """Return disjoint dwell, subtype segments and own-input shadows only."""
    rows, dt = list(rows), [float(value) for value in dt]
    if len(rows) != len(dt) or any(not math.isfinite(t) or t < 0 for t in dt):
        raise ValueError('dt must match rows and contain finite nonnegative seconds')
    dwell, subtypes, transitions, segments = {}, {}, {}, []
    shadow_dwell = {'gate': 0., 'target_raised': 0., 'target_fully_masked': 0.,
                    'target_partly_masked': 0., 'pedals_equal_despite_target_raise': 0.}
    mask_dwell, gate_count, delta_sum, delta_max = {}, 0, 0., 0.
    previous = None
    for index, (row, duration) in enumerate(zip(rows, dt)):
        if duration == 0:
            continue
        item, shadow = _limits(row)
        label, subtype = item['label'], item['subtype']
        key = (label, subtype)
        dwell[label] = dwell.get(label, 0.) + duration
        if subtype is not None:
            subtypes[subtype] = subtypes.get(subtype, 0.) + duration
        start = float(row['truth_before']['time'])
        step = row.get('step', index+1)
        contiguous = previous is not None and abs(start-segments[-1]['end_time_s']) <= TOL
        if previous != key or not contiguous:
            if previous is not None and contiguous and previous != key:
                transition = segments[-1]['class'] + ('/' + segments[-1]['curvature_subtype']
                    if segments[-1]['curvature_subtype'] else '') + ' -> ' + label + ('/' + subtype if subtype else '')
                transitions[transition] = transitions.get(transition, 0) + 1
            segments.append({'class': label, 'curvature_subtype': subtype,
                             'start_step': step, 'end_step': step,
                             'start_time_s': start, 'end_time_s': start+duration,
                             'duration_s': duration, 'intervals': 1})
        else:
            segments[-1]['end_step'] = step
            segments[-1]['end_time_s'] = start+duration
            segments[-1]['duration_s'] += duration
            segments[-1]['intervals'] += 1
        previous = key
        if shadow is not None:
            gate_count += 1
            delta = shadow['delta']
            shadow_dwell['gate'] += duration
            shadow_dwell['target_raised' if delta > TOL else 'target_fully_masked'] += duration
            if delta > TOL and shadow['partly_masked']:
                shadow_dwell['target_partly_masked'] += duration
            if delta > TOL and shadow['pedals_equal']:
                shadow_dwell['pedals_equal_despite_target_raise'] += duration
            if shadow['mask_label']:
                mask_dwell[shadow['mask_label']] = mask_dwell.get(shadow['mask_label'], 0.) + duration
            delta_sum += duration*delta
            delta_max = max(delta_max, delta)
    elapsed = sum(dt)
    return {'interval_dwell_s': dwell,
            'interval_dwell_share': {k:v/elapsed for k,v in dwell.items()} if elapsed else {},
            'curvature_subtype_dwell_s': subtypes, 'elapsed_s': elapsed,
            'transition_counts': transitions, 'transition_count': sum(transitions.values()),
            'segments': segments, 'tie_tolerance_m_s': TOL,
            'own_input_7_vs_14': {'gate_intervals': gate_count, 'dwell_s': shadow_dwell,
                'mask_dwell_s': mask_dwell,
                'target_delta_mean_on_gate_m_s': delta_sum/shadow_dwell['gate'] if shadow_dwell['gate'] else None,
                'target_delta_max_m_s': delta_max},
            'trajectory_comparison_performed': False,
            'immediate_shadows_are_not_causal_lap_time_decomposition': True,
            'policy_environment_model_calls': 0}
