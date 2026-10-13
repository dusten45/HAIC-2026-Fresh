"""Current240 pixel route and memory; replace final pedals by one local profile law."""
import time
import numpy as np
from retry.frozen240_root import Agent as Frozen240
import retry.nominal238_base as nominal_module

# Source-derived vehicle constants, common to roads; no runtime simulator reads.
MEFF=29.249793766661764
REAR_ACCEL=35.0188778925416
BRAKE_ACCEL=91.16873397261595


def profile(path,speed,lateral,cap):
    line=np.asarray(path,np.float64).reshape(-1,2)
    if len(line)<3 or not np.isfinite(line).all():return None
    ds=np.linalg.norm(np.diff(line,axis=0),axis=1)
    if np.any(ds<=1e-8):return None
    s=np.r_[0,np.cumsum(ds)]
    # Curvature chords sample the unchanged polyline one wheelbase either side.
    # This differentiates the existing pixel geometry; it never edits that route.
    a=np.maximum(0,s-3.24);b=np.minimum(s[-1],s+3.24)
    pa=np.c_[np.interp(a,s,line[:,0]),np.interp(a,s,line[:,1])]
    pb=np.c_[np.interp(b,s,line[:,0]),np.interp(b,s,line[:,1])]
    va=line-pa;vb=pb-line;vc=pb-pa
    k=2*(va[:,0]*vb[:,1]-va[:,1]*vb[:,0])/np.maximum(np.linalg.norm(va,axis=1)*np.linalg.norm(vb,axis=1)*np.linalg.norm(vc,axis=1),1e-9)
    k[0]=k[1];k[-1]=k[-2]
    limits=np.minimum(cap,np.sqrt(lateral/np.maximum(abs(k),1e-6)));v=limits.copy();v[0]=min(v[0],speed)
    # Unknown tail continues last observed curvature. Its cap remains nonzero.
    for _ in range(4):
        for i in range(len(v)-2,-1,-1):v[i]=min(v[i],np.sqrt(v[i+1]**2+2*BRAKE_ACCEL*ds[i]))
        for i in range(len(v)-1):
            acceleration=min(REAR_ACCEL,80000/(v[i]+2.7)/MEFF);v[i+1]=min(v[i+1],np.sqrt(v[i]**2+2*acceleration*ds[i]))
    return dict(speed=v,ds=ds,curvature=k,limits=limits,length=float(s[-1]))


class Agent(Frozen240):
    def __init__(self):
        super().__init__();self.last_path=None;self.last_obstacles=[];self.last_features=None
        route=nominal_module.connected_route
        def observe(*args,**kwargs):
            path=route(*args,**kwargs);self.last_path=path;self.last_obstacles=args[1];return path
        nominal_module.connected_route=observe

    def correct_pedals(self,features,nominal):
        self.last_features=list(features)
        return super().correct_pedals(features,nominal)

    def act(self,observation):
        self.last_path=None;self.last_features=None
        baseline=np.asarray(super().act(observation),np.float32)
        f=self.last_features
        self.last_plan=dict(active=False,fallback=True,reason='absent_or_nonforward_route',planner_ms=0.,baseline_pedals=baseline[1:].tolist(),steering_unchanged=True,nominal_memory_preserved=True)
        if f is None or bool(f[0]) or f[2]<=0 or self.last_path is None:return baseline
        tic=time.perf_counter();result=profile(self.last_path,max(0,f[4]),self.controller.lateral_acceleration,self.controller.speed_cap)
        if result is None:return baseline
        v=result['speed'];desired=float(v[0]);feed=float((v[1]**2-v[0]**2)/(2*result['ds'][0]));feedback=1.5*(desired-max(0,f[4]));acc=float(np.clip(feed+feedback,-BRAKE_ACCEL,REAR_ACCEL));speed=max(0,f[4]);action=baseline.copy()
        # Sole composition point: replace final post-head/post-scale pedals.
        # Reusing the residual/scales here would apply a second incompatible law.
        action[1]=np.clip(MEFF*max(acc,0)*(speed+2.7)/80000,0,1)
        action[2]=np.clip(MEFF*max(-acc,0)/(4*1.6*15/(.02*.54)),0,1)
        assert action[0]==baseline[0]
        self.last_plan=dict(planner_ms=(time.perf_counter()-tic)*1000,active=True,fallback=False,reason=None,path_points=len(self.last_path),path_length_m=result['length'],obstacle_count=len(self.last_obstacles),feedback_speed_m_s=speed,desired_speed_m_s=desired,feedforward_accel=feed,feedback_accel=feedback,command_accel=acc,tail_curvature=float(result['curvature'][-1]),tail_curvature_cap=float(result['limits'][-1]),tail_profile_speed=float(v[-1]),baseline_pedals=baseline[1:].tolist(),planner_pedals=action[1:].tolist(),steering_unchanged=True,nominal_memory_preserved=True,head_and_scales_bypassed_on_active=True)
        return action
