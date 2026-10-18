"""One planar correction on the fixed503 matrix; reuse saved paired controls."""
import datetime, hashlib, json, math, resource, signal, subprocess, sys, time
from pathlib import Path
from types import SimpleNamespace as NS
from retry.brake503_diagnostic import fixtures,com,observed_state
from retry.brake504_planar import Planar,choose,forecast

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response504-private');OLD=Path('/workspace/haic-response503-private')


def planar(car,steer):
    center=com(car,True);linear=observed_state(car);bodies=[car.hull,*car.wheels]
    levers=[tuple(b.worldCenter[j]-center[j] for j in range(2)) for b in bodies]
    intrinsic=[b.inertia-b.mass*sum(v*v for v in b.localCenter) for b in bodies]
    inertia=sum(I+b.mass*sum(x*x for x in r) for I,b,r in zip(intrinsic,bodies,levers))
    momentum=sum(I*b.angularVelocity+b.mass*(r[0]*(b.linearVelocity[1]-linear.velocity[1])-r[1]*(b.linearVelocity[0]-linear.velocity[0])) for I,b,r in zip(intrinsic,bodies,levers))
    return Planar(linear,tuple(levers[1:]),inertia,momentum,car.hull.angularVelocity,car.hull.angle,tuple(w.angle-car.hull.angle for w in car.wheels),tuple(w.angularVelocity-car.hull.angularVelocity for w in car.wheels),tuple(intrinsic[1:]),steer,car.steering_multiplier)


def run():
    cpu=time.process_time();start=time.perf_counter();child0=resource.getrusage(resource.RUSAGE_CHILDREN)
    c=json.loads((G/'retry/brake504_contract.json').read_text());D.mkdir(mode=0o700,exist_ok=False)
    def save(p,v):
        data=(json.dumps(v,indent=2,allow_nan=False)+'\n').encode()
        if sum(x.stat().st_size for x in D.iterdir())+len(data)>16*1024**2:raise RuntimeError('STORAGE_CAP')
        with p.open('xb') as f:f.write(data)
        p.chmod(0o600 if D in p.parents else 0o644)
    def usage():
        x=resource.getrusage(resource.RUSAGE_CHILDREN)
        return time.process_time()-cpu+x.ru_utime+x.ru_stime-child0.ru_utime-child0.ru_stime
    def guard(*args):
        if usage()>=60 or time.perf_counter()-start>=90:raise RuntimeError('RESOURCE_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGALRM,lambda *args:(_ for _ in ()).throw(RuntimeError('WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,90)
    signal.signal(signal.SIGPROF,lambda *args:(_ for _ in ()).throw(RuntimeError('CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,60)
    for n,h in c['source_sha256'].items():
        if hashlib.sha256((G/n).read_bytes()).hexdigest()!=h:raise RuntimeError('SOURCE_CHANGED')
    if hashlib.sha256((OLD/'bench-raw.json').read_bytes()).hexdigest()!=c['old503_raw_sha256']:raise RuntimeError('OLD_DATA_CHANGED')
    old=json.loads((OLD/'bench-raw.json').read_text());controls=json.loads((G/'retry/brake503_result.json').read_text())
    assert (controls['research_remaining'],controls['reserve'],controls['reserve_used'])==(26027,84000,0)
    test=subprocess.run([sys.executable,'-m','unittest','retry.test_brake504','-v'],cwd=G,capture_output=True,text=True,timeout=30)
    save(D/'pure-tests.json',dict(returncode=test.returncode,stdout=test.stdout,stderr=test.stderr))
    if test.returncode:raise RuntimeError('PURE_GATE_NO_WORLD')
    from Box2D.b2 import world as World
    from core.vendor.car_dynamics import Car
    save(D/'PHYSICS_STARTED.json',dict(once=True,contract_sha256=hashlib.sha256((G/'retry/brake504_contract.json').read_bytes()).hexdigest()))
    worlds=ticks=closed=0;rows=[];cases={};initial_exact=0
    for name,fixture in fixtures():
        guard()
        if worlds>=9:raise RuntimeError('WORLD_CAP')
        worlds+=1;world=World(gravity=(0,0));car=None
        try:
            car=Car(world,0.,0.,0.)
            for w in car.wheels[:2]:w.angle=fixture['front']
            center=com(car,True)
            for b in [car.hull,*car.wheels]:
                x,y=b.worldCenter[0]-center[0],b.worldCenter[1]-center[1]
                b.linearVelocity=(fixture['vx']-fixture['yaw']*y,fixture['vy']+fixture['yaw']*x);b.angularVelocity=fixture['yaw']
            for i,w in enumerate(car.wheels):
                w.tiles=[NS(road_friction=fixture['left_friction'] if i%2==0 else 1.)]
                e=w.GetWorldVector((0,1));w.omega=(e[0]*w.linearVelocity[0]+e[1]*w.linearVelocity[1]+fixture['extra'])/.54
            state=planar(car,fixture['steer']);prior=next(r for r in old if r['fixture']==name and r['arm']=='response')
            observed=dict(velocity=list(state.linear.velocity),wheels=[dict(w.__dict__,offset=list(w.offset)) for w in state.linear.wheels])
            if observed!=prior['ticks'][0]['observed_before']:raise RuntimeError('PAIRED_INITIAL_INPUT_NOT_EXACT')
            initial_exact+=1;target=prior['target']
            try:brake,prediction=choose(state,target)
            except ValueError as error:cases[name]=dict(abstention=str(error));continue
            trace=[]
            for tick in range(4):
                guard()
                if fixture['lose_left'] and tick==2:
                    for w in car.wheels[::2]:w.tiles=[]
                before=observed_state(car)
                car.gas(0.);car.brake(brake);car.steer(fixture['steer']);car.step(.02)
                if ticks>=36:raise RuntimeError('TICK_CAP')
                ticks+=1;world.Step(.02,180,60)
                trace.append(dict(before={'velocity':before.velocity,'wheels':[w.__dict__ for w in before.wheels]},after_COM=com(car),hull_velocity=list(car.hull.linearVelocity),yaw=car.hull.angularVelocity,headings=[w.angle for w in car.wheels]))
            actual=math.hypot(*com(car));cases[name]=dict(error_m_s=actual-target,forecast_error_m_s=actual-prediction,hull_error_m_s=math.hypot(*car.hull.linearVelocity)-target)
            rows.append(dict(fixture=name,initial_planar=state.__dict__|{'linear':state.linear.__dict__|{'wheels':[w.__dict__ for w in state.linear.wheels]}},brake=brake,target=target,prediction=prediction,ticks=trace))
        finally:
            for b in list(world.bodies):world.DestroyBody(b)
            assert world.bodyCount==world.jointCount==0
            car=None;world=None;closed+=1
    values=[v['error_m_s'] for v in cases.values() if 'error_m_s' in v];abstentions=len(cases)-len(values)
    stats=lambda a:dict(count=len(a),RMSE=math.sqrt(sum(x*x for x in a)/len(a)) if a else None,max_abs=max(map(abs,a)) if a else None)
    new=stats(values);passed=bool(not abstentions and new['RMSE']<=.5*controls['scalar']['RMSE'] and new['max_abs']<=.15 and max(abs(v['hull_error_m_s']) for v in cases.values())<=.15)
    save(D/'bench-raw.json',rows)
    result=dict(status='PLANAR_GATE_PASS' if passed else 'PLANAR_CORRECTION_REJECTED_STOP',cases=cases,planar=new,prior_frozen=controls['response'],prior_scalar=controls['scalar'],abstentions=abstentions,paired_initial_inputs_exact=initial_exact,
        worlds=worlds,closed_worlds=closed,live_worlds=worlds-closed,raw_ticks=ticks,CPU_s_including_test_child=usage(),wall_s=time.perf_counter()-start,
        research_remaining=26027,reserve=84000,reserve_used=0,native_actions_resets_seeds_HOLDOUT_SEALED=0,
        source_sha256=c['source_sha256'],contacts_frozen_no_future_schedule_given_to_candidate=True,no_second_correction_or_tuning=True,scope='One mechanistic correction on fixed503 synthetic cases; no track or original501 evidence')
    guard();save(G/'retry/brake504_result.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':run()
