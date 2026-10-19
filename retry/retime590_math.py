"""Frozen549 primary retiming, node-index backup, crossing and lineage helpers."""
import math
import numpy as np
from retry.envelope500 import MASS,REAR
from retry.smoother588_math import endpoint

class Lineage:
    def __init__(self,linear,history):self.rows={id(linear):(linear,list(history))};self.seed=linear
    def history(self,linear):
        obj,h=self.rows[id(linear)]
        if obj is not linear:raise RuntimeError('HISTORY_OBJECT_ALIAS')
        return h.copy()
    def successor(self,linear,history):self.rows[id(linear)]=(linear,list(history))

def plan_for_raw(raw,old,new):return old if raw<=96 else new

def backup_profile(path,primary,oldbackup,count=lambda *a:None):
    n=len(path['points'])
    if len(oldbackup['periodic_squared'])!=n or len(oldbackup['launch_squared'])!=n+1:raise ValueError('BACKUP_NODE_ASSOCIATION')
    periodic=[];launch=[]
    for i in range(n):
        count('profile_bound_evaluations',1);count('backup_node_minimum_evaluations',1);periodic.append(min(primary['periodic_squared'][i],6400.,oldbackup['periodic_squared'][i]))
    for i in range(n+1):
        count('profile_bound_evaluations',1);count('backup_node_minimum_evaluations',1);launch.append(min(primary['launch_squared'][i],6400.,oldbackup['launch_squared'][i]))
    return dict(path,periodic_squared=periodic,launch_squared=launch)

def retime(path,static,count,guard):
    p=static['root']['planar'];mass=p['linear']['mass'];a=p['angle'];f=(-math.sin(a),math.cos(a));front=sum(sum(f[j]*r[j] for j in range(2)) for r in p['levers'][:2])/2;rear=-sum(sum(f[j]*r[j] for j in range(2)) for r in p['levers'][2:])/2
    if min(front,rear)<=0:raise ValueError('AXLE_GEOMETRY')
    coeff=[mass*rear/(front+rear)/2]*2+[mass*front/(front+rear)/2]*2;mu=[w['friction'] for w in p['linear']['wheels']]
    if mu!=[400.]*4:raise ValueError('FROZEN_MATERIAL_DOMAIN')
    limit=[.999*z for z in mu];n=len(path['ds']);K=np.abs(path['curvature']);segment=[max(K[i],K[(i+1)%n]) for i in range(n)];cap=[]
    def charge():guard();count('profile_bound_evaluations',1)
    for i in range(n):
        charge();support=max(segment[i-1],segment[i]);cap.append(min(8100.,min(limit[j]/(coeff[j]*max(support,1e-12)) for j in range(4))))
    def acc(q,k,braking):
        charge();lat=[c*q*k for c in coeff];available=[math.sqrt(max(0.,lim**2-z**2)) for lim,z in zip(limit,lat)]
        if braking:return min(80.,min(4*z/mass for z in available))
        return min(REAR,80000./(MASS*(math.sqrt(max(q,0.))+2.7)),min(2*z/mass for z in available[2:]))
    def restrict(current,other,k,ds,braking):
        if current<=other:return current
        if current-other<=2*acc(current,k,braking)*ds:return current
        lo=other;hi=current
        for _ in range(40):
            count('profile_bisection_updates',1);mid=(lo+hi)/2
            if mid-other<=2*acc(mid,k,braking)*ds:lo=mid
            else:hi=mid
        return lo
    q=cap.copy()
    for it in range(2*n):
        guard();before=q.copy()
        for i in range(n-1,-1,-1):q[i]=restrict(q[i],q[(i+1)%n],segment[i],path['ds'][i],True)
        for i in range(n):j=(i+1)%n;q[j]=restrict(q[j],q[i],segment[i],path['ds'][i],False)
        count('profile_periodic_passes',1)
        if q==before:break
    else:raise ValueError('FINITE_PROFILE_PASSES_EXHAUSTED')
    launch=[0.]
    for i,ds in enumerate(path['ds']):launch.append(restrict(q[(i+1)%n],launch[-1],segment[i],ds,False))
    peak=0.
    for values in [q+[q[0]],launch]:
        for i,ds in enumerate(path['ds']):
            charge();qmax=max(values[i:i+2]);a=(values[i+1]-values[i])/(2*ds);lat=[c*qmax*segment[i] for c in coeff];long=([0.,0.]+[mass*max(a,0)/2]*2) if a>=0 else [mass*abs(a)/4]*4;peak=max(peak,max(math.hypot(x,y)/z for x,y,z in zip(lat,long,mu)))
    if peak>.9990000001:raise ValueError('PROFILE_NOMINAL_FORCE_BOUND')
    return dict(path,periodic_squared=q,launch_squared=launch,periodic_pass_rounds=it+1),dict(nominal_peak_wheel_force_ratio=peak,body_mass_kg=mass,longitudinal_effective_mass_kg=MASS,axle_coefficients=coeff,cap90=True,old_observed_curvature_used=False)

class Gates:
    def __init__(self,planes):self.planes=planes;self.hits={}
    def add(self,row):
        if 'root_without_roads' not in row:return
        for plane in self.planes:
            key=str(plane['station_m'])
            if key in self.hits:continue
            normal=np.asarray(plane['normal']);center=np.asarray(plane['center']);a=float((np.asarray(row['before_root_without_roads']['center'])-center)@normal);b=float((np.asarray(row['root_without_roads']['center'])-center)@normal)
            if not a<0<=b:continue
            f=-a/(b-a);v0=np.asarray(row['before_root_without_roads']['planar']['linear']['velocity']);v1=np.asarray(row['root_without_roads']['planar']['linear']['velocity']);w0=row['before_root_without_roads']['planar']['yaw'];w1=row['root_without_roads']['planar']['yaw'];s=row.get('old_progress',row['progress']);err=row.get('old_path_error',row['path_error'])
            self.hits[key]=dict(before_raw=row['global_raw_before'],after_raw=row['global_raw_after'],fraction=f,time_s=row['episode_before_s']+f*.02,COM_speed_m_s=float(np.linalg.norm(v0+f*(v1-v0))),yaw_rad_s=w0+f*(w1-w0),hold=row['index'],eligible=abs(s-plane['station_m'])<=10 and err<=3,whole_hold_safe=False)
            if 'forces' in row:
                self.hits[key].update(force_peak=max(z['ratio'] for z in row['forces']),tracking_clip_history=row['proposed_history'],margin_m=row.get('margin'),new_progress=row['progress'],old_progress=s,new_path_error=row['path_error'],old_path_error=err,new_reference_excess=row.get('reference_overspeed'),old_reference_excess=row.get('old_reference_overspeed',row.get('reference_overspeed')),body_speed=row.get('body'))
    def finish_hold(self,rows):
        if len(rows)!=4 or any(r.get('pre_failure') or r.get('post_failure') for r in rows):return
        for h in self.hits.values():
            if h['hold']==rows[0]['index']:h['whole_hold_safe']=True
    def passed(self,key):return key in self.hits and self.hits[key]['eligible'] and self.hits[key]['whole_hold_safe']

def planes(old):
    return [dict(station_m=s,center=endpoint(old,float(s))[0].tolist(),normal=endpoint(old,float(s))[1].tolist()) for s in [200,300,400]]
