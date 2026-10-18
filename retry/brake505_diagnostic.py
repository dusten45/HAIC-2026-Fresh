"""Same nine hidden-event fixtures, robust contact family, cost gates fixed."""
import datetime,hashlib,json,math,resource,signal,subprocess,sys,time
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace as NS
from retry.brake503_diagnostic import fixtures,com,observed_state
from retry.brake504_diagnostic import planar
from retry.brake505_uncertainty import choose

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response505-private');OLD=Path('/workspace/haic-response504-private')


def progress(ticks,direction,key):
    return .02*sum(sum(t[key][j]*direction[j] for j in range(2)) for t in ticks)


def run():
    start=time.perf_counter();cpu=time.process_time();children=resource.getrusage(resource.RUSAGE_CHILDREN)
    contract=json.loads((G/'retry/brake505_contract.json').read_text());D.mkdir(mode=0o700,exist_ok=False)
    def save(p,value):
        data=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
        if sum(x.stat().st_size for x in D.iterdir())+len(data)>16*1024**2:raise RuntimeError('STORAGE_CAP')
        with p.open('xb') as f:f.write(data)
        p.chmod(0o600 if D in p.parents else 0o644)
    def usage():
        r=resource.getrusage(resource.RUSAGE_CHILDREN)
        return time.process_time()-cpu+r.ru_utime+r.ru_stime-children.ru_utime-children.ru_stime
    def guard(*args):
        if usage()>=60 or time.perf_counter()-start>=90:raise RuntimeError('RESOURCE_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(contract['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,60)
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,90)
    for n,h in contract['source_sha256'].items():
        assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    assert hashlib.sha256((OLD/'bench-raw.json').read_bytes()).hexdigest()==contract['old504_raw_sha256']
    old=json.loads((OLD/'bench-raw.json').read_text());prior=json.loads((G/'retry/brake504_result.json').read_text())
    assert (prior['research_remaining'],prior['reserve'],prior['reserve_used'])==(26027,84000,0)
    tests=subprocess.run([sys.executable,'-m','unittest','retry.test_brake505','-v'],cwd=G,capture_output=True,text=True,timeout=30)
    save(D/'pure-tests.json',dict(returncode=tests.returncode,stdout=tests.stdout,stderr=tests.stderr))
    if tests.returncode:raise RuntimeError('PURE_GATE_NO_WORLD')
    guard();signal.setitimer(signal.ITIMER_PROF,max(.001,60-usage()))
    from Box2D.b2 import world as World
    from core.vendor.car_dynamics import Car
    save(D/'PHYSICS_STARTED.json',dict(once=True,contract_sha256=hashlib.sha256((G/'retry/brake505_contract.json').read_bytes()).hexdigest()))
    worlds=closed=tickcount=0;rows=[];cases={};blind={};initial_exact=0
    for name,fixture in fixtures():
        guard();assert worlds<9;worlds+=1;world=World(gravity=(0,0));car=None
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
            state=planar(car,fixture['steer']);reference=next(r for r in old if r['fixture']==name)
            current=json.loads(json.dumps(asdict(state)))
            if current!=reference['initial_planar']:raise RuntimeError('INITIAL_NOT_EXACT')
            initial_exact+=1;target=reference['target'];floors=(400.*car.grass_friction_multiplier*car.grip_multiplier,)*4
            # Only current state/target/source grass bound enter the candidate.
            try:brake,bounds=choose(state,target,floors)
            except ValueError as error:cases[name]=dict(abstention=str(error));continue
            key=hashlib.sha256(json.dumps([current,target,floors],sort_keys=True).encode()).hexdigest()
            if key in blind and blind[key]!=brake:raise RuntimeError('SCHEDULE_BLINDNESS_FAILURE')
            blind[key]=brake;trace=[]
            direction=tuple(v/math.hypot(*state.linear.velocity) for v in state.linear.velocity)
            for tick in range(4):
                guard()
                if fixture['lose_left'] and tick==2:
                    for w in car.wheels[::2]:w.tiles=[]
                car.gas(0.);car.brake(brake);car.steer(fixture['steer']);car.step(.02)
                assert tickcount<36;tickcount+=1;world.Step(.02,180,60)
                trace.append(dict(after_COM=com(car),hull_velocity=list(car.hull.linearVelocity),yaw=car.hull.angularVelocity,joints=[w.joint.angle for w in car.wheels]))
            end=math.hypot(*com(car));old_end=math.hypot(*reference['ticks'][-1]['after_COM'])
            extra_distance=progress(reference['ticks'],direction,'after_COM')-progress(trace,direction,'after_COM')
            cases[name]=dict(error_m_s=end-target,overspeed_m_s=max(0.,end-target),excess_braking_m_s=max(0.,target-end),
                progress_proxy_loss_vs504_m=extra_distance,brake_change_vs504=brake-reference['brake'],
                yaw_peak_rad_s=max(abs(t['yaw']) for t in trace),baseline_yaw_peak_rad_s=max(abs(t['yaw']) for t in reference['ticks']),
                positive_progress=all(sum(t['after_COM'][j]*direction[j] for j in range(2))>0 for t in trace),model_range_width_m_s=bounds['max_end_speed']-bounds['min_end_speed'],
                max_predicted_target_excess_m_s=bounds['max_end_speed']-target,scenarios=bounds['scenarios'],synthetic_hidden_event=fixture['lose_left'])
            rows.append(dict(fixture=name,initial=current,target=target,brake=brake,range=bounds,ticks=trace))
        finally:
            for b in list(world.bodies):world.DestroyBody(b)
            assert world.bodyCount==world.jointCount==0
            car=None;world=None;closed+=1
    executed=[v for v in cases.values() if 'error_m_s' in v];quiet=[v for v in executed if not v['synthetic_hidden_event']]
    abstentions=len(cases)-len(executed);maxover=max((v['overspeed_m_s'] for v in executed),default=0.)
    maxbrake=max((v['excess_braking_m_s'] for v in quiet),default=0.);maxloss=max((v['progress_proxy_loss_vs504_m'] for v in quiet),default=0.)
    safe=bool(not abstentions and maxover<=.15 and all(v['positive_progress'] for v in executed))
    economical=bool(not abstentions and maxbrake<=.4 and maxloss<=.016)
    save(D/'bench-raw.json',rows)
    result=dict(status='LOCAL_SAFETY_AND_COST_GATE_PASS' if safe and economical else 'CONTACT_UNCERTAINTY_CANDIDATE_REJECTED',
        end_speed_safety_gate=safe,no_event_braking_cost_gate=economical,abstentions=abstentions,cases=cases,
        maximum_overspeed_m_s=maxover,maximum_no_event_excess_braking_m_s=maxbrake,maximum_no_event_progress_proxy_loss_m=maxloss,
        target_RMSE_m_s=math.sqrt(sum(v['error_m_s']**2 for v in executed)/len(executed)) if executed else None,
        paired_initial_inputs_exact=initial_exact,unique_current_input_groups=len(blind),identical_current_inputs_produced_identical_commands=True,
        worlds=worlds,closed_worlds=closed,live_worlds=worlds-closed,raw_ticks=tickcount,CPU_s_including_test_child=usage(),wall_s=time.perf_counter()-start,
        research_remaining=26027,reserve=84000,reserve_used=0,native_actions_resets_seeds_HOLDOUT_SEALED=0,
        source_sha256=contract['source_sha256'],geometry_available_to_candidate=False,future_schedule_or_trace_given_to_candidate=False,
        scope='One fixed hidden-event synthetic bench; uncertainty family is not a track guarantee; no whole-lap improvement claim')
    guard();save(G/'retry/brake505_result.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':run()
