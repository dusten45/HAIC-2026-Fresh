"""A single legal16 residual applied after exact296 final scaling/clipping."""
import numpy as np
from retry.pedal306_base import Agent as FrozenAgent
from retry.pedal306_model import MEAN,STD,WEIGHTS
class Agent(FrozenAgent):
 def correct_pedals(self,features,nominal):
  self.delta_features=list(features)
  return super().correct_pedals(features,nominal)
 def act(self,observation):
  before=np.asarray(super().act(observation),np.float32);memory=float(self.controller.previous_steer)
  delta=np.clip(np.r_[(np.asarray(self.delta_features)-MEAN)/STD,1.]@WEIGHTS,-.5,.5)
  after=before.copy();after[1:]=np.clip(before[1:].astype(float)+delta,0,1).astype(np.float32)
  assert after[0]==before[0] and memory==float(self.controller.previous_steer)
  self.delta_audit=dict(before=before.tolist(),delta=delta.tolist(),after=after.tolist(),memory_preserved=True)
  return after
