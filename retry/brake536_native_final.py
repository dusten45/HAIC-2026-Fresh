"""Conditional525 corrected-model current-state governor pair, source-force guards."""
import atexit,datetime,hashlib,json,math,resource,signal,sys,time
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.lap518_control import force_rows,project,reference,nominal,steering
from retry.response528_control import forecast
from retry.brake536_control import geometry_context
from retry.governor525b_control import choose as baseline_choose
from retry.brake536_control import choose as candidate_choose
from retry.corner515_model import obstacle_margin
from retry.brake503_diagnostic import com,observed_state
from retry.brake509_adapter import context
from retry.brake508_corridor import bounds,indexed_contacts
from retry.brake510_common import native_roads,track_boundary,boundary_index,clearance
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response536-private')

def run():
    started=time.perf_counter();cpu=time.process_time();c=json.loads((G/'retry/brake536_contract.json').read_text());pref=json.loads((G/'retry/brake536_gate_result.json').read_text())
    assert pref['native_pair_eligible'] and pref['status']=='BRAKE_MODEL_NATIVE_ELIGIBLE'
    if (D/'NATIVE_STARTED.json').exists():raise RuntimeError('NO_NATIVE_SCIENTIFIC_RETRY')
    def ready(x):
        if isinstance(x,np.generic):return x.item()
        if isinstance(x,np.ndarray):return x.tolist()
        raise TypeError(type(x).__name__)
    def sha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,default=ready).encode()).hexdigest()
    admitted=[len(list(D.iterdir())),sum(p.stat().st_size for p in D.iterdir())]
    def save(path,x):
        data=(json.dumps(x,indent=2,default=ready,allow_nan=False)+'\n').encode()
        if admitted[0]>=8192 or admitted[1]+len(data)+65536>128*1024**2:raise RuntimeError('PRIVATE_CAP')
        with path.open('xb') as f:f.write(data)
        if D in path.parents:admitted[0]+=1;admitted[1]+=len(data)
        path.chmod(0o600 if D in path.parents else 0o644)
    def guard(*a):
        if time.process_time()-cpu>=900 or time.perf_counter()-started>=1080:raise RuntimeError('NATIVE_COST_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,900)
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,1080)
    assert all(hashlib.sha256((G/n).read_bytes()).hexdigest()==h for n,h in c['source_sha256'].items())
    case=json.loads((D/'approved-case-private.json').read_text());assert hashlib.sha256((D/'approved-case-private.json').read_bytes()).hexdigest()==c['case_private_sha256']
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text())
    registered=json.loads((D/'native-registration-private.json').read_text());assert hashlib.sha256((G/'retry/brake536_native_final.py').read_bytes()).hexdigest()==registered['native_source_sha256']
    assert hashlib.sha256((D/'frozen-paths-private.json').read_bytes()).hexdigest()==c['fixed_path_sha256']==registered['paths_sha256']
    fixed=json.loads((D/'frozen-paths-private.json').read_text());old525=json.loads(Path('/workspace/haic-response525-private/frozen-paths-private.json').read_text());assert hashlib.sha256(Path('/workspace/haic-response525-private/frozen-paths-private.json').read_bytes()).hexdigest()==registered['baseline525_paths_sha256']
    paths=dict(baseline=old525['governor'],baseline_backup=old525['baseline'],candidate=fixed['candidate'],backup=fixed['backup']);forecast_geometry=geometry_context(static,85000)
    from core.vendor.car_racing import CarRacing,TRACK_WIDTH
    from core.vendor.car_dynamics import Car
    from Box2D.b2 import polygonRadius
    from gymnasium.wrappers import TimeLimit
    from env_wrapper import CarEnvironment
    from damage import calculate_damage_effects
    lines=(G/'core/vendor/car_dynamics.py').read_text().splitlines();rawline=next(i+1 for i,s in enumerate(lines) if 'if abs(force) > 2.0 * friction_limit' in s);finalline=next(i+1 for i,s in enumerate(lines) if 'w.omega -= dt * f_force' in s)
    save(D/'NATIVE_STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/brake536_contract.json').read_bytes()).hexdigest()))
    counts=dict(worlds=0,closed=0,resets=0,actions=0,raw_attempts=0,raw_completed=0);model=[0];force_evals=0;planner_cost=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0);pair_initial=None;pair_prefix=None;arms=[];skin=2*float(polygonRadius)
    live=dict(raw=None,env=None)
    def exit_counters():
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);sys.settrace(None);cleanup=None
        if live['raw'] is not None:
            try:
                (live['env'] or live['raw']).close();cleanup=dict(body_count=live['raw'].world.bodyCount,joint_count=live['raw'].world.jointCount)
                if cleanup['body_count']==cleanup['joint_count']==0:counts['closed']+=1
            except BaseException as exc:cleanup=dict(error=type(exc).__name__+':'+str(exc))
            live.update(raw=None,env=None)
        with (D/'native-exit-counters-private.json').open('w') as f:json.dump(dict(counts=counts,model_ticks=model[0],explicit_force_evaluations=force_evals+planner_cost['force_evaluations'],planner_cost=planner_cost,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-started,emergency_cleanup=cleanup),f,indent=2)
    atexit.register(exit_counters)
    def ids(car):return tuple(tuple(sorted(t.idx for t in w.tiles)) for w in car.wheels)
    for budget in ('baseline','candidate'):
        guard();assert counts['worlds']<2;counts['worlds']+=1;label=budget;path=paths[budget]
        raw=CarRacing(**case['base']);live['raw']=raw;env=CarEnvironment(TimeLimit(raw,max_episode_steps=case['TimeLimit_max_episode_steps']),**case['wrapper']);live['env']=env;original_step=raw.step;original_reset=raw.reset
        st=dict(mode_counts={},lap_progress=None,reference_arc=None,unused_startup_over=0.,force_groups={g:dict(peak=0.,samples=0,clipped=0) for g in ('launch','running')},phase='reset',resets=0,reset_ticks=0,actions=0,action_ticks=0,active=None,pred=None,flags=[],mesh=None,ticks=[],events={},epoch=None,minimum=float('inf'),max_path_error=0.,max_ref_over=0.,force_peak=0.,clipped=0,samples=0,force_oracle_max=0.,impulse_max=0.)
        def reset(**kwargs):
            guard()
            if st['resets'] or counts['resets']>=2:raise RuntimeError('RESET_CAP')
            st['resets']+=1;counts['resets']+=1;save(D/('reset-charge-'+label+'.json'),dict(counts));return original_reset(**kwargs)
        def step(action):
            nonlocal force_evals
            guard()
            if counts['raw_attempts']>=4102 or (st['phase']=='reset' and st['reset_ticks']>=51):raise RuntimeError('RAW_CAP')
            if st['mesh'] is None:
                st['mesh']=native_roads(raw.road);st['index']=bounds(st['mesh']);st['base']=[p for p,mu in st['mesh']];st['edge']=track_boundary(raw.track,TRACK_WIDTH);st['edgeindex']=boundary_index(st['edge'])
            before=observed_state(raw.car);position=com(raw.car,True);clock=raw.t;used=ids(raw.car);effects=(raw.car.grip_multiplier,raw.car.engine_multiplier,raw.car.steering_multiplier)
            sensor=tuple(indexed_contacts([tuple(w.GetWorldPoint(v)) for v in w.fixtures[0].shape.vertices],st['mesh'],st['index'],skin) for w in raw.car.wheels)
            oracle=[];beforeplanar=None;actual={}
            if st['phase']=='action':
                before_root=context(raw.car,raw.road,st['active'],skin=skin);beforeplanar=asdict(before_root.planar);oracle=force_rows(before_root,st['active']);force_evals+=4
                if force_evals+planner_cost['force_evaluations']>400000:raise RuntimeError('MODEL_FORCE_EVAL_CAP')
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
                if st['pred'] is not None:
                    force_prediction_error=max(abs(actual[i]['ratio']-st['pred'][st['action_ticks']-1]['force_ratios'][i]) for i in range(4));forecast_error['max_force_ratio_error']=force_prediction_error
                    if force_prediction_error>.19:errors.append('WHEEL_FORCE_PREDICTION')
                if source_error>.05:errors.append('SOURCE_FORCE_ORACLE')
                if impulse_error>.01:errors.append('SOURCE_COM_IMPULSE')
            body_speed_max=max(math.hypot(*body.linearVelocity) for body in [raw.car.hull,*raw.car.wheels])
            if body_speed_max>=100.:errors.append('BOX2D_TRANSLATION_MODEL_DOMAIN')
            roadgap=clearance(raw.car,st['base'],st['index'],st['edge'],st['edgeindex']);polys=[[tuple(b.GetWorldPoint(v)) for v in f.shape.vertices] for b in [raw.car.hull,*raw.car.wheels] for f in b.fixtures]
            gap=min(roadgap,obstacle_margin(polys,static['obstacles']));st['minimum']=min(st['minimum'],gap)
            if gap<.25:errors.append('ROAD_OR_OBSTACLE_MARGIN')
            if q[4].get('collision',False):errors.append('COLLISION')
            q0=project(position,path,st['lap_progress'] if st['phase']=='action' else None);qp=project(position_after,path,q0['s']);st['lap_progress']=qp['s'];refspeed,ff=reference(qp['s'],path)
            if st['phase']=='action':
                st['max_path_error']=max(st['max_path_error'],qp['distance']);delta=qp['s']-q0['s']
                if delta<-.5 or delta>max(5.,2*math.dist(position_after,position)):errors.append('PROJECTION_VALIDITY')
                if qp['distance']>3:errors.append('PATH_ERROR')
                group='launch' if st['actions']<=24 else 'running';z=st['force_groups'][group];z['peak']=max(z['peak'],max(x['ratio'] for x in actual.values()));z['samples']+=4;z['clipped']+=sum(x['ratio']>1 for x in actual.values())
                if group=='launch':
                    st['unused_startup_over']=max(st['unused_startup_over'],speed-refspeed)
                    if z['peak']>2.5 or (st['actions']==24 and st['action_ticks']==4 and z['clipped']/z['samples']>.15):errors.append('LAUNCH_FORCE_GUARD')
                else:
                    st['max_ref_over']=max(st['max_ref_over'],speed-refspeed)
                    if speed-refspeed>5 or z['peak']>1.25 or z['clipped']/z['samples']>.10:errors.append('DYNAMICS_GUARD')
                if st['reference_arc'] is None and q0['s']<path['length']<=qp['s']:
                    f=(path['length']-q0['s'])/(qp['s']-q0['s']);st['reference_arc']=dict(lower=clock-st['epoch'],upper=raw.t-st['epoch'],time=clock-st['epoch']+.02*f)
                if qp['s']>path['length']+10 and raw.finish_time_s is None:errors.append('NO_OFFICIAL_FINISH_AFTER_ARC')
            record=dict(body_speed_max=body_speed_max,phase=st['phase'],action=st['actions'],time=raw.t,before=asdict(before),before_planar=beforeplanar,before_position=position,position=position_after,velocity=velocity,speed=speed,angle=raw.car.hull.angle,yaw=raw.car.hull.angularVelocity,station=qp['s'],path_error=qp['distance'],reference_speed=refspeed,margin=gap,used_contacts=used,after_contacts=ids(raw.car),effects=effects,forces=list(actual.values()),force_oracle_vector_error_N=source_error,COM_impulse_error_m_s=impulse_error,forecast_error=forecast_error,official_tracker=asdict(raw.finish_line_tracker),official_finished=raw.finish_time_s is not None,visited_tiles=raw.tile_visited_count,errors=errors)
            save(D/('raw-%04d.json'%counts['raw_completed']),record);st['ticks'].append(record);st['flags'].extend(errors)
            if errors:raise RuntimeError('ACTUAL_RAW_GUARD:'+','.join(errors))
            return q
        raw.reset=reset;raw.step=step;rows=[];initial_ok=False;prefix=[];stop='MAX500'
        try:
            obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});assert st['reset_ticks']==51
            geometry=sha(raw.track);obstacles=[[list(o.position),o.radius] for o in raw.track_variables.obstacles]
            assert geometry==case['old_episode']['geometry_sha256_diagnostic_only'] and sha(obstacles)==case['old_episode']['obstacles_sha256_diagnostic_only'] and obstacles==static['obstacles']
            root=context(raw.car,raw.road,[0,0,0],skin=skin);full=sha(dict(root=asdict(root),RNG=raw.np_random.bit_generator.state,observation=hashlib.sha256(obs.tobytes()).hexdigest()))
            assert full==static['full_identity']
            if pair_initial is None:pair_initial=full
            elif full!=pair_initial:raise RuntimeError('PAIR_INITIAL')
            initial_ok=True;st['epoch']=raw.t;st['phase']='action';st['lap_progress']=project(com(raw.car,True),path)['s']
            for i in range(500):
                guard()
                if st['flags']:stop=st['flags'][0];break
                root=context(raw.car,raw.road,[0,0,0],skin=skin)
                action=np.array([steering(root,path,st['lap_progress']),.32,0.],np.float32) if i<24 else nominal(root,path,st['lap_progress'])
                detail=dict(mode='FIXED_LAUNCH' if i<24 else 'BASELINE')
                if i>=24:
                    if force_evals+planner_cost['force_evaluations']+6400>400000:raise RuntimeError('ALL_FORCE_COST_CAP_RESERVE')
                    selector=candidate_choose if budget=='candidate' else baseline_choose
                    kwargs=dict(geometry=forecast_geometry) if budget=='candidate' else {}
                    action,detail=selector(root,path,paths['backup'] if budget=='candidate' else paths['baseline_backup'],st['lap_progress'],model,planner_cost,80000,history=(st['force_groups']['running']['clipped'],st['force_groups']['running']['samples']),**kwargs)
                    if action is None:stop='NO_ADMISSIBLE_ACTION';break
                if force_evals+planner_cost['force_evaluations']>400000:raise RuntimeError('ALL_FORCE_COST_CAP')
                st['mode_counts'][detail['mode']]=st['mode_counts'].get(detail['mode'],0)+1
                assert action.dtype==np.float32 and np.isfinite(action).all() and -1<=action[0]<=1 and 0<=action[1]<=1 and 0<=action[2]<=1 and not(action[1]>0 and action[2]>0)
                if model[0]+4>80000:raise RuntimeError('ALL_MODEL_TICK_CAP')
                force_evals+=16
                predicted,predrows=forecast(root,action,path,st['lap_progress'],bounds(root.roads),model)
                st['active']=action.copy();st['pred']=predrows;st['action_ticks']=0;begin=len(st['ticks'])
                assert counts['actions']<1000;counts['actions']+=1;st['actions']+=1
                save(D/('charge-%03d.json'%counts['actions']),dict(budget=budget,index=i+1,attempted_actual_actions=counts['actions'],research_remaining=c['research_start']-counts['actions'],reserve=84000,reserve_used=0,model_ticks=model[0],explicit_force_evaluations=force_evals+planner_cost['force_evaluations'],planner_cost=planner_cost))
                obs,reward,terminated,truncated,info=env.step(action)
                if not(obs.shape==(4,84,84) and obs.dtype==np.float32 and np.isfinite(obs).all() and 0<=obs.min()<=obs.max()<=1):st['flags'].append('OBSERVATION')
                e=calculate_damage_effects(env.damage.damage)
                if (raw.car.grip_multiplier,raw.car.engine_multiplier,raw.car.steering_multiplier)!=(e.grip_multiplier,e.engine_multiplier,e.steering_multiplier):st['flags'].append('WRAPPER_EFFECT')
                if env.damage.damage>0:st['flags'].append('DAMAGE')
                current=st['ticks'][begin:];root_after=context(raw.car,raw.road,[0,0,0],skin=skin);before_state=asdict(root);before_state.pop('roads');after_state=asdict(root_after);after_state.pop('roads')
                record=dict(governor_mode=detail['mode'],index=i+1,action=action.tolist(),obs_sha256=hashlib.sha256(obs.tobytes()).hexdigest(),speed=math.hypot(*com(raw.car)),progress=info['progress'],raw_ticks=st['action_ticks'],flags=list(dict.fromkeys(st['flags'])),min_margin=min(x['margin'] for x in current))
                save(D/('action-'+label+'-%03d.json'%(i+1)),dict(record=record,governor_detail=detail,before_root_without_roads=before_state,after_root_without_roads=after_state));rows.append(record)
                if i<24:prefix.append(dict(action=record['action'],obs_sha256=record['obs_sha256']))
                # Paths differ; preserve eachlaunchprefix, not a false same-action test.
                if i==23:save(D/('launch-prefix-'+label+'-private.json'),prefix)
                if st['flags']:stop=st['flags'][0];break
                if raw.finish_time_s is not None and info.get('finished',False):stop='OFFICIAL_FINISH';break
                if terminated or truncated:stop='ENV_TERMINAL';break
        except BaseException as error:
            stop='TECHNICAL:'+type(error).__name__+':'+str(error);save(D/('error-'+label+'.json'),dict(error=stop,counts=dict(counts),model_ticks=model[0],explicit_force_evaluations=force_evals+planner_cost['force_evaluations'],planner_cost=planner_cost))
        finally:
            sys.settrace(None);env.close();assert raw.world.bodyCount==raw.world.jointCount==0;live.update(raw=None,env=None);counts['closed']+=1
            error_rows=[x for x in st['ticks'] if x['forecast_error'] is not None]
            item=dict(mode_counts=st['mode_counts'],high_fraction=st['mode_counts'].get('HIGH',0)/max(1,st['actions']-24),budget=budget,stop=stop,initial_identity=initial_ok,actions=st['actions'],reset_ticks=st['reset_ticks'],official_finish=raw.finish_time_s is not None,official_finish_episode_s=raw.finish_time_s-st['epoch'] if raw.finish_time_s is not None else None,confirmation_episode_s=raw.t-st['epoch'] if raw.finish_time_s is not None else None,reference_arc_event=st['reference_arc'],unwrapped_progress=st['lap_progress'],reference_path_length=path['length'],visited_tiles=raw.tile_visited_count,tile_count=len(raw.track),official_tracker=asdict(raw.finish_line_tracker),min_margin_m=st['minimum'],max_path_error_m=st['max_path_error'],max_tracking_overspeed_m_s=st['max_ref_over'],max_unused_startup_reference_difference_m_s=st['unused_startup_over'],force_groups=st['force_groups'],source_force_oracle_max_N=st['force_oracle_max'],source_COM_impulse_max_m_s=st['impulse_max'],max_prediction_errors={k:max((abs(x['forecast_error'][k]) for x in error_rows),default=0.) for k in ('position_m','speed_m_s','angle_rad','yaw_rad_s','max_force_ratio_error')},rows=rows)
            save(D/('close-'+label+'-private.json'),dict(record=item,counts=dict(counts),model_ticks=model[0],explicit_force_evaluations=force_evals+planner_cost['force_evaluations'],planner_cost=planner_cost));arms.append(item)
        if stop!='OFFICIAL_FINISH':break
    signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
    summaries=[{k:v for k,v in a.items() if k not in ('rows','official_tracker')} for a in arms]
    both=len(summaries)==2 and all(a['stop']=='OFFICIAL_FINISH' and a['official_finish'] for a in summaries)
    gain=summaries[0]['official_finish_episode_s']-summaries[1]['official_finish_episode_s'] if both else None
    passed=both and gain>=.50 and summaries[1]['high_fraction']>=.5
    result=dict(status='ACTUAL_OFFICIAL_FINISH_PAIR_PASS' if passed else 'ACTUAL_FULL_PAIR_NOT_QUALIFIED',arms=summaries,both_actual_official_finishes=both,official_finish_gain_s=gain,practical_effect_gate=passed,counts=counts,native_model_integrator_ticks=model[0],all_model_integrator_ticks=pref['model_integrator_ticks']+model[0],native_explicit_force_evaluations=force_evals+planner_cost['force_evaluations'],all_model_wheel_force_evaluations=pref['explicit_force_evaluations']+force_evals+planner_cost['force_evaluations'],native_planner_cost=planner_cost,research_remaining=c['research_start']-counts['actions'],reserve=84000,reserve_used=0,native_CPU_s=time.process_time()-cpu,native_wall_s=time.perf_counter()-started,preflight_model_ticks=pref['model_integrator_ticks'],preflight_explicit_force_evaluations=pref['explicit_force_evaluations'],native_geometry_checks=planner_cost.get('geometry_checks',0),all_geometry_checks=pref['planner_cost']['geometry_checks']+planner_cost.get('geometry_checks',0),total_CPU_s=pref['CPU_s']+time.process_time()-cpu,total_wall_s=pref['wall_s']+time.perf_counter()-started,scope='536fixed533path/535footprintplusbroaderbrake+internal.001buffer vsfreshactual525.535failurepreserved. Actualpackagecomparisonnotpath-alone/optimality/pixel/11sclaim;528actualunvalidated.')
    save(D/'native-full-records-private.json',arms);save(D/'budget-final-private.json',dict(counts=counts,research_remaining=result['research_remaining'],reserve=84000,reserve_used=0,model_ticks=model[0],explicit_force_evaluations=force_evals+planner_cost['force_evaluations'],planner_cost=planner_cost));save(G/'retry/brake536_native_result.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':run()
