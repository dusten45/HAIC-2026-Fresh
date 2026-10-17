"""Saved-only465 cohort comparison: scalar geometry and records, no physics imports."""
import json,math,re,sys,time
from pathlib import Path
from retry.loss389_analyze import read,save,sha
from retry.signed417_executor import canonical_projection

def safe_error(value):
    return None if value is None else re.sub(r'/(?:workspace|tmp)/[^\s\'\"]+','[private-path]',str(value))

def run(root):
    cpu,wall=time.process_time(),time.perf_counter();d=root/'stage465';g=Path(__file__).resolve().parents[1]
    p=read(d/'plan.json');result=read(d/'result.json');closed=read(d/'progress-private.json');budget=result['budget'];model=budget['model'];actual=budget['actual']
    assert closed['phase']=='CLOSED' and sha(d/'plan.json')==result['plan_sha256']==(d/'plan.sha256').read_text().strip()
    for group in ['sources','protected','original408_preserve']:
        for path,digest in p[group].items():assert sha(path)==digest,path
    assert sha(p['ledger_path'])==p['ledger_sha256'];ledger=read(p['ledger_path'])
    assert ledger['version']==475 and ledger['stage463_status']=='CLOSED' and ledger['research_remaining']==26346
    assert 0<=model['ticks']<=model['reserved_ticks']<=1458<=2048 and model['worlds']<=41<=64
    assert actual['actions']==actual['resets']==result['new_actual_actions']==result['new_resets']==0
    streams={s['link']['label']:s for s in (read(f) for f in d.glob('*-observer-private.json'))};post_count=sum(len(s['posts']) for s in streams.values())
    protected_count=sum(len(p[group]) for group in ['protected','original408_preserve']);assert protected_count==18
    assert post_count==model['ticks'] and len(streams)==model['confirmed_worlds']==model['worlds']
    if result['status']=='H13_COMPARISON_COMPLETE':assert budget['wholeworker_CPU_s']<180 and budget['whole_execution_wall_s']<300
    fixed=read(p['fixed_plan']);pace=read(p['pace_path'])['frozen268'];nodes=[a*b for a,b in zip(fixed['free_profile']['speed'],pace)];ds=fixed['free_profile']['ds'];arcs=[0.]
    for length in ds:arcs.append(arcs[-1]+length)
    line=fixed['line'];L=arcs[-1];B=fixed['model']['brake_accel'];assert B>0;details={}
    drivers=read(d/'policyrecords-private.json') if (d/'policyrecords-private.json').exists() else []
    for cohort in result['cohorts']:
        arm=cohort['arm'];assert arm in ('PulseOnce','S13');pair=cohort['trajectories'];assert len(pair)==2 and pair[0]['signature']==pair[1]['signature']
        assert cohort['independent_repeat_exact'] and cohort['held_first_passed'];a=pair[0];child=read(a['child_private_path']);rows=child['rows'];stream=streams[a['label']];posts=stream['posts'];initial=stream['link']['model_ledger']
        assert len(rows)==a['rows']<=13 and len(posts)==sum(r['predicted']['raw_ticks'] for r in rows)
        assert rows[0]['command'][1:]==[1.,0.];assert all(x['nominal_calls']==1 and x['prepared_nominal_used'] for x in drivers if x['arm']==arm)
        root_hull=rows[0]['raw_hull'][0];v0=math.hypot(*root_hull['COM_linear_velocity']);q0=canonical_projection(line,root_hull['origin_position'],root_hull['COM_linear_velocity'],'FIRST_LAP');arc=q0['arc'];progress=initial['progress_m'];previous_tick=0;cross=None
        for post in posts:
            q=canonical_projection(line,post['position'],post['velocity'],post['phase']);after=progress+(q['arc']-arc+L/2)%L-L/2;tick=post['raw_clock']-initial['last_clock_tick']
            assert tick==previous_tick+1
            if cross is None and progress-initial['progress_m']<60<=after-initial['progress_m']:cross=[previous_tick/50,tick/50]
            progress,arc,previous_tick=after,q['arc'],tick
        endpoint=rows[-1];vel=endpoint['predicted']['velocity'];v=math.hypot(*vel);q=canonical_projection(line,endpoint['predicted']['position'],vel,'FIRST_LAP');j,u=q['index'],q['u'];r=math.sqrt((1-u)*nodes[j]**2+u*nodes[j+1]**2)
        end_progress=endpoint['model_progress'];end_arc=q['arc'];lower=[(s-end_arc,n) for s,n in zip(arcs,nodes) if s>end_arc and n<v]
        debt=[(v*v-n*n)/(2*distance)/B for distance,n in lower];slack=[distance-(v*v-n*n)/(2*B) for distance,n in lower]
        tires=[t for row in rows for t in row['tires']];hulls=[h for row in rows for h in row['raw_hull']]
        assert len(tires)==4*len(posts) and len(hulls)==len(posts)
        gases={str(w):[t['gas'] for t in tires if t['wheel']==w] for w in sorted({t['wheel'] for t in tires})}
        calibration=a['factual_calibration']
        if arm=='PulseOnce' and cohort['status']=='COMPLETE_H13':assert calibration and calibration['certified_prefix_actions']==13 and calibration['fresh_current_first_pass']>=1
        details[arm]=dict(status=cohort['status'],scope_exit=cohort['scope_exit'],error=safe_error(cohort['error']),actions=len(rows),observed_raw_posts=len(posts),wheel_samples=len(tires),independent_repeat_exact=True,held_first_passed=True,first_fullgas_alias=True,raw60m_crossing_from_root_s=cross,crossing_censored=cross is None,elapsed_s=len(posts)/50,fixed1_04s_complete=len(posts)==52 and len(rows)==13,progress_delta_m=end_progress-initial['progress_m'],endpoint_speed_m_s=v,speed_change_m_s=v-v0,endpoint_reference_m_s=r,endpoint_speed_minus_reference_m_s=v-r,endpoint_reference_deficit_m_s=r-v,pointmass_brake_debt_proxy=dict(future_lower_nodes=len(lower),max_required_deceleration_over_original_B=max(debt,default=None),minimum_distance_minus_original_B_braking_distance_m=min(slack,default=None),exact_physical_feasibility=False,current_speed_defines_lower_reference=True),max_path_error_m=max((row['path_error_m'] for row in rows),default=None),max_abs_yaw_rad_s=max((abs(h['yaw']) for h in hulls),default=None),mean_abs_lateral_slip_m_s=sum(abs(t['lateral_slip_m_s']) for t in tires)/len(tires),max_force_ratio=max(t['force_ratio'] for t in tires),clipped_wheel_samples=sum(bool(t['clipped']) for t in tires),gas_ramp_by_wheel={w:dict(first=xs[0],last=xs[-1],minimum=min(xs),maximum=max(xs)) for w,xs in gases.items()},native_same_command_prefix_actions=a['native_same_command_prefix_actions'],native_first_command_divergence=a['native_first_command_divergence'],native_factual_calibration=None if calibration is None else {k:calibration[k] for k in ['certified_prefix_actions','fresh_current_first_pass']},native_factual_scope=cohort['native_factual_scope'],after_first_same_command_native_factual_actions=max(0,a['native_same_command_prefix_actions']-1) if arm=='PulseOnce' else 0,actual_finish_witness=False)
    complete=result['status']=='H13_COMPARISON_COMPLETE' and len(details)==2 and all(x['status']=='COMPLETE_H13' and x['fixed1_04s_complete'] for x in details.values())
    gain=None;progress_gain=None
    if len(details)==2:
        c,s=details['PulseOnce'],details['S13'];progress_gain=s['progress_delta_m']-c['progress_delta_m']
        if c['raw60m_crossing_from_root_s'] and s['raw60m_crossing_from_root_s']:
            lo,hi=c['raw60m_crossing_from_root_s'];sl,sh=s['raw60m_crossing_from_root_s'];gain=[lo-sh,hi-sl]
    promote=bool(complete and gain is not None and gain[0]>0 and progress_gain>0)
    outcome='PROMOTION_CRITERIA_PASS_MODEL_ONLY' if promote else 'CROSSING_CENSORED' if gain is None else 'OVERLAPPING_OR_NONPOSITIVE_GAIN' if gain[0]<=0<=gain[1] else 'NEGATIVE_GAIN' if gain[1]<0 else 'GATES_OR_PROGRESS_NOT_PASS'
    static=read(d/'static-result.json');public=dict(stage=465,status=result['status'],error=safe_error(result['error']),last_stage=result['last_stage'],closed_at_utc=closed['at_utc'],details=details,PulseOnce_minus_S13_60m_bracket_s=gain,S13_minus_PulseOnce_fixed1_04s_progress_m=progress_gain,all_gates_complete=complete,model_only_promotion_criterion_passed=promote,research_outcome=outcome,actual_promotion=False,time_extrapolation=False,actual_finish_witness=False,verification=dict(source_protected_hashes_preserved=True,protected_hash_count=protected_count,ledger475_unchanged=True,observer_posts=post_count,observer_streams=len(streams),meter_consistent=True,static={k:v for k,v in static.items() if k in ['passed','tests','failures','errors','CPU_s','wall_s']},preflight=read(d/'preflight-private.json') if(d/'preflight-private.json').exists() else None),cost=dict(model_ticks=model['ticks'],reserved_ticks=model['reserved_ticks'],worlds=model['worlds'],wholeworker_CPU_s=budget['wholeworker_CPU_s'],wholeworker_wall_s=budget['whole_execution_wall_s']),scope_ticks=1458,scope_worlds=41,hard_ticks=2048,hard_worlds=64,new_actual_actions=0,new_resets=0,new_seed_learning_HOLDOUT_SEALED_reserve_paid=0,research_remaining=ledger['research_remaining'],actual_cumulative_wrapper_actions=ledger['actual_cumulative_wrapper_actions'],reserve=ledger['final_reserved_actions'],reserve_used=ledger['final_reserve_used'],deadline_utc=p['deadline_utc'],plan_sha256=result['plan_sha256'],saved_audit_CPU_s=time.process_time()-cpu,saved_audit_wall_s=time.perf_counter()-wall)
    save(d/'saved-closure-private.json',public);save(g/'retry/compare465_result.json',public);print(json.dumps(public,ensure_ascii=False));return public

if __name__=='__main__':run(Path(sys.argv[1]))
