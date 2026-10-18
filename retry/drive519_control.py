"""One change: constant25 forward envelope -> source rear/power node envelope."""
import math
from retry.lap518_control import path_for as baseline_path,project,nominal,steering,reference,force_rows
from retry.envelope500 import MASS,REAR


def drive(q):return min(REAR,80000./(MASS*(math.sqrt(max(0.,q))+2.7)))


def path_for(static,variant):
    path=baseline_path(static,100.)
    if variant=='baseline':return path
    if variant!='source_drive':raise ValueError('UNREGISTERED_VARIANT')
    ds=path['ds'];n=len(ds);q=[min(80.,math.sqrt(100./max(abs(k),1e-8)))**2 for k in path['curvature']]
    for rounds in range(2*n):
        previous=q.copy()
        for i in range(n-1,-1,-1):q[i]=min(q[i],q[(i+1)%n]+2*45.*ds[i])
        for i in range(n):j=(i+1)%n;q[j]=min(q[j],q[i]+2*drive(q[i])*ds[i])
        if previous==q:break
    else:raise ValueError('SOURCE_DRIVE_PERIODIC_NONCONVERGENCE')
    launch=[0.]
    for i,d in enumerate(ds):launch.append(min(q[(i+1)%n],launch[-1]+2*drive(launch[-1])*d))
    path['periodic_squared']=q;path['launch_squared']=launch;path['periodic_pass_rounds']=rounds+1;return path
