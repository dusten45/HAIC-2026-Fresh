"""Single bounded full-station SLSQP run; geometry before any dynamics."""
import datetime,hashlib,json,math,signal,time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from retry.line530_control import rebuild,path_for,scalar_clock
from retry.brake506_geometry import point_segment
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response530-private')
HALF_WIDTH=1.58
FRONT=2.681
BACK=2.320
HALF_LENGTH=(FRONT+BACK)/2
SHIFT=(FRONT-BACK)/2


def frames(points):
    p=np.asarray(points);v=np.roll(p,-1,axis=0)-np.roll(p,1,axis=0);v/=np.linalg.norm(v,axis=1)[:,None]
    return v,np.c_[-v[:,1],v[:,0]]


def constraints(points,center,normal,obstacles,width):
    p=np.asarray(points);t,_=frames(p);pv=np.roll(p,-1,axis=0)-p;ds=np.linalg.norm(pv,axis=1);u=np.roll(pv,1,axis=0);k=np.arctan2(u[:,0]*pv[:,1]-u[:,1]*pv[:,0],(u*pv).sum(axis=1))/((ds+np.roll(ds,1))/2)
    # Endpoint central tangent plus each actual polygon segment midpoint tangent.
    pp=np.concatenate([p,(p+np.roll(p,-1,axis=0))/2]);tt=np.concatenate([t,pv/ds[:,None]]);nn=np.c_[-tt[:,1],tt[:,0]];cc=np.concatenate([center,(center+np.roll(center,-1,axis=0))/2]);rn=np.concatenate([normal,normal+np.roll(normal,-1,axis=0)]);rn/=np.linalg.norm(rn,axis=1)[:,None]
    box=pp+SHIFT*tt;support=HALF_LENGTH*abs((tt*rn).sum(axis=1))+HALF_WIDTH*abs((nn*rn).sum(axis=1));road=width-1.25-support-abs(((box-cc)*rn).sum(axis=1));parts=[road,ds-2.,math.tan(.4)/3.24-abs(k)]
    for obstacle,radius in obstacles:
        delta=np.array(obstacle)-box;xy=np.c_[abs((delta*tt).sum(axis=1))-HALF_LENGTH,abs((delta*nn).sum(axis=1))-HALF_WIDTH];distance=np.linalg.norm(np.maximum(xy,0),axis=1)+np.minimum(np.max(xy,axis=1),0);parts.append(distance-radius-1.25)
    return np.concatenate(parts)


def exact_screen(points,static):
    """Dense conservative outer rectangle vs exact stored road union/boundary."""
    boundary=np.asarray(static['boundary']);ea=boundary[:,0];eb=boundary[:,1];ev=eb-ea;ev2=(ev*ev).sum(axis=1);roads=np.asarray([x[0] for x in static['roads']]);rnext=np.roll(roads,-1,axis=1);re=rnext-roads
    minimum=float('inf');samples=0;outside=0
    def segment_distance(x,a,b):
        v=b-a;d=(v*v).sum(axis=-1);u=np.clip(((x-a)*v).sum(axis=-1)/np.maximum(d,1e-20),0,1);return np.linalg.norm(x-a-u[...,None]*v,axis=-1)
    for i,p in enumerate(np.asarray(points)):
        q=np.asarray(points)[(i+1)%len(points)];delta=q-p;length=np.linalg.norm(delta);t=delta/length;n=np.array([-t[1],t[0]])
        for f in np.arange(math.ceil(length/.5)+1)/math.ceil(length/.5):
            pos=p+f*delta+SHIFT*t;poly=np.array([pos+a*HALF_LENGTH*t+b*HALF_WIDTH*n for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]]);pn=np.roll(poly,-1,axis=0);samples+=1
            # Convex road quads: vertex coverage in stored union.
            dv=poly[:,None,None,:]-roads[None,:,:,:];cross=re[None,:,:,0]*dv[:,:,:,1]-re[None,:,:,1]*dv[:,:,:,0];covered=np.any(np.all(cross>=-1e-8,axis=2)|np.all(cross<=1e-8,axis=2),axis=1)
            # Segment/rectangle SAT rejects any boundary intersection, including containment.
            center_delta=ea-pos;end_delta=eb-pos;ax=np.c_[center_delta@t,center_delta@n];bx=np.c_[end_delta@t,end_delta@n];d=bx-ax;lo=np.zeros(len(ea));hi=np.ones(len(ea));valid=np.ones(len(ea),bool)
            for dim,half in enumerate((HALF_LENGTH,HALF_WIDTH)):
                parallel=abs(d[:,dim])<1e-14;valid &= ~parallel | (abs(ax[:,dim])<=half)
                den=np.where(parallel,1.,d[:,dim]);z1=(-half-ax[:,dim])/den;z2=(half-ax[:,dim])/den;lo=np.maximum(lo,np.where(parallel,-np.inf,np.minimum(z1,z2)));hi=np.minimum(hi,np.where(parallel,np.inf,np.maximum(z1,z2)))
            intersect=np.any(valid & (lo<=hi));dist=min(float(segment_distance(poly[:,None,:],ea[None,:,:],eb[None,:,:]).min()),float(segment_distance(ea[None,:,:],poly[:,None,:],pn[:,None,:]).min()),float(segment_distance(eb[None,:,:],poly[:,None,:],pn[:,None,:]).min()))
            gap=0. if intersect else dist
            if not np.all(covered):gap=-dist;outside+=1
            for oc,rad in static['obstacles']:
                dlt=np.array(oc)-pos;xy=np.array([abs(dlt@t)-HALF_LENGTH,abs(dlt@n)-HALF_WIDTH]);gap=min(gap,float(np.linalg.norm(np.maximum(xy,0))+min(max(xy),0)-rad))
            minimum=min(minimum,gap)
    return dict(samples=samples,spacing_at_most_m=.5,minimum_outer_rectangle_margin_m=minimum,outside_samples=outside,pass_geometry=minimum>=.75 and outside==0)


def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/line530_contract.json').read_text());assert not (D/'DESIGN_STARTED.json').exists()
    def guard():
        if time.process_time()-cpu>180 or time.perf_counter()-wall>240:raise RuntimeError('DESIGN_COST')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
    for filename,h in c['source_sha256'].items():assert hashlib.sha256((G/filename).read_bytes()).hexdigest()==h
    for filename,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(filename).read_bytes()).hexdigest()==h
    (D/'DESIGN_STARTED.json').write_text(json.dumps(dict(contract_sha256=hashlib.sha256((G/'retry/line530_contract.json').read_bytes()).hexdigest())))
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,180);signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,240)
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());baseline=path_for(static,'baseline');center=np.array([(x[2],x[3]) for x in static['track']]);t,normal=frames(center);initial=np.sum((np.array(baseline['points'])-center)*normal,axis=1);n=len(center);width=min(min(point_segment(x,*e) for e in static['boundary']) for x in center);calls=[0];ccalls=[0];iterations=[]
    # Preserve exact launch and seam20m on each side; no second start.
    arcs=np.r_[0,np.cumsum(np.linalg.norm(np.roll(center,-1,axis=0)-center,axis=1))];frozen=(arcs[:-1]<20)|(arcs[-1]-arcs[:-1]<20);limits=[(float(z),float(z)) if lock else (-4.,4.) for z,lock in zip(initial,frozen)];free=np.where(~frozen)[0];fixed=initial.copy()
    def points(x):
        offset=fixed.copy();offset[free]=x;return center+offset[:,None]*normal
    def objective(x):
        guard();calls[0]+=1
        if calls[0]>40000:raise RuntimeError('OBJECTIVE_CAP')
        return scalar_clock(rebuild(points(x),static))
    def feasible(x):
        guard();ccalls[0]+=1
        if ccalls[0]>41000:raise RuntimeError('CONSTRAINT_CAP')
        return constraints(points(x),center,normal,static['obstacles'],width)
    x0=np.clip(initial[free],-4.,4.);initial_clock=scalar_clock(baseline)
    result=minimize(objective,x0,method='SLSQP',bounds=[(-4.,4.)]*len(free),constraints={'type':'ineq','fun':feasible},callback=lambda x:iterations.append(dict(iteration=len(iterations)+1,scalar_clock=scalar_clock(rebuild(points(x),static)))),options=dict(maxiter=120,ftol=1e-7,eps=1e-5,disp=False))
    candidate=rebuild(points(result.x),static);backup=rebuild(points(result.x),static,True);violation=max(0.,-float(feasible(result.x).min()));screen=exact_screen(candidate['points'],static);clock=scalar_clock(candidate);gain=initial_clock-clock;passed=bool(result.success and violation<=1e-6 and screen['pass_geometry'] and gain>=.50)
    data=dict(baseline=baseline,baseline_backup=path_for(static,'baseline_backup'),candidate=candidate,backup=backup)
    with (D/'frozen-paths-private.json').open('x') as f:json.dump(data,f)
    with (D/'offsets-private.json').open('x') as f:json.dump(dict(offsets=(np.sum((np.array(candidate['points'])-center)*normal,axis=1)).tolist(),iterations=iterations),f)
    out=dict(method='single_full_station_SLSQP_scalar_clock',optimizer_success=bool(result.success),optimizer_message=str(result.message),iterations=int(result.nit),objective_calls=calls[0],constraint_calls=ccalls[0],station_count=n,free_variables=len(free),fixed_launch_seam_nodes=int(frozen.sum()),initial_scalar_clock_s=initial_clock,candidate_scalar_clock_s=clock,scalar_screen_gain_s=gain,initial_length_m=baseline['length'],candidate_length_m=candidate['length'],initial_curvature_squared_integral=float(sum(np.array(baseline['curvature'])**2*np.array(baseline['ds']))),candidate_curvature_squared_integral=float(sum(np.array(candidate['curvature'])**2*np.array(candidate['ds']))),max_abs_curvature=max(map(abs,candidate['curvature'])),minimum_constraint= -violation,geometry=screen,pass_design_gate=passed,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,model_ticks=0,force_evaluations=0,native_actions=0,native_resets=0,frozen_paths_sha256=hashlib.sha256((D/'frozen-paths-private.json').read_bytes()).hexdigest(),scope='Scalar clock is only a candidate screen, no feasible bound/actual gain/global optimum claim. Same528 speed/control laws, only path points and resulting geometry/profiles differ.')
    with (G/'retry/line530_design.json').open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps(out,indent=2));guard()

if __name__=='__main__':run()
