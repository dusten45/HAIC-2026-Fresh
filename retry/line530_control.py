"""Full-station racing line; unchanged528 controller and source speed laws."""
import math
import numpy as np
from retry.braking526_control import path_for as old_path
from retry.drive519_control import drive
from retry.response528_control import choose,forecast
from retry.path521_control import scalar_clock


def rebuild(points,static,backup=False):
    p=np.asarray(points,float);v=np.roll(p,-1,axis=0)-p;ds=np.linalg.norm(v,axis=1);u=np.roll(v,1,axis=0)
    k=np.arctan2(u[:,0]*v[:,1]-u[:,1]*v[:,0],(u*v).sum(axis=1))/((ds+np.roll(ds,1))/2)
    if min(ds)<1.:raise ValueError('DEGENERATE_PATH')
    lateral=100. if backup else .70*sum(w['friction'] for w in static['root']['planar']['linear']['wheels'])/static['root']['planar']['linear']['mass']
    q=np.minimum(80.**2,lateral/np.maximum(abs(k),1e-8)).tolist();ds=ds.tolist();n=len(ds);backward=45. if backup else 80.
    for rounds in range(2*n):
        previous=q.copy()
        for i in range(n-1,-1,-1):q[i]=min(q[i],q[(i+1)%n]+2*backward*ds[i])
        for i in range(n):j=(i+1)%n;q[j]=min(q[j],q[i]+2*drive(q[i])*ds[i])
        if previous==q:break
    else:raise ValueError('PROFILE_NONCONVERGENCE')
    launch=[0.]
    for i,d in enumerate(ds):launch.append(min(q[(i+1)%n],launch[-1]+2*drive(launch[-1])*d))
    return dict(points=p.tolist(),arcs=np.r_[0,np.cumsum(ds)].tolist(),length=sum(ds),ds=ds,curvature=k.tolist(),periodic_squared=q,launch_squared=launch,periodic_pass_rounds=rounds+1,obstacle_association_count=len(static['obstacles']))


def path_for(static,variant,points=None):
    if variant=='baseline':return old_path(static,'candidate')
    if variant=='baseline_backup':return old_path(static,'backup')
    if variant not in ('candidate','backup') or points is None:raise ValueError('FROZEN_POINTS_REQUIRED')
    return rebuild(points,static,backup=variant=='backup')
