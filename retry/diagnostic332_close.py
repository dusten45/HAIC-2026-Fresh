"""Aggregate-only332 report, unchanged native budget, bounded next-test proposal."""
import argparse
import datetime
import json
import math
from pathlib import Path

import numpy as np
from retry.path271_run import read,save,sha


def rows(path):return [json.loads(s) for s in path.read_text().splitlines()]
def contact_prefix(records):return records[:next(i for i,r in enumerate(records) if r['collision'])]
def first_difference(a,b,key):return next((i+1 for i,(x,y) in enumerate(zip(a,b)) if key(x)!=key(y)),None)
def span(v):
    v=[float(x) for x in v];return [min(v),max(v)] if v else None


def close(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage332';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert not (D/'cost.json').exists()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    for f,h in read(D/'build-private.json')['source_hashes'].items():assert sha(f)==h,f
    assert sha(G/'retry/diagnostic332_routes.py')==read(D/'routing-serialization-repair.json')['source_after_sha256']
    cfg=read(R/'stage330/artifacts-private.json')['ON']
    for path,h in read(D/'routing-counterfactual-private.json')['loaded_module_sha256'].items():assert cfg['members_sha256'][path]==h,path
    inventory=read(D/'inventory-private.json');base=rows(R/'stage294/policies/g1p4/N2/trace-private.jsonl');original=rows(R/'stage330/evaluation/N2/trace-private.jsonl');a=rows(R/'stage331/A/trace-private.jsonl');b=rows(R/'stage331/B/trace-private.jsonl')
    result=read(R/'stage294/policies/g1p4/N2/result.json');assert result['archive_sha256']==sha(R/'stage296/submission296.zip') and result['completed']
    assert result['geometry_sha256']==read(R/'stage330/plan.json')['cases']['N2']['road_geometry_sha256'];assert result['initial_observation_sha256']==read(R/'stage330/plan.json')['initial_observations']['N2']
    history={}
    for name,data,action in [('296_success',base,'action'),('330_failure',original,'action'),('331_A',a,'executed'),('331_B',b,'executed')]:
        prefix=contact_prefix(data);inputs=data[:len(prefix)+1];history[name]=dict(precontact_input_features_count=len(inputs),precontact_input_mean_feedback_speed_m_s=float(np.mean([r['features'][4] for r in inputs])),statistics_scope='Action statistics exclude first-contact action; input features count includes its collision-free pre-action input. Observation count does not imply saved pixels.',contact_free_executed_actions=len(prefix),precontact_observation_boundaries=len(prefix)+1,first_contact=prefix[-1]['step']+1,
            features_missing_target=sum(bool(r['features'][0]) for r in prefix),feedback_speed_m_s_range=span(r['features'][4] for r in prefix),
            mean_feedback_speed_m_s=float(np.mean([r['features'][4] for r in prefix])),mean_gas=float(np.mean([r[action][1] for r in prefix])),mean_brake=float(np.mean([r[action][2] for r in prefix])),
            mean_abs_steering=float(np.mean([abs(r[action][0]) for r in prefix])),geometry_aligned_with_other_policy=False)
    differences=dict(first_action_difference=first_difference(base,original,lambda r:r['action']),first_steering_difference=first_difference(base,original,lambda r:r['action'][0]),
        first_feedback_speed_difference=first_difference(base,original,lambda r:r['features'][4]),first_legacy_speed_feature_difference=first_difference(base,original,lambda r:r['features'][3]),
        comparison_scope='Same action index only, not the same location or tile; no success296 positions or pixels are available. Pedal channel differs at action1; subsequent observation/steering differences are consequences or other coupled responses, not isolated steering treatment.')
    geometry=read(D/'geometry-private.json');replays={label:read(D/label/'saved-pixel-replay-private.json') for label in ['A','B']};direct_errors=[];aged_errors=[];joint_errors=[];direct_identity=[];late=[]
    for label,data in geometry['actual_precontact_geometries'].items():
        recorded=a if label=='A' else b
        for state in data:
            i=state['boundary'];r=replays[label][i]['response'];previous_command=recorded[i-1]['executed'][0];joint_errors.extend(abs(j+previous_command) for j in state['steering_joint']);direct_errors.extend(m['nearest_GT_center_error_m'] for m in state['nearest_perception_matches']['direct']);direct_identity.extend(m['nearest_GT_obstacle'] for m in state['nearest_perception_matches']['direct'])
            matches=state['nearest_perception_matches']['tracked'];ages=[h[3] for h in r['state']['hazards']]
            aged_errors.extend(m['nearest_GT_center_error_m'] for m,age in zip(matches,ages) if age>0)
            late.append(state)
    routing=read(D/'routing-counterfactual-private.json');changes=[r for r in routing['records'] if r['variants']['retained']['steering']!=r['variants']['direct_only']['steering']]
    assert len(changes)==4 and sum(r['path_changed'] for r in routing['records'])==6
    static=dict(actual_precontact_boundaries=8,actual_boundary_indices=[64,65,66,67],spatially_matched_same_tile_pairs=len(geometry['spatial_alignment']),
        nearest_observed_A_B_position_gap_m_range=span(x['nearest_observed_position_gap_m'] for x in geometry['spatial_alignment']),
        aligned_B_minus_A_speed_m_s_range=span(x['speed_difference_B_minus_A'] for x in geometry['spatial_alignment']),
        direct_obstacle_nearest_GT_center_error_m_range=span(direct_errors),all_direct_matches_same_contact_obstacle=all(i==0 for i in direct_identity),
        aged_hazard_nearest_any_GT_center_error_m_range=span(aged_errors),
        maximum_abs_lateral_velocity_m_s=max(abs(x['lateral_velocity_m_s']) for x in late),maximum_abs_road_proxy_heading_error_rad=max(abs(x['road_heading_error_rad']) for x in late),
        maximum_joint_plus_previous_executed_steering_error_rad=max(joint_errors),
        hull_core_gap_to_eventual_contact_obstacle_m_range=span(x['obstacles'][0]['hull_core_gap_m'] for x in late),
        wheel_core_gap_to_eventual_contact_obstacle_m_range=span(x['obstacles'][0]['wheel_core_gap_m'] for x in late),
        last_boundary_initial_path_heading_rad_range=span(x['planned_initial_heading_clockwise_rad'] for x in late if x['boundary']==67),
        last_boundary_velocity_vs_initial_path_heading_error_abs_rad_range=span(abs(x['velocity_heading_minus_planned_rad']) for x in late if x['boundary']==67),
        route_counterfactual_frames=8,retained_route_and_original_steering_reproduced_exactly=True,direct_only_path_changes=6,direct_only_steering_changes=4,
        direct_only_steering_change_absolute_range=span(abs(x['variants']['retained']['steering']-x['variants']['direct_only']['steering']) for x in changes),
        static_effect='Removing aged hazards from routing changes selected steering sign at boundaries65/66 in both trajectories; path changes at67 do not change target or calculated steering. This proves a local routing output dependency, not a contact or full-policy benefit.',
        physical_contact='At actual post-action68 both arms touch the same obstacle through hull fixture0; B also has a front-wheel contact. Precontact core gaps are not swept clearance and omit unmeasured polygon skin.')
    proposal=dict(status='Proposed only, not executed, no extra budget authorized',hypothesis='Retained hazards alter the locally chosen avoidance direction; test whether one direct-only-derived steering command at action66 changes subsequent contact persistence, while all pedals and other steering commands remain stored330.',
        comparison_A='Existing exact331A replay, restricted to same endpoint71: first contact68, contact68-71, damage.8; actual later crash72 is outside proposed endpoint.',
        intervention_B='Independent reset; stored331A actions1-65 unchanged. At action66 compute the frozen routing function using only current direct detections, same saved-pixel image, original speed/previous nominal memory, same lookahead/controller laws. Override only executed steering with that derived value; pedals stay stored330. Actions67-71 all stored331A commands. Retain actual-observation original nominal memory updates throughout; distinguish calculated and executed steering. No threshold, fit, horizon or sweep.',
        native_cap=71,prefix_cost=65,single_probe_cost=1,followup_cost=5,new_A_cost=0,existing_A_is_measured_actual_reference=True,research_remaining_after_max=0,final_reserve_used=0,
        prebranch_gate='Match initial observation/geometry and full65-action saved raw prefix, actual captured pre-action66 physical snapshot, serialized policy state, action/features/audit/nominal memory/collision/damage. Match tracked RNG states where recorded; OpenCV hidden RNG and hidden Box2D state remain explicit limitations. Source contract must justify env RNG state unchanged since measured boundary64; otherwise do not claim that unmeasured state equality or execute the probe.',
        stop='Stop at first replay or state difference before probe; record consumed native, no retry/reseed/repair sweep. Stop official terminal immediately; otherwise protocol stop71, not DNF or completion. Stop at authorization deadline. No run under this332 task.',
        falsification='Same firstcontact68 and same contact persistence/damage through71 refutes sufficiency of this single direct-only-derived command, not all tracking explanations. Earlier contact or greater damage rejects it. Later first contact/lower damage only supports a local effect.',
        continuation_gate='Require no lost progress versus recordedA at71 and strictly less damage with later/no contact through71 before considering further investigation. No promotion or crash72/complete-lap claim; any further experiment needs its own authorization/budget/preregistration.',
        remaining_blocker='Full296-versus-failure spatial causal diagnosis remains impossible because historical296 success pixels/GT/path/tile records are absent. This local counterfactual does not fill them.')
    save(D/'next-single-probe-proposal-private.json',proposal)
    actor=read(D/'actor-cost.json');geomcost=read(D/'geometry-cost.json');repair=read(D/'routing-serialization-repair.json');assert actor['saved_observation_actor_calls']==136 and all(r['process_reaped'] and r['actor_pids_absent'] for r in actor['reaping'])
    before=R/'project-effective-budget-v338.json';v=read(before);assert v['research_remaining']==71 and v['final_reserved_actions']==84000 and v['final_reserve_used']==0
    cost=dict(stage=332,new_wrapper_actions=0,new_fits=0,new_source_physics_ticks=0,new_paid_resources=0,additional_research=0,
        saved_observation_actor_calls=136,pure_routing_function_calls=17,pure_routing_successful_calls=16,pure_routing_failed_validation_calls=1,
        saved_actor_wall_s=actor['wall_s'],saved_actor_CPU_s=actor['actor_CPU_s'],saved_actor_evaluator_CPU_s=actor['runner_CPU_s'],static_geometry_wall_s=geomcost['wall_s'],static_geometry_CPU_s=geomcost['runner_CPU_s'],static_routing_wall_s=routing['wall_s'],static_routing_CPU_s=routing['CPU_s'],failed_static_routing_invocation_wall_s=repair['failed_invocation_wall_s'],
        cost_scope='Recorded replay/geometry/function costs; initial discovery, JSON inventory and final reporting not timed. Failed read-only route check CPU not measured; failure was tuple/list serialization equality and happened before alternatives.',
        actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions'],research_remaining=71,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=v['B_operating_cap'])
    save(D/'cost.json',cost);v.update(version=339,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(before),prior_budget_sha256=sha(before),B_increment=0,cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),stage332_new_wrapper_actions=0)
    assert not (R/'project-effective-budget-v339.json').exists();save(R/'project-effective-budget-v339.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==332 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    public=dict(stage=332,full_success296_spatial_comparison_available=False,inventory={k:{x:y for x,y in val.items() if x not in ['folder','available_original_files']} for k,val in inventory.items()},
        coordinate_contract='Boundary n is after n wrapper actions, before action n+1; initial raw t1.02, .08s per action precontact. World axes transform by R(-hull angle) into x-right/y-forward body frame. Positive command steering is clockwise; actual joint target is negative command. Joint at boundary n compared with executed action n, never n+1. Pixel paths use anisotropic1.3608/1.701px/m and frozen detector calibration; HUD values are quantized proxies, not GT. Tile centerline is derived from actual saved road fixture centroids.',
        precontact_histories=history,index_only_prefix_differences=differences,static_results=static,next_single_probe_proposal=proposal,cost=cost,
        limitations=['296 success has no saved pixels/pose/path/tile/obstacle GT, so full spatial alignment cannot be performed. 330 earlier physical GT is also absent.',
            'Late A/B samples align by actual position and tile with reported longitudinal differences; no synthetic interpolation or guessed GT.',
            'Nearest-obstacle association reports distances to all six actual obstacles; it does not label visibility or infer GT for unobserved old frames. Direct detection accuracy does not establish retained-memory accuracy.',
            'Nominal local car footprint reconstructed from unchanged source constants; actual car fixture shapes/skin were not captured. Static endpoint clearance is not swept collision prediction.',
            '331 last8pedals negative result does not prove steering cause or unavoidability. Static route change is an output dependency, not a measured physical counterfactual.',
            'Stored-pixel replay follows each recorded input stream; it is not a closed-loop success296 run. Missing baseline pixels cannot be replaced by applying296 to330 pixels.'],
        champion296_preserved=True,TRAIN_registry_preserved=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False)
    save(D/'summary-private.json',public);save(G/'retry/diagnostic332_result.json',public)
    print(json.dumps(dict(index_differences=differences,static=static,cost=cost),ensure_ascii=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',required=True,type=Path);close(p.parse_args().private_root)
