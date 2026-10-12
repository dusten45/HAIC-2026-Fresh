"""Frozen232 nominal path with a learned78parameter raw-residual addition."""
import numpy as np
from retry.nominal237_base import Agent as FrozenAgent
from retry.submission232_model import HEAD_MEAN, HEAD_STD, HEAD_WEIGHTS
from retry.addition237_model import THETA, ACTIVATION


class Agent(FrozenAgent):
    def correct_pedals(self, features, nominal):
        z=(np.asarray(features,np.float64)-HEAD_MEAN)/HEAD_STD
        raw=np.concatenate((z,[1.]))@HEAD_WEIGHTS
        h=z@THETA[:64].reshape(16,4)+THETA[64:68]
        if ACTIVATION=='tanh':h=np.tanh(h)
        else:assert ACTIVATION=='identity'
        added=h@THETA[68:76].reshape(4,2)+THETA[76:78]
        combined=raw+added
        pre=np.asarray(nominal,np.float32)[1:].astype(float)+np.clip(combined,-.5,.5)
        out=np.asarray(nominal,np.float32).copy();out[1:]=np.clip(pre,0,1).astype(np.float32)
        self.last_audit=dict(features=list(map(float,features)),nominal_action=np.asarray(nominal,np.float32).tolist(),
            raw_base=raw.tolist(),raw_addition=added.tolist(),raw_combined=combined.tolist(),
            residual_clipped=(np.abs(combined)>.5).tolist(),pedal_clipped=((pre<0)|(pre>1)).tolist(),
            nominal_memory_after=float(self.controller.previous_steer),nominal_memory_preserved=True,steering_unchanged=True)
        return out
