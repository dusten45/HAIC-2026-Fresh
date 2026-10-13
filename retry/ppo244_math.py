"""Fixed244 latent Gaussian math, bounded pedal residual, reward accounting."""
import numpy as np

STD=.2
T_LIMIT=160.


def apply(base,latent):
    out=np.asarray(base,np.float32).copy()
    out[1:]=np.clip(out[1:].astype(float)+np.asarray([.03,.02])*np.tanh(latent),0,1).astype(np.float32)
    return out


def log_probability(latent,mean):
    return -.5*np.sum(((np.asarray(latent)-mean)/STD)**2,axis=-1)-2*np.log(STD)-np.log(2*np.pi)


def reward(progress,previous_progress,time_s,previous_time_s,terminal=None):
    r=progress-previous_progress-(time_s-previous_time_s)/T_LIMIT
    if terminal=='completed':r+=2-progress
    elif terminal=='DNF':r+=time_s/T_LIMIT-1
    else:assert terminal is None
    return float(r)
