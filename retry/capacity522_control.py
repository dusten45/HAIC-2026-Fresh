"""One corner-budget change on the frozen519 Gaussian path and controls."""
import math
from retry.drive519_control import path_for as baseline_path,drive


def lateral_budget(static):
    state=static['root']['planar']['linear']
    return .70*sum(w['friction'] for w in state['wheels'])/state['mass']


def path_for(static,variant):
    path=baseline_path(static,'source_drive')
    if variant=='baseline':return path
    if variant!='capacity':raise ValueError('UNREGISTERED_VARIANT')
    budget=lateral_budget(static);ds=path['ds'];n=len(ds)
    q=[min(80.,math.sqrt(budget/max(abs(k),1e-8)))**2 for k in path['curvature']]
    for rounds in range(2*n):
        previous=q.copy()
        for i in range(n-1,-1,-1):q[i]=min(q[i],q[(i+1)%n]+90.*ds[i])
        for i in range(n):j=(i+1)%n;q[j]=min(q[j],q[i]+2*drive(q[i])*ds[i])
        if q==previous:break
    else:raise ValueError('CAPACITY_PROFILE_NONCONVERGENCE')
    launch=[0.]
    for i,d in enumerate(ds):launch.append(min(q[(i+1)%n],launch[-1]+2*drive(launch[-1])*d))
    path['periodic_squared']=q;path['launch_squared']=launch;path['periodic_pass_rounds']=rounds+1
    return path
