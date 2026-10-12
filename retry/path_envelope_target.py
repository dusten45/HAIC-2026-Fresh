"""Shorten only the final lookahead when its ideal arc leaves path clearance.

Legal inputs: the already selected polyline, original pixel speed and existing
tracked circles. This is a geometric screen, not a calibrated dynamics model.
The connected planner still scores routes with its original target function.
"""
import numpy as np

from retry.route_agent import route_target as original_target

# Official hull corner (+/-1.2,2.6)m encloses the other hull polygons and all
# wheels at their nominal joint anchors, for any steering angle. Include skin.
VEHICLE_RADIUS = float(np.hypot(1.2, 2.6)) + .009999999776482582
ARC_SPACING = .05  # Numerical resolution, inherited from the geometry screen.
LAST_TARGET_DIAGNOSTIC = {}


def path_prefix(path, distance):
    result = [path[0]]
    for a, b in zip(path[:-1], path[1:]):
        length = float(np.linalg.norm(b-a))
        if length <= 1e-12:
            continue
        if length >= distance:
            result.append(a+(b-a)*distance/length)
            break
        result.append(b)
        distance -= length
    return np.asarray(result)


def arc_path_margin(point, path, obstacles):
    """Sufficient circle clearance via balls centered on the path prefix.

    At every sampled arc center A, project onto the entire prefix to get Q.
    slack(Q)=min_j(|Q-C_j|-r_j)-vehicle_radius. Require
    slack(Q)-|A-Q| >= half the arc sampling interval. Each such ball covers
    the intervening arc points by the triangle inequality; no fitted margin.
    A negative bound is inconclusive, not a predicted physical collision.
    """
    x, y = point
    if y <= 0 or np.dot(point,point) <= 1e-12 or len(path)<2:
        return None
    curvature = 2*x/float(np.dot(point,point))
    angle = 2*np.arctan2(x,y)
    length = float(angle/curvature) if abs(curvature)>1e-12 else float(y)
    s = np.linspace(0,length,max(2,int(np.ceil(length/ARC_SPACING))+1))
    if abs(curvature)>1e-12:
        a = np.c_[(1-np.cos(curvature*s))/curvature,np.sin(curvature*s)/curvature]
    else:
        a = np.c_[np.zeros(len(s)),s]
    starts = path[:-1]; edges = np.diff(path,axis=0)
    squared = np.sum(edges*edges,axis=1); valid = squared>1e-20
    starts,edges,squared = starts[valid],edges[valid],squared[valid]
    if not len(starts):
        return None
    t = np.clip(np.sum((a[:,None,:]-starts)*edges,axis=2)/squared,0,1)
    projected = starts+t[:,:,None]*edges
    distances = np.linalg.norm(a[:,None,:]-projected,axis=2)
    index = np.argmin(distances,axis=1)
    q = projected[np.arange(len(a)),index]
    departure = distances[np.arange(len(a)),index]
    clearance = (np.linalg.norm(q[:,None,:]-obstacles[None,:,:2],axis=2)-obstacles[None,:,2]).min(axis=1)-VEHICLE_RADIUS
    half_spacing = float(s[1]-s[0])/2
    return dict(margin_m=float(np.min(clearance-departure))-half_spacing,
        maximum_departure_m=float(departure.max()),arc_length_m=length,
        sampling_half_interval_m=half_spacing)


def route_target(path, speed, obstacles=()):
    global LAST_TARGET_DIAGNOSTIC
    target = original_target(path,speed)
    LAST_TARGET_DIAGNOSTIC = dict(changed=False,reason='empty_path' if target is None else 'no_hazards',
        original_target=None if target is None else np.asarray(target).tolist(),
        selected_target=None if target is None else np.asarray(target).tolist(),tested=0)
    if target is None or not len(obstacles):
        return target
    p=np.asarray(path,float);h=np.asarray(obstacles,float).reshape(-1,3)
    cumulative=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    desired=min(float(np.clip(4+.35*speed,6,14)),float(cumulative[-1]))
    candidates=[(np.asarray(target),desired)]
    candidates.extend((p[i],float(cumulative[i])) for i in range(len(p)-1,0,-1)
        if cumulative[i]<desired-1e-9 and cumulative[i]>1e-9)
    original_margin=None
    for i,(point,distance) in enumerate(candidates):
        screen=arc_path_margin(point,path_prefix(p,distance),h)
        if i==0:
            original_margin=screen
        if screen is not None and screen['margin_m']>=0:
            LAST_TARGET_DIAGNOSTIC.update(changed=i>0,reason='shorter_path_target' if i else 'original_clear',
                selected_target=point.tolist(),tested=i+1,original_screen=original_margin,
                selected_screen=screen,original_path_distance_m=desired,selected_path_distance_m=distance)
            return point
    # No new stop/brake/steering fallback or persistent route-holding state.
    LAST_TARGET_DIAGNOSTIC.update(reason='no_certified_target_original_fallback',tested=len(candidates),
        original_screen=original_margin,original_path_distance_m=desired,selected_path_distance_m=desired)
    return target
