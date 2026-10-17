"""Saved-only458 closure audit; no environment, model constructor or integration."""
import collections,json,re,time
from pathlib import Path
from retry.loss389_analyze import read,save,sha
from retry.receipt421_io import load_receipt


def jsonl(path):
    return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []


def public_error(value):
    return None if value is None else re.sub(r'/(?:workspace|tmp)/[^\s\'\"]+', '[private-path]', str(value))


def run(root):
    cpu=time.process_time();wall=time.perf_counter();d=root/'stage458';g=Path(__file__).resolve().parents[1]
    p=read(d/'plan.json');result=read(d/'result.json');closed=read(d/'progress-private.json')
    assert closed['phase']=='CLOSED','worker must close before saved audit'
    assert sha(d/'plan.json')==result['plan_sha256']==(d/'plan.sha256').read_text().strip()
    for group in ['sources','protected','original408_preserve']:
        for path,digest in p[group].items():assert sha(path)==digest,path
    budget=result['budget'];model=budget['model'];native=budget['actual'];completed=result['status']=='NATIVE_FULL_PAIR_COMPLETED'
    assert 0<=model['ticks']<=model['reserved_ticks']<=212992 and model['worlds']<=1792
    assert native['actions']<=440 and native['resets']<=2
    streams=[read(f) for f in d.glob('*-observer-private.json')];posts=sum(len(s['posts']) for s in streams)
    meter_consistent=posts==model['ticks'] and len(streams)==model['confirmed_worlds']
    if completed:assert meter_consistent
    queries=read(d/'query-records-private.json') if(d/'query-records-private.json').exists() else []
    reference=jsonl(root/'stage453/actual_candidate/trace-private.jsonl')
    root_reference=load_receipt(root/'stage453/actual_candidate/candidate_step113-before-native-private.json')['full_pre_before_nominal']
    details={};arms=[];total_facts=total_raw=0;prefix_proofs=current_proofs=0
    prefix_keys=['pre','post','nominal','command','memory_before','nominal_memory_after','raw_ticks','raw_tire_samples','raw_hull','collision','damage','completed','finish_time_s','ended','truncated','progress_before','progress_after','goal_before','deadline_before','goal_hit_actual_step']
    for arm in result['actual']:
        name=arm['arm'];folder=d/('actual_'+name);rows=jsonl(folder/'trace-private.jsonl');own=[q for q in queries if q['arm']==name]
        checks=read(folder/'first-transition-checks-private.json') if(folder/'first-transition-checks-private.json').exists() else []
        assert len(rows)==arm['confirmed_native_facts'];total_facts+=len(rows);total_raw+=sum(r['raw_ticks'] for r in rows)
        factual=clock=fidelity=0
        for row in rows:
            label=name+'_step'+str(row['step']);postpath=folder/(label+'-after-native-private.json');post=load_receipt(postpath);fact=load_receipt(folder/(label+'-actual-fact-private.json'))
            assert post['native_full_clock_verified'] and post['actual_ledger_not_yet_committed'] and fact['forecast_not_read'] and fact['full_native_post_sha256']==sha(postpath)
            assert len(post['posts'])==row['raw_ticks'] and fact['row']==row
            factual+=1;clock+=row['raw_ticks']
            if row['step']<=112:
                expected=reference[row['step']-1];assert {k:row[k] for k in prefix_keys}=={k:expected[k] for k in prefix_keys}
                proofpath=folder/(label+'-prefix-verification-private.json')
                if proofpath.exists():
                    proof=load_receipt(proofpath);assert proof['passed'] and proof['fidelity']['passed'] and proof['fidelity']['wheel']['clipped_flag_mismatches']==0
                    prefix_proofs+=1;fidelity+=1
        fullroot=read(folder/'root-before-nominal-private.json') if(folder/'root-before-nominal-private.json').exists() else None
        if fullroot is not None:
            assert fullroot==root_reference
            if name=='P':assert fullroot==read(d/'actual_C0/root-before-nominal-private.json')
        dispatched_queries=0;query_memory_verified=0
        for q in own:
            n=q['relative_decision'];packet=load_receipt(d/(name+'_decision'+str(n)+'-before-actual-dispatch-private.json'));beforepath=folder/(name+'_step'+str(n+112)+'-before-native-private.json')
            assert not q['actual_done_before_step'] and not q['model_authorizes_actual_DONE']
            if q['guardian_certificate']:assert not q['guardian_certificate']['actual_done_allowed']
            if not beforepath.exists():continue
            before=load_receipt(beforepath);assert before['actual_ledger_before']==packet['context']['ledger']
            assert before['full_pre_before_nominal']['controller']==packet['selected_first']['memory_before'] and before['full_pre_after_nominal']['controller']==packet['selected_first']['memory_after']
            assert before['command']==packet['selected_first']['command'];query_memory_verified+=1
            verification=folder/(name+'_step'+str(n+112)+'-verification-private.json')
            if verification.exists():assert load_receipt(verification)['passed'];dispatched_queries+=1
        assert sum(bool(q['planner_used']) for q in own)<=8
        if name=='C0':assert not any(q['planner_used'] for q in own)
        current_proofs+=dispatched_queries
        if arm['completed']:
            assert len(rows)<=212 and len(checks)==len(rows)-112 and all(c['passed'] for c in checks)
            assert arm['prefix_exact_rows']==112 and not arm['authority_halted'] and not arm['awaiting_verification'] and arm['actual_ledger']['done']
            assert arm['unconfirmed_native_actions']==0 and arm['successful_native_dispatch_records']==len(rows)
            assert len(own)==len(checks)==dispatched_queries==query_memory_verified
            assert rows[-1]['completed'] and rows[-1]['finish_time_s']==arm['official_event_time_s']
            assert round((arm['official_event_time_s']-arm['reset_complete_time_s'])*1000)==arm['lap_ms']
        confirmations=[]
        for f in folder.glob('*-pending-native-confirmation-private.json'):
            x=load_receipt(f);assert x['model_guardian_cannot_commit'] and x['actual_fact_committed']
            confirmations.append(dict(native_official_finish=x['official_native_finish'],native_ledger_done=x['actual_ledger_done'],raw_ticks=x['raw_ticks']))
        tires=[t for row in rows for t in row['raw_tire_samples']]
        details[name]=dict(native_facts=factual,raw_action_ticks=clock,prefix_exact_rows=arm['prefix_exact_rows'],prefix_root_exact=fullroot is not None,current_queries=len(own),current_verified=len(checks),saved_query_memory_verified=query_memory_verified,planner_decisions=sum(bool(q['planner_used']) for q in own),planner_recipe_counts=dict(collections.Counter(q['selected_recipe'] for q in own if q['planner_used'])),guardian_recipe_counts=dict(collections.Counter(q['selected_recipe'] for q in own if not q['planner_used'])),planner_neutral_count=sum(q['planner_used'] and q['selected_recipe']=='neutralbrake' for q in own),guardian_neutral_count=sum(not q['planner_used'] and q['selected_recipe']=='neutralbrake' for q in own),pending_queries=sum(q['route']=='REGISTERED_PENDING_GUARDIAN_ONLY' for q in own),own_native_pending_confirmations=confirmations,own_native_finish=arm['completed'],clipping_mismatches=sum(c['comparison']['fidelity']['wheel']['clipped_flag_mismatches'] for c in checks),max_abs_progress_model_actual_m=max((abs(c['comparison']['progress_difference_m']) for c in checks),default=None),max_progress_interval_width_m=max((c['comparison']['progress_interval'][1]-c['comparison']['progress_interval'][0] for c in checks),default=None),max_force_ratio=max((t['force_ratio'] for t in tires),default=None),clipped_wheel_samples=sum(t['clipped'] for t in tires),wheel_samples=len(tires),max_post_path_error_m=max((r['post_projection']['path_error_m'] for r in rows),default=None))
        allowed=['arm','status','error','completed','lap_ms','official_event_time_s','native_official_finish_observed','reset_complete_time_s','confirmation_time_s','prefix_exact_rows','suffix_rows','verified_suffix_transitions','native_actions','confirmed_native_facts','unconfirmed_native_actions','successful_native_dispatch_records','reset_ticks','raw_action_ticks','planner_decisions','guardian_decisions','pending_queries','authority_halted','awaiting_verification','model_ticks','model_worlds','actual_exclusive_CPU_s','actual_exclusive_wall_s','target11_99_achieved','damage']
        safe_arm={k:arm[k] for k in allowed if k in arm};safe_arm['error']=public_error(safe_arm.get('error'));arms.append(safe_arm)
    if completed:
        assert len(arms)==2 and all(a['completed'] for a in arms)
        assert result['official_lap_gain_s']==(arms[0]['lap_ms']-arms[1]['lap_ms'])/1000
        assert total_facts==native['actions'] and all(v['clipping_mismatches']==0 for v in details.values())
    else:assert result['official_lap_gain_s'] is None
    raw_native=total_raw+sum(a.get('reset_ticks') or 0 for a in arms)
    preflight=read(d/'preflight-private.json') if(d/'preflight-private.json').exists() else None
    static=read(d/'static-result.json');old456=read(root/'stage456/result.json');old451=read(root/'stage451/result.json')
    checks=dict(source_and_protected_hashes_preserved=True,original456_failure_preserved=old456['status']=='PREMODEL_RUNNER_BINDING_STOP' and old456['new_model_ticks']==0 and old456['new_actual_actions']==0,original451_censor_preserved=old451['branches']['fullgas']['status']=='CENSORED_NO_RECOVERY14',observer_posts=posts,observer_streams=len(streams),meter_consistent=meter_consistent,confirmed_native_facts=total_facts,verified_prefix_proofs=prefix_proofs,verified_current_proofs=current_proofs,raw_native_ticks_including_reset=raw_native,both_official_native_finishes=completed)
    assert checks['original456_failure_preserved'] and checks['original451_censor_preserved']
    cost=dict(model_ticks=model['ticks'],model_reserved_ticks=model['reserved_ticks'],model_worlds=model['worlds'],model_CPU_s=model['CPU_s'],model_wall_s=model['execution_wall_s'],actual_actions=native['actions'],actual_resets=native['resets'],actual_raw_action_ticks=total_raw,actual_raw_ticks_including_reset=raw_native,actual_exclusive_CPU_s=native['CPU_s'],actual_exclusive_wall_s=native['wall_s'],wholeworker_CPU_s=budget['wholeworker_CPU_s'],wholeworker_wall_s=budget['whole_execution_wall_s'],whole_project_overhead_fully_measured=False)
    safe_static={k:v for k,v in static.items() if k in ['passed','tests','test_count','tests_run','failures','errors','audit_completed','CPU_s','wall_s','plan_sha256']}
    public=dict(stage=458,status=result['status'],error=public_error(result['error']),arm_errors={a['arm']:public_error(a.get('error')) for a in result['actual']},last_stage=result['last_stage'],closed_at_utc=closed['at_utc'],actual=arms,details=details,official_lap_gain_s=result['official_lap_gain_s'],target_s=11.99,target_achieved_by_P=completed and arms[1]['lap_ms']<=11990,verification=checks,static=safe_static,preflight=None if preflight is None else {k:v for k,v in preflight.items() if k in ['passed','ticks','worlds','actual_actions','resets']},cost=cost,local_model_gains_added=False,official_server_pixel_generalization_qualified=False,new_seed_learning_HOLDOUT_SEALED_reserve_paid=0,deadline_utc=p['deadline_utc'],plan_sha256=result['plan_sha256'],saved_audit_CPU_s=time.process_time()-cpu,saved_audit_wall_s=time.perf_counter()-wall)
    public['baseline_full_native_rows_exactly_equal453_candidate']=jsonl(d/'actual_C0/trace-private.jsonl')==reference if completed else None
    ledger_path=root/'project-effective-budget-v474.json'
    if ledger_path.exists():
        ledger=read(ledger_path);public.update(ledger_version=474,research_remaining=ledger['research_remaining'],actual_cumulative_wrapper_actions=ledger['actual_cumulative_wrapper_actions'],reserve=ledger['final_reserved_actions'],reserve_used=ledger['final_reserve_used'])
    # Private failures retain full detail without placing raw states/commands/RNG
    # or private traceback paths in the aggregate publication.
    errors=dict(worker_error=result['error'],arm_errors={a['arm']:a.get('error') for a in result['actual']})
    save(d/'closure-checks-private.json',dict(**checks,errors=errors,cost=cost,saved_audit_CPU_s=public['saved_audit_CPU_s']))
    save(g/'retry/transfer458_result.json',public)
    print(json.dumps(dict(status=public['status'],gain=public['official_lap_gain_s'],actual=arms,cost=cost,saved_audit_CPU_s=public['saved_audit_CPU_s']),ensure_ascii=False))

if __name__=='__main__':run(Path(__import__('sys').argv[1]))
