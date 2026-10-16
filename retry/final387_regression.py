"""Synthetic final/provisional report, CLI and query consistency fixtures."""
import io,json,sys
from pathlib import Path
from unittest.mock import patch
from retry import final385_adapter as a
from retry.final385_dryrun import Synthetic


def run(root):
    root=Path(root);root.mkdir(mode=0o700);checks=[]
    def check(name,value):
        assert value,name
        checks.append(name)
    prior=dict(actual_cumulative_wrapper_actions=10,research_remaining=20,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=84030)
    def fixture(name):
        d=root/name;d.mkdir();bp=d/'prior.json';a.durable_save(bp,prior,exclusive=True)
        ledger=d/'experiment-cost-lines.jsonl';ledger.touch(mode=0o600)
        q=d/'protected-query-ledger-v1.json'
        a.durable_save(q,dict(SEALED=dict(episodes_used=0,future_episode_queries_this_phase_max=16,status='opened_once_no_retry',claims=[])),exclusive=True)
        auth=dict(experiment_cost_ledger_sha256=a.sha(ledger),budget_sha256=a.sha(bp))
        out=d/'evaluation';result=a.run_batch(out,16,2,lambda i:Synthetic(),on_claim=lambda i:a.claim_query(q,i))
        check(name+' initial report is explicitly provisional and never successful',result['summary_phase']=='PROVISIONAL_PRE_SETTLEMENT' and result['execution_qualification_passed'] and not result['batch_qualification_passed'])
        check(name+' no final aliases or commit marker before settlement',not(out/'summary-private.json').exists() and not(out/'summary-public.json').exists() and not(out/'summary-finalized.json').exists())
        return d,bp,ledger,q,auth,out
    def aligned(name,d,q,out,result,passed,accounting):
        private=a.read(out/'summary-private.json');public=a.read(out/'summary-public.json');pool=a.read(q)['SEALED']
        text=io.StringIO();code=a.emit_cli_summary(result,text)
        check(name+' final private/public/return/CLI agree',private==result and public==a.public_summary(result) and json.loads(text.getvalue())==public and code==(0 if passed else 2))
        check(name+' final accounting, qualification and query agree',public['summary_phase']=='FINAL_POST_SETTLEMENT' and public['batch_qualification_passed']==passed and public['accounting_status']==accounting and pool['future_episode_queries_this_phase_max']==0 and pool['status']==('closed_completed' if passed else 'closed_aborted_no_retry'))
        check(name+' published pointer verifies files and query snapshot',a.read_final_summary(out,q)==public and 'case_rows' not in public)
        check(name+' provisional history remains unchanged',a.read(out/'summary-provisional-public.json')['summary_phase']=='PROVISIONAL_PRE_SETTLEMENT' and not a.read(out/'summary-provisional-public.json')['batch_qualification_passed'])
    d,bp,ledger,q,auth,out=fixture('normal')
    r=a.settle_live(d,out,prior,bp,auth);aligned('normal',d,q,out,r,True,'CONFIRMED')
    d,bp,ledger,q,auth,out=fixture('drift')
    ledger.write_text(json.dumps(dict(stage='concurrent',new_wrapper_actions=5))+'\n')
    r=a.settle_live(d,out,prior,bp,auth);aligned('drift',d,q,out,r,False,'RECONCILIATION_REQUIRED')
    check('reconciliation final failure has no stale whole-budget publication',not(d/'project-effective-budget-final385.json').exists() and not(out/'project-budget-after.json').exists())
    d,bp,ledger,q,auth,out=fixture('settlement-error')
    with patch.object(a,'finalize_accounting',side_effect=RuntimeError('synthetic private detail')):
        try:a.settle_live(d,out,prior,bp,auth)
        except RuntimeError:pass
        else:raise AssertionError('Settlement error swallowed')
    r=a.read(out/'summary-private.json');aligned('settlement-error',d,q,out,r,False,'SETTLEMENT_ERROR_RECONCILIATION_REQUIRED')
    # Publication is fail-closed if a file/query changes after the final commit.
    (out/'summary-public.json').write_text('{}\n')
    try:a.read_final_summary(out,q)
    except RuntimeError:checks.append('tampered final alias cannot be consumed as success')
    else:raise AssertionError('Tampered alias accepted')
    check('report fixtures import no policy or simulator',not any(n.split('.')[0] in {'numpy','cv2','gymnasium','Box2D','core','env_wrapper','agent'} for n in sys.modules))
    result=dict(passed=True,regression_assertions=len(checks),checks=checks,real_actor_calls=0,real_environment_creation=0,real_native_actions=0,SEALED_reads=0,synthetic_only=True)
    a.durable_save(root/'verification.json',result,exclusive=True);print(json.dumps(result),flush=True);return result


if __name__=='__main__':run(Path(sys.argv[1]).resolve())
