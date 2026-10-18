"""Append same map-path rule; retain all existing100 points exactly, no new gains."""
import math
from retry.speed516_control import path_for as old_path_for,force_rows,forecast
from retry.corner515_control import project,nominal,steering,reference


def path_for(static,budget):
    old=old_path_for(static,budget);boundary=static['boundary'];n=len(boundary)//2
    points=[tuple((boundary[i][0][j]+boundary[n+i][0][j])/2 for j in range(2)) for i in range(n)]
    initial=static['root']['center'];origin=min(range(n),key=lambda i:math.dist(points[i],initial));points=(points[origin:]+points[:origin])[:150]
    arcs=[0.]
    for a,b in zip(points,points[1:]):arcs.append(arcs[-1]+math.dist(a,b))
    base=dict(points=points,arcs=arcs);avoid=[]
    for center,radius in static['obstacles']:
        q=project(center,base)
        if q['distance']>8. or not 0<q['s']<arcs[-1]:continue
        signed=q['tangent'][0]*(center[1]-q['point'][1])-q['tangent'][1]*(center[0]-q['point'][0]);amplitude=-math.copysign(max(0.,3.8-abs(signed)),signed if signed else 1.)
        avoid.append((q['s'],amplitude))
    adjusted=[]
    for i,point in enumerate(points):
        a,b=points[max(0,i-1)],points[min(len(points)-1,i+1)];dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        offset=max(-3.8,min(3.8,sum(amplitude*math.exp(-.5*((arcs[i]-s)/16.)**2) for s,amplitude in avoid)))
        adjusted.append((point[0]-dy/length*offset,point[1]+dx/length*offset))
    adjusted[:len(old['points'])]=old['points'];points=adjusted;arcs=[0.]
    for a,b in zip(points,points[1:]):arcs.append(arcs[-1]+math.dist(a,b))
    assert points[:100]==old['points'] and arcs[:100]==old['arcs']
    curvature=[0.]*len(points)
    for i in range(1,len(points)-1):
        a,b,c=points[i-1:i+2];u=tuple(b[j]-a[j] for j in range(2));v=tuple(c[j]-b[j] for j in range(2))
        curvature[i]=math.atan2(u[0]*v[1]-u[1]*v[0],sum(x*y for x,y in zip(u,v)))/((arcs[i+1]-arcs[i-1])/2)
    first=next(i for i,k in enumerate(curvature) if arcs[i]>old['corner_end']+20 and abs(k)>.02)
    last=first
    while last+1<len(points) and abs(curvature[last+1])>.02:last+=1
    end=arcs[last]+40.
    if end+25.>=arcs[-2]:raise ValueError('EXTENDED_PATH_HORIZON_INSUFFICIENT')
    speed=[min(80.,math.sqrt(budget/max(abs(k),1e-8))) for k in curvature];speed[0]=0.
    for i in range(len(speed)-2,-1,-1):speed[i]=min(speed[i],math.sqrt(speed[i+1]**2+2*45.*(arcs[i+1]-arcs[i])))
    for i in range(1,len(speed)):speed[i]=min(speed[i],math.sqrt(speed[i-1]**2+2*25.*(arcs[i]-arcs[i-1])))
    for i,s in enumerate(old['arcs']):
        if s<=old['measurement_end']:assert speed[i]==old['speeds'][i]
    return dict(points=points,arcs=arcs,curvature=curvature,speeds=speed,measurement_begin=old['measurement_begin'],measurement_end=end,corner_begin=old['corner_begin'],corner_end=old['corner_end'],prior_window_end=old['measurement_end'],next_corner_begin=arcs[first],next_corner_end=arcs[last],next_approach=arcs[first]-20.)


def markers(path):return [('begin',path['measurement_begin']),('prior_window_end',path['prior_window_end']),('corner_exit',path['corner_end']),('next_approach',path['next_approach']),('next_entry',path['next_corner_begin']),('next_exit',path['next_corner_end']),('end',path['measurement_end'])]
