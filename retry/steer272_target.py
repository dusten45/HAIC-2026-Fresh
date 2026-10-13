"""Exact258 arc-anchored steering target; privileged diagnostic, no pace."""
import numpy as np

def target(line, ds, position, angle, speed, index, fraction):
    n=len(line); sarc=np.r_[0,np.cumsum(ds)]; i=index%n
    look=max(6.,min(25.,3.24+.22*speed))
    arc=sarc[i]+fraction*ds[i]; goal=(arc+look)%sarc[-1]
    j=min(n-1,int(np.searchsorted(sarc,goal,side='right')-1))
    alpha=(goal-sarc[j])/max(ds[j],1e-9)
    world=line[j]+alpha*(line[(j+1)%n]-line[j]); delta=world-position
    x=float(delta@np.array([np.cos(angle),np.sin(angle)]))
    y=float(delta@np.array([-np.sin(angle),np.cos(angle)]))
    norm2=float(delta@delta)
    return (x,y,norm2),dict(steering_lookahead_m=look,GT_actual_speed_m_s=speed,
        steering_target_right=x,steering_target_forward=y,steering_target_world_norm2=norm2)

def pack(observation, mode=0, path=(), steering=None):
    active=steering is not None
    return np.concatenate([observation.ravel(),np.array([mode,len(path),int(active),*(steering or (0.,0.,0.))]),
                           np.asarray(path,np.float64).ravel()]).astype(np.float64)
