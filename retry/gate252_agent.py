"""Frozen251 correction gated3/12 after12 exact240 actions; nominal state never gated."""
import numpy as np
from retry.nominal251_source import Agent as FrozenNominal
from retry.submission232_model import HEAD_MEAN,HEAD_STD,HEAD_WEIGHTS
from retry.pedal251_model import CORRECTION


class Agent(FrozenNominal):
    def __init__(self):
        super().__init__();self.gate252_count=0;self.gate252_enabled=False

    def reset(self,observation):
        super().reset(observation);self.gate252_count=0;self.gate252_enabled=False

    def act(self,observation):
        self.gate252_enabled=self.gate252_count>=12 and (self.gate252_count-12)%12<3
        action=super().act(observation);self.gate252_count+=1
        return action

    def correct_pedals(self,features,nominal):
        row=np.r_[(np.asarray(features,np.float64)-HEAD_MEAN)/HEAD_STD,1.]
        correction=row@CORRECTION
        residual=np.clip(row@HEAD_WEIGHTS+(correction if self.gate252_enabled else 0.),-.5,.5)
        action=np.asarray(nominal,np.float32).copy()
        action[1:]=np.clip(action[1:].astype(float)+residual,0,1).astype(np.float32)
        return action
