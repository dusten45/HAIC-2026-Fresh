"""One 575 correction: propagate provably fixed-zero causal bounds to margins."""
import numpy as np
from scipy.optimize import linprog
from retry.rounding573 import rounding_box,TOL
from retry.path569_design import capsule

def actual_aux(z,groups):return np.asarray([max(abs(z[:end]),default=0.) for end in groups])

def effective_uncertainty(p):
    """Preserve free-variable boxes; only exact fixed-zero dependencies vanish."""
    N=len(p['x0']);effective=p['bounds'].copy();fixed=(effective[:N,0]==0)&(effective[:N,1]==0)
    q=rounding_box(p['x0'],p['scale'],np.vstack([effective[:N],effective[-1:]]));q[fixed]=0.
    for k,end in enumerate(p['groups']):
        if np.all(fixed[:end]):effective[N+k]=[0.,0.]
    inward=effective.copy();inward[:N,0]+=q;inward[:N,1]-=q
    return q,inward,np.max(abs(effective),axis=1)

def numerical_margin(A,b,mag,gamma):
    value=gamma*(abs(A)@mag+abs(b))
    # A stored constant row has no arithmetic on a variable-dependent lhs.
    value[np.all(A[:,mag>0]==0,axis=1)]=0.
    return value

def check(p,x):
    z=(np.asarray(x)-p['x0'])/p['scale'];u=actual_aux(z,p['groups']);y=np.r_[z,u];res=p['A']@y-p['b'];bounds=p['bounds'];bv=max(0.,float(max(bounds[:,0]-y)),float(max(y-bounds[:,1])));path=p['path'];pv=0.
    if path is not None:
        pos=path['center']+np.einsum('ijk,k->ij',path['J'],z);pv=max(0.,float(max(capsule(pos,path['a'],path['b'])[0]+path['L']*u[path['groups']]-3.)))
    lv=max(0.,float(max(res)));clip_ok=all(res[i]<=0 for i in p.get('ratio_rows',[]))
    return dict(pass_all=bool(lv<=TOL and bv<=TOL and pv<=TOL and clip_ok),linear_violation=lv,bound_violation=bv,path_violation=pv,exact_ratio_branch_upper_pass=bool(clip_ok),predicted_gain_s=-float(p['objective']@z),normalized_step=float(max(abs(z))),worst_row=int(np.argmax(res)),maximum_residual=float(max(res)))

def solve(p,max_solves=8,solve_fn=None,round_fn=None):
    if not 1<=max_solves<=8:raise ValueError('CUT_CAP')
    N=len(p['x0']);G=len(p['groups']);A=p['A'].copy();b=p['b'].copy();bounds=p['bounds'];x0=p['x0'];scale=p['scale']
    assert A.shape[1]==N+G and bounds.shape==(N+G,2) and all(np.all(np.isfinite(v)) for v in [A,b,bounds,x0,scale])
    assert p['groups']==list(range(2,N+1,2))
    q,inward,mag=effective_uncertainty(p);fixed=(bounds[:N,0]==0)&(bounds[:N,1]==0)
    seed=check(p,x0)
    if not seed['pass_all']:raise ValueError('EXACT_SEED_INFEASIBLE')
    meta=dict(seed_exact_feasible=True,seed_fallback_preserved=True,LP_solves=0,accepted=False,rounding_radius_max=float(max(q)),fixed_control_count=int(sum(fixed)))
    if np.any(inward[:,0]>inward[:,1]):return None,dict(meta,stop='EMPTY_CERTIFIED_CANDIDATE_BOX')
    path=p['path'];rad=np.linalg.norm(path['J'],axis=1)@q if path is not None else None;solver=solve_fn or linprog;rounder=round_fn or(lambda x:x.astype(np.float32).astype(float));eps=np.finfo(float).eps;gamma=(N+G+4)*eps/(1-(N+G+4)*eps)
    for iteration in range(max_solves):
        if p.get('budget_guard') is not None:p['budget_guard']()
        margins=abs(A[:,:N])@q;numerical=numerical_margin(A,b,mag,gamma);target=b-margins-numerical
        objective=np.r_[p['objective'],np.full(G,1e-8/G)];sol=solver(objective,A_ub=A,b_ub=target,bounds=inward.tolist(),method='highs',options=dict(primal_feasibility_tolerance=1e-9,dual_feasibility_tolerance=1e-9,time_limit=30.));meta['LP_solves']+=1
        if not sol.success:return None,dict(meta,stop='CERTIFIED_BRANCH_LP_FAILED',solver_status=int(sol.status))
        if not np.all(np.isfinite(sol.x)):return None,dict(meta,stop='NONFINITE_SOLVER_OUTPUT')
        z=sol.x[:N];aux=sol.x[N:]
        if path is not None:
            pos=path['center']+np.einsum('ijk,k->ij',path['J'],z);dist,res,*_=capsule(pos,path['a'],path['b']);bad=np.flatnonzero(dist+path['L']*aux[path['groups']]+rad>3.+1e-9)
            if len(bad):
                additions=[];rhs=[]
                for i in bad:
                    if dist[i]==0:return None,dict(meta,stop='PATH_ROUNDING_RADIUS_TOO_LARGE')
                    n=res[i]/dist[i];az=n@path['J'][i];au=np.zeros(G);au[path['groups'][i]]=path['L'][i];additions.append(np.r_[az,au]);support=max(n@path['a'][i],n@path['b'][i]);rhs.append(3.+support-n@path['center'][i]-rad[i]+abs(az)@q)
                A=np.vstack([A,additions]);b=np.r_[b,rhs];continue
        x=np.asarray(rounder(x0+scale*z),float)
        if x.shape!=x0.shape or not np.array_equal(x,x.astype(np.float32).astype(float)):return None,dict(meta,stop='INVALID_QUANTIZER_OUTPUT')
        zz=(x-x0)/scale
        if np.any(abs(zz-z)>q):return None,dict(meta,stop='ROUNDING_OUTSIDE_CERTIFICATE')
        verdict=check(p,x);meta.update(verdict=verdict,maximum_row_rounding_allowance=float(max(margins)),maximum_numerical_allowance=float(max(numerical)),worst_tightened_residual=float(max(A@sol.x-target)))
        if not verdict['pass_all']:return None,dict(meta,stop='QUANTIZED_JOINT_CHECK_FAILED')
        if verdict['predicted_gain_s']<1e-6:return None,dict(meta,stop='NO_MICROSECOND_CERTIFIED_GAIN')
        return x,dict(meta,accepted=True,stop='CERTIFIED_QUANTIZED_POINT')
    return None,dict(meta,stop='PATH_CUT_LIMIT8')
