"""Matched legal28 actor and equal31 critic; privileges are training-only."""
import fcntl
from pathlib import Path
import numpy as np
from retry.path271_run import read,save


def create():
    import torch
    from torch import nn
    torch.set_num_threads(1);torch.manual_seed(317)
    actor=nn.Sequential(nn.Linear(28,32,dtype=torch.float64),nn.Tanh(),nn.Linear(32,3,dtype=torch.float64))
    critic=nn.Sequential(nn.Linear(31,32,dtype=torch.float64),nn.Tanh(),nn.Linear(32,1,dtype=torch.float64))
    for net in [actor,critic]:
        nn.init.orthogonal_(net[0].weight,.5);nn.init.zeros_(net[0].bias)
        nn.init.zeros_(net[2].weight);nn.init.zeros_(net[2].bias)
    with torch.no_grad():critic[0].weight[:,28:]=0.
    return actor,critic


def inputs(x,progress,damage,time_fraction,arm):
    assert arm in ['B','C']
    privileged=np.array([progress,damage,time_fraction],np.float64)
    return np.r_[x,privileged if arm=='C' else np.zeros(3)],float(progress-time_fraction)


def charge(root,arm,phase):
    root=Path(root)
    with (root/'budget.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        b=read(root/'budget.json');local=read(root/arm/'budget.json')
        assert b['actions']<22384 and b[phase]<(16384 if phase=='training' else 6000)
        if phase=='training':assert local['training']<8192
        b['actions']+=1;b[phase]+=1;local['actions']+=1;local[phase]+=1
        save(root/'budget.json',b);save(root/arm/'budget.json',local)
        fcntl.flock(lock,fcntl.LOCK_UN)
