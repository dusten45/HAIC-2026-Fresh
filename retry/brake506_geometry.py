"""Known convex road polygons + predicted wheel rectangles, source sensor lag.

Full road/body geometry is privileged mechanics input, not a pixel policy.
Contact limits for the NEXT force use the CURRENT pre-world-step footprint.
"""
from dataclasses import dataclass,replace
import math
from retry.brake502_response import DT,bits,from_bits,f32
from retry.brake504_planar import step


def point_segment(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1];d=dx*dx+dy*dy
    t=max(0.,min(1.,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/d)) if d else 0.
    return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)


def polygon_distance(a,b):
    separated=False
    for p in (a,b):
        for v,w in zip(p,p[1:]+p[:1]):
            axis=(v[1]-w[1],w[0]-v[0]);pa=[x*axis[0]+y*axis[1] for x,y in a];pb=[x*axis[0]+y*axis[1] for x,y in b]
            if min(pa)>max(pb) or min(pb)>max(pa):separated=True
    if not separated:return 0.
    return min([point_segment(p,u,v) for p in a for u,v in zip(b,b[1:]+b[:1])]+[point_segment(p,u,v) for p in b for u,v in zip(a,a[1:]+a[:1])])


def rectangle(center,angle):
    c,s=math.cos(angle),math.sin(angle)
    return [(center[0]+c*x-s*y,center[1]+s*x+c*y) for x,y in ((-.28,-.54),(.28,-.54),(.28,.54),(-.28,.54))]


def contacts(footprint,roads,skin):
    return tuple(i for i,(polygon,coefficient) in enumerate(roads) if polygon_distance(footprint,polygon)<=skin)


@dataclass(frozen=True)
class Geometry:
    planar: object
    center: tuple
    roads: tuple
    current_contacts: tuple
    floor: float
    skin: float


def forecast(state,brake):
    rows=[]
    for _ in range(4):
        p=state.planar
        computed=tuple(contacts(rectangle(tuple(state.center[j]+r[j] for j in range(2)),w.heading),state.roads,state.skin) for r,w in zip(p.levers,p.linear.wheels))
        q=step(p,brake)
        center=tuple(state.center[j]+DT*q.linear.velocity[j] for j in range(2))
        wheels=tuple(replace(w,friction=max([state.floor,*[400.*state.roads[i][1] for i in ids]])) for w,ids in zip(q.linear.wheels,computed))
        q=replace(q,linear=replace(q.linear,wheels=wheels))
        rows.append(dict(contacts_used=state.current_contacts,contact_query_center=state.center,contact_query_levers=p.levers,contact_query_headings=tuple(w.heading for w in p.linear.wheels),contacts_for_next_force=computed))
        state=replace(state,planar=q,center=center,current_contacts=computed)
    return state,rows


def select(end,target):
    """First feasible coarse bracket, then a feasible float32 boundary.

    Contact switches can destroy global monotonicity. No global minimality is
    claimed: earlier unsampled feasible islands may be missed and cost is gated.
    """
    top=f32(.9);lock=from_bits(bits(top)+1)
    samples=[f32(top*i/32) for i in range(33)]
    if end(0.)<=target:return 0.,end(0.)
    bracket=next(((samples[i-1],b) for i,b in enumerate(samples[1:],1) if end(b)<=target),None)
    if bracket is None:
        if end(lock)>target:raise ValueError('GEOMETRY_TARGET_UNREACHABLE_STOP')
        return lock,end(lock)
    lo,hi=map(bits,bracket)
    while lo<hi:
        m=(lo+hi)//2
        if end(from_bits(m))<=target:hi=m
        else:lo=m+1
    b=from_bits(lo);prediction=end(b)
    if prediction>target or (lo and end(from_bits(lo-1))<=target):raise ValueError('FLOAT32_BOUNDARY_STOP')
    return b,prediction


def choose(state,target):
    return select(lambda b:math.hypot(*forecast(state,b)[0].planar.linear.velocity),target)
