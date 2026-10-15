"""Close feasibility and posthoc fixture-support falsification separately."""
import datetime
import json
from pathlib import Path
import sys
import numpy as np
from retry.path271_run import read,save,sha
from retry.package349_run import rows
from retry.episode355_stage import G
from retry.pair343_close import describe
from retry.confidence341_run import label,centers,polyline_distance


def close(R):
    D=R/'stage355';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    assert not (D/'cost.json').exists();r=read(D/'B/result.json');data=rows(D/'B/trace-private.jsonl');z=np.load(D/'B/frames-actions-private.npz');b=read(D/'native-budget.json');used=b['actions']
    assert r['technical_error'] is None and r['comparison_valid'] and read(D/'reset-qualification.json')['passed'];assert used==r['native_actions']==len(data)==len(z['actions'])==b['actor_act_calls']<=2000 and len(z['frames_uint8'])==used+1 and b['resets']==b['actor_resets']==1
    assert sum(x['raw_ticks'] for x in data)==r['raw_step_ticks']==r['raw_counter_at_stop']-50 and r['raw_reset_ticks']==51;assert all(not x['terminated'] and not x['truncated'] for x in data[:-1]);assert r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent']
    for x in data:
        assert x['executed']==x['returned_action'] and x['nominal_memory']==x['policy']['previous_steer'] and np.float32(x['nominal_memory'])==np.float32(x['executed'][0]);assert len(x['raw_observations'])==x['raw_ticks'];e=x['routing_evidence'];assert e['full_hazards']==x['tracker']['after'] and x['features'][11]==len(e['full_hazards'])
    if r['completed']:assert r['stop_reason']=='official_finish' and not r['actual_DNF'] and not r['censored'] and not r['protocol_stop'] and r['lap_ms']==round((r['finish']['finish_time_s']-r['postreset_start_time'])*1000)
    if r['protocol_stop']:assert used==2000 and r['censored'] and not r['completed'] and not r['actual_DNF']
    outcome=describe(data,r);birth_labels={};births=[];held=[];losses=[]
    for x in data:
        for item in x['support_record']['births']:
            lab,identity=label(item['point'],x['pre_physical']);birth_labels[tuple(item['uid'])]=dict(label=lab,fixture_index=identity)
            if item['low']:births.append(dict(action=x['step'],direct_index=item['uid'][1],area_pixels=item['component_area'],raw_road_neighbors=item['raw_road_neighbors'],posthoc_geometric_label=lab,fixture_index=identity))
        for item in x['routing_evidence']['removed_evidence']:
            held.append(dict(action=x['step'],uid=item['uid']))
            lab=birth_labels[tuple(item['uid'])]
            if lab['label']=='fixture_supported':
                idx=lab['fixture_index'];d=float(np.linalg.norm(np.asarray(item['point'][:2])-centers(x['pre_physical'])[idx]));radius=x['pre_physical']['obstacles'][idx]['fixture']['radius']
                losses.append(dict(action=x['step'],uid=item['uid'],fixture_index=idx,birth_point_to_fixture_center_m=d,fixture_radius_m=radius,selected_path_center_distance_at_birth_m=polyline_distance(x['pixel_path'],item['point'][:2]),full_tracker_point_preserved=True,scope='Birthpointgeometricallysupported bycapturedfixture; not semanticpixelmaterialorvisibilitygroundtruth. Selectedpathdistance descriptive, not counterfactualrouteeffect.'))
    local=[]
    if losses:
        first=losses[0]['action']
        for step in range(max(1,first-1),min(len(data),first+2)+1):
            x=data[step-1]
            for item in x['support_record']['births']:
                lab,idx=label(item['point'],x['pre_physical']);local.append(dict(action=step,uid=item['uid'],area_pixels=item['component_area'],raw_road_neighbors=item['raw_road_neighbors'],low=item['low'],posthoc_geometric_label=lab,fixture_index=idx))
    v=read(R/'project-effective-budget-v368.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'],v['B_operating_cap'])==(1285511,2000,84000,0,1371511);assert read(D/'budget-extension.json')['additional_research_actions']==1468
    measures=['wall_s','runner_CPU_s','actor_CPU_s','reset_wall_s','raw_step_render_wall_s','raw_contact_observer_wall_s','capture_wall_s','journal_wall_s','artifact_wall_s']
    cost=dict(stage=355,new_wrapper_actions=used,new_candidate_runs=1,new_baseline_runs=0,new_environment_resets=1,actual_actor_calls=b['actor_act_calls'],actual_actor_resets=1,new_cached_actor_calls=0,new_native_auxiliary=0,total_native_cap=2000,additional_research_registered_before_native=1468,raw_step_ticks=r['raw_step_ticks'],raw_reset_ticks=51,new_source_physics_rollout_ticks=0,new_learning_fits=0,new_tuning=0,new_paid_resources=0,technical_error=None,technical_recovery_native=0,measurements={k:r[k] for k in measures},actual_cumulative_wrapper_actions=1285511+used,research_remaining=2000-used,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1371511,unused_registered_native=2000-used,historical_results_charged_again=False,measurement_scope='Only355freshactualepisode charged; allprefix/capturewithinthisrun, no cacheorauxiliaryphysics. Rawstep includesrender; read-onlyGT/contact/capture/journal/artifactseparatetimers. Preparation/coding/closure/git/taskwall notfullytimed.')
    baseline=read(R/'stage295/TRAIN/T2954/g1p4/result.json');old330=read(R/'stage330/evaluation/T2954/result.json');historical=dict(baseline296=dict(completed=baseline['completed'],native_actions=baseline['native_actions'],lap_ms=baseline['lap_ms'],damage=baseline['damage'],visited=baseline['visited'],total_tiles=baseline['total_tiles']),H1_330=dict(completed=old330['completed'],actual_DNF=old330['actual_DNF'],native_actions=old330['native_actions'],retire_reason=old330['retire_reason'],visited=old330['visited'],total_tiles=old330['total_tiles'],damage=old330['damage']),reference_lap_difference_from296_ms=r['lap_ms']-baseline['lap_ms'] if r['completed'] and baseline['completed'] else None,not_new_or_recounted=True,scope='Knownsamecasehistoricalcontext, notfreshpairedcausaleffect.349versus330includes334fallbackand342filter;296is anotherpolicy. No qualifiedcurrent334T2954actualarm ormatchedhistoricalactor/physics/RNGprefix exists.')
    assessment=dict(official_feasibility='confirmed' if r['completed'] else 'not_confirmed',fixture_supported_footprint_preservation='falsified_on_this_record' if losses else 'no_counterexample_observed_not_general_safety',fixture_supported_withheld_count=len(losses),promotion=False,
        meaning='Completionandnocollision do not rescue the rulepreservation premise. Atleastone zero-ringbirthgeometricallysupportedbyrealfixture waswithheldfromhardrouting. Fullhazards remainedtracked andused bynear/count/min-distance, so this isnotcompleteobstacledeletion. No counterfactualcontrol/harmcausality ismeasured.' if losses else 'No semantic/occlusion safetyclaim fromoneknowncondition.')
    next_decision=dict(status='Proposed only, not executed.',decision='Pause broader rulequalification/promotion and furtheractualcandidateexpansion because the supported-footprint preservation premise failed. Preserve exactcandidate andallofficialoutcomes; no adhocthresholdrepair. Ifneeded, nextstep is a separatelyscopednative0review of92sourceassociation/pixelboundary andstoredroutingrelevance, withnopolicy/physicsreplayunlessregistered.',unresolved_conditions=['T29511','T2950 gain retention'],condition_priority_scope='354conditionpriorityremainscontext, not authorization to skip the newpreservationcounterexample or launch additional episodes.',new_native_cap=0,new_actor_calls_authorized=0,champion296_unchanged=True,final_reserve=84000)
    next_decision['minimum_diagnostic_proposal']=dict(status='notexecuted',input='Saved355action92only, identicalpixels/speed/priorsteer andallremaininghazards.',variants='Reproduce actualfilteredroute/target first, thenrestore only92:0footprint.',direct_routing_calls_cap=2,direct_target_calls_cap=2,actor_calls=0,native_actions=0,stop='Anyoriginalroute/targetreproductionmismatch stops. No extraframe/fit/tuning/controllercall.',interpretation='Isolatesdirectroutingrelevance ofthesupportedfootprint. Evenanunchangedroute wouldnoterase the no-supported-exclusion gatecounterexample; no fullcontrol/trajectoryharmclaim.')
    report=dict(stage=355,official_outcome=outcome,stop_reason=r['stop_reason'],technical_error=r['technical_error'],candidate_modified=False,candidate_archive_sha256=p['config']['archive_sha256'],candidate_worker_sha256=p['config']['worker_sha256'],fresh_reset_qualification=True,no_historical_forced_prefix=True,
        finish=dict(qualification_raw_time_s=r['finish']['finish_qualified_time_s'],center_crossing_raw_time_s=r['finish']['finish_time_s'],declaration_raw_time_s=r['finish']['raw_time'],postreset_start_time_s=r['postreset_start_time'],lap_ms=r['lap_ms']),historical_comparison=historical,posthoc_rule_audit=dict(low_births=births,held_actions=sorted({x['action'] for x in held}),fixture_supported_withheld=losses,local_birth_context=local,support_labels_computed_only_after_episode=True,GT_capture_scope='Readonlyevaluatorcaptureandinitialidentitygate duringrun; noGTtoactororcontrol. Geometryassociation/labelinterpretationonlyafterepisode.',semantic_material_or_actual_occlusion_verified=False),assessment=assessment,
        limits=['SinglepreviouslyobservedTRAINcase, notgeneralization orchampionpromotion. Now349actualcoverageN2/O0/O2/T2954only; other14conditions remainunmeasured, do notclaim an18conditioncount.',
        'Newofficialfinish is distinct fromfulltileprogress; historical330T2954had357/357andDNF. No historicalresultrelabelled, nofreshbaseline/isolated342effect.',
        'Fixture-supportedmeanscapturedcirclecorrespondence; do notconvertgeometriclabelintoauthoritativesemanticorocclusiontruth. The counterexampleinvalidates the conservative no-supported-exclusion gate regardlessofobservednocontact.',
        'Hidden solver/OpenCV RNG and omittedwarmstart/contactislandstate notdirectlycaptured. Noextraarm/retry/tuning/learning ornewprotectedsplit.'],cost=cost,next_decision=next_decision,champion296_preserved=True,new_HOLDOUT_opening=False,new_SEALED_opening=False,promotion=False,authorization_end_utc=p['deadline_utc'])
    assert sha(R/'stage296/submission296.zip')=='0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937' and sha(R/'stage296/champion-manifest.json')=='b92fe5307a491bfb9d1f5081bf97c9c1d4646dcf9c8511fb169bc48c8f9349e5'
    for name in ['DEV','screen-opening.json','DEV-opened-by309.json']:assert not (R/'stage297'/name).exists()
    save(D/'cost.json',cost);save(D/'summary-private.json',report);save(G/'retry/episode355_result.json',report);save(D/'final-report-verification.json',dict(passed=True,technical_error=None,onefreshcandidateepisode=True,official_finish=r['completed'],actualnative=used,GT_posthoc_only=True,supported_footprint_preservation_gate_passed=not losses,counterexample_recorded_not_hidden=bool(losses),candidate_andworker_unchanged=True,historical_results_not_neworrecounted=True,research_remaining=2000-used,final_reserve=84000,next_experiment_not_executed=True))
    v.update(version=369,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v368.json'),prior_budget_sha256=sha(R/'project-effective-budget-v368.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage355_new_wrapper_actions=used);assert not (R/'project-effective-budget-v369.json').exists();save(R/'project-effective-budget-v369.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==355 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(dict(outcome=outcome,assessment=assessment,supported_counterexamples=losses,cost=cost)),flush=True)


if __name__=='__main__':close(Path(sys.argv[1]).resolve())
