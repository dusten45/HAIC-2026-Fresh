"""Endpointarc repair of288; connectedbranch coordinate decreases onreverse."""
import numpy as np
from retry.preview286_control import rollout,L,HMAX
CURRENT_CORRIDOR=None

def project_progress(positions,P,arc):
 # Retain a connected local branch, not a globalnearest parallel segment.
 # Signed endpoint coordinate may decrease; never accumulate/max arc progress.
 valid=np.flatnonzero(np.diff(arc)>0)
 if not len(valid):return 0.
 branch=0;s=0.
 def projection(k,point):
  i=int(valid[k]);a,b=P[i],P[i+1];length=float(arc[i+1]-arc[i]);t=float(np.clip(np.dot(point-a,b-a)/(length*length),0,1));foot=a+t*(b-a)
  return float(np.sum((point-foot)**2)),float(arc[i]+t*length)
 for point in positions:
  while True:
   current=projection(branch,point);best=(current[0],branch,current[1])
   for neighbor in [branch-1,branch+1]:
    if 0<=neighbor<len(valid):
     value=projection(neighbor,point)
     # Equal distances retain currentbranch rather than jump across a fold.
     if value[0]<best[0]:best=(value[0],neighbor,value[1])
   if best[1]==branch:s=current[1];break
   branch=best[1]
 return float(s)
def inside(positions,mask):
 # Constraints at sameH action-boundary states as287; betweenstate containment
 # and true road/footprint safety are not proven by pixel segmentation.
 for x,y in positions:
  col=int(round(42+float(x)*1.3608));row=int(round(63-float(y)*1.701))
  if not 0<=row<84 or not 0<=col<84 or not mask[row,col]:return False
 return True
def control(base,features,path):
 action=np.array(base,np.float32);f=np.array(features,float);P=np.array(path,float).reshape(-1,2);v=float(f[4]);previous=float(f[7]);audit=dict(applied=False,kinematic_rollouts=0,kinematic_substeps=0)
 if f[0]!=0 or f[2]<=0 or v<=0 or len(P)<2 or not np.isfinite(P).all() or not np.isfinite(f).all() or CURRENT_CORRIDOR is None:return action,audit
 lengths=np.linalg.norm(np.diff(P,axis=0),axis=1);arc=np.r_[0,np.cumsum(lengths)];H=min(HMAX,int(arc[-1]/(v*.08)))
 if H<2:return action,audit
 s=(np.arange(H)+1)*v*.08;target=np.column_stack([np.interp(s,arc,P[:,k]) for k in range(2)]);U=np.full(H,float(base[0]));D=np.eye(H)
 for i in range(1,H):D[i,i-1]=-1
 prior=np.zeros(H);prior[0]=previous;rollouts=0;eps=1e-4
 def tracking(u,pos):return float(np.sum((pos-target)**2)+L*L*np.sum((D@u-prior)**2))
 initial=rollout(U,v,previous);rollouts+=1;initial_U=U.copy();initialprogress=project_progress(initial,P,arc)
 for _ in range(2):
  pred=rollout(U,v,previous);rollouts+=1;progress=project_progress(pred,P,arc);J=np.empty(H)
  for j in range(H):
   pert=U.copy();pert[j]+=eps;J[j]=(project_progress(rollout(pert,v,previous),P,arc)-progress)/eps;rollouts+=1
  # SamefiniteJacobian/2GN/boxprocedure, changedscalar residual is remainingarc.
  # 287tracking/rate weight has no role in the primarypurpose update.
  normal=np.outer(J,J)+1e-6*np.eye(H);rhs=J*(float(arc[-1])-progress);U=np.clip(U+np.linalg.solve(normal,rhs),-.4,.4)
 final=rollout(U,v,previous);rollouts+=1;finalprogress=project_progress(final,P,arc);initialfeasible=inside(initial,CURRENT_CORRIDOR);finalfeasible=inside(final,CURRENT_CORRIDOR);tied=initialfeasible and finalfeasible and finalprogress==initialprogress
 accepted=finalfeasible and (not initialfeasible or finalprogress>initialprogress or (tied and tracking(U,final)<tracking(initial_U,initial)))
 if accepted:action[0]=np.float32(U[0])
 audit=dict(applied=True,accepted=bool(accepted),H=int(H),HUD_speed=v,previous_steer=previous,path_length_m=float(arc[-1]),initial_progress_m=initialprogress,final_progress_m=finalprogress,initial_corridor_feasible=bool(initialfeasible),final_corridor_feasible=bool(finalfeasible),tracking_tie_break_used=bool(tied),no_feasible_candidate=bool(not initialfeasible and not finalfeasible),steering_changed=bool(action[0]!=base[0]),initial_positions=initial.tolist(),final_positions=final.tolist(),initial_U=initial_U.tolist(),final_U=U.tolist(),kinematic_rollouts=int(rollouts),kinematic_substeps=int(rollouts*H*4))
 return action,audit
