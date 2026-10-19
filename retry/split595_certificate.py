"""593 certificate with branch/row telemetry only; predicates retain exact order."""
import math
from dataclasses import asdict,replace
from retry.handoff562_model import FinishLineTracker,hull_pose,reference
from retry.cold593_certificate import future_commands,phase_failure

def geometry_branches(minimum,distance,delta,limit):
    flags=dict(FOOTPRINT=minimum<.50,PATH=distance>3,PROJECTION_BACKWARD=delta<-.5,PROJECTION_FORWARD=delta>limit)
    return flags,next((k for k,v in flags.items() if v),None)

def certify(owner,root,path,progress,start,commands,histories,tracker,visited,clock):
    r=root;s=progress;groups={k:list(v) for k,v in histories.items()};tr=FinishLineTracker(**asdict(tracker));seen=set(visited);time_s=clock;peak={'launch':0.,'running':0.};minimum=owner.source_geometry(r);n=0;sequence=[];snapshot=owner.short(root)
    def result(ok,reason):return dict(ok=ok,reason=reason,mode='FIXED_FUTURE_TAPE',start_global_hold=start,model_ticks=n,launch_peak=peak['launch'],tracking_peak=peak['running'],history=groups,min_footprint_margin_m=minimum,forecast_official_finish=tr.finish_time_s is not None,forecast_official_finish_time_s=tr.finish_time_s,certified_command_indices=sequence,actual_start_sha256=owner.hash(snapshot),actual_tracker_sha256=owner.hash(asdict(tracker)),actual_visited_sha256=owner.hash(sorted(visited)))
    if minimum<.50:return result(False,'CURRENT_FOOTPRINT')
    for h,use in future_commands(commands,start):
        sequence.append(h);r=replace(r,planar=replace(r.planar,steer=-float(use[0])));group='launch' if h<=24 else 'running'
        for k in range(1,5):
            f=owner.model_force(r,use);ratios=[z['ratio'] for z in f];groups[group][0]+=sum(z>1. for z in ratios);groups[group][1]+=4;peak[group]=max(peak[group],max(ratios));why=phase_failure(h,k,peak[group],groups[group]);row=dict(global_raw=4*(h-1)+k,hold=h,raw=k,attempt=owner.counts['attempted_raw'],force_peak=max(ratios),prefix_peak=peak[group],history=groups[group].copy(),clip_fraction=groups[group][0]/groups[group][1],force_gate=why,clock_before=time_s,tracker_before=asdict(tr),visited_before=sorted(seen),before_root=owner.short(r))
            if why:row.update(first_failure=why,tick_executed=False,tracker_updated=False);owner.record(row);return result(False,why)
            previous=r;r=owner.model_tick(r,float(use[1]),float(use[2]),owner.source_index,owner.model);n+=1;q=owner.project(r.center,path,s);delta=q['s']-s;s=q['s'];margin=owner.source_geometry(r);minimum=min(minimum,margin);over=math.hypot(*r.planar.linear.velocity)-reference(s,path)[0];limit=max(5.,2*math.dist(previous.center,r.center));flags,branch=geometry_branches(minimum,q['distance'],delta,limit);why=phase_failure(h,k,peak[group],groups[group],over)
            row.update(tick_executed=True,root=owner.short(r),progress=s,path_error=q['distance'],projection_segment=q['i'],projection_t=q['t'],projection_delta=delta,projection_lower=-.5,projection_upper=limit,projection_point=q['point'],footprint=margin,minimum_footprint=minimum,reference_excess=over,geometry_flags=flags,first_failure=why or branch,proposed_clock=time_s+.02,tracker_updated=False)
            if why:owner.record(row);return result(False,why)
            if branch:owner.record(row);return result(False,'GEOMETRY_PATH_PROJECTION')
            for ids in r.current_contacts:seen.update(ids)
            time_s+=.02;pose,velocity=hull_pose(r);tr.update(pose,velocity,len(seen)/owner.track_nodes,time_s);row.update(tracker_updated=True,tracker_after=asdict(tr),visited_after=sorted(seen),clock_after=time_s);owner.record(row)
            if tr.finish_time_s is not None:return result(True,'STRICT_THROUGH_FORECAST_OFFICIAL_FINISH')
    return result(True,'STRICT_FINITE_FUTURE_TAPE_HORIZON')
