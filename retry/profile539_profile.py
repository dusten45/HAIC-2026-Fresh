"""One fixed primary cap90 on frozen533 geometry; other profile rules unchanged."""
import math
from retry.envelope500 import MASS,REAR
TOP=90.

def rebuild_profile(path,lateral,top=TOP):
 q=[min(top**2,lateral/max(abs(k),1e-8)) for k in path['curvature']];ds=path['ds'];n=len(q)
 def drive(z):return min(REAR,80000./(MASS*(math.sqrt(max(0.,z))+2.7)))
 for rounds in range(2*n):
  old=q.copy()
  for i in range(n-1,-1,-1):q[i]=min(q[i],q[(i+1)%n]+160.*ds[i])
  for i in range(n):j=(i+1)%n;q[j]=min(q[j],q[i]+2*drive(q[i])*ds[i])
  if q==old:break
 else:raise RuntimeError('PROFILE_NONCONVERGENCE')
 launch=[0.]
 for i,d in enumerate(ds):launch.append(min(q[(i+1)%n],launch[-1]+2*drive(launch[-1])*d))
 return dict(path,periodic_squared=q,launch_squared=launch,periodic_pass_rounds=rounds+1)
