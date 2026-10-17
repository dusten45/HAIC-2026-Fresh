"""Saved-only native transfer audit and common-boundary debt diagnostics."""
import json,math,sys,time
from pathlib import Path
from retry.loss389_analyze import read,save,sha
from retry.receipt421_io import load_receipt
from retry.analyze446 import state_diagnostics
from retry.paired417_common import arrival


def exit_samples(rows,hit,line):
    root_clock=round(rows[0]['pre']['time']*50);lo,hi=hit['rawtick_bracket'];points={};lower=None
    for row in rows:
        phase=row['nominal_memory_after']['C']['phase']
        for hull in row['raw_hull']:
            tick=round(hull['time']*50)-root_clock
            if tick in [lo,hi]:points[tick]=state_diagnostics(dict(pos=hull['origin_position'],vel=hull['COM_linear_velocity'],angle=hull['angle'],yaw=hull['yaw']),line,phase)
            if tick==lo:
                k=hull['raw_tick']-1;lower=row['raw_tire_samples'][4*k:4*k+4]
        post=row['post'];tick=round(post['time']*50)-root_clock
        if tick in [lo,hi] and tick not in points:points[tick]=state_diagnostics(dict(pos=post['pos'],vel=post['vel'],angle=post['angle'],yaw=post['yaw']),line,phase)
    assert set(points)=={lo,hi} and lower is not None
    body={key:[min(v[key] for v in points.values()),max(v[key] for v in points.values())] for key in next(iter(points.values()))}
    wheel={key:[min(v[key] for v in lower),max(v[key] for v in lower)] for key in ['joint_angle','omega','force_ratio','lateral_slip_m_s','longitudinal_slip_m_s']}
    return dict(body_exit_bracket_sample_ranges=body,lower_crossing_preclip_tire_ranges=wheel,sample_ranges_not_continuous_time_bounds=True),dict(points=points,lower_preclip=lower)


def run(root):
    cpu=time.process_time();g=Path(__file__).resolve().parents[1];d=root/'stage448';p=read(d/'plan.json');result=read(d/'result.json')
    for group in ['sources','protected','original408_preserve']:
        for f,h in p[group].items():assert sha(f)==h,f
    assert result['plan_sha256']==sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
    budget=result['budget'];m=budget['model'];n=budget['actual']
    assert m['ticks']==m['reserved_ticks'] and m['ticks']<=6144 and m['worlds']<=128
    assert n['actions']<=96 and n['resets']<=2
    # Failed runs retain costs and censored arms; never manufacture a gain.
    if result['status']!='NATIVE_EXIT60_PAIR_COMPLETED':assert result['gain60_bracket_s'] is None
    assert m['CPU_s']<180 and m['execution_wall_s']<300 and n['CPU_s']<90 and n['wall_s']<180
    streams=[read(f) for f in d.glob('*-observer-private.json')]
    observer_posts=sum(len(s['posts']) for s in streams)
    assert observer_posts==m['ticks'] and len(streams)==m['worlds']
    fixed=read(Path(p['fixed_plan']));line=fixed['line'];details={};private={};proofs={};total_rows=total_raw=0
    for arm in result['actual']:
        name=arm['arm'];folder=d/('actual_'+name);rows=[json.loads(s) for s in (folder/'trace-private.jsonl').read_text().splitlines()]
        total_rows+=len(rows);total_raw+=sum(row['raw_ticks'] for row in rows)
        assert len(rows)==arm['confirmed_native_facts']
        if arm['status']=='NATIVE_EXIT60_VERIFIED':
            assert arm['prefix_exact_rows']==22 and arm['suffix_rows']==arm['verified_suffix_transitions'] and not arm['authority_halted'] and not arm['awaiting_verification']
            assert arm['unconfirmed_native_actions']==0 and arm['successful_native_dispatch_records']==len(rows)
        for row in rows:
            step=row['step'];fact=load_receipt(folder/(name+'_step'+str(step)+'-actual-fact-private.json'))
            post=load_receipt(folder/(name+'_step'+str(step)+'-after-native-private.json'))
            assert fact['forecast_not_read'] and post['actual_ledger_not_yet_committed'] and post['native_full_clock_verified']
            assert fact['full_native_post_sha256']==sha(folder/(name+'_step'+str(step)+'-after-native-private.json'))
        checks=read(folder/'first-transition-checks-private.json');queries=[q for q in read(d/'query-records-private.json') if q['arm']==name]
        assert all(c['passed'] for c in checks)
        for query in queries:
            label=name+'_current'+str(query['decision']);record=load_receipt(d/(label+'-before-actual-dispatch-private.json'))
            a=read(d/(label+'_copy1-private.json'));b=read(d/(label+'_copy2-private.json'))
            assert a['rows']==b['rows'] and a['final_state']==b['final_state'] and a['controller_memory']==b['controller_memory']
            assert record['selected_first']==a['rows'][0] and len(a['rows'])<=13
            assert not any(row['safety'] for row in a['rows']) and not a['model_ledger']['deadline_missed']
            for rep in [1,2]:
                observer=read(d/(label+'_copy'+str(rep)+'-observer-private.json'))
                assert all(act['command']==act['nominal'] for act in observer['actions'][1:])
                if query['recipe']=='nominal':assert observer['actions'][0]['command']==observer['actions'][0]['nominal']
            step=query['decision']+22
            pre=load_receipt(folder/(name+'_step'+str(step)+'-before-native-private.json'))
            assert pre['actual_ledger_before']==record['context']['ledger']
            assert pre['full_pre_before_nominal']['controller']==record['selected_first']['memory_before']
            assert pre['full_pre_after_nominal']['controller']==record['selected_first']['memory_after']
        suffix=rows[22:]
        if arm['crossing_from_original_root']['reached']:
            hit=arrival(suffix,__import__('numpy').asarray(line),suffix[0]['progress_before'],suffix[0]['progress_before']+60.)
            assert hit==arm['crossing_from_original_root']
            details[name],private[name]=exit_samples(suffix,hit,line)
            old=read(g/'retry/continuation447_result.json')['branches'][name]['crossing_from_original_root']
            details[name]['same_crossing_bracket_as_live447_model']=hit['elapsed_bracket_s']==old['elapsed_bracket_s']
        if name=='nominal':
            reference=[json.loads(s) for s in (root/'stage442/actual_C0/trace-private.jsonl').read_text().splitlines()][:len(rows)]
            assert rows==reference
        proofs[name]=dict(confirmed_native_facts=len(rows),fresh_current_pairs=len(queries),verified_suffix=len(checks),native_fact_before_forecast_comparison=True,independent_pairs_exact=True,command_memory_current_exact=True,
            clipping_mismatches=sum(c['comparison']['fidelity']['wheel']['clipped_flag_mismatches'] for c in checks),
            max_progress_comparison_interval_width_m=max((c['comparison']['progress_interval'][1]-c['comparison']['progress_interval'][0] for c in checks),default=None),
            max_abs_progress_model_actual_m=max((abs(c['comparison']['progress_difference_m']) for c in checks),default=None))
    assert total_rows==n['actions'] and all(s['failure'] is None for s in streams)
    save(d/'exit-samples-private.json',private)
    checks=dict(source_hashes_and_protected_preserved=True,original_main_preserved=True,source_g1_passed=read(d/'source-qualification-private.json')['passed'],static_tests=read(d/'static-result.json')['tests'],observer_posts=observer_posts,observer_streams=len(streams),native_facts=total_rows,raw_native_action_ticks=total_raw,actual_resets=n['resets'],actual_raw_ticks_including_reset=total_raw+sum(a['reset_ticks'] or 0 for a in result['actual']),first_error_no_retry=True,saved_CPU_s=time.process_time()-cpu)
    save(d/'closure-checks-private.json',checks)
    public=dict(stage=448,status=result['status'],error=result['error'],gain60_bracket_s=result['gain60_bracket_s'],actual=[{k:v for k,v in a.items() if k!='actual_ledger'} for a in result['actual']],details=details,factual_verification=proofs,verification=checks,
        cost=dict(model_ticks=m['ticks'],model_worlds=m['worlds'],model_CPU_s=m['CPU_s'],model_wall_s=m['execution_wall_s'],actual_wrapper_actions=n['actions'],actual_resets=n['resets'],actual_exclusive_CPU_s=n['CPU_s'],actual_exclusive_wall_s=n['wall_s'],whole_worker_CPU_s=budget['wholeworker_CPU_s'],whole_worker_wall_s=budget['whole_execution_wall_s'],model_region_cleanup_included=True,static_attempts=[read(d/'pre-model-v1/static-result.json'),read(d/'static-result.json')],saved_audit_CPU_s=checks['saved_CPU_s'],project_overhead_fully_measured=False),terminal_debt_resolved=False,wholelap_pixel_generalization_promoted=False,no_gain_addition=True,new_learning_seed_HOLDOUT_SEALED_reserve_paid=0,deadline_utc=p['deadline_utc'])
    save(g/'retry/transfer448_result.json',public)
    print(json.dumps(dict(status=result['status'],gain=result['gain60_bracket_s'],details=details,cost=public['cost'],verification=proofs)))

if __name__=='__main__':run(Path(sys.argv[1]))
