"""474 saved-only spatial/time alignment; stdlib geometry, no actor or physics imports."""
import bisect,hashlib,importlib.abc,json,math,os,sys,time
from pathlib import Path

G=Path(__file__).resolve().parents[1]
RUNS={'473_Original':('stage473/whole_OriginalReference-private.json','stage473/whole_OriginalReference-observer-private.json'),
      '473_P4':('stage473/whole_Projected4Reference-private.json','stage473/whole_Projected4Reference-observer-private.json'),
      '472_nativeP4':('stage472-native/actual_Projected4ReferenceCommonPulse/trace-private.jsonl',None),
      '442_nativeC0':('stage442/actual_C0/trace-private.jsonl',None),
      '442_nativeP':('stage442/actual_P/trace-private.jsonl',None)}

class NoPhysics(importlib.abc.MetaPathFinder):
    def __init__(self):self.attempts=[]
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in ('Box2D','gym','gymnasium','core') or fullname.startswith(('retry.terminal','retry.pilot','retry.native','retry.paired','retry.law')):
            self.attempts.append(fullname);raise RuntimeError('474_FORBIDDEN_PHYSICS_IMPORT:'+fullname)
        return None

def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def put(path,obj):
    with Path(path).open('x') as f:json.dump(obj,f,indent=2,allow_nan=False);f.write('\n')
def wrap(a):return (a+math.pi)%(2*math.pi)-math.pi
def avg(xs):return sum(xs)/len(xs) if xs else None
def norm(v):return math.hypot(*v)

def source_paths(root):
    root=Path(root);paths=[root/'stage473/plan.json',root/'stage472/plan.json',root/'stage442/plan.json']
    for rel,observer in RUNS.values():
        paths.append(root/rel)
        if observer:paths.append(root/observer)
        else:paths.extend([root/rel.replace('trace-private.jsonl',name) for name in ['result.json','initial-private.json']])
    p=read(root/'stage473/plan.json');paths.append(Path(p['fixed_plan']))
    paths.extend(G/x for x in ['retry/audit474_traces.py','core/vendor/car_dynamics.py','retry/headroom413_run.py','retry/observer435.py','retry/terminal410_model.py','core/vendor/car_racing.py'])
    for path in paths:assert path.is_file(),'required source missing:'+str(path)
    return paths

class Geometry:
    def __init__(self,line):
        self.line=line;self.edges=[];self.ds=[];self.arc=[0.]
        for i,a in enumerate(line):
            b=line[(i+1)%len(line)];d=[b[0]-a[0],b[1]-a[1]];length=norm(d);assert length>0
            self.edges.append(d);self.ds.append(length);self.arc.append(self.arc[-1]+length)
    def project(self,pos,phase='FIRST_LAP'):
        candidates=[]
        for i,(a,d,length) in enumerate(zip(self.line,self.edges,self.ds)):
            u=max(0.,min(1.,((pos[0]-a[0])*d[0]+(pos[1]-a[1])*d[1])/(length*length)))
            foot=[a[0]+u*d[0],a[1]+u*d[1]];distance=(pos[0]-foot[0])**2+(pos[1]-foot[1])**2
            vertex=i if u==0 else (i+1)%len(self.line) if u==1 else None
            candidates.append((distance,i,u,vertex))
        minimum=min(c[0] for c in candidates);ties=[c for c in candidates if c[0]==minimum]
        if len(ties)==1 and 0<ties[0][2]<1:_,i,u,_=ties[0]
        else:
            vertices={c[3] for c in ties};assert len(vertices)==1 and None not in vertices,'projection ambiguity'
            node=next(iter(vertices));i,u=(len(self.line)-1,1.) if node==0 and phase in ('FIRST_LAP','FINISH_CONFIRM') else (node,0.)
        d=self.edges[i];heading=math.atan2(d[1],d[0]);prev=self.edges[(i-1)%len(self.line)]
        # A polyline turn-density diagnostic, not the actor's preview/steering law.
        curvature=wrap(heading-math.atan2(prev[1],prev[0]))/(.5*(self.ds[i-1]+self.ds[i]))
        return dict(arc=self.arc[i]+u*self.ds[i],index=i,u=u,path_error_m=math.sqrt(minimum),heading=heading,kappa_polyline=curvature)

def axle_metrics(tires):
    result={}
    for name,ids in [('front',(0,1)),('rear',(2,3))]:
        group=[t for t in tires if t['wheel'] in ids];assert len(group)==2
        clipped=[];lost=[];lateral=[];longitudinal=[];shares=[];retentions=[];inferred_errors=[]
        for t in group:
            magnitude=math.hypot(t['raw_long_N'],t['raw_lat_N']);factor=min(1.,t['friction_limit']/magnitude) if magnitude else 1.
            clipped.append(abs(t['raw_lat_N'])*factor);lost.append(abs(t['raw_lat_N'])*(1-factor))
            lat=abs(t['raw_lat_N'])/t['friction_limit'];long=abs(t['raw_long_N'])/t['friction_limit'];lateral.append(lat);longitudinal.append(long)
            shares.append(t['raw_long_N']**2/magnitude**2 if magnitude else 0.);retentions.append(1/max(1,t['force_ratio']))
            if t['force_ratio']>0:inferred_errors.append(abs(magnitude/t['force_ratio']-t['friction_limit']))
        result[name]=dict(joint_mean=avg([t['joint_angle'] for t in group]),force_ratio_max=max(t['force_ratio'] for t in group),
            clipped_wheels=sum(bool(t['clipped']) for t in group),raw_lat_abs_N=avg([abs(t['raw_lat_N']) for t in group]),
            raw_long_abs_N=avg([abs(t['raw_long_N']) for t in group]),lat_after_vector_clip_abs_N=avg(clipped),lat_lost_to_vector_clip_abs_N=avg(lost),
            lateral_slip_abs_m_s=avg([abs(t['lateral_slip_m_s']) for t in group]),longitudinal_slip_abs_m_s=avg([abs(t['longitudinal_slip_m_s']) for t in group]),
            wheel_forward_speed_mean=avg([t['forward_speed_m_s'] for t in group]),applied_gas_mean=avg([t['gas'] for t in group]),applied_brake_mean=avg([t['brake'] for t in group]))
        result[name].update(lat_only_ratio_max=max(lateral),long_only_ratio_max=max(longitudinal),longitudinal_squared_share_mean=avg(shares),clip_retention_min=min(retentions),
            clipped_with_lat_only_within_limit=sum(bool(t['clipped']) and lat<=1 for t,lat in zip(group,lateral)),
            clipped_with_lat_only_above_limit=sum(bool(t['clipped']) and lat>1 for t,lat in zip(group,lateral)),
            inferred_limit_max_abs_error=max(inferred_errors,default=0.))
    return result

def points_for(root,label,geom):
    rel,observer=RUNS[label];model=observer is not None;payload=read(root/rel) if model else None
    rows=payload['rows'] if model else [json.loads(s) for s in (root/rel).read_text().splitlines() if s]
    posts=read(root/observer)['posts'] if model else None;points=[];postindex=0;tick=0;commands=[]
    for wi,row in enumerate(rows):
        hulls=row['raw_hull'];tires=row['tires'] if model else row['raw_tire_samples'];n=row['predicted']['raw_ticks'] if model else row['raw_ticks'];assert len(hulls)==n
        command=row['command'];commands.append(dict(wrapper=wi+1,time=hulls[0]['time'],command=command,previous=row['memory_before'].get('laststeer'),
            command_steer_rate_per_s=(command[0]-row['memory_before'].get('laststeer',command[0]))/.08))
        memory_after=row['memory_after'] if model else row['nominal_memory_after']
        phase=memory_after.get('C',{}).get('phase','FIRST_LAP')
        filtered=memory_after['laststeer'];previous=row['memory_before']['laststeer'];unfiltered=(filtered-.2*previous)/.8
        commands[-1].update(filtered_nominal_steer=filtered,reconstructed_clipped_pursuit=unfiltered,
                            actual_steer_matches_filtered_nominal=abs(command[0]-filtered)<1e-7)
        for k,hull in enumerate(hulls):
            tick+=1;selected=[t for t in tires if t['raw_tick']==k+1];assert sorted(t['wheel'] for t in selected)==[0,1,2,3]
            pre=geom.project(hull['origin_position'],phase);speed=norm(hull['COM_linear_velocity']);origin_speed=norm(hull['origin_linear_velocity'])
            if posts is not None:
                post=posts[postindex];postindex+=1;position=post['position'];velocity=post['velocity'];posttime=post['time'];frozen_guard_path=post['path_error_m']
            else:
                next_hull=hulls[k+1] if k+1<n else None
                position=next_hull['origin_position'] if next_hull else row['post']['pos'];velocity=next_hull['COM_linear_velocity'] if next_hull else row['post']['vel']
                posttime=next_hull['time'] if next_hull else row['post']['time']
            assert abs(posttime-hull['time']-.02)<1e-8,'pre/post50Hz mismatch'
            postq=geom.project(position,phase);axles=axle_metrics(selected);desired_yaw=speed*pre['kappa_polyline']
            postpath=postq['path_error_m']
            if posts is None:frozen_guard_path=max(pre['path_error_m'],postpath)
            point=dict(run=label,model=model,wrapper=wi+1,raw_tick=tick,raw_tick_in_wrapper=k+1,
                pre_time=hull['time'],post_time=posttime,wrapper_elapsed_pre=hull['time']-1.02,
                pre_origin=hull['origin_position'],pre_COM=hull['COM_world'],pre_COM_velocity=hull['COM_linear_velocity'],pre_origin_velocity=hull['origin_linear_velocity'],
                speed_COM=speed,speed_origin=origin_speed,pre_arc=pre['arc'],post_arc=postq['arc'],pre_path_error_m=pre['path_error_m'],post_path_error_m=postpath,
                frozen_guard_path_error_m=frozen_guard_path,frozen_guard_source='stored_observer_max_pre_post' if model else 'reconstructed_max_pre_post_from_native_snapshots',
                angle=hull['angle'],heading_error_rad=wrap(hull['angle']+math.pi/2-pre['heading']),velocity_heading_error_rad=wrap(math.atan2(hull['COM_linear_velocity'][1],hull['COM_linear_velocity'][0])-pre['heading']) if speed>1e-6 else None,
                yaw=hull['yaw'],kappa_polyline=pre['kappa_polyline'],desired_yaw_v_kappa_polyline=desired_yaw,yaw_minus_v_kappa=hull['yaw']-desired_yaw,
                command=command,steer_target_joint=-command[0],steer_command_saturated=abs(command[0])>=.4-1e-7,
                filtered_nominal_steer=filtered,reconstructed_clipped_pursuit=unfiltered,prefilter_delta=filtered-unfiltered,
                actual_steer_matches_filtered_nominal=abs(command[0]-filtered)<1e-7,
                front_joint_error=axles['front']['joint_mean']+command[0],axles=axles,
                stored_wrapper_safety=row['safety'],stored_wrapper_end_time=row['predicted']['time'] if model else row['post']['time'])
            point['front_joint_rate_per_s']=None if not points else (axles['front']['joint_mean']-points[-1]['axles']['front']['joint_mean'])/.02
            point['servo_rate_command_saturated']=abs(point['front_joint_error'])>.06
            point['front_joint_error_to_unfiltered_target']=axles['front']['joint_mean']+unfiltered
            points.append(point)
    if posts is not None:assert postindex==len(posts)
    first_pre=next((p for p in points if p['pre_path_error_m']>3),None)
    first_post=next((p for p in points if p['post_path_error_m']>3),None)
    first_guard=next((p for p in points if p['frozen_guard_path_error_m']>3),None)
    def event(p,phase):return None if p is None else dict(raw_tick=p['raw_tick'],wrapper=p['wrapper'],time=p[phase+'_time'],arc=p[phase+'_arc'],path_error_m=p[phase+'_path_error_m'],phase=phase)
    metadata=dict(model=model,wrappers=len(rows),raw_ticks=len(points),first_pre_world_path_guard=event(first_pre,'pre'),first_post_world_crossing3m=event(first_post,'post'),
                  first_frozen_guard=None if first_guard is None else dict(raw_tick=first_guard['raw_tick'],wrapper=first_guard['wrapper'],pre_time=first_guard['pre_time'],post_report_time=first_guard['post_time'],pre_arc=first_guard['pre_arc'],post_arc=first_guard['post_arc'],path_error_m=first_guard['frozen_guard_path_error_m'],pre_already_over3m=first_guard['pre_path_error_m']>3,post_over3m=first_guard['post_path_error_m']>3,source=first_guard['frozen_guard_source']),
                  first_command=rows[0]['command'],first_physical_time=points[0]['pre_time'],last_physical_time=points[-1]['post_time'],failure=payload.get('error') if model else None,
                  commands=commands)
    if not model:
        result=read((root/rel).parent/'result.json');assert result['completed'] and result['status']=='COMPLETED_SAFE_OFFICIAL'
        metadata.update(completed=True,lap_ms=result['lap_ms'],damage=rows[-1]['damage'],reset_complete_time=rows[0]['raw_hull'][0]['time'])
    return points,metadata

def describe_window(points,lo,hi):
    guard=next((p for p in points if p['pre_path_error_m']>3),None)
    valid=[p for p in points if guard is None or p['pre_time']<=guard['pre_time']]
    chosen=[p for p in valid if lo<=p['pre_arc']<=hi];assert chosen,'empty spatial window'
    first_failure=next((p for p in chosen if p['pre_path_error_m']>3),None)
    def first(predicate):
        p=next((p for p in chosen if predicate(p)),None)
        return None if p is None else dict(pre_time=p['pre_time'],pre_arc=p['pre_arc'],raw_tick=p['raw_tick'],before_first_pre_guard=first_failure is None or p['pre_time']<first_failure['pre_time'])
    result=dict(samples=len(chosen),excluded_after_first_pre_guard_ticks=len(points)-len(valid),time_pre_range=[chosen[0]['pre_time'],chosen[-1]['pre_time']],arc_pre_range=[chosen[0]['pre_arc'],chosen[-1]['pre_arc']],
        max_path_error=max(p['pre_path_error_m'] for p in chosen),speed_COM_range=[min(p['speed_COM'] for p in chosen),max(p['speed_COM'] for p in chosen)],
        max_abs_heading_error=max(abs(p['heading_error_rad']) for p in chosen),max_abs_yaw_minus_v_kappa=max(abs(p['yaw_minus_v_kappa']) for p in chosen),
        mean_abs_front_joint_error=avg([abs(p['front_joint_error']) for p in chosen]),max_abs_front_joint_error=max(abs(p['front_joint_error']) for p in chosen),
        servo_rate_command_saturated_ticks=sum(p['servo_rate_command_saturated'] for p in chosen),max_abs_prefilter_delta=max(abs(p['prefilter_delta']) for p in chosen),
        mean_abs_joint_error_to_unfiltered_target=avg([abs(p['front_joint_error_to_unfiltered_target']) for p in chosen]),
        actual_steer_matches_filtered_nominal_ticks=sum(p['actual_steer_matches_filtered_nominal'] for p in chosen),
        steer_saturated_ticks=sum(p['steer_command_saturated'] for p in chosen),gas_command_ticks=sum(p['command'][1]>0 for p in chosen),brake_command_ticks=sum(p['command'][2]>0 for p in chosen),
        first_command_saturation=first(lambda p:p['steer_command_saturated']),first_front_clip=first(lambda p:p['axles']['front']['clipped_wheels']>0),first_rear_clip=first(lambda p:p['axles']['rear']['clipped_wheels']>0))
    for axle in ('front','rear'):
        result[axle]=dict(max_force_ratio=max(p['axles'][axle]['force_ratio_max'] for p in chosen),clipped_wheel_samples=sum(p['axles'][axle]['clipped_wheels'] for p in chosen),
            max_raw_lat_abs_N=max(p['axles'][axle]['raw_lat_abs_N'] for p in chosen),max_raw_long_abs_N=max(p['axles'][axle]['raw_long_abs_N'] for p in chosen),
            max_lateral_slip_abs=max(p['axles'][axle]['lateral_slip_abs_m_s'] for p in chosen),max_longitudinal_slip_abs=max(p['axles'][axle]['longitudinal_slip_abs_m_s'] for p in chosen),
            vector_clip_lat_loss_integral_N_s=sum(p['axles'][axle]['lat_lost_to_vector_clip_abs_N']*.02 for p in chosen))
        result[axle].update(clipped_with_lat_only_within_limit_wheel_samples=sum(p['axles'][axle]['clipped_with_lat_only_within_limit'] for p in chosen),
            clipped_with_lat_only_above_limit_wheel_samples=sum(p['axles'][axle]['clipped_with_lat_only_above_limit'] for p in chosen),
            lat_only_ratio_max=max(p['axles'][axle]['lat_only_ratio_max'] for p in chosen),long_only_ratio_max=max(p['axles'][axle]['long_only_ratio_max'] for p in chosen),
            first_combined_clip_lat_only_within=first(lambda p:p['axles'][axle]['clipped_with_lat_only_within_limit']>0),
            first_clip_lat_only_above=first(lambda p:p['axles'][axle]['clipped_with_lat_only_above_limit']>0),
            inferred_limit_max_abs_error=max(p['axles'][axle]['inferred_limit_max_abs_error'] for p in chosen))
    grid=[]
    for boundary in range(math.ceil(lo/5)*5,math.floor(hi/5)*5+1,5):
        if not min(p['pre_arc'] for p in valid)<=boundary<=max(p['pre_arc'] for p in valid):continue
        point=min(valid,key=lambda p:abs(p['pre_arc']-boundary));sample={k:point[k] for k in ['pre_time','pre_arc','speed_COM','pre_path_error_m','heading_error_rad','yaw','desired_yaw_v_kappa_polyline','command','steer_target_joint','front_joint_error','axles']}
        sample.update(boundary_arc=boundary,nearest_saved_arc_error_m=abs(point['pre_arc']-boundary),interpolated=False);grid.append(sample)
    result['common5m_grid_nearest_saved_samples']=grid
    return result

def analyze(root,output_dir='/tmp/haic-retry-stage474-private'):
    started=time.process_time();root=Path(root);out=Path(output_dir);assert not(out/'alignment-private.json').exists()
    guard=NoPhysics();sys.meta_path.insert(0,guard)
    assert not any(n.split('.')[0] in ('Box2D','gym','gymnasium') for n in sys.modules),'run in fresh saved-only interpreter'
    p=read(root/'stage473/plan.json');p472=read(root/'stage472/plan.json');p442=read(root/'stage442/plan.json')
    assert sha(p['fixed_plan'])==sha(p472['fixed_plan'])==sha(p442['fixed_plan']),'different fixed line'
    assert p472['case']==p442['case'],'different known DEV case'
    fixed=read(p['fixed_plan']);geom=Geometry(fixed['line']);allpoints={};metadata={}
    for label in RUNS:allpoints[label],metadata[label]=points_for(root,label,geom)
    initials=[read((root/RUNS[label][0]).parent/'initial-private.json') for label in ['472_nativeP4','442_nativeC0','442_nativeP']]
    assert all(x['physical']['hull']==initials[0]['physical']['hull'] for x in initials),'native initial physical hull mismatch'
    windows=[]
    for failed in ['473_Original','473_P4']:
        failure=metadata[failed]['first_pre_world_path_guard'];assert failure
        center=failure['arc'];lo,hi=center-30,center+30
        windows.append(dict(selected_by=failed,selection='POST_HOC_DIAGNOSTIC_FAILURE_ARC_PLUS_MINUS30M_NOT_POLICY_OR_EXPERIMENT_SELECTION',center_arc=center,bounds=[lo,hi],
                            runs={label:describe_window(points,lo,hi) if max(p['pre_arc'] for p in points)>=lo else dict(observed=False,censored_before_window=True,observed_endpoint_arc=points[-1]['post_arc']) for label,points in allpoints.items()}))
    result=dict(stage=474,kind='SAVED_ONLY_TRACE_ALIGNMENT',sources={str(path):sha(path) for path in source_paths(root)},runs=metadata,windows=windows,
        coordinate_contract=dict(arc='same fixed-line canonical projection of hull origin; FIRST_LAP terminal vertex convention',time='physical seconds; wrapper elapsed=physical minus reset1.02; modelroot2.78=elapsed1.76',
            pre='raw_hull at pre-world time; COM and origin velocity retained separately',post='model observer afterWorld; native next pre-world snapshot or wrapper post; timestamp pre+0.02',
            path_guard='post_path_error is pure post geometry for all runs; frozen_guard_path_error separately retains model observer max(pre,post), reconstructed similarly for native; first_frozen_guard post report time does not timestamp its pre component',
            tire='same pre-world tick after engine/brake omega update before joint solver/world and vector friction clip; wheel-frame point velocity',
            steering='front wheels0,1; joint target=-steer command; limits±0.4rad; motor rate cap3rad/s times configured multiplier',
            prefilter='stored float64 laststeer reconstructs clipped pursuit=(after-.2before)/.8; fixed .8/.2 80ms filter has mean age.02s; diagnostic reconstruction is not a simulated ablation',
            curvature='polyline signed turn density diagnostic; v*kappa is not exact controller target; no driver act invoked',
            grids='nearest observed raw pre sample to common5m arc; no interpolated state or extrapolation beyond observed endpoint'),
        inference_limits=['Different closed-loop trajectories, times and controls; spatial alignment is diagnostic, not a randomized counterfactual.',
                          'Clipped with lat-only<=1 establishes algebraic combined-demand contribution at the same wheel state; it is not dynamic evidence from removing longitudinal demand. Lat-only>1 cannot become unclipped merely by removing longitudinal force at that fixed state.',
                          'Raw force demand and common vector clipping establish a mechanism in code; their association here does not isolate its causal contribution.',
                          'Lateral tracking/delay and longitudinal-lateral friction competition are at most two candidate explanations; no policy change or new experiment selected.'],
        physics=dict(new_models=0,native_steps=0,resets=0,SourceC_act_calls=0,import_guard_attempts=guard.attempts),CPU_s=time.process_time()-started)
    out.mkdir(mode=0o700,parents=True,exist_ok=True)
    with (out/'points-private.jsonl').open('x') as f:
        for points in allpoints.values():
            for point in points:f.write(json.dumps(point,allow_nan=False)+'\n')
    put(out/'alignment-private.json',result)
    print(json.dumps(dict(stage=474,runs={k:{q:v[q] for q in ['wrappers','raw_ticks','first_pre_world_path_guard','first_post_world_crossing3m']} for k,v in metadata.items()},windows=len(windows),CPU_s=result['CPU_s'],physics=result['physics'])))
    return result

if __name__=='__main__':analyze(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else '/tmp/haic-retry-stage474-private')
