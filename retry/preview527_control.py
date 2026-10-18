"""Current-state force governor: high153 first action with100-reference backup."""
import math
from dataclasses import replace
import numpy as np
from retry.braking526_control import path_for
from retry.drive519_control import nominal,project,force_rows,reference
from retry.closure524_control import tick
from retry.brake508_corridor import bounds
HORIZON=12
ADMISSION=1.06


def backup(root,high,low,s):
    a=nominal(root,high,s);b=nominal(root,low,s)
    return np.array([a[0],min(a[1],b[1]),max(a[2],b[2])],np.float32)


def choose(root,high,low,progress,counter,cost,max_ticks=120000,history=(0,0)):
    initial=nominal(root,high,progress);alternative=backup(root,high,low,progress);index=bounds(root.roads);reports=[]
    def certify(first):
        r=root;s=progress;peak=0.;maxover=0.;clipped,samples=history;nt=0;cost['forecast_calls']+=1
        for j in range(HORIZON):
            a=first if j==0 else backup(r,high,low,s);r=replace(r,planar=replace(r.planar,steer=-float(a[0])))
            for k in range(4):
                f=force_rows(r,a);cost['force_evaluations']+=4;samples+=4;clipped+=sum(z['clipped'] for z in f);peak=max(peak,max(z['ratio'] for z in f))
                if peak>ADMISSION or clipped/samples>.10:return dict(ok=False,reason='FORCE_PEAK' if peak>ADMISSION else 'CLIP_HISTORY',peak=peak,clipped=clipped,samples=samples,model_ticks=nt)
                if counter[0]>=max_ticks:raise RuntimeError('MODEL_TICK_CAP_525')
                previous=r;r=tick(r,float(a[1]),float(a[2]),index,counter);cost['forecast_ticks']+=1;nt+=1;q=project(r.center,high,s);delta=q['s']-s;s=q['s']
                maxover=max(maxover,math.hypot(*r.planar.linear.velocity)-reference(s,high)[0])
                if maxover>5.:return dict(ok=False,reason='REFERENCE_OVERSPEED',peak=peak,max_reference_overspeed=maxover,clipped=clipped,samples=samples,model_ticks=nt)
                if q['distance']>3 or delta<-.5 or delta>max(5.,2*math.dist(previous.center,r.center)):return dict(ok=False,reason='PROJECTION_OR_PATH',peak=peak,clipped=clipped,samples=samples,model_ticks=nt)
        return dict(ok=True,reason='CERTIFIED_FINITE_BACKUP',peak=peak,max_reference_overspeed=maxover,clipped=clipped,samples=samples,model_ticks=nt)
    for mode,a in [('HIGH',initial),('BACKUP',alternative)]:
        report=certify(a);reports.append(dict(mode=mode,**report))
        if report['ok']:return a,dict(mode=mode,reports=reports)
    return None,dict(mode='NO_ADMISSIBLE_ACTION',reports=reports)


def forecast(root,action,path,progress,index,counter):
    root=replace(root,planar=replace(root.planar,steer=-float(action[0])));rows=[]
    for _ in range(4):
        force=force_rows(root,action);used=root.current_contacts;root=tick(root,float(action[1]),float(action[2]),index,counter);q=project(root.center,path,progress);progress=q['s'];rows.append(dict(contacts_used=used,velocity=root.planar.linear.velocity,position=root.center,angle=root.planar.angle,yaw=root.planar.yaw,progress=progress,force_ratios=[z['ratio'] for z in force]))
    return root,rows
