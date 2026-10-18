"""One map curve reference; one brake-release consistency filter."""
from dataclasses import replace
import math
import numpy as np
from retry.envelope500 import source_pedals
from retry.plan512_control import tick
from retry.brake508_corridor import bounds
from retry.brake502_response import bits,from_bits


def make_path(boundary,initial,obstacles=()):
    n=len(boundary)//2
    points=[tuple((boundary[i][0][j]+boundary[n+i][0][j])/2 for j in range(2)) for i in range(n)]
    origin=min(range(n),key=lambda i:math.dist(points[i],initial));points=points[origin:]+points[:origin]
    points=points[:100];arcs=[0.]
    for a,b in zip(points,points[1:]):arcs.append(arcs[-1]+math.dist(a,b))
    base=dict(points=points,arcs=arcs)
    avoid=[]
    for center,radius in obstacles:
        q=project(center,base)
        if q['distance']>8. or not 0<q['s']<arcs[-1]:continue
        signed=q['tangent'][0]*(center[1]-q['point'][1])-q['tangent'][1]*(center[0]-q['point'][0])
        amplitude=-math.copysign(max(0.,3.8-abs(signed)),signed if signed else 1.)
        avoid.append((q['s'],amplitude))
    adjusted=[]
    for i,point in enumerate(points):
        a,b=points[max(0,i-1)],points[min(len(points)-1,i+1)]
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        offset=max(-3.8,min(3.8,sum(amplitude*math.exp(-.5*((arcs[i]-s)/16.)**2) for s,amplitude in avoid)))
        adjusted.append((point[0]-dy/length*offset,point[1]+dx/length*offset))
    points=adjusted;arcs=[0.]
    for a,b in zip(points,points[1:]):arcs.append(arcs[-1]+math.dist(a,b))
    curvature=[0.]*len(points)
    for i in range(1,len(points)-1):
        a,b,c=points[i-1:i+2];u=tuple(b[j]-a[j] for j in range(2));v=tuple(c[j]-b[j] for j in range(2))
        curvature[i]=math.atan2(u[0]*v[1]-u[1]*v[0],sum(x*y for x,y in zip(u,v)))/((arcs[i+1]-arcs[i-1])/2)
    first=next(i for i,k in enumerate(curvature) if abs(k)>.02)
    last=first
    while last+1<len(points) and abs(curvature[last+1])>.02:last+=1
    begin=arcs[first]-20.;end=arcs[last]+40.
    if end>=arcs[-2]:raise ValueError('PATH_TOO_SHORT')
    # Geometry-based cap and standard fixed longitudinal forward/backward pass.
    speed=[min(80.,math.sqrt(80./max(abs(k),1e-8))) for k in curvature];speed[0]=0.
    for i in range(len(points)-2,-1,-1):speed[i]=min(speed[i],math.sqrt(speed[i+1]**2+2*45.*(arcs[i+1]-arcs[i])))
    for i in range(1,len(points)):speed[i]=min(speed[i],math.sqrt(speed[i-1]**2+2*25.*(arcs[i]-arcs[i-1])))
    return dict(points=points,arcs=arcs,curvature=curvature,speeds=speed,measurement_begin=begin,measurement_end=end,corner_begin=arcs[first],corner_end=arcs[last])


def project(position,path):
    best=None
    for i,(a,b) in enumerate(zip(path['points'],path['points'][1:])):
        dx,dy=b[0]-a[0],b[1]-a[1];d=dx*dx+dy*dy;t=max(0.,min(1.,((position[0]-a[0])*dx+(position[1]-a[1])*dy)/d))
        point=(a[0]+t*dx,a[1]+t*dy);distance=math.dist(position,point)
        if best is None or distance<best['distance']:
            best=dict(s=path['arcs'][i]+t*math.sqrt(d),i=i,t=t,distance=distance,point=point,tangent=(dx/math.sqrt(d),dy/math.sqrt(d)))
    return best


def point_at(s,path):
    i=next((i for i in range(len(path['arcs'])-1) if path['arcs'][i+1]>=s),len(path['arcs'])-2)
    f=max(0.,min(1.,(s-path['arcs'][i])/(path['arcs'][i+1]-path['arcs'][i])))
    return tuple(path['points'][i][j]+f*(path['points'][i+1][j]-path['points'][i][j]) for j in range(2))


def reference(s,path):
    i=next((i for i in range(len(path['arcs'])-1) if path['arcs'][i+1]>=s),len(path['arcs'])-2)
    ds=path['arcs'][i+1]-path['arcs'][i];f=max(0.,min(1.,(s-path['arcs'][i])/ds));v0,v1=path['speeds'][i:i+2]
    return math.sqrt(max(0.,v0*v0+f*(v1*v1-v0*v0))),(v1*v1-v0*v0)/(2*ds)


def future_floor(s,path):
    values=[reference(s,path)[0],reference(s+40.,path)[0]]+[v for x,v in zip(path['arcs'],path['speeds']) if s<=x<=s+40.]
    return min(values)


def steering(root,path):
    q=project(root.center,path);v=math.hypot(*root.planar.linear.velocity);look=max(7.,.3*v)
    target=point_at(q['s']+look,path);dx,dy=(target[j]-root.center[j] for j in range(2));a=root.planar.angle;forward=(-math.sin(a),math.cos(a))
    curvature=2*(forward[0]*dy-forward[1]*dx)/(dx*dx+dy*dy)
    delta=math.atan(3.24*curvature)
    return float(np.float32(-max(-.4,min(.4,delta))))


def hold(root,action,index,counter):
    root=replace(root,planar=replace(root.planar,steer=-float(action[0])));rows=[]
    for _ in range(4):
        used=root.current_contacts;root=tick(root,float(action[1]),float(action[2]),index,counter)
        rows.append(dict(contacts_used=used,position_after=root.center,velocity_after=root.planar.linear.velocity))
    return root,rows


def nominal(root,path):
    q=project(root.center,path);speed=math.hypot(*root.planar.linear.velocity);target,feedforward=reference(q['s'],path)
    sigma=sum(root.planar.linear.velocity[j]*q['tangent'][j] for j in range(2))
    accel=feedforward*sigma/max(target,1.)+2.*(target-speed)
    gas,brake=source_pedals(accel,speed)
    action=np.array([steering(root,path),gas,brake],np.float32)
    return action,dict(station=q['s'],reference_speed=target,future_floor=future_floor(q['s'],path),desired_accel=accel)


def command(root,path,arm,counter):
    action,details=nominal(root,path);details['brake_changed']=False
    index=bounds(root.roads)
    if arm=='release' and action[2]>0:
        initial=root;pred,rows=hold(initial,action,index,counter);floor=details['future_floor']
        if min(math.hypot(*r['velocity_after']) for r in rows)<floor-.15:
            target=floor+.002;coast=action.copy();coast[2]=0.;q,_=hold(initial,coast,index,counter)
            if math.hypot(*q.planar.linear.velocity)<=target:action[2]=0.
            else:
                lo,hi=0,bits(float(action[2]))
                while lo<hi:
                    m=(lo+hi)//2;a=action.copy();a[2]=from_bits(m);q,_=hold(initial,a,index,counter)
                    if math.hypot(*q.planar.linear.velocity)<=target:hi=m
                    else:lo=m+1
                action[2]=from_bits(lo)
            details['brake_changed']=True
    elif arm not in ('reference','release'):raise ValueError('UNKNOWN_ARM')
    return action,details
