"""Confirmation after506 cap arithmetic stop; same candidate/fixtures/gates."""
import datetime,hashlib,json,math,resource,signal,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
from dataclasses import asdict
from retry.brake503_diagnostic import com
from retry.brake504_diagnostic import planar
from retry.brake504_planar import choose as fixed_choose
from retry.brake506_geometry import Geometry,contacts,choose,forecast

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response507-private')


def rect(x0,x1,y0,y1):return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]


def fixtures():
    base=dict(vx=0.,vy=80.,yaw=0.,steer=0.,extra=12.)
    return [(name,dict(base,**changes),roads) for name,changes,roads in [
        ('interior',dict(extra=0.),[rect(-10.,10.,-20.,25.)]),
        ('edge_exit',{},[rect(-10.,10.,-20.,2.6)]),
        ('edge_entry',{},[rect(-10.,10.,2.6,25.)]),
        ('gap_reentry',{},[rect(-10.,10.,-20.,2.6),rect(-10.,10.,5.2,25.)]),
        ('asym_side_exit',dict(vx=-15.,extra=0.),[rect(-.85,10.,-20.,25.)]),
        ('asym_steer',dict(vx=-10.,yaw=.3,steer=.25),[rect(-.85,10.,-20.,25.)])]]


def run():
    start=time.perf_counter();cpu=time.process_time();child0=resource.getrusage(resource.RUSAGE_CHILDREN)
    c=json.loads((G/'retry/brake507_contract.json').read_text());D.mkdir(mode=0o700,exist_ok=False)
    def save(p,value):
        data=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
        if sum(x.stat().st_size for x in D.iterdir())+len(data)>16*1024**2:raise RuntimeError('STORAGE_CAP')
        with p.open('xb') as f:f.write(data)
        p.chmod(0o600 if D in p.parents else 0o644)
    def usage():
        x=resource.getrusage(resource.RUSAGE_CHILDREN)
        return time.process_time()-cpu+x.ru_utime+x.ru_stime-child0.ru_utime-child0.ru_stime
    def guard(*args):
        if usage()>=60 or time.perf_counter()-start>=90:raise RuntimeError('RESOURCE_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,90)
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,60)
    for n,h in c['source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    budget=json.loads((G/'retry/brake505_result.json').read_text());assert (budget['research_remaining'],budget['reserve'],budget['reserve_used'])==(26027,84000,0)
    test=subprocess.run([sys.executable,'-m','unittest','retry.test_brake506','-v'],cwd=G,capture_output=True,text=True,timeout=30)
    save(D/'pure-tests.json',dict(returncode=test.returncode,stdout=test.stdout,stderr=test.stderr))
    if test.returncode:raise RuntimeError('PURE_GATE_NO_WORLD')
    guard();signal.setitimer(signal.ITIMER_PROF,max(.001,60-usage()))
    from Box2D.b2 import world as World,polygonShape,fixtureDef,polygonRadius
    from core.vendor.car_dynamics import Car
    from core.vendor.car_racing import VariablesContactDetector,FrictionDetector
    save(D/'PHYSICS_STARTED.json',dict(once=True,contract_sha256=hashlib.sha256((G/'retry/brake507_contract.json').read_bytes()).hexdigest()))
    counts=dict(worlds=0,closed=0,raw_ticks=0,zero_dt_contact_primes=0)
    def newworld():
        guard();assert counts['worlds']<17;counts['worlds']+=1
        return World(gravity=(0,0))
    def close(world,env=None):
        world.contactListener=None
        for b in list(world.bodies):world.DestroyBody(b)
        assert world.bodyCount==world.jointCount==0
        if env is not None:env.car=None
        counts['closed']+=1
        save(D/('closure-%02d.json'%counts['closed']),dict(counts))
    def prime(world):
        guard();assert counts['zero_dt_contact_primes']<17
        counts['zero_dt_contact_primes']+=1;world.Step(0.,180,60)
    def advance(world):
        guard();assert counts['raw_ticks']<84;counts['raw_ticks']+=1;world.Step(.02,180,60)
    def make_roads(world,polys):
        bodies=[];geometry=[]
        for i,poly in enumerate(polys):
            b=world.CreateStaticBody(fixtures=fixtureDef(shape=polygonShape(vertices=poly),isSensor=True))
            b.userData=b;b.road_friction=1.;b.road_visited=False;b.color=[0.,0.,0.];b.idx=i
            bodies.append(b);geometry.append(([tuple(b.GetWorldPoint(v)) for v in b.fixtures[0].shape.vertices],b.road_friction))
        return bodies,tuple(geometry)
    def members(wheels):return tuple(tuple(sorted(t.idx for t in w.tiles)) for w in wheels)
    def oracle(wheels,roads):
        return tuple(contacts([tuple(w.GetWorldPoint(v)) for v in w.fixtures[0].shape.vertices],roads,2*float(polygonRadius)) for w in wheels)
    # Probe sensor Collide timing without a vehicle/controller or track.
    world=newworld();probe=[];env=NS(road_color=[0.,0.,0.],reward=0.,track=[None],tile_visited_count=0,car=None)
    try:
        listener=FrictionDetector(env,.95);world.contactListener=listener
        road,geometry=make_roads(world,[rect(-5.,5.,0.,2.5)])
        wheel=world.CreateDynamicBody(position=(0.,-1.2),fixtures=fixtureDef(shape=polygonShape(box=(.28,.54)),density=.1))
        wheel.userData=wheel;wheel.tiles=set();wheel.linearVelocity=(0.,80.)
        prime(world)
        for i in range(4):
            before=oracle([wheel],geometry);advance(world)
            probe.append(dict(prepose=before,postpose=oracle([wheel],geometry),observed=members([wheel])))
    finally:close(world,env)
    save(D/'sensor-probe.json',probe)
    probe_pre=sum(a!=b for r in probe for a,b in zip(r['prepose'],r['observed']))
    probe_post=sum(a!=b for r in probe for a,b in zip(r['postpose'],r['observed']))
    if probe_pre or not probe_post:
        save(G/'retry/brake507_result.json',dict(status='SOURCE_SENSOR_TIMING_STOP',probe_pre_mismatches=probe_pre,probe_post_mismatches=probe_post,counts=counts));return
    raw=[];initials={}
    def batch(selected,holds,phase):
        output=[]
        for name,params,polys in selected:
            for arm in ('fixed504','geometry'):
                world=newworld();env=NS(road_color=[0.,0.,0.],reward=0.,track=[None]*len(polys),tile_visited_count=0,car=None)
                try:
                    listener=VariablesContactDetector(env,.95);world.contactListener=listener
                    road,geometry=make_roads(world,polys);car=Car(world,0.,0.,0.);env.car=car
                    center=com(car,True)
                    for b in [car.hull,*car.wheels]:
                        x,y=b.worldCenter[0]-center[0],b.worldCenter[1]-center[1]
                        b.linearVelocity=(params['vx']-params['yaw']*y,params['vy']+params['yaw']*x);b.angularVelocity=params['yaw']
                    for w in car.wheels:
                        e=w.GetWorldVector((0,1));w.omega=(e[0]*w.linearVelocity[0]+e[1]*w.linearVelocity[1]+params['extra'])/.54
                    prime(world)
                    initial=planar(car,params['steer']);initial_contacts=members(car.wheels)
                    identity=json.loads(json.dumps([asdict(initial),com(car,True),initial_contacts,geometry]))
                    key=(phase,name)
                    if arm=='fixed504':initials[key]=identity
                    elif initials[key]!=identity:raise RuntimeError('PAIRED_INITIAL_NOT_EXACT')
                    base_speed=math.hypot(*initial.linear.velocity);direction=tuple(v/base_speed for v in initial.linear.velocity)
                    all_ticks=[];metrics=[]
                    for hold in range(holds):
                        current=planar(car,params['steer']);tiles=members(car.wheels);target=base_speed-1.6*(hold+1)
                        geo=Geometry(current,com(car,True),geometry,tiles,400.*car.grass_friction_multiplier,2*float(polygonRadius))
                        try:brake,prediction=choose(geo,target) if arm=='geometry' else fixed_choose(current,target)
                        except ValueError as error:metrics.append(dict(abstention=str(error)));break
                        _,predicted=forecast(geo,brake)
                        if arm=='fixed504':predicted=[dict(contacts_used=tiles,method='CONTACT_FIXED') for _ in range(4)]
                        trace=[];model_mismatch=oracle_mismatch=postpose_mismatch=0
                        for tick in range(4):
                            used=members(car.wheels);pre_oracle=oracle(car.wheels,geometry)
                            model_mismatch+=sum(a!=b for a,b in zip(predicted[tick]['contacts_used'],used))
                            before=dict(center=com(car,True),headings=[w.angle for w in car.wheels],levers=planar(car,params['steer']).levers,tiles=used,oracle=pre_oracle)
                            car.gas(0.);car.brake(brake);car.steer(params['steer']);car.step(.02);advance(world)
                            after_tiles=members(car.wheels);after_oracle=oracle(car.wheels,geometry)
                            oracle_mismatch+=sum(a!=b for a,b in zip(pre_oracle,after_tiles));postpose_mismatch+=sum(a!=b for a,b in zip(after_oracle,after_tiles))
                            trace.append(dict(before=before,after_tiles=after_tiles,after_COM=com(car),center=com(car,True),hull_velocity=list(car.hull.linearVelocity),prediction=predicted[tick]))
                        end=math.hypot(*com(car));progress=.02*sum(sum(t['after_COM'][j]*direction[j] for j in range(2)) for t in trace)
                        transitions=sum(a!=b for t in trace for a,b in zip(t['before']['tiles'],t['after_tiles']))
                        entries=sum(bool(set(b)-set(a)) for t in trace for a,b in zip(t['before']['tiles'],t['after_tiles']))
                        exits=sum(bool(set(a)-set(b)) for t in trace for a,b in zip(t['before']['tiles'],t['after_tiles']))
                        asym=sum(any(bool(t['before']['tiles'][i])!=bool(t['before']['tiles'][i+1]) for i in (0,2)) for t in trace)
                        metrics.append(dict(error_m_s=end-target,hull_error_m_s=math.hypot(*car.hull.linearVelocity)-target,forecast_error_m_s=end-prediction,contact_mismatch_wheel_ticks=model_mismatch,prepose_oracle_mismatches=oracle_mismatch,postpose_oracle_mismatches=postpose_mismatch,transition_wheel_ticks=transitions,entry_events=entries,exit_events=exits,asymmetric_contact_samples=asym,projected_travel_m=progress))
                        all_ticks.extend(trace)
                    record=dict(phase=phase,fixture=name,arm=arm,holds=metrics)
                    output.append(record);raw.append(dict(**record,initial=identity,trace=all_ticks))
                    save(D/('world-%s-%s-%s.json'%(phase,name,arm)),raw[-1])
                finally:close(world,env)
        return output
    def decide(records):
        predicted=[m for r in records if r['arm']=='geometry' for m in r['holds'] if 'error_m_s' in m]
        abstentions=sum('abstention' in m for r in records for m in r['holds'])
        safe=bool(not abstentions and predicted and max(abs(m['error_m_s']) for m in predicted)<=.15 and max(abs(m['hull_error_m_s']) for m in predicted)<=.15)
        contact=bool(not abstentions and all(not m['contact_mismatch_wheel_ticks'] for m in predicted) and all(not m['prepose_oracle_mismatches'] for r in records for m in r['holds'] if 'error_m_s' in m))
        cost=bool(not abstentions and all(m['error_m_s']>=-.4 for m in predicted))
        interior=[r for r in records if r['fixture']=='interior']
        if interior and all(r['holds'] and 'projected_travel_m' in r['holds'][0] for r in interior):
            loss=interior[0]['holds'][0]['projected_travel_m']-interior[1]['holds'][0]['projected_travel_m'];cost=bool(cost and loss<=.016)
        elif interior:cost=False
        return dict(speed_gate=safe,contact_gate=contact,cost_gate=cost,pass_all=bool(safe and contact and cost),abstentions=abstentions)
    first=batch(fixtures(),1,'one_hold');gate=decide(first)
    observed={r['fixture']:r['holds'][0] for r in first if r['arm']=='geometry' and r['holds'] and 'error_m_s' in r['holds'][0]}
    coverage=bool(len(observed)==6 and observed['edge_exit']['exit_events']>0 and observed['edge_entry']['entry_events']>0 and observed['gap_reentry']['entry_events']>0 and observed['gap_reentry']['exit_events']>0 and any(observed[k]['asymmetric_contact_samples']>0 for k in ('asym_side_exit','asym_steer')))
    gate['physical_coverage_gate']=coverage;gate['pass_all']=bool(gate['pass_all'] and coverage)
    save(D/'first-phase-result.json',dict(gate=gate,records=first))
    follow=[]
    if gate['pass_all']:follow=batch([f for f in fixtures() if f[0] in ('gap_reentry','asym_steer')],2,'two_hold')
    save(D/'bench-raw.json',raw)
    result=dict(status='GEOMETRY_LOCAL_GATE_PASS' if gate['pass_all'] else 'GEOMETRY_CANDIDATE_REJECTED_STOP',one_hold_gate=gate,one_hold=first,two_hold=follow,two_hold_gate=decide(follow) if follow else None,
        probe_prepose_mismatches=probe_pre,probe_postpose_mismatches=probe_post,counts=counts,live_worlds=counts['worlds']-counts['closed'],
        CPU_s_including_test_child=usage(),wall_s=time.perf_counter()-start,research_remaining=26027,reserve=84000,reserve_used=0,native_actions_resets_seeds_HOLDOUT_SEALED=0,
        scope='New physical road-sensor geometry fixtures; never mixed with forced503 schedules; no track/lap/generalization qualification',future_actual_contacts_given_to_candidate=False,source_sha256=c['source_sha256'])
    if follow and not result['two_hold_gate']['pass_all']:result['status']='TWO_HOLD_GEOMETRY_REJECTED_STOP'
    guard();save(G/'retry/brake507_result.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':run()
