"""One-frame pixel reference recovery; accepted observed affine only."""
import numpy as np
from retry.reference305_base import Agent as FrozenAgent
from retry import nominal238_base as nominal
from retry import connected_agent as router
from retry.cem294_constants import LOOKAHEAD_SCALE

def recover(image,obstacles,path,transform,speed):
 audit=dict(transform_available=transform is not None,previous_reference_available=bool(path),accepted=False,reason='missing_signal')
 if transform is None or not path:return [],audit
 # The route itself uses (42,63), unlike the hazard detector origin.
 points=np.asarray(path[1:],float).reshape(-1,2)
 pixels=np.c_[42+1.3608*points[:,0],63-1.701*points[:,1],np.ones(len(points))]
 moved=pixels@np.asarray(transform).T
 points=np.c_[(moved[:,0]-42)/1.3608,(63-moved[:,1])/1.701]
 allowed=router.routing_problem(image,obstacles)[0];selected=[];started=False
 for p in points:
  row,col=np.rint([63-1.701*p[1],42+1.3608*p[0]]).astype(int)
  if not started and (p[1]<=0 or row>56):continue
  started=True
  if not(24<=row<=56 and 3<=col<81) or not allowed[row,col]:break
  if selected:
   a=selected[-1];n=max(1,int(np.ceil(max(abs((p-a)*[1.3608,1.701]))*2)))
   q=np.linspace(a,p,n+1);rc=np.rint(np.c_[63-1.701*q[:,1],42+1.3608*q[:,0]]).astype(int)
   if not np.all(allowed[rc[:,0],rc[:,1]]):break
  selected.append(p)
 candidate=[(0.,0.)]+[p.tolist() for p in selected]
 length=sum(float(np.linalg.norm(np.asarray(b)-a)) for a,b in zip(candidate[:-1],candidate[1:]));look=float(np.clip((4+.35*speed)*LOOKAHEAD_SCALE,6*LOOKAHEAD_SCALE,14*LOOKAHEAD_SCALE))
 if len(selected)<2 or length<look:return [],dict(audit,reason='current_mask_or_short_reference',transported_points=len(points),retained_points=len(selected),length_m=length)
 return candidate,dict(audit,accepted=True,reason='one_frame_transported_current_mask_reference',transported_points=len(points),retained_points=len(selected),length_m=length)

class Agent(FrozenAgent):
 def reset(self,observation):
  super().reset(observation);self.previous_fresh_reference=[];self.reference_motion305=None
 def act(self,observation):
  original=nominal.connected_route;previous=self.previous_fresh_reference
  self.reference_audit=dict(accepted=False,reason='fresh_route',transform_available=False,previous_reference_available=bool(previous))
  def route(image,obstacles,*args,**kwargs):
   fresh=original(image,obstacles,*args,**kwargs);self.previous_fresh_reference=[list(p) for p in fresh]
   if fresh:return fresh
   candidate,self.reference_audit=recover(image,obstacles,previous,self.reference_motion305,kwargs.get('speed',0.))
   return candidate
  nominal.connected_route=route
  try:return super().act(observation)
  finally:nominal.connected_route=original
