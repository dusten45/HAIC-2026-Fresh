"""Separate a predicate activation from an exposed closed-loop control test."""
import argparse
import datetime
import json
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.pair343_stage import verify
from retry.confidence341_run import label,polyline_distance


def rows(path):return [json.loads(s) for s in Path(path).read_text().splitlines()]


def describe(data,result):
    raw=[dict(action=r['step'],**tick) for r in data for tick in r['raw_observations']];pairs=sorted({tuple(pair) for tick in raw for pair in tick['pairs']});contacts=[]
    for pair in pairs:
        seen=[q for q in raw if list(pair) in q['pairs']]
        contacts.append(dict(fixture_pair=list(pair),first_raw_time_s=seen[0]['raw_time'],last_raw_time_s=seen[-1]['raw_time'],touching_raw_endpoint_count=len(seen),endpoint_sample_weight_s=len(seen)/50))
    hit=[];prior=set()
    for tick in raw:
        current=set(tick['hit_objects']);hit.extend(dict(object_index=q,action=tick['action'],raw_interval_s=[tick['raw_time']-.02,tick['raw_time']]) for q in sorted(current-prior));prior=current
    last=data[-1]
    return dict(native_actions=len(data),collision_event_actions=[q['step'] for q in data if q['collision']],raw_collision_flags=sum(q['collision'] for q in raw),new_obstacle_hit_intervals=hit,fixture_touching=contacts,raw_observation_count=len(raw),damage=last['damage'],unique_tiles=last['post']['unique_tiles'],speed_m_s=last['post']['speed_m_s'],off_track_counter=last['post']['off_track_counter'],last_tile_growth_action=max((q['step'] for q in data if q['post']['unique_tiles']!=q['pre']['unique_tiles']),default=None),actual_DNF=result['actual_DNF'],protocol_stop=result['protocol_stop'],completed=result['completed'],finish_time_s=result['finish']['finish_time_s'],lap_ms=result['lap_ms'],retire_reason=result['retire_reason'])


def close(R):
    D=R/'stage343';G=Path(__file__).resolve().parent.parent;p=verify(R);assert not (D/'cost.json').exists();start,cpu=time.perf_counter(),time.process_time();result={arm:read(D/arm/'result.json') for arm in ['A','B']};data={arm:rows(D/arm/'trace-private.jsonl') for arm in ['A','B']};budget=read(D/'native-budget.json');prefix=read(D/'natural-prefix-qualification.json');zs={arm:np.load(D/arm/'frames-actions-private.npz') for arm in ['A','B']}
    assert budget['actions']==sum(q['native_actions'] for q in result.values())==320 and budget['resets']==2 and budget['arms']==dict(A=160,B=160)
    assert all(not q['technical_error'] for q in result.values());assert prefix['passed'] and prefix['unexposed'] and prefix['prefix_actions']==160 and prefix['input_stacks']==161
    assert np.array_equal(zs['A']['actions'],zs['B']['actions']) and np.array_equal(zs['A']['frames_uint8'],zs['B']['frames_uint8'])
    for arm in ['A','B']:
        assert len(data[arm])==len(zs[arm]['actions'])==160 and len(zs[arm]['frames_uint8'])==161
        assert sum(q['raw_ticks'] for q in data[arm])==result[arm]['raw_step_ticks']==640 and result[arm]['raw_reset_ticks']==51
        assert result[arm]['raw_counter_at_stop']-result[arm]['raw_counter_after_reset']==640
        assert all(not q['terminated'] and not q['truncated'] for q in data[arm]);assert result[arm]['protocol_stop'] and not result[arm]['completed'] and not result[arm]['actual_DNF']
        for q in data[arm]:assert q['executed']==q['returned_action'] and q['nominal_memory']==q['policy']['previous_steer'] and np.float32(q['nominal_memory'])==np.float32(q['returned_action'][0])
    supported_losses=[];births=[];birth_labels={};footprints=[]
    for i,(a,b) in enumerate(zip(data['A'],data['B'])):
        for key in ['executed','features','audit','tracker','support_record','pixel_path','actor_state','nominal_memory','policy','pre','post','pre_physical','post_physical','pre_RNG','post_RNG','raw_observations']:assert a[key]==b[key],(i,key)
        for birth in b['support_record']['births']:
            lab,identity=label(birth['point'],b['pre_physical']);birth_labels[tuple(birth['uid'])]=dict(label=lab,id=identity)
            if birth['low']:births.append(dict(birth_action=b['step'],direct_index=birth['uid'][1],component_area=birth['component_area'],raw_road_neighbors=birth['raw_road_neighbors'],diagnostic_label=lab))
        e=b['routing_evidence'];assert e['tracker_preserved'] and e['full_hazards']==b['tracker']['after']
        for j in e['removed_indices']:
            flag=b['support_record']['after'][j];uid=tuple(flag['uid']);point=e['full_hazards'][j];distance=polyline_distance(a['pixel_path'],point[:2]);footprints.append(dict(action=b['step'],uid=list(uid),age=point[3],path_center_distance_m=distance,existing_router_clearance_m=2.6+point[2],clearance_margin_m=None if distance is None else distance-(2.6+point[2])))
            if birth_labels[uid]['label']=='fixture_supported':supported_losses.append(dict(action=b['step'],uid=list(uid)))
    assert births==[dict(birth_action=137,direct_index=0,component_area=6,raw_road_neighbors=0,diagnostic_label='unresolved')]
    assert [q['action'] for q in footprints]==list(range(137,146)) and not supported_losses
    comparison={arm:describe(data[arm],result[arm]) for arm in ['A','B']}
    sums=['wall_s','runner_CPU_s','actor_CPU_s','reset_wall_s','raw_step_render_wall_s','raw_contact_observer_wall_s','capture_wall_s','journal_wall_s','artifact_wall_s']
    v=read(R/'project-effective-budget-v354.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1282802,1436,84000,0)
    cost=dict(stage=343,new_wrapper_actions=320,new_A_runs=1,new_B_runs=1,new_environment_resets=2,per_arm_cap=160,total_cap=320,additional_research=0,raw_step_ticks=1280,raw_reset_ticks=102,actual_cumulative_wrapper_actions=1283122,research_remaining=1116,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1368238,new_learning_fits=0,parameter_sweeps=0,new_source_physics_rollout_ticks=0,new_paid_resources=0,technical_recovery_native_actions=0,technical_recovery_resets=0,technical_error=None,per_arm={arm:{k:result[arm][k] for k in sums} for arm in ['A','B']},totals={k:sum(result[arm][k] for arm in ['A','B']) for k in sums},closure_wall_s=time.perf_counter()-start,closure_CPU_s=time.process_time()-cpu,measurement_scope='Actual raw.step timing includes simulation+render, not pure solver time. Read-only raw-contact observer, pre/postcapture, journal and artifact writing timed separately; some reset capture/startup/hash/IPC/report/verification remain in total or outside namedsubtimers. No extra world advances.')
    next_experiment=dict(status='Proposed native0cache gate only, not executed/reserved.',question='Can the same observation rule create a naturally reachable near-car control change under the exact frozen policy that actually generated the historical O2near-car pixels?',
        reason='343current334ON/H1does not visit the historical near-car exposure within160. Reusing an off-policy cached birth or simply extending a matched no-effect pair cannot establish that exposure. A qualified source-policy replay checks policy/visitation mismatch cheaply.',
        design='Reuse existing historicalO2first160stored inputs. Exact frozen296collection baseline versus the unchanged zero-road-neighbor routing rule adapted only to that source tracker lineage bookkeeping. Original source fallback/tracker/controller/models remain frozen in both arms; do not substitute334ON/H1. Baseline must reproduce historical actions/features/normal memory before candidate. Metadata follows the source original transforms without changing them.',
        budget=dict(stored_policy_act_calls=320,actor_resets_on_stored_pixels=2,new_native_actions=0,new_environment_resets=0,new_source_physics_rollout_ticks=0,new_learning_fits=0,parameter_sweeps=0,research_remaining_after=1116,final_reserved_actions_after=84000),
        gates='One baseline and one exact-rule candidate, no extra arm/cutoff. Preserve detector/tracker; stop on reproduction/integrity or captured fixture-supported removal. Report first control-relevant footprint and all no-effect intervals. If no exposed effect, record inconclusive, no automatic extension.',
        value='Tests whether the original near-car falsification target is on-policy for a qualified known baseline, before spending more native. If exposed it can support a separately registered actual paired validation; it does not qualify currentH1safety or authorize a new native run.',limits='Different baseline context is explicit. Actual occlusion/material truth still absent, and cache is not an actual avoidance outcome. Champion remains unchanged.')
    verification=dict(passed=True,fresh_independent_resets=2,prefix_actions_exact=160,input_frames_exact=161,reset_actor_tracker_physics_accessible_RNG_exact=True,raw_tick_contacts_pose_speed_tiles_exact=True,full_returned_controls_normal_memory=True,predicate_exposed=True,routing_withheld_actions=list(range(137,146)),control_exposed=False,first_control_difference=None,forced146=False,supported_losses=0,no_postcap_steps=True,hidden_solver_OpenCV_RNG_not_directly_measured=True)
    public=dict(stage=343,decision='Control-unexposed/inconclusive for the intended near-car harmful-effect hypothesis. A low-support predicate activated but did not alter any path,target,fullcontrol ornormalmemory. Neither method counterexample nor safety pass; no actual completion.',verification=verification,comparison=comparison,flagged_births=births,withheld_route_geometry=dict(actions=[q['action'] for q in footprints],minimum_path_center_distance_m=min(q['path_center_distance_m'] for q in footprints),minimum_existing_clearance_margin_m=min(q['clearance_margin_m'] for q in footprints),scope='Existing source router2.6+observedradius margin on selected path only, not a new cutoff or vehicle swept-clearance proof.'),
        limits=['Exact160prefix and161pixels despite conditional footprint137-145; natural action branch never occurred. Historical146near-car point was not forced or reached as such undercurrentpolicy.',
                'Both raw-contactevent flags and sampled fixturetouching pairs are zero over1280actualticks; no fixture-specific contact interval observed. Samples are raw0.02sendpoints, not hidden solver substeps.',
                'No finish, lap time or DNF at160; both are protocolcensors. Damage0and161tiles cannot qualify global completion or rule safety.',
                'One postselected known TRAIN road, no generalization/occlusion/material safety. GT only posthoc, unresolved point not false-positive ground truth.',
                'Nextcache explicitly changes baseline context to the sourcepolicy to test reachability, not silently relabel the343result or tune a rule.'],cost=cost,next_minimum_experiment=next_experiment,preserved334_mixed_evidence=read(R/'stage342/summary-private.json')['preserved334_mixed_evidence'],actual_occlusion_preservation_verified=False,champion296_preserved=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,authorization_end_utc=p['deadline_utc'])
    save(D/'withheld-footprints-private.json',footprints);save(D/'cost.json',cost);save(D/'summary-private.json',public);save(D/'final-saved-evidence-check.json',verification);save(G/'retry/pair343_result.json',public)
    v.update(version=355,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v354.json'),prior_budget_sha256=sha(R/'project-effective-budget-v354.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,actual_cumulative_wrapper_actions=1283122,research_remaining=1116,stage343_new_wrapper_actions=320);assert not (R/'project-effective-budget-v355.json').exists();save(R/'project-effective-budget-v355.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==343 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(dict(verification=verification,comparison=comparison,withheld_geometry=public['withheld_route_geometry'],cost=cost,next_experiment_budget=next_experiment['budget'])),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);close(a.parse_args().private_root)
