"""Separate one O2actualpaired outcome from the historical N2feasibility result."""
import datetime
import json
from pathlib import Path
import sys
import numpy as np
from retry.path271_run import read,save,sha
from retry.pair353_stage import verify,G
from retry.package349_run import rows,projection
from retry.pair343_close import describe
from retry.confidence341_run import label


def close(R):
    D=R/'stage353';p=verify(R,True);assert not (D/'cost.json').exists();result={m:read(D/m/'result.json') for m in ['A','B']};data={m:rows(D/m/'trace-private.jsonl') for m in ['A','B']};zs={m:np.load(D/m/'frames-actions-private.npz') for m in ['A','B']};budget=read(D/'native-budget.json');gate=read(D/'natural-prefix-qualification.json')
    assert gate['passed'] and read(D/'paired-reset-qualification.json')['passed'];assert all(r['technical_error'] is None for r in result.values())
    used=sum(r['native_actions'] for r in result.values());assert used==budget['actions']==budget['actor_act_calls']<=800 and budget['resets']==budget['actor_resets']==2
    for m in ['A','B']:
        a=result[m];rr=data[m];assert a['historical343_prefix_actions_verified']==160 and read(D/m/'historical343-prefix160-qualified.json')['passed'];assert len(rr)==len(zs[m]['actions'])==a['native_actions']==budget['arms'][m]==budget['actor_arms'][m]<=400 and len(zs[m]['frames_uint8'])==len(rr)+1
        assert sum(x['raw_ticks'] for x in rr)==a['raw_step_ticks']==a['raw_counter_at_stop']-50 and a['raw_reset_ticks']==51
        assert all(not x['terminated'] and not x['truncated'] for x in rr[:-1]);assert a['reaping']['process_reaped'] and a['reaping']['actor_pids_absent']
        for x in rr:assert x['executed']==x['returned_action'] and x['nominal_memory']==x['policy']['previous_steer'] and np.float32(x['nominal_memory'])==np.float32(x['executed'][0]) and len(x['raw_observations'])==x['raw_ticks']
        if a['completed']:assert a['stop_reason']=='official_finish' and not a['censored'] and not a['protocol_stop'] and a['lap_ms']==round((a['finish']['finish_time_s']-a['postreset_start_time'])*1000)
        if a['protocol_stop']:assert a['native_actions']==400 and not a['completed'] and not a['actual_DNF'] and a['censored']
    if gate['no_semantic_branch']:
        assert len(data['A'])==len(data['B'])==gate['common_actual_actions'];assert np.array_equal(zs['A']['actions'],zs['B']['actions']) and np.array_equal(zs['A']['frames_uint8'],zs['B']['frames_uint8']);assert gate['common_input_stacks']==len(data['B'])+1
        for x,y in zip(data['A'],data['B']):
            for k in ['executed','features','pixel_path','nominal_memory','tracker','pre','post','pre_physical','post_physical','pre_RNG','post_RNG','raw_observations']:assert x[k]==y[k],k
            assert projection(x['actor_state'])==projection(y['actor_state']) and projection(x['policy'])==projection(y['policy'])
    outcomes={m:describe(data[m],result[m]) for m in ['A','B']};both=all(r['completed'] for r in result.values());delta=result['B']['lap_ms']-result['A']['lap_ms'] if both else None
    ordering='official_lap_tie' if both and delta==0 else 'candidate_B_slower' if both and delta>0 else 'candidate_B_faster' if both else 'candidate_only_observed_finish' if result['B']['completed'] and result['A']['actual_DNF'] else 'baseline_only_observed_finish' if result['A']['completed'] and result['B']['actual_DNF'] else 'censored_or_nonfinish_no_paired_lap_ordering'
    birth_labels={};births=[];held=[];supported_losses=[]
    for x in data['B']:
        for item in x['support_record']['births']:
            lab,_=label(item['point'],x['pre_physical']);birth_labels[tuple(item['uid'])]=lab
            if item['low']:births.append(dict(action=x['step'],direct_index=item['uid'][1],area_pixels=item['component_area'],posthoc_geometric_label=lab))
        for item in x['routing_evidence']['removed_evidence']:
            held.append(dict(action=x['step'],uid=item['uid']))
            if birth_labels[tuple(item['uid'])]=='fixture_supported':supported_losses.append(dict(action=x['step'],uid=item['uid']))
    v=read(R/'project-effective-budget-v365.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'],v['B_operating_cap'])==(1284945,1098,84000,0,1370043)
    measures=['wall_s','runner_CPU_s','actor_CPU_s','reset_wall_s','raw_step_render_wall_s','raw_contact_observer_wall_s','capture_wall_s','journal_wall_s','artifact_wall_s']
    cost=dict(stage=353,new_wrapper_actions=used,per_arm_native={m:result[m]['native_actions'] for m in ['A','B']},new_baseline_runs=1,new_candidate_runs=1,new_environment_resets=2,total_cap=800,per_arm_cap=400,additional_research=0,new_cached_actor_calls=0,actual_actor_calls=budget['actor_act_calls'],actual_actor_resets=2,new_native_auxiliary=0,raw_step_ticks=sum(r['raw_step_ticks'] for r in result.values()),raw_reset_ticks=102,new_source_physics_rollout_ticks=0,new_learning_fits=0,new_tuning=0,new_paid_resources=0,technical_error=None,technical_recovery_native=0,per_arm_measurements={m:{k:result[m][k] for k in measures} for m in ['A','B']},total_measurements={k:sum(r[k] for r in result.values()) for k in measures},actual_cumulative_wrapper_actions=1284945+used,research_remaining=1098-used,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1370043,unused_reserved_actions=800-used,historical_N2_charged_again=False,measurement_scope='Only two fresh353O2runs charged. Prefix within each400cap, no cache orauxiliarynative. Rawstep includesrender; observers/capture/journal/artifact distinct timers. Coding/setup/hash/closure/git not fully measured.')
    n2=read(R/'stage350/summary-private.json');assert n2['official_outcome']['completed'] and n2['official_outcome']['lap_ms']==23320
    no_observed_regression=bool(both and delta<=0 and not supported_losses)
    next_decision=dict(status='Proposal only, not executed/reserved.',keep_champion296=True,no_generalization_or_occlusion_claim=True,do_not_repeat_N2_orO2=True,additional_research_grant=0)
    next_decision.update(decision='Stop this known-case native sequence and preserve remainingresearch for contingency. Keep349as research-onlycandidate and296as champion. Do not repeat N2/O0/O2or add cache/tuning arms. Consolidate frozen artifact identities, condition-specific outcomes, censoring and final-validation readiness without opening protectedsplits or executing finalreserve.',
        reason='The planned three known-condition evidence set is complete. Its limits and existing334mixedaggregate evidence do not justify promotion/generalization. Any later newtest needs a distinct question and separately preregistered budget; no automatic extension.',
        next_action_native_cap=0,final_reserve_execution_authorized=False,research_remaining=cost['research_remaining'])
    oldO0=read(R/'stage352/summary-private.json')
    report=dict(stage=353,paired_condition_valid=True,artifacts_modified=False,baseline_archive_sha256=p['configs']['A']['archive_sha256'],candidate_archive_sha256=p['configs']['B']['archive_sha256'],outcomes=outcomes,official_ordering=ordering,both_finished=both,candidate_minus_baseline_lap_ms=delta,natural_prefix=gate,predicate_exposed_on_actual_B=bool(births),predicate_scope='No low-support birth on actualO2; fixedfilter never activated. This is observedno-op/nonregression on thisowntrajectory, not an activefilter/retention safety test.' if not births else 'Actualfixedpredicate activated; seebirths andheldactions, no generalsafetyclaim.',
        rule_audit=dict(low_births=births,withheld_action_count=len(held),withheld_actions=sorted({x['action'] for x in held}),fixture_supported_withheld_count=len(supported_losses),semantic_truth_or_actual_occlusion_verified=False,GT_input_to_policy=False),
        historical_N2_separate=dict(reused_not_new=True,candidate350=dict(native_actions=292,completed=True,lap_ms=23320,unique_tiles=292,total_tiles=292,damage=0.0),baseline337=dict(native_actions=233,actual_DNF=True,retire_reason='off_track',unique_tiles=132,total_tiles=292,damage=.2),lap_delta=None,scope='SeparateknownTRAINcondition; prior337/350notrerun/relabelled/charged. Do not pool times or substitute296champion.'),
        historical_O0_separate=dict(reused_not_new=True,outcomes=oldO0['outcomes'],lap_delta_ms=oldO0['candidate_minus_baseline_lap_ms'],predicate_exposed=False,scope='Prior352actualpairedcompletiontie withno low-supportbirth, not new353data or activefiltertest.'),historical343_prefix=dict(reused_not_new=True,each_new_arm_actions_reproduced=160,input_stacks_per_arm=161,originalstate_projection_pixels_physics_accessRNG_rawticks_exact=True,old343_native_charged_again=False),combined_interpretation='N2finish-versus-DNF, priorO0inactive-rulecompletiontie and newO2pairedobjective remain separate knownconditions. Do not pool laps orclaim general safety/superiority/championpromotion.',
        limits=['Three knownTRAINconditions only, postselected researchcontext. N2completed once, priorO0paired once and O2paired once; no successrate, generalization or occlusion-preservation claim.',
        'Original-state projection deliberately excludes fullagentpickle differences caused by candidate metadata. Capturedphysics/RNG/rawticks exactwherecommon; hidden solver/OpenCV RNG and omitted warmstart/contactisland state notdirectlymeasured.',
        'Only343prefix160was validated on freshlyreturnedcontrols, no storedcontinuation orforcedbirth.296O2stages346/347are a separatepolicycontext and never thebaseline. Damage/contact diagnostics do not replace officialcompletion/lapordering.',
        'Preserve existing334mixed aggregate evidence and champion296. No newprotected split, fit, tuning, automaticextension or extraarm.'],cost=cost,next_decision=next_decision,champion296_preserved=True,new_DEV_opening=False,new_HOLDOUT_opening=False,new_SEALED_opening=False,promotion=False,authorization_end_utc=p['deadline_utc'])
    assert sha(R/'stage296/submission296.zip')=='0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937' and sha(R/'stage296/champion-manifest.json')=='b92fe5307a491bfb9d1f5081bf97c9c1d4646dcf9c8511fb169bc48c8f9349e5'
    for name in ['DEV','screen-opening.json','DEV-opened-by309.json']:assert not (R/'stage297'/name).exists()
    save(D/'cost.json',cost);save(D/'summary-private.json',report);save(G/'retry/pair353_result.json',report);save(D/'final-report-verification.json',dict(passed=True,twoactualfreshresets=True,naturalprefixqualified=True,unchanged349artifacts=True,no_postterminal_steps=True,actualnative=used,oldN2notneworcharged=True,research_remaining=cost['research_remaining'],final_reserve=84000,next_comparison_not_executed=True))
    v.update(version=366,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v365.json'),prior_budget_sha256=sha(R/'project-effective-budget-v365.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage353_new_wrapper_actions=used);assert not (R/'project-effective-budget-v366.json').exists();save(R/'project-effective-budget-v366.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==353 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(dict(outcomes=outcomes,ordering=ordering,lap_delta=delta,naturalprefix=gate,low_births=births,cost=cost,next_decision=next_decision)),flush=True)


if __name__=='__main__':close(Path(sys.argv[1]).resolve())
