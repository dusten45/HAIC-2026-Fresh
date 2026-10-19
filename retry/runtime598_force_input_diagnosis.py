"""External fixed-action short force comparisons; never imported by the Agent."""
import argparse
import dataclasses as dc
import hashlib
import json
import math
from pathlib import Path
import pickle
import sys
import time
import numpy as np


def main():
    p=argparse.ArgumentParser();p.add_argument('checkpoint');p.add_argument('fixture');p.add_argument('output');a=p.parse_args()
    directory=Path(a.checkpoint);out=Path(a.output);out.mkdir(exist_ok=False);start=time.process_time()
    sys.path.insert(0,str(directory/'package'));import agent as participant;import runtime598 as core
    from retry.runtime598_diagnostic import dump
    import cv2
    load=lambda path:json.loads(Path(path).read_text())
    checkpoint=load(directory/'checkpoint-private.json');truth=load(directory/'external-truth-private.json');static=load(a.fixture)['static']
    image=cv2.imread(str(directory/'initial-private.png'),0);initial=np.repeat((image/255.).astype(np.float32)[None],4,axis=0)
    assert hashlib.sha256(initial.tobytes()).hexdigest()==static['observation_sha256'],'WORLD_MISMATCH'
    root=core.load_required_root(checkpoint['root']);h=truth['hull'];c,s=math.cos(h['angle']),math.sin(h['angle'])
    def vector(v):return (c*v[0]+s*v[1],-s*v[0]+c*v[1])
    vh=vector(h['velocity']);_,estimated_vh=core.hull_pose(root);actual_joints=tuple(w['joint_angle'] for w in truth['wheels'])
    actual_spin=tuple(w['omega'] for w in truth['wheels']);estimated_spin=tuple(w.omega for w in root.planar.linear.wheels)
    def canonical(velocity=estimated_vh,yaw=root.planar.yaw,spin=estimated_spin,joints=root.planar.joints,rates=root.planar.rates):
        wheels=tuple(dc.replace(w,omega=omega,heading=q,offset=(-yaw*r[1],yaw*r[0]))
            for w,omega,q,r in zip(root.planar.linear.wheels,spin,joints,root.planar.levers))
        linear=dc.replace(root.planar.linear,velocity=(0.,0.),wheels=wheels)
        planar=dc.replace(root.planar,linear=linear,yaw=yaw,joints=tuple(joints),rates=tuple(rates),
            angular_momentum=root.planar.inertia*yaw+sum(I*r for I,r in zip(root.planar.wheel_inertias,rates)))
        provisional=dc.replace(root,planar=planar);origin,bias=core.hull_pose(provisional)
        result=dc.replace(provisional,planar=dc.replace(planar,linear=dc.replace(linear,velocity=tuple(v-b for v,b in zip(velocity,bias)))))
        assert math.hypot(*origin)<1e-12 and math.dist(core.hull_pose(result)[1],velocity)<1e-12
        return result
    # Raw source-body conversion residual, kept distinct from observer error.
    mass=root.planar.linear.mass;mh=h['mass'];mw=(mass-mh)/4
    cm=tuple((mh*h['world_center'][j]+mw*sum(w['position'][j] for w in truth['wheels']))/mass for j in range(2))
    vm=tuple((mh*h['velocity'][j]+mw*sum(w['velocity'][j] for w in truth['wheels']))/mass for j in range(2))
    levers=tuple(vector((w['position'][0]-cm[0],w['position'][1]-cm[1])) for w in truth['wheels'])
    measured_wheels=tuple(dc.replace(w,omega=t['omega'],gas=t['gas'],heading=t['angle']-h['angle'],friction=t['friction'],
        offset=vector((t['velocity'][0]-vm[0],t['velocity'][1]-vm[1]))) for w,t in zip(root.planar.linear.wheels,truth['wheels']))
    raw=dc.replace(root,center=vector((cm[0]-h['position'][0],cm[1]-h['position'][1])),
        planar=dc.replace(root.planar,yaw=h['angular_velocity'],levers=levers,
        linear=dc.replace(root.planar.linear,velocity=vector(vm),wheels=measured_wheels)))
    raw_origin,raw_v=core.hull_pose(raw)
    memory=pickle.loads((directory/'agent-before-private.pkl').read_bytes());previous=memory['last_root'];action=memory['previous_action'];counter=[0]
    prediction=previous
    for _ in range(4):
        prediction=dc.replace(prediction,planar=dc.replace(prediction.planar,steer=-float(action[0])))
        prediction=core.tick(prediction,float(action[1]),float(action[2]),core.bounds(prediction.roads),counter)
    assert tuple((w.omega,w.gas) for w in prediction.planar.linear.wheels)==memory['predicted_wheels'],'OWN_ACTION_TIME_ALIGNMENT'
    motor=tuple(math.copysign(min(50*abs(-float(action[0])-q),3.),-float(action[0])-q) if i<2 else 0. for i,q in enumerate(actual_joints))
    # Actual joint angular velocities were not recorded: these are explicit
    # diagnostic assumptions, never labelled measured rates.
    states=[('estimated',root),('canonical_identity',canonical()),
      ('hull_velocity',canonical(velocity=vh)),
      ('speed_norm_only',canonical(velocity=tuple(v*math.hypot(*vh)/math.hypot(*estimated_vh) for v in estimated_vh))),
      ('yaw',canonical(yaw=h['angular_velocity'])),('wheelspin',canonical(spin=actual_spin)),
      ('joint_angle',canonical(joints=actual_joints)),('joint_rate_zero_assumption',canonical(rates=(0.,)*4)),
      ('joint_rate_predicted_end',canonical(rates=prediction.planar.rates)),
      ('joint_rate_motor_target_assumption',canonical(rates=motor)),
      ('wheelspin_stale_previous_decision',canonical(spin=tuple(w.omega for w in previous.planar.linear.wheels))),
      ('all_measured_observables_rate_average',canonical(velocity=vh,yaw=h['angular_velocity'],spin=actual_spin,joints=actual_joints)),
      ('all_measured_observables_rate_predicted',canonical(velocity=vh,yaw=h['angular_velocity'],spin=actual_spin,joints=actual_joints,rates=prediction.planar.rates)),
      ('all_measured_observables_rate_motor_assumption',canonical(velocity=vh,yaw=h['angular_velocity'],spin=actual_spin,joints=actual_joints,rates=motor))]
    actions=[t['action'] for t in load(directory/'forecasts-private.json')];rows=[]
    for label,state in states:
        comparisons=[]
        for action in actions:
            r=dc.replace(state,planar=dc.replace(state.planar,steer=-float(action[0])));peaks=[]
            for k in range(3):
                peaks.append(max(q['ratio'] for q in core.force_rows(r,action)))
                if k<2:r=core.tick(r,float(action[1]),float(action[2]),core.bounds(r.roads),counter)
            comparisons.append(dict(action=action,peaks=peaks))
        rows.append(dict(label=label,min_peak_by_tick=[min(q['peaks'][k] for q in comparisons) for k in range(3)],
            first_action_peaks=comparisons[0]['peaks'],first2tick_force_passes=sum(max(q['peaks'])<=core.ADMISSION for q in comparisons),comparisons=comparisons))
    # Nominal rigid projection and Box2D velocity-constraint time levels are
    # representation effects, not an observer correction or a core change.
    projection=[]
    for nominal,w in zip(np.asarray(core.WHEELPOS)*core.SIZE,truth['wheels']):
        lever=nominal-np.asarray(h['local_center']);actual=np.asarray(vector(w['velocity']));errors={}
        for label,angle in [('end_orientation',0.),('one_raw_tick_back',-h['angular_velocity']*core.DT)]:
            co,si=math.cos(angle),math.sin(angle);x,y=(co*lever[0]-si*lever[1],si*lever[0]+co*lever[1])
            velocity=np.asarray(vh)+h['angular_velocity']*np.array([-y,x]);errors[label]=float(np.linalg.norm(velocity-actual))
        projection.append(errors)
    summary=dict(wheel_velocity_representation_residuals=projection,rows=rows,raw_measured_conversion_position_residual_m=math.hypot(*raw_origin),
        raw_measured_conversion_velocity_residual_m_s=math.dist(raw_v,vh),canonical_hull_pose_and_velocity_match=True,
        estimated_hull_velocity=estimated_vh,measured_hull_velocity=vh,estimated_yaw=root.planar.yaw,measured_yaw=h['angular_velocity'],
        estimated_spin=estimated_spin,measured_spin=actual_spin,estimated_joint_rates=root.planar.rates,predicted_end_joint_rates=prediction.planar.rates,
        motor_rate_assumption=motor,actual_joint_rates_recorded=False,stack_frame_dt_s=.08,action_physics_ticks=4,
        own_action_prediction_wheelspin_memory_exact=True,model_ticks=counter[0],native_actions=0,CPU_s=time.process_time()-start,
        limits='Canonical nominal rigid projection; raw measured representation residual reported separately. No measured-state admission certificate, and unrecorded joint rates are assumptions. Fixed recorded candidate actions only; no controller/threshold changes.')
    dump(out/'result-private.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'},indent=2))
    print(json.dumps([{k:v for k,v in r.items() if k!='comparisons'} for r in rows],indent=2))
    assert counter[0]<5000 and summary['CPU_s']<60.


if __name__=='__main__':main()
