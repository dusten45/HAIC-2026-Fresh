"""Saved-state reconstruction and hull/wheel road test. Creates no Box2D world."""
from dataclasses import replace
import math
from retry.brake502_response import Wheel,State
from retry.brake504_planar import Planar
from retry.brake506_geometry import Geometry,rectangle,polygon_distance
from retry.brake508_corridor import inside
from core.vendor.car_dynamics import HULL_POLY1,HULL_POLY2,HULL_POLY3,HULL_POLY4,SIZE,WHEELPOS


def load_root(x):
    p=dict(x['planar']);q=dict(p.pop('linear'))
    q['wheels']=tuple(Wheel(**dict(w,offset=tuple(w['offset']))) for w in q['wheels']);q['velocity']=tuple(q['velocity'])
    for name in ('levers','joints','rates','wheel_inertias'):
        p[name]=tuple(tuple(r) if isinstance(r,list) else r for r in p[name])
    p['linear']=State(**q)
    return Geometry(Planar(**p),tuple(x['center']),tuple((tuple(tuple(v) for v in poly),mu) for poly,mu in x['roads']),tuple(tuple(z) for z in x['current_contacts']),x['floor'],x['skin'])


def start_root(trigger,postreset,firstaction):
    # Stored reset has complete State but lacks planar/joint/full solver state.
    # Rotate the trigger's rigid body layout to the observed reset rear heading.
    # This is explicitly a reconstruction, qualified only by actual prefix replay.
    w=firstaction['before']['wheels'];angle=(w[2]['heading']+w[3]['heading'])/2
    delta=angle-trigger.planar.angle;c,s=math.cos(delta),math.sin(delta)
    levers=tuple((c*x-s*y,s*x+c*y) for x,y in trigger.planar.levers)
    z=dict(firstaction['before']);z['wheels']=tuple(Wheel(**dict(x,offset=tuple(x['offset']))) for x in z['wheels']);z['velocity']=tuple(z['velocity'])
    p=replace(trigger.planar,linear=State(**z),levers=levers,angle=angle,joints=tuple(x['heading']-angle for x in w),rates=(0.,)*4,yaw=0.,angular_momentum=0.,steer=0.)
    return replace(trigger,planar=p,center=tuple(postreset['position']),current_contacts=tuple(tuple(v) for v in firstaction['used_contacts']))


def polygons(root):
    p=root.planar;c,s=math.cos(p.angle),math.sin(p.angle)
    rotate=lambda q:(c*q[0]-s*q[1],s*q[0]+c*q[1])
    origins=[tuple(root.center[j]+r[j]-rotate((wx*SIZE,wy*SIZE))[j] for j in range(2)) for r,(wx,wy) in zip(p.levers,WHEELPOS)]
    origin=tuple(sum(z[j] for z in origins)/4 for j in range(2))
    hull=[[(origin[0]+rotate((x*SIZE,y*SIZE))[0],origin[1]+rotate((x*SIZE,y*SIZE))[1]) for x,y in poly] for poly in (HULL_POLY1,HULL_POLY2,HULL_POLY3,HULL_POLY4)]
    return hull+[rectangle(tuple(root.center[j]+r[j] for j in range(2)),w.heading) for r,w in zip(p.levers,p.linear.wheels)]


def margin(root,mesh,roadindex,edge,edgeindex):
    minimum=float('inf')
    for poly in polygons(root):
        x0=min(x for x,y in poly);x1=max(x for x,y in poly);y0=min(y for x,y in poly);y1=max(y for x,y in poly);distance=float('inf')
        for (a,b),(u0,u1,v0,v1) in zip(edge,edgeindex):
            lower=math.hypot(max(0.,u0-x1,x0-u1),max(0.,v0-y1,y0-v1))
            if lower>=distance:continue
            distance=min(distance,polygon_distance(poly,[a,b]))
        covered=all(any(a<=x<=b and c<=y<=d and inside((x,y),p) for (p,mu),(a,b,c,d) in zip(mesh,roadindex)) for x,y in poly)
        minimum=min(minimum,distance if covered else -distance)
    return minimum
