"""Privileged ego-motion of retained tracks, with the frozen183 center adapter.

Only a previous-to-current vehicle-frame rigid transform is supplied. No target
identity, target truth, hidden object or future pose enters the motion hook.
The original tracker chooses the ordered surviving/associated cohort first;
only its retained coordinates change, keeping count, age and radii exact.
"""
import ast
from collections import deque
import hashlib
import json
from pathlib import Path
import textwrap
import zipfile

import numpy as np

SOURCE_WORKER_SHA256 = '9e42cf3c0d89ce40d7f8aef2e4a7a495fb2dcdd42f4db1979b7da1d72e54bf5c'
ARCHIVE_SHA256 = '9f9bd5abdd82250c0f84f7dd626ae900c2a7417191fb5354a0f21632bd8c284b'


def pose_transform(previous,current):
    """Map previous body coordinates to current body coordinates, column form."""
    angle=previous['angle']-current['angle'];c,s=np.cos(angle),np.sin(angle)
    rotation=np.array([[c,-s],[s,c]])
    c,s=np.cos(current['angle']),np.sin(current['angle'])
    translation=np.array([[c,s],[-s,c]]) @ (np.asarray(previous['position'])-current['position'])
    return np.c_[rotation,translation]


def tracker_source(archive):
    assert hashlib.sha256(Path(archive).read_bytes()).hexdigest()==ARCHIVE_SHA256
    with zipfile.ZipFile(archive) as z:source=z.read('retry/temporal_agent.py').decode()
    tree=ast.parse(source);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
    fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='tracked_obstacles')
    source=textwrap.dedent('\n'.join(source.splitlines()[fn.lineno-1:fn.end_lineno]))
    def replace(old,new):
        nonlocal source
        assert source.count(old)==1,old
        source=source.replace(old,new)
    replace('def tracked_obstacles(', 'def tracked_obstacles_ego(')
    replace('    predicted = []\n', '    predicted = []\n    retained_sources = {}\n')
    replace('    for x, y, radius, age in self.hazards:\n',
        '    for source_index, (x, y, radius, age) in enumerate(self.hazards):\n        source_xy = (x, y)\n')
    replace('            predicted.append((float(x), float(y), radius, age + 1))',
        '            predicted.append((float(x), float(y), radius, age + 1))\n            retained_sources[id(predicted[-1])] = (source_index, source_xy)')
    replace('    self.previous_image, self.hazards = current, predicted', '''    # Original ROI/age/association decisions are already complete here.
    matrix = np.asarray(ego_matrix(), np.float64).reshape(2,3)
    original_cohort = list(predicted)
    corrected = []
    audit_rows = []
    for slot, item in enumerate(original_cohort):
        if item[3] == 0:
            corrected.append(item)
            continue
        source_index, previous_xy = retained_sources[id(item)]
        xy = matrix @ np.array([*previous_xy,1.0])
        corrected.append((float(xy[0]),float(xy[1]),item[2],item[3]))
        audit_rows.append(dict(slot=slot,source_index=source_index,previous_xy=list(previous_xy),
            original_propagated_xy=list(item[:2]),corrected_xy=xy.tolist(),radius=item[2],age=item[3]))
    assert len(original_cohort)==len(corrected)
    assert all(a[2:]==b[2:] for a,b in zip(original_cohort,corrected))
    assert all(a==b for a,b in zip(original_cohort,corrected) if a[3]==0)
    self.ego_diagnostic = dict(transform=matrix.tolist(),retained=audit_rows,
        source_hazard_count=len(self.hazards),output_count=len(corrected),
        fresh_count=sum(v[3]==0 for v in corrected),
        count_order_age_radius_and_association_preserved=True,fresh_values_unchanged=True)
    self.previous_image, self.hazards = current, corrected''')
    replace('    return [p[:3] for p in predicted]', '    return [p[:3] for p in corrected]')
    compile(source,'tracker_ego_hook','exec')
    return source


def build_worker(source_path,archive,destination):
    source_path=Path(source_path);text=source_path.read_text()
    assert hashlib.sha256(source_path.read_bytes()).hexdigest()==SOURCE_WORKER_SHA256
    tracker=tracker_source(archive)
    def replace(old,new):
        nonlocal text
        assert text.count(old)==1,old
        text=text.replace(old,new)
    replace('import struct\n','import struct\nimport types\n')
    replace('original_tracker = agent.tracked_obstacles',
        'exec(compile('+repr(tracker)+", 'retained_ego_hook', 'exec'), temporal.__dict__)\n"
        "temporal.ego_matrix = lambda: geometry_context['ego_transform']\n"
        'original_tracker = types.MethodType(temporal.tracked_obstacles_ego, agent)')
    replace("assert set(geometry_context) == {'kind','original','replacement'}",
        "assert set(geometry_context) == {'kind','original','replacement','ego_transform'}\n"
        "    matrix = np.asarray(geometry_context['ego_transform'],np.float64)\n"
        "    assert matrix.shape == (2,3) and np.isfinite(matrix).all()\n"
        "    assert np.allclose(matrix[:,:2].T @ matrix[:,:2],np.eye(2),rtol=0,atol=1e-12)\n"
        "    assert abs(np.linalg.det(matrix[:,:2])-1)<1e-12")
    replace("'privileged_diagnostic':True,'submission_candidate':False,",
        "'privileged_diagnostic':True,'submission_candidate':False,\n"
        "                  'ego_boundary':'previous-to-current vehicle rigid transform only; frozen ordered cohort,age,radius and fresh detections',")
    replace("'observer_extra_policy_calls':0,\n                    'memory':",
        "'observer_extra_policy_calls':0,\n                    'ego_motion_probe':dict(agent.ego_diagnostic),\n                    'memory':")
    compile(text,str(destination),'exec');destination=Path(destination)
    with destination.open('x') as f:f.write(text)
    destination.chmod(0o600)
    return hashlib.sha256(destination.read_bytes()).hexdigest()


def ego_episode(plan_path,plan,case,initial_pairs,arm='O'):
    from retry import diagnose,frozen_composite_runtime as runtime,visible_geometry_diagnostic as geometry
    from retry.frozen_paired_evaluation import write
    original_factory,original_prepare=diagnose.make_env,runtime.prepare
    original_context,original_pack=geometry.context_for_existing_detections,geometry.pack
    state={};ring=deque(maxlen=20);first=None
    counts=dict(rows=0,retained_rows=0,changed_retained_coordinates=0,first_changed_step=None,
        changed_rows_before_first_contact=0,zero_detection_rows_with_changed_coordinates_before_first_contact=0,
        maximum_transport_error_m=0.,all_counts_ages_radii_order_associations_preserved=True)
    def pose(env):
        hull=env.unwrapped.car.hull
        return dict(position=list(hull.position),angle=float(hull.angle))
    def factory(*args,**kwargs):
        env=original_factory(*args,**kwargs);state['env']=env
        old_reset,old_step=env.reset,env.step
        def reset(*args,**kwargs):
            output=old_reset(*args,**kwargs);state['previous_pose']=pose(env)
            return output
        def step(action):
            nonlocal first
            probe=state['probe'];step_index=counts['rows']+1
            row=dict(step=step_index,probe=probe,actual_current_detection_count=state['detection_count'])
            changed=0
            matrix=np.asarray(probe['transform'])
            for r in probe['retained']:
                expected=matrix @ np.array([*r['previous_xy'],1.])
                error=float(np.linalg.norm(expected-r['corrected_xy']))
                counts['maximum_transport_error_m']=max(counts['maximum_transport_error_m'],error)
                assert error<1e-12
                changed+=np.linalg.norm(np.asarray(r['corrected_xy'])-r['original_propagated_xy'])>1e-9
            assert probe['count_order_age_radius_and_association_preserved'] and probe['fresh_values_unchanged']
            counts['rows']+=1;counts['retained_rows']+=len(probe['retained']);counts['changed_retained_coordinates']+=int(changed)
            if changed and counts['first_changed_step'] is None:counts['first_changed_step']=step_index
            if first is None and changed:
                counts['changed_rows_before_first_contact']+=1
                counts['zero_detection_rows_with_changed_coordinates_before_first_contact']+=int(state['detection_count']==0)
            output=old_step(action);row['collision']=bool(output[4]['collision'])
            if first is None and row['collision']:first=dict(event=row,precontact=list(ring))
            ring.append(row)
            return output
        env.reset,env.step=reset,step
        return env
    def context(env,image):
        packet,receipt=original_context(env,image)
        current=pose(env);matrix=pose_transform(state['previous_pose'],current)
        state['previous_pose']=current;state['detection_count']=len(packet['original'])
        return dict(packet,ego_transform=matrix.tolist()),receipt
    def pack(obs,packet):
        return original_pack(obs,dict(packet,ego_transform=packet.get('ego_transform',[[1.,0.,0.],[0.,1.,0.]])))
    def prepare(*args,**kwargs):
        worker=original_prepare(*args,**kwargs);assert 'ego_boundary' in worker.ready
        original_call=worker.call
        def call(op,obs):
            response,elapsed=original_call(op,obs)
            if op=='act':state['probe']=response['ego_motion_probe']
            return response,elapsed
        worker.call=call
        return worker
    diagnose.make_env,runtime.prepare=factory,prepare
    geometry.context_for_existing_detections,geometry.pack=context,pack
    try:
        result=geometry.geometry_episode(plan_path,plan,case,initial_pairs,arm)
    finally:
        diagnose.make_env,runtime.prepare=original_factory,original_prepare
        geometry.context_for_existing_detections,geometry.pack=original_context,original_pack
    result.update(ego_motion_privileged=True,ego_motion_intervention='retained coordinates propagated by previous/current vehicle pose only; original same-call cohort fixed')
    directory=plan_path.parent/'runs'/(case['id']+'__'+arm)
    write(directory/'result.json',result)
    write(directory/'ego-diagnostic.json',dict(counts=counts,first_contact=first,last_twenty=list(ring),
        no_target_truth_or_future_pose_in_motion_packet=True,new_offscreen_targets=0,no_promotion=True,
        comparisons_are_same_prestate_original_cohort=True,extra_policy_calls=0),exclusive=True)
    return result
