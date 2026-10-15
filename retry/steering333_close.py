"""Close one steering command intervention; publish aggregates, retain raw GT."""
import argparse
import datetime
import json
import math
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.pedal331_run import plain,digest,obs_sha


def rows(path):return [json.loads(s) for s in path.read_text().splitlines()]


def outcome(trace,result,limit):
    data=trace[:limit];contact=[r['step'] for r in data if r['collision']];last=data[-1] if data else None
    fixtures=[]
    for r in data:
        if r.get('post_physical') and r['collision']:
            for fixture in r['post_physical']['touching_obstacle_contacts']:
                if fixture not in fixtures:fixtures.append(fixture)
    first=next((r for r in data if r['collision']),None)
    return dict(observed_actions=len(data),first_contact=contact[0] if contact else None,contact_actions=contact,contact_action_count=len(contact),
        collision_endpoint_fixture_pairs=fixtures,fixture_scope='[obstacle index, obstacle fixture, car body index (0 hull,1-4wheels), car fixture], saved wrapper endpoints only; no substep fixture enumeration.',
        first_contact_time_interval_s=(first.get('contact_interval_s') or first.get('first_contact_interval_s')) if first else None,
        endpoint_damage=last['damage'] if last else None,endpoint_speed_m_s=last['post']['speed_m_s'] if last else None,
        endpoint_unique_tiles=last['post']['unique_tiles'] if last else None,total_tiles=292,
        endpoint_progress=last['post']['unique_tiles']/292 if last else None,
        actual_terminal_in_interval=any(r['terminal'] for r in data),actual_DNF=bool(result['actual_DNF'] and result['native_actions']<=limit),
        completed=bool(result['completed'] and result['native_actions']<=limit),protocol_stop=bool(result['protocol_stop'] and result['native_actions']<=limit))


def close(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage333';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert not (D/'cost.json').exists()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    actual=read(D/'B/result.json');A_result=read(R/'stage331/A/result.json');a=rows(R/'stage331/A/trace-private.jsonl');b=rows(D/'B/trace-private.jsonl');z=np.load(D/'B/raw-pixels-actions-private.npz');ref=np.load(R/'stage331/A/raw-pixels-actions-private.npz');budget=read(D/'native-budget.json');used=budget['actions']
    assert used==actual['native_actions']<=72
    valid=actual['comparison_valid'];checks={};comparison=None
    if valid:
        assert len(z['actions'])==len(b)==used and len(z['observations'])==used+1
        assert all(not row['terminal'] for row in b[:-1])
        assert np.array_equal(z['observations'][:66],ref['observations'][:66]);assert np.array_equal(z['actions'][:65],ref['actions'][:65])
        changed=np.argwhere(z['actions']!=ref['actions'][:used]);assert changed.tolist()==[[65,0]]
        assert np.array_equal(z['actions'][:,1:],ref['actions'][:used,1:]);assert np.array_equal(z['actions'][66:],ref['actions'][66:used])
        boundary=read(D/'B/prebranch65-private.json');assert boundary['physical']==a[65]['pre_physical'] and boundary['policy']==a[64]['policy'] and boundary['observation_sha256']==obs_sha(ref['observations'][65]) and boundary['RNG']==read(R/'stage331/A/boundary-private.json')['RNG']
        assert read(D/'prebranch-gate.json')['passed'];assert read(D/'A-reference-qualification.json')['passed']
        for r in b:assert r['nominal_memory']==r['policy']['previous_steer'] and np.float32(r['nominal_memory'])==np.float32(r['original_nominal_steering'])
        assert read(D/'B/probe-private.json')['state_preserved'] and read(D/'cache-receipt.json')['probe_equals332']
        assert actual['reaping']['process_reaped'] and actual['reaping']['actor_pids_absent']
        common=min(len(a),len(b));comparison=dict(common_actions=common,A=outcome(a,A_result,common),B=outcome(b,actual,common),
            endpoint_position_gap_m=float(np.linalg.norm(np.array(a[common-1]['post']['position'])-b[common-1]['post']['position'])),
            endpoint_heading_difference_B_minus_A_rad=float(math.atan2(math.sin(b[common-1]['post']['angle']-a[common-1]['post']['angle']),math.cos(b[common-1]['post']['angle']-a[common-1]['post']['angle']))),
            endpoint_unique_tile_difference_B_minus_A=int(b[common-1]['post']['unique_tiles']-a[common-1]['post']['unique_tiles']))
        checks=dict(passed=True,existing_A_330_331_commands_pixels_exact=True,reference_A_complete_exact_replay_qualified=True,prefix_actions_exact=65,prefix_observation_stacks_exact=66,
            physical_policy_tracked_RNG_prebranch_exact=True,only_changed_command_action=66,only_changed_component='steering',all_pedals_and_commands67_onward_stored_A_exact=True,
            nominal_memory_calculated_original_steering_preserved=True,probe_policy_state_preserved=True,no_actions_after_terminal=True,new_verification_native_actions=0)
    else:
        checks=dict(passed=False,comparison_invalid=True,technical_error=actual['technical_error'],no_repair_or_retry=True,new_verification_native_actions=0)
    save(D/'independent-verification.json',checks)
    prior=R/'project-effective-budget-v340.json';v=read(prior);assert v['research_remaining']==72 and v['B_increment']==1 and v['final_reserved_actions']==84000 and v['final_reserve_used']==0
    cache=read(D/'cache-receipt.json');cost=dict(stage=333,new_wrapper_actions=used,native_cap=72,new_B_runs=1,new_A_runs=0,reused_actual_A_runs=1,additional_research=1,
        raw_step_ticks=actual['raw_step_ticks'],raw_reset_ticks=actual['raw_reset_ticks'],native_wall_s=actual['wall_s'],runner_CPU_s=actual['runner_CPU_s'],actor_CPU_s=actual['actor_CPU_s'],cached_actor_calls=cache['cached_actor_calls'],cache_wall_s=cache['wall_s'],cache_actor_CPU_s=cache['actor_CPU_s'],cache_runner_CPU_s=cache['runner_CPU_s'],pure_routing_probe_calls=2 if valid else 1,
        new_fits=0,new_source_physics_ticks=0,new_paid_resources=0,actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions']+used,research_remaining=v['research_remaining']-used,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=v['B_operating_cap'])
    save(D/'cost.json',cost);v.update(version=341,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage333_new_wrapper_actions=used)
    assert not (R/'project-effective-budget-v341.json').exists();save(R/'project-effective-budget-v341.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==333 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    if not valid:interpretation='Prebranch or execution qualification failed; causal comparison invalid, no interpretation or retry.'
    elif comparison['B']['first_contact']==comparison['A']['first_contact'] and comparison['B']['contact_action_count']<comparison['A']['contact_action_count']:
        interpretation='Same first contact, less persistent contact and lower endpoint damage, with survival through72. Supports a local postcontact/persistence effect of one executed steering command under this fixed continuation. Does not establish contact avoidance, full-policy benefit, completion, or universal cause.'
    else:interpretation='Compare the common measured interval; same/worse outcome refutes sufficiency of this single command only. Damage increase alone is not an automatic veto. No full-policy/generalization conclusion.'
    next_proposal=dict(status='Proposed only; not executed; research balance may not fund another native run',
        component='Transport aged hazard points with legal ego-motion rotation and translation while preserving occluded hazards.',
        legal_inputs='Existing road-image optical-flow affine transform when accepted; otherwise consider fixed current HUD yaw/speed and a body-frame SE(2) motion approximation. Use measured GT only for diagnostic errors, never as policy motion input.',
        transform='p_next = R(-delta_yaw) (p_old - estimated_body_displacement); verify yaw sign, frame convention, sampling lag and pixel scaling on stored TRAIN observations. Norm speed alone does not reveal lateral velocity; forward-only translation is an approximation.',
        preserve_occlusion='Transport retained points, retain unchanged radius/age limit/dedup and direct detection. Missing current detection during occlusion must not delete a retained point. Direct-only333 probe is not a proposed replacement tracker.',
        isolation='Stored-pixel current tracker vs one transport-component change, identical detections/retention/route/controller constants. Include actual occlusion examples with saved GT where available; current N2 late observations alone do not validate occlusion preservation.',
        offline_gate='First reproduce original stored actor outputs and frame transforms; measure stale-point world/body error, duplicate persistence, real occluded-obstacle retention and downstream routing changes without any fit or threshold search. Stop mismatches. No automatic horizon extension or native budget expansion.',
        native_gate='Only after offline evidence, separately preregister any native comparison and its budget; preserve final reserve84000. No such run under333.')
    public=dict(stage=333,design='Independent reset, stored331A commands1-65, only action66 steering from same-pixel direct-only frozen routing/controller; storedA pedals66 and all commands67-72; actual-observation nominal memory retained.',
        comparison_valid=valid,verification=checks,common_interval_comparison=comparison,interpretation=interpretation,cost=cost,
        limitations=['Known postselected TRAIN N2 single-command experiment; fixed subsequent recorded controls, not a closed-loop direct-only policy.',
            'Only captured physical state and tracked Python/NumPy/environment RNG are directly matched; opaque OpenCV RNG and hidden Box2D solver state remain unmeasured. Environment RNG equality at65 also relies on measured64 state and unchanged source step call contract.',
            'Contact times are .08-second wrapper intervals. Fixture pairs are saved endpoints, not every raw substep contact.',
            'Protocol survival through72 is not completion or a general-policy improvement; firstcontact unchanged does not establish inevitability.',
            'Increased damage would not alone veto a candidate. Same/worse result would reject one-command sufficiency only, not all stale-coordinate defects.'],
        next_legal_transport_proposal=next_proposal,champion296_preserved=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,authorization_end_utc=p['deadline_utc'])
    save(D/'summary-private.json',public);save(G/'retry/steering333_result.json',public);print(json.dumps(dict(valid=valid,comparison=comparison,cost=cost,interpretation=interpretation)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',required=True,type=Path);close(p.parse_args().private_root)
