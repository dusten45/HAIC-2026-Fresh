"""Frozen nominal policy with one TRAIN-only 22-input affine pedal head."""
import numpy as np
from retry.nominal248_source import Agent as FrozenNominal
from retry.hud248_features import decode
from retry.hud248_model import HEAD_MEAN,HEAD_STD,HEAD_WEIGHTS


class Agent(FrozenNominal):
    def act(self,observation):
        self.hud248=decode(observation[-1])
        return super().act(observation)

    def correct_pedals(self,features,nominal):
        inputs=np.r_[np.asarray(features,np.float64),self.hud248]
        residual=np.clip(np.r_[(inputs-HEAD_MEAN)/HEAD_STD,1.]@HEAD_WEIGHTS,-.5,.5)
        corrected=np.asarray(nominal,np.float32).copy()
        corrected[1:]=np.clip(corrected[1:].astype(np.float64)+residual,0,1).astype(np.float32)
        return corrected
