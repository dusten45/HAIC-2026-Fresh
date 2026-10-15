"""Report one actual artifact across all18, original6 and remaining12 separately."""
import argparse
import json
from pathlib import Path

import numpy as np

from retry.h1_330_stage import verify
from retry.path271_run import read,save,sha


def compare(candidate,baseline):
    old={r['road']:r for r in baseline};new={r['road']:r for r in candidate}
    common=[r for r in new if new[r]['completed'] and old[r]['completed']]
    nc=sum(r['completed'] for r in candidate);bc=sum(r['completed'] for r in baseline)
    time_delta=float(np.mean([new[r]['lap_ms']-old[r]['lap_ms'] for r in common])) if common else None
    return dict(candidate_completions=nc,baseline_completions=bc,additional_completions=[r for r in new if new[r]['completed'] and not old[r]['completed']],
                lost_completions=[r for r in new if old[r]['completed'] and not new[r]['completed']],common_completions=len(common),common_completed_mean_time_delta_ms=time_delta,
                candidate_damage_sum=sum(r['damage'] for r in candidate),baseline_damage_sum=sum(r['damage'] for r in baseline),
                count_first_improved=bool(nc>bc or (nc==bc and time_delta is not None and time_delta<0)))


def close(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage330';p=verify(D);o=read(D/'native-outcome-private.json');rr=o['results'];b=read(D/'native-budget.json')
    assert not (D/'cost.json').exists();assert len(rr)==18 and not o['unobserved'] and o['shortfall'] is None
    assert all(not r['technical_error'] and not r['censored'] and r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent'] for r in rr)
    cfg=read(D/'artifacts-private.json')['ON'];assert len({r['archive_sha256'] for r in rr})==1 and all(r['archive_sha256']==cfg['archive_sha256'] for r in rr)
    assert sha(G/'retry/h1_330_native.py')==read(D/'native-opening.json')['script_sha256']
    for q,h in read(D/'build-receipt.json')['source_hashes'].items():assert sha(q)==h,q
    signals=[];distribution={};reasons={};support_counts=np.zeros(6,int);forecast_count=0;raw_mean_max=0.
    for result in rr:
        road=result['road'];F=D/'evaluation'/road;rows=[json.loads(s) for s in (F/'trace-private.jsonl').read_text().splitlines()]
        z=np.load(F/'raw-pixels-actions-private.npz');observations=z['observations'];actions=z['actions']
        assert len(rows)==result['native_actions']==len(actions)==len(observations)-1
        assert np.array_equal(observations[1:,:3],observations[:-1,1:]) and np.array_equal(actions,np.array([row['action'] for row in rows],np.float32))
        modelpath=F/'cpu/package/retry/h1_330_model.py';assert sha(modelpath)==cfg['members_sha256']['retry/h1_330_model.py']
        counts=dict(road=road,actions=len(rows),changed=0,acceleration=0,deceleration=0,base_any_support_fallback=0,rejected_alternative_candidates=0,
                    missing_target_fallback=0,baseline_best_or_tie=0,choices={},reasons={},first_contact=None)
        for row in rows:
            a=row['audit'];assert a['model_count']==6 and a['action']==row['action'] and np.float32(a['base'][0])==np.float32(row['action'][0])==np.float32(row['memory'])
            assert a['nominal_memory_preserved'];reason=a['reason'];name=a['selected_name']
            counts['reasons'][reason]=counts['reasons'].get(reason,0)+1;counts['choices'][name]=counts['choices'].get(name,0)+1
            distribution[name]=distribution.get(name,0)+1;reasons[reason]=reasons.get(reason,0)+1
            if a['base_support_by_model'] is not None:support_counts+=~np.array(a['base_support_by_model'],bool)
            counts['base_any_support_fallback']+=int(reason=='base_input_outside_any_support');counts['missing_target_fallback']+=int(reason=='absent_or_invalid_target')
            counts['baseline_best_or_tie']+=int(reason in ['baseline_best','exact_tie'])
            if a['changed']:
                assert a['selected_supported'] and a['chosen_error']<a['baseline_error'];delta=a['chosen_next_speed']-a['baseline_next_speed'];gap=a['q']-a['baseline_next_speed'];assert delta*gap>0
                counts['changed']+=1;counts['acceleration']+=int(delta>0);counts['deceleration']+=int(delta<0)
            else:assert a['action']==a['base']
            for c in a['candidates']:
                assert c['supported']==all(c['support_by_model']) and len(c['support_by_model'])==6
                if c['supported']:
                    assert len(c['model_next_speeds'])==6;difference=abs(float(np.mean(c['model_next_speeds']))-c['next_speed']);assert difference==0.;raw_mean_max=max(raw_mean_max,difference);forecast_count+=6
                else:assert c['model_next_speeds'] is None and c['next_speed'] is None;counts['rejected_alternative_candidates']+=1
            if row['collision'] and counts['first_contact'] is None:counts['first_contact']=row['step']
        signals.append(counts)
    assert sum(r['native_actions'] for r in rr)==b['actions']<=b['cap']
    baseline=p['baseline296']['results'];summaries={}
    for label,roads in [('original6',p['original6']),('remaining12',p['remaining12']),('all18',p['roads'])]:
        summaries[label]=compare([r for r in rr if r['road'] in roads],[r for r in baseline if r['road'] in roads])
    prior=R/'project-effective-budget-v336.json';v=read(prior);assert v['research_remaining']==5568
    cost=dict(stage=330,new_wrapper_actions=b['actions'],native_cap=b['cap'],new_official_runs=18,reused329_runs=0,reused_baseline296_runs=18,
              raw_step_ticks=sum(r['raw_step_ticks'] for r in rr),raw_reset_ticks=sum(r['raw_reset_ticks'] for r in rr),native_wall_s=o['wall_s'],
              runner_CPU_s=sum(r['runner_CPU_s'] for r in rr),actor_CPU_s=sum(r['actor_CPU_s'] for r in rr),cache_wall_s=read(D/'cache-receipt.json')['wall_s'],
              new_fits=0,new_PPO=0,new_source_physics_ticks=0,new_paid_resources=0,additional_research=5551,
              actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions']+b['actions'],research_remaining=v['research_remaining']-b['actions'],
              final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=v['B_operating_cap'])
    save(D/'cost.json',cost);v.update(version=337,prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),
                                    actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage330_new_wrapper_actions=b['actions'])
    assert not (R/'project-effective-budget-v337.json').exists();save(R/'project-effective-budget-v337.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==330 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    safe=lambda r:{k:r.get(k) for k in ['road','completed','actual_DNF','censored','technical_error','lap_ms','damage','native_actions','retire_reason','visited','total_tiles']}
    dnf=[dict(road=r['road'],retire_reason=r['retire_reason'],native_actions=r['native_actions'],visited=r['visited'],total_tiles=r['total_tiles'],progress=r['visited']/r['total_tiles']) for r in rr if r['actual_DNF']]
    public=dict(stage=330,question=p['question'],ensemble=p['ensemble'],support=p['support'],target=p['target'],candidates=p['candidates'],choice=p['choice'],rule=p['rule'],
                cache=read(D/'cache-receipt.json'),independent_cache=read(D/'independent-cache-verification.json'),summaries=summaries,results=[safe(r) for r in rr],
                baseline296=[safe(r) for r in baseline],DNF_progress=dnf,signals=signals,choices=distribution,reasons=reasons,
                support_fallback_by_model=support_counts.tolist(),accepted_original_model_forecasts=forecast_count,raw_m_s_mean_max_error=raw_mean_max,
                one_identical_artifact_used18=True,model_bank_module_identical_all18=True,model_count=6,all_outputs_equal_weight=True,reused329_results=0,
                cost=cost,technical_errors=0,censored=0,unobserved=0,champion296_maintained=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,
                interpretation='Onefixedartifactactual18TRAINdiagnostic; noindependentgeneralization orpromotion. Partialgroupgains cannotreplaceall18regression.',
                next_distinguishing_experiment='Proposedonly,notrun: N2own330prefix64, thenmatchedtwoarms330pedalselectionversussamecall296pedalsforactions65-72,ownresets/prefix/pixels/policystateexact,2x72=144native. First330contact68andactualcrash72;observecontactpersistence. Separatelast8H1choicesfromalreadychangedprefix;bothcrashwouldnotproveunavoidability. Postselecteddiagnostic,noH1horizon/fit/thresholdchange orfull-lapclaim.',
                limitations=['KnownTRAIN after329selection, modelbanktrainedon6knownroads,notfreshvalidation.',
                             'Ensemble andsupportintersection changedtogether vs329; noisolated causal attribution to eitherfactor.',
                             'Marginalintersection notjointconditionalcoverage or safetyguarantee; H1q objective differsfromfull-lap speed.',
                             'Singleactualepisodeperroad andonefrozenartifact; no newDEV/HOLDOUT/SEALED orchampionchange.'])
    save(D/'summary-private.json',public);save(G/'retry/h1_330_result.json',public)
    print(json.dumps(dict(summaries=summaries,DNF=dnf,cost=cost,choices=distribution,reasons=reasons)),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--private-root',type=Path,required=True)
    close(parser.parse_args().private_root.resolve())
