"""Phase-aware source launch, followed by byte-identical538tracking.

Finite online command optimization, not a fixed-gas parameter experiment.
"""
import math
from dataclasses import replace
import numpy as np
from retry.structure537_control import choose as tracking_choose,geometry_context
from retry.drive519_control import steering,project,reference,force_rows,nominal
from retry.preview527_control import backup
from retry.closure524_control import tick
from retry.brake508_corridor import bounds
from retry.corner515_model import margin
from retry.lap518_finish import hull_pose
LAUNCH_HOLDS=24
LAUNCH_ADMISSION=2.5-.001
TRACK_ADMISSION=1.06-.001


def traction_bound(root,ratio):
    """First-raw rear source-force upper command, including gas ramp branch."""
    limit=1.
    for w in root.planar.linear.wheels[2:]:
        f=(-math.sin(w.heading),math.cos(w.heading));side=(f[1],-f[0]);v=tuple(root.planar.linear.velocity[j]+w.offset[j] for j in range(2));vf=sum(f[j]*v[j] for j in range(2));vs=sum(side[j]*v[j] for j in range(2));available=(ratio*w.friction)**2-(82.*vs)**2
        if available<0:return 0.
        coefficient=.54*.02*40000*root.planar.linear.engine_multiplier/(1.6*(abs(w.omega)+5.));bound=(vf+math.sqrt(available)/82.-.54*w.omega)/coefficient
        command=1. if bound>=w.gas+.1 else max(0.,min(1.,bound));limit=min(limit,command)
    q=np.float32(limit)
    if float(q)>limit:q=np.nextafter(q,np.float32(0.))
    return float(q)


def choose_launch(root,high,low,progress,completed,history,counter,cost,max_ticks,geometry,guard=None):
    if not 0<=completed<24:raise ValueError('LAUNCH_ONLY')
    index=bounds(root.roads);cost.setdefault('geometry_checks',0);cost.setdefault('analytic_wheel_bounds',0);cost['analytic_wheel_bounds']+=4
    steer=steering(root,high,progress);points=sorted(set([float(np.float32(-1+i/8)) for i in range(17)]+[float(np.float32(.32)),traction_bound(root,1.-.001),traction_bound(root,LAUNCH_ADMISSION)]),reverse=True)
    def action(u):return np.array([steer,max(0.,u),max(0.,-u)],np.float32)
    def certify(a,full):
        r=root;s=progress;lc,ln=history;tc=tn=0;lp=tp=0.;minimum=float('inf');maxpath=maxover=maxbody=0.;first=None;cost['forecast_calls']+=1;cost.setdefault('launch_full_calls',0);cost.setdefault('launch_filter_calls',0);cost['launch_full_calls' if full else 'launch_filter_calls']+=1;nt=0
        def result(ok,reason):return dict(ok=ok,reason=reason,launch_peak=lp,tracking_peak=tp,launch_clipped=lc,launch_samples=ln,tracking_clipped=tc,tracking_samples=tn,launch_clip_prediction_threshold=.999,launch_clip_count_is_buffered=True,min_footprint_margin_m=minimum,max_path_error_m=maxpath,max_tracking_overspeed_m_s=maxover,max_body_speed_m_s=maxbody,first_hold=first,model_ticks=nt)
        def gap(r):
            if cost['geometry_checks']>=geometry['max_checks']:raise RuntimeError('LAUNCH_GEOMETRY_CAP')
            cost['geometry_checks']+=1
            return margin(r,geometry['roads'],geometry['road_index'],geometry['boundary'],geometry['edge_index'],geometry['obstacles'])
        minimum=gap(r)
        if minimum<.5:return result(False,'CURRENT_FOOTPRINT')
        for j in range(24-completed+12 if full else 1):
            h=completed+j;use=a if j==0 else (np.array([steering(r,high,s),.32,0.],np.float32) if h<24 else (nominal(r,high,s) if h==24 else backup(r,high,low,s)));r=replace(r,planar=replace(r.planar,steer=-float(use[0])))
            for k in range(4):
                if guard is not None:guard()
                cost['force_evaluations']+=4;forces=force_rows(r,use);peak=max(f['ratio'] for f in forces);clips=sum(f['ratio']>1.-.001 for f in forces) if h<24 else sum(f['clipped'] for f in forces)
                if h<24:
                    lc+=clips;ln+=4;lp=max(lp,peak)
                    if lp>LAUNCH_ADMISSION or lc>57 or (h>=23 and lc/ln>.15):return result(False,'LAUNCH_FORCE_OR_CLIP')
                else:
                    tc+=clips;tn+=4;tp=max(tp,peak)
                    if tp>TRACK_ADMISSION or tc/tn>.10:return result(False,'TRACK_FORCE_OR_CLIP')
                if counter[0]>=max_ticks:raise RuntimeError('LAUNCH_MODEL_CAP')
                before=r;r=tick(r,float(use[1]),float(use[2]),index,counter);cost['forecast_ticks']+=1;nt+=1;q=project(r.center,high,s);delta=q['s']-s;s=q['s'];minimum=min(minimum,gap(r));maxpath=max(maxpath,q['distance']);speed=math.hypot(*r.planar.linear.velocity);body=max(math.hypot(*(r.planar.linear.velocity[t]+w.offset[t] for t in range(2))) for w in r.planar.linear.wheels);maxbody=max(maxbody,body,math.hypot(*hull_pose(r)[1]))
                if h>=24:maxover=max(maxover,speed-reference(s,high)[0])
                if minimum<.5 or maxpath>3 or maxbody>=100 or maxover>4.85 or delta<-.5 or delta>max(5.,2*math.dist(before.center,r.center)):return result(False,'GEOMETRY_REFERENCE_BODY_PROJECTION')
                if j==0 and k==3:
                    slip=0.
                    for w in r.planar.linear.wheels[2:]:
                        f=(-math.sin(w.heading),math.cos(w.heading));vf=sum(f[t]*(r.planar.linear.velocity[t]+w.offset[t]) for t in range(2));slip+=(.54*w.omega-vf)**2
                    first=dict(progress_gain=s-progress,speed=speed,rear_slip_energy_proxy=slip)
        return result(True,'PHASE_CERTIFIED' if full else 'FIRST_HOLD_CERTIFIED')
    trials=[]
    for u in points:trials.append(dict(u=u,report=certify(action(u),False)))
    feasible=[t for t in trials if t['report']['ok']]
    rank=lambda t:(-t['report']['first_hold']['progress_gain'],t['report']['first_hold']['rear_slip_energy_proxy'],abs(t['u']),t['u'])
    feasible.sort(key=rank);short=feasible[:4];baseline=next((t for t in feasible if t['u']==float(np.float32(.32))),None)
    if baseline is not None and baseline not in short:short.append(baseline)
    full=[]
    for t in short:full.append(dict(u=t['u'],report=certify(action(t['u']),True)))
    good=[t for t in full if t['report']['ok']]
    if not good:return None,dict(mode='NO_LAUNCH_ADMISSIBLE_ACTION',filter_trials=trials,full_trials=full,final_recertified=False)
    good.sort(key=rank);best=good[0];selected=action(best['u']);final=certify(selected,True)
    if not final['ok']:return None,dict(mode='LAUNCH_FINAL_FAILED',filter_trials=trials,full_trials=full,final_recertified=False)
    return selected,dict(mode='SOURCE_LAUNCH',filter_trials=trials,full_trials=full,reports=[dict(mode='FINAL',**final)],final_recertified=True,horizon_holds=24-completed+12,selected_u=best['u'])
