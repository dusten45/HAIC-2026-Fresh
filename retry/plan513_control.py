"""One frozen straight centering law; unchanged512 pedal limits and goal."""
from dataclasses import replace
import math
import numpy as np
from retry.plan512_control import tick,pedal,BRAKE,TARGET,GOAL,station,scalar_action,hold
from retry.brake508_corridor import bounds


def steering(root,plan):
    v=math.hypot(*root.planar.linear.velocity);look=max(12.,.4*v)
    s=station(root.center,plan)
    target=tuple(plan['start'][j]+(s+look)*plan['axis'][j] for j in range(2))
    dx,dy=(target[j]-root.center[j] for j in range(2));angle=root.planar.angle
    forward=(-math.sin(angle),math.cos(angle))
    curvature=2*(forward[0]*dy-forward[1]*dx)/(dx*dx+dy*dy)
    delta=math.atan(3.24*curvature)
    return float(np.float32(-max(-.15,min(.15,delta))))


def steered(root,action):return replace(root,planar=replace(root.planar,steer=-float(action[0])))


def arrival(root,action,plan,index,counter):
    previous=root
    for i in range(104):
        if i==4 and math.hypot(*root.planar.linear.velocity)<=TARGET:return station(root.center,plan),None
        if i<4:gas,brake=float(action[1]),float(action[2])
        else:
            gas,brake=0.,BRAKE
            if i%4==0:root=steered(root,[steering(root,plan),0.,BRAKE])
        root=tick(root,gas,brake,index,counter)
        old,new=station(previous.center,plan),station(root.center,plan)
        if new<=old:raise ValueError('PREDICTED_REVERSE')
        speed=math.hypot(*root.planar.linear.velocity)
        if old<plan['gate']<=new:
            v0=math.hypot(*previous.planar.linear.velocity);f=(plan['gate']-old)/(new-old)
            crossing=v0+f*(speed-v0);return plan['gate']+(crossing-TARGET),crossing
        if i>=4 and speed<=TARGET:
            v0=math.hypot(*previous.planar.linear.velocity);f=(v0-TARGET)/(v0-speed) if v0>speed else 1.
            return old+f*(new-old),None
        previous=root
    raise ValueError('BRAKE_HORIZON_EXHAUSTED')


def response_action(root,steer,plan,counter):
    index=bounds(root.roads);probes=[]
    def feasible(u):
        action=pedal(u,steer);stop,cross=arrival(root,action,plan,index,counter)
        ok=cross<=TARGET if cross is not None else stop<=plan['gate']
        probes.append(dict(u=u,feasible=ok,stop_station=stop));return ok
    if feasible(1.):chosen=1.
    else:
        high=1.;low=None
        for i in range(1,9):
            u=1.-i/4
            if feasible(u):low=u;break
            high=u
        if low is None:raise ValueError('RESPONSE_STOPPING_SET_EMPTY')
        for _ in range(18):
            mid=(low+high)/2
            if feasible(mid):low=mid
            else:high=mid
        chosen=low
    action=pedal(chosen,steer);stop,cross=arrival(root,action,plan,index,counter)
    if not(cross<=TARGET if cross is not None else stop<=plan['gate']):raise ValueError('FLOAT32_PLAN_UNCERTIFIED')
    return action,dict(mode='RESPONSE_STOPPING_DISTANCE',probes=probes,stop_station=stop)
