"""Finite free-body steady-turn branch screen, then at most two source holds.

The old curve supplies diagnostic stations only. This is not a path-tracking
controller, a minimum-time bound, or a proof about other equilibrium branches.
"""
import datetime, hashlib, json, math, signal, time, traceback
from dataclasses import asdict, replace
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from retry.plan513_model import load_root
from retry.brake502_response import DT, POWER, INERTIA, RADIUS, STIFFNESS
from retry.brake508_corridor import bounds, indexed_contacts
from retry.brake506_geometry import rectangle
from retry.brake510_common import boundary_index
from retry.corner515_model import margin
from retry.closure524_control import tick
from retry.speed516_control import force_rows
from retry.lap518_finish import hull_pose

G = Path(__file__).resolve().parents[1]
D = Path('/workspace/haic-response555-private')
INPUTS = [Path('/workspace/haic-response515-private/collected-map-state-private.json'),
          Path('/workspace/haic-response551-private/frozen-paths-private.json')]
SOURCES = ['retry/drift555_mechanism.py', 'retry/brake502_response.py',
           'retry/brake504_planar.py', 'retry/plan512_control.py',
           'retry/closure524_control.py', 'retry/plan513_model.py',
           'retry/speed516_control.py', 'retry/corner515_model.py']

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def save(p, value):
    with p.open('x') as f: json.dump(value, f, indent=2, allow_nan=False)
    p.chmod(0o600 if D in p.parents else 0o644)

def run():
    D.mkdir(mode=0o700, exist_ok=False)
    contract = dict(
        registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        deadline_utc='2026-10-20T10:01:55+00:00',
        hypothesis='A quasi-steady free-body/sideslip force-allocation planner at the SAME 90m/s COM ceiling has a branch capable of an optimistic diagnostic clock <=12.22s, one second below source551. No PP, speed-reference or nominal backup is used in this mechanism screen. The old curve is a diagnostic seed; neither its feasibility nor a different free-corridor trajectory is proved.',
        scope='One analytic branch: constant-speed, constant-curvature, zero net body torque, equal rear gas, unpowered rolling front wheels, all tires UNCLIPPED. Body sideslip and front joint angle are solved jointly. Not a full trajectory or transient reachability claim.',
        constants=dict(speed_ceiling=90., minimum_speed=1., beta_search_rad=[-.6,.6], joint_limit_rad=.4, maximum_raw_force_ratio=.999, normalized_equilibrium_residual=1e-7, speed_bisections=12, least_squares_max_nfev=70),
        stop_promotion=dict(numerical_low_speed_branch_failure='stop; solver/branch failure, not physical impossibility', optimistic_clock_above12_22='stop this quasi-steady branch, no source propagation', next_check='Only if every station has a branch and optimistic clock <=12.22: independently propagate max-abs-beta and max-force states for 4 raw ticks each, deduplicated. Initial states are synthetic mechanism fixtures on the same known DEV map, not reachable-state certificates.', source_witness='all footprint>=.50, raw force<=1.059, all hull/wheel speed<100, no clip; speed drift<=.15, yaw drift<=.05, sideslip drift<=.02 rad. These last residual tolerances are diagnostic, not physical necessities.', deep='No full controller/cold/carry/native authorized by this mechanism alone. Future candidate gates remain cold >=500ms vs54113.66, carry nonworsening vs54114.46, fresh native pair >=500ms with <=1000 actions/2 resets/2 worlds/4102 raw.'),
        caps=dict(CPU_s=90, wall_s=120, analytic_wheel_evaluations=2000000, explicit_source_wheel_evaluations=40, model_ticks=8, geometry=10),
        split='known DEV only; no new seed, HOLDOUT, SEALED, reserve or external compute',
        source_sha256={p:sha(G/p) for p in SOURCES},
        private_inputs_sha256={str(p):sha(p) for p in INPUTS})
    save(G/'retry/drift555_contract.json', contract)
    save(D/'STARTED.json', dict(contract_sha256=sha(G/'retry/drift555_contract.json')))
    cpu, wall = time.process_time(), time.perf_counter()
    cost = dict(analytic_wheel_evaluations=0, explicit_source_wheel_evaluations=0, model_ticks=0, geometry=0, nonlinear_solves=0)
    counter = [0]; records=[]; witnesses=[]; out={}
    def guard(*_):
        if time.process_time()-cpu>=90 or time.perf_counter()-wall>=120: raise RuntimeError('COST_CAP')
        if cost['analytic_wheel_evaluations']>=2000000: raise RuntimeError('ALGEBRA_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(contract['deadline_utc']): raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGPROF,guard);signal.setitimer(signal.ITIMER_PROF,90)
    signal.signal(signal.SIGALRM,guard);signal.setitimer(signal.ITIMER_REAL,120)
    try:
        static, paths = map(read, INPUTS); path=paths['candidate']; root=load_root(static['root'])
        p=root.planar; mass=p.linear.mass; a=p.angle; c,s=math.cos(a),math.sin(a)
        levers=np.array([(c*x+s*y,-s*x+c*y) for x,y in p.levers]); wb=float(levers[:2,1].mean()-levers[2:,1].mean())
        rear=-float(levers[2:,1].mean()); engine=p.linear.engine_multiplier
        A=(1-STIFFNESS*DT*RADIUS**2/INERTIA)/(STIFFNESS*RADIUS)
        assert A>0 and all(w.friction==400. for w in p.linear.wheels)
        def forces(v,k,x):
            guard();cost['analytic_wheel_evaluations']+=4
            beta,delta,gas=x; yaw=v*k; velocity=np.array([-v*math.sin(beta),v*math.cos(beta)])
            result=[]; omegas=[]; ratios=[]
            for i,(rx,ry) in enumerate(levers):
                h=delta if i<2 else 0.; f=np.array([-math.sin(h),math.cos(h)]); side=np.array([math.cos(h),math.sin(h)])
                vel=velocity+np.array([-yaw*ry,yaw*rx]); vf=float(f@vel); vs=float(side@vel)
                if i<2: longitudinal=0.;omega=vf/RADIUS
                else:
                    B=vf/RADIUS+5.;C=POWER*engine*gas/RADIUS
                    longitudinal=2*C/(B+math.sqrt(B*B+4*A*C)) if C else 0.
                    omega=(vf+longitudinal*(1-STIFFNESS*DT*RADIUS**2/INERTIA)/STIFFNESS)/RADIUS
                lateral=-STIFFNESS*vs; result.append(longitudinal*f+lateral*side)
                omegas.append(omega);ratios.append(math.hypot(longitudinal,lateral)/400.)
            return np.array(result),omegas,ratios
        def solve(v,k):
            cost['nonlinear_solves']+=1
            x0=np.array([-math.atan(rear*k),math.atan(wb*k),.02])
            x0=np.clip(x0,[-.599,-.399,1e-12],[.599,.399,.999999])
            def residual(x):
                f,_,_=forces(v,k,x); beta=x[0];target=mass*v*v*k*np.array([-math.cos(beta),-math.sin(beta)])
                return np.r_[(f.sum(axis=0)-target)/400.,np.sum(levers[:,0]*f[:,1]-levers[:,1]*f[:,0])/(400.*wb)]
            opt=least_squares(residual,x0,bounds=([-.6,-.4,0.],[.6,.4,1.]),max_nfev=70,ftol=1e-10,xtol=1e-10,gtol=1e-10)
            f,w,r=forces(v,k,opt.x); error=float(np.max(np.abs(residual(opt.x))))
            ok=bool(error<=1e-7 and min(w)>0 and max(r)<=.999)
            return dict(speed=v,curvature=k,beta=float(opt.x[0]),delta=float(opt.x[1]),gas=float(opt.x[2]),force=f.tolist(),omegas=w,ratios=r,equilibrium_residual=error,solver_success=bool(opt.success),admitted=ok,nfev=opt.nfev)
        for i,k in enumerate(path['curvature']):
            guard(); top=solve(90.,k)
            if top['admitted']: chosen=top
            else:
                low=solve(1.,k)
                if not low['admitted']:
                    save(D/'branch-failure-private.json',dict(station=i,low=low,top=top))
                    raise RuntimeError('LOW_SPEED_BRANCH_NOT_FOUND')
                lo,hi=1.,90.;chosen=low
                for _ in range(12):
                    mid=(lo+hi)/2;candidate=solve(mid,k)
                    if candidate['admitted']: lo=mid;chosen=candidate
                    else:hi=mid
            chosen['station']=i;records.append(chosen)
        speeds=[z['speed'] for z in records]
        clock=sum(2*d/(speeds[i]+speeds[(i+1)%len(speeds)]) for i,d in enumerate(path['ds']))
        gate=clock<=12.22
        save(D/'steady-branches-private.json',records)
        if gate:
            ids=sorted(set([max(range(len(records)),key=lambda i:abs(records[i]['beta'])),max(range(len(records)),key=lambda i:max(records[i]['ratios']))]))
            roadindex=bounds(static['roads']);edgeindex=boundary_index(static['boundary'])
            for i in ids:
                rec=records[i];vx,vy=np.subtract(path['points'][(i+1)%len(records)],path['points'][i]);theta=math.atan2(-vx,vy)-rec['beta'];ct,st=math.cos(theta),math.sin(theta)
                rl=tuple((ct*x-st*y,st*x+ct*y) for x,y in levers); yaw=rec['speed']*rec['curvature']
                velocity=(-rec['speed']*math.sin(theta+rec['beta']),rec['speed']*math.cos(theta+rec['beta']))
                wheels=tuple(replace(w,omega=rec['omegas'][j],gas=rec['gas'] if j>=2 else 0.,heading=theta+(rec['delta'] if j<2 else 0.),offset=(-yaw*rl[j][1],yaw*rl[j][0]),friction=400.) for j,w in enumerate(p.linear.wheels))
                pp=replace(p,linear=replace(p.linear,velocity=velocity,wheels=wheels),angle=theta,levers=rl,joints=(rec['delta'],rec['delta'],0.,0.),rates=(0.,)*4,yaw=yaw,angular_momentum=p.inertia*yaw,steer=rec['delta'])
                state=replace(root,planar=pp,center=tuple(path['points'][i]))
                contacts=tuple(indexed_contacts(rectangle(tuple(state.center[t]+r[t] for t in range(2)),w.heading),state.roads,roadindex,state.skin) for r,w in zip(rl,wheels))
                state=replace(state,current_contacts=contacts); rows=[];action=np.array([-rec['delta'],rec['gas'],0.],np.float32)
                state=replace(state,planar=replace(state.planar,steer=-float(action[0])))
                initial=asdict(state);initial.pop('roads')
                witness=dict(station=i,initial_root_without_roads=initial,action=action.tolist(),rows=rows,passed=False)
                witnesses.append(witness)
                for raw in range(5):
                    guard(); mm=margin(state,static['roads'],roadindex,static['boundary'],edgeindex,static['obstacles']);cost['geometry']+=1
                    body=max(math.hypot(*hull_pose(state)[1]),*(math.hypot(*(state.planar.linear.velocity[t]+w.offset[t] for t in range(2))) for w in state.planar.linear.wheels))
                    if mm<.5 or body>=100:
                        witness.update(first_failure='SYNTHETIC_FIXTURE_GEOMETRY_OR_BODY',margin=mm,body=body);break
                    if raw==4:break
                    f=force_rows(state,action);cost['explicit_source_wheel_evaluations']+=4
                    if max(z['ratio'] for z in f)>1.059 or any(z['clipped'] for z in f):
                        witness.update(first_failure='SOURCE_FORCE_OR_CLIP');break
                    state=tick(state,float(action[1]),0.,roadindex,counter);cost['model_ticks']=counter[0]
                    rr=asdict(state);rr.pop('roads');rows.append(dict(raw=raw+1,root_without_roads=rr,forces=f,before_margin=mm,body=body))
                if len(rows)==4:
                    speed=math.hypot(*state.planar.linear.velocity);beta=math.atan2(-state.planar.linear.velocity[0],state.planar.linear.velocity[1])-state.planar.angle
                    bd=math.atan2(math.sin(beta-rec['beta']),math.cos(beta-rec['beta']))
                    witness.update(speed_drift=speed-rec['speed'],yaw_drift=state.planar.yaw-yaw,beta_drift=bd)
                    witness['passed']=abs(witness['speed_drift'])<=.15 and abs(witness['yaw_drift'])<=.05 and abs(bd)<=.02
                    if not witness['passed']:witness['first_failure']='FINITE_HOLD_EQUILIBRIUM_RESIDUAL'
            save(D/'source-witnesses-private.json',witnesses)
        out=dict(completed=True,steady_stations=len(records),optimistic_station_clock_s=clock,source551_s=13.22,target_clock_s=12.22,optimistic_clock_gate=gate,source_checks=len(witnesses),source_checks_passed=sum(z['passed'] for z in witnesses),source_failure_counts={reason:sum(z.get('first_failure')==reason for z in witnesses) for reason in sorted(set(z.get('first_failure','PASS') for z in witnesses))},max_abs_beta_rad=max(abs(z['beta']) for z in records),max_abs_joint_rad=max(abs(z['delta']) for z in records),max_steady_ratio=max(max(z['ratios']) for z in records),max_equilibrium_residual=max(z['equilibrium_residual'] for z in records),finite_branch_only=True,instantaneous_station_clock_omits_launch_transitions_and_geometry=True,model_clock_is_not_actual_gain_or_bound=True,full_controller_candidate=False,deep_phases_executed=0)
    except BaseException as e:
        out=dict(completed=False,error=type(e).__name__+':'+str(e),steady_stations_completed=len(records),deep_phases_executed=0)
        save(D/'failure-private.json',dict(error=out['error'],traceback=traceback.format_exc(),cost=cost,records=records,witnesses=witnesses))
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        out.update(cost=cost,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,new_native_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT_queries=0,SEALED_queries=0,research_remaining=22758,reserve=84000,reserve_used=0)
        save(G/'retry/drift555_result.json',out);print(json.dumps(out,indent=2))

if __name__=='__main__': run()
