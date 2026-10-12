"""Bounded current-policy precontact and visible-geometry oracle diagnostics.

Only two permanently exposed DEV conditions are allowed by the private plan.
The simulator-side labels never reach the baseline actor. The oracle actor gets
only the existing-detection coordinate replacements, with unchanged pixels.
"""
from collections import deque
import hashlib
from pathlib import Path
import time

import numpy as np

from retry.visible_detected_geometry import context_for_existing_detections, pack
from retry.visible_obstacle_oracle_v2 import world_to_body


def fixture_gap(env, obstacle):
    """Signed current fixture/circle gap, including the actual polygon skin."""
    center=tuple(obstacle.position); radius=float(obstacle.fixtures[0].shape.radius)
    gaps=[]
    for body in [env.unwrapped.car.hull,*env.unwrapped.car.wheels]:
        q=np.asarray(body.GetLocalPoint(center),float)
        for fixture in body.fixtures:
            p=np.asarray(fixture.shape.vertices,float);edge=np.roll(p,-1,axis=0)-p;rel=q-p
            alpha=np.clip(np.sum(rel*edge,axis=1)/np.sum(edge*edge,axis=1),0,1)
            distance=float(np.linalg.norm(rel-alpha[:,None]*edge,axis=1).min())
            cross=edge[:,0]*rel[:,1]-edge[:,1]*rel[:,0]
            inside=np.all(cross>=-1e-12) or np.all(cross<=1e-12)
            gaps.append((-distance if inside else distance)-radius-float(fixture.shape.radius))
    return min(gaps)


def path_distance(path, point):
    p=np.asarray(path,float).reshape(-1,2);q=np.asarray(point,float)
    if len(p)<2:return None
    a=p[:-1];v=p[1:]-a;denom=np.sum(v*v,axis=1)
    t=np.clip(np.sum((q-a)*v,axis=1)/np.maximum(denom,1e-12),0,1)
    return float(np.linalg.norm(q-a-t[:,None]*v,axis=1).min())


def geometry_episode(plan_path,plan,case,initial_pairs,arm):
    from retry import diagnose,frozen_composite_runtime as runtime,frozen_paired_evaluation as paired
    from retry.compact_dev_diagnostic import compact_episode
    from retry.full_route_reproduction import truth
    prefix=arm=='P';state={};ring=deque(maxlen=20);first=None;before_last=[]
    counters=dict(rows=0,detections=0,matched=0,unmatched=0,effective_centers=0,effective_radii=0,
        max_radius_error_m=0.,label_raster_passes=0,component_extractions=0,visible_context_calls=0,
        context_wall_s=0.,max_center_error_m=0.,sum_center_error_m=0.,first_effective_step=None)
    original_factory,original_prepare,original_write=diagnose.make_env,runtime.prepare,paired.write

    def factory(*args,**kwargs):
        env=original_factory(*args,**kwargs);state['env']=env
        original_reset,original_step=env.reset,env.step
        def reset(*args,**kwargs):
            output=original_reset(*args,**kwargs);state['obs']=output[0];state['start_time']=env.unwrapped.t
            listener=env.unwrapped.world.contactListener_bug_workaround;contact=listener._contact
            def observe_contact(c,begin):
                if begin:
                    body=listener._match_obstacle_contact(c)
                    if body is not None:
                        state.setdefault('contact_ids',set()).update(i for i,b in enumerate(env.unwrapped.obstacles) if b==body)
                return contact(c,begin)
            listener._contact=observe_contact
            return output
        def step(action):
            nonlocal first,before_last
            response=state['response'];cp=response['contact_probe'];route=response['speed_constraint_probe']
            receipt=state['geometry_receipt'];before=truth(env);state['contact_ids']=set()
            raw=env.unwrapped;centers=world_to_body([tuple(o.position) for o in raw.obstacles],tuple(raw.car.hull.position),float(raw.car.hull.angle))
            path=route['selected_path_body'];gt=[]
            for i,o in enumerate(raw.obstacles):
                r=float(o.fixtures[0].shape.radius);distance=path_distance(path,centers[i])
                gt.append(dict(obstacle_id=i,center=centers[i].tolist(),radius=r,fixture_gap_pre_m=fixture_gap(env,o),
                    selected_path_point_gap_m=distance-r if distance is not None else None,
                    selected_path_nominal_margin_m=distance-r-2.6 if distance is not None else None))
            output=original_step(action);after=truth(env);obs,reward,ended,truncated,info=output
            for i,o in enumerate(raw.obstacles):gt[i]['fixture_gap_post_m']=fixture_gap(env,o)
            counters['rows']+=1
            row=dict(step=counters['rows'],elapsed_pre_s=before['time']-state['start_time'],elapsed_post_s=after['time']-state['start_time'],
                speed_m_s=before['speed_m_s'],target_m_s=cp['target_speed_m_s'],near=cp['near'],action=list(map(float,action)),
                damage_before=before['damage'],damage_after=after['damage'],collision=bool(info['collision']),
                contact_obstacle_ids=sorted(state['contact_ids']),unique_tiles_after=after['unique_tiles'],
                detections=cp['detected_obstacles_xyr'],applied_detections=cp.get('applied_detected_obstacles_xyr',cp['detected_obstacles_xyr']),
                tracker_hazards=cp['tracker_hazards_after'],selected_path=path,matches=receipt['matches'],GT=gt)
            before_last=list(ring)
            if first is None and info['collision']:
                first=dict(event=row,precontact=list(ring))
            ring.append(row);state['obs']=obs
            if prefix and info['collision'] and not (ended or truncated):
                state['administrative_prefix_stop']=True
                return obs,reward,ended,True,dict(info,retire_reason='diagnostic_first_contact_prefix_stop')
            return output
        env.reset,env.step=reset,step
        return env

    def prepare(*args,**kwargs):
        worker=original_prepare(*args,**kwargs);original_call=worker.call
        if not prefix:
            assert worker.ready['privileged_diagnostic'] and worker.ready['submission_candidate'] is False
        def call(operation,obs):
            if operation=='act':
                t=time.perf_counter();packet,receipt=context_for_existing_detections(state['env'],obs[-1])
                counters['context_wall_s']+=time.perf_counter()-t
            else:
                packet=dict(original=[],replacement=[]);receipt=None
            response,elapsed=original_call(operation,obs if prefix else pack(obs,packet))
            if operation=='act':
                actual=response['contact_probe']['detected_obstacles_xyr']
                assert np.array_equal(np.asarray(actual).reshape(-1,3),np.asarray(packet['original']).reshape(-1,3))
                if not prefix:
                    applied=response['contact_probe']['applied_detected_obstacles_xyr']
                    assert np.array_equal(np.asarray(applied).reshape(-1,3),np.asarray(packet['replacement']).reshape(-1,3))
                for key in ('detections','matched','unmatched','effective_centers','effective_radii','label_raster_passes','component_extractions','visible_context_calls'):
                    counters[key]+=receipt[key]
                counters['max_radius_error_m']=max(counters['max_radius_error_m'],receipt['max_radius_error_m'])
                for m in receipt['matches']:
                    counters['max_center_error_m']=max(counters['max_center_error_m'],m['center_error_m'])
                    counters['sum_center_error_m']+=m['center_error_m']
                if receipt['effective_centers'] and counters['first_effective_step'] is None:
                    counters['first_effective_step']=counters['rows']+1
                state.update(response=response,geometry_receipt=receipt)
            return response,elapsed
        worker.call=call
        return worker

    def write(path,value,**kwargs):
        if Path(path).name=='result.json':
            value.update(oracle_inputs_to_policy=not prefix,privileged_diagnostic=not prefix,submission_candidate=False,
                diagnostic_prefix_only=prefix,geometry_intervention='existing detected center/radius only' if not prefix else 'none; evaluator labels only')
            if state.get('administrative_prefix_stop'):
                value.update(terminal_observed=False,censored=True,evaluation_endpoint_observed=False,truncated=False,
                    retire_reason='diagnostic_first_contact_prefix_stop',administrative_prefix_stop=True)
        return original_write(path,value,**kwargs)

    diagnose.make_env,runtime.prepare,paired.write=factory,prepare,write
    try:
        local=dict(plan,max_steps=500 if prefix else 2000)
        result=compact_episode(plan_path,local,case,initial_pairs,[],arm=arm)
    finally:
        diagnose.make_env,runtime.prepare,paired.write=original_factory,original_prepare,original_write
    diagnostic=dict(kind='normal32_first_contact_prefix' if prefix else 'visible_detected_geometry_oracle_full_lap',
        counters=counters,first_contact=first,last_twenty=list(ring),before_last=before_last,
        GT_sent_to_policy=not prefix,first_contact_missing=first is None,
        first_contact_after_official_finish=bool(first and result.get('finish_time_s') is not None and first['event']['elapsed_pre_s']>=result['lap_ms']/1000),
        source_detector_alignment_checked_every_action=True,original_count_order_and_unmatched_preserved=True,
        extra_policy_calls=0,new_full_pixel_GT_policy_streams=0,
        boundary_limit='Fixture/circle gaps use actual current polygons and skin at wrapper endpoints,not continuous collision sweeps. Selected path gaps are point-polyline distances,not vehicle feasibility certificates.',
        no_new_or_hidden_detections_to_actor=True,no_promotion=True)
    original_write(plan_path.parent/'runs'/(case['id']+'__'+arm)/'geometry-diagnostic.json',diagnostic,exclusive=True)
    return result
