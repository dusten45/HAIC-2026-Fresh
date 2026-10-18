"""Bounded synthetic/native bridge accounting and geometry-only diagnostics."""
import math
from retry.brake506_geometry import polygon_distance
from retry.brake508_corridor import inside,bounds


def caps():
    return dict(synthetic_worlds=2*2,synthetic_ticks=2*2*3*4,synthetic_zero_primes=4,
                native_worlds=2,native_actions=2*32,native_resets=2,native_reset_ticks=2*51,
                native_action_ticks=2*32*4,native_total_ticks=2*51+2*32*4,
                all_positive_ticks=2*2*3*4+2*51+2*32*4,all_worlds=6)


def native_roads(road):
    return tuple(([tuple(b.GetWorldPoint(v)) for v in b.fixtures[0].shape.vertices],float(b.road_friction)) for b in road)


def track_boundary(track,width):
    left=[(x-width*math.cos(beta),y-width*math.sin(beta)) for _,beta,x,y in track]
    right=[(x+width*math.cos(beta),y+width*math.sin(beta)) for _,beta,x,y in track]
    return list(zip(left,left[1:]+left[:1]))+list(zip(right,right[1:]+right[:1]))


def boundary_index(boundary):
    return [(min(a[0],b[0]),max(a[0],b[0]),min(a[1],b[1]),max(a[1],b[1])) for a,b in boundary]


def clearance(car,base,road_index,boundary,edge_index):
    minimum=float('inf')
    for body in [car.hull,*car.wheels]:
        for fixture in body.fixtures:
            poly=[tuple(body.GetWorldPoint(v)) for v in fixture.shape.vertices]
            x0=min(v[0] for v in poly);x1=max(v[0] for v in poly);y0=min(v[1] for v in poly);y1=max(v[1] for v in poly)
            distance=float('inf')
            for (a,b),(u0,u1,v0,v1) in zip(boundary,edge_index):
                lower=math.hypot(max(0.,u0-x1,x0-u1),max(0.,v0-y1,y0-v1))
                if lower>=distance:continue
                distance=min(distance,polygon_distance(poly,[a,b]))
            covered=all(any(q0<=x<=q1 and r0<=y<=r1 and inside((x,y),p) for p,(q0,q1,r0,r1) in zip(base,road_index)) for x,y in poly)
            minimum=min(minimum,distance if covered else -distance)
    return minimum
