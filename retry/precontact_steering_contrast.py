"""Saved full-footprint geometry and a bounded, charged steering contrast.

The frozen center/ego diagnostic worker is unchanged. The evaluator applies one
declared pulse to its returned steering action. Each arm resets and really
replays its prefix; no Box2D state is copied. This is not a submission policy.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

from retry.precontact_feasibility import HULL, WHEEL, ANCHORS, RADIUS, SKIN, route_curve
from retry.visible_geometry_diagnostic import path_distance, fixture_gap


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def steering_pulse(action, step, start, length, delta):
    result = np.asarray(action, dtype=np.float32).copy()
    if start <= step < start + length:
        result[0] = np.clip(float(result[0]) + delta, -.4, .4)
    return result.tolist()


def saved_geometry(geometry, ego, anchor_step):
    """Compare every saved precontact segment and the driven hull in one frame.

    The circle bound contains all official hull polygons and every wheel at any
    steering angle, at the nominal joint anchors. It proves obstacle clearance
    along a commanded polyline, not curvature, dynamics or road feasibility.
    Saved actual gaps already include live wheel poses and all eight fixtures.
    """
    rows = geometry['first_contact']['precontact']
    ego_rows = {r['step']: r for r in ego['first_contact']['precontact']}
    risk, = geometry['first_contact']['event']['contact_obstacle_ids']
    assert len(rows) == 20 and all(not r['collision'] for r in rows)
    wheel_bound = float(np.linalg.norm(ANCHORS, axis=1).max() + np.linalg.norm(WHEEL, axis=1).max())
    assert wheel_bound < RADIUS
    transforms = {}; matrix = np.eye(3)
    first_obstacles = {g['obstacle_id']: np.asarray(g['center']) for g in rows[0]['GT']}
    aligned = []; residual = 0.
    for i, row in enumerate(rows):
        step = row['step']
        if i:
            previous_to_current = np.eye(3)
            previous_to_current[:2] = ego_rows[step]['probe']['transform']
            matrix = matrix @ np.linalg.inv(previous_to_current)
        transforms[step] = matrix.copy()
        path = np.asarray(row['selected_path'])
        target = next(g for g in row['GT'] if g['obstacle_id'] == risk)
        bounds = []
        for g in row['GT']:
            center = matrix[:2, :2] @ g['center'] + matrix[:2, 2]
            residual = max(residual, float(np.linalg.norm(center - first_obstacles[g['obstacle_id']])))
            bounds.append(path_distance(path, g['center']) - g['radius'] - RADIUS - SKIN)
        tangent = route_curve(path, np.asarray(target['center']), target['radius'])
        aligned.append(dict(step=step,position=matrix[:2,2].tolist(),angle=float(np.arctan2(matrix[1,0],matrix[0,0])),
            selected_path=(path @ matrix[:2,:2].T + matrix[:2,2]).tolist(),
            hull_polygons=[(p @ matrix[:2,:2].T + matrix[:2,2]).tolist() for p in HULL],
            all_obstacles_heading_independent_bound_m=min(bounds),
            tangent_risk_gap_m=tangent['tangent_footprint']['min_clearance_m'],
            actual_all_fixture_risk_gap_pre_m=target['fixture_gap_pre_m'],
            actual_all_fixture_risk_gap_post_m=target['fixture_gap_post_m']))
    assert residual < 1e-9
    anchor = next(r for r in rows if r['step'] == anchor_step)
    anchor_record = next(r for r in aligned if r['step'] == anchor_step)
    assert anchor_record['all_obstacles_heading_independent_bound_m'] > 0
    anchor_path = np.asarray(anchor['selected_path'])
    target = next(g for g in anchor['GT'] if g['obstacle_id'] == risk)
    inverse = np.linalg.inv(transforms[anchor_step]); departure = []
    for row in rows:
        if row['step'] < anchor_step:
            continue
        pose = inverse @ transforms[row['step']]
        departure.append(dict(step=row['step'],position=pose[:2,2].tolist(),
            angle=float(np.arctan2(pose[1,0],pose[0,0])),
            origin_distance_from_fixed_anchor_polyline_m=path_distance(anchor_path,pose[:2,2])))
    # The controller consumes nominal body-space coordinates. Independently
    # record the physical pixel-center interpretation; never silently shift it.
    pixel_shift = np.array([(42-41.542)/1.3608,(62.4475-63)/1.701])
    decoded = anchor_path.copy(); decoded[1:] += pixel_shift
    return dict(status='PASS_COMMANDED_POLYLINE_CLEARANCE_AND_DRIVEN_DEPARTURE',
        window_steps=[rows[0]['step'],rows[-1]['step']],anchor_step=anchor_step,risk_obstacle_id=risk,
        first_contact_step=geometry['first_contact']['event']['step'],
        frame='Saved first input hull origin; x right,y forward; world=position+R(hull.angle)*body.',
        source_hull_radius_m=float(RADIUS),source_polygon_skin_m=SKIN,
        analytic_any_steer_wheel_radius_bound_m=wheel_bound,
        conservative_vehicle_radius_with_skin_m=float(RADIUS+SKIN),
        anchor_min_all_segment_all_obstacle_bound_m=anchor_record['all_obstacles_heading_independent_bound_m'],
        obstacle_alignment_residual_m=residual,rows=aligned,anchor_departure=departure,
        obstacles=[dict(obstacle_id=g['obstacle_id'],center=g['center'],radius=g['radius']) for g in rows[0]['GT']],
        coordinate_conventions=dict(command_origin=[0.,0.],grid_inverse_origin=[42.,63.],
            physical_pixel_center_origin=[41.542,62.4475],grid_point_shift_m=pixel_shift.tolist(),
            decoded_pixel_path_risk_bound_m=path_distance(decoded,target['center'])-target['radius']-RADIUS-SKIN,
            note='Negative alternate bound is inconclusive. Positive certificate is for the body-space path actually consumed by the controller, not the decoded road pixels.'),
        limits='Tangent placement alone is not safety proof. Positive disk bound covers every continuous segment, connector and all body headings, but does not prove dynamic/road feasibility. Actual live gaps include independent wheel poses. Replanning and following remain coupled.',
        new_native_actions=0,new_policy_calls=0)


def contrast_episode(plan_path, plan, case, arm, prefix_reference=None):
    from retry import diagnose, frozen_composite_runtime as runtime
    from retry.frozen_paired_evaluation import write
    from retry.full_route_reproduction import truth
    from retry.true_ego_geometry import ego_episode

    spec = plan['contrast']; start, length, horizon = spec['start_step'], spec['pulse_actions'], spec['end_step']
    delta = spec['deltas'][arm]; risk = spec['risk_obstacle_id']
    original_factory, original_prepare = diagnose.make_env, runtime.prepare
    state = dict(calls=0,steps=0); rows = []; prefix = {}
    observations, actions = hashlib.sha256(), hashlib.sha256()

    def factory(*args, **kwargs):
        env = original_factory(*args, **kwargs)
        old_reset, old_step = env.reset, env.step
        def reset(*args, **kwargs):
            output = old_reset(*args, **kwargs); observations.update(output[0].tobytes())
            raw = env.unwrapped; state['env'] = env
            bodies = [raw.car.hull,*raw.car.wheels]
            state['fixture_shapes'] = [dict(body=i,vertices=[list(p) for p in f.shape.vertices],skin=float(f.shape.radius))
                for i,b in enumerate(bodies) for f in b.fixtures]
            assert len(state['fixture_shapes']) == 8
            state['obstacles'] = [dict(obstacle_id=i,center=list(o.position),radius=float(o.fixtures[0].shape.radius))
                for i,o in enumerate(raw.obstacles)]
            old_raw_step = env.env.step
            def raw_step(action):
                result = old_raw_step(action)
                if state['steps']+1 >= spec['record_from_step']:
                    state['raw_gaps'].append(fixture_gap(env,raw.obstacles[risk]))
                return result
            env.env.step = raw_step
            return output
        def step(action):
            step_index = state['steps']+1
            assert step_index == state['calls'] <= horizon
            before = truth(env); response = state['response']; state['raw_gaps'] = []
            if step_index >= spec['record_from_step']:
                gap_before = fixture_gap(env,env.unwrapped.obstacles[risk])
            output = old_step(action); after = truth(env); state['steps'] = step_index
            if step_index < start:
                observations.update(output[0].tobytes()); actions.update(np.asarray(action,np.float32).tobytes())
            if step_index == start-1:
                prefix.update(actions=step_index,observation_sequence_sha256=observations.hexdigest(),
                    action_sequence_sha256=actions.hexdigest(),boundary_state_sha256=digest(after))
                if prefix_reference is not None:
                    assert all(prefix[k] == prefix_reference[k] for k in prefix), 'Replayed prefix differs'
            if step_index >= spec['record_from_step']:
                rows.append(dict(step=step_index,truth_before=before,truth_after=after,
                    original_action=response['contrast_probe']['original_action'],applied_action=list(map(float,action)),
                    pulse_active=response['contrast_probe']['pulse_active'],
                    selected_path=response['speed_constraint_probe']['selected_path_body'],
                    actual_risk_gap_before_m=gap_before,raw_endpoint_risk_gaps_m=list(state['raw_gaps']),
                    collision=bool(output[4]['collision']),retire_reason=output[4]['retire_reason']))
            obs,reward,ended,truncated,info = output
            if step_index == horizon and not (ended or truncated):
                state['administrative_stop'] = True
                return obs,reward,ended,True,dict(info,retire_reason='fixed_local_suffix_endpoint')
            return output
        env.reset, env.step = reset, step
        return env

    def prepare(*args, **kwargs):
        worker = original_prepare(*args, **kwargs); old_call = worker.call
        def call(operation, obs):
            response, elapsed = old_call(operation, obs)
            if operation == 'act':
                state['calls'] += 1; step = state['calls']
                if step == start:
                    # Original action plus all bounded policy state used by the
                    # route/steering hooks must agree before the intervention.
                    boundary = digest({k:response[k] for k in ('action','contact_probe','speed_constraint_probe','ego_motion_probe','connection_selection')})
                    prefix['boundary_policy_probe_sha256'] = boundary
                    if prefix_reference is not None:
                        assert boundary == prefix_reference['boundary_policy_probe_sha256'], 'Boundary policy differs'
                original = list(response['action'])
                response['action'] = steering_pulse(original,step,start,length,delta)
                assert response['action'][1:] == original[1:]
                response['contrast_probe'] = dict(original_action=original,delta=delta,
                    pulse_active=bool(delta and start <= step < start+length))
                state['response'] = response
            return response, elapsed
        worker.call = call
        return worker

    diagnose.make_env, runtime.prepare = factory, prepare
    try:
        result = ego_episode(plan_path,plan,case,dict(plan['cached_initial_pairs']),arm)
    finally:
        diagnose.make_env, runtime.prepare = original_factory, original_prepare
    if state.get('administrative_stop'):
        result.update(terminal_observed=False,censored=True,evaluation_endpoint_observed=False,
            truncated=False,retire_reason='fixed_local_suffix_endpoint',administrative_suffix_stop=True)
    result.update(local_counterfactual_only=True,full_lap_performance_claim=False,
        original_worker_unchanged=True,steering_pulse_delta=delta)
    directory = plan_path.parent/'runs'/(case['id']+'__'+arm)
    write(directory/'result.json',result)
    write(directory/'contrast-diagnostic.json',dict(prefix=prefix,rows=rows,
        fixture_shapes=state.get('fixture_shapes'),obstacles=state.get('obstacles'),
        prefix_replayed_and_charged=True,box2d_state_clones=0,extra_policy_calls=0,
        raw_gap_limit='Actual full fixture gaps sampled after each real 20ms physics tick; contact callbacks, not endpoint gap signs, decide collision.'),exclusive=True)
    return result, prefix
