"""Saved-only pre23 whole-arm measurements; finish, safety and proxies kept separate."""
import json,math,re,time
from pathlib import Path
from retry.loss389_analyze import read,save,sha
from retry.signed417_executor import canonical_projection

ARMS=['Projected4Reference','AllocationP4']
def clean(value):return None if value is None else re.sub(r'/(?:workspace|tmp)/[^\s\'\"]+','[private-path]',str(value))

def run(root):
    root=Path(root);d=root/'stage477-revision1';cpu=time.process_time();wall=time.perf_counter()
    p=read(d/'plan.json');r=read(d/'result.json');b=read(d/'budget.json');model=b['model']
    assert sha(d/'plan.json')==r['plan_sha256']==(d/'plan.sha256').read_text().strip()
    assert model['ticks']<=model['reserved_ticks']<=4096 and model['worlds']<=49
    assert b['actual']['actions']==b['actual']['resets']==r['new_actual_actions']==r['new_resets']==0
    for group in ['sources','protected','original408_preserve']:
        for filename,h in p[group].items():assert sha(filename)==h,filename
    assert sha(p['ledger_path'])==p['ledger_sha256']
    fixed=read(p['fixed_plan']);profile=read(p['projection_path']);assert sha(p['projection_path'])==p['projection_sha256']
    original,projected=profile['original_nodes'],profile['projected_nodes'];arc_nodes=[0.]
    for ds in fixed['free_profile']['ds']:arc_nodes.append(arc_nodes[-1]+ds)
    L=arc_nodes[-1];B=fixed['model']['brake_accel']
    def point(post,vector):
        # There is no remaining control reference after own official model finish.
        if post['tracker_after']['finish_time_s'] is not None:return dict(reference_m_s=None,brake_debt_proxy=None,terminal_reference_domain='NO_REMAINING_REFERENCE_AFTER_OWN_FINISH')
        q=canonical_projection(fixed['line'],post['position'],post['velocity'],post['phase']);j,u=q['index'],q['u'];v=math.hypot(*post['velocity'])
        lower=[(s-q['arc'],n) for s,n in zip(arc_nodes,vector) if s>q['arc'] and n<v]
        return dict(reference_m_s=math.sqrt((1-u)*vector[j]**2+u*vector[j+1]**2),terminal_reference_domain='ACTIVE_OR_STOPPED_WITH_REMAINING_REFERENCE',
                    brake_debt_proxy=dict(lower_nodes=len(lower),max_required_deceleration_over_B=max(((v*v-n*n)/(2*ds)/B for ds,n in lower),default=None),minimum_distance_margin_m=min((ds-(v*v-n*n)/(2*B) for ds,n in lower),default=None),exact_physical_feasibility=False))
    streams={x['link']['label']:x for x in (read(f) for f in d.glob('*-observer-private.json'))}
    observer_ticks=sum(len(x['posts']) for x in streams.values());observer_reconciled=observer_ticks==model['ticks']
    whole=r.get('whole_result') or {};policies=whole.get('policies',r.get('whole_arms',[]))
    if not policies and (d/'whole_policy-results.json').exists():policies=read(d/'whole_policy-results.json')
    details={}
    for policy in policies:
        arm=policy['arm'];assert arm in ARMS and arm not in details
        child=read(policy['rows_private_path']);rows=child['rows'];stream=streams[policy['label']];posts=stream['posts'];initial=stream['link']['model_ledger']
        assert len(rows)==policy['parent_actions']<=250 and len(posts)==sum(x['predicted']['raw_ticks'] for x in rows)==policy['raw_ticks']<=1000
        assert policy['whole_arm_runs']==1 and not policy['whole_arm_repeated'] and child['initial_actions']==child['tail_actions']==0
        own=projected;failure=None;crossings={};distance=0.;previous_tick=0
        prior_arc=None if not rows else canonical_projection(fixed['line'],rows[0]['raw_hull'][0]['origin_position'],rows[0]['raw_hull'][0]['COM_linear_velocity'],'FIRST_LAP')['arc']
        for post in posts:
            q=canonical_projection(fixed['line'],post['position'],post['velocity'],post['phase']);after=distance+(q['arc']-prior_arc+L/2)%L-L/2;tick=post['raw_clock']-initial['last_clock_tick'];assert tick==previous_tick+1
            reasons=[]
            if post['path_error_m']>3:reasons.append('path_error_over3m')
            if post['damage']>0:reasons.append('damage_increase')
            if post['collision']:reasons.append('collision_or_obstacle')
            if post['grass'] or post['wheel_road_contacts']<4:reasons.append('road_loss_or_grass')
            if reasons and failure is None:failure=dict(raw_tick=tick,elapsed_s=tick/50,reasons=reasons,progress_from_root_m=after)
            for boundary in range(60,math.floor(max(0,after)/60)*60+1,60):
                if str(boundary) not in crossings and distance<boundary<=after:
                    crossings[str(boundary)]=dict(bracket_s=[previous_tick/50,tick/50],safe_through_crossing=failure is None,speed_m_s=math.hypot(*post['velocity']),path_error_m=post['path_error_m'],max_force_ratio=max(x['force_ratio'] for x in post['preclip']),common_original=point(post,original),own=point(post,own))
            distance,prior_arc,previous_tick=after,q['arc'],tick
        tires=[t for row in rows for t in row['tires']];assert len(tires)==4*len(posts)
        endpoint=None if not posts else posts[-1]
        if policy['own_model_finish']:
            assert child['model_ledger']['done'] and child['final_state']['finish_tracker']['finish_time_s']==policy['official_event_time_s'] and failure is None
        details[arm]=dict(status=policy['status'],error=clean(policy['error']),actions=len(rows),raw_ticks=len(posts),elapsed_s=len(posts)/50,own_model_finish=policy['own_model_finish'],remaining_finish_bracket_s=policy['remaining_model_finish_s'],official_event_time_s=policy['official_event_time_s'],confirmation_time_s=policy['confirmation_time_s'],
                          whole_arm_runs=1,whole_arm_repeated=False,qualification_prefix13_exact=policy.get('prefix_match13'),common_boundary_crossings=crossings,first_raw_physical_failure=failure,
                          first_action_safety_failure=next((dict(action=i+1,reasons=row['safety']) for i,row in enumerate(rows) if row['safety']),None),endpoint_progress_delta_m=distance,endpoint_speed_m_s=None if endpoint is None else math.hypot(*endpoint['velocity']),
                          endpoint_common_original=None if endpoint is None else point(endpoint,original),endpoint_own=None if endpoint is None else point(endpoint,own),endpoint_phase=child['controller_memory']['C']['phase'],endpoint_ledger_done=child['model_ledger']['done'],
                          max_path_error_m=max((x['path_error_m'] for x in posts),default=None),max_force_ratio=max((x['force_ratio'] for x in tires),default=None),clipped_wheel_samples=sum(bool(x['clipped']) for x in tires),wheel_samples=len(tires),
                          brake_actions=sum(x['command'][2]>0 for x in rows),first_command=None if not rows else rows[0]['command'],first_nominal=None if not stream['actions'] else stream['actions'][0]['nominal'],forced_first_pulse=False,actual_finish_witness=False)
    both=len(details)==2 and all(x['own_model_finish'] for x in details.values());gain=None;common={}
    if len(details)==2:
        a,z=(details[arm] for arm in ARMS)
        for boundary in sorted(set(a['common_boundary_crossings'])&set(z['common_boundary_crossings']),key=int):
            ca,cz=a['common_boundary_crossings'][boundary],z['common_boundary_crossings'][boundary]
            common[boundary]=dict(OldP4=ca,AllocatedP4=cz,OldP4_minus_allocation_s=[ca['bracket_s'][0]-cz['bracket_s'][1],ca['bracket_s'][1]-cz['bracket_s'][0]],both_safe=ca['safe_through_crossing'] and cz['safe_through_crossing'])
        if both:
            a,z=a['remaining_finish_bracket_s'],z['remaining_finish_bracket_s'];gain=[a[0]-z[1],a[1]-z[0]]
    allocation_packets=[read(f) for f in sorted(d.glob('allocation-proof-*.json'))];input_packets={read(f)['number']:read(f) for f in sorted(d.glob('allocation-input-*.json'))};allocation_summary={}
    for arm,detail in details.items():
        label='whole_'+arm;packets=[x for x in allocation_packets if x['label']==label];events=[]
        child=read(d/(label+'-private.json'));rows=child['rows']
        for x in packets:
            row=rows[x['action']-1];before=input_packets[x['number']];h=row['raw_hull'][0];q=canonical_projection(fixed['line'],h['origin_position'],h['COM_linear_velocity'],before['phase']);first=[t for t in row['tires'] if t['raw_tick']==1]
            assert x['command']==row['command']
            assert max(0.,max(t['force_ratio']-1 for t in first))==x['proof']['objective']
            events.append(dict(action=x['action'],physical_time_s=h['time'],elapsed_from_root_s=h['time']-rows[0]['raw_hull'][0]['time'],arc_m=q['arc'],changed=x['changed'],nominal_pedals=before['nominal'][1:],actual_pedals=x['command'][1:],objective_q0=x['proof']['objective_q0'],objective_selected=x['proof']['objective'],first_raw_force_identity_exact=True,first_raw_only=True))
        allocation_summary[arm]=dict(calls=len(packets),interventions=sum(x['changed'] for x in packets),strict_first_raw_objective_reductions=sum(x['proof']['objective']<x['proof']['objective_q0'] for x in packets),first_intervention=next((x for x in events if x['changed']),None),intervention_events=[x for x in events if x['changed']],max_objective_q0=max((x['proof']['objective_q0'] for x in packets),default=None),max_objective_selected=max((x['proof']['objective'] for x in packets),default=None))
    out=dict(stage=477,allocation_summary=allocation_summary,integrated_qualification=read(d/'integrated-qualification.json') if (d/'integrated-qualification.json').exists() else None,allocator_cost=b.get('allocator'),status=r['status'],error=clean(r['error']),details=details,both_safe_own_model_finishes=both,remaining_finish_gain_bracket_s=gain,full_window_model_gain_criterion_passed=bool(both and gain[0]>0),common_boundaries=common,
             source_root_qualification_passed=bool((r.get('root_qualification') or r.get('cohort_result') or {}).get('passed')),observer_raw_ticks_reconciled=observer_reconciled,observer_raw_ticks=observer_ticks,
             first_pulse_forced=False,reference_only_treatment=False,actual_promotion=False,actual_finish_witness=False,pixel_or_generalization_promotion=False,whole_arm_repetition_claimed=False,
             cost=dict(ticks=model['ticks'],reserved_ticks=model['reserved_ticks'],worlds=model['worlds'],CPU_s=b['wholeworker_CPU_s'],wall_s=b['whole_execution_wall_s']),static=read(d/p.get('static_result_name','static-result.json')),preflight_counts=r.get('preflight_counts'),
             storage_forecast=p['storage_forecast'],storage_preflight=p['storage_preflight'],protected18_and_ledger476_unchanged=True,new_actual_actions=0,new_resets=0,new_seed_learning_HOLDOUT_SEALED_reserve_paid=0,
             diagnostic_reference_clock_s=12.260,goal11_99_s_unchanged=True,deadline_utc=p['deadline_utc'],plan_sha256=sha(d/'plan.json'),new_archive_created=False,workspace_raw_copies=0,
             reproduction_limit='Raw remains only on this executor /tmp. If lost exact raw cannot be reverified; hashes cannot reconstruct raw.',saved_audit_CPU_s=time.process_time()-cpu,saved_audit_wall_s=time.perf_counter()-wall)
    save(d/'saved-closure-private.json',out);save(Path(__file__).resolve().parent/'compare477_result.json',out);return out

if __name__=='__main__':
    import sys
    out=run(sys.argv[1]);print(json.dumps({k:v for k,v in out.items() if k not in ('details','common_boundaries','storage_forecast','storage_preflight','static')}))
