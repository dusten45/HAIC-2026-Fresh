"""Legal whole-path preview steering: fixed2GaussNewton updates, no GT control."""
import numpy as np
L=3.24;DT=.02;HMAX=8

def rollout(U,v,previous):
 x=y=heading=0.;delta=float(previous);positions=[]
 for u in U:
  for _ in range(4):
   delta+=float(np.clip(50*(float(u)-delta),-3,3))*DT
   heading+=v*np.tan(delta)/L*DT
   x+=v*np.sin(heading)*DT;y+=v*np.cos(heading)*DT
  positions.append([x,y])
 return np.array(positions)
def control(base,features,path):
 action=np.array(base,np.float32);f=np.array(features,float);P=np.array(path,float).reshape(-1,2);v=float(f[4]);previous=float(f[7]);audit=dict(applied=False,kinematic_rollouts=0,kinematic_substeps=0)
 if f[0]!=0 or f[2]<=0 or v<=0 or len(P)<2 or not np.isfinite(P).all() or not np.isfinite(f).all():return action,audit
 lengths=np.linalg.norm(np.diff(P,axis=0),axis=1);arc=np.r_[0,np.cumsum(lengths)];H=min(HMAX,int(arc[-1]/(v*.08)))
 if H<2:return action,audit
 # Only observedpath, no extrapolated unseen tail or world/road labels.
 s=(np.arange(H)+1)*v*.08;target=np.column_stack([np.interp(s,arc,P[:,k]) for k in range(2)]);U=np.full(H,float(base[0]));D=np.eye(H)
 for i in range(1,H):D[i,i-1]=-1
 prior=np.zeros(H);prior[0]=previous;rollouts=0;eps=1e-4
 def cost(u,pos):return float(np.sum((pos-target)**2)+L*L*np.sum((D@u-prior)**2))
 initial=rollout(U,v,previous);rollouts+=1;initialcost=cost(U,initial)
 for _ in range(2):
  pred=rollout(U,v,previous);rollouts+=1;J=np.empty((2*H,H))
  for j in range(H):
   pert=U.copy();pert[j]+=eps;J[:,j]=((rollout(pert,v,previous)-pred)/eps).ravel();rollouts+=1
  normal=J.T@J+L*L*(D.T@D)+1e-6*np.eye(H);rhs=-J.T@(pred-target).ravel()-L*L*D.T@(D@U-prior);U=np.clip(U+np.linalg.solve(normal,rhs),-.4,.4)
 final=rollout(U,v,previous);rollouts+=1;finalcost=cost(U,final)
 # Fixed baselineconstant sequence remains incumbent if the2updates fail to
 # improve the same physical objective; this is not outcome-based tuning.
 accepted=np.isfinite(U).all() and finalcost<initialcost
 if accepted:action[0]=np.float32(U[0])
 audit=dict(applied=True,accepted=bool(accepted),H=int(H),HUD_speed=v,previous_steer=previous,path_length_m=float(arc[-1]),initial_objective=initialcost,final_objective=finalcost,steering_changed=bool(action[0]!=base[0]),kinematic_rollouts=int(rollouts),kinematic_substeps=int(rollouts*H*4))
 return action,audit
