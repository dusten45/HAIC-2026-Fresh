"""Frozen502 candidate under steering, yaw and synthetic contact changes."""
import datetime, hashlib, json, math, signal, subprocess, sys, time, resource
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace as NS
from retry.brake502_response import DT, Wheel, State, choose_brake, forecast, wheel_response, f32

G=Path(__file__).resolve().parents[1]
D=Path('/workspace/haic-response503-private')


def fixtures():
    # Deterministic synthetic fixtures: no track, split draw, seed or old state.
    default=dict(vx=0.,vy=80.,yaw=0.,front=0.,steer=0.,left_friction=1.,extra=0.,lose_left=False)
    changes=[('straight_rolling',{}),('straight_spinning',dict(extra=12.)),
        ('steering_ramp',dict(steer=.3)),
        ('steering_reversal',dict(front=.25,steer=-.3)),
        ('lateral_yaw',dict(vx=6.,yaw=.6)),
        ('left_low_friction',dict(left_friction=.6,extra=12.)),
        ('left_contact_loss',dict(lose_left=True,extra=12.)),
        ('steer_yaw_asym',dict(steer=.3,vx=6.,yaw=.6,left_friction=.6)),
        ('steer_yaw_contact_loss',dict(steer=.3,vx=6.,yaw=.6,lose_left=True,extra=12.))]
    return [(name,dict(default,**change)) for name,change in changes]


def com(car,position=False):
    bodies=[car.hull,*car.wheels];mass=sum(b.mass for b in bodies)
    return tuple(sum(b.mass*(b.worldCenter if position else b.linearVelocity)[j] for b in bodies)/mass for j in range(2))


def friction(car,wheel):
    return max([400.*car.grass_friction_multiplier,*[400.*t.road_friction for t in wheel.tiles]])*car.grip_multiplier


def observed_state(car):
    velocity=com(car)
    wheels=tuple(Wheel(w.omega,w.gas,w.angle,friction(car,w),tuple(w.linearVelocity[j]-velocity[j] for j in range(2))) for w in car.wheels)
    return State(velocity,wheels,sum(b.mass for b in [car.hull,*car.wheels]),car.engine_multiplier)


def advance(state,brake):
    items=[wheel_response(w,state.velocity,0.,brake,state.engine_multiplier) for w in state.wheels]
    velocity=tuple(state.velocity[j]+DT*sum(item[1][j] for item in items)/state.mass for j in range(2))
    return replace(state,velocity=velocity,wheels=tuple(i[0] for i in items)),items


def stats(xs):
    return dict(count=len(xs),RMSE=math.sqrt(sum(x*x for x in xs)/len(xs)) if xs else None,max_abs=max(map(abs,xs)) if xs else None)


def run():
    start=time.perf_counter();cpu=time.process_time();child0=resource.getrusage(resource.RUSAGE_CHILDREN)
    contract=json.loads((G/'retry/brake503_contract.json').read_text())
    D.mkdir(mode=0o700,exist_ok=False)
    def save(path,value):
        data=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
        if sum(p.stat().st_size for p in D.iterdir())+len(data)>16*1024**2:raise RuntimeError('STORAGE_CAP')
        with path.open('xb') as f:f.write(data)
        path.chmod(0o600 if D in path.parents else 0o644)
    def elapsed_cpu():
        c=resource.getrusage(resource.RUSAGE_CHILDREN)
        return time.process_time()-cpu+c.ru_utime+c.ru_stime-child0.ru_utime-child0.ru_stime
    def guard(*args):
        if elapsed_cpu()>60 or time.perf_counter()-start>90:raise RuntimeError('RESOURCE_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(contract['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGALRM,lambda *args:(_ for _ in ()).throw(RuntimeError('WALL_CAP')))
    signal.signal(signal.SIGPROF,lambda *args:(_ for _ in ()).throw(RuntimeError('CPU_CAP')))
    signal.setitimer(signal.ITIMER_REAL,90);signal.setitimer(signal.ITIMER_PROF,60)
    for n,h in contract['source_sha256'].items():
        if hashlib.sha256((G/n).read_bytes()).hexdigest()!=h:raise RuntimeError('SOURCE_PIN')
    prior=json.loads((G/'retry/brake502_result.json').read_text())
    assert (prior['research_remaining'],prior['reserve'],prior['reserve_used'])==(26027,84000,0)
    assert len(fixtures())==9 and len(set(n for n,_ in fixtures()))==9
    pure=subprocess.run([sys.executable,'-m','unittest','retry.test_brake502_response','-v'],cwd=G,capture_output=True,text=True,timeout=30)
    save(D/'pure-tests.json',dict(returncode=pure.returncode,stdout=pure.stdout,stderr=pure.stderr))
    if pure.returncode:raise RuntimeError('PURE_GATE_NO_PHYSICS')
    from Box2D.b2 import world as World
    from core.vendor.car_dynamics import Car
    save(D/'PHYSICS_STARTED.json',dict(once=True,contract_sha256=hashlib.sha256((G/'retry/brake503_contract.json').read_bytes()).hexdigest()))
    force_line=next(i+1 for i,s in enumerate((G/'core/vendor/car_dynamics.py').read_text().splitlines()) if 'w.omega -= dt * f_force' in s)
    created=closed=ticks=0;raw=[];cases=[];oracle_force=[];oracle_omega=[];torque=[];oracle_first=[]
    force_by_stage={k:[] for k in ['frozen','heading','offset','friction','omega','velocity']}
    kinematics={'heading_drift_rad':0.,'wheel_offset_drift_m_s':0.,'hull_yaw_drift_rad_s':0.,'friction_changes':0}
    for name,fixture in fixtures():
        case={'fixture':name}
        for arm in ('scalar','response'):
            guard()
            if created>=18:raise RuntimeError('WORLD_CAP')
            created+=1;world=World(gravity=(0,0));car=None
            try:
                car=Car(world,0.,0.,0.)
                for w in car.wheels[:2]:w.angle=fixture['front']
                center=com(car,True)
                for b in [car.hull,*car.wheels]:
                    x,y=b.worldCenter[0]-center[0],b.worldCenter[1]-center[1]
                    b.linearVelocity=(fixture['vx']-fixture['yaw']*y,fixture['vy']+fixture['yaw']*x)
                    b.angularVelocity=fixture['yaw']
                for i,w in enumerate(car.wheels):
                    w.tiles=[NS(road_friction=fixture['left_friction'] if i%2==0 else 1.)]
                    e=w.GetWorldVector((0,1));w.omega=(e[0]*w.linearVelocity[0]+e[1]*w.linearVelocity[1]+fixture['extra'])/.54
                state=observed_state(car);predstate=state;target=math.hypot(*state.velocity)-.08*20.
                if arm=='response':
                    try:brake,prediction=choose_brake(state,target)
                    except ValueError as error:
                        case[arm]={'abstention':str(error)};continue
                else:
                    brake=f32((state.mass+4*1.6/.54**2)*20./(4*1.6*15/(.02*.54)));prediction=target
                actual=[]
                for tick in range(4):
                    guard()
                    if fixture['lose_left'] and tick==2:
                        for w in car.wheels[::2]:w.tiles=[]
                    car.gas(0.);car.brake(brake);car.steer(fixture['steer'])
                    observed=observed_state(car);forces=[];omega_before=[w.omega for w in car.wheels]
                    def trace(frame,event,arg):
                        if frame.f_code is Car.step.__code__:
                            if event=='line' and frame.f_lineno==force_line:
                                a=frame.f_locals;w=a['w'];e=w.GetWorldVector((0,1));n=w.GetWorldVector((1,0))
                                forces.append(dict(wheel=car.wheels.index(w),f=float(a['f_force']),p=float(a['p_force']),vector=[float(a['f_force']*e[j]+a['p_force']*n[j]) for j in range(2)],omega_braked=w.omega,vf=float(a['vf']),vs=float(a['vs'])))
                            return trace
                        return None
                    sys.settrace(trace)
                    try:car.step(.02)
                    finally:sys.settrace(None)
                    assert len(forces)==4
                    nextpred,preditems=advance(predstate,brake)
                    for i,(a,pw,ow) in enumerate(zip(forces,predstate.wheels,observed.wheels)):
                        exact,vector,detail=wheel_response(ow,observed.velocity,0.,brake)
                        residual=math.dist(vector,a['vector']);oracle_force.append(residual)
                        oracle_omega.append(exact.omega-car.wheels[i].omega)
                        torque.append(1.6*(car.wheels[i].omega-omega_before[i])-1.6*(a['omega_braked']-omega_before[i])+.02*a['f']*.54)
                        if tick==0:oracle_first.append(math.dist(preditems[i][1],a['vector']))
                        if arm=='response':
                            kinematics['heading_drift_rad']=max(kinematics['heading_drift_rad'],abs(ow.heading-pw.heading))
                            kinematics['wheel_offset_drift_m_s']=max(kinematics['wheel_offset_drift_m_s'],math.dist(ow.offset,pw.offset))
                            kinematics['hull_yaw_drift_rad_s']=max(kinematics['hull_yaw_drift_rad_s'],abs(car.hull.angularVelocity-fixture['yaw']))
                            kinematics['friction_changes']+=int(ow.friction!=pw.friction)
                            # Ordered conditional substitutions, each same wheel/tick.
                            x=pw;velocity=predstate.velocity
                            for stage in force_by_stage:
                                if stage=='heading':x=replace(x,heading=ow.heading)
                                elif stage=='offset':x=replace(x,offset=ow.offset)
                                elif stage=='friction':x=replace(x,friction=ow.friction)
                                elif stage=='omega':x=replace(x,omega=ow.omega)
                                elif stage=='velocity':velocity=observed.velocity
                                vector2=wheel_response(x,velocity,0.,brake)[1]
                                force_by_stage[stage].append(math.dist(vector2,a['vector']))
                    if ticks>=72:raise RuntimeError('TICK_CAP')
                    ticks+=1;world.Step(.02,180,60)
                    actual.append(dict(tick=tick+1,observed_before={'velocity':observed.velocity,'wheels':[w.__dict__ for w in observed.wheels]},forces=forces,omega_after=[w.omega for w in car.wheels],COM_after=com(car),hull_velocity=list(car.hull.linearVelocity),hull_yaw=car.hull.angularVelocity))
                    predstate=nextpred
                assert abs(math.hypot(*predstate.velocity)-math.hypot(*forecast(state,brake)[0].velocity))<1e-10
                actualspeed=math.hypot(*com(car));case[arm]=dict(error_m_s=actualspeed-target,forecast_error_m_s=actualspeed-prediction,hull_error_m_s=math.hypot(*car.hull.linearVelocity)-target)
                raw.append(dict(fixture=name,arm=arm,brake=brake,target=target,prediction=prediction,ticks=actual))
            finally:
                sys.settrace(None)
                for b in list(world.bodies):world.DestroyBody(b)
                assert world.bodyCount==world.jointCount==0
                car=None;world=None;closed+=1
        cases.append(case)
    scalar=[c['scalar']['error_m_s'] for c in cases];response=[c['response']['error_m_s'] for c in cases if 'error_m_s' in c['response']]
    abstentions=len(cases)-len(response)
    source_pass=max(oracle_force)<=1e-3 and max(map(abs,oracle_omega))<=1e-5
    passed=source_pass and not abstentions and stats(response)['RMSE']<=.5*stats(scalar)['RMSE'] and stats(response)['max_abs']<=.15 and max(abs(c['response']['hull_error_m_s']) for c in cases)<=.15
    save(D/'bench-raw.json',raw)
    result=dict(status='ROBUSTNESS_GATE_PASS' if passed else 'FROZEN_KINEMATICS_CANDIDATE_REJECTED',source_law_gate_pass=source_pass,
        scalar=stats(scalar),response=stats(response),abstentions=abstentions,cases=cases,
        source_force_oracle_error_N=stats(oracle_force),source_omega_oracle_error_rad_s=stats(oracle_omega),first_tick_frozen_force_error_N=stats(oracle_first),same_tick_torque_identity_residual=stats(torque),
        ordered_conditional_force_residual_N={k:stats(v) for k,v in force_by_stage.items()},kinematics=kinematics,
        worlds=created,closed_worlds=closed,live_worlds=created-closed,raw_ticks=ticks,CPU_s=elapsed_cpu(),wall_s=time.perf_counter()-start,
        racing_resets_native_actions_seeds_HOLDOUT_SEALED=0,research_remaining=26027,reserve=84000,reserve_used=0,
        source_sha256=contract['source_sha256'],scope='New deterministic synthetic mechanics only; not old501 or independent track evidence',private_raw_durable_off_host=False)
    guard();save(G/'retry/brake503_result.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':run()
