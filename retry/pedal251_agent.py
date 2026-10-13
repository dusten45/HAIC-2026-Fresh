"""Frozen240 head plus one16-input additive TRAIN-only affine correction."""
import numpy as np
from retry.nominal251_source import Agent as FrozenNominal
from retry.submission232_model import HEAD_MEAN,HEAD_STD,HEAD_WEIGHTS
from retry.pedal251_model import CORRECTION


class Agent(FrozenNominal):
    def correct_pedals(self,features,nominal):
        row=np.r_[(np.asarray(features,np.float64)-HEAD_MEAN)/HEAD_STD,1.]
        residual=np.clip(row@HEAD_WEIGHTS+row@CORRECTION,-.5,.5)
        action=np.asarray(nominal,np.float32).copy()
        action[1:]=np.clip(action[1:].astype(float)+residual,0,1).astype(np.float32)
        return action
