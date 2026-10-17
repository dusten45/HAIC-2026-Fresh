"""Saved-only445 lineage/cost audit; no simulation or controller calls."""
import json
import time
from pathlib import Path
from retry.planner419 import GoalLedger
from retry.audit439 import root_ledger
from retry.receipt421_io import load_receipt
from retry.loss389_analyze import read,sha,save


def run(root):
    cpu,wall=time.process_time(),time.perf_counter()
    g=Path(__file__).resolve().parents[1];d=root/'stage445'
    p,result=read(d/'plan.json'),read(d/'result.json')
    assert result['status']=='H2_LOCAL_REPRESENTATION_COUNTEREXAMPLE'
    for group in [p['sources'],p['protected']]:
        for path,digest in group.items():assert sha(path)==digest,path
    assert result['plan_sha256']==sha(d/'plan.json')
    b=result['budget'];assert b['ticks']==b['reserved_ticks']==3460
    assert b['worlds']==b['confirmed_worlds']==67
    assert b['CPU_s']<240 and b['execution_wall_s']<480
    streams=list(d.glob('*-observer-private.json'));finals=list(d.glob('*-observer-final-private.json'))
    assert len(streams)==len(finals)==67
    assert sum(len(read(x)['posts']) for x in streams)==3460
    assert all(read(x)['failure'] is None for x in streams)
    actual_rows=[json.loads(s) for s in (root/'stage442/actual_C0/trace-private.jsonl').read_text().splitlines()]
    root_digest=root_ledger(actual_rows[89]).digest()
    contexts=list(d.glob('B*_decision*-query-root-private.json'))
    assert len(contexts)==28
    view_digests=set();shadow_count=0
    for path in contexts:
        packet=load_receipt(path);ctx=packet['context'];label=path.name.removesuffix('-query-root-private.json')
        assert packet['value_view_only'] and not packet['actual_execution_allowed'] and not packet['actual_DONE_allowed']
        assert packet['actual_root_digest']==root_digest
        view=GoalLedger(**ctx['ledger']);stamp=view.digest();view_digests.add(stamp)
        for child in d.glob(label+'_*[12]-private.json'):
            x=read(child)
            assert x['model_ledger']['actual_root_digest']==stamp
            assert all(row['actual_root_ledger_digest']==stamp for row in x['rows'])
            shadow_count+=1
    assert shadow_count==60
    B=[]
    for label in ['B1','B2']:
        x=read(d/(label+'-private.json'))
        assert len(x['rows'])==14 and x['status']=='ACTIVE'
        assert not any(row['safety'] for row in x['rows'])
        assert not x['model_ledger']['done'] and not x['model_ledger']['deadline_missed']
        assert x['model_ledger']['actual_root_digest']==root_digest
        B.append(x)
    assert B[0]['rows']==B[1]['rows'] and B[0]['final_state']==B[1]['final_state']
    predicate=[read(d/f'predicate_nominal{i}-private.json') for i in [1,2]]
    assert predicate[0]['rows']==predicate[1]['rows']
    assert not any(row['safety'] for row in predicate[0]['rows'][:13])
    assert predicate[0]['rows'][13]['safety']==['path_error_over3m']
    checks=dict(source_hashes_and_protected_preserved=True,model_raw_posts=3460,
                model_observer_streams=67,final_observer_receipts=67,query_roots=28,
                shadow_current_value_bindings_verified=shadow_count,distinct_current_value_digests=len(view_digests),
                original_actual_root_digest_unchanged=True,B_parent_steps=28,
                B14_repeats_rows_and_final_state_exact=True,
                actual_DONE_authorized=False,new_H1_simulation=0,
                saved_CPU_s=time.process_time()-cpu,saved_wall_s=time.perf_counter()-wall)
    save(d/'closure-checks-private.json',checks)
    cost=dict(stage=445,model_ticks=3460,model_worlds=67,
              qualification_ticks=116,nominal_predicate_ticks=112,B_parent_ticks=112,B_shadow_ticks=3120,
              model_CPU_s=b['CPU_s'],model_wall_s=b['execution_wall_s'],
              static_attempts=[read(d/'pre-model-v1/static-result.json'),read(d/'static-result.json')],
              saved_audit_CPU_s=checks['saved_CPU_s'],saved_audit_wall_s=checks['saved_wall_s'],
              whole_preparation_report_Git_and_import_overhead_fully_measured=False,
              new_actual_actions_resets_learning_H1_SEALED_reserve_paid=0,
              research_remaining=27516,reserve=84000,reserve_used=0)
    save(d/'cost-private.json',cost)
    public={k:v for k,v in result.items() if k not in ['qualification','budget']}
    public.update(cost=cost,verification=checks,
                  transition14_path_error_m=predicate[0]['rows'][13]['path_error_m'],
                  correction='Model parent current GoalLedger value view via capture_context; original actual root bound separately, no native capability or ForecastLedger.digest added.',
                  original444_failure_unchanged=True,H1_extension_not_executed=True,
                  deadline_utc='2026-10-20T10:01:55Z')
    (g/'retry/experiment445_result.json').write_text(json.dumps(public,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],ticks=3460,worlds=67,B_choices=result['B_choices'],verification=checks)))


if __name__=='__main__':
    import sys
    run(Path(sys.argv[1]))
