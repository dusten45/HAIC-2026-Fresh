"""Finite577 future-tape certificate; observations never modify its payload."""
import math
from dataclasses import asdict,replace
import numpy as np
from retry.handoff562_model import FinishLineTracker,hull_pose,project,reference

def future_commands(commands,start):
    if not 1<=start<=166:raise ValueError('FINITE_TAPE_DOMAIN')
    return [(h,commands[h].copy()) for h in range(start,min(start+12,167))]
def phase_failure(index,raw,peak,history,overspeed=None):
    if index<=24:
        if peak>2.5:return 'LAUNCH_FORCE'
        if index==24 and raw==4 and history[0]/history[1]>.15:return 'LAUNCH_CLIP'
    else:
        if peak>1.059:return 'TRACK_FORCE'
        if history[0]/history[1]>.10:return 'TRACK_CLIP'
        if overspeed is not None and overspeed>4.85:return 'REFERENCE'
    return None
def finish_raw(finish,epoch):
    raw=round((finish-epoch)/.02)
    if abs((finish-epoch)-raw*.02)>1e-8:raise ValueError('OFFICIAL_CLOCK_NOT_RAW_GRID')
    return raw

def certify(owner,root,path,progress,start,commands,histories,tracker,visited,clock):
    r=root;s=progress;groups={k:list(v) for k,v in histories.items()};tr=FinishLineTracker(**asdict(tracker));seen=set(visited);time_s=clock;peak={'launch':0.,'running':0.};minimum=owner.source_geometry(r);n=0;sequence=[];snapshot=owner.short(root)
    def result(ok,reason):return dict(ok=ok,reason=reason,mode='FIXED_FUTURE_TAPE',start_global_hold=start,model_ticks=n,launch_peak=peak['launch'],tracking_peak=peak['running'],history=groups,min_footprint_margin_m=minimum,forecast_official_finish=tr.finish_time_s is not None,forecast_official_finish_time_s=tr.finish_time_s,certified_command_indices=sequence,actual_start_sha256=owner.hash(snapshot),actual_tracker_sha256=owner.hash(asdict(tracker)),actual_visited_sha256=owner.hash(sorted(visited)))
    if minimum<.50:return result(False,'CURRENT_FOOTPRINT')
    for h,use in future_commands(commands,start):
        sequence.append(h);r=replace(r,planar=replace(r.planar,steer=-float(use[0])));group='launch' if h<=24 else 'running'
        for k in range(1,5):
            f=owner.model_force(r,use);ratios=[z['ratio'] for z in f];groups[group][0]+=sum(z>1. for z in ratios);groups[group][1]+=4;peak[group]=max(peak[group],max(ratios));why=phase_failure(h,k,peak[group],groups[group])
            if why:return result(False,why)
            previous=r;r=owner.model_tick(r,float(use[1]),float(use[2]),owner.source_index,owner.model);n+=1;q=project(r.center,path,s);delta=q['s']-s;s=q['s'];minimum=min(minimum,owner.source_geometry(r));over=math.hypot(*r.planar.linear.velocity)-reference(s,path)[0]
            why=phase_failure(h,k,peak[group],groups[group],over)
            if why:return result(False,why)
            if minimum<.50 or q['distance']>3 or delta<-.5 or delta>max(5.,2*math.dist(previous.center,r.center)):return result(False,'GEOMETRY_PATH_PROJECTION')
            for ids in r.current_contacts:seen.update(ids)
            time_s+=.02;pose,velocity=hull_pose(r);tr.update(pose,velocity,len(seen)/owner.track_nodes,time_s)
            if tr.finish_time_s is not None:return result(True,'STRICT_THROUGH_FORECAST_OFFICIAL_FINISH')
    return result(True,'STRICT_FINITE_FUTURE_TAPE_HORIZON')
