"""One preregistered synthetic mechanics DEV bench; no racing case or seed."""
import datetime
import hashlib
import itertools
import json
import math
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
from types import SimpleNamespace as NS

from retry.brake502_response import Wheel, State, choose_brake, f32

G=Path(__file__).resolve().parents[1]
PRIVATE=Path('/workspace/haic-response502-private')


def run():
    start=time.perf_counter(); cpu=time.process_time()
    child0=resource.getrusage(resource.RUSAGE_CHILDREN)
    contract_path=G/'retry/brake502_final_contract.json'
    contract=json.loads(contract_path.read_text())
    PRIVATE.mkdir(mode=0o700,exist_ok=True)
    if (PRIVATE/'PHYSICS_STARTED.json').exists() or (G/'retry/brake502_result.json').exists():
        raise RuntimeError('NO_RETRY_AFTER_PHYSICS')
    def dump(path,data):
        encoded=(json.dumps(data,indent=2,allow_nan=False)+'\n').encode()
        if len(encoded)>16*1024**2:raise RuntimeError('DERIVED_CAP')
        with path.open('xb') as handle:handle.write(encoded)
        path.chmod(0o600 if PRIVATE in path.parents else 0o644)
    def usage():
        c=resource.getrusage(resource.RUSAGE_CHILDREN)
        return time.process_time()-cpu+c.ru_utime+c.ru_stime-child0.ru_utime-child0.ru_stime+2
    def guard(*args):
        if usage()>=120 or time.perf_counter()-start+2>=180:raise RuntimeError('RESOURCE_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(contract['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGPROF,lambda *args:(_ for _ in ()).throw(RuntimeError('CPU_TIMER')))
    signal.signal(signal.SIGALRM,lambda *args:(_ for _ in ()).throw(RuntimeError('WALL_TIMER')))
    signal.setitimer(signal.ITIMER_PROF,118);signal.setitimer(signal.ITIMER_REAL,178)
    for name,expected in contract['source_sha256'].items():
        if hashlib.sha256((G/name).read_bytes()).hexdigest()!=expected:raise RuntimeError('SOURCE_PIN:'+name)
    for name in ('screen501_result.json','envelope500_result.json','diagnostic499_result.json'):
        old=json.loads((G/'retry'/name).read_text())
        if old['research_remaining']!=26027 or old['reserve']!=84000 or old['reserve_used']!=0:
            raise RuntimeError('PUBLIC_BUDGET_CONFLICT:'+name)
    test=subprocess.run([sys.executable,'-m','unittest','retry.test_brake502_response','-v'],cwd=G,capture_output=True,text=True,timeout=60)
    dump(PRIVATE/'pure-tests-final.json',{'returncode':test.returncode,'stdout':test.stdout,'stderr':test.stderr})
    if test.returncode:raise RuntimeError('PURE_GATE_FAILED_NO_WORLD')
    guard()
    from Box2D.b2 import world as World
    from core.vendor.car_dynamics import Car
    dump(PRIVATE/'PHYSICS_STARTED.json',{'contract_sha256':hashlib.sha256(contract_path.read_bytes()).hexdigest(),'once':True,'new_synthetic_bench_not_501_replay':True})
    created=ticks=closed=0; rows=[]; errors={'scalar':[],'response':[]}; hull_errors={'scalar':[],'response':[]}
    prediction_errors=[];clips=0
    source=(G/'core/vendor/car_dynamics.py').read_text().splitlines()
    force_line=next(i+1 for i,s in enumerate(source) if 'w.omega -= dt * f_force' in s)
    def com(car):
        bodies=[car.hull,*car.wheels];mass=sum(b.mass for b in bodies)
        return tuple(sum(b.mass*b.linearVelocity[j] for b in bodies)/mass for j in range(2))
    for speed,extra,desired_a in itertools.product(contract['speed_grid'],contract['rim_surplus_grid'],contract['deceleration_grid']):
        for arm in ('scalar','response'):
            guard()
            if created>=16:raise RuntimeError('WORLD_CAP')
            created+=1;world=World(gravity=(0,0));car=None
            try:
                car=Car(world,0.,0.,0.)
                for b in [car.hull,*car.wheels]:b.linearVelocity=(0.,speed)
                for w in car.wheels:
                    w.tiles=[NS(road_friction=1.)];w.omega=(speed+extra)/.54
                for w in car.wheels[2:]:w.gas=.6
                mass=sum(b.mass for b in [car.hull,*car.wheels])
                state=State(com(car),tuple(Wheel(w.omega,w.gas,heading=w.angle) for w in car.wheels),mass)
                target=speed-.08*desired_a
                if arm=='response':brake,prediction=choose_brake(state,target)
                else:
                    effective_mass=mass+4*1.6/.54**2
                    brake=f32(effective_mass*desired_a/(4*1.6*15/(.02*.54)))
                    prediction=target
                actual=[]
                for tick in range(4):
                    guard()
                    car.gas(0.);car.brake(brake)
                    force=[]
                    def trace(frame,event,arg):
                        if frame.f_code is Car.step.__code__:
                            if event=='line' and frame.f_lineno==force_line:
                                loc=frame.f_locals;w=loc['w']
                                force.append({'wheel':car.wheels.index(w),'omega_before_reaction':w.omega,'f':float(loc['f_force']),'p':float(loc['p_force']),'vf':float(loc['vf']),'vs':float(loc['vs'])})
                            return trace
                        return None
                    before={'COM':com(car),'hull_velocity':list(car.hull.linearVelocity),'omega':[w.omega for w in car.wheels]}
                    sys.settrace(trace)
                    try:car.step(.02)
                    finally:sys.settrace(None)
                    if len(force)!=4:raise RuntimeError('FORCE_CAPTURE_COVERAGE')
                    clips+=sum(math.hypot(f['f'],f['p'])>=400.-1e-9 for f in force)
                    if ticks>=64:raise RuntimeError('TICK_CAP')
                    ticks+=1;world.Step(.02,180,60)
                    actual.append({'tick':tick+1,'before':before,'forces':force,'after_COM':com(car),'hull_velocity':list(car.hull.linearVelocity),'omega_after':[w.omega for w in car.wheels]})
                observed=math.hypot(*com(car));hull=math.hypot(*car.hull.linearVelocity)
                errors[arm].append(observed-target);hull_errors[arm].append(hull-target)
                if arm=='response':prediction_errors.append(observed-prediction)
                rows.append({'arm':arm,'speed':speed,'rim_surplus':extra,'desired_deceleration':desired_a,'target':target,'brake':brake,'prediction':prediction,'actual':actual})
            finally:
                sys.settrace(None)
                for body in list(world.bodies):world.DestroyBody(body)
                if world.bodyCount or world.jointCount:raise RuntimeError('WORLD_NOT_CLOSED')
                closed+=1;car=None;world=None
    def stats(values):
        return {'RMSE_m_s':math.sqrt(sum(x*x for x in values)/len(values)),'max_abs_m_s':max(map(abs,values)),'mean_signed_m_s':sum(values)/len(values)}
    scalar,response=stats(errors['scalar']),stats(errors['response'])
    passed=response['RMSE_m_s']<=.5*scalar['RMSE_m_s'] and response['max_abs_m_s']<=.15 and max(map(abs,hull_errors['response']))<=.15
    dump(PRIVATE/'bench-raw.json',rows)
    result={'status':'SYNTHETIC_RESPONSE_GATE_PASS' if passed else 'CANDIDATE_REJECTED_STOP',
        'scope':'New synthetic road-free source mechanics DEV bench; not old501 raw analysis, not racing or pixel-policy qualification',
        'hypothesis':'Four-tick wheel torque/slip response inversion reduces end-speed target error relative to steady effective-mass brake mapping',
        'scalar':scalar,'response':response,'response_forecast_vs_assembly_COM':stats(prediction_errors),
        'response_hull_target_error':stats(hull_errors['response']),
        'paired_cases':8,'pure_tests':3,'source_force_contexts':576,'worlds':created,'raw_ticks':ticks,'closed_worlds':closed,'live_worlds':created-closed,
        'force_capture_rows':ticks*4,'force_limit_saturated_wheel_ticks':clips,
        'racing_resets_native_actions_seeds_HOLDOUT_SEALED':0,'research_remaining':26027,'reserve':84000,'reserve_used':0,
        'not_claimed':['original501 cause decomposition','old root identity reproduction','track safety','lap finish','full method promotion','protected or independent DEV generalization'],
        'CPU_s_including_test_child_and_preparation_charge':usage(),'wall_s_including_preparation_charge':time.perf_counter()-start+2,'source_sha256':contract['source_sha256'],
        'private_raw_bytes':sum(p.stat().st_size for p in PRIVATE.iterdir()),'private_raw_durable_off_host':False}
    guard();dump(G/'retry/brake502_result.json',result)
    print(json.dumps(result,indent=2));return result


if __name__=='__main__':run()
