"""Close the native-zero audit; publish only aggregate diagnostic evidence."""
import argparse
import datetime
import json
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.lineage339_stage import verify


def changed(records,mode,key,stage):return [r['step'] for r in records if r['stage']==stage and r['variants'][mode][key]]


def close(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage339';p=verify(R,True);assert not (D/'cost.json').exists();audit=read(D/'audit-private.json');context=read(D/'context-private.json')
    receipts=[read(D/name) for name in ['reproduction-receipt.json','diagnostic-receipt.json','selection-repair-receipt.json','routing-only-receipt.json']];assert all(r['passed'] for r in receipts)
    failed=read(D/'selection-repair-first-failure.json');strict=context['strict_routing_comparisons'];full=audit['comparisons'];assert len(strict)==len(full)==18
    for stage in [337,338]:
        for record in read(D/f'routing-only/{stage}/probes-private.json'):
            base=record['probe']['variants']['original'];assert record['probe']['state_preserved']
            for mode in ['drop_birth121','drop_birth124']:
                v=record['probe']['variants'][mode];removed=[h for h in base['hazards'] if h not in v['hazards']]
                assert len(removed)<=1
                if removed:assert record['step']-removed[0][3]==int(mode.split('birth')[1])
                if record['step']==124:assert len(removed)==1 and removed[0]!=base['hazards'][-1]
            assert record['probe']['variants']['drop_birth121']['action']==record['probe']['variants']['current_only']['action']
        for mode in ['drop_birth121','current_only']:
            assert changed(strict,mode,'path_changed',stage)==[127,128,129]
            assert changed(strict,mode,'steering_changed',stage)==[128,129]
            assert changed(strict,mode,'pedals_changed',stage)==[127,128,129]
        assert not any(changed(strict,'drop_birth124',key,stage) for key in ['candidates_changed','path_changed','target_changed','steering_changed','pedals_changed'])
    for field in ['new_native_actions','new_environment_resets','new_source_physics_ticks','new_learning_fits']:
        assert all(r[field]==0 for r in receipts)
    budget_path=R/'project-effective-budget-v350.json';budget=read(budget_path)
    assert budget['actual_cumulative_wrapper_actions']==1282569 and budget['research_remaining']==1669 and budget['final_reserved_actions']==84000 and budget['final_reserve_used']==0
    assert sha(R/'stage296/champion-manifest.json')=='b92fe5307a491bfb9d1f5081bf97c9c1d4646dcf9c8511fb169bc48c8f9349e5'
    assert sha(R/'stage296/submission296.zip')=='0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937'
    for name in ['DEV','screen-opening.json','DEV-opened-by309.json']:assert not (R/'stage297'/name).exists()
    audit_costs=[read(D/'audit-initial-invalid.json')['cost'],audit['cost'],context['cost']]
    cost=dict(stage=339,new_wrapper_actions=0,new_native_actions=0,new_environment_resets=0,new_source_physics_ticks=0,new_learning_fits=0,new_paid_resources=0,
        cached_actor_calls=sum(r['cached_actor_calls'] for r in receipts)+failed['cached_actor_calls'],
        clone_act_calls=sum(r['clone_act_calls'] for r in receipts)+failed['clone_act_calls'],
        pure_clone_routing_calls=sum(r['pure_routing_calls'] for r in receipts)+failed['pure_routing_calls'],
        actor_resets_on_saved_pixels=sum(r['actor_resets'] for r in receipts)+failed['actor_resets'],
        measured_successful_actor_CPU_s=sum(r['actor_CPU_s'] for r in receipts),failed_repair_actor_CPU_s=None,
        measured_operation_wall_s=sum(r['wall_s'] for r in receipts)+sum(r['wall_s'] for r in audit_costs),
        measured_runner_CPU_s=sum(r['runner_CPU_s'] for r in receipts)+sum(r['runner_CPU_s'] for r in audit_costs),
        measurement_limit='Failed selector repair124acts+4clones included in call counts but no CPU receipt; CPU/wall totals exclude that failed process and setup/coding/inspection/reporting/closure. Not total task wall or simulator cost.',
        actual_cumulative_wrapper_actions=1282569,research_remaining=1669,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1368238)
    assert cost['cached_actor_calls']==1269 and cost['clone_act_calls']==156 and cost['actor_resets_on_saved_pixels']==9
    save(D/'cost.json',cost)
    timelines={}
    for stage in [337,338]:
        timelines[str(stage)]={mode:{key:changed(strict,mode,key,stage) for key in ['candidates_changed','path_changed','target_changed','steering_changed','pedals_changed']} for mode in ['drop_birth121','drop_birth124','current_only']}
    full_summary={mode:{key:sorted(set(r['step'] for r in full if r['variants'][mode][key])) for key in ['path_changed','steering_changed','pedals_changed']} for mode in ['drop_birth121','drop_birth124','current_only']}
    birth_summary=[]
    for tag in ['121:0','124:0']:
        b=audit['data']['337']['births'][tag];l=[x for x in context['data']['337']['lineages'] if x['tag']==tag][0]
        birth_summary.append(dict(birth_action=b['step'],direct_index=b['direct_index'],component_area_pixels=b['component']['area'],upper_boundary=True,HUD=False,
            nearest_captured_fixture_center_distance_at_birth_m=b['nearest_GT_distance_m'],nearest_projected_fixture_center_error_at_birth_px=b['nearest_projected_center_error_px'],
            world_stationarity_drift_max_through128_m=l['maximum_world_drift_through128_m'],
            lifetime_last_action=129 if tag=='121:0' else 132,expired_action=130 if tag=='121:0' else 133,
            interpretation='Unresolved birth; saved grayscale appearance/source palette suggests road-border aliasing for121 or road/grass boundary for124. Not a semantic false-positive label from GT distance alone.'))
    next_pair=dict(status='Proposal only; not executed or reserved',new_native_actions_cap=233,new_A_runs=0,new_B_runs=1,additional_budget_needed=0,research_remaining_after_maximum=1436,final_reserve_used=0,
        A='Reuse qualified actual337, same N2; do not rerun.',
        B='Same reset and exact original prefix1-126. One change: exclude only the121:0 lineage from connected_route input while it exists, starting at127; preserve tracker, current detections, dedup/age/expiry, near scheduling and hazard count/min-distance features. Track birth/direct-index metadata, no GT rule. Use modified frozen pipeline own returned controls and own nominal memory on its subsequent observations, no stored continuation.',
        preconditions='Native0 verify boundary first; float32 earliest full-control difference is127 via path-length pedal feature, steering first differs128. Exact prefix126 pixels/actions/actor/tracker/memory/captured physics/accessRNG; original frozen outputs reproduced, real current obstacle remains; no magnitude-selected129probe.',
        estimated_offline_verification_act_calls=132,maximum_B_actor_act_calls=233,new_environment_resets_cap=1,maximum_postreset_raw_ticks=932,reset_raw_ticks_expected=51,
        stops='Official terminal, any qualification mismatch,233actions or authorization deadline. No implicit extra A/retry/grant.233 survival without finish is protocol censor, not completion.',
        registered_outcomes='Jointly compare first contact fixture/time, endpoint touching duration, unique-tile growth past132, speed and official retirement. Damage reduction alone is insufficient. Same blockage/retirement rejects only persistent routing-removal sufficiency. Better local progress supports a routing contribution, not detector semantics, completion or generalization.',
        identification_limit='Birth appearance plus small pre128world drift separates available evidence for birth ambiguity vs large propagation error. This pair tests persistent routing influence on actual motion; failure does not prove target-following/lookahead/speed is the cause, and one pair cannot uniquely identify all three mechanisms.')
    public=dict(stage=339,native_zero=True,verification=dict(all_recorded337_inputs=233,all_recorded338_inputs=136,all_outputs_features_tracker_path_audit_full_state_nominal_memory_exact=True,original_clone_outputs_exact=True,one_lineage_only_final=True,live_actor_state_preserved=True,strict_routing_boundary_verified=True,all_tracker_updates_and_detector_outputs_reconstructed=369,maximum_tracker_reconstruction_error=0.0),
        births=birth_summary,contact_object_correspondence=dict(physical_object_index=2,real_detection_birth=123,real_birth_center_error_m=audit['data']['337']['births']['123:0']['nearest_GT_distance_m'],direct_detection_metric_error_range_m=[min(q['metric_error_m'] for d in context['data'].values() for q in d['current_contact_object_correspondence']),max(q['metric_error_m'] for d in context['data'].values() for q in d['current_contact_object_correspondence'])],direct_projection_centroid_error_max_px=max(q['projection_centroid_error_px'] for d in context['data'].values() for q in d['current_contact_object_correspondence'])),
        source_lineage=dict(optical_accepted_approach_actions=list(range(124,133)),birth121_optical_reason='no_hazards',actual_obstacle_direct_replacement_distance_range_m=[.013102102161224375,1.0456659846076517],dedup_rule='Delete predicted points within2m of each fresh detection, then append fresh age0; no persistent object-ID association.',expiry_rule='Previous age<8 permits output age8; next update expires. Birth121expires130, birth124expires133. Birth append has no35mspatial gate; real birth123also enters at top boundary.',failure_reason_at133='rejected_or_unavailable; finer point/status/candidate failure reason not captured. Both unresolved tags already reach expiry.',metric_projection='Analytic pixel-center map derived from source camera/flip and96to84resize; no calibration fit. Full pixel/input replay exact; rasterization/filtering centroid uncertainty remains.'),
        strict_routing_timelines=timelines,full_hazard_removal_comparator=full_summary,
        findings=['121lineage changes routing candidate/path at127-129, target/float32steer at128-129;127path length alone changes frozen pedal output.124-126and130-132 routing-only outputs unchanged.',
                  '124lineage changes no routing candidate/path/target/control in124-132. Removing it from all hazard-derived features changes count and pedals; therefore routing-no-effect is not whole-policy-no-effect.',
                  'Current-only routing matches121-only removal actions on all18fixed-scenes. Full-hazard removal changes different metadata and is kept separate.',
                  'Birth121 already7.27mfromfixture while pre128world drift only.063m. Temporal retention preserves this input until age expiry; no semantic object-ID/occlusion proof.'],
        limits=['Postselected existing TRAIN N2 only.337/338share inputs through128, so eighteen scenes are not eighteen independent trials. No real trajectory counterfactual, completion improvement or promotion.',
                'Saved grayscale lacks RGB/semantic material labels. Bright grass gray177and obstacle173both satisfy detector band; birth121looksnearstripedroadborder,124neargrassboundary, HUDgeometricallyexcluded. Exact rendered origin remains unresolved.',
                'GT diagnostic only; rawpose/pixels/models/seeds and private documents not public. Distance alone does not label false detection; real contact object is accurately registered in the same frames.',
                'Curved avoidance near-path/far-target angle can be normal; no controller/lookahead defect established. Actual occlusion preservation remains unverified.'],
        technical_recovery=dict(registration_inventory_fixed_before_actor_launch=True,initial_same_birth_step_filter_removed_two_points_at124=True,initial124drop_comparisons_invalidated=True,first_tuple_list_repair_failed_exactly_one_assertion=True,failed_attempts_preserved_and_counted=True,final_birth_plus_direct_index_selector_verified=True,strict_routing_only_reported_separately_from_full_hazard_removal=True),
        preserved334_mixed_evidence=read(R/'stage338/summary-private.json')['preserved334_mixed_evidence'],actual_occlusion_preservation_verified=False,
        cost=cost,next_minimum_paired_proposal=next_pair,champion296_preserved=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,authorization_end_utc=p['deadline_utc'])
    save(D/'summary-private.json',public);save(G/'retry/lineage339_result.json',public)
    verification=dict(passed=True,new_native_actions=0,all_recorded_outputs_exact=True,one_UID_removed_per_drop=True,real_current_obstacle_preserved=True,strict_features_3_4_7_8_11_12_fixed=True,no_live_state_pollution=True,original_input_hashes_preserved_with_documented_source_repair=True,protected_splits_unopened=True,champion296_preserved=True,next_pair_not_executed=True)
    save(D/'final-saved-evidence-check.json',verification)
    budget.update(version=351,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(budget_path),prior_budget_sha256=sha(budget_path),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,stage339_new_wrapper_actions=0)
    assert not (R/'project-effective-budget-v351.json').exists();save(R/'project-effective-budget-v351.json',budget)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==339 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(dict(verification=verification,cost=cost,next_native_cap=233,next_remaining_after_cap=1436)),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);close(a.parse_args().private_root)
