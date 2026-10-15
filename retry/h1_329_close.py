"""Close fixed six fold evaluation; retain296 and all protected splits."""
import argparse
import datetime
import json
import time
from pathlib import Path

import numpy as np

from retry.h1_329_stage import verify
from retry.path271_run import read,save,sha


def close(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage329';p=verify(D);o=read(D/'native-outcome-private.json');rr=o['results'];b=read(D/'native-budget.json')
    assert not (D/'cost.json').exists();assert len(rr)==6 and not o['unobserved'] and o['shortfall'] is None
    assert all(not r['technical_error'] and not r['censored'] and r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent'] for r in rr)
    assert sum(r['native_actions'] for r in rr)==b['actions']<=b['cap']==1874
    assert sha(G/'retry/h1_329_native.py')==read(D/'native-opening.json')['script_sha256']
    for q,h in read(D/'build-receipt.json')['public_code_hashes'].items():assert sha(q)==h,q
    distribution={};details=[];all_actions=0
    for r in rr:
        rows=[json.loads(s) for s in (D/'evaluation'/r['road']/'trace-private.jsonl').read_text().splitlines()]
        cache=np.load(D/'evaluation'/r['road']/'raw-pixels-actions-private.npz')
        assert len(cache['observations'])==len(rows)+1==r['native_actions']+1
        assert np.array_equal(cache['observations'][1:,:3],cache['observations'][:-1,1:])
        assert np.array_equal(cache['actions'],np.array([row['action'] for row in rows],np.float32))
        count=dict(road=r['road'],actions=len(rows),changed=0,acceleration=0,deceleration=0,fallback=0,choices={},first_contact=None)
        for row in rows:
            audit=row['audit'];action=np.array(row['action'],np.float32);assert action[0]==np.float32(audit['base'][0])==np.float32(row['memory'])
            assert audit['nominal_memory_preserved'] and audit['action']==row['action']
            if audit['changed']:
                assert audit['selected_supported'] and audit['chosen_error']<audit['baseline_error'];count['changed']+=1
                delta=audit['chosen_next_speed']-audit['baseline_next_speed'];gap=audit['q']-audit['baseline_next_speed'];assert delta*gap>0
                count['acceleration']+=int(delta>0);count['deceleration']+=int(delta<0)
            else:assert audit['base']==row['action'];count['fallback']+=1
            name=audit['selected_name'];count['choices'][name]=count['choices'].get(name,0)+1;distribution[name]=distribution.get(name,0)+1
            if row['collision'] and count['first_contact'] is None:count['first_contact']=row['step']
        details.append(count);all_actions+=len(rows)
    baseline=[r for r in p['baseline296']['results'] if r['road'] in p['roads']];base={r['road']:r for r in baseline};new={r['road']:r for r in rr}
    common=[r for r in p['roads'] if base[r]['completed'] and new[r]['completed']]
    added=[r for r in p['roads'] if new[r]['completed'] and not base[r]['completed']];lost=[r for r in p['roads'] if base[r]['completed'] and not new[r]['completed']]
    paired=dict(candidate_completions=sum(r['completed'] for r in rr),baseline_completions=sum(r['completed'] for r in baseline),additional_completions=added,lost_completions=lost,
                common_completions=len(common),common_completed_mean_time_delta_ms=float(np.mean([new[r]['lap_ms']-base[r]['lap_ms'] for r in common])),
                candidate_damage_sum=sum(r['damage'] for r in rr),baseline_damage_sum=sum(r['damage'] for r in baseline),
                count_first_positive=bool(sum(r['completed'] for r in rr)>sum(r['completed'] for r in baseline)))
    prior=R/'project-effective-budget-v334.json';v=read(prior);assert v['research_remaining']==1874
    cost=dict(stage=329,new_wrapper_actions=all_actions,native_cap=1874,new_official_runs=6,cached_baseline_runs_reused=6,
              raw_step_ticks=sum(r['raw_step_ticks'] for r in rr),raw_reset_ticks=sum(r['raw_reset_ticks'] for r in rr),
              native_wall_s=o['wall_s'],runner_CPU_s=sum(r['runner_CPU_s'] for r in rr),actor_CPU_s=sum(r['actor_CPU_s'] for r in rr),
              cache_wall_s=read(D/'cache-receipt.json')['wall_s'],new_fits=0,new_PPO=0,new_source_physics_ticks=0,new_paid_resources=0,
              additional_research=1874,actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions']+all_actions,research_remaining=v['research_remaining']-all_actions,
              final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=v['B_operating_cap'])
    save(D/'cost.json',cost);v.update(version=335,prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),
                                    actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage329_new_wrapper_actions=all_actions)
    assert not (R/'project-effective-budget-v335.json').exists();save(R/'project-effective-budget-v335.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==329 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    safe=lambda r:{k:r.get(k) for k in ['road','completed','actual_DNF','censored','technical_error','lap_ms','damage','native_actions','retire_reason']}
    public=dict(stage=329,deadline_utc=p['deadline_utc'],novelty=p['novelty'],target=p['target'],inputs=p['inputs'],candidates=p['candidates'],support=p['support'],choice=p['choice'],model_rule=p['model_rule'],
                cache_gate=p['cache_gate'],cache=read(D/'cache-receipt.json'),independent_cache_verification=read(D/'independent-cache-verification.json'),
                results=[safe(r) for r in rr],baseline296=[safe(r) for r in baseline],paired=paired,signals=details,native_choices=distribution,cost=cost,
                technical_errors=0,censored=0,unobserved=0,champion296_maintained=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,
                decision='Positive count-first knownTRAINcrossfold diagnostic:6/6vs5/6, common5slower. Sixdifferentfoldartifacts arenotonesingledeployablepolicy; retain296,nofurtherstudyhere.',
                limitations=['KnownsixTRAIN after extensivepastanalysis,base296alreadytrainedonTRAIN;predictormodelroad-excludedisnotfreshindependentgeneralization.',
                             'H1currentqtracking isnotdirectlap-timeobjective;heavybrake-upbias andslowercommontimesretained.',
                             'Rectangularmarginalsupport gate isnotjointcoverage, counterfactualcalibration or safetyguarantee.',
                             'Sixfoldartifactsuseconstantmodelparameters,noroadIDbranchinsideactor;notonefullfit/deployablepolicy.',
                             'Onefullepisodeperfold,notfull18qualificationorofficialserververification;noDEV,HOLDOUT,SEALEDor promotion.'])
    save(D/'summary-private.json',public);save(G/'retry/h1_329_result.json',public)
    print(json.dumps(dict(paired=paired,cost=cost,signals=details)),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--private-root',type=Path,required=True)
    close(parser.parse_args().private_root.resolve())
