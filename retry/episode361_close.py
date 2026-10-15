"""Close one frozen357 T2950 run, with independent official/support gates."""
import datetime
import json
from pathlib import Path
import sys
import numpy as np
from retry.path271_run import read,save,sha
from retry.episode361_stage import G
from retry.pair343_close import describe
from retry.confidence341_run import label
from retry.lineage354 import safe

def rows(path):return [json.loads(x) for x in Path(path).read_text().splitlines()]

def close(R):
    D=R/'stage361';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    assert not (D/'cost.json').exists();r=read(D/'B/result.json');data=rows(D/'B/trace-private.jsonl');b=read(D/'native-budget.json');z=np.load(D/'B/frames-actions-private.npz');used=b['actions']
    assert r['technical_error'] is None and r['comparison_valid'] and read(D/'reset-qualification.json')['passed']
    assert used==r['native_actions']==len(data)==len(z['actions'])==b['actor_act_calls']==b['actor_commit_calls']<=1725 and len(z['frames_uint8'])==used+1 and b['resets']==b['actor_resets']==1
    assert sum(x['raw_ticks'] for x in data)==r['raw_step_ticks']==r['raw_counter_at_stop']-50 and r['raw_reset_ticks']==51
    assert all(not x['terminated'] and not x['truncated'] for x in data[:-1]) and r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent']
    for x in data:
        assert x['executed']==x['returned_action'] and x['nominal_memory']==x['policy']['previous_steer'] and np.float32(x['nominal_memory'])==np.float32(x['executed'][0]) and len(x['raw_observations'])==x['raw_ticks']
        e=x['routing_evidence'];assert e['full_hazards']==x['tracker']['after'] and x['features'][11]==len(e['full_hazards'])
        assert e['removed_indices']==[j for j,(h,item) in enumerate(zip(x['tracker']['after'],x['support_record']['after'])) if item['low'] and h[3]>0]
    if r['completed']:assert not r['actual_DNF'] and not r['censored'] and r['stop_reason']=='official_finish' and r['lap_ms']==round((r['finish']['finish_time_s']-r['postreset_start_time'])*1000)
    if r['protocol_stop']:assert used==1725 and r['censored'] and not r['actual_DNF'] and not r['completed']
    births={};direct=retained=missing_direct=missing_retained=0;losses=[];lowbirths=[];protected=[];held=[]
    for x in data:
        for item in x['support_record']['births']:
            lab,idx=label(item['point'],x['pre_physical']);births[tuple(item['uid'])]=dict(label=lab,fixture_index=idx)
            if item['low']:lowbirths.append(dict(action=x['step'],uid=item['uid'],area_pixels=item['component_area'],label=lab))
        for j,(h,item) in enumerate(zip(x['tracker']['after'],x['support_record']['after'])):
            lab=births[tuple(item['uid'])]['label'];age=h[3];excluded=j in x['routing_evidence']['removed_indices']
            if lab=='fixture_supported':
                if age==0:direct+=1
                else:retained+=1
                if excluded:losses.append(dict(action=x['step'],uid=item['uid'],age=age,kind='direct' if age==0 else 'birth_supported_retained'))
            if lab=='missing_GT':
                if age==0:missing_direct+=1
                else:missing_retained+=1
            if age==0:assert not excluded
            if item['low'] and age==0:protected.append(x['step'])
            if excluded:held.append(dict(action=x['step'],uid=item['uid'],age=age))
    br=read(R/'stage295/TRAIN/T2950/g1p4/result.json');cr=read(R/'stage330/evaluation/T2950/result.json');assert p['historical']['baseline296']==safe(br) and p['historical']['H1_330']==safe(cr)
    v=read(R/'project-effective-budget-v375.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'],v['B_operating_cap'])==(1286717,1725,84000,0,1372442)
    measures=['wall_s','runner_CPU_s','actor_CPU_s','reset_wall_s','raw_step_render_wall_s','raw_contact_observer_wall_s','capture_wall_s','journal_wall_s','artifact_wall_s']
    cost=dict(stage=361,new_wrapper_actions=used,new_candidate_runs=1,new_baseline_runs=0,new_environment_resets=1,new_actor_act_calls=b['actor_act_calls'],new_actor_commit_calls=b['actor_commit_calls'],actor_resets=1,new_cached_actor_calls=0,new_native_auxiliary=0,native_cap=1725,additional_research_registered_before_native=0,raw_step_ticks=r['raw_step_ticks'],raw_reset_ticks=51,new_source_physics_rollout_ticks=0,new_learning_fits=0,new_tuning=0,new_paid_resources=0,technical_error=None,technical_recovery_native=0,measurements={k:r[k] for k in measures},actual_cumulative_wrapper_actions=1286717+used,research_remaining=1725-used,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1372442,unused_registered_native=1725-used,historical_results_not_recounted=True,measurement_scope='Only361freshactualepisode; no newcontrol/cache/auxiliaryphysics. Rawstep includesrender; contact/capture/journal/artifact timers distinct. Registration/coding/closure/git/taskwall notfullytimed.')
    audit=dict(known_supported_direct_contexts=direct,known_birth_supported_retained_contexts=retained,supported_direct_losses=sum(x['kind']=='direct' for x in losses),supported_retained_losses=sum(x['kind']=='birth_supported_retained' for x in losses),losses=losses,missing_birth_GT_direct=missing_direct,missing_birth_GT_retained=missing_retained,low_births=lowbirths,protected_current_direct_actions=protected,retained_exclusions=held,gate_passed=not losses,scope='Birthcirclecorrespondencecomputedafterepisode, notsemanticmaterial/occlusiontruth. Initialidentity/read-onlycapture didnotenteractorcontrols. MissingGTreportedseparately.')
    report=dict(stage=361,case_key='T2950',official_outcome=describe(data,r),stop_reason=r['stop_reason'],technical_error=r['technical_error'],candidate_modified=False,candidate_archive_sha256=p['config']['archive_sha256'],candidate_worker_sha256=p['config']['worker_sha256'],fresh_reset_qualified=True,ownobservations_fullcontrols_normalmemory=True,historical_comparison=dict(baseline296=safe(br),H1_330=safe(cr),same_case_verified=True,reused_not_new=True,new_minus_historical296_lap_ms=r['lap_ms']-br['lap_ms'] if r['completed'] and br['completed'] else None,new_minus_historical330_lap_ms=r['lap_ms']-cr['lap_ms'] if r['completed'] and cr['completed'] else None,scope='Historicaldifferentpolicies, notfreshpairedcontrol orisolatedguard/filter/fallbackeffect. No matchedhistoricalstate/RNGprefixclaim; observerRNGfixednew361 and historical330seednotrecorded.'),support_audit=audit,finish=dict(qualification_raw_time_s=r['finish']['finish_qualified_time_s'],center_crossing_raw_time_s=r['finish']['finish_time_s'],declaration_raw_time_s=r['finish']['raw_time'],postreset_start_time_s=r['postreset_start_time'],official_lap_ms=r['lap_ms']),cost=cost,promotion=False,champion296_preserved=True,new_DEV_opening=False,new_HOLDOUT_opening=False,new_SEALED_opening=False,limits=['SingleknownTRAINcondition; N2/O2successdoesnotimplythisconditionorgeneralization. No automaticcandidatepromotion.', 'Officialcompletionandgeometricpreservationgate are separate. Anyknownsupportedwithheld pointfailsgate evenwithfinish; retainedlowpointsundernewocclusion remainunproven.', 'Current357differsfrom330by334fallbackand342filterplusage0guard. Cannotattributetrajectoryoutcomes solelytoonechange;296isalsoanotherpolicy.', 'Hidden solver/OpenCV RNG/warmstart/islandstate notdirectlycaptured. No newcontrol/retry/extraarm/tuning, paidresources orprotectedcaseopening.'],next_step='Preserve frozen357 andthiscondition-specific outcome; no automaticexperiment,extension,tuning orpromotion.',authorization_end_utc=p['deadline_utc'])
    measured=[]
    for stage,key in [(358,'O2'),(359,'N2'),(360,'T29511'),(361,'T2950')]:
        pp=read(R/f'stage{stage}/plan.json');rr=read(R/f'stage{stage}/B/result.json');assert pp['config']['archive_sha256']==p['config']['archive_sha256'] and pp['case']==read(R/'stage330/plan.json')['cases'][key]
        measured.append(dict(condition=key,source_stage=stage,completed=rr['completed'],actual_DNF=rr['actual_DNF'],censored=rr['censored'],native_actions=rr['native_actions'],lap_ms=rr['lap_ms'],damage=rr['damage'],visited=rr['unique_tiles'],total_tiles=rr['total_tiles']))
    known=read(R/'stage330/plan.json')['roads'];unmeasured=[key for key in known if key not in {x['condition'] for x in measured}];assert len(known)==18 and len(unmeasured)==14
    report['actual357_coverage']=dict(known_conditions=18,actual_measured=measured,not_yet_actual_measured=unmeasured,scope='Onlyfouractual357conditions, not18conditionbenchmarkorunbiasedsuccessestimate. Historical349T2954andO0and357cachedreplays arenotactual357episodes.')
    report['proposed_next_scope']=dict(status='proposalonly_noexecution_orreservation',first='T2954actual357: prior355freshsupportedpoint92was349,357onlycached356inputreplay; testguardinownclosedloopandposthocsupport.',second='O0actual357: historical349completionexistsbut357onlycachedreplay, then remainingknownTRAIN/Nconditions withfixedcandidateandconditionbudgetbeforeeachrun.',stops='Anyknownsupportedloss stopsqualification; no tuningorautomaticextension. ProtectedDEV/HOLDOUT/SEALEDstayclosed; no promotion fromselectedknowncases.',budget='Existingremainingresearchonlyunlessseparatelyauthorized;reserve84000untouched. Registercapsbeforeanynextreset.')
    assert sha(R/'stage296/submission296.zip')=='0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937' and sha(R/'stage296/champion-manifest.json')=='b92fe5307a491bfb9d1f5081bf97c9c1d4646dcf9c8511fb169bc48c8f9349e5'
    for name in ['DEV','screen-opening.json','DEV-opened-by309.json']:assert not (R/'stage297'/name).exists()
    save(D/'cost.json',cost);save(D/'summary-private.json',report);save(G/'retry/episode361_result.json',report);save(D/'final-report-verification.json',dict(passed=True,onefreshcandidate=True,official_finish=r['completed'],native_actions=used,support_gate_passed=not losses,support_losses_recorded=len(losses),candidate_unchanged=True,historical_notneworrecounted=True,research_remaining=1725-used,final_reserve=84000,no_promotion_or_newprotected_split=True))
    v.update(version=376,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v375.json'),prior_budget_sha256=sha(R/'project-effective-budget-v375.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage361_new_wrapper_actions=used);assert not (R/'project-effective-budget-v376.json').exists();save(R/'project-effective-budget-v376.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==361 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(dict(outcome=report['official_outcome'],audit=audit,cost=cost)),flush=True)
if __name__=='__main__':close(Path(sys.argv[1]).resolve())
