"""Full-trajectory metrics and causal empirical errors for the 574 control space."""
import math
import numpy as np
from retry.checkpoints574 import START,HORIZON
from retry.clip561_core import prefix_slacks,nonexempt_branch
from retry.geometry571 import vertices
import retry.handoff562_model as d
SCALE=np.tile([.003,.03],132)

def metric(owner,rows):
    roots=[owner.start['root']]+[d.load_root(dict(v['root_without_roads'],roads=owner.static['root']['roads'])) for v in rows];g=[];labels=[];ratios=[];progress=owner.start['progress']
    for i,row in enumerate(rows):
        delta=row['progress']-progress;limit=max(5.,2*math.dist(roots[i].center,roots[i+1].center));progress=row['progress'];g.extend([row['margin']-.5,3-row['path_error'],4.85-row['reference_overspeed'],*[1.059-f['ratio'] for f in row['forces']],100-row['body'],delta+.5,limit-delta]);labels.extend(['footprint','path','reference']+['force']*4+['body','projection','projection']);ratios.extend(f['ratio'] for f in row['forces'])
    c0,n0=owner.start['tracking'];order=prefix_slacks(ratios,c0,n0);times={};tracker=owner.start['tracker']
    for name,point,normal,use_hull in [('hull_finish',tracker.center,tracker.forward,True),('center_finish',tracker.center,tracker.forward,False)]:
        values=[sum((p[j]-point[j])*normal[j] for j in range(2)) for p in [d.hull_pose(root)[0] if use_hull else root.center for root in roots]];hit=None
        for k in range(1,len(roots)):
            if values[k-1]<0<=values[k]:
                fraction=-values[k-1]/(values[k]-values[k-1]);hit=.02*(START+k-1+fraction);break
        times[name]=hit
    previous=[owner.start['progress']]+[r['progress'] for r in rows]
    for station in [300.,600.,900.]:
        hit=None
        for k in range(1,len(previous)):
            if previous[k-1]<station<=previous[k]:hit=.02*(START+k-1+(station-previous[k-1])/(previous[k]-previous[k-1]));break
        times['progress_s'+str(int(station))]=hit
    safe=all(not r.get('pre_failure') and not r.get('post_failure') for r in rows) and min(g)>=0 and min(order)>=0
    return dict(g=np.asarray(g),labels=labels,ratios=np.asarray(ratios),order=order,times=times,P=np.asarray([r.center for r in roots[1:]]),V=np.stack([vertices(root) for root in roots[1:]]),physical_safe=bool(safe),violation_counts={key:sum(key in r.get('all_failures',[]) for r in rows) for key in ['FORCE','CLIP_HISTORY','FOOTPRINT','PATH','REFERENCE','PROJECTION']})

def prefix_radii(dx):return np.maximum.accumulate(np.max(abs(np.asarray(dx).reshape(-1,2)/SCALE.reshape(-1,2)),axis=1))[np.arange(HORIZON)//4]

def empirical(center,linear,observations):
    n=len(center['rows']);ulp=abs(np.spacing(center['x'].astype(np.float32))).astype(float);tiny=4*np.finfo(float).eps/.05;spec=[('g','g','J',1,10),('ratio','ratios','R',-1,4),('order','order','O',1,1)];out={}
    for key,field,jac,sign,repeats in spec:
        J=linear[jac];base=center[field];errors=[]
        for obs in observations:
            dx=obs['x']-center['x'];r=np.repeat(prefix_radii(dx),repeats);difference=sign*(base+J@dx-obs[field]);zero=r==0
            if np.any(difference[zero]!=0):raise RuntimeError('ZERO_CAUSAL_DISPLACEMENT_ERROR:'+key)
            errors.append(np.divide(np.maximum(0,difference),r,out=np.zeros_like(r),where=r>0))
        out[key]=2*(np.max(errors,axis=0)+abs(J)@ulp/.05+tiny)
    errors=[]
    for obs in observations:
        dx=obs['x']-center['x'];r=prefix_radii(dx);error=np.linalg.norm(center['P']+np.einsum('ijk,k->ij',linear['P'],dx)-obs['P'],axis=1)
        if np.any(error[r==0]!=0):raise RuntimeError('ZERO_CAUSAL_POSITION_ERROR')
        errors.append(np.divide(error,r,out=np.zeros_like(r),where=r>0))
    out['position']=2*(np.max(errors,axis=0)+np.linalg.norm(np.einsum('ijk,k->ij',abs(linear['P']),ulp),axis=1)/.05+tiny)
    out['rule']='Fresh actual causal-prefix displacement observed errors;factor2+fullfloat32ULP/.05+fourbinary64eps/.05. Empirical,not universal. No prior tail coefficient.'
    return out

def signed(center,JV,features,vl,observations):
    q=[];J=[];L=[];groups=[];keys=[];ulp=abs(np.spacing(center['x'].astype(np.float32))).astype(float);tiny=4*np.finfo(float).eps/.05
    for f in features:
        i=f['raw'];normal=np.asarray(f['normal']);offset=f['offset']
        for v in vl[f['polygon']]:
            value=float(center['V'][i,v]@normal-offset-.5);jac=normal@JV[i,v];errors=[]
            for obs in observations:
                dx=obs['x']-center['x'];r=prefix_radii(dx)[i];actual=float(obs['V'][i,v]@normal-offset-.5);difference=value+jac@dx-actual
                if r==0 and difference!=0:raise RuntimeError('ZERO_CAUSAL_SUPPORT_ERROR')
                errors.append(max(0.,difference)/r if r>0 else 0.)
            q.append(value);J.append(jac);L.append(2*(max(errors,default=0.)+abs(jac)@ulp/.05+tiny));groups.append(i//4);keys.append(f"{i}:{f['kind']}:{f['polygon']}:{f['feature']}:{v}")
    return np.asarray(q),np.asarray(J),np.asarray(L),np.asarray(groups),keys

def matrix(owner,center,linear,env,features,vl,observations,rho):
    N=len(center['x']);G=N//2;H=len(center['rows']);groups=np.arange(H)//4;labels=np.asarray(center['labels']);keep=labels!='path';J=linear['J']*SCALE;R=linear['R']*SCALE;P=linear['P']*SCALE;T=linear['T']*SCALE
    def aux(coeff,ids):
        z=np.zeros((len(coeff),G));z[np.arange(len(coeff)),ids]=coeff;return z
    c0,n0=owner.start['tracking'];ids=nonexempt_branch(center['ratios'],c0,n0);A=[np.c_[-J[keep],aux(np.asarray(env['g'])[keep],np.repeat(groups,10)[keep])],np.c_[R[ids],aux(np.asarray(env['ratio'])[ids],(ids//4)//4)]];b=[center['g'][keep],1-center['ratios'][ids]];ratio_rows=list(range(sum(keep),sum(keep)+len(ids)))
    q,S,L,sg,keys=signed(center,linear['V'],features,vl,observations);A.append(np.c_[-S*SCALE,aux(L,sg)]);b.append(q);support_begin=sum(keep)+len(ids)
    # All tightening targets remain attainable locally and vanish at zero prefix motion.
    upper=center['g']+rho*np.sum(abs(J),axis=1);universal=np.asarray([1.059 if x=='force' else 100. if x=='body' else 84.85 if x=='reference' else np.inf for x in labels]);cap=np.minimum(upper,universal)
    A.append(np.c_[np.zeros((sum(keep),N)),aux(np.asarray(env['g'])[keep],np.repeat(groups,10)[keep])]);b.append(cap[keep]);A.append(np.c_[np.zeros((H,N)),aux(np.asarray(env['position']),groups)]);b.append(np.full(H,3.));A.append(np.c_[np.zeros((len(ids),N)),aux(np.asarray(env['ratio'])[ids],(ids//4)//4)]);b.append(np.ones(len(ids)))
    known=np.isfinite(universal);A.append(np.c_[J[known],np.zeros((sum(known),G))]);b.append(universal[known]-center['g'][known]);A.append(np.c_[np.zeros((len(q),N)),aux(L,sg)]);b.append(q+rho*np.sum(abs(S*SCALE),axis=1))
    I=np.eye(N);norm_group=np.arange(N)//2
    A.extend([np.c_[I,aux(-np.ones(N),norm_group)],np.c_[-I,aux(-np.ones(N),norm_group)]]);b.extend([np.zeros(N),np.zeros(N)])
    monotone=np.zeros((G-1,N+G))
    for i in range(G-1):monotone[i,N+i]=1.;monotone[i,N+i+1]=-1.
    A.append(monotone);b.append(np.zeros(G-1));bounds=[]
    for j,value in enumerate(center['x']):
        lo,hi=(-float(np.float32(.4)),float(np.float32(.4))) if j%2==0 else (-1.,1.);offset=(value-owner.seed_x[j])/SCALE[j];bounds.append([max(-rho,-.10-offset,(lo-value)/SCALE[j]),min(rho,.10-offset,(hi-value)/SCALE[j])])
    bounds.extend([[0.,rho] for _ in range(G)])
    direction=owner.segB-owner.segA;unit=direction/np.linalg.norm(direction,axis=1)[:,None];normal=np.c_[-unit[:,1],unit[:,0]]
    for vectors in [normal,-normal,unit,-unit]:
        projection=np.einsum('ij,ijk->ik',vectors,P);support=np.maximum(np.sum(vectors*owner.segA,axis=1),np.sum(vectors*owner.segB,axis=1));A.append(np.c_[projection,aux(np.asarray(env['position']),groups)]);b.append(3.+support-np.sum(vectors*center['P'],axis=1))
    problem=dict(A=np.vstack(A),b=np.concatenate(b),bounds=np.asarray(bounds),objective=T,x0=center['x'],scale=SCALE,groups=list(range(2,N+1,2)),ratio_rows=ratio_rows,path=dict(center=center['P'],J=P,L=np.asarray(env['position']),a=owner.segA,b=owner.segB,groups=groups))
    detail=dict(rows=len(problem['b']),columns=N+G,physical_rows=int(sum(keep)),ratio_branch_rows=len(ids),signed_support_rows=len(q),minimum_seed_support_slack=float(min(q)),maximum_signed_coefficient=float(max(L)),support_begin=int(support_begin),support_keys=keys,initial_counts=[c0,n0],O_used='Diagnostic only; direct nonexempt sufficient force branch. Exact source count decides.')
    return problem,detail
