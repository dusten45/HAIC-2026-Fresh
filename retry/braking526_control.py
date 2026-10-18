"""Only high-reference backward envelope45->80;525 governor unchanged."""
from retry.capacity522_control import path_for as profile
from retry.drive519_control import drive
from retry.governor525b_control import choose,forecast
BACKWARD=80.


def path_for(static,variant):
    if variant=='backup':return profile(static,'baseline')
    path=profile(static,'capacity')
    if variant=='baseline':return path
    if variant!='candidate':raise ValueError('UNKNOWN_VARIANT')
    # Begin with unchanged curvature/top80 node caps, not pre-braked45 q.
    budget=.70*sum(w['friction'] for w in static['root']['planar']['linear']['wheels'])/static['root']['planar']['linear']['mass']
    q=[min(80.**2,budget/max(abs(k),1e-8)) for k in path['curvature']];ds=path['ds'];n=len(q)
    for rounds in range(2*n):
        old=q.copy()
        for i in range(n-1,-1,-1):q[i]=min(q[i],q[(i+1)%n]+2*BACKWARD*ds[i])
        for i in range(n):j=(i+1)%n;q[j]=min(q[j],q[i]+2*drive(q[i])*ds[i])
        if q==old:break
    else:raise ValueError('BACKWARD80_PROFILE_NONCONVERGENCE')
    launch=[0.]
    for i,d in enumerate(ds):launch.append(min(q[(i+1)%n],launch[-1]+2*drive(launch[-1])*d))
    return dict(path,periodic_squared=q,launch_squared=launch,periodic_pass_rounds=rounds+1)
