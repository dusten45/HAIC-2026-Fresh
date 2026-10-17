"""Saved-only463 closure audit; no environment, model constructor or integration."""
import collections,json,re,time
from pathlib import Path
from retry.loss389_analyze import read,save,sha
from retry.receipt421_io import load_receipt


def jsonl(path):
    return [json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []


def public_error(value):
    return None if value is None else re.sub(r'/(?:workspace|tmp)/[^\s\'\"]+', '[private-path]', str(value))


def durable(path,value):
    import os,tempfile
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as out:
            json.dump(value,out,indent=2,sort_keys=True);out.write('\n');out.flush();os.fsync(out.fileno())
        os.replace(name,path)
        fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
    finally:
        if os.path.exists(name):os.unlink(name)


def reconcile_ledger(root,d,nd,p,result):
    """Close the same LIVE v475 without debiting charged actions a second time."""
    import fcntl
    prior=Path(p['budget_before_path']);path=Path(p['ledger_path']);plan=sha(d/'plan.json')
    assert prior.name=='project-effective-budget-v474.json' and path.name=='project-effective-budget-v475.json'
    assert sha(prior)==p['budget_before_sha256'];old=read(prior)
    assert (old['research_remaining'],old['actual_cumulative_wrapper_actions'],old['final_reserved_actions'],old['final_reserve_used'])==(26695,1321369,84000,0)
    journals=[read(f) for f in sorted(nd.glob('charge463-*-private.json'))];counts=dict(actions=0,resets=0);aa={};rr={}
    for index,j in enumerate(journals,1):
        assert j['sequence']==index and j['owner']['plan_sha256']==plan and j['owner']['native_directory']==str(nd.resolve())
        assert j['kind'] in ('action','reset') and j['arm'] in ('Original','SecantOnce')
        key='actions' if j['kind']=='action' else 'resets';counts[key]+=1;group=aa if key=='actions' else rr;group[j['arm']]=group.get(j['arm'],0)+1
        assert (j['actions'],j['resets'],j['arm_actions'],j['arm_resets'])==(counts['actions'],counts['resets'],aa,rr)
        assert j['research_remaining']==26695-counts['actions']
    charged=counts['actions'];resets=counts['resets'];assert charged<=390 and resets<=2 and all(x<=195 for x in aa.values()) and all(x<=1 for x in rr.values())
    measured=result['budget']['actual'];assert measured['actions']<=charged and measured['resets']<=resets
    if result['status']=='NATIVE_FULL_PAIR_COMPLETED':assert measured['actions']==charged and measured['resets']==resets
    if not path.exists():
        assert not journals and measured['actions']==measured['resets']==0
        return dict(ledger_version=474,ledger475_created=False,research_remaining=26695,actual_cumulative_wrapper_actions=1321369,reserve=84000,reserve_used=0,charged_actions=0,charged_resets=0,closure_additional_debit=0)
    with open(str(path)+'.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);ledger=read(path);frozen_hash=sha(path)
        assert ledger['version']==475 and ledger['prior_budget_sha256']==p['budget_before_sha256']
        assert ledger['owner']['plan_sha256']==plan and ledger['owner']['native_directory']==str(nd.resolve())
        assert ledger['owner']==journals[-1]['owner'] and ledger['owner']['pid']==read(d/'opening.json')['pid']
        assert (ledger['stage463_new_wrapper_actions'],ledger['stage463_actual_resets'],ledger['research_remaining'],ledger['actual_cumulative_wrapper_actions'])==(charged,resets,26695-charged,1321369+charged)
        assert ledger['final_reserved_actions']==84000 and ledger['final_reserve_used']==0
        assert ledger['stage463_status'] in ('LIVE','CLOSED') and sha(path)==frozen_hash
        if ledger['stage463_status']=='LIVE':
            ledger.update(stage463_status='CLOSED',research_status='STAGE463_CLOSED_CHARGED_ATTEMPTS_RECONCILED',stage463_worker_status=result['status'],stage463_closed_plan_sha256=plan,stage463_charge_journal_records=len(journals),stage463_closure_additional_debit=0)
            durable(path,ledger)
        assert sha(prior)==p['budget_before_sha256']
    return dict(ledger_version=475,ledger475_created=True,ledger_status='CLOSED',research_remaining=26695-charged,actual_cumulative_wrapper_actions=1321369+charged,reserve=84000,reserve_used=0,charged_actions=charged,charged_resets=resets,charge_journal_records=len(journals),charged_minus_budget_actions=charged-measured['actions'],closure_additional_debit=0)


def run(root):
    cpu=time.process_time();wall=time.perf_counter();d=root/'stage463';g=Path(__file__).resolve().parents[1]
    p=read(d/'plan.json');nd=Path(p['native_directory']);result=read(d/'result.json');closed=read(d/'progress-private.json')
    assert closed['phase']=='CLOSED','worker must close before saved audit'
    assert sha(d/'plan.json')==result['plan_sha256']==(d/'plan.sha256').read_text().strip()
    for group in ['sources','protected','original408_preserve']:
        for path,digest in p[group].items():assert sha(path)==digest,path
    budget=result['budget'];model=budget['model'];native=budget['actual'];completed=result['status']=='NATIVE_FULL_PAIR_COMPLETED'
    assert 0<=model['ticks']<=model['reserved_ticks']<=30370 and model['worlds']<=597
    model_policy_parents=sum(v for k,v in model['worlds_by_tag'].items() if 'model_parent' in k)
    assert model_policy_parents==0
    assert native['actions']<=390 and native['resets']<=2
    streams=[read(f) for f in d.glob('*-observer-private.json')];posts=sum(len(s['posts']) for s in streams)
    meter_consistent=posts==model['ticks'] and len(streams)==model['confirmed_worlds']
    if completed:assert meter_consistent
    queries=read(d/'query-records-private.json') if(d/'query-records-private.json').exists() else []
    reference=jsonl(root/'stage458/actual_P/trace-private.jsonl')
    root_reference=load_receipt(root/'stage458/actual_P/P_step126-before-native-private.json')['full_pre_before_nominal']
    details={};arms=[];total_facts=total_raw=0;prefix_proofs=current_proofs=0
    prefix_keys=['pre','post','nominal','command','memory_before','nominal_memory_after','raw_ticks','raw_tire_samples','raw_hull','collision','damage','completed','finish_time_s','ended','truncated','progress_before','progress_after','goal_before','deadline_before','goal_hit_actual_step']
    for arm in result['actual']:
        name=arm['arm'];folder=nd/('actual_'+name);rows=jsonl(folder/'trace-private.jsonl');own=[q for q in queries if q['arm']==name]
        checks=read(folder/'first-transition-checks-private.json') if(folder/'first-transition-checks-private.json').exists() else []
        assert [r['step'] for r in rows]==list(range(1,len(rows)+1))
        assert len(rows)==arm['confirmed_native_facts'];total_facts+=len(rows);total_raw+=sum(r['raw_ticks'] for r in rows)
        factual=clock=fidelity=0
        for row in rows:
            label=name+'_step'+str(row['step']);postpath=folder/(label+'-after-native-private.json');post=load_receipt(postpath);fact=load_receipt(folder/(label+'-actual-fact-private.json'))
            assert post['native_full_clock_verified'] and post['actual_ledger_not_yet_committed'] and fact['forecast_not_read'] and fact['full_native_post_sha256']==sha(postpath)
            assert len(post['posts'])==row['raw_ticks'] and fact['row']==row
            assert abs((row['post']['time']-row['pre']['time'])-row['raw_ticks']/50)<1e-7
            factual+=1;clock+=row['raw_ticks']
            if row['step']<=125:
                expected=reference[row['step']-1];assert {k:row[k] for k in prefix_keys}=={k:expected[k] for k in prefix_keys}
                proofpath=folder/(label+'-prefix-verification-private.json')
                if proofpath.exists():
                    proof=load_receipt(proofpath);assert proof['passed'] and proof['fidelity']['passed'] and proof['fidelity']['wheel']['clipped_flag_mismatches']==0
                    prefix_proofs+=1;fidelity+=1
        fullroot=read(folder/'root-before-nominal-private.json') if(folder/'root-before-nominal-private.json').exists() else None
        if fullroot is not None:
            assert fullroot==root_reference
            if name=='SecantOnce':assert fullroot==read(nd/'actual_Original/root-before-nominal-private.json')
        dispatched_queries=0;query_memory_verified=0
        for q in own:
            n=q['relative_decision'];packet=load_receipt(d/(name+'_decision'+str(n)+'-before-actual-dispatch-private.json'));beforepath=folder/(name+'_step'+str(n+125)+'-before-native-private.json')
            assert not q['actual_done_before_step'] and not q['model_authorizes_actual_DONE']
            if q['guardian_certificate']:assert not q['guardian_certificate']['actual_done_allowed']
            if not beforepath.exists():continue
            before=load_receipt(beforepath);assert before['actual_ledger_before']==packet['context']['ledger']
            assert before['full_pre_before_nominal']['controller']==packet['selected_first']['memory_before'] and before['full_pre_after_nominal']['controller']==packet['selected_first']['memory_after']
            assert before['command']==packet['selected_first']['command']
            assert packet['context']['parent']['raw_clock_tick']==before['actual_ledger_before']['last_clock_tick']==round(before['full_pre_before_nominal']['physical']['actual_time']*50)
            assert q['parent_memory_RNG_ledger_unchanged'];query_memory_verified+=1
            verification=folder/(name+'_step'+str(n+125)+'-verification-private.json')
            if verification.exists():assert load_receipt(verification)['passed'];dispatched_queries+=1
        assert not arm['planner_decisions'] and len(own)<=70
        assert all(q['fixed_first']==(q['relative_decision']==1) for q in own)
        if own:assert own[0]['selected_recipe']==('nominal' if name=='Original' else 'fullgas')
        current_proofs+=dispatched_queries
        if arm['completed']:
            assert fidelity==125 and len(rows)<=195 and len(checks)==len(rows)-125 and all(c['passed'] for c in checks)
            assert arm['prefix_exact_rows']==125 and not arm['authority_halted'] and not arm['awaiting_verification'] and arm['actual_ledger']['done']
            assert arm['unconfirmed_native_actions']==0 and arm['successful_native_dispatch_records']==len(rows)
            assert len(own)==len(checks)==dispatched_queries==query_memory_verified
            assert rows[-1]['completed'] and rows[-1]['finish_time_s']==arm['official_event_time_s']
            assert round((arm['official_event_time_s']-arm['reset_complete_time_s'])*1000)==arm['lap_ms']
        confirmations=[]
        for f in folder.glob('*-pending-native-confirmation-private.json'):
            x=load_receipt(f);assert x['model_guardian_cannot_commit'] and x['actual_fact_committed']
            confirmations.append(dict(native_official_finish=x['official_native_finish'],native_ledger_done=x['actual_ledger_done'],raw_ticks=x['raw_ticks']))
        tires=[t for row in rows for t in row['raw_tire_samples']]
        details[name]=dict(native_facts=factual,raw_action_ticks=clock,prefix_exact_rows=arm['prefix_exact_rows'],prefix_root_exact=fullroot is not None,current_queries=len(own),current_verified=len(checks),saved_query_memory_verified=query_memory_verified,fixed_first_queries=sum(bool(q['fixed_first']) for q in own),fixed_first_recipe_counts=dict(collections.Counter(q['selected_recipe'] for q in own if q['fixed_first'])),guardian_recipe_counts=dict(collections.Counter(q['selected_recipe'] for q in own if not q['fixed_first'])),fixed_first_neutral_count=sum(q['fixed_first'] and q['selected_recipe']=='neutralbrake' for q in own),guardian_neutral_count=sum(not q['fixed_first'] and q['selected_recipe']=='neutralbrake' for q in own),pending_queries=sum(q['route']=='REGISTERED_PENDING_GUARDIAN_ONLY' for q in own),own_native_pending_confirmations=confirmations,own_native_finish=arm['completed'],clipping_mismatches=sum(c['comparison']['fidelity']['wheel']['clipped_flag_mismatches'] for c in checks),max_abs_progress_model_actual_m=max((abs(c['comparison']['progress_difference_m']) for c in checks),default=None),max_progress_interval_width_m=max((c['comparison']['progress_interval'][1]-c['comparison']['progress_interval'][0] for c in checks),default=None),max_force_ratio=max((t['force_ratio'] for t in tires),default=None),clipped_wheel_samples=sum(t['clipped'] for t in tires),wheel_samples=len(tires),max_post_path_error_m=max((r['post_projection']['path_error_m'] for r in rows),default=None))
        suffix=rows[125:];first=suffix[0] if suffix else None;first13=suffix[:13]
        details[name]['native_remaining_tail_s']=None if not arm['completed'] or first is None else arm['official_event_time_s']-first['pre']['time']
        details[name]['first_native_wrapper']=None if first is None else dict(raw_ticks=first['raw_ticks'],duration_s=first['raw_ticks']/50,speed_before_m_s=first['pre']['speed'],speed_after_m_s=first['post']['speed'],delta_speed_m_s=first['post']['speed']-first['pre']['speed'],post_path_error_m=first['post_projection']['path_error_m'])
        first_tires=[t for row in first13 for t in row['raw_tire_samples']]
        details[name]['first13_native_summary']=dict(actions=len(first13),raw_ticks=sum(r['raw_ticks'] for r in first13),max_post_path_error_m=max((r['post_projection']['path_error_m'] for r in first13),default=None),max_force_ratio=max((t['force_ratio'] for t in first_tires),default=None),clipped_wheel_samples=sum(t['clipped'] for t in first_tires),wheel_samples=len(first_tires),speed_after_m_s=first13[-1]['post']['speed'] if first13 else None)
        allowed=['arm','status','error','completed','lap_ms','official_event_time_s','native_official_finish_observed','reset_complete_time_s','confirmation_time_s','prefix_exact_rows','suffix_rows','verified_suffix_transitions','native_actions','confirmed_native_facts','unconfirmed_native_actions','successful_native_dispatch_records','reset_ticks','raw_action_ticks','planner_decisions','guardian_decisions','pending_queries','authority_halted','awaiting_verification','model_ticks','model_worlds','actual_exclusive_CPU_s','actual_exclusive_wall_s','target11_99_achieved','damage']
        safe_arm={k:arm[k] for k in allowed if k in arm};safe_arm['error']=public_error(safe_arm.get('error'));arms.append(safe_arm)
    if completed:
        assert budget['wholeworker_CPU_s']<1800 and budget['whole_execution_wall_s']<2400
        assert native['CPU_s']<240 and native['wall_s']<480
        assert len(arms)==2 and all(a['completed'] for a in arms)
        assert result['official_lap_gain_s']==(arms[0]['lap_ms']-arms[1]['lap_ms'])/1000
        assert total_facts==native['actions'] and all(v['clipping_mismatches']==0 for v in details.values())
    else:assert result['official_lap_gain_s'] is None
    raw_native=total_raw+sum(a.get('reset_ticks') or 0 for a in arms)
    preflight=read(d/'preflight-private.json') if(d/'preflight-private.json').exists() else None
    static=read(d/'static-result.json');old456=read(root/'stage456/result.json');old451=read(root/'stage451/result.json')
    checks=dict(source_and_protected_hashes_preserved=True,original456_failure_preserved=old456['status']=='PREMODEL_RUNNER_BINDING_STOP' and old456['new_model_ticks']==0 and old456['new_actual_actions']==0,original451_censor_preserved=old451['branches']['fullgas']['status']=='CENSORED_NO_RECOVERY14',observer_posts=posts,observer_streams=len(streams),meter_consistent=meter_consistent,model_policy_parent_worlds=model_policy_parents,confirmed_native_facts=total_facts,verified_prefix_proofs=prefix_proofs,verified_current_proofs=current_proofs,raw_native_ticks_including_reset=raw_native,both_official_native_finishes=completed)
    assert checks['original456_failure_preserved'] and checks['original451_censor_preserved']
    cost=dict(model_ticks=model['ticks'],model_reserved_ticks=model['reserved_ticks'],model_worlds=model['worlds'],model_CPU_s=model['CPU_s'],model_wall_s=model['execution_wall_s'],actual_actions=native['actions'],actual_resets=native['resets'],actual_raw_action_ticks=total_raw,actual_raw_ticks_including_reset=raw_native,actual_exclusive_CPU_s=native['CPU_s'],actual_exclusive_wall_s=native['wall_s'],wholeworker_CPU_s=budget['wholeworker_CPU_s'],wholeworker_wall_s=budget['whole_execution_wall_s'],whole_project_overhead_fully_measured=False)
    safe_static={k:v for k,v in static.items() if k in ['passed','tests','test_count','tests_run','failures','errors','audit_completed','CPU_s','wall_s','plan_sha256']}
    public=dict(stage=463,status=result['status'],error=public_error(result['error']),arm_errors={a['arm']:public_error(a.get('error')) for a in result['actual']},last_stage=result['last_stage'],closed_at_utc=closed['at_utc'],actual=arms,details=details,official_lap_gain_s=result['official_lap_gain_s'],target_s=11.99,target_achieved_by_SecantOnce=completed and arms[1]['lap_ms']<=11990,verification=checks,static=safe_static,preflight=None if preflight is None else {k:v for k,v in preflight.items() if k in ['passed','ticks','worlds','actual_actions','resets']},cost=cost,local_model_gains_added=False,model462_tail_added=False,official_server_pixel_generalization_qualified=False,new_seed_learning_HOLDOUT_SEALED_reserve_paid=0,deadline_utc=p['deadline_utc'],plan_sha256=result['plan_sha256'],saved_audit_CPU_s=time.process_time()-cpu,saved_audit_wall_s=time.perf_counter()-wall)
    public['original_full_native_rows_exactly_equal458_P']=jsonl(nd/'actual_Original/trace-private.jsonl')==reference if completed else None
    public.update(reconcile_ledger(root,d,nd,p,result))
    public['saved_audit_CPU_s']=time.process_time()-cpu
    public['saved_audit_wall_s']=time.perf_counter()-wall
    # Private failures retain full detail without placing raw states/commands/RNG
    # or private traceback paths in the aggregate publication.
    errors=dict(worker_error=result['error'],arm_errors={a['arm']:a.get('error') for a in result['actual']})
    save(d/'closure-checks-private.json',dict(**checks,errors=errors,cost=cost,saved_audit_CPU_s=public['saved_audit_CPU_s']))
    save(d/'saved-closure-private.json',public)
    save(g/'retry/transfer463_result.json',public)
    print(json.dumps(dict(status=public['status'],gain=public['official_lap_gain_s'],actual=arms,cost=cost,saved_audit_CPU_s=public['saved_audit_CPU_s']),ensure_ascii=False))

if __name__=='__main__':run(Path(__import__('sys').argv[1]))
