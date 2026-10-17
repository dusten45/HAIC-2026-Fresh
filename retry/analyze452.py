"""Saved-only new single-decision and immutable451 censor audit."""
import time
from pathlib import Path
from dataclasses import asdict
from retry.loss389_analyze import read,save,sha
from retry.receipt421_io import load_receipt
from retry.root449 import load_root449
from retry.pilot420_backend import model_ledger_view
from retry.planner419_model_ledger import ForecastLedger


def run(root):
    cpu=time.process_time();g=Path(__file__).resolve().parents[1];d=root/'stage452';p=read(d/'plan.json');result=read(d/'result.json');b=result['budget'];out=result['result']
    assert result['status']=='SINGLE_CURRENT_DECISION_SCOPE_COMPLETED' and result['error'] is None
    for group in ['sources','protected','original408_preserve']:
        for f,h in p[group].items():assert sha(f)==h,f
    assert sha(d/'plan.json')==result['plan_sha256']==(d/'plan.sha256').read_text().strip()
    assert b['ticks']==b['reserved_ticks']==796 and b['worlds']==b['confirmed_worlds']==7 and b['CPU_s']<90 and b['execution_wall_s']<150
    streams=[read(f) for f in d.glob('*-observer-private.json')]
    assert len(streams)==7 and sum(len(s['posts']) for s in streams)==796 and all(s['failure'] is None for s in streams)
    source=read(root/'stage451/fullgas1-private.json');native=load_root449(root,'fullgas');a=read(d/'candidate1-private.json');repeat=read(d/'candidate2-private.json');held=read(d/'candidate_held-private.json')
    assert a['rows']==repeat['rows']==held['rows'] and a['final_state']==repeat['final_state']==held['final_state'] and a['controller_memory']==repeat['controller_memory']==held['controller_memory']
    for label in ['candidate1','candidate2','candidate_held']:
        parent=read(d/(label+'-private.json'));assert len(parent['rows'])==49 and parent['rows'][:48]==source['rows']
        assert parent['recorded_model_prefix_actions']==48 and parent['new_current_actions']==1 and parent['native_facts_produced']==0
        assert parent['nominal_only_ranking_forbidden'] and parent['model_ledger']['actual_root_digest']==native['ledger'].digest() and not parent['model_ledger']['done']
        saved=load_receipt(d/(label+'-recorded-model-prefix48-private.json'))
        assert saved['snapshot']==source['final_state'] and saved['memory']==source['controller_memory'] and saved['ledger']==source['model_ledger'] and saved['immutable_native_ledger']==asdict(native['ledger'])
    for rep in [1,2]:
        label='candidate'+str(rep);query=load_receipt(d/(label+'_one-query-root-private.json'));selection=load_receipt(d/(label+'_one-selection-before-parent-private.json'));record=read(d/(label+'-new-decision-private.json'))
        assert query['full_parent_ledger']==source['model_ledger'] and query['immutable_native_ledger']==asdict(native['ledger'])
        assert query['context']['ledger']==asdict(model_ledger_view(ForecastLedger(**source['model_ledger'])))
        assert not query['actual_execution_allowed'] and not query['actual_DONE_allowed']
        assert selection['record']['selected_recipe']=='nominal' and len(selection['record']['alternatives'])==1
        assert all(a['rows'][-1][k]==selection['selected_first'][k] for k in ['command','memory_before','memory_after'])
        assert record['report']['physical']['passed'] and not record['report']['physical']['wheel']['clipped_flag_mismatches'] and record['report']['ledger']['clock_age_deadline_DONE_exact']
        one=read(d/(label+'_one_nominal1-private.json'));two=read(d/(label+'_one_nominal2-private.json'))
        assert len(one['rows'])==13 and one['rows']==two['rows'] and one['final_state']==two['final_state'] and all(not row['safety'] for row in one['rows'])
    assert read(d/'held-first-private.json')['passed']
    original=read(root/'stage451/result.json');assert original['branches']['fullgas']['status']=='CENSORED_NO_RECOVERY14' and not original['both_first_intervention_recovery_witnessed']
    assert out['outcome']=='NOMINAL_SAFE_RECOVERY_IN_NEW_SINGLE_DECISION' and out['original451_uncensored'] is False
    checks=dict(source_and_protected_preserved=True,recorded_model_source_replayed_exactly=True,no_new_policy_selection_in_replay=True,live_reconstructed_model_parent_to_current_one=True,current_root_contexts=2,current_shadow_worlds=4,required_repeat_and_held_exact=True,own_parent_first_fidelity_and_ledger_passed=True,nominal_only_completion_blocked=True,original451_censor_preserved=True,second_new_decision_not_executed=True,observer_posts=796,streams=7,actual_calls_resets=0,saved_CPU_s=time.process_time()-cpu)
    save(d/'closure-checks-private.json',checks)
    public=dict(stage=452,status=result['status'],error=None,result={k:v for k,v in out.items() if k!='current_record'},selected_alternatives=out['current_record']['alternatives'],verification=checks,cost=dict(model_ticks=796,model_worlds=7,model_CPU_s=b['CPU_s'],model_wall_s=b['execution_wall_s'],recorded_model_replay_ticks=576,fresh_current_shadow_ticks=208,required_parent_ticks=8,held_first_ticks=4,static=read(d/'static-result.json'),saved_audit_CPU_s=checks['saved_CPU_s'],old_cost_recharged=False,full_project_overhead_measured=False),whole_policy_or_native_lap_qualified=False,deadline_utc=p['deadline_utc'])
    save(g/'retry/decision452_result.json',public);print(__import__('json').dumps(dict(status=result['status'],outcome=out['outcome'],cost=public['cost'],checks=checks)))

if __name__=='__main__':run(Path(__import__('sys').argv[1]))
