"""One conditional same-DEV80/100 pair; raw source/calibration guards precede promotion."""
import datetime,hashlib,json,math,resource,signal,sys,time
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.speed516_control import path_for,forecast,force_rows
from retry.corner515_control import nominal,steering,project,reference
from retry.corner515_model import obstacle_margin
from retry.brake503_diagnostic import com,observed_state
from retry.brake509_adapter import context
from retry.brake508_corridor import bounds,indexed_contacts
from retry.brake510_common import native_roads,track_boundary,boundary_index,clearance
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response516-private')

def run():
    started=time.perf_counter();cpu=time.process_time();c=json.loads((G/'retry/speed516_native_contract.json').read_text());pref=json.loads((G/'retry/speed516_model_result.json').read_text());proof=json.loads((G/'retry/speed516_model_gate_correction.json').read_text())
    assert proof['native_pair_eligible'] and proof['original_model_result_sha256']==hashlib.sha256((G/'retry/speed516_model_result.json').read_bytes()).hexdigest()
    if (D/'NATIVE_STARTED.json').exists():raise RuntimeError('NO_NATIVE_SCIENTIFIC_RETRY')
    def ready(x):
        if isinstance(x,np.generic):return x.item()
        if isinstance(x,np.ndarray):return x.tolist()
        raise TypeError(type(x).__name__)
    def sha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,default=ready).encode()).hexdigest()
    def save(path,x):
        data=(json.dumps(x,indent=2,default=ready,allow_nan=False)+'\n').encode();files=list(D.iterdir())
        if len(files)>=3000 or sum(p.stat().st_size for p in files)+len(data)>64*1024**2:raise RuntimeError('PRIVATE_CAP')
        with path.open('xb') as f:f.write(data)
        path.chmod(0o600 if D in path.parents else 0o644)
    def guard(*a):
        if time.process_time()-cpu>=180 or time.perf_counter()-started>=240:raise RuntimeError('NATIVE_COST_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,180)
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,240)
    assert all(hashlib.sha256((G/n).read_bytes()).hexdigest()==h for n,h in c['source_sha256'].items())
    case=json.loads((D/'approved-case-private.json').read_text());assert hashlib.sha256((D/'approved-case-private.json').read_bytes()).hexdigest()==c['case_private_sha256']
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text())
    paths={b:path_for(static,b) for b in (80.,100.)};assert {k:v for k,v in paths[80.].items() if k!='speeds'}=={k:v for k,v in paths[100.].items() if k!='speeds'}
    from core.vendor.car_racing import CarRacing,TRACK_WIDTH
    from core.vendor.car_dynamics import Car
    from Box2D.b2 import polygonRadius
    from gymnasium.wrappers import TimeLimit
    from env_wrapper import CarEnvironment
    from damage import calculate_damage_effects
    lines=(G/'core/vendor/car_dynamics.py').read_text().splitlines();rawline=next(i+1 for i,s in enumerate(lines) if 'if abs(force) > 2.0 * friction_limit' in s);finalline=next(i+1 for i,s in enumerate(lines) if 'w.omega -= dt * f_force' in s)
    save(D/'NATIVE_STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/speed516_native_contract.json').read_bytes()).hexdigest()))
    counts=dict(worlds=0,closed=0,resets=0,actions=0,raw_attempts=0,raw_completed=0);model=[pref['model_integrator_ticks']];force_evals=pref['model_wheel_force_evaluations'];pair_initial=None;pair_prefix=None;arms=[];skin=2*float(polygonRadius)
    def ids(car):return tuple(tuple(sorted(t.idx for t in w.tiles)) for w in car.wheels)
    for budget in (80.,100.):
        guard();assert counts['worlds']<2;counts['worlds']+=1;label=str(int(budget));path=paths[budget]
        raw=CarRacing(**case['base']);env=CarEnvironment(TimeLimit(raw,max_episode_steps=case['TimeLimit_max_episode_steps']),**case['wrapper']);original_step=raw.step;original_reset=raw.reset
        st=dict(phase='reset',resets=0,reset_ticks=0,actions=0,action_ticks=0,active=None,pred=None,flags=[],mesh=None,ticks=[],events={},epoch=None,minimum=float('inf'),max_path_error=0.,max_ref_over=0.,force_peak=0.,clipped=0,samples=0,force_oracle_max=0.,impulse_max=0.)
        def reset(**kwargs):
            guard()
            if st['resets'] or counts['resets']>=2:raise RuntimeError('RESET_CAP')
            st['resets']+=1;counts['resets']+=1;save(D/('reset-charge-'+label+'.json'),dict(counts));return original_reset(**kwargs)
        def step(action):
            nonlocal force_evals
            guard()
            if counts['raw_attempts']>=1382 or (st['phase']=='reset' and st['reset_ticks']>=51):raise RuntimeError('RAW_CAP')
            if st['mesh'] is None:
                st['mesh']=native_roads(raw.road);st['index']=bounds(st['mesh']);st['base']=[p for p,mu in st['mesh']];st['edge']=track_boundary(raw.track,TRACK_WIDTH);st['edgeindex']=boundary_index(st['edge'])
            before=observed_state(raw.car);position=com(raw.car,True);clock=raw.t;used=ids(raw.car);effects=(raw.car.grip_multiplier,raw.car.engine_multiplier,raw.car.steering_multiplier)
            sensor=tuple(indexed_contacts([tuple(w.GetWorldPoint(v)) for v in w.fixtures[0].shape.vertices],st['mesh'],st['index'],skin) for w in raw.car.wheels)
            oracle=[];beforeplanar=None;actual={}
            if st['phase']=='action':
                before_root=context(raw.car,raw.road,st['active'],skin=skin);beforeplanar=asdict(before_root.planar);oracle=force_rows(before_root,st['active']);force_evals+=4
                if force_evals>10000:raise RuntimeError('MODEL_FORCE_EVAL_CAP')
            def trace(frame,event,arg):
                if frame.f_code is Car.step.__code__:
                    if event=='line' and frame.f_lineno in (rawline,finalline):
                        x=frame.f_locals;j=raw.car.wheels.index(x['w']);item=actual.setdefault(j,dict(wheel=j))
                        if frame.f_lineno==rawline:item.update(ratio=float(x['force']/x['friction_limit']),friction=float(x['friction_limit']))
                        else:item['vector']=[float(x['f_force']*x['forw'][k]+x['p_force']*x['side'][k]) for k in range(2)]
                    return trace
                return None
            counts['raw_attempts']+=1
            if st['phase']=='action':sys.settrace(trace)
            try:q=original_step(action)
            finally:sys.settrace(None)
            counts['raw_completed']+=1
            if st['phase']=='reset':st['reset_ticks']+=1
            else:st['action_ticks']+=1
            errors=[]
            if sensor!=ids(raw.car):errors.append('SOURCE_SENSOR_PHASE')
            if effects!=(raw.car.grip_multiplier,raw.car.engine_multiplier,raw.car.steering_multiplier):errors.append('WITHIN_RAW_EFFECT')
            if st['active'] is not None and (action is None or not np.array_equal(action,st['active'].astype(np.float64))):errors.append('PAYLOAD')
            position_after=com(raw.car,True);velocity=com(raw.car);speed=math.hypot(*velocity);forecast_error=None
            if st['pred'] is not None:
                k=st['action_ticks']-1
                if k>=4:errors.append('HOLD_TICKS')
                else:
                    pred=st['pred'][k];forecast_error=dict(position_m=math.dist(pred['position'],position_after),speed_m_s=speed-math.hypot(*pred['velocity']),angle_rad=math.remainder(raw.car.hull.angle-pred['angle'],2*math.pi),yaw_rad_s=raw.car.hull.angularVelocity-pred['yaw'])
                    if forecast_error['position_m']>.10 or abs(forecast_error['speed_m_s'])>.15 or abs(forecast_error['angle_rad'])>.02 or abs(forecast_error['yaw_rad_s'])>.05:errors.append('PHYSICAL_PREDICTION')
                    mu=lambda t:max([400*raw.car.grass_friction_multiplier*effects[0],*[400*st['mesh'][j][1]*effects[0] for j in t]])
                    if any(mu(a)!=mu(b) for a,b in zip(pred['contacts_used'],used)):errors.append('PREDICTED_FRICTION')
            source_error=impulse_error=None
            if oracle:
                if len(actual)!=4 or any('vector' not in x or 'ratio' not in x for x in actual.values()):raise RuntimeError('SOURCE_FORCE_CAPTURE')
                source_error=max(math.dist(oracle[i]['vector'],actual[i]['vector']) for i in range(4));st['force_oracle_max']=max(st['force_oracle_max'],source_error)
                expected=tuple(before.velocity[j]+.02*sum(actual[i]['vector'][j] for i in range(4))/before.mass for j in range(2));impulse_error=math.dist(expected,velocity);st['impulse_max']=max(st['impulse_max'],impulse_error)
                if source_error>.05:errors.append('SOURCE_FORCE_ORACLE')
                if impulse_error>.01:errors.append('SOURCE_COM_IMPULSE')
            roadgap=clearance(raw.car,st['base'],st['index'],st['edge'],st['edgeindex']);polys=[[tuple(b.GetWorldPoint(v)) for v in f.shape.vertices] for b in [raw.car.hull,*raw.car.wheels] for f in b.fixtures]
            gap=min(roadgap,obstacle_margin(polys,static['obstacles']));st['minimum']=min(st['minimum'],gap)
            if gap<.25:errors.append('ROAD_OR_OBSTACLE_MARGIN')
            if q[4].get('collision',False):errors.append('COLLISION')
            q0,qp=project(position,path),project(position_after,path);refspeed,ff=reference(qp['s'],path)
            if st['phase']=='action':
                st['max_path_error']=max(st['max_path_error'],qp['distance'])
                if qp['distance']>3:errors.append('PATH_ERROR')
                if qp['s']>=path['measurement_begin']:
                    st['max_ref_over']=max(st['max_ref_over'],speed-refspeed);st['force_peak']=max(st['force_peak'],max(x['ratio'] for x in actual.values()));st['samples']+=4;st['clipped']+=sum(x['ratio']>1 for x in actual.values())
                    if speed-refspeed>5 or st['force_peak']>1.25 or st['clipped']/st['samples']>.10:errors.append('DYNAMICS_GUARD')
                for name,s in [('begin',path['measurement_begin']),('corner_exit',path['corner_end']),('end',path['measurement_end'])]:
                    if name not in st['events'] and q0['s']<s<=qp['s']:
                        f=(s-q0['s'])/(qp['s']-q0['s']);v0=math.hypot(*before.velocity);st['events'][name]=dict(lower=clock-st['epoch'],upper=raw.t-st['epoch'],time=clock-st['epoch']+.02*f,speed=v0+f*(speed-v0))
            record=dict(phase=st['phase'],action=st['actions'],time=raw.t,before=asdict(before),before_planar=beforeplanar,before_position=position,position=position_after,velocity=velocity,speed=speed,angle=raw.car.hull.angle,yaw=raw.car.hull.angularVelocity,station=qp['s'],path_error=qp['distance'],reference_speed=refspeed,margin=gap,used_contacts=used,after_contacts=ids(raw.car),effects=effects,forces=list(actual.values()),force_oracle_vector_error_N=source_error,COM_impulse_error_m_s=impulse_error,forecast_error=forecast_error,errors=errors)
            save(D/('raw-%04d.json'%counts['raw_completed']),record);st['ticks'].append(record);st['flags'].extend(errors);return q
        raw.reset=reset;raw.step=step;rows=[];initial_ok=False;prefix=[];stop='MAX160'
        try:
            obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});assert st['reset_ticks']==51
            geometry=sha(raw.track);obstacles=[[list(o.position),o.radius] for o in raw.track_variables.obstacles]
            assert geometry==case['old_episode']['geometry_sha256_diagnostic_only'] and sha(obstacles)==case['old_episode']['obstacles_sha256_diagnostic_only'] and obstacles==static['obstacles']
            root=context(raw.car,raw.road,[0,0,0],skin=skin);full=sha(dict(root=asdict(root),RNG=raw.np_random.bit_generator.state,observation=hashlib.sha256(obs.tobytes()).hexdigest()))
            assert full==static['full_identity']
            if pair_initial is None:pair_initial=full
            elif full!=pair_initial:raise RuntimeError('PAIR_INITIAL')
            initial_ok=True;st['epoch']=raw.t;st['phase']='action'
            for i in range(160):
                guard()
                if st['flags']:stop=st['flags'][0];break
                root=context(raw.car,raw.road,[0,0,0],skin=skin)
                action=np.array([steering(root,path),.32,0.],np.float32) if i<24 else nominal(root,path)[0]
                assert action.dtype==np.float32 and np.isfinite(action).all() and -1<=action[0]<=1 and 0<=action[1]<=1 and 0<=action[2]<=1 and not(action[1]>0 and action[2]>0)
                predicted,predrows=forecast(root,action,bounds(root.roads),model)
                st['active']=action.copy();st['pred']=predrows;st['action_ticks']=0;begin=len(st['ticks'])
                assert counts['actions']<320;counts['actions']+=1;st['actions']+=1
                save(D/('charge-%03d.json'%counts['actions']),dict(budget=budget,index=i+1,attempted_actual_actions=counts['actions'],research_remaining=25804-counts['actions'],reserve=84000,reserve_used=0))
                obs,reward,terminated,truncated,info=env.step(action)
                if not(obs.shape==(4,84,84) and obs.dtype==np.float32 and np.isfinite(obs).all() and 0<=obs.min()<=obs.max()<=1):st['flags'].append('OBSERVATION')
                e=calculate_damage_effects(env.damage.damage)
                if (raw.car.grip_multiplier,raw.car.engine_multiplier,raw.car.steering_multiplier)!=(e.grip_multiplier,e.engine_multiplier,e.steering_multiplier):st['flags'].append('WRAPPER_EFFECT')
                if env.damage.damage>0:st['flags'].append('DAMAGE')
                current=st['ticks'][begin:];root_after=context(raw.car,raw.road,[0,0,0],skin=skin);before_state=asdict(root);before_state.pop('roads');after_state=asdict(root_after);after_state.pop('roads')
                record=dict(index=i+1,action=action.tolist(),obs_sha256=hashlib.sha256(obs.tobytes()).hexdigest(),speed=math.hypot(*com(raw.car)),progress=info['progress'],raw_ticks=st['action_ticks'],flags=list(dict.fromkeys(st['flags'])),min_margin=min(x['margin'] for x in current))
                save(D/('action-'+label+'-%03d.json'%(i+1)),dict(record=record,before_root_without_roads=before_state,after_root_without_roads=after_state));rows.append(record)
                if i<24:prefix.append(dict(action=record['action'],obs_sha256=record['obs_sha256']))
                if i==23:
                    if pair_prefix is None:pair_prefix=sha(prefix)
                    elif pair_prefix!=sha(prefix):st['flags'].append('PAIR_PREFIX')
                if st['flags']:stop=st['flags'][0];break
                if 'end'in st['events']:stop='WINDOW_END';break
                if terminated or truncated:stop='ENV_TERMINAL';break
        except BaseException as error:
            stop='TECHNICAL:'+type(error).__name__+':'+str(error);save(D/('error-'+label+'.json'),dict(error=stop,counts=dict(counts)))
        finally:
            sys.settrace(None);env.close();assert raw.world.bodyCount==raw.world.jointCount==0;counts['closed']+=1
            error_rows=[x for x in st['ticks'] if x['forecast_error'] is not None]
            item=dict(budget=budget,stop=stop,initial_identity=initial_ok,actions=st['actions'],reset_ticks=st['reset_ticks'],events=st['events'],min_margin_m=st['minimum'],max_path_error_m=st['max_path_error'],max_tracking_overspeed_m_s=st['max_ref_over'],peak_force_ratio=st['force_peak'],clipped_wheel_samples=st['clipped'],wheel_samples=st['samples'],source_force_oracle_max_N=st['force_oracle_max'],source_COM_impulse_max_m_s=st['impulse_max'],max_prediction_errors={k:max((abs(x['forecast_error'][k]) for x in error_rows),default=0.) for k in ('position_m','speed_m_s','angle_rad','yaw_rad_s')},official_finish=raw.finish_time_s is not None,rows=rows)
            save(D/('close-'+label+'-private.json'),dict(record=item,counts=dict(counts)));arms.append(item)
        if stop!='WINDOW_END':break
    summaries=[]
    for a in arms:
        b={k:v for k,v in a.items() if k!='rows'};events=a['events'];b['window_time_s']=events['end']['time']-events['begin']['time'] if a['stop']=='WINDOW_END' else None
        b['window_duration_lower_s']=events['end']['lower']-events['begin']['upper'] if a['stop']=='WINDOW_END' else None;b['window_duration_upper_s']=events['end']['upper']-events['begin']['lower'] if a['stop']=='WINDOW_END' else None;summaries.append(b)
    gain=lower=None
    if len(summaries)==2 and all(x['stop']=='WINDOW_END' for x in summaries):gain=summaries[0]['window_time_s']-summaries[1]['window_time_s'];lower=summaries[0]['window_duration_lower_s']-summaries[1]['window_duration_upper_s']
    passed=lower is not None and lower>=.08
    result=dict(status='NATIVE_WINDOW_EFFECT_PASS' if passed else 'NATIVE_WINDOW_NOT_QUALIFIED',arms=summaries,interpolated_window_gain_s=gain,bracket_certified_gain_lower_s=lower,practical_effect_gate=passed,counts=counts,all_model_integrator_ticks=model[0],all_model_wheel_force_evaluations=force_evals,research_remaining=25804-counts['actions'],reserve=84000,reserve_used=0,native_CPU_s=time.process_time()-cpu,native_wall_s=time.perf_counter()-started,total_CPU_s=pref['CPU_s']+time.process_time()-cpu,total_wall_s=pref['wall_s']+time.perf_counter()-started,scope='One current DEV curved window, exact state/map diagnostic; no full lap/13.640/pixel claim. Prefix time differences never substituted for fullwindow gain.')
    save(D/'native-full-records-private.json',arms);save(D/'budget-final-private.json',dict(counts=counts,research_remaining=result['research_remaining'],reserve=84000,reserve_used=0));guard();save(G/'retry/speed516_native_result.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':run()
