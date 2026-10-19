"""Row-wise float32 certification with an exact, separate zero-step branch."""
import numpy as np
from scipy.optimize import linprog
from retry.path569_design import capsule

TOL=1e-8

def rounding_box(x0,scale,bounds):
    x0=np.asarray(x0,float);scale=np.asarray(scale,float);bounds=np.asarray(bounds,float)
    if x0.ndim!=1 or scale.shape!=x0.shape or bounds.shape!=(len(x0)+1,2):raise ValueError('SHAPE')
    if not all(np.all(np.isfinite(v)) for v in [x0,scale,bounds]) or np.any(scale<=0) or np.any(bounds[:,0]>bounds[:,1]):raise ValueError('DOMAIN')
    if not np.array_equal(x0,x0.astype(np.float32).astype(float)):raise ValueError('SEED_NOT_EXACT_FLOAT32')
    endpoints=x0[:,None]+scale[:,None]*bounds[:-1]
    maximum=np.max(abs(endpoints),axis=1).astype(np.float32)
    if not np.all(np.isfinite(maximum)):raise ValueError('FLOAT32_OVERFLOW')
    # The spacing above |endpoint| also covers a binade crossing and negative ties.
    gap=np.nextafter(maximum,np.float32(np.inf),dtype=np.float32).astype(float)-maximum.astype(float)
    arithmetic=8*np.finfo(float).eps*(abs(x0)+scale*np.max(abs(bounds[:-1]),axis=1))/scale
    q=np.nextafter(.5*gap/scale+arithmetic,np.inf)
    if not np.all(np.isfinite(q)):raise ValueError('FLOAT32_OVERFLOW')
    return q

def check(problem,x):
    x=np.asarray(x,float);x0=problem['x0'];scale=problem['scale'];A=problem['A'];b=problem['b'];bounds=problem['bounds']
    if x.shape!=x0.shape or not np.all(np.isfinite(x)):return dict(pass_all=False,reason='NONFINITE_OR_SHAPE')
    z=(x-x0)/scale;t=float(max(abs(z)));y=np.r_[z,t];res=A@y-b
    bv=max(0.,float(max(bounds[:,0]-y)),float(max(y-bounds[:,1])));pv=0.
    if problem.get('path') is not None:
        p=problem['path'];pred=p['center']+np.einsum('ijk,k->ij',p['J'],z);pv=max(0.,float(max(capsule(pred,p['a'],p['b'])[0]+p['L']*t-3.)))
    lv=max(0.,float(max(res)));gain=-float(problem['objective']@z)
    return dict(pass_all=bool(lv<=TOL and bv<=TOL and pv<=TOL),linear_violation=lv,bound_violation=bv,path_violation=pv,predicted_gain_s=gain,normalized_step=t,worst_row=int(np.argmax(res)),residual=float(max(res)))

def solve(problem,max_solves=8,round_fn=None,solve_fn=None):
    if not 1<=max_solves<=8:raise ValueError('SOLVE_CAP')
    x0=np.asarray(problem['x0'],float);scale=np.asarray(problem['scale'],float);bounds=np.asarray(problem['bounds'],float);A=np.asarray(problem['A'],float);b=np.asarray(problem['b'],float);objective=np.asarray(problem['objective'],float)
    if A.ndim!=2 or A.shape[1]!=len(x0)+1 or b.shape!=(len(A),) or objective.shape!=x0.shape or not all(np.all(np.isfinite(v)) for v in [A,b,objective]):raise ValueError('MODEL_SHAPE_OR_FINITE')
    problem=dict(problem,x0=x0,scale=scale,bounds=bounds,A=A,b=b,objective=objective)
    q=rounding_box(x0,scale,bounds);seed=check(problem,x0)
    if not seed['pass_all']:raise ValueError('ORIGINAL_SEED_INFEASIBLE')
    # The feasible set is {exact seed at z=t=0} UNION the certified candidate tube.
    # No nonzero rounding target is imposed on the exact seed branch.
    inward=bounds.copy();inward[:-1,0]+=q;inward[:-1,1]-=q
    result=dict(seed_exact_feasible=True,seed_fallback_preserved=True,method='row_rounding_tube_union_exact_seed',rounding_radius_max=float(max(q)),LP_solves=0,accepted=False)
    if np.any(inward[:,0]>inward[:,1]):return None,dict(result,stop='EMPTY_CERTIFIED_CANDIDATE_BOX')
    p=problem.get('path');path_radius=None
    if p is not None:
        if np.any(np.asarray(p['L'])<0):raise ValueError('NEGATIVE_PATH_ENVELOPE')
        path_radius=np.linalg.norm(p['J'],axis=1)@q
    solver=solve_fn or linprog;rounder=round_fn or (lambda x:x.astype(np.float32).astype(float))
    for attempt in range(max_solves):
        # t itself is continuous. It bounds the norm of every quantized z in the box.
        # This also tightens ±z_j-t<=0 to ±z_j+q_j<=t, jointly with all other rows.
        margins=abs(A[:,:-1])@q
        mag=np.max(abs(bounds),axis=1);eps=np.finfo(float).eps;gamma=(len(x0)+4)*eps/(1-(len(x0)+4)*eps)
        numerical=gamma*(abs(A)@mag+abs(b))+4*eps
        target=b-margins-numerical
        sol=solver(np.r_[objective,1e-8],A_ub=A,b_ub=target,bounds=inward.tolist(),method='highs',options=dict(primal_feasibility_tolerance=1e-9,dual_feasibility_tolerance=1e-9))
        result['LP_solves']+=1
        if not sol.success:return None,dict(result,stop='CERTIFIED_BRANCH_LP_FAILED',solver_status=int(sol.status))
        z=np.asarray(sol.x[:-1]);t=float(sol.x[-1])
        if not np.all(np.isfinite(sol.x)):return None,dict(result,stop='NONFINITE_SOLVER_OUTPUT')
        if p is not None:
            pred=p['center']+np.einsum('ijk,k->ij',p['J'],z);dist,res,*_=capsule(pred,p['a'],p['b']);bad=np.flatnonzero(dist+p['L']*t+path_radius>3.+1e-9)
            if len(bad):
                additions=[];rhs=[]
                for i in bad:
                    if dist[i]==0:return None,dict(result,stop='PATH_RADIUS_TOO_LARGE')
                    n=res[i]/dist[i];az=n@p['J'][i];additions.append(np.r_[az,p['L'][i]]);support=max(n@p['a'][i],n@p['b'][i]);rhs.append(3.+support-n@p['center'][i]-path_radius[i]+abs(az)@q)
                A=np.vstack([A,additions]);b=np.r_[b,rhs];continue
        unrounded=x0+scale*z;rounded=np.asarray(rounder(unrounded),float)
        if rounded.shape!=x0.shape or not np.array_equal(rounded,rounded.astype(np.float32).astype(float)):return None,dict(result,stop='INVALID_QUANTIZER_OUTPUT')
        actual=(rounded-x0)/scale
        if not np.all(np.isfinite(rounded)) or np.any(abs(actual-z)>q):return None,dict(result,stop='ROUNDING_OUTSIDE_CERTIFICATE')
        verdict=check(problem,rounded)
        result.update(verdict=verdict,maximum_row_rounding_allowance=float(max(margins)),maximum_numerical_allowance=float(max(numerical)),worst_tightened_residual=float(max(A@sol.x-target)))
        if not verdict['pass_all']:return None,dict(result,stop='QUANTIZED_JOINT_CHECK_FAILED')
        if verdict['predicted_gain_s']<1e-6:return None,dict(result,stop='NO_MICROSECOND_CERTIFIED_GAIN')
        return rounded,dict(result,accepted=True,stop='CERTIFIED_QUANTIZED_POINT')
    return None,dict(result,stop='PATH_CUT_LIMIT8')
