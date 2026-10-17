"""Saved442 trajectory algebra, using412 definitions; no act/step/model imports."""
import datetime
import hashlib
import json
import math
import sys
import time
from pathlib import Path
import numpy as np
from retry.decompose412_analyze import Reference, projection

TERMS = ['reference_clock_s', 'speed_tracking_s', 'heading_s', 'body_slip_s',
         'path_metric_s', 'quadrature_residual_s']


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    assert not path.exists(), path
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def target(ref, state, phase):
    q = projection(ref.line, state['pos'], state['vel'], phase)
    j, u = q['index'], q['u']
    r = math.sqrt((1-u)*ref.nodes[j]**2 + u*ref.nodes[j+1]**2)
    return q, r


def raw_points(rows, end, origin_velocity=False):
    points = []
    for row in rows:
        for k, h in enumerate(row['raw_hull']):
            if h['time'] > end + 1e-9:
                continue
            vel = h['origin_linear_velocity' if origin_velocity else 'COM_linear_velocity']
            points.append(dict(time=h['time'], pos=h['origin_position'], vel=vel,
                               speed=math.hypot(*vel), angle=h['angle'], step=row['step'],
                               phase=row['nominal_memory_after']['C']['phase'],
                               yaw=h['yaw'], command=row['command'], nominal=row['nominal'],
                               wrapper_pre=row['pre'],
                               tires=row['raw_tire_samples'][4*k:4*k+4]))
    assert abs(points[-1]['time'] - end) < 1e-9, 'Official event must be a saved raw boundary'
    return points


def intervals(points, ref):
    out = []
    arc = 0.
    frontier = 0.
    special = dict(stationary_s=0., reverse_s=0., revisit_s=0.,
                   nonpositive_proxy_s=0., outside_reference_support_s=0.)
    for first, last in zip(points, points[1:]):
        dt = last['time'] - first['time']
        assert abs(dt - .02) < 1e-8
        q0, _ = target(ref, first, first['phase'])
        q1, _ = target(ref, last, last['phase'])
        delta = (q1['arc'] - q0['arc'] + ref.L/2) % ref.L - ref.L/2
        assert abs(delta) < ref.L/2
        after = arc + delta
        reason = None
        if delta <= 0:
            reason = 'stationary_s' if delta == 0 else 'reverse_s'
        elif arc < 0 or after > ref.L:
            reason = 'outside_reference_support_s'
        elif arc < frontier:
            # Keep the entire mixed raw interval separate rather than infer a
            # fractional time of first passage from unobserved motion.
            reason = 'revisit_s'
        e0, e1 = ref.endpoint(first, q0), ref.endpoint(last, q1)
        V = (e0['v'] + e1['v'])/2
        H = (e0['h'] + e1['h'])/2
        Q = (e0['q'] + e1['q'])/2
        if reason is None and min(V, H, Q) <= 0:
            reason = 'nonpositive_proxy_s'
        item = dict(step=first['step'], s0=arc, s1=after, dt=dt,
                    t0=first['time']-points[0]['time'], t1=last['time']-points[0]['time'],
                    speed=V, reason=reason)
        if reason:
            special[reason] += dt
        else:
            D = delta
            chord = math.dist(first['pos'], last['pos'])
            clock = ref.clock(arc, after)
            values = [clock, D/V-clock, D/H-D/V, D/Q-D/H,
                      chord/V-D/Q, dt-chord/V]
            assert abs(sum(values)-dt) < 1e-9
            item.update(dict(zip(TERMS, values)), chord_m=chord,
                        heading_rad=(e0['heading'] or 0.)/2+(e1['heading'] or 0.)/2,
                        body_slip_rad=(e0['body_slip'] or 0.)/2+(e1['body_slip'] or 0.)/2,
                        abs_curvature=(e0['curvature']+e1['curvature'])/2)
        frontier = max(frontier, after)
        arc = after
        out.append(item)
    return out, special


def aggregate(items, ref, lo=None, hi=None):
    result = {k: 0. for k in TERMS}
    result.update(scored_time_s=0., special_time_s=0., total_time_s=0.)
    for item in items:
        fraction = 1.
        if lo is not None:
            if item['s1'] <= item['s0']:
                continue
            left, right = max(lo, item['s0']), min(hi, item['s1'])
            if right <= left:
                continue
            fraction = (right-left)/(item['s1']-item['s0'])
        dt = item['dt']*fraction
        result['total_time_s'] += dt
        if item['reason']:
            result['special_time_s'] += dt
            continue
        result['scored_time_s'] += dt
        if lo is None:
            for k in TERMS:
                result[k] += item[k]
        else:
            # Only the analytic reference clock is nonlinear within a bin.
            clock = ref.clock(left, right)
            result['reference_clock_s'] += clock
            result['speed_tracking_s'] += (item['reference_clock_s']+item['speed_tracking_s'])*fraction-clock
            for k in TERMS[2:]:
                result[k] += item[k]*fraction
    result['identity_error_s'] = sum(result[k] for k in TERMS)-result['scored_time_s']
    assert abs(result['identity_error_s']) < 1e-8
    return result


def diagnostics(rows, points, ref):
    result = dict(command_time_s={k:0. for k in ['brake','fullgas','partialgas','coast']},
                  speed_bin_time_s={k:0. for k in ['0_1','1_10','10_30','30_60','60_plus']},
                  brake_below_current_target_s=0., brake_below_current_target_actions=[],
                  command_override_actions=[], front_clip_wheel_fraction=0., rear_clip_wheel_fraction=0.,
                  clipped_raw_time_s=0., path_error_time_mean_m=0., path_error_max_m=0.,
                  steering_abs_time_mean=0., joint_lag_abs_time_mean_rad=0.,
                  force_ratio_max=0., curvature_abs_time_mean=0.,
                  current_trigger_candidates=[])
    tire_front = tire_rear = clip_front = clip_rear = 0
    duration = 0.
    lookup = {r['step']:r for r in rows}
    for first, last in zip(points, points[1:]):
        dt = last['time']-first['time']
        row = lookup[first['step']]
        command = row['command']
        group = 'brake' if command[2] > 0 else 'fullgas' if command[1] == 1 else 'partialgas' if command[1] > 0 else 'coast'
        result['command_time_s'][group] += dt
        v = (first['speed']+last['speed'])/2
        key = '0_1' if v < 1 else '1_10' if v < 10 else '10_30' if v < 30 else '30_60' if v < 60 else '60_plus'
        result['speed_bin_time_s'][key] += dt
        phase = row['nominal_memory_after']['C']['phase']
        q, r = target(ref, row['pre'], phase)
        if command[2] > 0 and row['pre']['speed'] < r:
            result['brake_below_current_target_s'] += dt
            result['brake_below_current_target_actions'].append(row['step'])
        if row['command'] != row['nominal']:
            result['command_override_actions'].append(row['step'])
        qp, _ = target(ref, first, first['phase'])
        result['path_error_max_m'] = max(result['path_error_max_m'], qp['path_error_m'])
        result['path_error_time_mean_m'] += dt*qp['path_error_m']
        result['steering_abs_time_mean'] += dt*abs(command[0])
        result['curvature_abs_time_mean'] += dt*abs(ref.curve[qp['index']])
        front = [z for z in first['tires'] if z['wheel'] < 2]
        rear = [z for z in first['tires'] if z['wheel'] >= 2]
        result['joint_lag_abs_time_mean_rad'] += dt*sum(abs(z['joint_angle']+command[0]) for z in front)/2
        tire_front += len(front)
        tire_rear += len(rear)
        clip_front += sum(z['clipped'] for z in front)
        clip_rear += sum(z['clipped'] for z in rear)
        result['clipped_raw_time_s'] += dt*any(z['clipped'] for z in front+rear)
        result['force_ratio_max'] = max(result['force_ratio_max'], *(z['force_ratio'] for z in front+rear))
        duration += dt
    for k in ['path_error_time_mean_m','steering_abs_time_mean','joint_lag_abs_time_mean_rad','curvature_abs_time_mean']:
        result[k] /= duration
    for k in ['brake_below_current_target_actions','command_override_actions']:
        result[k] = sorted(set(result[k]))
    result['front_clip_wheel_fraction'] = clip_front/tire_front
    result['rear_clip_wheel_fraction'] = clip_rear/tire_rear
    # Selection uses only each current state, fixed GT target and nominal command.
    # Future native commands/outcomes play no role in the predicate.
    for row in rows:
        phase = row['memory_before']['C']['phase']
        q, r = target(ref, row['pre'], phase)
        if (row['step'] <= 118 and phase == 'FIRST_LAP' and row['nominal'][2] > 0
                and 30 <= row['pre']['speed'] < r and q['sigma'] >= 0
                and (rows[row['step']-2]['damage'] if row['step'] > 1 else 0.) == 0 and all(x > 0 for x in row['pre']['road_contacts'])):
            result['current_trigger_candidates'].append(dict(step=row['step'],
                      pre_speed_m_s=row['pre']['speed'], current_target_m_s=r,
                      arc_fraction=q['arc']/ref.L))
    return result


def run(root):
    cpu, wall = time.process_time(), time.perf_counter()
    d = root/'stage443'
    assert not (d/'result.json').exists()
    plan = read(root/'stage442/plan.json')
    fixed_path = Path(plan['fixed_plan'])
    profiles_path = root/'stage404/profiles-private.json'
    fixed, profiles = read(fixed_path), read(profiles_path)
    ref = Reference(fixed, profiles['speed_nodes268'])
    assert np.array_equal(np.asarray(fixed['free_profile']['speed'])*profiles['frozen268'], ref.nodes)
    data, private = {}, {}
    allrows = {}
    sources = [Path(__file__), Path(__file__).with_name('decompose412_analyze.py'),
               Path(__file__).with_name('executor397.py'), fixed_path, profiles_path,
               root/'stage442/plan.json', root/'stage442/result.json',
               root/'project-effective-budget-v462.json']
    for name in ['C0','P']:
        path = root/f'stage442/actual_{name}/trace-private.jsonl'
        sources.append(path)
        rows = [json.loads(s) for s in path.read_text().splitlines()]
        allrows[name] = rows
        end = rows[-1]['finish_time_s']
        pp = raw_points(rows, end)
        aa, special = intervals(pp, ref)
        primary = aggregate(aa, ref)
        prefix = aggregate([x for x in aa if x['step'] <= 118], ref)
        suffix = aggregate([x for x in aa if x['step'] > 118], ref)
        assert abs(primary['total_time_s']-(end-rows[0]['pre']['time'])) < 1e-8
        assert abs(primary['scored_time_s']+sum(special.values())-primary['total_time_s']) < 1e-8
        assert abs(prefix['total_time_s']-9.44) < 1e-8
        origins, _ = intervals(raw_points(rows, end, True), ref)
        bins = [dict(arc_fraction=[j/10,(j+1)/10], **aggregate(aa, ref, ref.L*j/10, ref.L*(j+1)/10)) for j in range(10)]
        crossings = [dict(fraction=j/10, step=x['step'], time_bracket_s=[x['t0'],x['t1']])
                     for j in range(1,10) for x in aa if x['s0'] < ref.L*j/10 <= x['s1']]
        # Raw endpoint sampled at the official event, no future confirmation tick.
        assert len(aa) == round(primary['total_time_s']*50)
        data[name] = dict(official_lap_s=round(primary['total_time_s'], 8),
                          raw_intervals=len(aa), whole=primary, prefix=prefix, suffix=suffix,
                          special_time_ledger=special, spatial_bins=bins,
                          spatial_crossing_brackets=crossings,
                          origin_velocity_sensitivity=aggregate(origins, ref),
                          whole_diagnostics=diagnostics(rows, pp, ref),
                          prefix_diagnostics=diagnostics(rows[:118], [x for x in pp if x['time'] <= rows[118]['pre']['time']+1e-9], ref),
                          pre119_arc_fraction=aa[471]['s1']/ref.L)
        private[name] = aa
    assert allrows['C0'][:118] == allrows['P'][:118]
    assert data['C0']['prefix'] == data['P']['prefix']
    nominal = read(root/'stage411/gate_Cpre91_queried/forecast-91-private.json')
    old = [json.loads(s) for s in (root/'stage404/C_268/trace-private.jsonl').read_text().splitlines()]
    assert all(allrows['C0'][i][k] == old[i][k] for i in range(90) for k in ['pre','post','command'])
    assert allrows['C0'][90]['pre'] == old[90]['pre']
    assert [r['step'] for r in allrows['C0'] if r['command'] != r['nominal']] == [91]
    witness = dict(prefix_pre90_physical_and_commands_exact_historical_C=True,
                   pre91_physical_exact=True, actual_C0_only_nominal_override_step=91,
                   C0_after91_own_nominal_to_safe_official_finish=True,
                   historical_pre91_nominal13_valid=nominal['nominal']['valid'],
                   historical_pre91_nominal13_safety=nominal['nominal']['safety_flags'],
                   historical_pre91_neutral13_valid=nominal['pulse']['valid'],
                   historical_only_not_new_current_model_qualification=True,
                   latest_442_nominal_tail_from_each_early_root_unobserved=True)
    sources += [root/'stage411/gate_Cpre91_queried/forecast-91-private.json',
                root/'stage404/C_268/trace-private.jsonl',
                root/'stage410/result.json']
    source_hashes = {str(p):sha(p) for p in sources}
    result = dict(stage=443, status='COMPLETED_SAVED_ONLY', datasets=data,
                  reference_clock_s=ref.clock(0,ref.L), reference_not_physical_bound=True,
                  witness_audit=witness, new_actual_model_training=0,
                  research_remaining=27516, reserve=84000, reserve_used=0,
                  deadline_utc='2026-10-20T10:01:55Z',
                  source_hashes=source_hashes, CPU_s=time.process_time()-cpu,
                  wall_s=time.perf_counter()-wall)
    save(d/'result.json', result)
    save(d/'intervals-private.json', private)
    public = dict(result)
    public.pop('source_hashes')
    public = json.loads(json.dumps(public))
    for dataset in public['datasets'].values():
        for key in ['whole_diagnostics', 'prefix_diagnostics']:
            diag = dataset[key]
            candidates = diag.pop('current_trigger_candidates')
            diag['current_trigger_count'] = len(candidates)
            diag['first_current_trigger_step'] = candidates[0]['step'] if candidates else None
    save(Path(__file__).with_name('decompose443_result.json'), public)
    print(json.dumps(dict(stage=443, CPU_s=result['CPU_s'],
                         whole={k:v['whole'] for k,v in data.items()},
                         prefix=data['C0']['prefix'],
                         prefix_diagnostics=data['C0']['prefix_diagnostics'],
                         witness_audit=witness)))


if __name__ == '__main__':
    run(Path(sys.argv[1]))
