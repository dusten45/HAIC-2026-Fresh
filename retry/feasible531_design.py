"""One feasibility-first continuation, then one fixed smooth-performance stage."""
import datetime,hashlib,json,signal,time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from retry.line530_control import path_for,rebuild,scalar_clock
from retry.line530_design import frames,exact_screen
from retry.feasible531_geometry import Geometry,geometric_constraints,shape,TARGET,KMAX
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response531-private')
EPS=1e-5


def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/feasible531_contract.json').read_text());assert not (D/'DESIGN_STARTED.json').exists()
    for p,h in c['source_sha256'].items():assert hashlib.sha256((G/p).read_bytes()).hexdigest()==h
    for p,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
    assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(c['deadline_utc'])
    (D/'DESIGN_STARTED.json').write_text(json.dumps(dict(contract_sha256=hashlib.sha256((G/'retry/feasible531_contract.json').read_bytes()).hexdigest())))
    stage_clock=[time.process_time(),time.perf_counter()];phase=['feasibility'];cost=dict(geometry_jacobians=0,performance_objective_calls=0,constraint_calls=0);hist=[]
    def guard():
        if time.process_time()-stage_clock[0]>180 or time.perf_counter()-stage_clock[1]>240:raise RuntimeError('STAGE_COST_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('DESIGN_CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,360)
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('DESIGN_WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,480)
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());baseline=path_for(static,'baseline');center=np.array([(p[2],p[3]) for p in static['track']]);normal=frames(center)[1];n=len(center);initial=((np.array(baseline['points'])-center)*normal).sum(axis=1);arcs=np.r_[0,np.cumsum(np.linalg.norm(np.roll(center,-1,axis=0)-center,axis=1))];frozen=(arcs[:-1]<20)|(arcs[-1]-arcs[:-1]<20);free=np.where(~frozen)[0];geo=Geometry(static,center);M=9*n;cache={};jac_cache={}
    def points(x):
        offset=initial.copy();offset[free]=x[:len(free)];return center+offset[:,None]*normal
    def cons(x):
        guard();key=x[:len(free)].tobytes()
        if cache.get('key')!=key:
            cost['constraint_calls']+=1
            if cost['constraint_calls']>40000:raise RuntimeError('CONSTRAINT_CAP')
            cache.update(key=key,points=points(x),value=geometric_constraints(geo,points(x)))
        return cache['value']
    def jac(x):
        guard();key=x[:len(free)].tobytes()
        if jac_cache.get('key')==key:return jac_cache['value']
        cost['geometry_jacobians']+=1
        if cost['geometry_jacobians']>205:raise RuntimeError('JACOBIAN_CAP')
        base=cons(x);p=points(x);J=np.zeros((M,len(free)))
        for col,j in enumerate(free):
            if col%16==0:guard()
            changed=p.copy();changed[j]+=EPS*normal[j];ids=np.array([(j-1)%n,j]);rows=(ids[:,None]*7+np.arange(7)).ravel();J[rows,col]=((geo.evaluate(changed,ids)-TARGET).ravel()-base[rows])/EPS
            ds,k=shape(changed);rows2=7*n+ids;J[rows2,col]=(ds[ids]-2-base[rows2])/EPS
            ki=np.array([(j-1)%n,j,(j+1)%n]);rows3=8*n+ki;J[rows3,col]=((KMAX-abs(k[ki]))*3.24**2-base[rows3])/EPS
        jac_cache.update(key=key,value=J);return J
    def callback(x):
        v=cons(x);hist.append(dict(phase=phase[0],iteration=len([h for h in hist if h['phase']==phase[0]])+1,max_normalized_violation=max(0.,-float(v.min())),slack=float(x[-1]) if phase[0]=='feasibility' else None))
    x0=np.clip(initial[free],-4.,4.);start=cons(x0);slack=max(0.,-float(start.min()))+.001;z=np.r_[x0,slack]
    # Epigraph restoration: minimize only worst normalized violation, not time.
    feasibility=minimize(lambda x:float(x[-1]),z,jac=lambda x:np.r_[np.zeros(len(free)),1.],method='SLSQP',bounds=[(-4.,4.)]*len(free)+[(0.,5.)],constraints={'type':'ineq','fun':lambda x:cons(x)+x[-1],'jac':lambda x:np.c_[jac(x),np.ones(M)]},callback=callback,options=dict(maxiter=80,ftol=1e-8,disp=False))
    feasible_points=points(feasibility.x);restored=cons(feasibility.x);fgap,fdetail=geo.evaluate(feasible_points,details=True);fscreen=exact_screen(feasible_points,static);feas_pass=bool(max(0.,-float(restored.min()))<=1e-6 and fdetail['minimum_outer_rectangle_margin_m']>=1.25 and fdetail['outside_samples']==0 and fdetail['max_sample_spacing_m']<=.5 and fscreen['minimum_outer_rectangle_margin_m']>=1.25 and fscreen['pass_geometry'])
    fcost=dict(CPU_s=time.process_time()-stage_clock[0],wall_s=time.perf_counter()-stage_clock[1]);guard();feas_summary=dict(success=bool(feasibility.success),message=str(feasibility.message),iterations=int(feasibility.nit),initial_slack_m=slack,final_slack=float(feasibility.x[-1]),max_normalized_violation=max(0.,-float(restored.min())),geometry=fdetail,independent530screen=fscreen,pass_feasibility=feas_pass,**fcost)
    candidate_points=feasible_points;performance_summary=None;baseline_clock=candidate_clock=gain=None
    if feas_pass:
        phase[0]='performance';stage_clock[:]=[time.process_time(),time.perf_counter()];budget=.70*sum(w['friction'] for w in static['root']['planar']['linear']['wheels'])/static['root']['planar']['linear']['mass']
        def smooth(x):
            guard();cost['performance_objective_calls']+=1
            if cost['performance_objective_calls']>40000:raise RuntimeError('OBJECTIVE_CAP')
            ds,k=shape(points(x));inverse_speed=np.sqrt(np.sqrt(k*k+1e-8)/budget+1./80.**2);return float(np.sum(ds*(inverse_speed+np.roll(inverse_speed,-1))/2))
        performance=minimize(smooth,feasibility.x[:len(free)],method='SLSQP',bounds=[(-4.,4.)]*len(free),constraints={'type':'ineq','fun':cons,'jac':jac},callback=callback,options=dict(maxiter=120,ftol=1e-7,eps=EPS,disp=False));candidate_points=points(performance.x);pv=cons(performance.x);pgap,pdetail=geo.evaluate(candidate_points,details=True);pscreen=exact_screen(candidate_points,static);baseline_clock=scalar_clock(baseline);candidate_clock=scalar_clock(rebuild(candidate_points,static));gain=baseline_clock-candidate_clock
        performance_summary=dict(success=bool(performance.success),message=str(performance.message),iterations=int(performance.nit),smooth_surrogate=float(performance.fun),max_normalized_violation=max(0.,-float(pv.min())),geometry=pdetail,independent530screen=pscreen,scalar_gain_s=gain,pass_performance=bool(performance.success and max(0.,-float(pv.min()))<=1e-6 and pdetail['minimum_outer_rectangle_margin_m']>=1.25 and pdetail['outside_samples']==0 and pdetail['max_sample_spacing_m']<=.5 and pscreen['pass_geometry'] and pscreen['minimum_outer_rectangle_margin_m']>=1.25 and gain>=.5),CPU_s=time.process_time()-stage_clock[0],wall_s=time.perf_counter()-stage_clock[1]);guard()
    frozen_paths=dict(baseline=baseline,baseline_backup=path_for(static,'baseline_backup'),candidate=rebuild(candidate_points,static),backup=rebuild(candidate_points,static,True));
    for name,data in [('frozen-paths-private.json',frozen_paths),('design-history-private.json',dict(history=hist,restored_points=feasible_points.tolist(),initial_normal_offsets=initial.tolist()))]:
        p=D/name
        with p.open('x') as f:json.dump(data,f)
        p.chmod(0o600)
    details=performance_summary['geometry'] if performance_summary else fdetail;cg=(geo.evaluate(candidate_points)-TARGET).ravel();ds,k=shape(candidate_points)
    out=dict(status='DESIGN_ELIGIBLE' if performance_summary and performance_summary['pass_performance'] else 'DESIGN_NOT_PROMOTED',feasibility=feas_summary,performance=performance_summary,pass_design_gate=bool(performance_summary and performance_summary['pass_performance']),initial_scalar_clock_s=baseline_clock,candidate_scalar_clock_s=candidate_clock,scalar_screen_gain_s=gain,candidate_length_m=float(ds.sum()),candidate_max_abs_curvature=float(max(abs(k))),normalized_final_minimum=float(min(cg.min(),(ds-2).min(),((KMAX-abs(k))*3.24**2).min())),geometry_cost=dict(calls=geo.calls,segment_samples=geo.segment_samples),optimizer_cost=cost,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,model_integrator_ticks=0,force_evaluations=0,native_actions=0,native_resets=0,native_worlds=0,frozen_paths_sha256=hashlib.sha256((D/'frozen-paths-private.json').read_bytes()).hexdigest(),scope='Onefeasibility-firstprocedure. Feasibilitynotperformance;smoothtime-likeobjectiveisnophysicalbound;finalactualscalarprofileonlyscreen. Same528control/top80/back80/backup100back45.')
    # Detailed locations stay private; public records retain residual categories.
    with (D/'constraint-residuals-private.json').open('x') as f:json.dump(dict(geometric=cg.reshape(n,7).tolist(),segment=(ds-2).tolist(),curvature=((KMAX-abs(k))*3.24**2).tolist()),f)
    with (G/'retry/feasible531_design.json').open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
