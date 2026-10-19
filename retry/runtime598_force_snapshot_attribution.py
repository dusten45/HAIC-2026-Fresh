"""External saved-state force attribution; never imported by the Agent."""
import argparse
from dataclasses import replace
import json,math,pickle,sys,time
from pathlib import Path
import numpy as np


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('checkpoint');parser.add_argument('estimated_input')
    parser.add_argument('trial_report');parser.add_argument('output')
    args=parser.parse_args();out=Path(args.output);assert not out.exists()
    cpu=time.process_time();wall=time.perf_counter();directory=Path(args.checkpoint)
    sys.path.insert(0,str(directory/'package'))
    import runtime598 as c
    from retry.runtime598_diagnostic import dump
    load=lambda p:json.loads(Path(p).read_text())
    x=load(args.estimated_input);root=c.load_required_root(x['root'])
    truth=load(directory/'external-truth-private.json');h=truth['hull']
    co,si=math.cos(h['angle']),math.sin(h['angle'])
    def vector(v):return (co*v[0]+si*v[1],-si*v[0]+co*v[1])
    vh=vector(h['velocity']);estimated_vh=c.hull_pose(root)[1]
    spin=tuple(w.omega for w in root.planar.linear.wheels)
    actual_spin=tuple(w['omega'] for w in truth['wheels'])
    joints=tuple(w['joint_angle'] for w in truth['wheels'])
    def canonical(velocity=estimated_vh,yaw=root.planar.yaw,omegas=spin,
                  angles=root.planar.joints,rates=root.planar.rates,
                  gases=None):
        wheels=tuple(replace(w,omega=o,heading=q,offset=(-yaw*r[1],yaw*r[0]),
                     gas=w.gas if gases is None else gases[i])
                     for i,(w,o,q,r) in enumerate(zip(root.planar.linear.wheels,omegas,angles,root.planar.levers)))
        linear=replace(root.planar.linear,velocity=(0.,0.),wheels=wheels)
        planar=replace(root.planar,linear=linear,yaw=yaw,joints=tuple(angles),rates=tuple(rates),
                 angular_momentum=root.planar.inertia*yaw+sum(I*r for I,r in zip(root.planar.wheel_inertias,rates)))
        provisional=replace(root,planar=planar);origin,bias=c.hull_pose(provisional)
        result=replace(provisional,planar=replace(planar,linear=replace(linear,velocity=tuple(v-b for v,b in zip(velocity,bias)))))
        assert math.dist(c.hull_pose(result)[1],velocity)<1e-12
        return result
    # Raw wheel velocities are used directly, with no nominal rigid projection.
    physical_wheels=tuple(c.Wheel(w['omega'],w['gas'],w['angle']-h['angle'],w['friction'],vector(w['velocity'])) for w in truth['wheels'])
    raw=replace(root,planar=replace(root.planar,linear=replace(root.planar.linear,
             velocity=(0.,0.),wheels=physical_wheels,engine_multiplier=truth['engine_multiplier'])))
    mass=root.planar.linear.mass;mh=h['mass'];mw=(mass-mh)/4
    cm=tuple((mh*h['world_center'][j]+mw*sum(w['position'][j] for w in truth['wheels']))/mass for j in range(2))
    vm=tuple((mh*h['velocity'][j]+mw*sum(w['velocity'][j] for w in truth['wheels']))/mass for j in range(2))
    levers=tuple(vector((w['position'][0]-cm[0],w['position'][1]-cm[1])) for w in truth['wheels'])
    raw_conversion=replace(root,center=vector((cm[0]-h['position'][0],cm[1]-h['position'][1])),
       planar=replace(root.planar,levers=levers,yaw=h['angular_velocity'],
       linear=replace(raw.planar.linear,velocity=vector(vm),wheels=tuple(replace(w,offset=vector((t['velocity'][0]-vm[0],t['velocity'][1]-vm[1]))) for w,t in zip(physical_wheels,truth['wheels'])))))
    origin,converted_v=c.hull_pose(raw_conversion)
    measured_canonical=canonical(velocity=vh,yaw=h['angular_velocity'],omegas=actual_spin,angles=joints,gases=tuple(w['gas'] for w in truth['wheels']))
    prediction_memory=pickle.loads((directory/'agent-before-private.pkl').read_bytes())
    # Four original own-action model ticks verify the saved endpoint chronology.
    prediction=prediction_memory['last_root'];previous_action=prediction_memory['previous_action'];counter=[0]
    for _ in range(4):
        prediction=replace(prediction,planar=replace(prediction.planar,steer=-float(previous_action[0])))
        prediction=c.tick(prediction,float(previous_action[1]),float(previous_action[2]),c.bounds(prediction.roads),counter)
    assert tuple((w.omega,w.gas) for w in prediction.planar.linear.wheels)==prediction_memory['predicted_wheels']
    assert prediction.planar.rates==prediction_memory['predicted_joint_rates']
    initial=c.nominal(root,x['high'],x['progress'])
    trials=load(args.trial_report)['report']['trials']
    actions=[np.array([initial[0],max(0.,t['u']),max(0.,-t['u'])],np.float32) for t in trials]
    lat=vh[0];speed=math.hypot(*estimated_vh)
    states=[('estimated',root),('canonical_identity',canonical()),
      ('wheelspin',canonical(omegas=actual_spin)),
      ('lateral_velocity_at_fixed_hull_speed',canonical(velocity=(lat,math.sqrt(max(0.,speed*speed-lat*lat))))),
      ('hull_velocity',canonical(velocity=vh)),('yaw',canonical(yaw=h['angular_velocity'])),
      ('joint_angles',canonical(angles=joints)),('joint_rates_zero',canonical(rates=(0.,)*4)),
      ('wheel_gas',canonical(gases=tuple(w['gas'] for w in truth['wheels']))),
      ('all_measured_canonical',measured_canonical),('raw_measured_first_force',raw),
      ('own_action_endpoint_preserving_core_offsets',prediction)]
    rows=[]
    for label,state in states:
        comparisons=[]
        for action in actions:
            f=c.force_rows(state,action)
            comparisons.append(dict(action=action,peak=max(w['ratio'] for w in f),force_rows=f))
        rows.append(dict(label=label,comparisons=comparisons,
            minimum_initial_peak=min(v['peak'] for v in comparisons),
            initial_passes=sum(v['peak']<=c.ADMISSION for v in comparisons)))
    velocity_residual=[]
    for i,w in enumerate(truth['wheels']):
        projected=tuple(measured_canonical.planar.linear.velocity[j]+measured_canonical.planar.linear.wheels[i].offset[j] for j in range(2))
        actual=vector(w['velocity'])
        velocity_residual.append(dict(wheel=i,canonical=projected,measured=actual,error_m_s=math.dist(projected,actual)))
    braking=[]
    quarter=next(a for a in actions if float(a[2])==.25)
    for label,state in [('estimated',root),('raw_measured',raw)]:
        details=[]
        for i,w in enumerate(state.planar.linear.wheels):
            gas=w.gas+min(.1,float(quarter[1])-w.gas) if i>=2 else w.gas
            _,_,d=c.wheel_response(w,state.planar.linear.velocity,gas,float(quarter[2]),state.planar.linear.engine_multiplier)
            forward=(-math.sin(w.heading),math.cos(w.heading));v=tuple(state.planar.linear.velocity[j]+w.offset[j] for j in range(2))
            details.append(dict(wheel=i,omega_before=w.omega,omega_drive=d['omega_drive'],omega_braked=d['omega_braked'],forward_velocity=sum(a*b for a,b in zip(forward,v)),lateral_velocity=forward[1]*v[0]-forward[0]*v[1]))
        braking.append(dict(label=label,quarter_brake=details,no_brake_peak=max(w['ratio'] for w in c.force_rows(state,np.array([quarter[0],0.,0.],np.float32)))))
    result=dict(rows=rows,brake_timing=braking,representation=dict(raw_conversion_origin_residual_m=math.hypot(*origin),raw_conversion_hull_velocity_residual_m_s=math.dist(converted_v,vh),nominal_wheel_velocity_residuals=velocity_residual),
       observed_errors=dict(estimated_hull_velocity=estimated_vh,measured_hull_velocity=vh,estimated_yaw=root.planar.yaw,measured_yaw=h['angular_velocity'],estimated_spin=spin,measured_spin=actual_spin,estimated_joint_angles=root.planar.joints,measured_joint_angles=joints,estimated_joint_rates=root.planar.rates,actual_joint_rates_recorded=False),
       own_action_prediction_exact=True,model_ticks=counter[0],native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,
       limits='Fixed existing cached trial commands only. Raw physical first-force evaluation is separate from nominal projection; actual joint rates absent. No true inputs enter Agent. No action search or threshold fit.')
    dump(out,result)
    print(json.dumps(dict(rows=[{k:v for k,v in row.items() if k!='comparisons'} for row in rows],representation=result['representation'],observed_errors=result['observed_errors'],model_ticks=result['model_ticks'],CPU_s=result['CPU_s']),indent=2))


if __name__=='__main__':main()
