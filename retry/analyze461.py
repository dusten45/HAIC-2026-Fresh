"""461 saved-only reference-clock/control audit. No world/actor imports.

python -m retry.analyze461 PRIVATE_ROOT [OUTPUT_JSON]
Private raw rows and full input hashes stay in PRIVATE_ROOT/stage461.
"""
import hashlib,json,math,sys,time,shutil
from pathlib import Path
import numpy as np
from retry.executor397 import canonical_projection


def run(root):
    cpu,wall=time.process_time(),time.perf_counter();manifest={}
    def read(p,lines=False):
        b=p.read_bytes();manifest[str(p)]=hashlib.sha256(b).hexdigest()
        return [json.loads(x) for x in b.splitlines()] if lines else json.loads(b)
    source_dir=Path(__file__).resolve().parent.parent
    source_paths=['retry/signed417_executor.py','retry/executor397.py','retry/scalar392_audit.py','retry/paired417_common.py','retry/racing258_plan.py','retry/racing258_run.py','retry/pace268_profile.py','retry/source_vehicle_transition.py','core/vendor/car_dynamics.py']
    source_hashes={}
    for rel in source_paths:
        path=source_dir/rel;digest=hashlib.sha256(path.read_bytes()).hexdigest();manifest[str(path)]=digest;source_hashes[rel]=digest
    preserved=read(root/'stage460-plan-durable-private.json')
    for group in ['protected','original408_preserve']:
        for p,h in preserved[group].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
    plan=read(root/'stage453/plan.json');fixed=read(Path(plan['fixed_plan']));pace=np.asarray(read(Path(plan['pace_path']))['frozen268'])
    nodes=np.asarray(fixed['free_profile']['speed'])*pace;ds=np.asarray(fixed['free_profile']['ds']);arc=np.r_[0,np.cumsum(ds)];L=float(arc[-1]);line=np.asarray(fixed['line']);model=fixed['model'];edge=np.roll(line,-1,axis=0)-line;tangents=edge/np.linalg.norm(edge,axis=1)[:,None]
    totals=2*ds/(nodes[:-1]+nodes[1:]);clocks=np.r_[0,np.cumsum(totals)]
    def ref(s):
        assert 0<=s<=L
        j=min(len(ds)-1,int(np.searchsorted(arc,s,side='right')-1));u=(s-arc[j])/ds[j];r=math.sqrt((1-u)*nodes[j]**2+u*nodes[j+1]**2);f=(nodes[j+1]**2-nodes[j]**2)/(2*ds[j])
        clock=clocks[j]+2*(s-arc[j])/(nodes[j]+r) if s>arc[j] else clocks[j]
        return float(r),float(f),float(clock),j
    def pedal(raw,v):
        a=min(model['rear_traction_accel'],max(-model['brake_accel'],raw))
        return np.asarray([min(1.,max(0.,model['effective_mass']*max(a,0)*(v+2.7)/80000)),min(1.,max(0.,model['effective_mass']*max(-a,0)/(4*1.6*15/(.02*.54))))],np.float32)
    bounds=[0,60,120,180,240,270,330,390,450,510,570,630,690,750];data={};private_rows={};origin=None
    for label,stage,lap,prefix in [('442P',442,13.76,118),('458P',458,14.00,112)]:
        d=root/f'stage{stage}/actual_P';rows=read(d/'trace-private.jsonl',True);origin=rows[22]['progress_before'] if origin is None else origin
        queries={x['relative_decision']+prefix:x for x in read(root/f'stage{stage}/query-records-private.json') if x['arm']=='P'}
        start=rows[0]['pre']['time'];intervals=[];actions=[];formula_error=0.;excluded=0.
        for row in rows:
            n=row['step'];receipt=read(d/f'P_step{n}-after-native-private.json');assert len(receipt['posts'])==len(row['raw_hull'])==row['raw_ticks']
            nominal_equal=np.array_equal(np.asarray(row['command'],np.float32),np.asarray(row['nominal'],np.float32));phase=row['nominal_memory_after']['C']['phase']
            s=row['progress_before'];preq=canonical_projection(line,row['pre']['pos'],row['pre']['vel'],'FIRST_LAP');lastarc=preq['arc']
            r0,f0,_,_=ref(min(L,max(0.,s)));v0=row['pre']['speed'];ff0=f0*preq['sigma']/r0 if r0 else None
            raw0=None if ff0 is None else ff0+1.5*(r0-v0)
            formula_qualified=phase=='FIRST_LAP' and n>1 and 0<s<L
            if formula_qualified:
                formula_error=max(formula_error,float(np.max(abs(pedal(raw0,v0)-np.asarray(row['nominal'][1:],np.float32)))))
            predicted_s=s+preq['sigma']*.08
            secant=None
            if formula_qualified and preq['sigma']>=0 and predicted_s<=L:
                secff=(ref(predicted_s)[0]-r0)/.08;secraw=secff+1.5*(r0-v0);newpedal=pedal(secraw,v0)
                secant=dict(feed=secff,raw=secraw,pedal_changed=not np.array_equal(newpedal,np.asarray(row['nominal'][1:],np.float32)),brake=float(newpedal[1]),gas=float(newpedal[0]),crosses_node=ref(predicted_s)[3]!=preq['index'])
            authority='archived_prefix' if n not in queries else ('planner' if queries[n].get('planner_used') else 'guardian')
            recipe='nominal' if nominal_equal else (queries[n]['selected_recipe'] if n in queries else 'archived_non_nominal')
            action=dict(step=n,offset_m=s-origin,elapsed_s=row['pre']['time']-start,nominal_equal=nominal_equal,phase=phase,r=r0,v=v0,ff=ff0,raw=raw0,authority=authority,recipe=recipe,secant=secant,hold_conflict_s=0.,under_target_braking=formula_qualified and v0<r0 and raw0<0,future13_target_min=None,end_speed_error=None)
            if formula_qualified:
                future=rows[n-1:n+12];targets=[ref(x['progress_before'])[0] for x in future if 0<x['progress_before']<L]
                action['future13_target_min']=min(targets) if targets else None
            for i,(h,post) in enumerate(zip(row['raw_hull'],receipt['posts'])):
                pq=canonical_projection(line,h['origin_position'],h['COM_linear_velocity'],'FIRST_LAP');postq=canonical_projection(line,post['position'],post['velocity'],'FIRST_LAP');s1=s+(postq['arc']-lastarc+L/2)%L-L/2;dt=max(0.,min(post['time']-start,lap)-min(h['time']-start,lap))
                if n<23 or dt==0 or phase!='FIRST_LAP' or not(0<s<s1<=L):
                    if n>=23:excluded+=dt
                    s,lastarc=s1,postq['arc'];continue
                r,f,clock,j=ref(s);r1,_,clock1,_=ref(s1);drho=clock1-clock;assert drho>0
                invr=drho/(s1-s);v=math.hypot(*h['COM_linear_velocity']);sigma=pq['sigma'];origin_sigma=float(np.asarray(h['origin_linear_velocity'])@tangents[pq['index']]);forward=np.asarray([-math.sin(h['angle']),math.cos(h['angle'])]);cos=float(forward@tangents[pq['index']]);sample_raw=f*sigma/r+1.5*(r-v)
                ff=f*sigma/r;feedback=1.5*(r-v);speed_term=dt*(1-v*invr);heading_term=dt*v*(1-cos)*invr;slip_term=dt*(v*cos-sigma)*invr;origin_term=dt*(sigma-origin_sigma)*invr;residual=dt*origin_sigma*invr-drho
                assert abs(drho+speed_term+heading_term+slip_term+origin_term+residual-dt)<1e-12
                tires=[x for x in row['raw_tire_samples'] if x['raw_tick']==i+1];assert len(tires)==4
                conflict=nominal_equal and row['command'][2]>0 and sample_raw>=0 and i>0
                action['hold_conflict_s']+=dt if conflict else 0.
                intervals.append(dict(offset_m=(s+s1)/2-origin,dt=dt,reference_s=drho,speed_tracking_s=speed_term,heading_s=heading_term,body_slip_correction_s=slip_term,origin_COM_correction_s=origin_term,geometry_sampling_residual_s=residual,actual_brake_s=dt if row['command'][2]>0 else 0.,under_target_braking_s=dt if v<r and sample_raw<0 else 0.,held_sign_conflict_s=dt if conflict else 0.,clipped_s=dt if any(x['clipped'] for x in tires) else 0.,gas_ramp_deficit_s=dt*sum(max(0.,row['command'][1]-x['gas']) for x in tires[2:])/2,ff=ff,feedback=feedback,observed_accel=(math.hypot(*post['velocity'])-v)/.02,recipe=recipe,authority=authority))
                s,lastarc=s1,postq['arc']
            if 0<s<L:action['end_speed_error']=row['post']['speed']-ref(s)[0]
            if n>=23:actions.append(action)
        bins={}
        additive=['dt','reference_s','speed_tracking_s','heading_s','body_slip_correction_s','origin_COM_correction_s','geometry_sampling_residual_s','actual_brake_s','under_target_braking_s','held_sign_conflict_s','clipped_s','gas_ramp_deficit_s']
        for lo,hi in zip(bounds,bounds[1:]+[math.inf]):
            subset=[x for x in intervals if lo<=x['offset_m']<hi];bins[str(lo)]={key:sum(x[key] for x in subset) for key in additive}
        aggregate={key:sum(x[key] for x in intervals) for key in additive};assert abs(aggregate['dt']+excluded+1.76-lap)<1e-8
        under=[x for x in actions if x['under_target_braking']];conflicts=[x for x in actions if x['hold_conflict_s']>0];candidates=[x for x in actions if x['secant'] and x['secant']['pedal_changed'] and x['hold_conflict_s']>0 and x['nominal_equal'] and x['under_target_braking'] and x['offset_m']>=450]
        summaries=dict(under_target_braking_actions=len(under),future13_target_below_initial_speed=sum(x['future13_target_min']<x['v'] for x in under if x['future13_target_min'] is not None),hold_conflict_actions=len(conflicts),hold_conflict_s=sum(x['hold_conflict_s'] for x in actions),secant_qualified_actions=sum(x['secant'] is not None for x in actions),secant_changed_actions=sum(bool(x['secant'] and x['secant']['pedal_changed']) for x in actions),secant_underbrake_retained=sum(bool(x['secant'] and x['secant']['brake']>0) for x in under),first_conflict_changed_nominal=None if not candidates else dict(step=candidates[0]['step'],offset_m=round(candidates[0]['offset_m'],6),elapsed_s=round(candidates[0]['elapsed_s'],8),held_conflict_s=round(candidates[0]['hold_conflict_s'],8),secant_changes_brake_to_drive=candidates[0]['secant']['raw']>0,secant_fullgas_recipe_alias=candidates[0]['secant']['gas']==1 and candidates[0]['secant']['brake']==0))
        data[label]=dict(official_native_lap_s=lap,common_prefix_elapsed_s=1.76,qualified_s=aggregate,excluded_finish_boundary_s=excluded,bins=bins,control_summary=summaries,formula_max_float32_pedal_error=formula_error,actual_control_exposure_s={key:sum(x['dt'] for x in intervals if x['recipe']==key) for key in sorted(set(x['recipe'] for x in intervals))},time_components_by_selected_control={recipe:{key:sum(x[key] for x in intervals if x['recipe']==recipe) for key in additive} for recipe in sorted(set(x['recipe'] for x in intervals))})
        assert formula_error==0
        private_rows[label]=dict(actions=actions,intervals=intervals)
    from retry.receipt421_io import load_receipt
    from retry.terminal410_model import from_actual_full
    rootfiles={key:root/path for key,path in dict(dispatch='stage458/P_decision14-before-actual-dispatch-private.json',query='stage458/P_decision14_query-before-integration-private.json',native='stage458/actual_P/P_step126-before-native-private.json').items()}
    for f in rootfiles.values():read(f)
    dispatch=load_receipt(rootfiles['dispatch']);proof=load_receipt(rootfiles['query']);native=load_receipt(rootfiles['native'])
    parent=dispatch['context']['parent']
    # Use the already-tested immutable Parent value codec; no world constructor.
    from retry.planner419 import Parent
    archived=Parent(**parent);state,memory,rng=archived.fork_inputs()
    assert state['terminal_model']==from_actual_full(native['full_pre_before_nominal'])
    assert proof['memory']==memory and proof['state']==state['terminal_model'] and proof['ledger']==dispatch['context']['ledger']
    selected=next(x for x in private_rows['458P']['actions'] if x['step']==126)
    assert selected['nominal_equal'] and selected['secant']['gas']==1 and selected['secant']['brake']==0
    candidate=np.asarray(rows[125]['nominal'],np.float32).copy();candidate[1:]=[selected['secant']['gas'],selected['secant']['brake']]
    existing=np.asarray(rows[125]['nominal'],np.float32).copy();existing[1:]=[1.,0.]
    assert np.array_equal(candidate,existing) and memory==rows[125]['memory_before']
    assert all(x['command']==x['nominal'] for x in rows[125:138])
    assert selected['hold_conflict_s']>0 and selected['offset_m']>=450
    root_binding=dict(native_step=126,offset_m=round(selected['offset_m'],6),observed_prefix_elapsed_s=10.0,root_state_memory_ledger_binding_passed=True,secant_fullgas_float32_alias=True,source_hashes={k:hashlib.sha256(f.read_bytes()).hexdigest() for k,f in rootfiles.items()})
    profile=dict(reference_clock_by_common_boundary_s={str(b):ref(origin+b)[2]-ref(origin)[2] for b in bounds},common_reference_from_pre23_to_profile_end_s=ref(L)[2]-ref(origin)[2],reference_whole_profile_clock_s=float(sum(totals)),base_profile_clock_s=fixed['free_profile']['estimated_time_s'],scaled_squared_speed_gradient_min=float(np.min(np.diff(nodes**2)/(2*ds))),scaled_squared_speed_gradient_max=float(np.max(np.diff(nodes**2)/(2*ds))),scaled_gradient_brake_allowance_exceeded_segments=int(np.sum(np.diff(nodes**2)/(2*ds)<-model['brake_accel'])),scaled_gradient_drive_allowance_exceeded_segments=int(np.sum(np.diff(nodes**2)/(2*ds)>model['rear_traction_accel'])),lateral_accel_ratio_to_base_allowance_max=float(np.max(nodes[:-1]**2*np.abs(fixed['free_profile']['curvature'])/model['lateral_accel'])))
    from_reference=read(Path(__file__).resolve().parent/'compare459_result.json')
    crossing_excess={}
    for label in data:
        crossing_excess[label]={str(b):[round(t-1.76-profile['reference_clock_by_common_boundary_s'][str(b)],8) for t in from_reference['data'][label]['crossings'][str(b)]['time_s']] for b in bounds}
    trace_hashes={label:dict(trace=manifest[str(root/f'stage{stage}/actual_P/trace-private.jsonl')],query_records=manifest[str(root/f'stage{stage}/query-records-private.json')]) for label,stage in [('442P',442),('458P',458)]}
    public=dict(trace_input_hashes=trace_hashes,fixed_profile_input_sha256=manifest[plan['fixed_plan']],pace_input_sha256=manifest[plan['pace_path']],control_source_hashes=source_hashes,protected_and_original_hashes_preserved=18,next_root_binding=root_binding,reference_clock_excess_bracket_s=crossing_excess,stage=461,scope='SAVED_ONLY_DESCRIPTIVE_NO_CAUSAL_TIME_ATTRIBUTION',new_actual_actions=0,new_model_ticks=0,new_worlds=0,new_resets=0,profile=profile,data=data,clock_identity='For each positive-progress FIRST_LAP raw interval inside profile domain: drho=int(ds/r); invr=drho/ds; dt=drho+dt(1-v*invr)+dt*v(1-cosheading)*invr+dt(v*cosheading-sigmaCOM)*invr+dt(sigmaCOM-sigmaOrigin)*invr+[dt*sigmaOrigin*invr-drho]. Signed convention, exact closure; residual contains discrete geometry/sampling. Midpoint spatial bins, no independent causal attribution. Prefix1.76 and profile-end straddling intervals excluded explicitly.',storage={str(p):dict(total=shutil.disk_usage(p).total,used=shutil.disk_usage(p).used,free=shutil.disk_usage(p).free) for p in ['/workspace','/tmp']})
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in manifest.items())
    d=root/'stage461';d.mkdir(mode=0o700,exist_ok=True)
    (d/'input-sha256-private.json').write_text(json.dumps(manifest,indent=2)+'\n');(d/'rows-private.json').write_text(json.dumps(private_rows,indent=2)+'\n');(d/'analysis-cost.json').write_text(json.dumps(dict(CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,input_files=len(manifest)),indent=2)+'\n')
    public['private_input_manifest_sha256']=hashlib.sha256((d/'input-sha256-private.json').read_bytes()).hexdigest()
    return public

if __name__=='__main__':
    out=Path(sys.argv[2]) if len(sys.argv)>2 else Path('retry/structural461_result.json');out.write_text(json.dumps(run(Path(sys.argv[1]).resolve()),indent=2)+'\n');print(str(out))
