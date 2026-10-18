"""Whole vehicle model margin against road boundaries and static obstacle circles."""
import math
from retry.plan513_model import margin as road_margin,polygons
from retry.brake506_geometry import point_segment
from retry.brake508_corridor import inside


def obstacle_margin(polys,obstacles):
    value=float('inf')
    for poly in polys:
        for center,radius in obstacles:
            d=min(point_segment(center,a,b) for a,b in zip(poly,poly[1:]+poly[:1]))
            value=min(value,(-d if inside(center,poly) else d)-radius)
    return value


def margin(root,roads,index,boundary,edgeindex,obstacles):
    return min(road_margin(root,roads,index,boundary,edgeindex),obstacle_margin(polygons(root),obstacles))
