"""Actual effects gate then one identity-qualified short native DEV pair."""
import copy,datetime,hashlib,json,math,pickle,resource,signal,subprocess,sys,time
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
from retry.brake503_diagnostic import com,observed_state
from retry.brake509_adapter import context,brake_action
from retry.brake508_corridor import corridor,bounds,indexed_contacts,forecast
from retry.brake510_common import caps,native_roads,track_boundary,boundary_index,clearance
from retry.pixel_agent import PixelAgent

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response510-private')


def run():
    start=time.perf_counter();cpu=time.process_time();child0=resource.getrusage(resource.RUSAGE_CHILDREN)
    contract=json.loads((G/'retry/brake510_contract.json').read_text());case=json.loads((D/'approved-case-private.json').read_text())
    if (D/'PHYSICS_STARTED.json').exists():raise RuntimeError('NO_PHYSICS_RETRY')
    def ready(x):
        if isinstance(x,np.generic):return x.item()
        if isinstance(x,np.ndarray):return x.tolist()
        raise TypeError(type(x).__name__)
    def save(p,value):
        data=(json.dumps(value,default=ready,indent=2,allow_nan=False)+'\n').encode()
        files=list(D.iterdir())
        if len(files)>=1024 or sum(f.stat().st_size for f in files)+len(data)>32*1024**2:raise RuntimeError('STORAGE_CAP')
        with p.open('xb') as f:f.write(data)
        p.chmod(0o600 if D in p.parents else 0o644)
    def digest(value):return hashlib.sha256(json.dumps(value,default=ready,sort_keys=True).encode()).hexdigest()
    def usage():
        x=resource.getrusage(resource.RUSAGE_CHILDREN)
        return time.process_time()-cpu+x.ru_utime+x.ru_stime-child0.ru_utime-child0.ru_stime
    def guard(*a):
        if usage()>=180 or time.perf_counter()-start>=240:raise RuntimeError('RESOURCE_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(contract['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,240)
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,180)
    for n,h in contract['source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    assert hashlib.sha256((D/'approved-case-private.json').read_bytes()).hexdigest()==contract['case_private_sha256']
    assert caps()==contract['physical_caps']
    tests=subprocess.run([sys.executable,'-m','unittest','retry.test_brake509','retry.test_brake510','-v'],cwd=G,capture_output=True,text=True,timeout=40)
    save(D/'pure-tests.json',dict(returncode=tests.returncode,stdout=tests.stdout,stderr=tests.stderr))
    if tests.returncode:raise RuntimeError('PURE_GATE_NO_WORLD')
    guard();signal.setitimer(signal.ITIMER_PROF,max(.001,180-usage()))
    from Box2D.b2 import world as World,polygonShape,fixtureDef,polygonRadius
    from core.vendor.car_dynamics import Car
    from core.vendor.car_racing import CarRacing,VariablesContactDetector,TRACK_WIDTH
    from gymnasium.wrappers import TimeLimit
    from env_wrapper import CarEnvironment
    from local_runner import safe_act,safe_reset
    from damage import calculate_damage_effects
    skin=2*float(polygonRadius)
    save(D/'PHYSICS_STARTED.json',dict(once=True,contract_sha256=hashlib.sha256((G/'retry/brake510_contract.json').read_bytes()).hexdigest()))
    counts=dict(synthetic_worlds=0,synthetic_closed=0,synthetic_ticks=0,synthetic_zero=0,native_worlds=0,native_closed=0,native_resets=0,native_actions=0,native_raw_attempts=0,native_raw_completed=0)
    def tile_ids(car):return tuple(tuple(sorted(t.idx for t in w.tiles)) for w in car.wheels)
    def oracle(car,roads,index):return tuple(indexed_contacts([tuple(w.GetWorldPoint(v)) for v in w.fixtures[0].shape.vertices],roads,index,skin) for w in car.wheels)
    def nominal_target(root,nominal):
        mass=root.planar.linear.mass+4*1.6/.54**2
        return math.hypot(*root.planar.linear.velocity)-.08*float(nominal[2])*(4*1.6*15/(.02*.54))/mass
    synthetic=[]
    for damage in (0.,.4):
        effects=calculate_damage_effects(damage)
        for arm in ('reference','adapter'):
            guard();assert counts['synthetic_worlds']<4;counts['synthetic_worlds']+=1
            world=World(gravity=(0,0));env=None;rows=[]
            try:
                car=Car(world,0.,0.,0.,grass_friction_multiplier=.6);car.set_damage_effects(effects.grip_multiplier,effects.engine_multiplier,effects.steering_multiplier)
                center=com(car,True);steer=math.atan(3.24/40.)
                polygons,_,boundary=corridor(center[1],mixed=True);road=[];base=[]
                env=NS(car=car,road_color=[0.,0.,0.],reward=0.,track=[None]*len(polygons),tile_visited_count=0)
                listener=VariablesContactDetector(env,.95);world.contactListener=listener
                for i,(poly,mu) in enumerate(polygons):
                    b=world.CreateStaticBody(fixtures=fixtureDef(shape=polygonShape(vertices=poly),isSensor=True))
                    b.userData=b;b.road_friction=mu;b.road_visited=False;b.color=[0.,0.,0.];b.idx=i;road.append(b)
                    if mu==.35:base.append([tuple(b.GetWorldPoint(v)) for v in b.fixtures[0].shape.vertices])
                mesh=native_roads(road);mesh_index=bounds(mesh);base_index=bounds(tuple((p,1.) for p in base));edge_index=boundary_index(boundary)
                for b in [car.hull,*car.wheels]:
                    x,y=b.worldCenter[0]-center[0],b.worldCenter[1]-center[1];b.linearVelocity=(-1.5*y,60+1.5*x);b.angularVelocity=1.5
                for w in car.wheels:
                    e=w.GetWorldVector((0,1));w.omega=(e[0]*w.linearVelocity[0]+e[1]*w.linearVelocity[1])/.54
                counts['synthetic_zero']+=1;world.Step(0.,180,60)
                for hold in range(3):
                    nominal=np.array([-steer,.25 if hold==0 else 0.,0. if hold==0 else .03],np.float32)
                    root=context(car,road,nominal,skin=skin)
                    action,detail=brake_action(nominal,car,road,skin=skin) if arm=='adapter' else (nominal.copy(),dict(mode='REFERENCE'))
                    expected,sequence=forecast(root,float(action[2]),bounds(root.roads)) if hold else (None,None)
                    target=nominal_target(root,nominal) if hold else None
                    actual=[];mismatch=oracle_errors=0;minimum=float('inf')
                    for tick in range(4):
                        guard();before=oracle(car,mesh,mesh_index)
                        if sequence:
                            for a,b in zip(sequence[tick]['contacts_used'],tile_ids(car)):
                                f=lambda ids:max([400*.6*car.grip_multiplier,*[400*mesh[i][1]*car.grip_multiplier for i in ids]])
                                mismatch+=int(f(a)!=f(b))
                        car.gas(float(action[1]));car.brake(float(action[2]));car.steer(-float(action[0]));car.step(.02)
                        assert counts['synthetic_ticks']<48;counts['synthetic_ticks']+=1;world.Step(.02,180,60)
                        oracle_errors+=sum(a!=b for a,b in zip(before,tile_ids(car)))
                        margin=clearance(car,base,base_index,boundary,edge_index);minimum=min(minimum,margin)
                        tickrow=dict(damage=damage,arm=arm,hold=hold+1,tick=tick+1,speed=math.hypot(*com(car)),position=com(car,True),tiles=tile_ids(car),effects=[car.grip_multiplier,car.engine_multiplier,car.steering_multiplier],margin=margin)
                        save(D/('synthetic-tick-%03d.json'%counts['synthetic_ticks']),tickrow);actual.append(tickrow)
                    speed=math.hypot(*com(car));metric=dict(damage=damage,arm=arm,hold=hold+1,prediction_error_m_s=speed-math.hypot(*expected.planar.linear.velocity) if expected else None,
                        steady_request_residual_m_s=speed-target if target is not None else None,contact_mu_mismatches=mismatch,source_oracle_mismatches=oracle_errors,min_margin_m=minimum,
                        nominal_steer_gas_preserved=bool(np.array_equal(action[:2],nominal[:2])),nominal_brake=float(nominal[2]),applied_brake=float(action[2]),speed=speed)
                    save(D/('synthetic-hold-%s-%s-%d.json'%(damage,arm,hold)),dict(root=asdict(root),metric=metric));rows.append(metric);synthetic.append(metric)
            finally:
                world.contactListener=None
                for b in list(world.bodies):world.DestroyBody(b)
                assert world.bodyCount==world.jointCount==0
                if env is not None:env.car=None
                counts['synthetic_closed']+=1;car=None;world=None
                save(D/('synthetic-close-%02d.json'%counts['synthetic_closed']),dict(counts=counts,rows=rows))
    adapter=[r for r in synthetic if r['arm']=='adapter' and r['hold']>1]
    synth_pass=bool(len(synthetic)==12 and all(abs(r['prediction_error_m_s'])<=.15 and abs(r['steady_request_residual_m_s'])<=.15 and r['contact_mu_mismatches']==0 for r in adapter)
                    and all(r['source_oracle_mismatches']==0 and r['min_margin_m']>=.25 and r['nominal_steer_gas_preserved'] for r in synthetic))
    save(D/'synthetic-result.json',dict(passed=synth_pass,rows=synthetic,counts=dict(counts)))
    native=[];initial_identity=None
    if synth_pass:
        for arm in ('reference','adapter'):
            guard();assert counts['native_worlds']<2;counts['native_worlds']+=1
            raw=CarRacing(**case['base']);env=CarEnvironment(TimeLimit(raw,max_episode_steps=case['TimeLimit_max_episode_steps']),**case['wrapper'])
            original_reset=raw.reset;original_step=raw.step
            state=dict(phase='reset',resets=0,reset_ticks=0,action_ticks=0,actions=0,pred=None,flags=[],mesh=None,allrows=[],active=None)
            def guarded_reset(**kwargs):
                guard()
                if state['resets'] or counts['native_resets']>=2:raise RuntimeError('EXTRA_RESET_FORBIDDEN')
                state['resets']+=1;counts['native_resets']+=1
                save(D/('native-reset-charge-%s.json'%arm),dict(counts=counts))
                return original_reset(**kwargs)
            def observed_step(action):
                guard()
                if counts['native_raw_attempts']>=358:raise RuntimeError('NATIVE_RAW_CAP')
                if state['phase']=='reset' and state['reset_ticks']>=51:raise RuntimeError('RESET_RAW_CAP')
                if state['mesh'] is None:
                    state['mesh']=native_roads(raw.road);state['index']=bounds(state['mesh']);state['base']=[p for p,c in state['mesh']]
                    state['base_index']=state['index'];state['boundary']=track_boundary(raw.track,TRACK_WIDTH);state['edge_index']=boundary_index(state['boundary'])
                before=oracle(raw.car,state['mesh'],state['index']);used=tile_ids(raw.car)
                pre_effects=(raw.car.grip_multiplier,raw.car.engine_multiplier,raw.car.steering_multiplier)
                local=state['reset_ticks'] if state['phase']=='reset' else state['action_ticks']
                counts['native_raw_attempts']+=1
                output=original_step(action);counts['native_raw_completed']+=1
                if state['phase']=='reset':state['reset_ticks']+=1
                else:state['action_ticks']+=1
                errors=[]
                if before!=tile_ids(raw.car):errors.append('SOURCE_SENSOR_PHASE')
                if pre_effects!=(raw.car.grip_multiplier,raw.car.engine_multiplier,raw.car.steering_multiplier):errors.append('EFFECT_CHANGED_WITHIN_RAW')
                if state['active'] is not None:
                    if action is None or not np.array_equal(np.asarray(action),state['active'].astype(np.float64)):errors.append('FLOAT32_PAYLOAD')
                    if abs(raw.car.wheels[0].steer+float(state['active'][0]))>1e-7:errors.append('STEER_SIGN')
                if state['pred'] is not None:
                    i=state['action_ticks']-1
                    if i>=4:errors.append('HOLD_RAW_COUNT')
                    else:
                        grip=pre_effects[0];floor=400*raw.car.grass_friction_multiplier*grip
                        f=lambda ids:max([floor,*[400*state['mesh'][j][1]*grip for j in ids]])
                        if any(f(a)!=f(b) for a,b in zip(state['pred'][i]['contacts_used'],used)):errors.append('PREDICTED_FRICTION')
                margin=clearance(raw.car,state['base'],state['base_index'],state['boundary'],state['edge_index'])
                if margin<.25:errors.append('ROAD_MARGIN')
                if output[4].get('collision',False):errors.append('COLLISION')
                row=dict(phase=state['phase'],action=state['actions'],raw=counts['native_raw_completed'],time=raw.t,speed=math.hypot(*com(raw.car)),position=com(raw.car,True),tiles=tile_ids(raw.car),margin=margin,errors=errors,effects=pre_effects)
                save(D/('native-raw-%03d.json'%counts['native_raw_completed']),row);state['allrows'].append(row);state['flags'].extend(errors)
                return output
            raw.reset=guarded_reset;raw.step=observed_step
            rows=[];stop='MAX32_PREFIX';identity_pass=False
            try:
                obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']})
                assert state['reset_ticks']==51 and abs(raw.t-1.02)<1e-8
                assert obs.shape==(4,84,84) and obs.dtype==np.float32 and np.isfinite(obs).all() and 0<=obs.min()<=obs.max()<=1
                old=case['old_episode'];geom=digest(raw.track);obstacles=digest([[list(s.position),s.radius] for s in raw.track_variables.obstacles])
                if geom!=old['geometry_sha256_diagnostic_only'] or obstacles!=old['obstacles_sha256_diagnostic_only']:raise RuntimeError('OLD_INITIAL_GEOMETRY_OBSTACLE_IDENTITY')
                identity=digest(dict(geometry=geom,obstacles=obstacles,obs=hashlib.sha256(obs.tobytes()).hexdigest(),body=asdict(observed_state(raw.car)),position=com(raw.car,True),angle=raw.car.hull.angle,time=raw.t,RNG=raw.np_random.bit_generator.state))
                if initial_identity is None:initial_identity=identity
                elif identity!=initial_identity:raise RuntimeError('PAIRED_INITIAL_IDENTITY')
                identity_pass=True;save(D/('native-initial-%s.json'%arm),dict(identity=identity,geometry=geom,obstacles=obstacles))
                reference=PixelAgent(adaptive=True);safe_reset(reference,obs);state['phase']='action'
                for index in range(32):
                    guard()
                    if state['flags']:stop=state['flags'][0];break
                    nominal,valid=safe_act(reference,obs)
                    if not valid:stop='INVALID_NOMINAL';break
                    nominal=np.asarray(nominal,np.float32);committed=hashlib.sha256(pickle.dumps(vars(reference),protocol=5)).hexdigest()
                    try:
                        root=context(raw.car,raw.road,nominal,skin=skin)
                        if not np.isfinite([*root.planar.linear.velocity,*[w.omega for w in root.planar.linear.wheels]]).all():raise ValueError('NONFINITE_MODEL_INPUT')
                        action,detail=brake_action(nominal,raw.car,raw.road,skin=skin) if arm=='adapter' else (nominal.copy(),dict(mode='REFERENCE'))
                    except ValueError as error:
                        stop='INPUT:'+str(error)
                        save(D/('native-input-stop-%s.json'%arm),dict(error=stop,nominal=nominal.tolist(),speed=math.hypot(*com(raw.car)),body=asdict(observed_state(raw.car)),nominal_memory_digest=committed))
                        break
                    assert hashlib.sha256(pickle.dumps(vars(reference),protocol=5)).hexdigest()==committed and np.array_equal(nominal[:2],action[:2])
                    brake_only=bool(nominal[2]>0 and nominal[1]==0)
                    expected,sequence=forecast(root,float(action[2]),bounds(root.roads)) if brake_only else (None,None)
                    target=nominal_target(root,nominal) if brake_only else None
                    state['pred']=sequence;state['active']=action.copy();state['action_ticks']=0
                    assert counts['native_actions']<64;counts['native_actions']+=1;state['actions']+=1
                    save(D/('action-charge-%02d.json'%counts['native_actions']),dict(arm=arm,index=index+1,attempted_actions=counts['native_actions'],research_remaining=26027-counts['native_actions'],reserve=84000,reserve_used=0))
                    before_rows=len(state['allrows']);obs,reward,terminated,truncated,info=env.step(action)
                    if not(obs.shape==(4,84,84) and obs.dtype==np.float32 and np.isfinite(obs).all() and 0<=obs.min()<=obs.max()<=1):state['flags'].append('OBSERVATION_CONTRACT')
                    speed=math.hypot(*com(raw.car));e=calculate_damage_effects(env.damage.damage)
                    if (raw.car.grip_multiplier,raw.car.engine_multiplier,raw.car.steering_multiplier)!=(e.grip_multiplier,e.engine_multiplier,e.steering_multiplier):state['flags'].append('WRAPPER_DAMAGE_EFFECT')
                    prediction_error=speed-math.hypot(*expected.planar.linear.velocity) if expected and state['action_ticks']==4 else None
                    if prediction_error is not None and abs(prediction_error)>.15:state['flags'].append('PHYSICAL_PREDICTION_ERROR')
                    row=dict(index=index+1,nominal=nominal.tolist(),action=action.tolist(),brake_request=brake_only,changed=not np.array_equal(action,nominal),raw_ticks=state['action_ticks'],speed=speed,progress=info['progress'],damage=info['damage'],
                        minimum_margin_m=min(x['margin'] for x in state['allrows'][before_rows:]),physical_prediction_error_m_s=prediction_error,
                        steady_request_residual_m_s=speed-target if target is not None else None,flags=list(dict.fromkeys(state['flags'])),memory_once=True,observation_sha256=hashlib.sha256(obs.tobytes()).hexdigest())
                    save(D/('native-action-%s-%02d.json'%(arm,index+1)),row);rows.append(row)
                    if state['flags']:stop=state['flags'][0];break
                    if terminated or truncated:stop='ENV_TERMINAL_PREFIX';break
            except BaseException as error:
                stop='TECHNICAL:'+type(error).__name__+':'+str(error)
                save(D/('native-error-%s.json'%arm),dict(error=stop,counts=dict(counts)))
            finally:
                env.close();assert raw.world.bodyCount==raw.world.jointCount==0;counts['native_closed']+=1
                record=dict(arm=arm,stop=stop,initial_identity_pass=identity_pass,actions=state['actions'],reset_ticks=state['reset_ticks'],rows=rows)
                save(D/('native-close-%s.json'%arm),dict(record=record,counts=dict(counts)));native.append(record)
            if not identity_pass or stop.startswith('TECHNICAL:'):break
    def summarize(record,n=None):
        rows=record['rows'] if n is None else record['rows'][:n]
        pred=[abs(r['physical_prediction_error_m_s']) for r in rows if r['physical_prediction_error_m_s'] is not None]
        intent=[r['steady_request_residual_m_s'] for r in rows if r['steady_request_residual_m_s'] is not None]
        return dict(arm=record['arm'],stop=record['stop'],actions_charged=record['actions'],actions_observed=len(rows),reset_ticks=record['reset_ticks'],initial_identity_pass=record['initial_identity_pass'],
            final_speed_m_s=rows[-1]['speed'] if rows else None,final_progress=rows[-1]['progress'] if rows else None,min_margin_m=min((r['minimum_margin_m'] for r in rows),default=None),
            brake_requests=sum(r['brake_request'] for r in rows),changed_actions=sum(r['changed'] for r in rows),max_physical_prediction_error_m_s=max(pred,default=None),
            steady_request_mean_residual_m_s=sum(intent)/len(intent) if intent else None,max_steady_request_abs_residual_m_s=max(map(abs,intent),default=None))
    common=min((len(a['rows']) for a in native),default=0) if len(native)==2 else 0
    for i in range(common):
        if any(a['rows'][i]['raw_ticks']!=4 for a in native):common=i;break
    save(D/'native-full-records-private.json',native)
    result=dict(status='NATIVE_PREFIX_COMPLETED' if len(native)==2 and all(r['stop']=='MAX32_PREFIX' for r in native) else ('NATIVE_LIMITED_STOP' if native else 'SYNTHETIC_GATE_STOP'),synthetic_gate_pass=synth_pass,synthetic=synthetic,native=[summarize(a) for a in native],common_full_hold_prefix_actions=common,common_prefix=[summarize(a,common) for a in native] if common else [],counts=counts,
        research_remaining=26027-counts['native_actions'],reserve=84000,reserve_used=0,CPU_s_including_test_child=usage(),wall_s=time.perf_counter()-start,
        native_brake_requests=sum(r['brake_request'] for a in native for r in a['rows']),native_changed_actions=sum(r['changed'] for a in native if a['arm']=='adapter' for r in a['rows']),
        case_source_commit=case['source_commit'],case_index=case['case_index'],old_and_paired_identity_verified=bool(len(native)==2 and all(r['initial_identity_pass'] for r in native)),
        scope='Known DEV initial-case diagnostic; reference is new frozen public PixelAgent(adaptive), not old starter or champion replay. Exact state/map privilege for brake adapter; no score/11s/generalization claim.',source_sha256=contract['source_sha256'])
    result['brake_control_change_observed']=bool(result['native_changed_actions'])
    if native and not result['native_brake_requests'] and result['status']=='NATIVE_PREFIX_COMPLETED':result['status']='NATIVE_PREFIX_NO_BRAKE_EVIDENCE'
    save(D/'budget510-final-private.json',dict(attempted_actual_actions=counts['native_actions'],actual_resets=counts['native_resets'],actual_raw_completed=counts['native_raw_completed'],research_remaining=result['research_remaining'],reserve=84000,reserve_used=0))
    guard();save(G/'retry/brake510_result.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('synthetic','native')},indent=2))


if __name__=='__main__':run()
