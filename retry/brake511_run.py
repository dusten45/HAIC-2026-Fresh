"""Known DEV small physical speed-step pair, all actual calls precharged."""
import datetime,hashlib,json,math,pickle,resource,signal,subprocess,sys,time
from pathlib import Path
from dataclasses import asdict
import numpy as np
from retry.brake503_diagnostic import com,observed_state
from retry.brake509_adapter import context
from retry.brake508_corridor import bounds,indexed_contacts,forecast
from retry.brake510_common import native_roads,track_boundary,boundary_index,clearance
from retry.brake511_control import Reference,caps,boundary,command,PREFIX,DROP

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response511-private')


def run():
    start=time.perf_counter();cpu=time.process_time();child0=resource.getrusage(resource.RUSAGE_CHILDREN)
    c=json.loads((G/'retry/brake511_execution_contract.json').read_text());case=json.loads((D/'approved-case-private.json').read_text())
    if (D/'PHYSICS_STARTED.json').exists():raise RuntimeError('NO_RETRY')
    def ready(x):
        if isinstance(x,np.generic):return x.item()
        if isinstance(x,np.ndarray):return x.tolist()
        raise TypeError(type(x).__name__)
    def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,default=ready).encode()).hexdigest()
    def save(p,value):
        data=(json.dumps(value,default=ready,indent=2,allow_nan=False)+'\n').encode();files=list(D.iterdir())
        if len(files)>=1024 or sum(f.stat().st_size for f in files)+len(data)>32*1024**2:raise RuntimeError('STORAGE_CAP')
        with p.open('xb') as f:f.write(data)
        p.chmod(0o600 if D in p.parents else 0o644)
    def usage():
        x=resource.getrusage(resource.RUSAGE_CHILDREN);return time.process_time()-cpu+x.ru_utime+x.ru_stime-child0.ru_utime-child0.ru_stime
    def guard(*a):
        if usage()>=180 or time.perf_counter()-start>=240:raise RuntimeError('RESOURCE_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,180)
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,240)
    for n,h in c['source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    assert caps()==c['physical_caps']
    assert hashlib.sha256((D/'approved-case-private.json').read_bytes()).hexdigest()==c['case_private_sha256']
    old=json.loads((G/'retry/brake510_result.json').read_text());assert (old['research_remaining'],old['reserve'],old['reserve_used'])==(25963,84000,0)
    historical=json.loads(Path('/workspace/haic-response510-private/native-full-records-private.json').read_text())[0]['rows'][:24]
    prior_initial=json.loads(Path('/workspace/haic-response510-private/native-initial-reference.json').read_text())['identity']
    tests=subprocess.run([sys.executable,'-m','unittest','retry.test_brake511','-v'],cwd=G,capture_output=True,text=True,timeout=30)
    save(D/'pure-tests-corrected.json',dict(returncode=tests.returncode,stdout=tests.stdout,stderr=tests.stderr))
    if tests.returncode:raise RuntimeError('PURE_GATE_NO_WORLD')
    guard();signal.setitimer(signal.ITIMER_PROF,max(.001,180-usage()))
    from core.vendor.car_racing import CarRacing,TRACK_WIDTH
    from core.vendor.car_dynamics import Car
    from Box2D.b2 import polygonRadius
    from gymnasium.wrappers import TimeLimit
    from env_wrapper import CarEnvironment
    from local_runner import safe_act,safe_reset
    from damage import calculate_damage_effects
    save(D/'PHYSICS_STARTED.json',dict(once=True,contract_sha256=hashlib.sha256((G/'retry/brake511_execution_contract.json').read_bytes()).hexdigest()))
    counters=dict(worlds=0,closed=0,resets=0,actions=0,raw_attempts=0,raw_completed=0)
    pair_initial=None;pair_trigger=None;native=[];skin=2*float(polygonRadius)
    force_line=next(i+1 for i,line in enumerate((G/'core/vendor/car_dynamics.py').read_text().splitlines()) if 'w.omega -= dt * f_force' in line)
    def ids(car):return tuple(tuple(sorted(t.idx for t in w.tiles)) for w in car.wheels)
    for arm in ('steady','response'):
        guard();assert counters['worlds']<2;counters['worlds']+=1
        raw=CarRacing(**case['base']);env=CarEnvironment(TimeLimit(raw,max_episode_steps=case['TimeLimit_max_episode_steps']),**case['wrapper'])
        oldreset=raw.reset;oldstep=raw.step
        state=dict(phase='reset',resets=0,reset_ticks=0,action_ticks=0,actions=0,braking=False,goal=None,pred=None,active=None,flags=[],mesh=None,ticks=[],distance=0.,brake_distance=0.,brake_work=0.)
        def reset(**kwargs):
            guard()
            if state['resets'] or counters['resets']>=2:raise RuntimeError('EXTRA_RESET')
            state['resets']+=1;counters['resets']+=1;save(D/('reset-charge-%s.json'%arm),dict(counters))
            return oldreset(**kwargs)
        def step(action):
            guard()
            if counters['raw_attempts']>=422:raise RuntimeError('RAW_CAP')
            if state['phase']=='reset' and state['reset_ticks']>=51:raise RuntimeError('RESET_RAW_CAP')
            if state['mesh'] is None:
                state['mesh']=native_roads(raw.road);state['index']=bounds(state['mesh']);state['base']=[p for p,mu in state['mesh']]
                state['edge']=track_boundary(raw.track,TRACK_WIDTH);state['edgeindex']=boundary_index(state['edge'])
                save(D/('map-%s-private.json'%arm),dict(roads=state['mesh'],boundary=state['edge']))
            current=observed_state(raw.car);position=com(raw.car,True);used=ids(raw.car)
            actual_geometry=tuple(indexed_contacts([tuple(w.GetWorldPoint(v)) for v in w.fixtures[0].shape.vertices],state['mesh'],state['index'],skin) for w in raw.car.wheels)
            effects=(raw.car.grip_multiplier,raw.car.engine_multiplier,raw.car.steering_multiplier);forces=[]
            def trace(frame,event,arg):
                if frame.f_code is Car.step.__code__:
                    if event=='line' and frame.f_lineno==force_line:
                        x=frame.f_locals;w=x['w'];e=w.GetWorldVector((0,1));n=w.GetWorldVector((1,0))
                        forces.append(dict(wheel=raw.car.wheels.index(w),omega_braked=w.omega,vector=[float(x['f_force']*e[j]+x['p_force']*n[j]) for j in range(2)]))
                    return trace
                return None
            counters['raw_attempts']+=1
            if state['braking']:sys.settrace(trace)
            try:q=oldstep(action)
            finally:sys.settrace(None)
            counters['raw_completed']+=1
            if state['phase']=='reset':state['reset_ticks']+=1
            else:state['action_ticks']+=1
            errors=[]
            if actual_geometry!=ids(raw.car):errors.append('SOURCE_SENSOR_PHASE')
            if effects!=(raw.car.grip_multiplier,raw.car.engine_multiplier,raw.car.steering_multiplier):errors.append('EFFECT_WITHIN_RAW')
            if state['active'] is not None and (action is None or not np.array_equal(action,state['active'].astype(np.float64))):errors.append('ACTION_PAYLOAD')
            if state['pred'] is not None:
                i=state['action_ticks']-1
                if i>=4:errors.append('HOLD_TICKS')
                else:
                    mu=lambda t:max([400*raw.car.grass_friction_multiplier*effects[0],*[400*state['mesh'][j][1]*effects[0] for j in t]])
                    if any(mu(a)!=mu(b) for a,b in zip(state['pred'][i]['contacts_used'],used)):errors.append('PREDICTED_FRICTION')
            margin=clearance(raw.car,state['base'],state['index'],state['edge'],state['edgeindex'])
            if margin<.25:errors.append('ROAD_MARGIN')
            if q[4].get('collision',False):errors.append('COLLISION')
            if state['phase']=='action':state['distance']+=math.dist(position,com(raw.car,True))
            if state['braking']:
                assert len(forces)==4
                state['brake_distance']+=math.dist(position,com(raw.car,True))
                state['brake_work']+=sum(.8*(current.wheels[f['wheel']].omega**2-f['omega_braked']**2) for f in forces)
            row=dict(arm=arm,phase=state['phase'],action=state['actions'],braking=state['braking'],time=raw.t,before=asdict(current),before_position=position,used_contacts=used,
                speed=math.hypot(*com(raw.car)),velocity=com(raw.car),position=com(raw.car,True),angle=raw.car.hull.angle,yaw=raw.car.hull.angularVelocity,after_contacts=ids(raw.car),omega_after=[w.omega for w in raw.car.wheels],
                forces=forces,margin=margin,errors=errors,effects=effects)
            save(D/('raw-%03d.json'%counters['raw_completed']),row);state['ticks'].append(row);state['flags'].extend(errors)
            return q
        raw.reset=reset;raw.step=step
        rows=[];identity_ok=trigger_ok=False;stop='ACTION_CAP40';trigger_time=None;reference=Reference()
        try:
            obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']})
            assert state['reset_ticks']==51 and obs.shape==(4,84,84) and obs.dtype==np.float32
            assert digest(raw.track)==case['old_episode']['geometry_sha256_diagnostic_only']
            assert digest([[list(s.position),s.radius] for s in raw.track_variables.obstacles])==case['old_episode']['obstacles_sha256_diagnostic_only']
            partial=digest(dict(geometry=digest(raw.track),obstacles=digest([[list(s.position),s.radius] for s in raw.track_variables.obstacles]),obs=hashlib.sha256(obs.tobytes()).hexdigest(),body=asdict(observed_state(raw.car)),position=com(raw.car,True),angle=raw.car.hull.angle,time=raw.t,RNG=raw.np_random.bit_generator.state))
            if partial!=prior_initial:raise RuntimeError('PRIOR_INITIAL_IDENTITY')
            full=digest(dict(root=asdict(context(raw.car,raw.road,[0.,0.,0.],skin=skin)),RNG=raw.np_random.bit_generator.state,observation=hashlib.sha256(obs.tobytes()).hexdigest()))
            if pair_initial is None:pair_initial=full
            elif full!=pair_initial:raise RuntimeError('FULL_INITIAL_MODEL_INPUTS')
            identity_ok=True;safe_reset(reference,obs);state['phase']='action'
            for index in range(40):
                guard()
                if state['flags']:stop=state['flags'][0];break
                if index==PREFIX:
                    state['braking']=True;state['goal']=math.hypot(*com(raw.car))-DROP;trigger_time=raw.t
                    if state['goal']<=0:raise RuntimeError('NONPOSITIVE_TRIGGER_GOAL')
                    snap=dict(root=asdict(context(raw.car,raw.road,[reference.last_steer,0.,0.],skin=skin)),observation=hashlib.sha256(obs.tobytes()).hexdigest(),reference=hashlib.sha256(pickle.dumps(vars(reference),protocol=5)).hexdigest(),goal=state['goal'])
                    if pair_trigger is None:pair_trigger=digest(snap)
                    elif pair_trigger!=digest(snap):raise RuntimeError('TRIGGER_GOAL_OR_INPUT_PAIR')
                    trigger_ok=True;save(D/('trigger-%s-private.json'%arm),snap)
                if state['braking'] and boundary(math.hypot(*com(raw.car)),state['goal'])!='RUN':stop=boundary(math.hypot(*com(raw.car)),state['goal']);break
                nominal,valid=safe_act(reference,obs)
                if not valid:stop='INVALID_REFERENCE';break
                nominal=np.asarray(nominal,np.float32);memory=hashlib.sha256(pickle.dumps(vars(reference),protocol=5)).hexdigest()
                if state['braking']:
                    action,root,intent=command(nominal,raw.car,raw.road,state['goal'],arm,skin)
                    predicted,pred_rows=forecast(root,float(action[2]),bounds(root.roads))
                else:
                    if nominal[2]!=0:raise RuntimeError('UNEXPECTED_PREFIX_BRAKE')
                    action=nominal.copy();root=context(raw.car,raw.road,action,skin=skin);intent=None;predicted=pred_rows=None
                assert hashlib.sha256(pickle.dumps(vars(reference),protocol=5)).hexdigest()==memory
                assert action[0]==nominal[0] and (action[1]==0 if state['braking'] else action[1]==nominal[1])
                if not np.isfinite([*root.planar.linear.velocity,*[w.omega for w in root.planar.linear.wheels]]).all():raise RuntimeError('NONFINITE_INPUT')
                state['pred']=pred_rows;state['active']=action.copy();state['action_ticks']=0
                assert counters['actions']<80;counters['actions']+=1;state['actions']+=1
                save(D/('charge-%02d.json'%counters['actions']),dict(arm=arm,index=index+1,attempted_actual_actions=counters['actions'],research_remaining=25963-counters['actions'],reserve=84000,reserve_used=0))
                begin=len(state['ticks']);obs,reward,terminated,truncated,info=env.step(action)
                if not(obs.shape==(4,84,84) and obs.dtype==np.float32 and np.isfinite(obs).all() and 0<=obs.min()<=obs.max()<=1):state['flags'].append('OBSERVATION')
                e=calculate_damage_effects(env.damage.damage)
                if (raw.car.grip_multiplier,raw.car.engine_multiplier,raw.car.steering_multiplier)!=(e.grip_multiplier,e.engine_multiplier,e.steering_multiplier):state['flags'].append('WRAPPER_EFFECT')
                if env.damage.damage>0:state['flags'].append('DAMAGE')
                speed=math.hypot(*com(raw.car));error=speed-math.hypot(*predicted.planar.linear.velocity) if predicted and state['action_ticks']==4 else None
                if error is not None and abs(error)>.15:state['flags'].append('PHYSICAL_PREDICTION')
                record=dict(index=index+1,braking=state['braking'],raw_ticks=state['action_ticks'],speed=speed,progress=info['progress'],goal_error_m_s=speed-state['goal'] if state['braking'] else None,
                    request_error_m_s=speed-intent['requested_end_speed'] if intent else None,physical_prediction_error_m_s=error,min_margin_m=min(x['margin'] for x in state['ticks'][begin:]),
                    distance_m=state['distance'],brake_distance_m=state['brake_distance'],brake_work_J=state['brake_work'],flags=list(dict.fromkeys(state['flags'])),nominal=nominal.tolist(),action=action.tolist(),obs_sha256=hashlib.sha256(obs.tobytes()).hexdigest(),reference_calls=reference.calls)
                save(D/('action-%s-%02d.json'%(arm,index+1)),dict(record=record,intent=intent,root=asdict(root) if state['braking'] else None,
                    reference_state=dict(calls=reference.calls,last_steer=reference.last_steer,pixel=vars(reference.pixel))));rows.append(record)
                if index<PREFIX and (record['obs_sha256']!=historical[index]['observation_sha256'] or action.tolist()!=historical[index]['action']):state['flags'].append('PREFIX_REPRODUCTION')
                if state['flags']:stop=state['flags'][0];break
                if terminated or truncated:stop='ENV_TERMINAL';break
                if state['braking'] and boundary(speed,state['goal'])!='RUN':stop=boundary(speed,state['goal']);break
        except BaseException as error:
            stop='TECHNICAL:'+type(error).__name__+':'+str(error);save(D/('error-%s.json'%arm),dict(error=stop,counters=dict(counters)))
        finally:
            sys.settrace(None);env.close();assert raw.world.bodyCount==raw.world.jointCount==0;counters['closed']+=1
            item=dict(arm=arm,stop=stop,actions=state['actions'],reset_ticks=state['reset_ticks'],goal=state['goal'],trigger_time=trigger_time,
                goal_elapsed_s=raw.t-trigger_time if trigger_time is not None else None,identity_ok=identity_ok,trigger_identity_ok=trigger_ok,rows=rows)
            save(D/('close-%s.json'%arm),dict(record=item,counters=dict(counters)));native.append(item)
        if not identity_ok or stop.startswith('TECHNICAL:'):break
    save(D/'full-records-private.json',native)
    def summary(item,n=None):
        rows=item['rows'] if n is None else item['rows'][:n];brakes=[r for r in rows if r['braking']]
        return dict(arm=item['arm'],stop=item['stop'],actions=item['actions'],rows_compared=len(rows),brake_actions=len(brakes),global_goal_m_s=item['goal'],goal_elapsed_s=item['goal_elapsed_s'],
            final_speed_m_s=rows[-1]['speed'] if rows else None,final_goal_error_m_s=rows[-1]['goal_error_m_s'] if rows else None,final_progress=rows[-1]['progress'] if rows else None,
            min_margin_m=min((r['min_margin_m'] for r in rows),default=None),max_request_abs_error_m_s=max((abs(r['request_error_m_s']) for r in brakes),default=None),
            max_physical_prediction_error_m_s=max((abs(r['physical_prediction_error_m_s']) for r in brakes if r['physical_prediction_error_m_s'] is not None),default=None),
            unnecessary_underspeed_m_s=max([0.,*[-r['goal_error_m_s'] for r in brakes]]),distance_m=rows[-1]['distance_m'] if rows else None,brake_distance_m=rows[-1]['brake_distance_m'] if rows else None,brake_work_J=rows[-1]['brake_work_J'] if rows else None)
    common=min((len(n['rows']) for n in native),default=0) if len(native)==2 else 0
    while common and any(any(r['raw_ticks']!=4 for r in n['rows'][:common]) for n in native):common-=1
    successful=bool(len(native)==2 and all(n['stop']=='GOAL_BAND' for n in native))
    result=dict(status='PHYSICAL_GOAL_PAIR_PASS' if successful else 'PHYSICAL_GOAL_PAIR_LIMITED_STOP',native=[summary(n) for n in native],common_actions=common,common_time_s=common*.08,
        common_prefix=[summary(n,common) for n in native] if common else [],counters=counters,research_remaining=25963-counters['actions'],reserve=84000,reserve_used=0,
        CPU_s_including_test_child=usage(),wall_s=time.perf_counter()-start,case_source_commit=case['source_commit'],case_index=case['case_index'],
        scope='New explicit physical-goal probe, identical frozen steering/acceleration schedule; not PixelAgent performance, lap record or independent evaluation',source_sha256=c['source_sha256'])
    result['response_local_goal_gate']=bool(any(n['arm']=='response' and n['stop']=='GOAL_BAND' for n in native))
    save(D/'budget-final-private.json',dict(actual_actions=counters['actions'],resets=counters['resets'],raw_completed=counters['raw_completed'],research_remaining=result['research_remaining'],reserve=84000,reserve_used=0))
    guard();save(G/'retry/brake511_result.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':run()
