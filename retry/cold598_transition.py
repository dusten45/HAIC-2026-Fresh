"""Bounded prefix certificate with one explicit future537 transition anchor."""
import math
from dataclasses import asdict,replace
from retry.handoff562_model import FinishLineTracker,hull_pose,reference
from retry.cold593_certificate import phase_failure

def horizon(start):
 if not 1<=start<=39:raise ValueError('PREFIX1_TO39_ONLY')
 return [(h,'FIXED577' if h<40 else 'ANCHOR537' if h==40 else 'BACKUP537') for h in range(start,start+12)]

def payload(h,mode,commands,root,history,choose,backup,path,low,progress):
 if mode=='FIXED577':return commands[h].copy(),None
 if mode=='ANCHOR537':return choose(root,path,low,progress,tuple(history))
 if mode=='BACKUP537':return backup(root,path,low,progress),None
 raise ValueError('UNKNOWN_FORECAST_MODE')

def certify(owner,root,path,progress,start,commands,histories,tracker,visited,clock):
 r=root;s=progress;groups={k:list(v) for k,v in histories.items()};tr=FinishLineTracker(**asdict(tracker));seen=set(visited);time_s=clock;peaks={'launch':0.,'running':0.};minimum=owner.source_geometry(r);n=0;sequence=[];anchor=None;first_failure=None
 def result(ok,reason):return dict(ok=ok,reason=reason,mode='FIXED_PREFIX_WITH_SINGLE_537_ANCHOR_AND_BACKUP',start_global_hold=start,model_ticks=n,launch_peak=peaks['launch'],tracking_peak=peaks['running'],history=groups,min_footprint_margin_m=minimum,forecast_official_finish=tr.finish_time_s is not None,forecast_official_finish_time_s=tr.finish_time_s,certified_holds=sequence,anchor537=anchor,first_failure=first_failure,actual_start_sha256=owner.hash(owner.short(root)),actual_tracker_sha256=owner.hash(asdict(tracker)),actual_visited_sha256=owner.hash(sorted(visited)))
 if minimum<.5:return result(False,'CURRENT_FOOTPRINT')
 for h,mode in horizon(start):
  use,detail=payload(h,mode,commands,r,groups['running'],owner.transition_choose,owner.backup_command,path,owner.candidate_backup,s)
  sequence.append(dict(hold=h,mode=mode))
  if mode=='ANCHOR537':
   anchor=detail
   if use is None:return result(False,'TRANSITION537_NO_FRESH_FINAL')
  r=replace(r,planar=replace(r.planar,steer=-float(use[0])));group='launch' if h<=24 else 'running'
  for k in range(1,5):
   history_before=groups[group].copy();f=owner.model_force(r,use);groups[group][0]+=sum(z['clipped'] for z in f);groups[group][1]+=4;peaks[group]=max(peaks[group],max(z['ratio'] for z in f));why=phase_failure(h,k,peaks[group],groups[group]);row=dict(hold=h,raw=k,mode=mode,history_before=history_before,history_after=groups[group].copy(),force_peak=peaks[group],clip_fraction=groups[group][0]/groups[group][1],pre_failure=why,tick_executed=False)
   if why:first_failure=row;owner.journal.append('PREFIX_FORECAST_RAW',label=owner.label,row=row);return result(False,why)
   previous=r;r=owner.model_tick(r,float(use[1]),float(use[2]),owner.source_index,owner.model);n+=1;q=owner.project('prefix_forecast',r.center,path,s);delta=q['s']-s;s=q['s'];gap=owner.source_geometry(r);minimum=min(minimum,gap);over=math.hypot(*r.planar.linear.velocity)-reference(s,path)[0];limit=max(5.,2*math.dist(previous.center,r.center));why=phase_failure(h,k,peaks[group],groups[group],over);flags=dict(FOOTPRINT=minimum<.5,PATH=q['distance']>3,PROJECTION_BACKWARD=delta<-.5,PROJECTION_FORWARD=delta>limit)
   split='REFERENCE' if why=='REFERENCE' else next((name for name,v in flags.items() if v),None);row.update(tick_executed=True,root_sha256=owner.hash(owner.short(r)),path_error=q['distance'],projection_segment=q['i'],projection_delta=delta,projection_lower=-.5,projection_upper=limit,footprint=gap,minimum_footprint=minimum,reference_excess=over,geometry_flags=flags,first_failure=why or split)
   owner.journal.append('PREFIX_FORECAST_RAW',label=owner.label,row=row)
   if why or split:first_failure=row;return result(False,why or split)
   for ids in r.current_contacts:seen.update(ids)
   time_s+=.02;pose,velocity=hull_pose(r);tr.update(pose,velocity,len(seen)/owner.track_nodes,time_s)
   if tr.finish_time_s is not None:return result(True,'STRICT_THROUGH_FORECAST_OFFICIAL_FINISH')
 return result(True,'STRICT_PREFIX_ANCHOR_BACKUP_HORIZON')
