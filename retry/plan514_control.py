"""One repair: bounded-residual backup prediction to physical interval center.

No epsilon feasibility test. Bounds are empirical sample allowances, not proofs
for unobserved states or independent wheel/joint/geometry errors.
"""
import math
from dataclasses import replace
import numpy as np
from retry.plan512_control import tick,pedal,BRAKE,station
from retry.plan513_control import steering,steered
from retry.brake508_corridor import bounds

POSITION_ALLOWANCE=.001
SPEED_ALLOWANCE=.002
PLANNING_NODE=30.
PHYSICAL_LOW=29.5
PHYSICAL_HIGH=30.5


def perturb(root,plan,sign):
    if sign==0:return root
    dv=sign*SPEED_ALLOWANCE;axis=plan['axis']
    p=root.planar;velocity=tuple(p.linear.velocity[j]+dv*axis[j] for j in range(2))
    # Coherent rolling-speed perturbation; independent slip/joint errors are NOT
    # enclosed by this two-coordinate uncertainty model.
    wheels=tuple(replace(w,omega=w.omega+dv*(-math.sin(w.heading)*axis[0]+math.cos(w.heading)*axis[1])/.54) for w in p.linear.wheels)
    center=tuple(root.center[j]+sign*POSITION_ALLOWANCE*axis[j] for j in range(2))
    return replace(root,center=center,planar=replace(p,linear=replace(p.linear,velocity=velocity,wheels=wheels)))


def guarded_arrival(root,action,plan,index,counter):
    for i in range(104):
        if i%4==0:
            old_station=station(root.center,plan);root=perturb(root,plan,1)
            if old_station<plan['gate']<=station(root.center,plan):return math.hypot(*root.planar.linear.velocity)
            if i>=4:
                if math.hypot(*root.planar.linear.velocity)<=PLANNING_NODE:return None
                root=steered(root,[steering(root,plan),0.,BRAKE])
        previous=root
        gas,brake=(float(action[1]),float(action[2])) if i<4 else (0.,BRAKE)
        root=tick(root,gas,brake,index,counter)
        a,b=station(previous.center,plan),station(root.center,plan)
        if b<=a:raise ValueError('PREDICTED_REVERSE')
        speed=math.hypot(*root.planar.linear.velocity)
        if a<plan['gate']<=b:
            v0=math.hypot(*previous.planar.linear.velocity);fraction=(plan['gate']-a)/(b-a)
            return v0+fraction*(speed-v0)
        if i>=4 and speed<=PLANNING_NODE:return None
    raise ValueError('GUARDED_BACKUP_HORIZON_EXHAUSTED')


def robust_action(root,steer,plan,counter):
    index=bounds(root.roads);probes=[]
    def feasible(u):
        action=pedal(u,steer);cross=guarded_arrival(root,action,plan,index,counter)
        ok=cross is None or cross<=PLANNING_NODE
        probes.append(dict(u=u,feasible=ok,guarded_crossing_speed_m_s=cross));return ok
    if feasible(1.):chosen=1.
    else:
        low=None;high=1.
        for i in range(1,9):
            u=1.-i/4
            if feasible(u):low=u;break
            high=u
        if low is None:raise ValueError('GUARDED_BACKUP_SET_EMPTY')
        for _ in range(18):
            middle=(low+high)/2
            if feasible(middle):low=middle
            else:high=middle
        chosen=low
    action=pedal(chosen,steer)
    crossing=guarded_arrival(root,action,plan,index,counter)
    if crossing is not None and crossing>PLANNING_NODE:raise ValueError('FLOAT32_GUARDED_PLAN_UNCERTIFIED')
    return action,dict(mode='PER_HOLD_RESIDUAL_BACKUP',guarded_crossing_speed_m_s=crossing,probes=probes)
