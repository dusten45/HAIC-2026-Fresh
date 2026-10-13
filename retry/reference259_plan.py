"""Minimumcenterline displacement reference, same258geometry/solver constraints.

No curvature/time term in objective; curvature is steeringfeasibility only.
"""
import time
import numpy as np
from retry.racing258_plan import geometry,basis,curvature,obstacle_clearance,profile
from retry.racing258_feasibility import project


def solve_reference(snapshot,model):
    start=time.perf_counter();center,normal,obs,radii=geometry(snapshot);B,_,_=basis(center);bound=40/6-1.4-.35;dscenter=np.linalg.norm(np.roll(center,-1,axis=0)-center,axis=1);weights=np.ones(len(center))*.01;desired=np.zeros(len(center));calls=0
    # Identical258 obstacle-away initialization.
    for o,r in zip(obs,radii):
        i=int(np.argmin(np.linalg.norm(center-o,axis=1)));l=float((o-center[i])@normal[i]);side=-1 if l>=0 else 1;desired[i]=side*min(bound,r+2.9+.45-abs(l));weights[i]=50
    theta=np.linalg.solve(B.T@(weights[:,None]*B)+.02*np.eye(16),B.T@(weights*desired));theta=np.clip(theta,-bound,bound)
    def evaluate(t):
        nonlocal calls;calls+=1;offset=B@t;line=center+normal*offset[:,None];clear=obstacle_clearance(line,obs,radii);k=curvature(line);violation=float(np.sum(np.maximum(-clear,0)**2)+100*np.sum(np.maximum(abs(k)-np.tan(.4)/3.24,0)**2)+np.sum(np.maximum(abs(offset)-bound,0)**2));displacement=float(np.sum(offset**2*dscenter)/dscenter.sum());return displacement+1000*violation,line,clear,violation,displacement
    tic=time.perf_counter();best=evaluate(theta);first=time.perf_counter()-tic
    for step in [2.,2.,1.,1.,.4,.4]:
        for i in range(16):
            chosen=theta.copy();value=best
            for sign in [-1,1]:
                trial=theta.copy();trial[i]=np.clip(trial[i]+sign*step,-bound,bound);r=evaluate(trial)
                if r[0]<value[0]:chosen,value=trial,r
            theta,best=chosen,value
    score,line,clear,violation,disp=evaluate(theta);repair=None;feasible=bool(clear.min()>=-1e-6 and violation<=1e-8)
    if not feasible:
        # Same258 boundedgeometric projection; no feasibility tolerance relaxed.
        try:
            fixed=project(snapshot,dict(coefficients=theta.tolist(),model=model));theta=fixed['coefficients'];line=fixed['line'];clear=fixed['clearance'];k=curvature(line);violation=float(100*np.sum(np.maximum(abs(k)-np.tan(.4)/3.24,0)**2));feasible=clear.min()>=0 and violation<=1e-8;repair={k:v for k,v in fixed.items() if k in ['geometry_evaluations','max_coefficient_change']};disp=float(np.sum((B@theta)**2*dscenter)/dscenter.sum())
        except AssertionError:repair=dict(failed=True)
    # Freezegeometry first; speedplanning cannotaffectgeometric objective.
    planprofile=profile(line,model)
    return dict(line=line,center=center,coefficients=theta,reference_profile=planprofile,geometry_feasible=bool(feasible),min_clearance=float(clear.min()),constraint_violation=violation,displacement_mean_square_m2=disp,objective='Arcweightedmean lateraldisplacement squared only; constraints include steeringcurvature',objective_calls=calls,first_objective_wall_s=first,wall_s=time.perf_counter()-start,projection=repair,model=model,solver_status='Fixedbudgetfeasible, nooptimalitycertificate' if feasible else 'Boundedsolver failedfeasibility; doesnotprove actualgeometricinfeasibility')
