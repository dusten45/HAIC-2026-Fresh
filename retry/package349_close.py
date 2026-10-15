"""Saved-evidence closure and unexecuted single-episode cost calculation."""
import datetime
import json
import math
from pathlib import Path
import sys
from retry.path271_run import read,save,sha
from retry.package349_stage import verify,G
from retry.package349_run import cached,rows,projection
from retry.support342_logic import advance_evidence
import numpy as np


def close(R):
    D=R/'stage349';p=verify(R);run=read(D/'run-result.json');assert run['passed'] and not run['technical_error'];assert not (D/'cost.json').exists()
    assert run['budget']['actor_act_calls']==466 and run['budget']['actor_resets']==2
    candidate=cached(D/'candidate/records-private.jsonl');actual=rows(R/'stage340/B/trace-private.jsonl');assert len(candidate)==len(actual)==233
    changed={key:[i+1 for i in range(233) if candidate[i]['response'][key]!=actual[i][ref]] for key,ref in [('action','returned_action'),('features','features'),('pixel_path','pixel_path'),('delta_audit','audit')]}
    changed['nominal_memory']=[i+1 for i in range(233) if candidate[i]['commit']['memory']!=actual[i]['nominal_memory']]
    changed['original_state_projection']=[i+1 for i in range(233) if projection(candidate[i]['commit']['state'])!=projection(actual[i]['policy'])]
    assert not any(changed.values())
    contexts={}
    for stage in [337,340]:
        saved=cached(R/f'stage342/N2_{stage}/candidate/records-private.jsonl');old=rows(R/f'stage{stage}/B/trace-private.jsonl');frames=np.load(R/f'stage{stage}/B/frames-actions-private.npz')['frames_uint8'];previous=[];selection_diff=[];active=[];extra_births=set()
        for i in range(233):
            step=i+1;ref=saved[i]['response'];state=advance_evidence(old[i]['tracker'],previous,step,frames[i].astype(np.float32)/255);previous=state['after'];assert state==ref['support_record']
            generic=[j for j,e in enumerate(previous) if e['low']]
            known=[j for j,e in enumerate(previous) if e['uid']==[121,0] and step>=127]
            assert generic==ref['routing_evidence']['removed_indices']
            if stage==340:assert known==old[i]['routing_filter']['removed_indices']
            if generic:active.append(step)
            if generic!=known:
                selection_diff.append(step)
                for j in generic:
                    if j not in known:extra_births.add(tuple(previous[j]['uid']))
        contexts[str(stage)]=dict(inputs=233,general_rule_active_steps=active,selection_diff_from_known121_start127=selection_diff,extra_selected_births=[list(q) for q in sorted(extra_births)],verification='New frozen candidate actor233 on340, exact saved342 general-rule replay and exact actual340 outputs.' if stage==340 else 'Reused saved342 general-rule actor replay on337 plus exact packaged-helper source and offline metadata/tracker algebra; no new candidate337 actor.',fresh_candidate_actor_calls=233 if stage==340 else 0)
    assert contexts['337']['selection_diff_from_known121_start127']==list(range(121,127))
    assert contexts['340']['selection_diff_from_known121_start127']==list(range(121,127))+[135,232]
    v=read(R/'project-effective-budget-v360.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1284005,233,84000,0)
    reset=read(R/'stage337/actual-reset-contract.json');cap=math.ceil((reset['raw_limit']-reset['elapsed_after_reset'])/reset['frame_skip']);assert cap==2038
    oldcost=read(R/'stage340/B/result.json');future=dict(status='costed_only_not_executed_or_reserved',design='One fresh actual N2 candidate349 episode, same frozen334ON/H1 initialization/environment/RNG as qualified337/340. Reuse actual337 baseline; no new baseline run. All own observations/returned controls/normal memory. Prior233 replay and prefix validation are included in the episode cap, not an extra native phase.',
        candidate_archive_sha256=p['configs']['candidate']['archive_sha256'],total_maximum_new_wrapper_actions=cap,new_candidate_runs=1,new_baseline_runs=0,new_environment_resets=1,maximum_actor_act_calls=cap,actor_resets=1,
        raw_time_limit=reset['raw_limit'],raw_counter_after_reset=reset['elapsed_after_reset'],frame_skip=reset['frame_skip'],maximum_postreset_raw_ticks=reset['remaining_raw'],expected_reset_raw_ticks=reset['raw_reset_ticks'],maximum_total_physics_ticks_including_reset=reset['remaining_raw']+reset['raw_reset_ticks'],last_action_raw_ticks=reset['last_action_raw_ticks'],
        available_research=233,with_current_research='At most233fresh actions including prefix. Existing evidence predicts exact340 prefix233 and protocol censor without observed finish; this buys no new continuation. Minimum234actions for one novel endpoint would need+1 but cannot guarantee a full episode.',minimum_additional_research_for_full_horizon=cap-233,research_operating_cap_after_requested_grant=1368238+cap-233,final_reserved_actions=84000,final_reserve_used=0,
        accounting='No grant is made here.2038 is a maximum reservation, not a promise of completion or a fixed charged total. Charge actual steps and technical failures; stop at official finish/retirement, mismatch, time limit or deadline. A fresh start must repay233prefix; no saved-physics resume or implied discount.',
        stops_and_gate='Before native execution separately register archive/environment/init/RNG hashes and cap; qualify reset, input-only interface and exact returned controls/tracker/original-memory/physical/accessRNG prefix against340. Extra packaged metadata has its own audit, so fullagent pickle identity with old340 is not claimed. Any leak/interface/technical or prefix mismatch stops expansion. Finish first; retroactive official lap; DNF/protocol/technical censor separate. No automatic retry/extension/protected split/promotion.',
        approximate_instrumented_wall_s=oldcost['wall_s']/233*cap,wall_estimate_scope='Single historical340instrumented wall/action extrapolation including its reset; not a fresh measurement, not a strict upper bound, and excludes setup/hash/coding/report/git. Actual final run may stop earlier or cost differently.',deadline_utc=p['deadline_utc'])
    cost=dict(stage=349,new_wrapper_actions=0,new_native_actions=0,cached_actor_calls=466,actor_resets_on_saved_pixels=2,new_environment_resets=0,new_source_physics_ticks=0,new_learning_fits=0,new_thresholds=0,new_tuning=0,new_paid_resources=0,wall_s=run['wall_s'],runner_CPU_s=run['runner_CPU_s'],actor_CPU_s=run['actor_CPU_s_known'],measurement_scope='Replay runner includes IPC/preparation/recording/hash verification. Does not measure new simulator cost or all task coding/closure/git wall.',actual_cumulative_wrapper_actions=1284005,research_remaining=233,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1368238)
    assert sha(R/'stage296/submission296.zip')=='0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937'
    assert sha(R/'stage296/champion-manifest.json')=='b92fe5307a491bfb9d1f5081bf97c9c1d4646dcf9c8511fb169bc48c8f9349e5'
    for f in ['DEV','screen-opening.json','DEV-opened-by309.json']:assert not (R/'stage297'/f).exists()
    assert all(r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent'] for r in run['receipts'])
    result=dict(stage=349,passed=True,technical_error=None,artifacts={m:dict(archive_sha256=c['archive_sha256'],worker_sha256=c['worker_sha256'],private_only=True) for m,c in p['configs'].items()},baseline233_exact=True,candidate340233_exact_saved342=True,candidate340_differences_from_known121_actual=changed,contexts=contexts,
        interpretation='General342 rule filters121lineage from birth121, whereas known340starts127. Those earlier selections are not route-relevant on saved inputs. Extra zero-ring births135and232 occur on340only and are also route-irrelevant here. The233actions/features/paths/audits/nominal memory/original state projection all match actual340; candidate is not rewritten. This is replay equivalence, not a new actual completion result.',
        interface=dict(input='Only float32(4,84,84) grayscale stacks in[0,1], oldest-to-newest; reset repeats one frame.',output='Finite float32 shape3 and official ranges; commit own returned actions, nominal memory preserved.',reset='Baseline full saved state exact; candidate original-state projection exact and packaged metadata empty/step0/recordNone.',code_path='Standalone archive executes metadata and routing selection; observer validates/records arguments without changing selection. Actual root/nominal/tracker module paths and loaded hashes checked inside clean package.',audit='No denied Python audit events, no simulator import, one CPU/thread, memory limit and module-origin checks. Same-host research isolation; official fresh-machine parity is not proven.'),
        limits=['337and340are different post127actual trajectories; never treat their two new replay arms as a paired causal A/B test. Candidate337 evidence is reused342replay/algebra, not new candidate337invocation.',
        'Packaged metadata adds persistent attributes so serialized full-agent hashes differ by construction. Controller/hazard/image/history/RNG state projections are compared explicitly.',
        'Single previously observed N2 condition; no semantic false-positive, occlusion-preservation, generalization or completion inference.334mixed evidence and296champion remain unchanged.'],next_single_experiment=future,cost=cost,new_protected_split_opened=False,promotion=False,champion296_preserved=True,deadline_utc=p['deadline_utc'])
    save(D/'cost.json',cost);save(D/'summary-private.json',result);save(D/'next-single-experiment-cost.json',future);save(G/'retry/package349_result.json',result)
    save(D/'final-report-verification.json',dict(passed=True,immutable_artifacts_and_registered_sources_preserved=True,baseline_full_state233_exact=True,candidate_generic342_outputs233_exact=True,actual340_original_state_projection233_exact=True,native_actions=0,no_extra_actor_calls=True,protected_split_unchanged=True,champion296_preserved=True,next_native_experiment_executed=False))
    v.update(version=361,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v360.json'),prior_budget_sha256=sha(R/'project-effective-budget-v360.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,stage349_new_wrapper_actions=0);assert not (R/'project-effective-budget-v361.json').exists();save(R/'project-effective-budget-v361.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==349 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(dict(passed=True,contexts=contexts,cost=cost,full_episode_cap=cap,additional_research_needed=cap-233)),flush=True)


if __name__=='__main__':close(Path(sys.argv[1]).resolve())
