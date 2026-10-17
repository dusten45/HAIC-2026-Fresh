"""Saved-only 481 diagnostics. This entry point cannot construct or step physics.

Full scalar/command-linked series stays private; the public output is aggregates.
All consumed 481 files and codec references are authenticated against its manifest.
"""
import time
START = time.perf_counter()
import hashlib, json, math, os, signal, sys
from pathlib import Path
import numpy as np
from retry.io481 import read, STATE_KEY, CODEC_KEY
import retry.io481 as codec
from functools import lru_cache
from retry.signed417_executor import canonical_projection
from retry.source_vehicle_transition import SourceVehicleTransition
from retry.terminal410_model import TerminalVehicleTransition

G = Path(__file__).resolve().parents[1]
MIB = 1024**2
# Only immutable saved JSON is cached; codec still authenticates decoded SHA.
codec.ORIGINAL_READ = lru_cache(maxsize=None)(codec.ORIGINAL_READ)

def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False).encode()).hexdigest()

def forbidden(*args, **kwargs):
    raise RuntimeError('482_NEW_PHYSICS_FORBIDDEN')

for cls in (SourceVehicleTransition, TerminalVehicleTransition):
    cls.__init__ = forbidden
    cls.step = forbidden

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def dump(path, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()
    assert len(data) <= 16*MIB
    with Path(path).open('xb') as f:
        f.write(data)

def wrap(x):
    return (x+math.pi)%(2*math.pi)-math.pi

def geometry(line, pos, vel, angle, phase='FIRST_LAP'):
    q = canonical_projection(line, pos, vel, phase)
    j = q['index']; tangent = line[(j+1)%len(line)]-line[j]
    tangent = tangent/np.linalg.norm(tangent)
    normal = np.array([-tangent[1], tangent[0]])
    foot = line[j]+q['u']*(line[(j+1)%len(line)]-line[j])
    forward = np.array([-math.sin(angle), math.cos(angle)])
    return dict(path_error_m=q['path_error_m'], signed_error_m=float((np.asarray(pos)-foot)@normal),
                normal_velocity_m_s=float(np.asarray(vel)@normal), tangent_velocity_m_s=q['sigma'],
                heading_error_deg=math.degrees(math.atan2(float(tangent[0]*forward[1]-tangent[1]*forward[0]),float(tangent@forward))),
                velocity_heading_deg=math.degrees(math.atan2(float(np.asarray(vel)@normal),q['sigma'])),
                projection_side=q['side'], segment=j, fraction=q['u'], arc_m=q['arc'])

def tire_stats(row):
    out = {}
    for label, wheels in [('front',(0,1)),('rear',(2,3))]:
        samples = [t for t in row['tires'] if t['wheel'] in wheels]
        out[label] = dict(max_abs_lateral_slip_m_s=max(abs(t['lateral_slip_m_s']) for t in samples),
            max_abs_longitudinal_slip_m_s=max(abs(t['longitudinal_slip_m_s']) for t in samples),
            max_force_ratio=max(t['force_ratio'] for t in samples),
            max_abs_raw_lateral_N=max(abs(t['raw_lat_N']) for t in samples),
            max_abs_raw_longitudinal_N=max(abs(t['raw_long_N']) for t in samples),
            clipped_samples=sum(t['clipped'] for t in samples), samples=len(samples))
    target = -row['command'][0] # source model calls car.steer(-action[0])
    front = [t for t in row['tires'] if t['wheel']<2]
    out['steering'] = dict(target_joint_rad=target,
        max_abs_pre_force_lag_rad=max(abs(t['joint_angle']-target) for t in front),
        last_pre_force_lag_rad=max(abs(t['joint_angle']-target) for t in front if t['raw_tick']==row['predicted']['raw_ticks']),
        last_pre_force_joint_rad=sum(t['joint_angle'] for t in front if t['raw_tick']==row['predicted']['raw_ticks'])/2)
    return out

def run(root):
    signal.signal(signal.SIGPROF, forbidden);signal.signal(signal.SIGALRM, forbidden)
    signal.setitimer(signal.ITIMER_PROF, 90);signal.setitimer(signal.ITIMER_REAL, 180)
    target = root/'stage482'/'analysis1'; assert not target.exists(); target.mkdir(mode=0o700,parents=True)
    for volume in ('/workspace','/tmp'):
        import shutil
        assert shutil.disk_usage(volume).free >= 512*MIB+16*MIB
    d=root/'stage481'; manifest_path=root/'stage481-retention-manifest-private.json'
    manifest=read(manifest_path); inv={Path(x['path']).name:x for x in manifest['files']}; consumed={}
    def check(path):
        path=Path(path);name=path.name
        if name not in consumed:
            rec=inv[name];assert path.stat().st_size==rec['bytes'] and sha(path)==rec['sha256']
            consumed[name]=rec
            packed=json.loads(path.read_text())
            def refs(x):
                if isinstance(x,dict):
                    if set(x)=={STATE_KEY}:check(d/('state-'+x[STATE_KEY]+'.json'))
                    else:
                        for v in x.values():refs(v)
                elif isinstance(x,list):
                    for v in x:refs(v)
            refs(packed)
        return read(path)
    plan=check(d/'plan.json');material_path=Path(plan['input_material_path'])
    assert sha(material_path)==plan['input_material_sha256'];material=read(material_path)
    line=np.asarray(material['fixed']['line']);ds=np.asarray(material['fixed']['free_profile']['ds']);curve=np.asarray(material['fixed']['free_profile']['curvature']);nodes=np.asarray(material['projected_nodes']);sarc=np.r_[0,np.cumsum(ds)]
    result=check(d/'result.json');online=check(d/'online-private.json');observed=check(d/'online-observer-private.json');queries=result['outcome']['online_queries']
    assert len(online['rows'])==125 and len(observed['posts'])==500 and len(queries)==126
    contexts={}
    for path in sorted(d.glob('context-*-private.json')):
        c=check(path)
        if c['label']=='online':contexts[c['index']+1]=c
    assert set(contexts)==set(range(1,127))
    def risk(row):
        q=row['predicted']; phase=row['memory_after']['C']['phase']
        points=[(h['origin_position'],h['origin_linear_velocity']) for h in row['raw_hull']]+[(q['position'],q['velocity'])]
        error=max(canonical_projection(line,p,v,phase)['path_error_m'] for p,v in points)
        return dict(M80=max(0.,max(t['force_ratio'] for t in row['tires'])-1),max_guard_path_error_m=error,margin_m=3-error,
                    endpoint_path_error_m=row['path_error_m'],endpoint_speed_m_s=q['speed_m_s'],safety=row['safety'])
    series=[]; options_all=[];sacrifices=[];changes=[]
    for i,qry in enumerate(queries,1):
        ctx=contexts[i];h=ctx['state']['physical']['hull'];stategeo=geometry(line,h['position'],h['velocity'],h['angle']);j=stategeo['segment'];u=stategeo['fraction'];speed=math.hypot(*h['velocity'])
        refspeed=float(math.sqrt((1-u)*nodes[j]**2+u*nodes[j+1]**2));feed=float((nodes[j+1]**2-nodes[j]**2)/(2*ds[j]))
        # Exact frozen cursor/preview steering reconstruction, without Controller.act.
        N=len(line);ix=ctx['before']['index'];cand=np.arange(max(0,ix-2),ix+18);closest=int(cand[np.argmin(np.linalg.norm(line[cand%N]-h['position'],axis=1))]);ix=max(ix,closest);ci=ix%N
        edge=line[(ci+1)%N]-line[ci];cu=float(np.clip((np.asarray(h['position'])-line[ci])@edge/max(edge@edge,1e-9),0,1));arc=sarc[ci]+cu*ds[ci];look=max(6.,min(25.,3.24+.22*speed));goal=(arc+look)%sarc[-1];gj=min(N-1,int(np.searchsorted(sarc,goal,side='right')-1));alpha=(goal-sarc[gj])/max(ds[gj],1e-9);delta=line[gj]+alpha*(line[(gj+1)%N]-line[gj])-h['position'];right=np.array([math.cos(h['angle']),math.sin(h['angle'])]);unsmoothed=float(np.clip(np.arctan(2*3.24*float(delta@right)/max(float(delta@delta),1e-6)),-.4,.4));command=.8*unsmoothed+.2*ctx['before']['laststeer']
        assert np.float32(command)==np.float32(ctx['nominal'][0]) and command==ctx['after']['laststeer']
        options=[]; traces={}; candidate_raw={}
        for k,opt in qry['options'].items():
            trace=check(opt['first_path']);row=trace['rows'][0];r=risk(row)
            assert sha(opt['first_path'])==opt['first_sha256']
            assert np.asarray(opt['command'],dtype='<f4').tobytes().hex()==k
            assert abs(r['M80']-opt['M80'])<1e-12 and row['command']==opt['command']
            assert row['command'][0]==ctx['nominal'][0]
            obs=check(Path(opt['first_path']).with_name(Path(opt['first_path']).name.replace('-private.json','-observer-private.json')))
            assert obs['actions'][0]['frozen_row']==row and len(obs['posts'])==row['predicted']['raw_ticks']
            rawpoints=[]
            for z,p in enumerate(obs['posts']):
                endangle=row['raw_hull'][z+1]['angle'] if z+1<len(obs['posts']) else row['predicted']['angle']
                endyaw=row['raw_hull'][z+1]['yaw'] if z+1<len(obs['posts']) else row['predicted']['angular_velocity']
                g=geometry(line,p['position'],p['velocity'],endangle);g.update(raw_tick=z+1,time_s=p['time'],yaw_rad_s=endyaw,guard_path_error_m=p['path_error_m'],road_contacts=p['wheel_road_contacts'],grass=p['grass']);rawpoints.append(g)
            assert abs(max(p['guard_path_error_m'] for p in rawpoints)-r['max_guard_path_error_m'])<1e-10
            firstguard=next((p['raw_tick'] for p in rawpoints if p['guard_path_error_m']>3 or p['road_contacts']<4 or p['grass']),None)
            options.append(dict(key=k,aliases=opt['aliases'],valid=opt['valid'],command=opt['command'],risk=r,tire=tire_stats(row),first_guard_failure_raw_tick=firstguard,raw_diagnostics=rawpoints))
            traces[k]=trace;candidate_raw[k]=obs
        active=1 if ctx['nominal'][1]>0 else 2 if ctx['nominal'][2]>0 else None
        assert all((o['command'][2 if active==1 else 1]==0 if active is not None else o['command'][1:]==[0,0]) for o in options)
        selected=next((o for o in options if o['aliases']==qry.get('selected_aliases')),None)
        item=dict(action=i,pre_time_s=ctx['state']['physical']['actual_time'],pre=stategeo,pre_speed_m_s=speed,
                  reference_speed_m_s=refspeed,speed_minus_reference_m_s=speed-refspeed,reference_feed_accel_m_s2=feed,
                  reference_node_curvature_m_inv=float(curve[j]),reference_r2_abs_curvature_m_s2=refspeed**2*abs(float(curve[j])),
                  cursor_segment=ci,projection_cursor_segment_match=ci==j,preview_distance_m=look,preview_curvature_rad_per_m=2*float(delta@right)/max(float(delta@delta),1e-6),
                  steering_unsmoothed_rad=unsmoothed,steering_command_rad=command,steering_smoothing_delta_rad=command-unsmoothed,pre_yaw_rad_s=h['angular_velocity'],
                  active_branch='gas' if active==1 else 'brake' if active==2 else 'neutral',nominal=ctx['nominal'],qstar=ctx['qstar'],
                  selected_aliases=None if selected is None else selected['aliases'],options=options)
        if selected:
            own=online['rows'][i-1];post=own['predicted'];item.update(post=geometry(line,post['position'],post['velocity'],post['angle']),post_time_s=post['time'],post_speed_m_s=post['speed_m_s'],own_risk=risk(own),own_tire=tire_stats(own),selected_command=own['command'])
            assert own['command']==selected['command'] and not own['safety']
            number=ctx['allocation_number'];decision_path=d/f'decision-{number:03d}-private.json';decision=check(decision_path);auth=decision['authorization'];proof=decision['selected_repeat_proof'];ownlink=check(d/f'own-link-{number:03d}-private.json')
            context_path=d/f'context-{number:03d}-private.json'
            assert sha(context_path)==auth['context_sha256'] and auth['context_path']==str(context_path)
            assert auth['state_before_digest']==fingerprint(ctx['state']) and auth['before_memory_digest']==fingerprint(ctx['before']) and auth['after_memory_digest']==fingerprint(ctx['after'])
            assert auth['selected_key']==selected['key'] and auth['command']==own['command'] and auth['action_index']==i
            assert decision['options']==qry['options'] and proof['full_trace_exact']
            assert sha(proof['first_path'])==proof['first_sha256'] and sha(proof['repeat_path'])==proof['repeat_sha256']
            repeated=check(proof['repeat_path']);first=traces[selected['key']]
            for field in ('rows','status','final_state','controller_memory','model_ledger'):assert repeated[field]==first[field]
            repeatobs=check(Path(proof['repeat_path']).with_name(Path(proof['repeat_path']).name.replace('-private.json','-observer-private.json')))
            assert repeatobs['posts']==candidate_raw[selected['key']]['posts']
            assert ownlink['decision_sha256']==sha(decision_path) and ownlink['row_digest']==fingerprint(own) and ownlink['selected_source_join']['passed']
            assert observed['actions'][i-1]['frozen_row']==own
            item['binding_verified']=True;item['post_yaw_rad_s']=post['angular_velocity']
            eligible=[o for o in options if o['valid']];best=max(eligible,key=lambda o:o['risk']['margin_m']);nom=next(o for o in options if 'nominal' in o['aliases'])
            gap=best['risk']['margin_m']-selected['risk']['margin_m'];item['best_margin_sacrificed_m']=gap
            if gap>0.001:sacrifices.append(dict(action=i,gap_m=gap,M80_advantage=best['risk']['M80']-selected['risk']['M80'],best_aliases=best['aliases'],selected_aliases=selected['aliases']))
            if selected['command']!=nom['command']:
                changes.append(dict(action=i,branch=item['active_branch'],nominal_pedal=nom['command'][active],selected_pedal=selected['command'][active],M80_change=selected['risk']['M80']-nom['risk']['M80'],guard_path_change_m=selected['risk']['max_guard_path_error_m']-nom['risk']['max_guard_path_error_m'],nominal_valid=nom['valid'],pre_signed_error_m=stategeo['signed_error_m'],post_signed_error_m=item['post']['signed_error_m'],post_normal_velocity_m_s=item['post']['normal_velocity_m_s']))
        series.append(item);options_all.extend(options)
    # Raw post guard is joined to its own pre-force samples, not relabeled as simultaneous.
    raw=[]
    for k,p in enumerate(observed['posts']):
        h=p['pre_hull'];r=geometry(line,h['origin_position'],h['origin_linear_velocity'],h['angle']);r.update(action=k//4+1,raw_tick=k%4+1,pre_force_time_s=h['time'],post_time_s=p['time'],post_guard_path_error_m=p['path_error_m'],preclip=p['preclip'],pre_yaw_rad_s=h['yaw'],road_contacts=p['wheel_road_contacts'],grass=p['grass']);raw.append(r)
    measures={'post_path_over1m':lambda x:x['post']['path_error_m']>1,'post_abs_normal_over5m_s':lambda x:abs(x['post']['normal_velocity_m_s'])>5,'post_abs_heading_over10deg':lambda x:abs(x['post']['heading_error_deg'])>10,'front_ratio_over2':lambda x:x['own_tire']['front']['max_force_ratio']>2,'front_lag_over0_01rad':lambda x:x['own_tire']['steering']['last_pre_force_lag_rad']>.01}
    onset={}
    for name,predicate in measures.items():
        hits=[x['action'] for x in series[:-1] if predicate(x)];start=125
        if not predicate(series[124]):start=None
        else:
            while start>1 and predicate(series[start-2]):start-=1
        onset[name]=dict(first_action=hits[0] if hits else None,actions=len(hits),final_contiguous_start=start)
    public_points=[]
    for i in (90,100,110,115,118,120,121,122,123,124,125):
        x=series[i-1];public_points.append(dict(action=i,time_s=x['post_time_s'],path_error_m=x['post']['path_error_m'],signed_error_m=x['post']['signed_error_m'],normal_velocity_m_s=x['post']['normal_velocity_m_s'],heading_error_deg=x['post']['heading_error_deg'],yaw_rad_s=x['post_yaw_rad_s'],speed_m_s=x['post_speed_m_s'],reference_speed_m_s=x['reference_speed_m_s'],reference_curvature_m_inv=x['reference_node_curvature_m_inv'],projection_side=x['post']['projection_side'],segment=x['post']['segment'],front_slip_m_s=x['own_tire']['front']['max_abs_lateral_slip_m_s'],rear_slip_m_s=x['own_tire']['rear']['max_abs_lateral_slip_m_s'],front_ratio=x['own_tire']['front']['max_force_ratio'],rear_ratio=x['own_tire']['rear']['max_force_ratio'],front_joint_target_rad=x['own_tire']['steering']['target_joint_rad'],last_pre_force_joint_rad=x['own_tire']['steering']['last_pre_force_joint_rad'],last_pre_force_lag_rad=x['own_tire']['steering']['last_pre_force_lag_rad'],branch=x['active_branch'],selected_pedal=x['selected_command'][1 if x['active_branch']=='gas' else 2],selected_aliases=x['selected_aliases'],M80=x['own_risk']['M80'],margin_m=x['own_risk']['margin_m']))
    public=dict(stage=482,mode='SAVED_ONLY_NO_NEW_PHYSICS',deadline_utc=plan['deadline_utc'],source_code_sha256=sha(__file__),source481_manifest_sha256=sha(manifest_path),new_worlds=0,new_ticks=0,new_native=0,new_resets=0,new_HOLDOUT_SEALED=0,
                observations=dict(baseline_safe_prefix=73,baseline_unsafe_action=74,own_actions=125,own_safe_actions=125,own_raw_ticks=500,queries=126,unique_candidate_traces=len(options_all),all_queries_same_steering=True,all_queries_same_active_branch=True,context_candidate_repeat_own_bindings=125),
                descriptive_thresholds_not_validated_alarm=onset,sparse_final_segment=public_points,
                minM80_margin_tradeoffs_over1mm=sacrifices,selected_pedal_changes_vs_nominal=changes,
                final_query=dict(action=126,pre=series[-1]['pre'],pre_speed_m_s=series[-1]['pre_speed_m_s'],reference_speed_m_s=series[-1]['reference_speed_m_s'],reference_curvature_m_inv=series[-1]['reference_node_curvature_m_inv'],branch=series[-1]['active_branch'],all_unsafe=True,candidates=[{k:o[k] for k in ('aliases','valid','risk','tire','first_guard_failure_raw_tick','raw_diagnostics')} for o in series[-1]['options']],no_own_dispatch=True),
                finish_gain=None,unselected_repeats=False,causal_long_horizon_observed=False)
    private=dict(series=series,raw_series=raw,consumed481=consumed,material=dict(path=str(material_path),sha256=sha(material_path)),source_code_sha256=sha(__file__),CPU_s=time.process_time(),wall_s=time.perf_counter()-START)
    dump(target/'timeseries-private.json',private)
    dump(G/'retry/diagnostic482_summary.json',public)
    # No old evidence is rewritten; preserve global/protected source hashes.
    for group in ('protected','original408_preserve'):
        for f,h in plan[group].items():assert sha(f)==h
    assert sha(plan['ledger_path'])==plan['ledger_sha256']
    inventory=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in target.iterdir() if p.is_file()]
    cpu=time.process_time();wall=time.perf_counter()-START;assert cpu<90 and wall<180
    dump(target/'analysis-cost-private.json',dict(stage=482,CPU_s=cpu,wall_s=wall,hard_CPU_s=90,hard_wall_s=180,files=inventory,source_code_sha256=sha(__file__),source481_consumed_files=len(consumed),source481_consumed_bytes=sum(v['bytes'] for v in consumed.values()),new_physics=0,new_worlds=0,new_native=0,new_resets=0,protected_and_global_ledger_unchanged=True))
    print(json.dumps(dict(stage=482,CPU_s=cpu,wall_s=wall,onset=onset,changes=changes,sacrifices_over1mm=sacrifices,public=public_points[-6:]),ensure_ascii=False))

if __name__=='__main__':run(Path(sys.argv[1]))
