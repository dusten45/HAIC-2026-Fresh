"""One persistent contact-loss event, unknown time/subset; no future schedule.

At most one event in the next three ticks is a declared uncertainty assumption,
not a guarantee for arbitrary roads. All subsets, including all-wheel loss, are
considered. The first tick uses the actually observed current contact state.
"""
from dataclasses import replace
import math
from retry.brake502_response import bits,from_bits,f32
from retry.brake504_planar import step


def histories(state,floors):
    if len(floors)!=4 or any(not 0<f<=w.friction for f,w in zip(floors,state.linear.wheels)):
        raise ValueError('INVALID_CONTACT_RANGE')
    eligible=[i for i,(f,w) in enumerate(zip(floors,state.linear.wheels)) if f<w.friction]
    return [(None,())]+[(tick,tuple(eligible[j] for j in range(len(eligible)) if mask>>j&1)) for tick in (1,2,3) for mask in range(1,1<<len(eligible))]


def end_speed(state,brake,floors,history):
    event,subset=history
    for tick in range(4):
        if event==tick:
            state=replace(state,linear=replace(state.linear,wheels=tuple(replace(w,friction=floors[i]) if i in subset else w for i,w in enumerate(state.linear.wheels))))
        state=step(state,brake)
    return math.hypot(*state.linear.velocity)


def choose(state,target,floors):
    scenarios=histories(state,floors)
    bound=lambda b:max(end_speed(state,b,floors,h) for h in scenarios)
    top=f32(.9);lock=from_bits(bits(top)+1)
    values=[bound(top*i/16) for i in range(17)]
    if any(b>a+1e-10 for a,b in zip(values,values[1:])):raise ValueError('WORST_RESPONSE_NONMONOTONE_STOP')
    if values[0]<=target:brake=0.
    elif values[-1]>target:
        if bound(lock)>target:raise ValueError('WORST_TARGET_UNREACHABLE_STOP')
        brake=lock
    else:
        lo,hi=0,bits(top)
        while lo<hi:
            m=(lo+hi)//2
            if bound(from_bits(m))<=target:hi=m
            else:lo=m+1
        brake=from_bits(lo)
        if bound(brake)>target or (lo and bound(from_bits(lo-1))<=target):raise ValueError('FLOAT32_BOUNDARY_STOP')
    ends=[end_speed(state,brake,floors,h) for h in scenarios]
    return brake,dict(scenarios=len(scenarios),min_end_speed=min(ends),max_end_speed=max(ends))
