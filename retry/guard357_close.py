"""Separate actual cached actors, no-op algebra and unmeasured closed loops."""
import datetime
import json
from pathlib import Path
import sys
import time
import zipfile
from retry.path271_run import read,save,sha
from retry.guard357_stage import G
from retry.package349_run import cached,projection


def close(R):
    D=R/'stage357';assert not (D/'cost.json').exists();p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    repair=read(D/'parser-repair-registration.json');assert repair['original_registered_runner_sha256']==sha(G/'retry/guard357_run.py') and repair['recovery_adapter_sha256']==sha(G/'retry/guard357_recover.py')
    initial=read(D/'technical-parser-failure0/run-result.json');assert initial['budget']['actor_act_calls']==initial['budget']['actor_resets']==0
    run=read(D/'run-result.json');pre=read(D/'support-preflight-private.json');b=read(D/'call-budget.json');start,cpu=time.perf_counter(),time.process_time();pairs=[];N2=[];T355=None
    passed=bool(run['passed'] and pre['passed'])
    if passed:
        assert b['actor_act_calls']==b['actor_commit_calls']==3342 and b['actor_resets']==12
        assert len(run['receipts'])==12 and all(x['error'] is None and x['reaping']['process_reaped'] and x['reaping']['actor_pids_absent'] for x in run['receipts'])
        for case in p['cases']:
            key=case['key'];a=cached(D/key/'baseline/records-private.jsonl');v=cached(D/key/'variant/records-private.jsonl');assert len(a)==len(v)==case['count'];changes={k:[] for k in ['routing_membership','path','target','features','float32_action','nominal_memory','original_state_projection']};protected_direct=[]
            for i in range(case['count']):
                x,y=a[i]['response'],v[i]['response'];cx,cy=a[i]['commit'],v[i]['commit'];assert x['tracker_record']==y['tracker_record'] and x['support_record']==y['support_record']
                flags=dict(routing_membership=x['routing_evidence']['removed_indices']!=y['routing_evidence']['removed_indices'],path=x['pixel_path']!=y['pixel_path'],target=x['features'][:3]!=y['features'][:3],features=x['features']!=y['features'],float32_action=x['action']!=y['action'],nominal_memory=cx['memory']!=cy['memory'],original_state_projection=projection(cx['state'])!=projection(cy['state']))
                for k,f in flags.items():
                    if f:changes[k].append(i+1)
                if flags['routing_membership']:
                    restored=set(x['routing_evidence']['removed_indices'])-set(y['routing_evidence']['removed_indices']);assert restored and all(y['tracker_record']['after'][j][3]==0 for j in restored);protected_direct.append(i+1)
            item=dict(key=key,inputs=case['count'],evidence='Two actualfrozenpixelactorreplays, ownreturnedcommands/normalmemory; no environment.',changes=changes,protected_direct_actions=protected_direct,baseline_historical_reproduction_passed=True,variant_known_supported_direct_and_retained_losses=0);pairs.append(item)
            if key=='T2954_355':
                x,y=a[91]['response'],v[91]['response'];assert x['routing_evidence']['removed_indices']==[1] and y['routing_evidence']['removed_indices']==[] and y['support_record']['after'][1]['uid']==[92,0] and y['support_record']['after'][1]['low']
                T355=dict(fixture_supported92_current_direct_routed=True,original_low_metadata_flag_still_true=True,verified_by_actual_actor_replay=True,all356path_target_action_nominalmemory_unchanged=all(not changes[k] for k in ['path','target','float32_action','nominal_memory']),source356inference_confirmed_by_actor_replay=not any(92 in changes[k] for k in ['path','target','float32_action','nominal_memory']),new_actual_completion_claim=False)
            if key in ['N2_337','N2_340']:
                assert not any(changes[k] for k in ['path','target','features','float32_action','nominal_memory','original_state_projection']);old=cached(R/f'stage342/{key}/baseline/records-private.jsonl');vsnofilter={k:[] for k in ['path','target','float32_action','steering','pedals','nominal_memory']};ages=[]
                for i in range(case['count']):
                    x,y=old[i]['response'],v[i]['response'];flags=dict(path=x['pixel_path']!=y['pixel_path'],target=x['features'][:3]!=y['features'][:3],float32_action=x['action']!=y['action'],steering=x['action'][0]!=y['action'][0],pedals=x['action'][1:]!=y['action'][1:],nominal_memory=old[i]['commit']['memory']!=v[i]['commit']['memory'])
                    for k,f in flags.items():
                        if f:vsnofilter[k].append(i+1)
                    if 127<=i+1<=129:
                        removed=y['routing_evidence']['removed_indices'];assert len(removed)==1;j=removed[0];assert y['support_record']['after'][j]['uid']==[121,0];ages.append(y['tracker_record']['after'][j][3])
                assert ages==[6,7,8] and vsnofilter['path']==[127,128,129] and vsnofilter['target']==[128,129] and vsnofilter['float32_action'][0]==127 and vsnofilter['steering'][0]==128
                N2.append(dict(key=key,all233old349outputs_and_normalmemory_preserved=True,critical_retained_exclusion_actions=[127,128,129],critical_retained_ages=ages,differences_from_no_filter342baseline=vsnofilter,evidence='Newvariantactualactorreplay versus qualifiedsavednofilterreference. Bothsource trajectories partlyshared, notindependenttrials oractualworldcomparisons.'))
        assert len(N2)==2 and T355 is not None
    totals={k:sum(x[k] for x in pre['cases']) for k in ['inputs','supported_direct_contexts','supported_birth_retained_contexts','missing_birth_GT_direct_contexts','missing_birth_GT_retained_contexts','baseline_supported_direct_losses','baseline_supported_retained_losses','variant_supported_direct_losses','variant_supported_retained_losses','baseline_removed_contexts','variant_removed_contexts']}
    assert totals['inputs']==2792
    if passed:assert totals['variant_supported_direct_losses']==totals['variant_supported_retained_losses']==0 and totals['baseline_supported_direct_losses']==1
    configs=p['configs'];assert sha(configs['baseline']['archive_path'])=='ef1965a5b09ec9324498643842badbcd972c48fb7c141770d7cce88fe6496208'
    with zipfile.ZipFile(configs['baseline']['archive_path']) as z:oldmembers={n:z.read(n) for n in z.namelist()}
    with zipfile.ZipFile(configs['variant']['archive_path']) as z:
        assert z.testzip() is None;newmembers={n:z.read(n) for n in z.namelist()}
    assert set(oldmembers)==set(newmembers) and {n for n in oldmembers if oldmembers[n]!=newmembers[n]}=={'retry/nominal238_base.py'}
    v=read(R/'project-effective-budget-v370.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1285867,1644,84000,0)
    cost=dict(stage=357,new_wrapper_actions=0,new_actor_act_calls=b['actor_act_calls'],new_actor_commit_calls=b.get('actor_commit_calls',0),actor_resets_on_saved_pixels=b['actor_resets'],actor_act_cap=3342,actor_reset_cap=12,new_environment_resets=0,new_standalone_routing_calls=0,new_learning_fits=0,new_paid_resources=0,covered_saved_input_contexts=2792,actually_paired_actor_input_contexts=1671 if passed else None,algebra_only_input_contexts=1121,standalone_metadata_preflight_updates=2792 if pre['passed'] else None,execution_wall_s=run['wall_s'],runner_CPU_s=run['runner_CPU_s'],actor_CPU_s=run['actor_CPU_s_known'],failed_preflight_wall_s=initial['wall_s'],failed_preflight_CPU_s=initial['runner_CPU_s'],failed_preflight_actor_calls=0,technical_recovery_extra_actor_calls=0,technical_setup_error_recovered_before_actors=True,policy_gate_failure=run['gate_failure'],closure_wall_s=time.perf_counter()-start,closure_CPU_s=time.process_time()-cpu,actual_cumulative_wrapper_actions=1285867,research_remaining=1644,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1371511,measurement_scope='Successfulcache runner includes supportpreflight/loading/hashing/IPC/journals. Failedzeroactorpathparserattempt separatelytimed; recovery staysoriginal3342/12cap. Artifactbuilding/coding/report/git/alltaskwall notfullytimed. Actorinternallyroutes; standalone routing calls0doesnotmean no internalrouting.')
    next_step=dict(status='Proposal only; notexecuted.',decision='Keep357as cache-qualifiedresearchvariant only, do notclaimactualcompletion/generalization or promote296. Lowclassificationitselfremains unchanged and genuine lowflagbirthcouldlaterbeexcludedasretained; knowncorpuspassing isnotocclusionproof.' if passed else 'Stopvariantwork without expandingchange/sweep. Preservecounterexample andsourcefailurerecords; only a separatelyscopednextminimalhypothesis mayfollow.',condition_priority_if_later_actual='T29511remains distinctunmeasuredregressioncondition before T2950gainretention. A futureactualtest must useexact357artifact/runtime andnewregisteredepisodebudget, no automatic355rerun.',normal_episode_cap=2000,current_research=1644,minimum_additional_if_full_normal_episode_requested=356,final_reserve=84000,new_native_authorized_now=0)
    report=dict(stage=357,passed_cached_gate=passed,error=run['error'],variant_archive_sha256=configs['variant']['archive_sha256'],unmodified349_archive_sha256=configs['baseline']['archive_sha256'],single_policy_change='Preserveallcurrentdirectage0routingpoints; applyexistinglowlineagefilteronlytoage>0retainedpoints. Exactlynominal238_base.pychanged; otherarchivebytes/modelparameters/metadata/tracker unchanged.',common_observer='Samepassiveactual-subsetrecorderbotharms, no policyselection. Baselinehistoricalreproduction qualifiesthismeasurementchange.',support_audit=dict(totals=totals,cases=pre['cases'],label_definition='Birthpointwithinexactlyonecapturedfixturecircle; retainedlabelpropagatedfrombirth. MissingbirthGTcontexts remainunknown. Countsarepointcontexts, notindependentobjects/trials.',gate='No knownfixture-supported currentdirect orbirth-supportedretained UID actuallyexcluded. Lowflagaloneisnotexclusionunderageguard; old342evaluatorassumption separatedwithoutrelaxingroutingpreservationrequirement.'),T2954_counterexample=T355,N2_retained_effect=N2,actual_actor_pairs=pairs,algebra_only_cases=[x for x in pre['cases'] if not x['actor_replay_planned']],
        limitations=['No newworld/simulation/learning. Allactorresultsarefixedstoredpixelreplays withownreturnedcommands/normalmemory, notactualcompleteepisodes. Historical355T2954finishbelongs349, not a new357completion.',
        'Six zero-lowbirthtrajectories1121inputs arecoveredbycurrentrule/tracker/sourceinduction, not actorreplays. Six pairedtrajectories1671inputs haveactualnewactoroutputs. Do notmix theseevidence types.',
        'O2cachedsourcepixels were generated underanotherpolicy. Any146path/controlchangefrom protecting a fresh point is reported, not claimed as actualavoidance/regression.',
        'KnownGTsupportgate passed only on availablelabels; missingbirthGT/material/visibility/occlusionunknown. Supportedretainedpoints could fail onnewdata; do notgeneralize.',
        'Independentobservationsarenotindependenttrials: N2trajectoriesshareprefixes. Preserve existing334mixedaggregate evidence and296champion.'],technical_recovery=dict(kind='Hostpathstr-to-Pathadapterbeforefirstactor',original_failure_preserved=True,failed_actor_act_reset_native_calls=0,original_runner_andpolicyartifacts_unchanged=True,recovery_within_original_caps=True),cost=cost,next_step=next_step,promotion=False,champion296_preserved=True,new_protected_split_opened=False,new_actual_completion_claim=False)
    save(D/'cost.json',cost);save(D/'summary-private.json',report);save(G/'retry/guard357_result.json',report);save(D/'final-report-verification.json',dict(passed=passed,actor_calls=b['actor_act_calls'],commit_calls=b.get('actor_commit_calls',0),savedpixel_resets=b['actor_resets'],all12trajectories_covered=True,T2954knownsupportcounterexample_resolved=passed,N2criticalretainedeffect_preserved=passed,new_native=0,new_learning=0,original349_preserved=True,variant_only_one_policy_selection_changed=True,research_remaining=1644,final_reserve=84000,no_actualcompletionorgeneralization_claim=True))
    assert sha(R/'stage296/champion-manifest.json')=='b92fe5307a491bfb9d1f5081bf97c9c1d4646dcf9c8511fb169bc48c8f9349e5'
    for name in ['DEV','screen-opening.json','DEV-opened-by309.json']:assert not (R/'stage297'/name).exists()
    v.update(version=371,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v370.json'),prior_budget_sha256=sha(R/'project-effective-budget-v370.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,stage357_new_wrapper_actions=0);assert not (R/'project-effective-budget-v371.json').exists();save(R/'project-effective-budget-v371.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==357 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(dict(passed=passed,variant_sha256=configs['variant']['archive_sha256'],support_totals=totals,T2954=T355,pairs=pairs,N2=N2,cost=cost)),flush=True)


if __name__=='__main__':close(Path(sys.argv[1]).resolve())
