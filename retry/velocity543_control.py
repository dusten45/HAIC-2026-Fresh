"""537 source-response progress selection; nominal is a feasible sample, not an upper bound."""
import math
from dataclasses import replace
import numpy as np
from retry.braking526_control import path_for
from retry.drive519_control import nominal as legacy_nominal,project,force_rows,reference
from retry.lap518_control import point_at
from retry.closure524_control import tick
from retry.brake508_corridor import bounds
from retry.preview527_control import backup as legacy_backup,forecast
from retry.corner515_model import margin
from retry.brake510_common import boundary_index
HORIZON=12
EXTERNAL_ADMISSION=1.06
FORCE_BUFFER=.001
ADMISSION=EXTERNAL_ADMISSION-FORCE_BUFFER
# Existing native one-hold speed error allowance, not a tuned performance value.
TRACKING_RESERVE=.15


FOOTPRINT_ADMISSION=.50


def steering_velocity(root,path,progress):
    q=project(root.center,path,progress);vx,vy=root.planar.linear.velocity;v=math.hypot(vx,vy);target=point_at(q['s']+max(7.,.3*v),path);dx,dy=(target[j]-root.center[j] for j in range(2))
    if v==0.:fx,fy=-math.sin(root.planar.angle),math.cos(root.planar.angle)
    else:fx,fy=vx/v,vy/v
    delta=math.atan(3.24*2*(fx*dy-fy*dx)/(dx*dx+dy*dy))
    return float(np.float32(-max(-.4,min(.4,delta))))


def nominal(root,path,progress):
    action=legacy_nominal(root,path,progress).copy();action[0]=steering_velocity(root,path,progress);return action


def backup(root,high,low,progress):
    action=legacy_backup(root,high,low,progress).copy();action[0]=steering_velocity(root,high,progress);return action


def geometry_context(static,max_checks=65000):
    return dict(roads=static['roads'],road_index=bounds(static['roads']),boundary=static['boundary'],edge_index=boundary_index(static['boundary']),obstacles=static['obstacles'],max_checks=max_checks)


def certifier(root,high,low,progress,counter,cost,geometry,max_ticks=60000,history=(0,0)):
    if geometry is None:raise ValueError('FULL_GEOMETRY_REQUIRED')
    cost.setdefault('geometry_checks',0);index=bounds(root.roads);start_s=progress
    def check(r):
        if cost['geometry_checks']>=geometry['max_checks']:raise RuntimeError('GEOMETRY_COST_CAP_536')
        cost['geometry_checks']+=1
        return margin(r,geometry['roads'],geometry['road_index'],geometry['boundary'],geometry['edge_index'],geometry['obstacles'])
    def certify(a):
        r=root;s=progress;peak=maxover=0.;clipped,samples=history;nt=0;first=None;cost['forecast_calls']+=1;minimum=check(r);violation=None;first_pass=False
        def result(ok,reason):return dict(ok=ok,reason=reason,peak=peak,max_reference_overspeed=maxover,clipped=clipped,samples=samples,model_ticks=nt,first_hold=first,min_footprint_margin_m=minimum,first_footprint_violation=violation,first_hold_pass=first_pass)
        if minimum<FOOTPRINT_ADMISSION:return result(False,'CURRENT_FOOTPRINT_MARGIN')
        for j in range(HORIZON):
            use=a if j==0 else backup(r,high,low,s);r=replace(r,planar=replace(r.planar,steer=-float(use[0])))
            for k in range(4):
                f=force_rows(r,use);cost['force_evaluations']+=4;samples+=4;clipped+=sum(z['clipped'] for z in f);peak=max(peak,max(z['ratio'] for z in f))
                if peak>ADMISSION or clipped/samples>.10:return result(False,'FORCE_PEAK' if peak>ADMISSION else 'CLIP_HISTORY')
                if counter[0]>=max_ticks:raise RuntimeError('MODEL_TICK_CAP_528')
                before=r;r=tick(r,float(use[1]),float(use[2]),index,counter);cost['forecast_ticks']+=1;nt+=1;q=project(r.center,high,s);delta=q['s']-s;s=q['s'];v=math.hypot(*r.planar.linear.velocity);target=reference(s,high)[0];maxover=max(maxover,v-target)
                if j==0 and k==3:first=dict(speed=v,reference=target,positive_deficit=max(0.,target-v),progress_gain=s-start_s)
                minimum=min(minimum,check(r))
                if j==0 and k==3:first['min_footprint_margin_m']=minimum
                if minimum<FOOTPRINT_ADMISSION:
                    violation=dict(hold=j+1,raw_in_hold=k+1,raw_from_root=nt,margin_m=minimum)
                    return result(False,'FORECAST_FOOTPRINT_MARGIN')
                if maxover>5.-TRACKING_RESERVE:return result(False,'REFERENCE_WITH_NUMERIC_RESERVE')
                if q['distance']>3 or delta<-.5 or delta>max(5.,2*math.dist(before.center,r.center)):return result(False,'PROJECTION_OR_PATH')
                if j==0 and k==3:first_pass=True
        return result(True,'CERTIFIED_12HOLD_FLOAT32')
    return certify

def choose(root,high,low,progress,counter,cost,max_ticks=60000,history=(0,0),geometry=None):
    initial=nominal(root,high,progress);alternative=backup(root,high,low,progress);nominal_u=float(initial[1]) if initial[1]>0 else -float(initial[2]);upper=1.;oldlower=float(alternative[1]) if alternative[1]>0 else -float(alternative[2]);lower=-1.;before=cost['forecast_calls'];trials=[];cache={}
    if oldlower>upper or not -1<=upper<=1:raise ValueError('PEDAL_DOMAIN')
    certify=certifier(root,high,low,progress,counter,cost,geometry,max_ticks,history)
    def command(u):
        u=float(np.float32(u));return np.array([initial[0],max(0.,u),max(0.,-u)],np.float32)
    def evaluate(u):
        u=float(np.float32(u));u=0. if u==0 else u
        if not lower<=u<=upper:raise ValueError('PEDAL_OUTSIDE_DOMAIN')
        if u not in cache:
            if len(cache)>=31:raise RuntimeError('TRIAL_CAP_536')
            report=certify(command(u));cache[u]=dict(u=u,report=report);trials.append(dict(u=u,**report))
        return cache[u]
    high_trial=evaluate(upper)
    if high_trial['report']['ok']:
        full=command(upper);final=certify(full)
        if not final['ok']:return None,dict(mode='FINAL_CERTIFICATION_FAILED',reports=[dict(mode='FINAL',**final)],final_recertified=False)
        return full,dict(mode='SOURCE_FULL',reports=[dict(mode='HIGH',**high_trial['report']),dict(mode='FINAL',**final)],final_recertified=True,force_buffer=FORCE_BUFFER,internal_force_admission=ADMISSION,numerical_calls=0)
    lock=np.float32(.9)
    if float(lock)<.9:lock=np.nextafter(lock,np.float32(1.))
    below=np.nextafter(lock,np.float32(0.))
    points=[float(np.float32(-1+i/8)) for i in range(17)]+[upper,nominal_u,oldlower,-float(lock),-float(below)]
    points=sorted(set(x for x in points if lower<=x<=upper),reverse=True);coarse=[evaluate(x) for x in points]
    def regime(u):return 'locked' if u<0 and -u>=.9 else 'brake' if u<0 else 'coastgas'
    edges=[]
    for a,b in zip(coarse,coarse[1:]):
        if a['report']['ok']!=b['report']['ok'] and regime(a['u'])==regime(b['u']):
            safe=a if a['report']['ok'] else b;unsafe=b if a['report']['ok'] else a;edges.append(dict(safe=safe['u'],unsafe=unsafe['u'],score=safe['report']['first_hold']['progress_gain']))
    edges.sort(key=lambda x:(-x['score'],-x['safe']));refinements=0
    for i in range(9):
        if not edges or len(cache)>=31:break
        edge=edges[i%len(edges)];middle=float(np.float32((edge['safe']+edge['unsafe'])/2));lo=min(edge['safe'],edge['unsafe']);hi=max(edge['safe'],edge['unsafe'])
        if not lo<middle<hi:continue
        tested=evaluate(middle);refinements+=1
        if tested['report']['ok']:edge['safe']=middle
        else:edge['unsafe']=middle
    feasible=[x for x in cache.values() if x['report']['ok']]
    nonmonotone=any(a['report']['ok'] and not b['report']['ok'] for a,b in zip(coarse,coarse[1:]))
    if not feasible:return None,dict(mode='NO_ADMISSIBLE_ACTION',reports=[dict(mode='HIGH',**high_trial['report'])],trials=trials,final_recertified=False,coarse_nonmonotone=nonmonotone,coarse_points=len(points),refinements=refinements,force_buffer=FORCE_BUFFER,internal_force_admission=ADMISSION)
    best=max(feasible,key=lambda x:(x['report']['first_hold']['progress_gain'],x['u']));action=command(best['u']);final=certify(action)
    if cost['forecast_calls']-before>32:raise RuntimeError('CERTIFICATE_CAP_536')
    if not final['ok']:return None,dict(mode='FINAL_CERTIFICATION_FAILED',reports=[dict(mode='FINAL',**final)],trials=trials,final_recertified=False)
    if action[0].tobytes()!=initial[0].tobytes() or (action[1]>0 and action[2]>0):raise RuntimeError('ACTION_STEER_DOMAIN')
    mode='BACKUP' if np.array_equal(action,alternative) else ('NOMINAL' if np.array_equal(action,initial) else 'SOURCE_RESPONSE')
    return action,dict(mode=mode,reports=[dict(mode='HIGH',**high_trial['report']),dict(mode='FINAL',**final)],trials=trials,final_recertified=True,coarse_nonmonotone=nonmonotone,coarse_points=len(points),refinements=refinements,force_buffer=FORCE_BUFFER,internal_force_admission=ADMISSION,selected_below_old_backup=best['u']<oldlower,selected_above_nominal=best['u']>nominal_u,finite_samples_only=True)
