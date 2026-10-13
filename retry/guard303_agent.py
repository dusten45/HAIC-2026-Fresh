"""Exact296 with one near-hazard target-absent nominal-zero-gas consistency gate."""
import numpy as np
from retry.guard303_base import Agent as FrozenAgent
class Agent(FrozenAgent):
 def correct_pedals(self,features,nominal):
  self.guard_features=list(features)
  return super().correct_pedals(features,nominal)
 def act(self,observation):
  before=np.asarray(super().act(observation),np.float32);memory=float(self.controller.previous_steer);f=self.guard_features;active=bool(f[8]==1 and f[14]==0 and f[0]==1);after=before.copy()
  if active:after[1]=np.float32(0.)
  assert after[0]==before[0] and after[2]==before[2] and float(self.controller.previous_steer)==memory
  self.guard_audit=dict(active=active,before=before.tolist(),after=after.tolist(),feature0=float(f[0]),feature8=float(f[8]),feature14=float(f[14]),memory_preserved=True)
  return after
