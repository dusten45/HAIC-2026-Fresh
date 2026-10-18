"""Only primary-reference cap80->90;528 algorithm and backup remain fixed."""
from retry.braking526_control import path_for as old_path
from retry.drive519_control import drive
from retry.response528_control import choose,forecast
TOP=90.


def path_for(static,variant):
    if variant=='baseline':return old_path(static,'baseline')
    if variant=='backup':return old_path(static,'backup')
    path=old_path(static,'candidate')
    if variant=='comparison':return path
    if variant!='candidate':raise ValueError('UNKNOWN_VARIANT')
    budget=.70*sum(w['friction'] for w in static['root']['planar']['linear']['wheels'])/static['root']['planar']['linear']['mass'];q=[min(TOP**2,budget/max(abs(k),1e-8)) for k in path['curvature']];ds=path['ds'];n=len(q)
    for rounds in range(2*n):
        before=q.copy()
        for i in range(n-1,-1,-1):q[i]=min(q[i],q[(i+1)%n]+160.*ds[i])
        for i in range(n):j=(i+1)%n;q[j]=min(q[j],q[i]+2*drive(q[i])*ds[i])
        if q==before:break
    else:raise ValueError('CAP90_PROFILE_NONCONVERGENCE')
    launch=[0.]
    for i,d in enumerate(ds):launch.append(min(q[(i+1)%n],launch[-1]+2*drive(launch[-1])*d))
    return dict(path,periodic_squared=q,launch_squared=launch,periodic_pass_rounds=rounds+1)
