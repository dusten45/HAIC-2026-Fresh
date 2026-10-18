"""Single known-DEV approach pair. No physical retry or protected evaluation."""
import datetime,hashlib,json,math,pickle,resource,signal,subprocess,sys,time
from pathlib import Path
from dataclasses import asdict
import numpy as np
from retry.brake503_diagnostic import com,observed_state
from retry.brake509_adapter import context
from retry.brake508_corridor import bounds,indexed_contacts
from retry.brake510_common import native_roads,track_boundary,boundary_index,clearance
from retry.brake511_control import Reference
from retry.plan512_control import axis_plan,station,hold,scalar_action,response_action,GOAL
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response512-private')

def run():
    started=time.perf_counter();cpu=time.process_time();child=resource.getrusage(resource.RUSAGE_CHILDREN)
    c=json.loads((G/'retry/plan512_contract.json').read_text());case=json.loads((D/'approved-case-private.json').read_text())
    if (D/'PHYSICS_STARTED.json').exists():raise RuntimeError('NO_PHYSICAL_RETRY')
    def ready(x):
        if isinstance(x,np.generic):return x.item()
        if isinstance(x,np.ndarray):return x.tolist()
        raise TypeError(type(x).__name__)
    def sha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,default=ready).encode()).hexdigest()
    def save(p,x):
        data=(json.dumps(x,default=ready,indent=2,allow_nan=False)+'\n').encode();files=list(D.iterdir())
        if len(files)>=3000 or sum(q.stat().st_size for q in files)+len(data)>64*1024**2:raise RuntimeError('PRIVATE_CAP')
        with p.open('xb') as f:f.write(data)
        p.chmod(0o600 if D in p.parents else 0o644)
    def usage():
        r=resource.getrusage(resource.RUSAGE_CHILDREN);return time.process_time()-cpu+r.ru_utime+r.ru_stime-child.ru_utime-child.ru_stime
    def guard(*a):
        if usage()>=180 or time.perf_counter()-started>=240:raise RuntimeError('RESOURCE_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,180)
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,240)
    assert all(hashlib.sha256((G/n).read_bytes()).hexdigest()==h for n,h in c['source_sha256'].items())
    assert hashlib.sha256((D/'approved-case-private.json').read_bytes()).hexdigest()==c['case_private_sha256']
    assert json.loads((G/'retry/brake511_result.json').read_text())['research_remaining']==25909
    historical=json.loads(Path('/workspace/haic-response510-private/native-full-records-private.json').read_text())[0]['rows'][:24]
    prior_initial=json.loads(Path('/workspace/haic-response510-private/native-initial-reference.json').read_text())['identity']
    test=subprocess.run([sys.executable,'-m','unittest','retry.test_plan512','-v'],cwd=G,capture_output=True,text=True,timeout=30)
    save(D/'pure-tests.json',dict(returncode=test.returncode,stdout=test.stdout,stderr=test.stderr))
    if test.returncode:raise RuntimeError('PURE_GATE_NO_WORLD')
    guard();signal.setitimer(signal.ITIMER_PROF,max(.001,180-usage()))
    from core.vendor.car_racing import CarRacing,TRACK_WIDTH
    from Box2D.b2 import polygonRadius
    from gymnasium.wrappers import TimeLimit
    from env_wrapper import CarEnvironment
    from local_runner import safe_act,safe_reset
    from damage import calculate_damage_effects
    save(D/'PHYSICS_STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/plan512_contract.json').read_bytes()).hexdigest()))
    counts=dict(worlds=0,closed=0,resets=0,actions=0,raw_attempts=0,raw_completed=0);model=[0];pair_initial=pair_trigger=pair_plan=None;arms=[];skin=2*float(polygonRadius)
    def contacts(car):return tuple(tuple(sorted(t.idx for t in w.tiles)) for w in car.wheels)
    for arm in ('scalar','response'):
        guard();assert counts['worlds']<2;counts['worlds']+=1
        raw=CarRacing(**case['base']);env=CarEnvironment(TimeLimit(raw,max_episode_steps=case['TimeLimit_max_episode_steps']),**case['wrapper'])
        original_reset=raw.reset;original_step=raw.step
        st=dict(phase='reset',resets=0,reset_ticks=0,actions=0,action_ticks=0,active=None,pred=None,ticks=[],flags=[],mesh=None,plan=None,cross=None,epoch=None,minimum=float('inf'))
        def reset(**kwargs):
            guard()
            if st['resets'] or counts['resets']>=2:raise RuntimeError('EXTRA_RESET')
            st['resets']+=1;counts['resets']+=1;save(D/('reset-charge-'+arm+'.json'),dict(counts));return original_reset(**kwargs)
        def step(action):
            guard()
            if counts['raw_attempts']>=1702 or (st['phase']=='reset' and st['reset_ticks']>=51):raise RuntimeError('RAW_CAP')
            if st['mesh'] is None:
                st['mesh']=native_roads(raw.road);st['index']=bounds(st['mesh']);st['base']=[p for p,mu in st['mesh']]
                st['edge']=track_boundary(raw.track,TRACK_WIDTH);st['edgeindex']=boundary_index(st['edge'])
            before=observed_state(raw.car);position=com(raw.car,True);used=contacts(raw.car);clock=raw.t
            source=tuple(indexed_contacts([tuple(w.GetWorldPoint(v)) for v in w.fixtures[0].shape.vertices],st['mesh'],st['index'],skin) for w in raw.car.wheels)
            effects=(raw.car.grip_multiplier,raw.car.engine_multiplier,raw.car.steering_multiplier)
            counts['raw_attempts']+=1;q=original_step(action);counts['raw_completed']+=1
            if st['phase']=='reset':st['reset_ticks']+=1
            else:st['action_ticks']+=1
            errors=[]
            if source!=contacts(raw.car):errors.append('SOURCE_CONTACT_PHASE')
            if effects!=(raw.car.grip_multiplier,raw.car.engine_multiplier,raw.car.steering_multiplier):errors.append('WITHIN_RAW_EFFECT')
            if st['active'] is not None and (action is None or not np.array_equal(action,st['active'].astype(np.float64))):errors.append('PAYLOAD')
            prediction_error=None
            if st['pred'] is not None:
                k=st['action_ticks']-1
                if k>=4:errors.append('HOLD_TICKS')
                else:
                    pred=st['pred'][k];prediction_error=math.hypot(*com(raw.car))-math.hypot(*pred['velocity_after'])
                    if abs(prediction_error)>.15:errors.append('PHYSICAL_PREDICTION')
                    mu=lambda ids:max([400*raw.car.grass_friction_multiplier*effects[0],*[400*st['mesh'][j][1]*effects[0] for j in ids]])
                    if any(mu(a)!=mu(b) for a,b in zip(pred['contacts_used'],used)):errors.append('PREDICTED_FRICTION')
            margin=clearance(raw.car,st['base'],st['index'],st['edge'],st['edgeindex']);st['minimum']=min(st['minimum'],margin)
            if margin<.25:errors.append('ROAD_MARGIN')
            if q[4].get('collision',False):errors.append('COLLISION')
            speed=math.hypot(*com(raw.car));s=station(com(raw.car,True),st['plan']) if st['plan'] else None
            if st['plan'] and st['phase']=='action' and st['cross'] is None:
                old=station(position,st['plan']);gate=st['plan']['gate']
                if old<gate<=s:
                    f=(gate-old)/(s-old);v0=math.hypot(*before.velocity)
                    st['cross']=dict(time_lower_s=clock-st['epoch'],time_upper_s=raw.t-st['epoch'],interpolated_time_s=clock-st['epoch']+.02*f,speed_m_s=v0+f*(speed-v0),station=gate)
            row=dict(phase=st['phase'],action=st['actions'],time=raw.t,position=com(raw.car,True),station=s,speed=speed,velocity=com(raw.car),before=asdict(before),used_contacts=used,after_contacts=contacts(raw.car),prediction_error_m_s=prediction_error,effects=effects,margin=margin,errors=errors)
            save(D/('raw-%04d.json'%counts['raw_completed']),row);st['ticks'].append(row);st['flags'].extend(errors);return q
        raw.reset=reset;raw.step=step;rows=[];identity=False;trigger=False;ref=Reference();stop='ACTION_CAP200'
        try:
            obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']})
            assert st['reset_ticks']==51
            geometry=sha(raw.track);obstacles=sha([[list(s.position),s.radius] for s in raw.track_variables.obstacles])
            assert geometry==case['old_episode']['geometry_sha256_diagnostic_only'] and obstacles==case['old_episode']['obstacles_sha256_diagnostic_only']
            partial=sha(dict(geometry=geometry,obstacles=obstacles,obs=hashlib.sha256(obs.tobytes()).hexdigest(),body=asdict(observed_state(raw.car)),position=com(raw.car,True),angle=raw.car.hull.angle,time=raw.t,RNG=raw.np_random.bit_generator.state))
            if partial!=prior_initial:raise RuntimeError('OLD_INITIAL_IDENTITY')
            full=sha(dict(root=asdict(context(raw.car,raw.road,[0.,0.,0.],skin=skin)),RNG=raw.np_random.bit_generator.state,observation=hashlib.sha256(obs.tobytes()).hexdigest()))
            if pair_initial is None:pair_initial=full
            elif pair_initial!=full:raise RuntimeError('PAIR_INITIAL')
            identity=True;st['epoch']=raw.t;st['plan']=axis_plan(raw.track,com(raw.car,True))
            if pair_plan is None:pair_plan=sha(st['plan'])
            elif pair_plan!=sha(st['plan']):raise RuntimeError('PAIR_PLAN')
            save(D/('plan-'+arm+'-private.json'),st['plan']);safe_reset(ref,obs);st['phase']='action'
            for i in range(200):
                guard()
                if st['flags']:stop=st['flags'][0];break
                nominal,valid=safe_act(ref,obs)
                if not valid:raise RuntimeError('INVALID_REFERENCE')
                nominal=np.asarray(nominal,np.float32);mem=sha(dict(calls=ref.calls,last_steer=ref.last_steer,pixel=vars(ref.pixel)))
                root=context(raw.car,raw.road,nominal,skin=skin)
                details=None
                if i==24:
                    snap=dict(root=asdict(root),obs=hashlib.sha256(obs.tobytes()).hexdigest(),reference=mem,plan=st['plan'])
                    if pair_trigger is None:pair_trigger=sha(snap)
                    elif pair_trigger!=sha(snap):raise RuntimeError('PAIR_TRIGGER')
                    trigger=True;save(D/('trigger-'+arm+'-private.json'),snap)
                if i<24:
                    action=nominal.copy()
                    if action[2]!=0:raise RuntimeError('UNEXPECTED_PREFIX_BRAKE')
                else:
                    try:action,details=(scalar_action(root,ref.last_steer,st['plan']) if arm=='scalar' else response_action(root,ref.last_steer,st['plan'],model))
                    except ValueError as e:stop='PLAN_STOP:'+str(e);save(D/('plan-stop-'+arm+'-private.json'),dict(error=stop,root=asdict(root),plan=st['plan']));break
                if mem!=sha(dict(calls=ref.calls,last_steer=ref.last_steer,pixel=vars(ref.pixel))):raise RuntimeError('REFERENCE_MEMORY_MUTATED')
                assert action.dtype==np.float32 and action[0]==nominal[0] and np.isfinite(action).all() and 0<=action[1]<=1 and 0<=action[2]<=np.float32(.3)
                predicted,predrows=hold(root,action,bounds(root.roads),model)
                st['pred']=predrows;st['active']=action;st['action_ticks']=0;begin=len(st['ticks'])
                assert counts['actions']<400;counts['actions']+=1;st['actions']+=1
                save(D/('charge-%03d.json'%counts['actions']),dict(arm=arm,index=i+1,attempted_actual_actions=counts['actions'],research_remaining=25909-counts['actions'],reserve=84000,reserve_used=0))
                obs,reward,terminated,truncated,info=env.step(action)
                if not(obs.shape==(4,84,84) and obs.dtype==np.float32 and np.isfinite(obs).all() and 0<=obs.min()<=obs.max()<=1):st['flags'].append('OBSERVATION')
                effects=calculate_damage_effects(env.damage.damage)
                if (raw.car.grip_multiplier,raw.car.engine_multiplier,raw.car.steering_multiplier)!=(effects.grip_multiplier,effects.engine_multiplier,effects.steering_multiplier):st['flags'].append('WRAPPER_EFFECT')
                if env.damage.damage>0:st['flags'].append('DAMAGE')
                obs_sha=hashlib.sha256(obs.tobytes()).hexdigest()
                if i<24 and (obs_sha!=historical[i]['observation_sha256'] or action.tolist()!=historical[i]['action']):st['flags'].append('PREFIX_REPRODUCTION')
                speed=math.hypot(*com(raw.car));sigma=sum(com(raw.car)[j]*st['plan']['axis'][j] for j in range(2));s=station(com(raw.car,True),st['plan'])
                record=dict(index=i+1,action=action.tolist(),nominal=nominal.tolist(),observation_sha256=obs_sha,station=s,speed=speed,progress=info['progress'],raw_ticks=st['action_ticks'],flags=list(dict.fromkeys(st['flags'])),prediction_error_m_s=speed-math.hypot(*predicted.planar.linear.velocity),min_margin=min(x['margin'] for x in st['ticks'][begin:]),reference_calls=ref.calls,
                    scalar_request_error_m_s=speed-details['predicted_end_speed'] if details and arm=='scalar' else None)
                save(D/('action-'+arm+'-%03d.json'%(i+1)),dict(record=record,root=asdict(root) if i>=24 else None,details=details));rows.append(record)
                if st['flags']:stop=st['flags'][0];break
                if st['cross'] is not None:stop='GATE_CROSSED';break
                if terminated or truncated:stop='ENV_TERMINAL';break
        except BaseException as e:
            stop='TECHNICAL:'+type(e).__name__+':'+str(e);save(D/('error-'+arm+'.json'),dict(error=stop,counts=dict(counts)))
        finally:
            env.close();assert raw.world.bodyCount==raw.world.jointCount==0;counts['closed']+=1
            item=dict(arm=arm,stop=stop,identity=identity,trigger=trigger,cross=st['cross'],rows=rows,minimum_raw_margin=st['minimum'],official_finish=raw.finish_time_s is not None)
            save(D/('close-'+arm+'-private.json'),dict(record=item,counts=dict(counts)));arms.append(item)
        if not identity or (stop not in ('GATE_CROSSED','ACTION_CAP200') and not stop.startswith('PLAN_STOP:')):break
    def brief(a):
        rows=a['rows'];return dict(arm=a['arm'],stop=a['stop'],actions=len(rows),initial_identity=a['identity'],trigger_identity=a['trigger'],crossing={k:v for k,v in a['cross'].items() if k!='station'} if a['cross'] else None,
            crossing_goal_pass=bool(a['cross'] and abs(a['cross']['speed_m_s']-GOAL)<=.5 and not any(r['flags'] for r in rows)),min_raw_margin_m=a['minimum_raw_margin'],final_progress=rows[-1]['progress'] if rows else None,
            first_brake_action=next((r['index'] for r in rows if r['action'][2]>0),None),brake_actions=sum(r['action'][2]>0 for r in rows),max_prediction_error_m_s=max((abs(r['prediction_error_m_s']) for r in rows),default=None),
            max_scalar_request_error_m_s=max((abs(r['scalar_request_error_m_s']) for r in rows if r['scalar_request_error_m_s'] is not None),default=None),official_finish=a['official_finish'])
    summaries=[brief(a) for a in arms];effect=False;time_gain=None
    if len(summaries)==2 and summaries[1]['crossing_goal_pass']:
        b,a=summaries
        if b['crossing_goal_pass']:
            time_gain=b['crossing']['interpolated_time_s']-a['crossing']['interpolated_time_s'];effect=b['crossing']['time_lower_s']-a['crossing']['time_upper_s']>=.08
        else:effect=b['stop'].startswith('PLAN_STOP:') or bool(b['crossing'] and b['crossing']['speed_m_s']>GOAL+.5)
    result=dict(status='APPROACH_EFFECT_GATE_PASS' if effect else 'APPROACH_EFFECT_NOT_SHOWN',arms=summaries,practical_effect_gate=effect,interpolated_gate_time_gain_s=time_gain,
        counts=counts,hypothetical_model_ticks=model[0],research_remaining=25909-counts['actions'],reserve=84000,reserve_used=0,CPU_s_including_test_child=usage(),wall_s=time.perf_counter()-started,
        scope='One fixed first-straight speed-limited approach on known DEV; privileged current state/map; no lap finish or 13.640 comparison; no pixel-policy claim',source_sha256=c['source_sha256'])
    save(D/'full-records-private.json',arms);save(D/'budget-final-private.json',dict(counts=counts,research_remaining=result['research_remaining'],reserve=84000,reserve_used=0));guard()
    save(G/'retry/plan512_result.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':run()
