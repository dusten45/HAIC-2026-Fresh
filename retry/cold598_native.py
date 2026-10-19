"""598 reuses594 native arm with explicit candidate transition and complete meters."""
import time
BOOT_CPU=time.process_time();BOOT_WALL=time.perf_counter()
from retry.cold594_native import *
from retry.cold598_support import Support,INPUTS,CAPS,LIMITS,G,D,C
CPU=BOOT_CPU;WALL=BOOT_WALL
class Study(Support):
 def __init__(self):super().__init__(BOOT_CPU,BOOT_WALL)
 def arm(self,label):
  self.label=label;self.arm_counts=Counter();self.armCPU=time.process_time();self.armWall=time.perf_counter();self.world_reserve(label);self.stage='science';self.scCPU=time.process_time();self.scWall=time.perf_counter();self.add('worlds');self.journal.append('WORLD_CHARGED',label=label,counts=dict(self.counts));raw=env=None;st=None;rows=[];stop='MAX_ACTIONS';error=None;initial_ok=False;official=None;pred_errors=[]
  try:
   self.add('world_constructor_calls');raw=CarRacing(**self.case['base']);self.native_live=raw;env=CarEnvironment(TimeLimit(raw,max_episode_steps=self.case['TimeLimit_max_episode_steps']),**self.case['wrapper']);self.env_live=env;original_step=raw.step;original_reset=raw.reset;path=self.paths[label];skin=2*float(polygonRadius)
   st=dict(mode_counts={},lap_progress=None,reference_arc=None,unused_startup_over=0.,force_groups={g:dict(peak=0.,samples=0,clipped=0) for g in ('launch','running')},phase='reset',resets=0,reset_ticks=0,actions=0,action_ticks=0,active=None,pred=None,flags=[],mesh=None,ticks=[],epoch=None,minimum=float('inf'),max_path_error=0.,max_ref_over=0.,force_oracle_max=0.,impulse_max=0.,max_body=0.)
   def ids(car):return tuple(tuple(sorted(t.idx for t in w.tiles)) for w in car.wheels)
   lines=(G/'core/vendor/car_dynamics.py').read_text().splitlines();rawline=next(i+1 for i,s in enumerate(lines) if 'if abs(force) > 2.0 * friction_limit' in s);finalline=next(i+1 for i,s in enumerate(lines) if 'w.omega -= dt * f_force' in s)
   def reset(**kwargs):
    self.capacity(dict(resets=1))
    if st['resets']:raise IdentityStop('UNEXPECTED_SECOND_RESET')
    st['resets']+=1;self.add('resets');self.journal.append('RESET_CHARGED',label=label,counts=dict(self.counts));self.add('reset_calls');return original_reset(**kwargs)
   def step(action):
    self.guard()
    if st['phase']=='reset' and st['reset_ticks']>=51:raise IdentityStop('RESET_RAW51_CAP')
    if st['mesh'] is None:st['mesh']=native_roads(raw.road);st['index']=bounds(st['mesh']);st['base']=[p for p,mu in st['mesh']];st['edge']=track_boundary(raw.track,TRACK_WIDTH);st['edgeindex']=boundary_index(st['edge'])
    before=observed_state(raw.car);position=com(raw.car,True);clock=raw.t;used=ids(raw.car);effects=(raw.car.grip_multiplier,raw.car.engine_multiplier,raw.car.steering_multiplier);sensor=tuple(indexed_contacts([tuple(w.GetWorldPoint(v)) for v in w.fixtures[0].shape.vertices],st['mesh'],st['index'],skin) for w in raw.car.wheels);oracle=[];actual={};beforeplanar=None
    if st['phase']=='action':
     self.capacity(dict(external_force=4));before_root=context(raw.car,raw.road,st['active'],skin=skin);beforeplanar=asdict(before_root.planar);self.journal.append('BEFORE_NATIVE_ORACLE',root=self.short(before_root),action=st['active'].tolist(),label=label);oracle=d.force_rows(before_root,st['active']);self.add('native_oracle_groups')
    def trace(frame,event,arg):
     if frame.f_code is Car.step.__code__:
      if event=='line' and frame.f_lineno in (rawline,finalline):
       x=frame.f_locals;j=raw.car.wheels.index(x['w']);item=actual.setdefault(j,dict(wheel=j))
       if frame.f_lineno==rawline:self.add('native_wheel_observed');item.update(ratio=float(x['force']/x['friction_limit']),friction=float(x['friction_limit']))
       else:item['vector']=[float(x['f_force']*x['forw'][k]+x['p_force']*x['side'][k]) for k in range(2)]
      return trace
     return None
    self.capacity(dict(raw_attempts=1,native_wheel_reserved=4,geometry=1));self.add('raw_attempts');self.add('native_wheel_reserved',4);self.journal.append('BEFORE_NATIVE_RAW',label=label,phase=st['phase'],action=st['actions'],clock=clock,counts=dict(self.counts),**native_input_fields(before,action),before_position=position,tracker=asdict(raw.finish_line_tracker),visited=sorted(t.idx for t in raw.road if t.road_visited));sys.settrace(trace)
    try:
     self.add('native_raw_calls');q=original_step(action)
    finally:sys.settrace(None)
    self.add('raw_completed');st['reset_ticks' if st['phase']=='reset' else 'action_ticks']+=1;errors=[]
    if len(actual)!=4 or any('vector' not in x or 'ratio' not in x for x in actual.values()):raise RuntimeError('SOURCE_FORCE_CAPTURE')
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
     source_error=max(math.dist(oracle[i]['vector'],actual[i]['vector']) for i in range(4));st['force_oracle_max']=max(st['force_oracle_max'],source_error);expected=tuple(before.velocity[j]+.02*sum(actual[i]['vector'][j] for i in range(4))/before.mass for j in range(2));impulse_error=math.dist(expected,velocity);st['impulse_max']=max(st['impulse_max'],impulse_error)
     if st['pred'] is not None:
      force_prediction_error=max(abs(actual[i]['ratio']-st['pred'][st['action_ticks']-1]['force_ratios'][i]) for i in range(4));forecast_error['max_force_ratio_error']=force_prediction_error
      if force_prediction_error>.19:errors.append('WHEEL_FORCE_PREDICTION')
     if source_error>.05:errors.append('SOURCE_FORCE_ORACLE')
     if impulse_error>.01:errors.append('SOURCE_COM_IMPULSE')
    maxbody=max(math.hypot(*b.linearVelocity) for b in [raw.car.hull,*raw.car.wheels]);st['max_body']=max(st['max_body'],maxbody)
    if not math.isfinite(maxbody) or maxbody>=100:errors.append('BOX2D_TRANSLATION_MODEL_DOMAIN')
    self.capacity(dict(geometry=1));self.add('geometry');roadgap=clearance(raw.car,st['base'],st['index'],st['edge'],st['edgeindex']);polys=[[tuple(b.GetWorldPoint(v)) for v in f.shape.vertices] for b in [raw.car.hull,*raw.car.wheels] for f in b.fixtures];gap=min(roadgap,obstacle_margin(polys,self.static['obstacles']));st['minimum']=min(st['minimum'],gap)
    if gap<.25:errors.append('ROAD_OR_OBSTACLE_MARGIN')
    if q[4].get('collision',False):errors.append('COLLISION')
    q0=d.project(position,path,st['lap_progress'] if st['phase']=='action' else None);qp=d.project(position_after,path,q0['s']);st['lap_progress']=qp['s'];refspeed,_=d.reference(qp['s'],path)
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
    record=dict(projection_delta=qp['s']-q0['s'],projection_lower=-.5,projection_upper=max(5.,2*math.dist(position_after,position)),native_geometry_flags=dict(FOOTPRINT=gap<.25,PATH=qp['distance']>3,PROJECTION_BACKWARD=qp['s']-q0['s']<-.5,PROJECTION_FORWARD=qp['s']-q0['s']>max(5.,2*math.dist(position_after,position))),label=label,body_speed_max=maxbody,phase=st['phase'],action=st['actions'],time=raw.t,before=asdict(before),before_planar=beforeplanar,before_position=position,position=position_after,velocity=velocity,speed=speed,angle=raw.car.hull.angle,yaw=raw.car.hull.angularVelocity,station=qp['s'],path_error=qp['distance'],reference_speed=refspeed,margin=gap,used_contacts=used,after_contacts=ids(raw.car),effects=effects,forces=list(actual.values()),force_oracle_vector_error_N=source_error,COM_impulse_error_m_s=impulse_error,forecast_error=forecast_error,official_tracker=asdict(raw.finish_line_tracker),official_finished=raw.finish_time_s is not None,visited_tiles=raw.tile_visited_count,errors=errors);self.journal.append('AFTER_NATIVE_RAW',record=record,counts=dict(self.counts));st['ticks'].append(record);st['flags'].extend(errors)
    if errors:raise SafetyStop(','.join(errors))
    return q
   raw.reset=reset;raw.step=step;obs,_=env.reset(seed=self.case['seed'],options={'track_id':self.case['track_id']})
   if st['reset_ticks']!=51:raise IdentityStop('RESET51_IDENTITY')
   ready=lambda x:plain(x);oldhash=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,default=ready).encode()).hexdigest();obstacles=[[list(o.position),o.radius] for o in raw.track_variables.obstacles]
   if oldhash(raw.track)!=self.case['old_episode']['geometry_sha256_diagnostic_only'] or oldhash(obstacles)!=self.case['old_episode']['obstacles_sha256_diagnostic_only'] or obstacles!=self.static['obstacles']:raise IdentityStop('GEOMETRY_OBSTACLES_IDENTITY')
   root=context(raw.car,raw.road,[0,0,0],skin=skin);full=oldhash(dict(root=asdict(root),RNG=raw.np_random.bit_generator.state,observation=hashlib.sha256(obs.tobytes()).hexdigest()))
   if full!=self.static['full_identity']:raise IdentityStop('INITIAL_FULL_IDENTITY')
   initial_ok=True;st['epoch']=raw.t;st['phase']='action';st['lap_progress']=d.project(com(raw.car,True),path)['s']
   for i in range(LIMITS[label]['actions']):
    self.current=dict(label=label,next_hold=i+1);self.reserve_hold();root=context(raw.car,raw.road,[0,0,0],skin=skin);before_actual=self.hash(dict(root=self.short(root),tracker=asdict(raw.finish_line_tracker),visited=sorted(t.idx for t in raw.road if t.road_visited),clock=raw.t,groups=st['force_groups'],actuators=[(w.steer,w.gas,w.brake,w.omega) for w in raw.car.wheels],RNG=raw.np_random.bit_generator.state,damage=env.damage.damage,offtrack=env.off_track_counter,stack_sha256=hashlib.sha256(env.stack_state.tobytes()).hexdigest()))
    self.model_mode='baseline_selection' if label=='baseline' else 'candidate_selection'
    if label=='baseline':
     if i<24:
      z=st['force_groups']['launch'];action,detail=launch.choose_launch(root,path,self.backup,st['lap_progress'],i,(z['clipped'],z['samples']),self.model,self.planner,90000,self.geometry_context,guard=self.guard)
     else:
      z=st['force_groups']['running'];action,detail=tracking.choose(root,path,self.backup,st['lap_progress'],self.model,self.planner,90000,history=(z['clipped'],z['samples']),geometry=self.geometry_context)
     if action is None or not detail.get('final_recertified') or not any(q['mode']=='FINAL' and q['ok'] for q in detail.get('reports',[])):
      atomic_write(D/f'certificate-rejected-{label}-{i+1:03d}-private.json',dict(detail=detail,root=self.short(root)));raise CertificateStop('BASELINE_NO_FRESH_FINAL')
    else:
     action,detail=self.candidate_select(root,path,st,i,raw,skin)
    if self.hash(dict(root=self.short(context(raw.car,raw.road,[0,0,0],skin=skin)),tracker=asdict(raw.finish_line_tracker),visited=sorted(t.idx for t in raw.road if t.road_visited),clock=raw.t,groups=st['force_groups'],actuators=[(w.steer,w.gas,w.brake,w.omega) for w in raw.car.wheels],RNG=raw.np_random.bit_generator.state,damage=env.damage.damage,offtrack=env.off_track_counter,stack_sha256=hashlib.sha256(env.stack_state.tobytes()).hexdigest()))!=before_actual:raise IdentityStop('FORECAST_MUTATED_ACTUAL')
    if action.dtype!=np.float32 or not np.isfinite(action).all() or not(-1<=action[0]<=1 and 0<=action[1]<=1 and 0<=action[2]<=1) or action[1]*action[2]!=0:raise IdentityStop('PAYLOAD_DOMAIN')
    self.model_mode='four_raw_prediction';_,predrows=preview.forecast(root,action,path,st['lap_progress'],bounds(root.roads),self.model);st['active']=action.copy();st['pred']=predrows;st['action_ticks']=0;begin=len(st['ticks']);self.capacity(dict(actions=1));self.add('actions');st['actions']+=1;st['mode_counts'][detail['mode']]=st['mode_counts'].get(detail['mode'],0)+1
    self.journal.append('ACTION_CHARGED',label=label,index=i+1,payload=action.tolist(),payload_bits=action.tobytes().hex(),counts=dict(self.counts),research_remaining=22548-self.counts['actions'],certificate=detail,prediction=predrows,before_root=self.short(root),tracker=asdict(raw.finish_line_tracker),clock=raw.t,visited=sorted(t.idx for t in raw.road if t.road_visited));self.add('action_calls');obs,reward,terminated,truncated,info=env.step(action)
    if not(obs.shape==(4,84,84) and obs.dtype==np.float32 and np.isfinite(obs).all() and 0<=obs.min()<=obs.max()<=1):st['flags'].append('OBSERVATION')
    e=calculate_damage_effects(env.damage.damage)
    if (raw.car.grip_multiplier,raw.car.engine_multiplier,raw.car.steering_multiplier)!=(e.grip_multiplier,e.engine_multiplier,e.steering_multiplier):st['flags'].append('WRAPPER_EFFECT')
    if env.damage.damage>0:st['flags'].append('DAMAGE')
    record=dict(index=i+1,mode=detail['mode'],obs_sha256=hashlib.sha256(obs.tobytes()).hexdigest(),raw_ticks=st['action_ticks'],flags=list(st['flags']));rows.append(record);self.journal.append('ACTION_COMPLETED',label=label,record=record,counts=dict(self.counts));atomic_write(D/'latest-progress-private.json',dict(label=label,actions=st['actions'],drive_raw=self.arm_counts['raw_completed']-51,progress=st['lap_progress'],counts=dict(self.counts),time=self.times()),True)
    if st['flags']:raise SafetyStop(','.join(st['flags']))
    if raw.finish_time_s is not None and info.get('finished',False):stop='OFFICIAL_FINISH';break
    if terminated or truncated:stop='ENV_TERMINAL_WITHOUT_FINISH';break
   else:stop='ACTION_CAP'
   if stop=='OFFICIAL_FINISH':official=finish_raw(raw.finish_time_s,st['epoch'])
   if label=='baseline' and (stop!='OFFICIAL_FINISH' or official!=683 or self.arm_counts['raw_completed']-51!=683):raise IdentityStop('BASELINE_NOT_SAFE_EXACT683RAW')
  except BaseException as exc:
   error=type(exc).__name__+':'+str(exc);stop='COST_CENSORED' if isinstance(exc,CostStop) else 'ACTUAL_SAFETY_FAILURE' if isinstance(exc,SafetyStop) else 'MODEL_DOMAIN_STOP' if isinstance(exc,DomainStop) else 'CERTIFICATE_REJECTED' if isinstance(exc,CertificateStop) else 'IDENTITY_FAILURE' if isinstance(exc,IdentityStop) else 'TECHNICAL_FAILURE';atomic_write(D/f'failure-{label}-private.json',dict(error=error,current=self.current,traceback=traceback.format_exc(),counts=dict(self.counts),arm_counts=dict(self.arm_counts),tracker=asdict(raw.finish_line_tracker) if raw is not None and raw.finish_line_tracker else None))
  finally:
   sys.settrace(None);cleanup=None
   if raw is not None:
    try:
     (env or raw).close();cleanup=dict(body=raw.world.bodyCount,joint=raw.world.jointCount)
     if cleanup['body']!=0 or cleanup['joint']!=0:raise RuntimeError('BODY_JOINT_LEAK')
     self.add('closed')
    except BaseException as exc:stop='TECHNICAL_FAILURE';error=(error or '')+';CLEANUP:'+str(exc);cleanup=dict(error=str(exc))
   self.native_live=self.env_live=None;self.scienceCPU+=time.process_time()-self.scCPU;self.scienceWall+=time.perf_counter()-self.scWall;self.stage='audit';item=dict(label=label,stop=stop,error=error,initial_identity=initial_ok,official_finish_raw=official,official_finish_episode_s=(raw.finish_time_s-st['epoch'] if raw is not None and raw.finish_time_s is not None and st and st['epoch'] is not None else None),confirmation_episode_s=(raw.t-st['epoch'] if st and st['epoch'] is not None else None),counts=dict(self.arm_counts),cleanup=cleanup,mode_counts=st['mode_counts'] if st else {},force_groups=st['force_groups'] if st else {},minimum_margin_m=st['minimum'] if st and math.isfinite(st['minimum']) else None,maximum_body_speed_m_s=st['max_body'] if st else None,maximum_path_error_m=st['max_path_error'] if st else None,maximum_reference_excess_m_s=st['max_ref_over'] if st else None,force_oracle_max_N=st['force_oracle_max'] if st else None,COM_impulse_max_m_s=st['impulse_max'] if st else None,reference_arc_diagnostic=st['reference_arc'] if st else None,flags=st['flags'] if st else [],CPU_s=time.process_time()-self.armCPU,wall_s=time.perf_counter()-self.armWall)
   if st:
    relevant=[q['forecast_error'] for q in st['ticks'] if q['forecast_error'] is not None];item['max_prediction_errors']={k:max((abs(q[k]) for q in relevant if k in q),default=0.) for k in ['position_m','speed_m_s','angle_rad','yaw_rad_s','max_force_ratio_error']}
   atomic_write(D/f'arm-{label}-private.json',dict(summary=item,rows=rows,raw_records=st['ticks'] if st else []));self.arms.append(item);self.journal.append('WORLD_CLOSED',summary=item,counts=dict(self.counts));self.guard()
  return item

if __name__=='__main__':Study().run()
