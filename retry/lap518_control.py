"""Same gains/rules on a closed path; explicit seam and launch speed semantics."""
import math
import numpy as np
from retry.envelope500 import source_pedals
from retry.speed516_control import force_rows
from retry.plan512_control import tick


def raw_projection(position,path):
    points=path['points'];arcs=path['arcs'];out=[]
    for i,a in enumerate(points):
        b=points[(i+1)%len(points)];dx,dy=b[0]-a[0],b[1]-a[1];d=dx*dx+dy*dy;t=max(0.,min(1.,((position[0]-a[0])*dx+(position[1]-a[1])*dy)/d));p=(a[0]+t*dx,a[1]+t*dy)
        out.append(dict(s=arcs[i]+t*math.sqrt(d),i=i,t=t,distance=math.dist(position,p),point=p,tangent=(dx/math.sqrt(d),dy/math.sqrt(d))))
    return out


def project(position,path,previous=None):
    L=path['length'];rows=raw_projection(position,path)
    if previous is None:
        q=min(rows,key=lambda x:x['distance']);q['s']=q['s'] if q['s']<=L/2 else q['s']-L;return q
    valid=[]
    for q in rows:
        q['s']+=round((previous-q['s'])/L)*L
        if previous-5.<=q['s']<=previous+30.:valid.append(q)
    if not valid:raise ValueError('PROJECTION_CONTINUITY_DOMAIN')
    return min(valid,key=lambda q:q['distance'])


def periodic_profile(caps,ds):
    q=[v*v for v in caps];n=len(q);rounds=0
    for _ in range(2*n):
        before=q.copy();rounds+=1
        for i in range(n-1,-1,-1):q[i]=min(q[i],q[(i+1)%n]+2*45.*ds[i])
        for i in range(n):j=(i+1)%n;q[j]=min(q[j],q[i]+2*25.*ds[i])
        if q==before:return q,rounds
    raise ValueError('PERIODIC_SPEED_PASS_NOT_CONVERGED')


def path_for(static,budget):
    if budget not in (80.,100.):raise ValueError('UNREGISTERED_BUDGET')
    source=[(p[2],p[3]) for p in static['track']];origin=min(range(len(source)),key=lambda i:math.dist(source[i],static['root']['center']));source=source[origin:]+source[:origin];n=len(source)
    if origin!=0:raise ValueError('RESET_START_ASSOCIATION')
    arcs=[0.]
    for i in range(n):arcs.append(arcs[-1]+math.dist(source[i],source[(i+1)%n]))
    base=dict(points=source,arcs=arcs,length=arcs[-1]);avoid=[]
    for center,radius in static['obstacles']:
        q=min(raw_projection(center,base),key=lambda x:x['distance'])
        if q['distance']>8.:raise ValueError('OBSTACLE_MAP_ASSOCIATION')
        signed=q['tangent'][0]*(center[1]-q['point'][1])-q['tangent'][1]*(center[0]-q['point'][0]);amplitude=-math.copysign(max(0.,3.8-abs(signed)),signed if signed else 1.);avoid.append((q['s'],amplitude))
    for i,(a,r) in enumerate(static['obstacles']):
        for b,t in static['obstacles'][i+1:]:
            if math.dist(a,b)<=r+t:raise ValueError('OVERLAPPING_NATIVE_OBSTACLES')
    adjusted=[]
    for i,p in enumerate(source):
        a,b=source[(i-1)%n],source[(i+1)%n];dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        offset=max(-3.8,min(3.8,sum(amplitude*math.exp(-.5*(min(abs(arcs[i]-s),arcs[-1]-abs(arcs[i]-s))/16.)**2) for s,amplitude in avoid)))
        adjusted.append((p[0]-dy/length*offset,p[1]+dx/length*offset))
    points=adjusted;ds=[math.dist(points[i],points[(i+1)%n]) for i in range(n)];arcs=[0.]
    for d in ds:arcs.append(arcs[-1]+d)
    curvature=[]
    for i,b in enumerate(points):
        a,c=points[(i-1)%n],points[(i+1)%n];u=tuple(b[j]-a[j] for j in range(2));v=tuple(c[j]-b[j] for j in range(2));curvature.append(math.atan2(u[0]*v[1]-u[1]*v[0],sum(x*y for x,y in zip(u,v)))/((ds[i-1]+ds[i])/2))
    caps=[min(80.,math.sqrt(budget/max(abs(k),1e-8))) for k in curvature];q,rounds=periodic_profile(caps,ds)
    launch=[min(q[i],2*25.*arcs[i]) for i in range(n)]+[min(q[0],2*25.*arcs[-1])]
    return dict(points=points,arcs=arcs,length=arcs[-1],ds=ds,curvature=curvature,periodic_squared=q,launch_squared=launch,periodic_pass_rounds=rounds,obstacle_association_count=len(avoid))


def reference(s,path):
    L=path['length'];first=0<=s<=L;u=min(max(s,0.),L) if first or s<0 else s%L
    i=next((i for i in range(len(path['ds'])) if path['arcs'][i+1]>=u),len(path['ds'])-1);d=path['ds'][i];f=max(0.,min(1.,(u-path['arcs'][i])/d))
    values=path['launch_squared'] if first or s<0 else path['periodic_squared']+[path['periodic_squared'][0]];q0,q1=values[i:i+2]
    return math.sqrt(max(0.,q0+f*(q1-q0))),(q1-q0)/(2*d)


def point_at(s,path):
    u=s%path['length'];i=next((i for i in range(len(path['ds'])) if path['arcs'][i+1]>=u),len(path['ds'])-1);f=(u-path['arcs'][i])/path['ds'][i]
    return tuple(path['points'][i][j]+f*(path['points'][(i+1)%len(path['points'])][j]-path['points'][i][j]) for j in range(2))


def steering(root,path,progress):
    q=project(root.center,path,progress);target=point_at(q['s']+max(7.,.3*math.hypot(*root.planar.linear.velocity)),path);dx,dy=(target[j]-root.center[j] for j in range(2));a=root.planar.angle
    delta=math.atan(3.24*2*(-math.sin(a)*dy-math.cos(a)*dx)/(dx*dx+dy*dy))
    return float(np.float32(-max(-.4,min(.4,delta))))


def nominal(root,path,progress):
    q=project(root.center,path,progress);v=math.hypot(*root.planar.linear.velocity);target,ff=reference(q['s'],path);sigma=sum(root.planar.linear.velocity[j]*q['tangent'][j] for j in range(2));accel=ff*sigma/max(target,1.)+2*(target-v);gas,brake=source_pedals(accel,v)
    return np.array([steering(root,path,q['s']),gas,brake],np.float32)


def forecast(root,action,path,progress,index,counter):
    from dataclasses import replace
    root=replace(root,planar=replace(root.planar,steer=-float(action[0])));rows=[]
    for _ in range(4):
        used=root.current_contacts;root=tick(root,float(action[1]),float(action[2]),index,counter);q=project(root.center,path,progress);progress=q['s'];rows.append(dict(contacts_used=used,velocity=root.planar.linear.velocity,position=root.center,angle=root.planar.angle,yaw=root.planar.yaw,progress=progress))
    return root,rows
