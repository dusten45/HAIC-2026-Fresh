"""Read saved pixel-policy records at compatible road positions, without replay.

Inputs and detailed outputs belong in a private directory supplied by the caller.
This module imports no policy, renderer, simulator or learned-model runtime.
Road projection, route clearances and association distances are diagnostic
proxies. Spatial alignment does not establish equal observations or states.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha_array(value):
    return hashlib.sha256(value.tobytes()).hexdigest()


def wrap(value):
    return np.arctan2(np.sin(value), np.cos(value))


def project(points, line, closed=False):
    """Return all segment projections; keep branch alternatives available."""
    line = np.asarray(line, dtype=float)
    a = line if closed else line[:-1]
    b = np.roll(line, -1, axis=0) if closed else line[1:]
    delta = b-a
    length = np.linalg.norm(delta, axis=1)
    valid = length > 1e-12
    assert valid.all()
    query = np.asarray(points, dtype=float).reshape(-1, 2)
    fraction = np.clip(np.einsum('qsd,sd->qs', query[:, None]-a, delta)/(length**2), 0, 1)
    feet = a+fraction[:, :, None]*delta
    distances = np.linalg.norm(query[:, None]-feet, axis=2)
    cumulative = np.r_[0., np.cumsum(length)]
    arcs = cumulative[:-1]+fraction*length
    return distances, arcs, feet, delta/length[:, None], cumulative


def persistent(values, threshold, count=10):
    flags = np.abs(np.asarray(values)) > threshold
    for end in range(count-1, len(flags)):
        if flags[end-count+1:end+1].all():
            return {'onset_step': end-count+2, 'confirmation_step': end+1}
    return None


def prefix_samples(path, extent=10., spacing=1.):
    path = np.asarray(path, float).reshape(-1, 2)
    if len(path) < 2:
        return None
    lengths = np.linalg.norm(np.diff(path, axis=0), axis=1)
    cumulative = np.r_[0., np.cumsum(lengths)]
    if cumulative[-1] <= 1e-12:
        return None
    arcs = np.r_[np.arange(0., min(extent, cumulative[-1]), spacing), min(extent, cumulative[-1])]
    points = np.column_stack([np.interp(arcs, cumulative, path[:, axis]) for axis in range(2)])
    return points


def rotation(angle):
    return np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]])


def segment_margin(path, obstacles, inflation=2.6):
    if len(path) < 2 or not obstacles:
        return None
    path = np.asarray(path, float)
    path = path[np.r_[True, np.linalg.norm(np.diff(path, axis=0), axis=1)>1e-12]]
    if len(path) < 2:
        return None
    objects = np.asarray(obstacles, float).reshape(-1, 3)
    distances, *_ = project(objects[:, :2], path)
    return float(np.min(distances-objects[:, 2, None]-inflation))


def inspect_run(spec, bin_m=5.):
    paths = spec['files']
    rows = [json.loads(s) for s in Path(paths['trace']).read_text().splitlines()]
    scene = json.loads(Path(paths['scene']).read_text())
    result = json.loads(Path(paths['result']).read_text())
    started = json.loads(Path(paths['started']).read_text())
    receipts = json.loads(Path(paths['receipts']).read_text())
    with np.load(paths['pixels_actions'], allow_pickle=False) as z:
        frames, actions = z['frames'].copy(), z['actions'].copy()
    with np.load(paths['masks'], allow_pickle=False) as z:
        masks = z['masks'].copy()
    assert len(rows) == len(actions) == result['charged_wrapper_actions']
    assert len(frames) == len(masks) == len(receipts) == len(rows)+1
    assert frames.dtype == masks.dtype == np.uint8 and actions.dtype == np.float32
    positions = [rows[0]['truth_before']['position']]+[r['truth_after']['position'] for r in rows]
    line = np.asarray(scene['track'], float)[:, 2:4]
    distances, arcs, feet, tangent, cumulative = project(positions, line, closed=True)
    total_arc = float(cumulative[-1])
    chosen = np.argmin(distances, axis=1)
    arc = arcs[np.arange(len(positions)), chosen]
    unwrapped = np.zeros_like(arc)
    ambiguous = np.zeros(len(arc), bool)
    for i in range(len(arc)):
        unwrapped[i] = (arc[i] if arc[i] < total_arc/2 else arc[i]-total_arc) if i == 0 else arc[i]+round((unwrapped[i-1]-arc[i])/total_arc)*total_arc
        apart = np.abs(arcs[i]-arc[i]); apart = np.minimum(apart, total_arc-apart)
        ambiguous[i] = bool(np.any((apart > 20.) & (distances[i]-distances[i, chosen[i]] <= .5)))
    contact_step = next((r['step'] for r in rows if r['info']['collision']), None)
    records = []
    seen_bins = set()
    last_bin = None
    maximum_arc = unwrapped[0]
    for i, row in enumerate(rows):
        before, after = row['truth_before'], row['truth_after']
        response = row['policy_response']; telemetry = response['route_telemetry']
        curve = response.get('curve_diagnostic') or {}
        cap = response.get('cap_diagnostic') or {}
        obs = frames[np.maximum(0, np.arange(i-3, i+1))].astype(np.float32)/255
        obs_after = frames[np.maximum(0, np.arange(i-2, i+2))].astype(np.float32)/255
        assert sha_array(obs) == row['observation_sha256_before']
        assert sha_array(obs_after) == row['observation_sha256_after']
        assert np.asarray(row['action'], np.float32).tobytes() == actions[i].tobytes()
        assert sha_array(masks[i+1]) == response['student_receipt']['student_mask_sha256']
        assert receipts[i+1]['observation_sha256'] == row['observation_sha256_before']
        if i:
            assert rows[i-1]['truth_after'] == before
        target = telemetry.get('controller_target')
        selected = telemetry.get('selected_path') or []
        path_samples = prefix_samples(selected)
        path_offset = physical_margin = observed_margin = near_bearing = None
        if path_samples is not None:
            world_path = path_samples@rotation(before['angle']).T+np.asarray(before['position'])
            path_offset = float(np.max(np.min(project(world_path, line, closed=True)[0], axis=1)))
            body_obstacles = [(np.asarray(o['position'])-before['position'])@rotation(before['angle'])
                              for o in scene['obstacles']]
            physical_margin = segment_margin(selected, [[*v, o['radius']] for v, o in zip(body_obstacles, scene['obstacles'])])
            observed_margin = segment_margin(selected, [o[:3] for o in telemetry['route_obstacle_inputs']])
            first = next((np.asarray(v) for v in selected[1:] if np.linalg.norm(v) > 1e-12), None)
            if first is not None:
                near_bearing = float(math.atan2(first[0], first[1]))
        index = chosen[i]; direction = tangent[index]
        relative = np.asarray(before['position'])-feet[i, index]
        lateral = float(relative@np.array([direction[1], -direction[0]]))
        heading = float(wrap(before['angle']-math.atan2(-direction[0], direction[1])))
        move = float(np.linalg.norm(np.asarray(after['position'])-before['position']))
        delta_arc = float(unwrapped[i+1]-unwrapped[i])
        bin_id = int(math.floor(unwrapped[i]/bin_m))
        revisited = bin_id != last_bin and bin_id in seen_bins
        if bin_id != last_bin:
            seen_bins.add(bin_id)
        first_pass = not revisited and unwrapped[i] >= maximum_arc-.25
        maximum_arc = max(maximum_arc, unwrapped[i+1]); last_bin = bin_id
        reasons = []
        if ambiguous[i] or ambiguous[i+1]: reasons.append('branch_ambiguous')
        if abs(delta_arc) > move*2+2: reasons.append('projection_jump')
        if delta_arc < -.25: reasons.append('reverse')
        if not first_pass: reasons.append('repeated_or_recovery')
        if contact_step is not None and i+1 >= contact_step: reasons.append('contact_or_postcontact')
        r = {'step':i+1, 'pre_time_s':before['time'], 'post_time_s':after['time'],
             'arc_m':float(unwrapped[i]), 'post_arc_m':float(unwrapped[i+1]),
             'road_segment':int(index), 'spatial_bin':bin_id, 'alignment_exclusions':reasons,
             'position':before['position'], 'road_lateral_m':lateral, 'road_heading_rad':heading,
             'unique_before':before['unique_tiles'], 'unique_after':after['unique_tiles'],
             'counter_before':before['off_track_counter'], 'counter_after':after['off_track_counter'],
             'damage_before':before['damage'], 'damage_after':after['damage'],
             'contact':row['info']['collision'], 'actual_speed_m_s':before['speed_m_s'],
             'HUD_speed_m_s':telemetry['speed_estimate'], 'yaw_rate_rad_s':before['angular_velocity'],
             'steer':row['action'][0], 'gas':row['action'][1], 'brake':row['action'][2],
             'front_joint_mean_rad':float(np.mean([w['joint_angle'] for w in before['wheels'][:2]])),
             'target':target, 'target_bearing_rad':None if target is None else float(math.atan2(target[0],target[1])),
             'curvature_inv_m':curve.get('curvature'), 'curve_gate':curve.get('gate'), 'near':curve.get('near'),
             'target_speed_m_s':curve.get('applied_final_target',cap.get('effective_target')),
             'distance_cap_m_s':cap.get('distance_cap'), 'cap_active':cap.get('cap_active'),
             'detections':telemetry['current_detections'], 'hazards':telemetry['memory_hazards_after_tracker'],
             'path':selected, 'centerline':telemetry['centerline'],
             'mask_sha256':response['student_receipt']['student_mask_sha256'],
             'path_near_road_max_offset_m':path_offset,
             'path_physical_obstacle_margin_proxy_m':physical_margin,
             'path_observed_obstacle_margin_proxy_m':observed_margin,
             'near_connector_bearing_rad':near_bearing,
             'fallback':telemetry['actual_fallback_called'],
             'observation_sha256':row['observation_sha256_before']}
        records.append(r)
    bins = {}
    for b in range(max(0,int(math.floor(unwrapped[0]/bin_m))), int(math.floor(np.max(unwrapped)/bin_m))):
        lower, upper = b*bin_m, (b+1)*bin_m
        crossings_low = [i for i,r in enumerate(records) if r['arc_m'] <= lower < r['post_arc_m']]
        crossings_high = [i for i,r in enumerate(records) if r['arc_m'] < upper <= r['post_arc_m']]
        if not crossings_low or not crossings_high: continue
        start = crossings_low[0]; end = next((i for i in crossings_high if i>=start),None)
        if end is None: continue
        internal = records[start:end+1]
        excluded = sorted({reason for r in internal for reason in r['alignment_exclusions']})
        bins[str(b)] = {'lower_arc_m':lower,'upper_arc_m':upper,'start_step':start+1,'end_step':end+1,
                        'elapsed_s':internal[-1]['post_time_s']-internal[0]['pre_time_s'],
                        'row_count':len(internal),'reliable':not excluded,'exclusions':excluded,
                        'unique_start':internal[0]['unique_before'],'unique_end':internal[-1]['unique_after'],
                        'metrics':{key:float(np.median([r[key] for r in internal if r[key] is not None]))
                                   for key in ('actual_speed_m_s','HUD_speed_m_s','curvature_inv_m','target_speed_m_s',
                                               'road_lateral_m','road_heading_rad','steer','gas','brake','near_connector_bearing_rad',
                                               'path_near_road_max_offset_m')
                                   if any(r[key] is not None for r in internal)}}
    markers = {'first_contact':contact_step,
               'first_damage':next((r['step'] for r in records if r['damage_after']>0),None),
               'persistent_road_heading':persistent([r['road_heading_rad'] for r in records],.2),
               'persistent_road_lateral':persistent([r['road_lateral_m'] for r in records],.5),
               'terminal_counter_run_start':next((r['step'] for r in reversed(records)
                                                if r['counter_before']==0),None) if records[-1]['counter_after']>100 else None}
    summary = {'status':result['status'],'steps':len(records),'completed':result['completed'],
               'unique_tiles':result['unique_tiles'],'total_tiles':result['total_tiles'],
               'official_lap_ms':result.get('official_lap_ms'),'damage':result['damage'],
               'failure_type':result.get('failure_type'),'markers':markers,
               'alignment_exclusion_rows':dict(Counter(reason for r in records for reason in r['alignment_exclusions'])),
               'reliable_complete_bins':sum(v['reliable'] for v in bins.values()),
               'initial_observation_sha256':started['initial_observation_sha256'],
               'road_geometry_sha256':scene['geometry_sha256'],
               'physical_obstacles_sha256':scene['physical_obstacle_sha256']}
    return {'summary':summary,'records':records,'bins':bins,'raw_rows':rows,'scene':scene}


def compare_runs(a, b):
    common = sorted(set(a['bins']) & set(b['bins']), key=int)
    pairs = []
    for key in common:
        left, right = a['bins'][key], b['bins'][key]
        pairs.append({'bin':int(key),'lower_arc_m':left['lower_arc_m'],'upper_arc_m':left['upper_arc_m'],
                      'reliable':left['reliable'] and right['reliable'],
                      'exclusions':sorted(set(left['exclusions']+right['exclusions'])),
                      'a':left,'b':right})
    first = None
    for i,(left,right) in enumerate(zip(a['raw_rows'],b['raw_rows'])):
        if np.asarray(left['action'],np.float32).tobytes()!=np.asarray(right['action'],np.float32).tobytes():
            first={'step':i+1,'same_observation':left['observation_sha256_before']==right['observation_sha256_before'],
                   'same_stored_truth':left['truth_before']==right['truth_before'],
                   'a_action':left['action'],'b_action':right['action']};break
    return {'common_complete_bins':len(pairs),'reliable_common_bins':sum(p['reliable'] for p in pairs),
            'first_action_difference':first,'paired_bins':pairs}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    assert np.__version__=='1.26.0'
    wall,cpu=time.perf_counter(),time.process_time()
    manifest=json.loads(args.manifest.read_text())
    for path,expected in manifest['source_sha256'].items():
        assert sha_file(path)==expected,path
    runs={name:inspect_run(spec,manifest.get('bin_m',5.)) for name,spec in manifest['runs'].items()}
    first=next(iter(runs.values()))
    for run in runs.values():
        assert np.array_equal(run['scene']['track'],first['scene']['track'])
        assert run['scene']['obstacles']==first['scene']['obstacles']
        assert run['summary']['initial_observation_sha256']==first['summary']['initial_observation_sha256']
    pairs={name:compare_runs(runs[values[0]],runs[values[1]]) for name,values in manifest['comparisons'].items()}
    for run in runs.values():run.pop('raw_rows');run.pop('scene')
    output={'runs':runs,'comparisons':pairs,'new_environment_policy_model_renderer_calls':0,
            'analysis_wall_s':time.perf_counter()-wall,'analysis_CPU_s':time.process_time()-cpu,
            'source_sha256':manifest['source_sha256'],
            'limits':['Spatial agreement is not identical-state counterfactual matching.',
                      'Route origin is synthetic: zero current path distance does not certify following.',
                      'Road widths and radial margins are geometry proxies, not full-body contacts.',
                      'Masks and detections differ after the first physical divergence.']}
    assert not args.output.exists()
    args.output.write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    args.output.chmod(0o600)
    print(json.dumps({'summary':{name:r['summary'] for name,r in runs.items()},
                      'comparisons':{k:{f:v[f] for f in ['common_complete_bins','reliable_common_bins','first_action_difference']} for k,v in pairs.items()},
                      'wall_s':output['analysis_wall_s'],'CPU_s':output['analysis_CPU_s']}))


if __name__=='__main__':
    main()
