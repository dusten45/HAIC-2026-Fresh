"""Fixed-budget source-response pedal search; every float32 action is certified."""
import math
from dataclasses import replace
import numpy as np
from retry.braking526_control import path_for
from retry.drive519_control import nominal,project,force_rows,reference
from retry.closure524_control import tick
from retry.brake508_corridor import bounds
from retry.preview527_control import backup,forecast
HORIZON=12
ADMISSION=1.06
# Existing native one-hold speed error allowance, not a tuned performance value.
TRACKING_RESERVE=.15


def choose(root,high,low,progress,counter,cost,max_ticks=120000,history=(0,0)):
    initial=nominal(root,high,progress);alternative=backup(root,high,low,progress);index=bounds(root.roads);start_s=progress;calls_before=cost['forecast_calls'];trials=[];cache={}
    def signed(a):
        if a[1]>0 and a[2]>0:raise ValueError('SIMULTANEOUS_PEDALS')
        return float(a[1]) if a[1]>0 else -float(a[2])
    upper=signed(initial);lower=signed(alternative)
    if lower>upper or lower< -1 or upper>1:raise ValueError('PEDAL_INTERVAL')
    def command(u):
        u=float(np.float32(u));u=0. if u==0 else u
        return np.array([initial[0],max(0.,u),max(0.,-u)],np.float32)
    def certify(a):
        r=root;s=progress;peak=maxover=0.;clipped,samples=history;nt=0;first=None;cost['forecast_calls']+=1
        def result(ok,reason):return dict(ok=ok,reason=reason,peak=peak,max_reference_overspeed=maxover,clipped=clipped,samples=samples,model_ticks=nt,first_hold=first)
        for j in range(HORIZON):
            use=a if j==0 else backup(r,high,low,s);r=replace(r,planar=replace(r.planar,steer=-float(use[0])))
            for k in range(4):
                f=force_rows(r,use);cost['force_evaluations']+=4;samples+=4;clipped+=sum(z['clipped'] for z in f);peak=max(peak,max(z['ratio'] for z in f))
                if peak>ADMISSION or clipped/samples>.10:return result(False,'FORCE_PEAK' if peak>ADMISSION else 'CLIP_HISTORY')
                if counter[0]>=max_ticks:raise RuntimeError('MODEL_TICK_CAP_528')
                before=r;r=tick(r,float(use[1]),float(use[2]),index,counter);cost['forecast_ticks']+=1;nt+=1;q=project(r.center,high,s);delta=q['s']-s;s=q['s'];v=math.hypot(*r.planar.linear.velocity);target=reference(s,high)[0];maxover=max(maxover,v-target)
                if j==0 and k==3:first=dict(speed=v,reference=target,positive_deficit=max(0.,target-v),progress_gain=s-start_s)
                if maxover>5.-TRACKING_RESERVE:return result(False,'REFERENCE_WITH_NUMERIC_RESERVE')
                if q['distance']>3 or delta<-.5 or delta>max(5.,2*math.dist(before.center,r.center)):return result(False,'PROJECTION_OR_PATH')
        return result(True,'CERTIFIED_12HOLD_FLOAT32')
    def evaluate(u):
        u=float(np.float32(u));u=0. if u==0 else u
        if not lower<=u<=upper:raise ValueError('FLOAT32_OUTSIDE_PEDAL_INTERVAL')
        if u not in cache:
            a=command(u);report=certify(a);cache[u]=dict(u=u,action=a,report=report);trials.append(dict(u=u,**report))
        return cache[u]
    high_trial=evaluate(upper)
    if high_trial['report']['ok']:
        return initial,dict(mode='HIGH',reports=[dict(mode='HIGH',**high_trial['report'])],final_recertified=True,numerical_calls=0,local_search_only=True)
    low_trial=evaluate(lower)
    # Explicitly cover gas/coast/brake and source float32 brake-lock discontinuity.
    points=[upper if i==0 else lower if i==8 else float(np.float32(upper-(upper-lower)*i/8)) for i in range(9)]
    if lower<=0<=upper:points.append(0.)
    lock=np.float32(.9)
    if float(lock)<.9:lock=np.nextafter(lock,np.float32(1.))
    below=np.nextafter(lock,np.float32(0.))
    for brake in (below,lock):
        u=-float(brake)
        if lower<=u<=upper:points.append(u)
    points=sorted(set(points),reverse=True);coarse=[evaluate(u) for u in points];seen_safe=False;nonmonotone=False
    for z in coarse:
        if z['report']['ok']:seen_safe=True
        elif seen_safe:nonmonotone=True
    feasible=[z for z in cache.values() if z['report']['ok']]
    if feasible and not nonmonotone:
        j=next(i for i,z in enumerate(coarse) if z['report']['ok'])
        if j:
            safe=coarse[j]['u'];unsafe=coarse[j-1]['u']
            for _ in range(16):
                middle=float(np.float32((safe+unsafe)/2))
                if not safe<middle<unsafe:break
                z=evaluate(middle)
                if z['report']['ok']:safe=middle
                else:unsafe=middle
            adjacent=float(np.nextafter(np.float32(safe),np.float32(1.)))
            if adjacent<=upper:evaluate(adjacent)
    feasible=[z for z in cache.values() if z['report']['ok']]
    if not feasible:return None,dict(mode='NO_ADMISSIBLE_ACTION',reports=[dict(mode='HIGH',**high_trial['report']),dict(mode='BACKUP',**low_trial['report'])],coarse_nonmonotone=nonmonotone,trials=trials,final_recertified=False)
    selected=max(feasible,key=lambda z:(z['report']['first_hold']['progress_gain'],z['u']));a=selected['action'].copy();final=certify(a)
    if cost['forecast_calls']-calls_before>32:raise RuntimeError('NUMERICAL_CALL_CAP_528')
    if not final['ok']:return None,dict(mode='FINAL_CERTIFICATION_FAILED',reports=[dict(mode='FINAL',**final)],trials=trials,final_recertified=False)
    if a[0].tobytes()!=initial[0].tobytes() or (a[1]>0 and a[2]>0):raise RuntimeError('COMMAND_DOMAIN_OR_STEER')
    mode='BACKUP' if np.array_equal(a,alternative) else 'RESPONSE'
    return a,dict(mode=mode,reports=[dict(mode='HIGH',**high_trial['report']),dict(mode='FINAL',**final)],coarse_nonmonotone=nonmonotone,coarse_points=len(points),bisection_limit=16,local_search_only=True,no_global_minimum_brake_claim=True,trials=trials,final_recertified=True,numerical_calls=cost['forecast_calls']-calls_before,numeric_tracking_reserve=TRACKING_RESERVE)
