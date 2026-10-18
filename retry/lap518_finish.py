"""Source tracker on predicted hull/visited sensors: estimate, never actual finish."""
import math
from core.finish_line import FinishLineTracker
from core.vendor.car_dynamics import HULL_POLY1,HULL_POLY2,HULL_POLY3,HULL_POLY4,SIZE,WHEELPOS
from core.vendor.car_racing import TRACK_WIDTH,TRACK_DETAIL_STEP


def hull_pose(root):
    p=root.planar;c,s=math.cos(p.angle),math.sin(p.angle);rot=lambda x,y:(c*x-s*y,s*x+c*y)
    origins=[tuple(root.center[j]+r[j]-rot(wx*SIZE,wy*SIZE)[j] for j in range(2)) for r,(wx,wy) in zip(p.levers,WHEELPOS)];origin=tuple(sum(q[j] for q in origins)/4 for j in range(2))
    mass=cx=cy=0.
    for poly in (HULL_POLY1,HULL_POLY2,HULL_POLY3,HULL_POLY4):
        vertices=[(x*SIZE,y*SIZE) for x,y in poly];cross=[a[0]*b[1]-b[0]*a[1] for a,b in zip(vertices,vertices[1:]+vertices[:1])];area=sum(cross)/2
        x=sum((a[0]+b[0])*k for a,b,k in zip(vertices,vertices[1:]+vertices[:1],cross))/(6*area);y=sum((a[1]+b[1])*k for a,b,k in zip(vertices,vertices[1:]+vertices[:1],cross))/(6*area)
        mass+=abs(area);cx+=abs(area)*x;cy+=abs(area)*y
    offset=rot(cx/mass,cy/mass);lever=tuple(origin[j]+offset[j]-root.center[j] for j in range(2));velocity=(p.linear.velocity[0]-p.yaw*lever[1],p.linear.velocity[1]+p.yaw*lever[0])
    return origin,velocity


def tracker_for(static,root,visited,carry,clock):
    beta,x,y=static['track'][0][1:4];tracker=FinishLineTracker(center=(x,y),forward=(-math.sin(beta),math.cos(beta)),half_width=TRACK_WIDTH,half_depth=TRACK_DETAIL_STEP*.25,qualification_ratio=.95)
    position,velocity=hull_pose(root)
    if carry:
        if len(visited)/len(static['track'])>=.95:raise ValueError('UNOBSERVED_CARRY_TRACKER_HISTORY')
        tracker.departed_start_area=True
    tracker.update(position,velocity,len(visited)/len(static['track']),clock)
    return tracker
