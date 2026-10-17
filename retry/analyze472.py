"""472 saved-only closure; no simulator imports, constructors or steps."""
import json
from pathlib import Path
from retry.loss389_analyze import read,save,sha
from retry.budget472 import close472

def analyze(root):
    root=Path(root);d=root/'stage472';p=read(d/'plan.json');r=read(d/'result.json');b=r['budget'];results=r['actual_results']
    assert len(results)<=1 and r['new_actual_actions']<=195 and r['new_resets']<=1
    assert b['model']['ticks']<=8738 and b['model']['worlds']<=181
    assert r['new_actual_actions']==b['actual']['actions'] and r['new_resets']==b['actual']['resets']
    assert sha(p['budget_before_path'])==p['budget_before_sha256']
    for group in ('protected','original408_preserve'):
        for name,digest in p[group].items():assert sha(name)==digest,name
    native=results[0] if results else None
    closure=close472(p,d,r)
    out=dict(stage=472,status=r['status'],error=r['error'],last_stage=r['last_stage'],plan_sha256=r['plan_sha256'],
             model_ticks=b['model']['ticks'],model_worlds=b['model']['worlds'],whole_CPU_s=b['wholeworker_CPU_s'],whole_wall_s=b['whole_execution_wall_s'],
             native_actions=r['new_actual_actions'],resets=r['new_resets'],native=native,
             research_remaining=26346-r['new_actual_actions'],reserve=84000,reserve_used=0,
             baseline_13_780s='historical reference only; no fresh paired or causal gain claim',
             model470_remaining_finish_bracket_s=[3.62,3.64],model470_is_native_result=False,
             HOLDOUT_SEALED_new_seed_learning_paid=0,protected18_verified=True,no_followup=True,ledger_closure=closure)
    save(d/'saved-closure-private.json',out);return out

if __name__=='__main__':
    import sys
    print(json.dumps(analyze(sys.argv[1])))
