"""One fixed longitudinal integral state; legal current features only."""
import numpy as np
class IntegralGas:
 def __init__(self):self.integral=0.
 def control(self,base,features,path=None):
  action=np.asarray(base,np.float32).copy();old=self.integral;missing=bool(features[0]);error=float(features[6])-float(features[4]);trial=old+.08*.08*error
  # Original nominal gas slope .08, one-second integration time; dt=.08.
  # Conditional integration prevents growth outward at executed gas limits.
  blocked=(float(base[1])+trial>1 and error>0) or (float(base[1])+trial<0 and error<0)
  if missing:self.integral=0.
  elif not blocked:self.integral=float(np.clip(trial,-1,1))
  action[1]=np.float32(np.clip(float(base[1])+self.integral,0,1))
  assert action[0]==base[0] and action[2]==base[2]
  return action,dict(applied=not missing,error=error,integral_before=old,integral=self.integral,antiwindup_blocked=blocked,gas_changed=bool(action[1]!=base[1]),accepted=False,steering_changed=False,kinematic_rollouts=0,kinematic_substeps=0)
