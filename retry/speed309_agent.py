"""Only speed-error-conditioned multipliers after exact296 final pedals."""
import numpy as np
from retry.speed309_base import Agent as FrozenAgent
from retry.speed309_model import THETA
class Agent(FrozenAgent):
 def correct_pedals(self,features,nominal):
  self.speed_features=list(features)
  return super().correct_pedals(features,nominal)
 def act(self,observation):
  before=np.asarray(super().act(observation),np.float32);memory=float(self.controller.previous_steer);f=self.speed_features;v=float(f[4]);q=float(f[6]);active=bool(not f[0] and np.isfinite([v,q]).all() and v>=0 and q>=0);after=before.copy();e=None;w=None;scale=np.ones(2)
  if active:
   e=float(np.clip((v-q)/6.,-1.,1.));w=np.array([max(-e,0.),1.-abs(e),max(e,0.)]);scale=np.exp(np.asarray(THETA).reshape(2,3)@w)
   if np.any(THETA):after[1:]=np.clip(before[1:].astype(float)*scale,0,1).astype(np.float32)
  assert after[0]==before[0] and memory==float(self.controller.previous_steer)
  self.speed_audit=dict(active=active,before=before.tolist(),after=after.tolist(),e=e,weights=w.tolist() if w is not None else None,multipliers=scale.tolist(),memory_preserved=True)
  return after
