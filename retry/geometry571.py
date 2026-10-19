"""Read-only exact-primitive identification and frozen separating supports."""
import math
import numpy as np
from retry.plan513_model import polygons
from retry.brake506_geometry import polygon_distance
from retry.brake508_corridor import inside

def closest(p,a,b):
    p=np.asarray(p,float);a=np.asarray(a,float);b=np.asarray(b,float);v=b-a;u=float(np.dot(p-a,v)/np.dot(v,v)) if np.dot(v,v) else 0.;return a+min(1.,max(0.,u))*v

def road_support(poly,a,b):
    candidates=[]
    for p in poly:
        q=closest(p,a,b);candidates.append((float(np.linalg.norm(np.asarray(p)-q)),np.asarray(p),q))
    for q in [a,b]:
        for p0,p1 in zip(poly,poly[1:]+poly[:1]):
            p=closest(q,p0,p1);candidates.append((float(np.linalg.norm(p-np.asarray(q))),p,np.asarray(q)))
    distance,p,q=min(candidates,key=lambda z:z[0])
    if distance<=0:raise ValueError('NONSEPARATED_ROAD_PRIMITIVE')
    n=(p-q)/distance;h=max(n@a,n@b);gap=float(min(np.asarray(poly)@n)-h)
    if abs(gap-distance)>1e-8:raise ValueError('ROAD_SUPPORT_NOT_EXACT')
    return n,float(h),distance

def obstacle_support(poly,center,radius):
    center=np.asarray(center);points=[closest(center,a,b) for a,b in zip(poly,poly[1:]+poly[:1])];p=min(points,key=lambda p:np.linalg.norm(p-center));distance=float(np.linalg.norm(p-center))
    if inside(tuple(center),poly) or distance==0:raise ValueError('NONSEPARATED_OBSTACLE_PRIMITIVE')
    n=(p-center)/distance;h=float(n@center+radius);gap=float(min(np.asarray(poly)@n)-h)
    if abs(gap-(distance-radius))>1e-8:raise ValueError('OBSTACLE_SUPPORT_NOT_EXACT')
    return n,h,distance-radius

def component(root,static,kind,poly_index,feature):
    poly=polygons(root)[poly_index]
    if kind=='road':n,h,gap=road_support(poly,*static['boundary'][feature])
    elif kind=='obstacle':n,h,gap=obstacle_support(poly,*static['obstacles'][feature])
    else:raise ValueError(kind)
    return dict(kind=kind,polygon=int(poly_index),feature=int(feature),normal=n,offset=h,gap=gap)

def active_component(root,static):
    pp=polygons(root);best=None
    for k,poly in enumerate(pp):
        lowx=min(p[0] for p in poly);highx=max(p[0] for p in poly);lowy=min(p[1] for p in poly);highy=max(p[1] for p in poly)
        for j,(a,b) in enumerate(static['boundary']):
            dx=max(0.,min(a[0],b[0])-highx,lowx-max(a[0],b[0]));dy=max(0.,min(a[1],b[1])-highy,lowy-max(a[1],b[1]))
            if best is not None and math.hypot(dx,dy)>best['gap']:continue
            dist=polygon_distance(poly,[a,b])
            if best is None or dist<best['gap']:best=dict(kind='road',polygon=k,feature=j,gap=dist)
        for j,(center,radius) in enumerate(static['obstacles']):
            if inside(center,poly):raise ValueError('OBSTACLE_INSIDE_POLYGON')
            dist=min(math.dist(center,closest(center,a,b)) for a,b in zip(poly,poly[1:]+poly[:1]))-radius
            if best is None or dist<best['gap']:best=dict(kind='obstacle',polygon=k,feature=j,gap=dist)
    answer=component(root,static,best['kind'],best['polygon'],best['feature']);assert abs(answer['gap']-best['gap'])<1e-8;return answer

def vertices(root):return np.asarray([point for poly in polygons(root) for point in poly],float)
def layout(root):
    offset=0;out=[]
    for poly in polygons(root):out.append(list(range(offset,offset+len(poly))));offset+=len(poly)
    return out
