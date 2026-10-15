"""Actual357T2954regression check versus an explicitly historical349record."""
import datetime
import json
from pathlib import Path
import sys
import numpy as np
from retry.path271_run import read,save,sha
from retry.episode362_stage import G
from retry.package349_run import projection
from retry.pair343_close import describe
from retry.confidence341_run import label


def rows(path):return [json.loads(x) for x in Path(path).read_text().splitlines()]


def connection_status(D):
    c=read(D/'connection-alert-check-private.json')
    return dict(parent_reported_alert=c['parent_reported_disconnect_alert'],tool_access_succeeded=c['tool_access_succeeded'],existing_run_continued=c['later_check_actions']>c['first_check_actions'],first_checked_actions=c['first_check_actions'],later_checked_actions=c['later_check_actions'],one_runner_observed=len(c['matching_runner_pids'])==1,environment_resets=c['resets'],manual_reconnection=c['manual_reconnection'],restart_or_duplicate_run=c['restart_or_duplicate_run'],actual_block_observed=False,scope='Alertcauseunverified;read-onlytoolchecksaccessedexistingrunnerandpersistedprogress. Normalcompletion,noexperimentrecoveryorrestart. Thisdoesnotdiagnoseeverytransientnetworkevent.')

def close(R):
    D=R/'stage362';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    assert not (D/'cost.json').exists();r=read(D/'B/result.json');data=rows(D/'B/trace-private.jsonl');old=rows(R/'stage355/B/trace-private.jsonl');oldresult=read(R/'stage355/B/result.json');z=np.load(D/'B/frames-actions-private.npz');oz=np.load(R/'stage355/B/frames-actions-private.npz');b=read(D/'native-budget.json');gate=read(D/'historical-comparison-qualification.json')
    assert r['technical_error'] is None and r['comparison_valid'] and gate['passed'] and read(D/'reset-qualification.json')['passed'];used=b['actions'];assert used==r['native_actions']==len(data)==len(z['actions'])==b['actor_act_calls']==b['actor_commit_calls']<=1393 and len(z['frames_uint8'])==used+1 and b['resets']==b['actor_resets']==1
    assert sum(x['raw_ticks'] for x in data)==r['raw_step_ticks']==r['raw_counter_at_stop']-50;assert all(not x['terminated'] and not x['truncated'] for x in data[:-1]);assert r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent']
    for x in data:assert x['executed']==x['returned_action'] and x['nominal_memory']==x['policy']['previous_steer'] and np.float32(x['nominal_memory'])==np.float32(x['executed'][0]) and len(x['raw_observations'])==x['raw_ticks']
    if gate['no_semantic_branch']:
        assert used==len(old)==gate['common_semantic_actions'] and gate['common_qualified_input_stacks']==used+1 and np.array_equal(z['actions'],oz['actions']) and np.array_equal(z['frames_uint8'],oz['frames_uint8'])
        for x,y in zip(data,old):
            for key in ['executed','features','pixel_path','audit','nominal_memory','tracker','support_record','pre','post','pre_physical','post_physical','pre_RNG','post_RNG','raw_observations','finish']:assert x[key]==y[key],key
            assert projection(x['actor_state'])==projection(y['actor_state']) and projection(x['policy'])==projection(y['policy'])
    if r['completed']:assert r['stop_reason']=='official_finish' and not r['censored'] and not r['protocol_stop'] and r['lap_ms']==round((r['finish']['finish_time_s']-r['postreset_start_time'])*1000)
    if r['protocol_stop']:assert used==1393 and r['censored'] and not r['completed'] and not r['actual_DNF']
    births={};direct=retained=missing_direct=missing_retained=0;losses=[];lowbirths=[];held=[];protected=[]
    for x in data:
        for item in x['support_record']['births']:
            lab,idx=label(item['point'],x['pre_physical']);births[tuple(item['uid'])]=dict(label=lab,fixture_index=idx)
            if item['low']:lowbirths.append(dict(action=x['step'],uid=item['uid'],area_pixels=item['component_area'],label=lab))
        for j,(h,item) in enumerate(zip(x['tracker']['after'],x['support_record']['after'])):
            lab=births[tuple(item['uid'])]['label'];age=h[3];excluded=j in x['routing_evidence']['removed_indices']
            if lab=='fixture_supported':
                if age==0:direct+=1
                else:retained+=1
                if excluded:losses.append(dict(action=x['step'],uid=item['uid'],kind='direct' if age==0 else 'birth_supported_retained'))
            if lab=='missing_GT':
                if age==0:missing_direct+=1
                else:missing_retained+=1
            if age==0:assert not excluded
            if item['low'] and age==0:protected.append(x['step'])
            if excluded:assert item['low'] and age>0;held.append(x['step'])
    pathdiff=[x['step'] for x,y in zip(data,old) if x['pixel_path']!=y['pixel_path']]
    targetdiff=[x['step'] for x,y in zip(data,old) if x['features'][:3]!=y['features'][:3]]
    retained_details=[dict(action=x['step'],uid=x['support_record']['after'][j]['uid'],age=x['tracker']['after'][j][3]) for x in data for j in x['routing_evidence']['removed_indices']]
    observed92=[]
    if len(data)>=92:
        x=data[91]
        for j,(h,item) in enumerate(zip(x['tracker']['after'],x['support_record']['after'])):
            if item['uid']==[92,0]:observed92.append(dict(action=92,uid=item['uid'],age=h[3],low=item['low'],label=births[tuple(item['uid'])]['label'],routed=j not in x['routing_evidence']['removed_indices']))
    outcome=describe(data,r);historic=describe(old,oldresult);both=r['completed'] and oldresult['completed'];delta=r['lap_ms']-oldresult['lap_ms'] if both else None
    ordering='official_lap_tie' if both and delta==0 else 'new357_slower' if both and delta>0 else 'new357_faster' if both else 'historical_finish_new_DNF' if oldresult['completed'] and r['actual_DNF'] else 'censored_or_nonfinish_no_lap_ordering'
    v=read(R/'project-effective-budget-v376.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'],v['B_operating_cap'])==(1287049,1393,84000,0,1372442)
    measures=['wall_s','runner_CPU_s','actor_CPU_s','reset_wall_s','raw_step_render_wall_s','raw_contact_observer_wall_s','capture_wall_s','journal_wall_s','artifact_wall_s']
    cost=dict(stage=362,new_wrapper_actions=used,new_candidate_runs=1,new_baseline_runs=0,new_environment_resets=1,new_actor_act_calls=b['actor_act_calls'],new_actor_commit_calls=b['actor_commit_calls'],actor_resets=1,new_cached_actor_calls=0,new_native_auxiliary=0,native_cap=1393,additional_research=0,raw_step_ticks=r['raw_step_ticks'],raw_reset_ticks=r['raw_reset_ticks'],new_source_physics_rollout_ticks=0,new_learning_fits=0,new_tuning=0,new_paid_resources=0,technical_error=None,technical_recovery_native=0,measurements={k:r[k] for k in measures},actual_cumulative_wrapper_actions=1287049+used,research_remaining=1393-used,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1372442,unused_reserved_native=1393-used,historical355_reexecuted_or_recounted=False,measurement_scope='Only362freshactualrun charged; no newcontrol/cache/auxiliaryphysics. Rawstep includesrender; contact/capture/journal/artifact distincttimers. Registration/coding/closure/git/taskwall notfullytimed.')
    report=dict(stage=362,new_actual_policy='Frozen357age0guard on334ON/H1',candidate_archive_sha256=p['config']['archive_sha256'],candidate_modified=False,comparison_valid=True,official_outcome=outcome,stop_reason=r['stop_reason'],historical355_349_B=dict(reused_not_new=True,outcome=historic,worker_version_difference='357passiveactual-subsetobserver versus349low-implies-excludedobserver; no selection inobserver. Same357observer baselinequalifiedbefore362, actualcode/modulehashesbound.',case_init_environment_runtime_models_matched=True),official_ordering=ordering,new_minus_historical_lap_ms=delta,qualification=gate,
        first_differences=dict(routing_membership=r['first_routing_membership_difference'],pixel_path=pathdiff[0] if pathdiff else None,target=targetdiff[0] if targetdiff else None,semantic_path_target_features_audit_state=r['first_semantic_output_difference'],full_control=r['first_full_control_difference'],scope='Membershipdifference isnot automatically a path/target/controloutputdifference. Postbranch temporalcomparisons wouldbecoupledtrajectory descriptors.'),
        support_audit=dict(known_supported_direct_contexts=direct,known_birth_supported_retained_contexts=retained,supported_direct_losses=sum(x['kind']=='direct' for x in losses),supported_retained_losses=sum(x['kind']=='birth_supported_retained' for x in losses),losses=losses,missing_birth_GT_direct=missing_direct,missing_birth_GT_retained=missing_retained,low_births=lowbirths,protected_current_direct_actions=protected,retained_exclusion_actions=sorted(set(held)),retained_exclusions=retained_details,scope='GTbirthlabelscomputedafterepisode; sourcecirclecorrespondence, notsemanticmaterial/occlusiontruth. Initialidentity/readonlystatecapture didnotenteractorcontrols.'),
        direct92_audit=observed92,
        cache_context='357T2954wasfixed355pixelreplayonly;362isfirstactual357T2954episode.355349recordishistoricalnotnewcontrol.',
        finish=dict(qualification_raw_time_s=r['finish']['finish_qualified_time_s'],center_crossing_raw_time_s=r['finish']['finish_time_s'],declaration_raw_time_s=r['finish']['raw_time'],postreset_start_time_s=r['postreset_start_time'],official_lap_ms=r['lap_ms']),
        limits=['OneknownT2954condition andonefreshcandidateversusqualifiedhistoricalrecord; no newpairedcontrol, population/generalization orpromotionclaim.',
        'This362is a newactual357T2954episode. Prior358/359/360/361measureotherconditions;357cachedreplayandhistorical355349completionremainseparate.',
        'Originalpolicy stateprojection excludesfullagentpickle andcodeidentityboundseparately. AccessibleRNG/capturedphysics/rawtickscheckedwherecommon; hidden solver/OpenCV RNG/warmstart/islandstate notdirectlycaptured.',
        'The age0guard doesnotprove safetyofretained lowflagpointsundernewocclusion. Preserve355counterexamplehistory,357cachetradeoffand334mixedaggregate evidence. No othercandidate, protectedsplit, fit ortuning.'],cost=cost,promotion=False,champion296_preserved=True,new_HOLDOUT_opening=False,new_SEALED_opening=False,next_step='Remaining13conditionsbudgetproposalonly; no automaticnative,grant,retuning,protectedopeningorpromotion.')
    report['connection_alert']=connection_status(D)
    measured=[]
    for stage,key in [(358,'O2'),(359,'N2'),(360,'T29511'),(361,'T2950'),(362,'T2954')]:
        pp=read(R/f'stage{stage}/plan.json');rr=read(R/f'stage{stage}/B/result.json');assert pp['config']['archive_sha256']==p['config']['archive_sha256'] and pp['case']==read(R/'stage330/plan.json')['cases'][key]
        measured.append(dict(condition=key,source_stage=stage,completed=rr['completed'],native_actions=rr['native_actions'],lap_ms=rr['lap_ms'],damage=rr['damage']))
    remaining=[key for key in read(R/'stage330/plan.json')['roads'] if key not in {x['condition'] for x in measured}];assert len(remaining)==13
    report['actual357_coverage']=dict(actual_measured=measured,not_yet_actual_measured=remaining,not18conditionbenchmark=True)
    report['remaining13_budget_proposal']=dict(status='proposalonly_noreservation_grantorexecution',conditions=remaining,episodes=13,per_episode_action_cap=2000,maximum_wrapper_actions=26000,environment_resets=13,maximum_actor_act_calls=26000,maximum_actor_commit_calls=26000,maximum_raw_step_ticks=104000,expected_raw_reset_ticks=663,maximum_total_raw_ticks=104663,existing_research_after362=1393-used,additional_research_needed_for26000=26000-(1393-used),final_reserve=84000,reserve_change=0,new_controls=0,new_cache_calls=0,new_fits=0,source='Existingnormalepisodecontract/local_runnerdefault2000; notautomatic2038TimeLimitextension. Eachrunstopsatfirstofficialterminal/cap/deadline; actualcostonly. Currentdeadlineunchanged.',underlying2038_option=dict(maximum_wrapper_actions=26494,additional_needed=26494-(1393-used),explicit_separate_authorization_required=True))
    assert sha(R/'stage296/submission296.zip')=='0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937' and sha(R/'stage296/champion-manifest.json')=='b92fe5307a491bfb9d1f5081bf97c9c1d4646dcf9c8511fb169bc48c8f9349e5'
    for name in ['DEV','screen-opening.json','DEV-opened-by309.json']:assert not (R/'stage297'/name).exists()
    save(D/'cost.json',cost);save(D/'summary-private.json',report);save(G/'retry/episode362_result.json',report);save(D/'final-report-verification.json',dict(passed=True,onefreshcandidate=True,newnative=used,historical355_notneworrecounted=True,T2954_355_history_only=True,source_andinitialization_qualified=True,first_routing_membership_difference=r['first_routing_membership_difference'],first_full_control_difference=r['first_full_control_difference'],known_support_gate_passed=not losses,official_finish=r['completed'],research_remaining=1393-used,final_reserve=84000,newprotected_split_orpromotion=False))
    v.update(version=377,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v376.json'),prior_budget_sha256=sha(R/'project-effective-budget-v376.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage362_new_wrapper_actions=used);assert not (R/'project-effective-budget-v377.json').exists();save(R/'project-effective-budget-v377.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==362 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(dict(outcome=outcome,historical=historic,ordering=ordering,lap_delta=delta,qualification=gate,support=report['support_audit'],cost=cost)),flush=True)


if __name__=='__main__':close(Path(sys.argv[1]).resolve())
