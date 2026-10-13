"""Small privileged whole-lap spline line and source-grounded speed envelope.

Approximate point-mass/rolling-wheel model, not exactBox2D. No H12 macros.
"""
import json,time
from pathlib import Path
import numpy as np


def geometry(snapshot):
    roads=sorted(snapshot['roads'],key=lambda r:r['idx']);quads=[np.asarray(r['fixture']['geometry']['vertices']) for r in roads];center=[]
    for i,q in enumerate(quads):
        edges=np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1);ends=[(q[j]+q[(j+1)%4])/2 for j in np.argsort(edges)[-2:]];nxt=quads[(i+1)%len(quads)].mean(0);center.append(min(ends,key=lambda x:np.linalg.norm(x-nxt)))
    c=np.asarray(center);t=np.roll(c,-1,axis=0)-np.roll(c,1,axis=0);t/=np.linalg.norm(t,axis=1)[:,None];normal=np.c_[t[:,1],-t[:,0]];obs=np.asarray([o['body']['position'] for o in snapshot['obstacles']]);radii=np.asarray([o['fixture']['radius'] for o in snapshot['obstacles']]);return c,normal,obs,radii


def curvature(path):
    a=path-np.roll(path,1,axis=0);b=np.roll(path,-1,axis=0)-path;c=a+b;cross=a[:,0]*b[:,1]-a[:,1]*b[:,0];return 2*cross/np.maximum(np.linalg.norm(a,axis=1)*np.linalg.norm(b,axis=1)*np.linalg.norm(c,axis=1),1e-9)


def basis(center,K=16):
    ds=np.linalg.norm(np.roll(center,-1,axis=0)-center,axis=1);s=np.r_[0,np.cumsum(ds[:-1])];L=ds.sum();u=s/L*K;B=np.zeros((len(center),K))
    for j in range(K):
        distance=np.abs((u-j+K/2)%K-K/2);B[:,j]=np.where(distance<1,(4-6*distance**2+3*distance**3)/6,np.where(distance<2,(2-distance)**3/6,0))
    # Finishline crossing/initialcenter position fixed, smooth10m taper.
    d=np.minimum(s,L-s);taper=np.minimum(d/10,1);taper=taper*taper*(3-2*taper);return B*taper[:,None],s,L


def obstacle_clearance(path,obstacles,radii):
    a=path[:,None,:];b=np.roll(path,-1,axis=0)[:,None,:];v=b-a;t=np.clip(np.sum((obstacles[None]-a)*v,axis=2)/np.maximum(np.sum(v*v,axis=2),1e-9),0,1);near=a+t[:,:,None]*v;return np.min(np.linalg.norm(near-obstacles[None],axis=2),axis=0)-(radii+2.9+.25)


def profile(path,model,blocked=None):
    ds=np.linalg.norm(np.roll(path,-1,axis=0)-path,axis=1);k=curvature(path);lat=model['lateral_accel'];vlim=np.minimum(100.,np.sqrt(lat/np.maximum(abs(k),1e-6)));v=np.r_[vlim,vlim[0]];v[0]=0.
    if blocked is not None:
        stop=max(1,int(blocked)-2);v[stop:]=0.
    # Standingstart, unrestrictedfinishspeed; four fixedbidirectional passes.
    for _ in range(4):
        for i in range(len(path)-1,-1,-1):v[i]=min(v[i],np.sqrt(v[i+1]**2+2*model['brake_accel']*ds[i]))
        for i in range(len(path)):
            acceleration=min(model['rear_traction_accel'],80000/(v[i]+2.7)/model['effective_mass']);v[i+1]=min(v[i+1],np.sqrt(v[i]**2+2*acceleration*ds[i]))
    times=2*ds/np.maximum(v[:-1]+v[1:],1e-8);T=float(times.sum()) if blocked is None else None
    return dict(speed=v,curvature=k,ds=ds,estimated_time_s=T,max_abs_curvature=float(np.max(abs(k))))


def solve(snapshot,model):
    start=time.perf_counter();center,normal,obs,radii=geometry(snapshot);B,s,L=basis(center);bound=40/6-1.4-.35;calls=0
    # Deterministic one-homotopy obstacle-away initialization, no side search.
    desired=np.zeros(len(center));weights=np.ones(len(center))*.01
    for o,r in zip(obs,radii):
        i=int(np.argmin(np.linalg.norm(center-o,axis=1)));l=float((o-center[i])@normal[i]);side=-1 if l>=0 else 1;desired[i]=side*min(bound,r+2.9+.45-abs(l));weights[i]=50
    coeff=np.linalg.solve(B.T@(weights[:,None]*B)+.02*np.eye(16),B.T@(weights*desired));coeff=np.clip(coeff,-bound,bound)
    def evaluate(theta):
        nonlocal calls;calls+=1;offset=B@theta;path=center+normal*offset[:,None];clear=obstacle_clearance(path,obs,radii);p=profile(path,model);steer_excess=np.maximum(abs(p['curvature'])-np.tan(.4)/3.24,0);violation=float(np.sum(np.maximum(-clear,0)**2)+np.sum(steer_excess**2)*100+np.sum(np.maximum(abs(offset)-bound,0)**2));score=p['estimated_time_s']+1000*violation+.001*np.sum((np.roll(theta,-1)-theta)**2);return score,path,p,clear,violation
    tick=time.perf_counter();first=evaluate(coeff);first_wall=time.perf_counter()-tick;best=first
    # Fixed6passes x16coords x2directions =193objectivecalls plusfirst/final.
    for step in [2.,2.,1.,1.,.4,.4]:
        for j in range(16):
            chosen=coeff.copy();value=best
            for direction in [-1,1]:
                trial=coeff.copy();trial[j]=np.clip(trial[j]+direction*step,-bound,bound);test=evaluate(trial)
                if test[0]<value[0]:chosen,value=trial,test
            coeff,best=chosen,value
    score,line,free,clear,violation=evaluate(coeff);center_clear=obstacle_clearance(center,obs,radii);segments=np.linalg.norm(center[:,None]-obs[None],axis=2)<(radii[None]+2.9+.25);blocked=int(np.flatnonzero(segments.any(1))[0]) if segments.any() else None;fixed=profile(center,model,blocked);free_valid=bool(clear.min()>=-1e-6 and violation<=1e-8)
    return dict(center=center,line=line,coefficients=coeff,center_profile=fixed,free_profile=free,center_clearance=center_clear,free_clearance=clear,center_blocked=blocked,free_feasible=free_valid,objective=score,violation=violation,model_calls=calls,first_model_wall_s=first_wall,model_wall_s=time.perf_counter()-start,dimension=16,solver_converged=free_valid,solver_scope='Fixedboundedcoordinate search; feasible is not optimality certificate')
