"""One bounded16-coefficient path deformation;519 speed/control laws unchanged."""
import math
import numpy as np
from retry.drive519_control import path_for as baseline_path,drive


def rebuild(points,obstacles):
    points=[tuple(map(float,p)) for p in points];n=len(points);ds=[math.dist(points[i],points[(i+1)%n]) for i in range(n)];arcs=[0.]
    for d in ds:
        if d<=1e-8:raise ValueError('DEGENERATE_PATH')
        arcs.append(arcs[-1]+d)
    curvature=[]
    for i,b in enumerate(points):
        a,c=points[(i-1)%n],points[(i+1)%n];u=tuple(b[j]-a[j] for j in range(2));v=tuple(c[j]-b[j] for j in range(2));curvature.append(math.atan2(u[0]*v[1]-u[1]*v[0],sum(x*y for x,y in zip(u,v)))/((ds[i-1]+ds[i])/2))
    q=[min(80.,math.sqrt(100./max(abs(k),1e-8)))**2 for k in curvature]
    for rounds in range(2*n):
        old=q.copy()
        for i in range(n-1,-1,-1):q[i]=min(q[i],q[(i+1)%n]+2*45.*ds[i])
        for i in range(n):j=(i+1)%n;q[j]=min(q[j],q[i]+2*drive(q[i])*ds[i])
        if old==q:break
    else:raise ValueError('PROFILE_NONCONVERGENCE')
    launch=[0.]
    for i,d in enumerate(ds):launch.append(min(q[(i+1)%n],launch[-1]+2*drive(launch[-1])*d))
    return dict(points=points,arcs=arcs,length=arcs[-1],ds=ds,curvature=curvature,periodic_squared=q,launch_squared=launch,periodic_pass_rounds=rounds+1,obstacle_association_count=len(obstacles))


def scalar_clock(path):return sum(2*d/(math.sqrt(path['launch_squared'][i])+math.sqrt(path['launch_squared'][i+1])) for i,d in enumerate(path['ds']))


def obstacle_clearances(points,obstacles):
    a=np.asarray(points);v=np.roll(a,-1,axis=0)-a;result=[]
    for center,radius in obstacles:
        t=np.clip(np.sum((np.asarray(center)-a)*v,axis=1)/np.sum(v*v,axis=1),0,1);result.append(float(np.min(np.linalg.norm(a+t[:,None]*v-center,axis=1))-radius))
    return result


def solve(static):
    baseline=baseline_path(static,'source_drive');center=np.asarray([(p[2],p[3]) for p in static['track']]);t=np.roll(center,-1,axis=0)-np.roll(center,1,axis=0);t/=np.linalg.norm(t,axis=1)[:,None];normal=np.c_[-t[:,1],t[:,0]]
    ds=np.linalg.norm(np.roll(center,-1,axis=0)-center,axis=1);s=np.r_[0,np.cumsum(ds[:-1])];L=float(ds.sum());K=16;u=s/L*K;B=np.zeros((len(center),K))
    for j in range(K):
        d=np.abs((u-j+K/2)%K-K/2);B[:,j]=np.where(d<1,(4-6*d*d+3*d**3)/6,np.where(d<2,(2-d)**3/6,0))
    taper=np.minimum(np.minimum(s,L-s)/10,1);B*= (taper*taper*(3-2*taper))[:,None]
    base=np.asarray(baseline['points']);baseoffset=np.sum((base-center)*normal,axis=1);calls=0;history=[]
    def evaluate(theta):
        nonlocal calls;calls+=1
        extra=B@theta;points=base+normal*extra[:,None];p=rebuild(points,static['obstacles']);clear=obstacle_clearances(points,static['obstacles']);offset=baseoffset+extra
        violation=float(np.sum(np.maximum(np.abs(offset)-4.4,0)**2)+np.sum(np.maximum(2.5-np.asarray(clear),0)**2)+100*np.sum(np.maximum(np.abs(p['curvature'])-math.tan(.4)/3.24,0)**2))
        clock=scalar_clock(p);score=clock+1000*violation+.001*float(np.sum((np.roll(theta,-1)-theta)**2))
        return dict(score=score,clock=clock,path=p,violation=violation,minimum_obstacle_point_clearance=min(clear),max_track_normal_offset=float(max(abs(offset))),max_curvature=max(map(abs,p['curvature'])))
    coeff=np.zeros(16);first=evaluate(coeff);best=first
    for step in (2.,2.,1.,1.,.4,.4):
        for j in range(16):
            chosen=coeff.copy();value=best
            for sign in (-1,1):
                trial=coeff.copy();trial[j]=np.clip(trial[j]+sign*step,-4.4,4.4);test=evaluate(trial)
                if test['score']<value['score']:chosen,value=trial,test
            coeff,best=chosen,value
        history.append(dict(step=step,score=best['score'],clock=best['clock'],violation=best['violation']))
    final=evaluate(coeff);assert calls==194
    # Exact invariant: zero deformation reproduces519 profile, no speed-law change.
    for name in ('points','arcs','ds','curvature','periodic_squared','launch_squared'):
        if np.max(np.abs(np.asarray(first['path'][name])-np.asarray(baseline[name])))>1e-10:raise ValueError('ZERO_PATH_IDENTITY')
    feasible=final['violation']<=1e-12
    return baseline,final['path'],dict(objective_evaluations=calls,coefficient_dimension=16,fixed_coordinate_passes=6,initial_scalar_clock_s=first['clock'],final_scalar_clock_s=final['clock'],scalar_clock_gain_s=first['clock']-final['clock'],geometric_screen_pass=feasible and first['clock']-final['clock']>=.75,geometric_feasible=feasible,violation=final['violation'],max_track_normal_offset_m=final['max_track_normal_offset'],minimum_obstacle_point_clearance_m=final['minimum_obstacle_point_clearance'],max_curvature=final['max_curvature'],initial_path_length_m=baseline['length'],candidate_path_length_m=final['path']['length'],history=history),coeff.tolist()
