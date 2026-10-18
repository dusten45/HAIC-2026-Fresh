"""Gas-only implementation of the same nominal four-tick physical request."""
import math
import numpy as np
from retry.envelope500 import MASS
from retry.brake502_response import bits,from_bits
from retry.brake508_corridor import bounds
from retry.speed516_control import forecast


def request(root,nominal):
    a=np.asarray(nominal,np.float32)
    if a.shape!=(3,) or not np.isfinite(a).all() or a[1]<0 or a[1]>1 or a[2]<0 or a[2]>1:raise ValueError('NOMINAL_DOMAIN')
    speed=math.hypot(*root.planar.linear.velocity)
    if a[1]<=0:return dict(active=False,target=None,steady_acceleration=None)
    if a[2]>0:raise ValueError('SIMULTANEOUS_GAS_BRAKE')
    acceleration=80000*float(a[1])/(MASS*(speed+2.7))
    return dict(active=True,target=speed+.08*acceleration,steady_acceleration=acceleration)


def action(root,nominal,arm,counter):
    a=np.asarray(nominal,np.float32).copy();intent=request(root,a)
    if arm not in ('steady','response'):raise ValueError('UNKNOWN_ARM')
    if not intent['active'] or arm=='steady':return a,intent,dict(mode='PASSTHROUGH')
    index=bounds(root.roads);cache={}
    def end(g):
        g=float(np.float32(g));k=bits(g)
        if k not in cache:
            q=a.copy();q[1]=g;p,_=forecast(root,q,index,counter);cache[k]=math.hypot(*p.planar.linear.velocity)
        return cache[k]
    samples=[float(np.float32(i/8)) for i in range(9)];values=[end(g) for g in samples]
    # Sampled monotonicity is a local admission check, not a continuum proof.
    # Contact/slip switches can invalidate it: stop rather than extrapolate.
    if any(y<x-1e-9 for x,y in zip(values,values[1:])):raise ValueError('GAS_COARSE_NONMONOTONE')
    target=intent['target']
    if values[0]>=target:g=0.;mode='TARGET_BELOW_GAS0_END'
    elif values[-1]<target:g=1.;mode='TARGET_ABOVE_GAS1_END'
    else:
        j=next(i for i,v in enumerate(values) if v>=target);lo,hi=bits(samples[j-1]),bits(samples[j])
        while lo<hi:
            mid=(lo+hi)//2
            if end(from_bits(mid))>=target:hi=mid
            else:lo=mid+1
        g=from_bits(lo);prediction=end(g)
        if prediction<target or prediction-target>1e-4 or (lo and end(from_bits(lo-1))>=target):raise ValueError('GAS_FLOAT32_BRACKET_UNCERTIFIED')
        mode='LOCAL_FLOAT32_TARGET_BRACKET'
    a[1]=g
    if not np.array_equal(a[[0,2]],np.asarray(nominal,np.float32)[[0,2]]):raise ValueError('STEERING_BRAKE_CHANGED')
    return a,intent,dict(mode=mode,predicted_speed=end(g),target_residual=end(g)-target,coarse_min=values[0],coarse_max=values[-1],forecast_evaluations=len(cache))
