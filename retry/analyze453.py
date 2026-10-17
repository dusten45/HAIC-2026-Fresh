"""Saved native whole-pair authority, official timing and cost audit only."""
import json,time
from pathlib import Path
from retry.loss389_analyze import read,save,sha
from retry.receipt421_io import load_receipt


def native_segments453(root,result):
    cpu=time.process_time();d=root/'stage453';parts={}
    for arm in result['actual']:
        crossing=arm['B_switch']['root270_crossing']['elapsed_bracket_s']
        to270=[22*4/50+t for t in crossing];lap=arm['lap_ms']/1000
        parts[arm['arm']]=dict(lap_to270_native_bracket_s=to270,remaining270_to_official_finish_native_bracket_s=[lap-to270[1],lap-to270[0]])
    a,b=[parts[k]['lap_to270_native_bracket_s'] for k in ['baseline','candidate']]
    gain270=[a[0]-b[1],a[1]-b[0]];gain=result['official_lap_gain_s']
    rows=lambda f:[json.loads(x) for x in f.read_text().splitlines()]
    same=rows(d/'actual_baseline/trace-private.jsonl')==rows(root/'stage442/actual_C0/trace-private.jsonl')
    return dict(parts=parts,native270_gain_bracket_s=gain270,official_full_lap_gain_s=gain,candidate_additional_time_after270_s=[gain270[0]-gain,gain270[1]-gain],causal_source_of_extra_time_identified=False,baseline_full_native_rows_exactly_equal442=same,analysis_new_physics_calls=0,CPU_s=time.process_time()-cpu)


def run(root):
    cpu=time.process_time();g=Path(__file__).resolve().parents[1];d=root/'stage453';p=read(d/'plan.json');result=read(d/'result.json');budget=result['budget'];model=budget['model'];native=budget['actual']
    for group in ['sources','protected','original408_preserve']:
        for f,h in p[group].items():assert sha(f)==h,f
    assert sha(d/'plan.json')==result['plan_sha256']==(d/'plan.sha256').read_text().strip()
    assert model['ticks']<=model['reserved_ticks']<=98304 and model['worlds']<=1792 and native['actions']<=440 and native['resets']<=2
    streams=[read(f) for f in d.glob('*-observer-private.json')];posts=sum(len(s['posts']) for s in streams)
    assert posts==model['ticks'] and len(streams)==model['confirmed_worlds']
    completed=result['status']=='NATIVE_FULL_PAIR_COMPLETED'
    if completed:assert len(result['actual'])==2 and all(a['completed'] for a in result['actual'])
    else:assert result['official_lap_gain_s'] is None
    details={};total_facts=total_raw=0;queries=read(d/'query-records-private.json') if(d/'query-records-private.json').exists() else []
    for arm in result['actual']:
        name=arm['arm'];folder=d/('actual_'+name);rows=[json.loads(s) for s in (folder/'trace-private.jsonl').read_text().splitlines()];checks=read(folder/'first-transition-checks-private.json');own_queries=[q for q in queries if q['arm']==name]
        assert len(rows)==arm['confirmed_native_facts'];total_facts+=len(rows);total_raw+=sum(r['raw_ticks'] for r in rows)
        for row in rows:
            label=name+'_step'+str(row['step']);post=load_receipt(folder/(label+'-after-native-private.json'));fact=load_receipt(folder/(label+'-actual-fact-private.json'))
            assert post['native_full_clock_verified'] and post['actual_ledger_not_yet_committed'] and fact['forecast_not_read'] and fact['full_native_post_sha256']==sha(folder/(label+'-after-native-private.json'))
        for q in own_queries:
            packet=load_receipt(d/(name+'_decision'+str(q['relative_decision'])+'-before-actual-dispatch-private.json'));step=q['relative_decision']+22
            before=load_receipt(folder/(name+'_step'+str(step)+'-before-native-private.json'))
            assert before['actual_ledger_before']==packet['context']['ledger'] and before['full_pre_before_nominal']['controller']==packet['selected_first']['memory_before'] and before['full_pre_after_nominal']['controller']==packet['selected_first']['memory_after']
            if q['selected_recipe']=='fullgas':assert name=='candidate' and q['relative_decision']==1 and q['mode']=='FIXED_FIRST_PULSE'
            if q['selected_recipe']=='neutralbrake':assert q['mode'] in ['CONDITIONAL_B','REGISTERED_PENDING_B'] and q['B_started']
            if q['guardian_certificate']:assert not q['guardian_certificate']['actual_done_allowed']
            assert not q['actual_done_before_step'] and not q['model_authorizes_actual_DONE']
        if arm['completed']:
            assert len(checks)==len(rows)-22 and all(x['passed'] for x in checks) and not arm['authority_halted'] and not arm['awaiting_verification'] and arm['actual_ledger']['done']
            assert arm['unconfirmed_native_actions']==0 and arm['successful_native_dispatch_records']==len(rows)
            assert rows[-1]['completed'] and rows[-1]['finish_time_s']==arm['official_event_time_s']
            assert round((arm['official_event_time_s']-arm['reset_complete_time_s'])*1000)==arm['lap_ms']
            assert arm['target11_99_achieved']==(arm['lap_ms']<=11990)
        pending_confirmations=[]
        for f in folder.glob('*-pending-native-confirmation-private.json'):
            value=load_receipt(f);assert value['model_guardian_cannot_commit'] and value['actual_fact_committed'];pending_confirmations.append(dict(native_official_finish=value['official_native_finish'],native_ledger_done=value['actual_ledger_done'],raw_ticks=value['raw_ticks']))
        tires=[t for row in rows for t in row['raw_tire_samples']]
        details[name]=dict(native_facts=len(rows),current_verified=len(checks),current_queries=len(own_queries),pending_native_confirmations=pending_confirmations,first_pulse_count=arm['fixed_pulse_count'],neutral_count=arm['B_neutral_count'],B_switch_after_native_step=None if arm['B_switch'] is None else arm['B_switch']['after_native_step'],clipping_mismatches=sum(c['comparison']['fidelity']['wheel']['clipped_flag_mismatches'] for c in checks),max_abs_progress_model_actual_m=max((abs(c['comparison']['progress_difference_m']) for c in checks),default=None),max_progress_interval_width_m=max((c['comparison']['progress_interval'][1]-c['comparison']['progress_interval'][0] for c in checks),default=None),max_force_ratio=max((t['force_ratio'] for t in tires),default=None),clipped_wheel_samples=sum(t['clipped'] for t in tires),wheel_samples=len(tires),max_post_path_error_m=max((r['post_projection']['path_error_m'] for r in rows),default=None))
    assert total_facts<=native['actions']
    source_passed=all((d/name).exists() and read(d/name)['passed'] for name in ['source-qualification-private.json','qualification.json','pending-qualification.json','parent-pending-qualification.json'])
    checks=dict(source_and_protected_preserved=True,all_source_preflight_passed=source_passed,observer_posts=posts,observer_streams=len(streams),confirmed_native_facts=total_facts,raw_action_ticks=total_raw,resets=native['resets'],raw_native_including_reset=total_raw+sum(a['reset_ticks'] or 0 for a in result['actual']),both_official_native_finishes=completed,original451_censor_preserved=read(root/'stage451/result.json')['branches']['fullgas']['status']=='CENSORED_NO_RECOVERY14',saved_CPU_s=time.process_time()-cpu)
    save(d/'closure-checks-private.json',checks)
    public=dict(stage=453,status=result['status'],error=result['error'],actual=[{k:v for k,v in a.items() if k not in ['actual_ledger','B_switch']} for a in result['actual']],official_lap_gain_s=result['official_lap_gain_s'],details=details,verification=checks,cost=dict(model_ticks=model['ticks'],model_reserved_ticks=model['reserved_ticks'],model_worlds=model['worlds'],model_CPU_s=model['CPU_s'],model_wall_s=model['execution_wall_s'],actual_actions=native['actions'],actual_resets=native['resets'],actual_exclusive_CPU_s=native['CPU_s'],actual_exclusive_wall_s=native['wall_s'],wholeworker_CPU_s=budget['wholeworker_CPU_s'],wholeworker_wall_s=budget['whole_execution_wall_s'],static=read(d/'static-result.json'),saved_audit_CPU_s=checks['saved_CPU_s'],full_project_overhead_measured=False),target_s=11.99,local_gains_added=False,pixel_generalization_official_server_qualified=False,deadline_utc=p['deadline_utc'])
    if completed:public['saved_segment_diagnosis']=native_segments453(root,result)
    save(g/'retry/pair453_result.json',public)
    print(json.dumps(dict(status=result['status'],gain=result['official_lap_gain_s'],details=details,cost=public['cost'])))

if __name__=='__main__':run(Path(__import__('sys').argv[1]))
