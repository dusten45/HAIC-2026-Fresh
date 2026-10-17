"""Saved-only finite composition audit; no new model queries or parent actions."""
import json,time
from pathlib import Path
from dataclasses import asdict
from retry.loss389_analyze import read,save,sha
from retry.receipt421_io import load_receipt
from retry.pilot420_backend import model_ledger_view,fingerprint
from retry.planner419_model_ledger import ForecastLedger
from retry.root449 import load_root449


def run(root):
    cpu=time.process_time();g=Path(__file__).resolve().parents[1];d=root/'stage451';p=read(d/'plan.json');result=read(d/'result.json');budget=result['budget']
    assert result['status']=='B_COMPOSITION_SCOPE_COMPLETED' and result['error'] is None
    for group in ['sources','protected','original408_preserve']:
        for f,h in p[group].items():assert sha(f)==h,f
    assert sha(d/'plan.json')==result['plan_sha256']==(d/'plan.sha256').read_text().strip()
    assert budget['ticks']==budget['reserved_ticks']==7312 and budget['worlds']==budget['confirmed_worlds']==126
    assert budget['CPU_s']<420 and budget['execution_wall_s']<600
    streams=[read(f) for f in d.glob('*-observer-private.json')]
    assert len(streams)==126 and sum(len(s['posts']) for s in streams)==7312 and all(s['failure'] is None for s in streams)
    details={};query_count=shadow_count=expected_rejected=0;prefix_ticks=parent_B_ticks=held_ticks=0;private={}
    for arm,branch in result['branches'].items():
        data=load_root449(root,arm);actual=asdict(data['ledger']);a=read(d/(arm+'1-private.json'));b=read(d/(arm+'2-private.json'));held=read(d/(arm+'_held-private.json'))
        assert a['rows']==b['rows'] and a['final_state']==b['final_state'] and a['controller_memory']==b['controller_memory']
        assert a['nominal_tail_ranking_forbidden'] and b['nominal_tail_ranking_forbidden'] and held['nominal_tail_ranking_forbidden']
        n=branch['prefix_actions'];B=branch['B_actions_each'];assert B<=14
        assert len(a['rows'])==n+B and len(held['rows'])==n+1
        assert a['rows'][:n]==held['rows'][:n]==read(root/'stage450'/(arm+'1-private.json'))['rows']
        assert all(held['rows'][n][k]==a['rows'][n][k] for k in ['command','memory_before','memory_after'])
        prefix_ticks+=3*n*4;parent_B_ticks+=2*B*4;held_ticks+=4
        observed_choices=[];events=[];all_records=[]
        for rep in [1,2]:
            label=arm+str(rep);parent=read(d/(label+'-private.json'));prefix=load_receipt(d/(label+'-nominal-prefix270-private.json'))
            assert prefix['actual_native_ledger']==actual and prefix['rows']==parent['rows'][:n]
            assert prefix['tail']['policy']=='SIGNED_C_NOMINAL' and prefix['tail']['outcome']=='ACTIVE'
            source=read(d/(label+'-prefix-source-private.json'));assert source['prefix450_exact']
            if arm=='nominal':assert source['initial13']['certified_prefix_actions']==13 and source['finite_continuation']['certified_prefix_actions']==n
            records=read(d/(label+'-B-decisions-private.json'));assert len(records)==B
            for i,record in enumerate(records,1):
                query_count+=1;query=load_receipt(d/(label+'_B'+str(i)+'-query-root-private.json'));selection=load_receipt(d/(label+'_B'+str(i)+'-selection-before-parent-private.json'))
                assert query['immutable_native_ledger']==actual
                full=ForecastLedger(**query['full_parent_ledger']);assert full.actual_root_digest==data['ledger'].digest()
                assert asdict(model_ledger_view(full))==query['context']['ledger'] and query['context_digest']==record['context_digest']
                assert not query['actual_execution_allowed'] and not query['actual_DONE_allowed']
                assert selection['record']['selected_recipe']==record['selected_recipe'] and selection['record']['alternatives']==record['alternatives']
                assert record['own_parent_verification']['physical']['passed'] and not record['own_parent_verification']['physical']['wheel']['clipped_flag_mismatches']
                assert record['own_parent_verification']['ledger']['goal_hit_exact'] and record['own_parent_verification']['ledger']['clock_age_deadline_DONE_exact']
                selected=selection['selected_first'];own=parent['rows'][n+i-1]
                assert all(selected[k]==own[k] for k in ['command','memory_before','memory_after'])
                alts=record['alternatives'];assert alts[0]['recipe']=='nominal'
                if len(alts)==2:
                    assert not alts[0]['valid'] and alts[0]['kind'] in ['REGISTERED_PHYSICAL_INELIGIBILITY','REGISTERED_PROGRESS_INELIGIBILITY'] and alts[1]['recipe']=='neutralbrake' and alts[1]['valid']
                else:assert alts[0]['valid'] and record['selected_recipe']=='nominal'
                for alternative in alts:
                    recipe=alternative['recipe'];one=read(d/(label+'_B'+str(i)+'_'+recipe+'1-private.json'));two=read(d/(label+'_B'+str(i)+'_'+recipe+'2-private.json'))
                    assert one['rows']==two['rows'] and one['final_state']==two['final_state'] and one['model_ledger']==two['model_ledger']
                    shadow_count+=2;expected_rejected+=2*int(not alternative['valid'])
                if rep==1:
                    observed_choices.append(record['selected_recipe'])
                    if record['selected_recipe']=='neutralbrake':events.append(dict(decision=i,kind='NEUTRAL_INTERVENTION',rejected_nominal=alts[0],selected_neutral=alts[1],first_selected_parent_physical_passed=True))
                all_records.append(record)
            assert not parent['model_ledger']['done'] and not parent['model_ledger']['deadline_missed'] and all(not row['safety'] for row in parent['rows'])
        assert observed_choices==branch['choices']
        held_proof=read(d/(arm+'-held-first-private.json'));assert held_proof['passed'] and held_proof['RNG_unchanged'] and held_proof['context_digest']==held_proof['required_first_context_digest']
        nominal_prefix_rng=load_receipt(d/(arm+'_held-nominal-prefix270-private.json'))['actual_native_ledger'];assert nominal_prefix_rng==actual
        details[arm]=dict(status=branch['status'],prefix_replay_exact=True,prefix_actions=n,B_actions_each=B,neutral_events=events,first_neutral=branch['first_neutral_decision'],recovery=branch['recovery_decision'],required_repeat_exact=True,held_first_current_context_exact=True,held_first_passed=True,selected_parent_unsafe_rows=0,nominal_only_ranking_blocked=True,native_ledger_unmodified=True,all_current_views_bound=True,missing_recovery_is_censor_not_infeasibility=branch['status']=='CENSORED_NO_RECOVERY14')
        private[arm]=dict(end_model_state=a['final_state'],end_forecast=a['model_ledger'],B_reports=all_records)
    assert query_count==56 and shadow_count==120 and expected_rejected==8
    assert prefix_ticks==840 and parent_B_ticks==224 and held_ticks==8
    shadow_ticks=budget['ticks']-prefix_ticks-parent_B_ticks-held_ticks;assert shadow_ticks==6240
    save(d/'end-models-and-reports-private.json',private)
    checks=dict(source_and_protected_preserved=True,observer_posts=7312,observer_streams=126,current_query_roots=query_count,shadow_worlds=shadow_count,expected_nonselected_rejected_worlds=expected_rejected,selected_parent_failures=0,actual_calls_resets=0,model_prefix_and_B_same_live_parent=True,nominal_completion_reuse_blocked=True,candidate_B15_not_executed=True,saved_CPU_s=time.process_time()-cpu)
    save(d/'closure-checks-private.json',checks)
    public={k:v for k,v in result.items() if k not in ['budget','plan_sha256']}
    public.update(details=details,verification=checks,cost=dict(model_ticks=7312,model_worlds=126,model_CPU_s=budget['CPU_s'],model_wall_s=budget['execution_wall_s'],prefix_replay_ticks=prefix_ticks,parent_B_ticks=parent_B_ticks,held_first_ticks=held_ticks,shadow_ticks=shadow_ticks,static_attempts=[read(d/'pre-model-v1/static-result.json'),read(d/'static-result.json')],saved_audit_CPU_s=checks['saved_CPU_s'],full_project_overhead_measured=False,old_model_cost_recharged=False),candidate_recovery_beyond14_unknown=True,whole_policy_or_native_lap_qualified=False,new_common_exit_gain=None,single_hypothesis_scope=True,deadline_utc=p['deadline_utc'])
    save(g/'retry/composition451_result.json',public)
    print(json.dumps(dict(status=result['status'],details=details,verification=checks,cost=public['cost'])))

if __name__=='__main__':run(Path(__import__('sys').argv[1]))
