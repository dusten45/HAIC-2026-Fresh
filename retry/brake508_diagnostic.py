"""Eight-hold curved-corridor test; closed braking and open model shadows."""
import datetime,hashlib,json,math,resource,signal,subprocess,sys,time
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace as NS
from retry.brake503_diagnostic import com,observed_state
from retry.brake504_diagnostic import planar
from retry.brake504_planar import choose as fixed_choose
from retry.brake506_geometry import Geometry,polygon_distance
from retry.brake508_corridor import budget,corridor,bounds,indexed_contacts,inside,choose,forecast

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response508-private')


def run():
    started=time.perf_counter();cpu=time.process_time();child0=resource.getrusage(resource.RUSAGE_CHILDREN)
    c=json.loads((G/'retry/brake508_contract.json').read_text());D.mkdir(mode=0o700,exist_ok=False)
    def save(p,value):
        data=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
        files=list(D.iterdir())
        if len(files)>=256 or sum(x.stat().st_size for x in files)+len(data)>16*1024**2:raise RuntimeError('STORAGE_CAP')
        with p.open('xb') as f:f.write(data)
        p.chmod(0o600 if D in p.parents else 0o644)
    def usage():
        x=resource.getrusage(resource.RUSAGE_CHILDREN)
        return time.process_time()-cpu+x.ru_utime+x.ru_stime-child0.ru_utime-child0.ru_stime
    def guard(*a):
        if usage()>=90 or time.perf_counter()-started>=120:raise RuntimeError('RESOURCE_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,120)
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,90)
    for n,h in c['source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    assert budget()==c['physical_budget']
    prior=json.loads((G/'retry/brake507_result.json').read_text());assert (prior['research_remaining'],prior['reserve'],prior['reserve_used'])==(26027,84000,0)
    tests=subprocess.run([sys.executable,'-m','unittest','retry.test_brake508','-v'],cwd=G,capture_output=True,text=True,timeout=30)
    save(D/'pure-tests.json',dict(returncode=tests.returncode,stdout=tests.stdout,stderr=tests.stderr))
    if tests.returncode:raise RuntimeError('PURE_GATE_NO_WORLD')
    guard();signal.setitimer(signal.ITIMER_PROF,max(.001,90-usage()))
    from Box2D.b2 import world as World,fixtureDef,polygonShape,polygonRadius
    from core.vendor.car_dynamics import Car
    from core.vendor.car_racing import VariablesContactDetector
    save(D/'PHYSICS_STARTED.json',dict(once=True,contract_sha256=hashlib.sha256((G/'retry/brake508_contract.json').read_bytes()).hexdigest()))
    counters=dict(worlds=0,closed=0,positive_ticks=0,zero_dt_primes=0);records=[];pair={}
    force_line=next(i+1 for i,line in enumerate((G/'core/vendor/car_dynamics.py').read_text().splitlines()) if 'w.omega -= dt * f_force' in line)
    def tiles(car):return tuple(tuple(sorted(t.idx for t in w.tiles)) for w in car.wheels)
    def actual_oracle(car,roads,index,skin):
        return tuple(indexed_contacts([tuple(w.GetWorldPoint(v)) for v in w.fixtures[0].shape.vertices],roads,index,skin) for w in car.wheels)
    def effective(ids,roads):return max([140.,*[400.*roads[i][1] for i in ids]])
    def clearance(car,base,boundary):
        minimum=float('inf')
        for b in [car.hull,*car.wheels]:
            for fixture in b.fixtures:
                p=[tuple(b.GetWorldPoint(v)) for v in fixture.shape.vertices]
                distance=min(polygon_distance(p,[a,b]) for a,b in boundary)
                if not all(any(inside(v,q) for q in base) for v in p):distance=-distance
                minimum=min(minimum,distance)
        return minimum
    for case in ('uniform','material_stripes'):
        for arm in ('fixed504','geometry'):
            guard();assert counters['worlds']<4;counters['worlds']+=1;world=World(gravity=(0,0));env=None;car=None
            world_rows=[];world_status='COMPLETE'
            try:
                car=Car(world,0.,0.,0.,grass_friction_multiplier=.35);steer=math.atan(3.24/40.)
                for w in car.wheels[:2]:w.angle=steer
                center=com(car,True);origin_y=center[1];mixed=case=='material_stripes'
                generated,base_original,boundary=corridor(origin_y,mixed);roads=[];base=[]
                env=NS(car=car,road_color=[0.,0.,0.],reward=0.,track=[None]*len(generated),tile_visited_count=0)
                listener=VariablesContactDetector(env,.95);world.contactListener=listener
                for i,(poly,mu) in enumerate(generated):
                    b=world.CreateStaticBody(fixtures=fixtureDef(shape=polygonShape(vertices=poly),isSensor=True))
                    b.userData=b;b.road_friction=mu;b.road_visited=False;b.color=[0.,0.,0.];b.idx=i
                    native=[tuple(b.GetWorldPoint(v)) for v in b.fixtures[0].shape.vertices];roads.append((native,mu))
                    if not mixed or mu==.35:base.append(native)
                roads=tuple(roads);index=bounds(roads);skin=2*float(polygonRadius)
                for b in [car.hull,*car.wheels]:
                    x,y=b.worldCenter[0]-center[0],b.worldCenter[1]-center[1]
                    b.linearVelocity=(-1.5*y,60.+1.5*x);b.angularVelocity=1.5
                for w in car.wheels:
                    e=w.GetWorldVector((0,1));w.omega=(e[0]*w.linearVelocity[0]+e[1]*w.linearVelocity[1])/.54
                assert counters['zero_dt_primes']<4;counters['zero_dt_primes']+=1;world.Step(0.,180,60)
                initial=Geometry(planar(car,steer),com(car,True),roads,tiles(car),140.,skin)
                ident=json.loads(json.dumps(asdict(initial)))
                if arm=='fixed504':pair[case]=ident
                elif pair[case]!=ident:raise RuntimeError('INITIAL_PAIR_MISMATCH')
                shadow=initial;initial_arc=40.*math.atan2(center[1]-origin_y,center[0]+40.)
                initial_speed=math.hypot(*com(car))
                for hold in range(8):
                    guard();root=Geometry(planar(car,steer),com(car,True),roads,tiles(car),140.,skin);target=initial_speed-.8*(hold+1)
                    try:brake,prediction=choose(root,target,index) if arm=='geometry' else fixed_choose(root.planar,target)
                    except ValueError as error:world_status='ABSTAIN:'+str(error);break
                    closed,closed_rows=forecast(root,brake,index,geometry=arm=='geometry')
                    shadow,shadow_rows=forecast(shadow,brake,index,geometry=arm=='geometry')
                    trace=[];mu_mismatch=tile_mismatch=oracle_mismatch=open_mu=material_changes=0;min_clear=float('inf');brake_work=0.
                    for tick in range(4):
                        guard();used=tiles(car);before=observed_state(car);oracle=actual_oracle(car,roads,index,skin);forces=[]
                        tile_mismatch+=sum(a!=b for a,b in zip(closed_rows[tick]['contacts_used'],used))
                        mu_mismatch+=sum(effective(a,roads)!=effective(b,roads) for a,b in zip(closed_rows[tick]['contacts_used'],used))
                        open_mu+=sum(effective(a,roads)!=effective(b,roads) for a,b in zip(shadow_rows[tick]['contacts_used'],used))
                        def tracer(frame,event,arg):
                            if frame.f_code is Car.step.__code__:
                                if event=='line' and frame.f_lineno==force_line:
                                    f=frame.f_locals;w=f['w'];e=w.GetWorldVector((0,1));n=w.GetWorldVector((1,0))
                                    forces.append(dict(wheel=car.wheels.index(w),omega_braked=w.omega,vector=[float(f['f_force']*e[j]+f['p_force']*n[j]) for j in range(2)]))
                                return tracer
                            return None
                        car.gas(0.);car.brake(brake);car.steer(steer);sys.settrace(tracer)
                        try:car.step(.02)
                        finally:sys.settrace(None)
                        assert len(forces)==4
                        omega_after=[w.omega for w in car.wheels]
                        brake_work+=sum(.5*1.6*(before.wheels[f['wheel']].omega**2-f['omega_braked']**2) for f in forces)
                        assert counters['positive_ticks']<128;counters['positive_ticks']+=1;world.Step(.02,180,60)
                        oracle_mismatch+=sum(a!=b for a,b in zip(oracle,tiles(car)))
                        material_changes+=sum(effective(a,roads)!=effective(b,roads) for a,b in zip(used,tiles(car)))
                        margin=clearance(car,base,boundary);min_clear=min(min_clear,margin)
                        row=dict(case=case,arm=arm,hold=hold+1,tick=tick+1,before=asdict(before),forces=forces,omega_after=omega_after,
                            used_contacts=used,after_contacts=tiles(car),after_COM=com(car),center=com(car,True),angle=car.hull.angle,yaw=car.hull.angularVelocity,
                            sigma=sum(com(car)[j]*(-math.sin(math.atan2(com(car,True)[1]-origin_y,com(car,True)[0]+40.)),math.cos(math.atan2(com(car,True)[1]-origin_y,com(car,True)[0]+40.)))[j] for j in range(2)),clearance_m=margin)
                        save(D/('tick-%03d.json'%counters['positive_ticks']),row);trace.append(row)
                    current=com(car,True);speed=math.hypot(*com(car));arc=40.*math.atan2(current[1]-origin_y,current[0]+40.)-initial_arc
                    metric=dict(case=case,arm=arm,hold=hold+1,target_error_m_s=speed-target,closed_speed_error_m_s=speed-prediction,
                        open_speed_error_m_s=speed-math.hypot(*shadow.planar.linear.velocity),closed_position_error_m=math.dist(current,closed.center),open_position_error_m=math.dist(current,shadow.center),
                        closed_mu_mismatches=mu_mismatch,closed_tile_mismatches=tile_mismatch,open_mu_mismatches=open_mu,source_oracle_mismatches=oracle_mismatch,material_transitions=material_changes,
                        min_sampled_clearance_m=min_clear,brake_work_J=brake_work,brake=brake,arc_progress_m=arc,norm_minus_sigma_m_s=speed-trace[-1]['sigma'])
                    save(D/('hold-%s-%s-%02d.json'%(case,arm,hold+1)),dict(root=asdict(root),brake=brake,target=target,metric=metric,ticks=trace))
                    world_rows.append(metric);records.append(metric)
            except BaseException as error:
                world_status='TECHNICAL_STOP:'+type(error).__name__;raise
            finally:
                sys.settrace(None);world.contactListener=None
                for b in list(world.bodies):world.DestroyBody(b)
                assert world.bodyCount==world.jointCount==0
                if env is not None:env.car=None
                counters['closed']+=1;car=None;world=None
                save(D/('world-%s-%s.json'%(case,arm)),dict(status=world_status,rows=world_rows,counters=dict(counters)))
    geometry=[r for r in records if r['arm']=='geometry'];baseline=[r for r in records if r['arm']=='fixed504']
    ends={(name,arm):next((r['arc_progress_m'] for r in reversed(records) if r['case']==name and r['arm']==arm),None) for name in ('uniform','material_stripes') for arm in ('fixed504','geometry')}
    losses={name:ends[name,'fixed504']-ends[name,'geometry'] if ends[name,'fixed504'] is not None and ends[name,'geometry'] is not None else None for name in ('uniform','material_stripes')}
    complete=len(records)==32
    safety=bool(complete and min(r['min_sampled_clearance_m'] for r in geometry)>=.25)
    speed=bool(complete and max(abs(r['target_error_m_s']) for r in geometry)<=.15 and max(abs(r['closed_speed_error_m_s']) for r in geometry)<=.15)
    coverage=bool(sum(r['material_transitions'] for r in geometry if r['case']=='material_stripes')>=4)
    contact=bool(complete and coverage and sum(r['closed_mu_mismatches'] for r in geometry)==0 and sum(r['source_oracle_mismatches'] for r in records)==0)
    cost=bool(complete and min(r['target_error_m_s'] for r in geometry)>=-.2 and all(losses[n]<=.005*next(r['arc_progress_m'] for r in reversed(baseline) if r['case']==n) for n in losses))
    result=dict(status='CURVED_CORRIDOR_LOCAL_PASS' if safety and speed and contact and cost else 'CURVED_CORRIDOR_REJECTED',gates=dict(safety=safety,speed=speed,contact=contact,cost=cost,complete=complete),
        records=records,progress_loss_vs504_m=losses,counters=counters,CPU_s_including_test_child=usage(),wall_s=time.perf_counter()-started,
        research_remaining=26027,reserve=84000,reserve_used=0,native_actions_resets_seeds_HOLDOUT_SEALED=0,
        scope='Two fixed synthetic curved roads, exact map and full current dynamics privilege; braking feedback, identical constant steering; no lap or pixel qualification',open_prediction_receives='Executed command only; never current/future actual state after root',source_sha256=c['source_sha256'])
    guard();save(G/'retry/brake508_result.json',result);print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))


if __name__=='__main__':run()
