"""Frozen profile/executor adapters, without editing historical policy sources."""
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from retry.executor397 import CoherentExecutor
from retry.probe390_run import control_code
from retry.pace268_profile import multipliers
G=Path(__file__).resolve().parent.parent

def scope_for(env,fixed,pace):
 prof=fixed['free_profile'];ds=np.asarray(prof['ds']);sarc=np.r_[0,np.cumsum(ds)]
 return dict(env=env,line=np.asarray(fixed['line']),vprof=np.asarray(prof['speed']),ds=ds,curve=np.asarray(prof['curvature']),sarc=sarc,L=sarc[-1],model=fixed['model'],index=0,laststeer=0.,pace=np.asarray(pace))
def executor(fixed,pace):
 c=CoherentExecutor(fixed);c.nodes=np.asarray(fixed['free_profile']['speed'])*np.asarray(pace);return c
def fake_env(state):return SimpleNamespace(unwrapped=SimpleNamespace(car=SimpleNamespace(hull=SimpleNamespace(position=state['pos'],linearVelocity=state['vel'],angle=state['angle']))))
