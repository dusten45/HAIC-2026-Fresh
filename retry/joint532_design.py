"""One sparse trust-constr solve from the sole531 restored endpoint."""
import datetime,hashlib,json,signal,time,traceback
from pathlib import Path
import numpy as np
from scipy.optimize import minimize,NonlinearConstraint,Bounds,BFGS
from retry.joint532_problem import Problem,Q
from retry.line530_control import path_for,rebuild,scalar_clock
from retry.line530_design import exact_screen
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response532-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/joint532_contract.json').read_text());assert not (D/'DESIGN_STARTED.json').exists()
    for p,h in c['source_sha256'].items():assert hashlib.sha256((G/p).read_bytes()).hexdigest()==h
    for p,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
    (D/'DESIGN_STARTED.json').write_text(json.dumps(dict(contract_sha256=hashlib.sha256((G/'retry/joint532_contract.json').read_bytes()).hexdigest())))
    solving=[True]
    def guard():
        if solving[0] and (time.process_time()-cpu>600 or time.perf_counter()-wall>720):raise RuntimeError('SOLVER_BUDGET')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('OVERALL_CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,630)
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('OVERALL_WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,760)
    s=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());history=json.loads(Path('/workspace/haic-response531-private/design-history-private.json').read_text());problem=Problem(s,history['restored_points'],guard);x0=problem.x0;initial_c=problem.constraints(x0);_,initial_geometry=problem.geo.evaluate(problem.points(x0),details=True);assert initial_c.min()>=-1e-6 and initial_geometry['minimum_outer_rectangle_margin_m']>=1.25
    saved=dict(x=x0.copy(),iteration=0);iterations=[];result=None;error=None
    def callback(x,state):
        saved.update(x=x.copy(),iteration=int(state.nit));row=dict(iteration=int(state.nit),design_time_s=float(state.fun*problem.time_scale),constraint_violation=float(state.constr_violation),optimality=float(state.optimality),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall);iterations.append(row)
        with (D/'latest-iterate-private.json').open('w') as f:json.dump(dict(x=x.tolist(),state=row),f)
        with (D/'iteration-cost-private.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
        return False
    try:
        result=minimize(problem.objective,x0,jac=problem.gradient,hess=BFGS(),method='trust-constr',bounds=Bounds(problem.lower,problem.upper),constraints=NonlinearConstraint(problem.constraints,0.,np.inf,jac=problem.jacobian,hess=BFGS()),callback=callback,options=dict(maxiter=160,gtol=1e-5,xtol=1e-8,barrier_tol=1e-8,initial_barrier_parameter=1e-5,initial_barrier_tolerance=1e-5,sparse_jacobian=True,factorization_method='AugmentedSystem',verbose=0))
        x=result.x
    except BaseException as exc:
        error=type(exc).__name__+':'+str(exc);x=saved['x'];(D/'solver-error-private.txt').write_text(traceback.format_exc())
    solving[0]=False;optimizer_cost=dict(CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall);points=problem.points(x);profile=rebuild(points,s);backup=rebuild(points,s,True);baseline=path_for(s,'baseline');rows=problem.constraints(x);_,geometry=problem.geo.evaluate(points,details=True);screen=exact_screen(points,s);periodic=x[problem.k:problem.k+problem.n]*Q;launch=np.r_[0.,x[problem.k+problem.n:]*Q];regperiodic=np.array(profile['periodic_squared']);reglaunch=np.array(profile['launch_squared']);speed_over_periodic=float(max(0.,max(np.sqrt(np.maximum(periodic,0))-np.sqrt(regperiodic))));speed_over_launch=float(max(0.,max(np.sqrt(np.maximum(launch,0))-np.sqrt(reglaunch))));conservative=max(speed_over_periodic,speed_over_launch)<=.001;design_time=problem.objective(x)*problem.time_scale;clock=scalar_clock(profile);gain=scalar_clock(baseline)-clock;bound_violation=max(0.,float(max(problem.lower-x)),float(max(x-problem.upper)));residual=max(0.,-float(rows.min()),bound_violation);converged=bool(result is not None and result.success and result.status==1 and result.optimality<=1e-5 and residual<=1e-6);eligible=bool(converged and geometry['minimum_outer_rectangle_margin_m']>=1.25 and geometry['outside_samples']==0 and geometry['max_sample_spacing_m']<=.5 and screen['minimum_outer_rectangle_margin_m']>=1.25 and screen['pass_geometry'] and gain>=.5)
    # Design q is never deployed. Rebuilt existing528 profiles alone set scalar gate.
    data=dict(baseline=baseline,baseline_backup=path_for(s,'baseline_backup'),candidate=profile,backup=backup)
    for filename,value in [('frozen-paths-private.json',data),('design-solution-private.json',dict(x=x.tolist(),periodic_squared=periodic.tolist(),launch_squared=launch.tolist(),iterations=iterations))]:
        p=D/filename
        with p.open('x') as f:json.dump(value,f)
        p.chmod(0o600)
    categories={name:dict(minimum=float(rows[a:b].min()),violated=int(sum(rows[a:b]<-1e-6))) for name,a,b in [('geometry',0,9*problem.n),*[(name,(9+j)*problem.n,(10+j)*problem.n) for j,name in enumerate(['lateral_minus','lateral_plus','periodic_forward_force','periodic_forward_power','periodic_backward80','launch_periodic_cap','launch_forward_force','launch_forward_power','launch_backward80'])]]}
    out=dict(status='JOINT_PATH_SPEED_DESIGN_ELIGIBLE' if eligible else 'JOINT_PATH_SPEED_NOT_PROMOTED',pass_design_gate=eligible,initialization='Only531restoredendpoint+unchanged528periodic/launchprofile',initial_time_s=problem.time_scale,initial_max_normalized_violation=max(0.,-float(initial_c.min())),initial_geometry=initial_geometry,variables=problem.size,path_variables=problem.k,periodic_speed_variables=problem.n,launch_speed_variables=problem.n,optimizer_success=bool(result.success) if result is not None else False,optimizer_status=int(result.status) if result is not None else None,optimizer_message=str(result.message) if result is not None else error,iterations=int(result.nit) if result is not None else saved['iteration'],optimality=float(result.optimality) if result is not None else None,solver_converged=converged,max_normalized_violation=residual,residual_categories=categories,geometry=geometry,independent530screen=screen,design_speed_clock_s=design_time,regenerated528_profile_clock_s=clock,baseline528_scalar_clock_s=scalar_clock(baseline),scalar_screen_gain_s=gain,design_periodic_speed_excess_over_regenerated_m_s=speed_over_periodic,design_launch_speed_excess_over_regenerated_m_s=speed_over_launch,design_speed_conservative_or_equal=conservative,performance_gate_profile='Alwaysregenerated528;designspeednotdeployed',candidate_length_m=profile['length'],candidate_max_abs_curvature=max(map(abs,profile['curvature'])),optimizer_cost=optimizer_cost,evaluation_cost=problem.cost,geometry_cost=dict(calls=problem.geo.calls,segment_samples=problem.geo.segment_samples),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,model_integrator_ticks=0,force_evaluations=0,native_actions=0,native_resets=0,native_worlds=0,frozen_paths_sha256=hashlib.sha256((D/'frozen-paths-private.json').read_bytes()).hexdigest(),scope='OnejointNLPwithactualds/speedtimeandexplicitunchangedlateral/source-forward/back80constraints. Numericaldesignnotphysicsbound/gain. Same528controller/path-only;nativewouldcompare525vs532package.')
    with (G/'retry/joint532_design.json').open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
