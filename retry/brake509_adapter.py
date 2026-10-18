"""Privileged wrapper brake-only adapter, no environment creation or reset.

Reference steering/gas pass through; only exclusive braking requests are mapped
to a four-tick target using the original steady-torque convention. This does not
make full body/wheel/map information available in participant pixel observations.
"""
import hashlib,math,pickle
import numpy as np
from retry.brake502_response import DT,INERTIA,RADIUS
from retry.brake503_diagnostic import com
from retry.brake504_diagnostic import planar
from retry.brake506_geometry import Geometry
from retry.brake508_corridor import bounds,choose


def native_caps():
    return dict(arms=2,actions_per_arm=32,actions=64,resets=2,
                wrapper_raw_ticks=2*32*4,reset_raw_ticks=2*(1+50),total_raw_ticks=358,
                remaining_if_full=26027-64,reserve=84000,reserve_used=0)


def context(car,road_bodies,nominal,skip_frames=4,skin=.02):
    if skip_frames!=4:raise ValueError('UNSUPPORTED_SKIP_FRAMES')
    if len(car.wheels)!=4 or any(abs(w.wheel_rad-RADIUS)>1e-7 for w in car.wheels):
        raise ValueError('UNSUPPORTED_WHEEL_MODEL')
    # CarRacing.step applies car.steer(-action[0]). Body velocities are COM
    # velocities; hull.position is the body origin, not hull/world assembly COM.
    p=planar(car,-float(nominal[0]));grip=float(car.grip_multiplier)
    floor=400.*float(car.grass_friction_multiplier)*grip
    roads=tuple(([tuple(b.GetWorldPoint(v)) for v in b.fixtures[0].shape.vertices],float(b.road_friction)*grip) for b in road_bodies)
    def road_index(tile):
        for i,b in enumerate(road_bodies):
            if tile is b or tile==b:return i
        raise ValueError('CONTACT_NOT_IN_CURRENT_MAP')
    memberships=tuple(tuple(sorted(road_index(t) for t in w.tiles)) for w in car.wheels)
    for w,ids in zip(p.linear.wheels,memberships):
        predicted=max([floor,*[400.*roads[i][1] for i in ids]])
        if abs(w.friction-predicted)>1e-10:raise ValueError('EFFECTIVE_FRICTION_INPUT_MISMATCH')
    if abs(sum(b.mass for b in [car.hull,*car.wheels])-p.linear.mass)>1e-10:raise ValueError('MASS_MISMATCH')
    return Geometry(p,com(car,True),roads,memberships,floor,float(skin))


def brake_action(nominal,car,road_bodies,skip_frames=4,skin=.02):
    action=np.asarray(nominal,dtype=np.float32).copy()
    if action.shape!=(3,) or not np.isfinite(action).all():raise ValueError('BAD_NOMINAL')
    if not(-1<=action[0]<=1 and 0<=action[1]<=1 and 0<=action[2]<=1):raise ValueError('NOMINAL_OUT_OF_RANGE')
    if action[1]>0 and action[2]>0:raise ValueError('SIMULTANEOUS_GAS_BRAKE_UNQUALIFIED')
    if action[2]==0:
        return action,dict(mode='REFERENCE_ACCELERATION_OR_COAST_PASSTHROUGH',prediction_claim=False)
    root=context(car,road_bodies,action,skip_frames,skin)
    speed=math.hypot(*root.planar.linear.velocity)
    effective_mass=root.planar.linear.mass+4*INERTIA/RADIUS**2
    deceleration=float(action[2])*(4*INERTIA*15/(DT*RADIUS))/effective_mass
    target=speed-4*DT*deceleration
    if target<=0:raise ValueError('FORWARD_BRAKE_TARGET_NOT_POSITIVE')
    brake,prediction=choose(root,target,bounds(root.roads));action[2]=brake
    if not np.array_equal(action[:2],np.asarray(nominal,np.float32)[:2]):raise ValueError('NOMINAL_STEER_GAS_CHANGED')
    return action,dict(mode='BRAKE_RESPONSE_ONLY',target_speed=target,predicted_end_speed=prediction,
                       source_steer_target=root.planar.steer,effective_mass=effective_mass,
                       grip=car.grip_multiplier,engine=car.engine_multiplier,steering=car.steering_multiplier)


def act_once(reference,observation,car,road_bodies,**kwargs):
    nominal=np.asarray(reference.act(observation),dtype=np.float32)
    committed=hashlib.sha256(pickle.dumps(vars(reference),protocol=5)).hexdigest()
    action,details=brake_action(nominal,car,road_bodies,**kwargs)
    if hashlib.sha256(pickle.dumps(vars(reference),protocol=5)).hexdigest()!=committed:
        raise ValueError('NOMINAL_MEMORY_CHANGED_BY_ADAPTER')
    return action,details
