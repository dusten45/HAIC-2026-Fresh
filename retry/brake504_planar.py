"""One503 correction: propagate rigid planar yaw and source steering servo.

Contact friction remains frozen. No future contacts or data from actual future
ticks enter selection. Rigid joints and unsaturated steering motors are assumed.
"""
from dataclasses import dataclass, replace
import math
from retry.brake502_response import DT, wheel_response, bits, from_bits, f32


@dataclass(frozen=True)
class Planar:
    linear: object
    levers: tuple
    inertia: float
    angular_momentum: float
    yaw: float
    angle: float
    joints: tuple
    rates: tuple
    wheel_inertias: tuple
    steer: float
    steering_multiplier: float = 1.


def step(state,brake):
    items=[wheel_response(w,state.linear.velocity,0.,brake,state.linear.engine_multiplier) for w in state.linear.wheels]
    velocity=tuple(state.linear.velocity[j]+DT*sum(x[1][j] for x in items)/state.linear.mass for j in range(2))
    torque=sum(r[0]*x[1][1]-r[1]*x[1][0] for r,x in zip(state.levers,items))
    momentum=state.angular_momentum+DT*torque
    rates=tuple((math.copysign(min(50.*abs(state.steer-q),3.),state.steer-q)*state.steering_multiplier if i<2 and state.steer!=q else 0.) for i,q in enumerate(state.joints))
    yaw=(momentum-sum(I*r for I,r in zip(state.wheel_inertias,rates)))/state.inertia
    delta=DT*yaw;c,s=math.cos(delta),math.sin(delta)
    levers=tuple((c*x-s*y,s*x+c*y) for x,y in state.levers)
    joints=tuple(max(-.4,min(.4,q+DT*r)) for q,r in zip(state.joints,rates))
    angle=state.angle+delta
    wheels=tuple(replace(x[0],heading=angle+q,offset=(-yaw*r[1],yaw*r[0])) for x,q,r in zip(items,joints,levers))
    return replace(state,linear=replace(state.linear,velocity=velocity,wheels=wheels),levers=levers,angular_momentum=momentum,yaw=yaw,angle=angle,joints=joints,rates=rates)


def forecast(state,brake):
    for _ in range(4):state=step(state,brake)
    return state


def choose(state,target):
    end=lambda b:math.hypot(*forecast(state,b).linear.velocity)
    top=f32(.9);lock=from_bits(bits(top)+1)
    values=[end(top*i/16) for i in range(17)]
    if any(b>a+1e-10 for a,b in zip(values,values[1:])):raise ValueError('NONMONOTONE_STOP')
    if values[0]<=target:return 0.,values[0]
    if values[-1]>target:
        if end(lock)>target:raise ValueError('UNREACHABLE_STOP')
        return lock,end(lock)
    lo,hi=0,bits(top)
    while lo<hi:
        m=(lo+hi)//2
        if end(from_bits(m))<=target:hi=m
        else:lo=m+1
    value=from_bits(lo);prediction=end(value)
    if prediction>target or (lo and end(from_bits(lo-1))<=target):raise ValueError('FLOAT32_STOP')
    return value,prediction
