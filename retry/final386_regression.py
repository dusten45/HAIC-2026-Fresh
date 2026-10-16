"""Synthetic regression fixtures for five pre-opening adapter defects."""
import copy
import hashlib
import json
from pathlib import Path
import sys
from retry import final385_adapter as a
from retry.final385_dryrun import Synthetic


def run(root):
    root=Path(root);root.mkdir(mode=0o700)
    checks=[]
    def check(name, value):
        assert value,name
        checks.append(name)
    def rejected(name, operation):
        try:operation()
        except RuntimeError:checks.append(name)
        else:raise AssertionError(name)
    #1: immutable schema/digest must reject omissions before installed-file iteration.
    dep=root/'dep.txt';dep.write_text('synthetic dependency')
    files={'dep.txt':a.sha(dep)}
    canonical=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    expected={'synthetic':dict(version='1.0',file_count=1,content_manifest_sha256=canonical)}
    snapshot={'synthetic':dict(version='1.0',file_count=1,content_manifest_sha256=canonical,files_sha256=files)}
    calls=[]
    class Dist:
        version='1.0'
        def locate_file(self, rel):return root/rel
    def resolver(name):calls.append(name);return Dist()
    rejected('empty dependency map denied',lambda:a.verify_dependencies({},expected,resolver))
    bad=copy.deepcopy(snapshot);bad['synthetic']['files_sha256']={}
    rejected('dependency file omission denied',lambda:a.verify_dependencies(bad,expected,resolver))
    bad=copy.deepcopy(snapshot);bad['synthetic']['version']='2.0'
    rejected('dependency snapshot version mismatch denied',lambda:a.verify_dependencies(bad,expected,resolver))
    bad=copy.deepcopy(snapshot);bad['synthetic']['files_sha256']={'other.txt':a.sha(dep)}
    rejected('same-size dependency map substitution denied',lambda:a.verify_dependencies(bad,expected,resolver))
    check('all dependency map gates precede resolver access',calls==[])
    a.verify_dependencies(snapshot,expected,resolver)
    check('valid bound dependency map verifies actual file',calls==['synthetic'])
    dep.write_text('mutated installed file')
    rejected('installed dependency mutation denied',lambda:a.verify_dependencies(snapshot,expected,resolver))
    #2: final cap commit is a definitive max_steps DNF even without case_terminal.
    def cap_journal(name,finish=None,pending=False):
        p=root/name;j=a.Journal(p)
        j.event('batch_prepared',count=16,per_case_cap=2)
        j.event('case_claimed',case_index=0)
        j.event('reset_committed',case_index=0,metadata=dict(start_time_s=1.02))
        for step in [1,2]:
            j.event('step_intent',case_index=0,step=step)
            if not(pending and step==2):
                j.event('step_committed',case_index=0,step=step,metrics=dict(finish_time_s=finish if step==2 else None,terminated=False,truncated=False))
        j.close();return a.summarize(p,16)
    r=cap_journal('cap.jsonl')
    check('cap commit without terminal restores normal max_steps DNF',r['DNF']==1 and r['case_rows'][0]['reason']=='max_steps' and r['native_confirmed']==2)
    r=cap_journal('cap-finish.jsonl',finish=1.1)
    check('finish dominates recovered cap retirement',r['completed']==1 and r['case_rows'][0]['lap_ms']==80)
    r=cap_journal('cap-pending.jsonl',pending=True)
    check('unconfirmed cap intent remains censored',r['DNF']==0 and r['native_unresolved']==1 and r['censored']==1)
    #3: mock clock expires inside act, before any step intent.
    expired=[False];steps=[0]
    class SlowAct(Synthetic):
        def act(self,obs):expired[0]=True;return super().act(obs)
        def step(self,action):steps[0]+=1;return super().step(action)
    def clock():
        if expired[0]:raise a.Deadline('Synthetic act crossed approval end')
    r=a.run_batch(root/'late-act',16,2,lambda i:SlowAct(),check_time=clock)
    check('act crossing deadline prevents every env step',steps==[0] and r['native_upper_bound']==0 and r['case_rows'][0]['status']=='CENSORED_DEADLINE')
    check('actor response and measured cost survive post-act expiry',r['actor_act_committed']==1 and r['max_recorded_act_IPC_ms']==2)
    #4: independent cost only if the under-lock base ledger/prior no longer match.
    prior=dict(actual_cumulative_wrapper_actions=10,research_remaining=20,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=84030)
    def account_root(name):
        p=root/name;p.mkdir();bp=p/'prior.json';a.durable_save(bp,prior,exclusive=True)
        ledger=p/'experiment-cost-lines.jsonl';ledger.touch(mode=0o600)
        return p,bp,ledger
    out=root/'confirmed';a.run_batch(out,16,2,lambda i:Synthetic())
    ar,bp,ledger=account_root('drift-account')
    baseline=a.sha(ledger);bh=a.sha(bp)
    ledger.write_text(json.dumps(dict(stage='concurrent',new_wrapper_actions=5))+'\n')
    changed=ledger.read_bytes()
    r=a.finalize_accounting(ar,out,prior,bp,baseline,bh)
    check('concurrent ledger drift yields independent reconciliation only',r['accounting_status']=='RECONCILIATION_REQUIRED' and not(ar/'project-effective-budget-final385.json').exists() and not(out/'project-budget-after.json').exists())
    check('drift never appends to or overwrites concurrent ledger',ledger.read_bytes()==changed and a.read(out/'cost-independent.json')['new_wrapper_actions']==16)
    ar,bp,ledger=account_root('budget-drift')
    baseline=a.sha(ledger);bh=a.sha(bp);mutated=dict(prior);mutated['research_remaining']=19;a.durable_save(bp,mutated)
    r=a.finalize_accounting(ar,out,prior,bp,baseline,bh)
    check('changed prior budget never publishes stale balances',r['accounting_status']=='RECONCILIATION_REQUIRED' and not(ar/'project-effective-budget-final385.json').exists())
    # The live settlement closes queries even when accounting refuses publication.
    ar2,bp2,ledger2=account_root('settlement-drift')
    baseline2=a.sha(ledger2);bh2=a.sha(bp2)
    a.durable_save(ar2/'protected-query-ledger-v1.json',dict(SEALED=dict(episodes_used=16,future_episode_queries_this_phase_max=16,status='opened_once_no_retry',claims=[dict(case_index=i) for i in range(16)])),exclusive=True)
    ledger2.write_text(json.dumps(dict(stage='concurrent',new_wrapper_actions=3))+'\n')
    r=a.settle_live(ar2,out,prior,bp2,dict(experiment_cost_ledger_sha256=baseline2,budget_sha256=bh2))
    check('drift settlement closes query and fails qualification without stale budget',a.read(ar2/'protected-query-ledger-v1.json')['SEALED']['future_episode_queries_this_phase_max']==0 and not r['batch_qualification_passed'] and not(ar2/'project-effective-budget-final385.json').exists())
    #5: real orchestration helper used by run_live must settle before propagating.
    for name,signal in [('keyboard',KeyboardInterrupt),('system-exit',SystemExit)]:
        ar,bp,ledger=account_root(name)
        q=ar/'protected-query-ledger-v1.json'
        a.durable_save(q,dict(SEALED=dict(episodes_used=0,future_episode_queries_this_phase_max=16,status='opened_once_no_retry',claims=[])),exclusive=True)
        authority=dict(experiment_cost_ledger_sha256=a.sha(ledger),budget_sha256=a.sha(bp))
        output=ar/'evaluation'
        class Interrupted(Synthetic):
            def act(self,obs):
                if signal is KeyboardInterrupt:raise KeyboardInterrupt()
                return super().act(obs)
            def step(self,action):raise SystemExit(7)
        try:
            a.run_with_settlement(lambda:a.run_batch(output,16,2,lambda i:Interrupted(),on_claim=lambda i:a.claim_query(q,i)),
                lambda:a.settle_live(ar,output,prior,bp,authority))
        except signal as exc:
            if signal is SystemExit:assert exc.code==7
        else:raise AssertionError('Catchable exit was swallowed')
        closed=a.read(q)['SEALED'];budget=a.read(ar/'project-effective-budget-final385.json')
        check(name+' settles accounting and closes query before propagation',closed['episodes_used']==1 and closed['future_episode_queries_this_phase_max']==0 and (output/'cost.json').exists())
        check(name+' preserves confirmed or unresolved native cost without replay',budget['actual_cumulative_wrapper_actions']==10 and budget['final_reserve_encumbered_unresolved']==(1 if signal is SystemExit else 0))
    check('regression fixtures import no policy/environment',not any(n.split('.')[0] in {'numpy','cv2','gymnasium','Box2D','core','env_wrapper','agent'} for n in sys.modules))
    result=dict(passed=True,regression_assertions=len(checks),checks=checks,real_actor_calls=0,real_environment_creation=0,real_native_actions=0,SEALED_reads=0,synthetic_only=True)
    a.durable_save(root/'verification.json',result,exclusive=True)
    print(json.dumps(result),flush=True)
    return result


if __name__=='__main__':run(Path(sys.argv[1]).resolve())
