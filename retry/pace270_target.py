"""One prediction from original240 features; corrected goal only, never GT inputs."""
import time
import numpy as np
from retry.submission232_model import HEAD_MEAN,HEAD_STD
from retry.scalar270_model import WEIGHTS,LOG_MIN,LOG_MAX
from retry.mode270 import SAME_TARGET

def choose(agent,features):
    original=float(features[6]);first=getattr(agent,'pace270_first',True);agent.pace270_first=False
    if SAME_TARGET or first or bool(features[0]) or original<=0:
        agent.last_plan=dict(active=False,fallback=True,reason='identity' if SAME_TARGET else 'standing_start' if first else 'absent_or_zero_goal',planner_ms=0.,original_target=original,selected_target=original,pace_calls=0,steering_unchanged=True,nominal_memory_preserved=True)
        return original
    tic=time.perf_counter();row=np.r_[(np.asarray(features,np.float64)-HEAD_MEAN)/HEAD_STD,1.];raw=float(row@WEIGHTS);logpace=float(np.clip(raw,LOG_MIN,LOG_MAX));goal=original*float(np.exp(logpace))
    agent.last_plan=dict(active=True,fallback=False,reason=None,planner_ms=(time.perf_counter()-tic)*1000,original_target=original,selected_target=goal,raw_logpace=raw,logpace=logpace,log_clipped=raw!=logpace,pace_calls=1,steering_unchanged=True,nominal_memory_preserved=True)
    return goal
