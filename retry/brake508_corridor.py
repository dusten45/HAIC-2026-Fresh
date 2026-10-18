"""Deterministic curved strip, materials, and exact AABB contact acceleration."""
from dataclasses import replace
import math
from retry.brake502_response import DT
from retry.brake504_planar import step
from retry.brake506_geometry import contacts,rectangle,Geometry,select


def budget(cases=2,arms=2,holds=8,ticks=4):
    return dict(worlds=cases*arms,positive_ticks=cases*arms*holds*ticks,zero_dt_primes=cases*arms,
                failure_analysis_extra_worlds=0,failure_analysis_extra_ticks=0)


def corridor(origin_y=0.,mixed=False):
    R,W=40.,4.5;stations=list(range(-8,65,4))
    def point(s,d):
        a=s/R;return ((R+d)*math.cos(a)-R,origin_y+(R+d)*math.sin(a))
    roads=[];base=[]
    for i,(a,b) in enumerate(zip(stations,stations[1:])):
        quad=[point(a,-W),point(a,W),point(b,W),point(b,-W)];base.append(quad)
        roads.append((quad,.35 if mixed else 1.))
        if mixed:
            band=(-W,W) if i<4 or i%4==3 else ((0.,W) if i%4==0 else ((-W,0.) if i%4==2 else None))
            if band:
                lo,hi=band;roads.append(([point(a,lo),point(a,hi),point(b,hi),point(b,lo)],1.))
    inner=[point(s,-W) for s in stations];outer=[point(s,W) for s in stations]
    boundary=list(zip(inner,inner[1:]))+list(zip(outer,outer[1:]))+[(inner[0],outer[0]),(inner[-1],outer[-1])]
    return tuple(roads),base,boundary


def bounds(roads):
    return tuple((min(x for x,y in p),max(x for x,y in p),min(y for x,y in p),max(y for x,y in p)) for p,c in roads)


def indexed_contacts(footprint,roads,index,skin):
    x0=min(p[0] for p in footprint);x1=max(p[0] for p in footprint);y0=min(p[1] for p in footprint);y1=max(p[1] for p in footprint)
    result=[]
    for i,(a,b,c,d) in enumerate(index):
        if x1+skin<a or b+skin<x0 or y1+skin<c or d+skin<y0:continue
        if contacts(footprint,(roads[i],),skin):result.append(i)
    return tuple(result)


def forecast(state,brake,index=None,geometry=True):
    index=bounds(state.roads) if index is None else index;rows=[]
    for _ in range(4):
        p=state.planar
        membership=tuple(indexed_contacts(rectangle(tuple(state.center[j]+r[j] for j in range(2)),w.heading),state.roads,index,state.skin) for r,w in zip(p.levers,p.linear.wheels)) if geometry else state.current_contacts
        q=step(p,brake);center=tuple(state.center[j]+DT*q.linear.velocity[j] for j in range(2))
        if geometry:
            wheels=tuple(replace(w,friction=max([state.floor,*[400.*state.roads[i][1] for i in ids]])) for w,ids in zip(q.linear.wheels,membership))
            q=replace(q,linear=replace(q.linear,wheels=wheels))
        rows.append(dict(contacts_used=state.current_contacts,velocity_after=q.linear.velocity))
        state=replace(state,planar=q,center=center,current_contacts=membership)
    return state,rows


def choose(state,target,index):
    return select(lambda b:math.hypot(*forecast(state,b,index)[0].planar.linear.velocity),target)


def inside(p,poly):
    signs=[(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]) for a,b in zip(poly,poly[1:]+poly[:1])]
    return min(signs)>=0. or max(signs)<=0.
