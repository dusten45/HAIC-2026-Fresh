"""Algebraic current-state tyre-cone projection. No model/force kernel imports.

This is a target proxy, NOT a prediction/certificate of servo/yaw evolution.
"""
import math
from collections import Counter
import numpy as np
COUNTS=Counter()
DT=.02;K=82.;R=.54
class LawStop(ValueError):pass

def wheel_formula(p,w,i,gas,brake):
    COUNTS['pure_wheel_formula']+=1
    vx,vy=[p['linear']['velocity'][j]+w['offset'][j] for j in range(2)]
    forward=(-math.sin(w['heading']),math.cos(w['heading']));side=(forward[1],-forward[0]);vf=forward[0]*vx+forward[1]*vy;vs=side[0]*vx+side[1]*vy
    g=w['gas']+min(.1,float(gas)-w['gas']) if i>=2 else w['gas']
    omega=w['omega']+DT*40000*p['linear']['engine_multiplier']*g/1.6/(abs(w['omega'])+5.)
    omega=0. if brake>=.9 else omega-math.copysign(min(15.*brake,abs(omega)),omega) if brake>0 else omega
    longitudinal=K*(omega*R-vf);lateral=-K*vs;magnitude=math.hypot(longitudinal,lateral);scale=min(1.,w['friction']/magnitude) if magnitude else 1.
    return dict(vf=vf,vs=vs,omega_braked=omega,rolling=omega*R,ratio=magnitude/w['friction'],longitudinal_ratio=longitudinal/w['friction'],lateral_ratio=lateral/w['friction'],vector=[scale*(longitudinal*forward[j]+lateral*side[j]) for j in range(2)])

def intersection(a,b):
    return [(max(x,u),min(y,v)) for x,y in a for u,v in b if max(x,u)<=min(y,v)]

def cone(p,w,rolling):
    COUNTS['pure_cone_coefficients']+=1
    vx,vy=[p['linear']['velocity'][j]+w['offset'][j] for j in range(2)];V=math.hypot(vx,vy);radius=w['friction']/K
    if not all(math.isfinite(z) for z in [V,rolling,radius,p['angle']]) or radius<=0:raise LawStop('NONFINITE_OR_FRICTION_DOMAIN')
    if V==0 or rolling==0:
        return [(-.4,.4)] if math.hypot(V,rolling)<=radius else []
    # Negative rolling speed changes the cone centre by pi.
    z=(rolling*rolling+V*V-radius*radius)/(2*abs(rolling)*V)
    if z>1:return []
    if z<=-1:return [(-.4,.4)]
    width=math.acos(z);theta=math.atan2(-vx,vy)+(math.pi if rolling<0 else 0.)-p['angle'];theta=math.atan2(math.sin(theta),math.cos(theta))
    return intersection([(-.4,.4)],[(theta+2*math.pi*k-width,theta+2*math.pi*k+width) for k in [-1,0,1]])

def virtual_ratio(p,w,rolling,q):
    COUNTS['pure_wheel_formula']+=1
    vx,vy=[p['linear']['velocity'][j]+w['offset'][j] for j in range(2)];heading=p['angle']+q;vf=-math.sin(heading)*vx+math.cos(heading)*vy;vs=math.cos(heading)*vx+math.sin(heading)*vy
    return K*math.hypot(rolling-vf,vs)/w['friction']

def select(root,nominal):
    COUNTS['pure_law_decisions']+=1
    a=np.asarray(nominal,np.float32)
    if a.shape!=(3,) or not np.all(np.isfinite(a)) or abs(float(a[0]))>float(np.float32(.4)) or any(not 0<=float(v)<=1 for v in a[1:]) or a[1]*a[2]!=0:raise LawStop('NOMINAL_ACTION_DOMAIN')
    p=root['planar'];wheels=p['linear']['wheels']
    if len(wheels)!=4:raise LawStop('WHEEL_DOMAIN')
    current=[wheel_formula(p,w,i,float(a[1]),float(a[2])) for i,w in enumerate(wheels)]
    intervals=[cone(p,w,current[i]['rolling']) for i,w in enumerate(wheels[:2])];feasible=intersection(intervals[0],intervals[1])
    if not feasible:raise LawStop('EMPTY_CURRENT_FRONT_CONE')
    goal=-float(a[0]);options=[]
    for low,high in feasible:
        # Nearest representable joint target within this closed interval.
        lo=np.float32(low);hi=np.float32(high)
        if float(lo)<low:lo=np.nextafter(lo,np.float32(math.inf))
        if float(hi)>high:hi=np.nextafter(hi,np.float32(-math.inf))
        if lo>hi:continue
        q=float(np.float32(max(float(lo),min(float(hi),goal))));ratios=None
        for repair in range(9):
            ratios=[virtual_ratio(p,w,current[i]['rolling'],q) for i,w in enumerate(wheels[:2])]
            if max(ratios)<=1.:break
            if repair==8:raise LawStop('CONE_FLOAT32_RECHECK')
            # Fixed bounded ULP repair toward the interval midpoint, no gain search.
            nxt=float(np.nextafter(np.float32(q),np.float32((low+high)/2)))
            if nxt==q or not low<=nxt<=high:raise LawStop('CONE_FLOAT32_EMPTY')
            q=nxt
        options.append((abs(q-goal),abs(q),q,ratios,repair,[low,high]))
    if not options:raise LawStop('NO_REPRESENTABLE_TARGET')
    distance,_,q,ratios,repair,interval=min(options,key=lambda z:z[:3]);action=np.array([-q,a[1],a[2]],np.float32)
    return action,dict(path_joint_target_rad=goal,selected_joint_target_rad=q,projected_distance_rad=distance,front_intervals_rad=intervals,common_intervals_rad=feasible,selected_interval_rad=interval,virtual_target_force_ratios=ratios,ULP_repairs=repair,current_force_formula=current,nominal_pedals_unchanged=action[1:].tobytes()==a[1:].tobytes(),current_joints_rad=p['joints'][:2],current_yaw_rad_s=p['yaw'],proxy_only=True)
