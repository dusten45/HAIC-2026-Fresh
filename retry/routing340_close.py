"""Close one real paired test without extrapolating beyond its observed endpoint."""
import argparse
import datetime
import json
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.routing340_stage import verify
from retry.probe338_close import describe


def rows(path):return [json.loads(s) for s in Path(path).read_text().splitlines()]


def close(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage340';p=verify(R,True);assert not (D/'cost.json').exists();result=read(D/'B/result.json');a=rows(R/'stage337/B/trace-private.jsonl');b=rows(D/'B/trace-private.jsonl');z=np.load(D/'B/frames-actions-private.npz');original=np.load(R/'stage337/B/frames-actions-private.npz');used=read(D/'native-budget.json')['actions']
    assert used==result['native_actions']==len(b)==len(z['actions'])<=233 and len(z['frames_uint8'])==used+1
    assert result['comparison_valid'] and not result['technical_error'] and result['prefix126_verified']==126
    assert np.array_equal(z['actions'][:126],original['actions'][:126]) and np.array_equal(z['frames_uint8'][:127],original['frames_uint8'][:127]);assert read(D/'prefix126-qualification.json')['passed']
    assert read(D/'cache-receipt.json')['passed'] and read(D/'339-cache-gate.json')['passed']
    assert all(not r['terminated'] and not r['truncated'] for r in b[:-1]);assert sum(r['raw_ticks'] for r in b)==result['raw_step_ticks']==result['raw_counter_at_stop']-result['raw_counter_after_reset']
    filters=[]
    for r in b:
        assert r['executed']==r['returned_action'] and r['nominal_memory']==r['policy']['previous_steer'] and np.float32(r['nominal_memory'])==np.float32(r['returned_action'][0])
        f=r['routing_filter'];assert f['tracker_preserved'] and f['full_hazards']==r['tracker']['after'] and len(f['removed'])<=1
        assert f['routing_hazards']==[h[:3] for i,h in enumerate(f['full_hazards']) if i not in f['removed_indices']]
        assert r['features'][11]==len(f['full_hazards'])
        for point in f['removed']:assert r['step']-point[3]==121 and r['step'] in [127,128,129]
        if f['removed']:filters.append(r['step'])
    common=min(len(a),len(b));first_action=next((i+1 for i in range(common) if a[i]['executed']!=b[i]['executed']),None);assert first_action==127
    first_steer=next((i+1 for i in range(common) if a[i]['executed'][0]!=b[i]['executed'][0]),None)
    first_pixel=next((i+1 for i in range(min(len(original['frames_uint8']),len(z['frames_uint8']))) if not np.array_equal(original['frames_uint8'][i],z['frames_uint8'][i])),None)
    comparison=dict(common_actions=common,A=describe(a,common),B=describe(b,common),A_full=dict(actions=233,actual_DNF=True,retire_reason='off_track'),B_actual_DNF=result['actual_DNF'],B_censored=result['censored'],B_protocol_stop=result['protocol_stop'],B_finish=result['finish']['finish_time_s'],B_lap_ms=result['lap_ms'])
    cache=read(D/'cache-receipt.json');v=read(R/'project-effective-budget-v351.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1282569,1669,84000,0)
    cost=dict(stage=340,new_wrapper_actions=used,new_B_runs=1,new_A_runs=0,native_cap=233,additional_research=0,raw_step_ticks=result['raw_step_ticks'],raw_reset_ticks=result['raw_reset_ticks'],native_wall_s=result['wall_s'],runner_CPU_s=result['runner_CPU_s'],actor_CPU_s=result['actor_CPU_s'],capture_wall_s=result['capture_wall_s'],cached_actor_calls=cache['cached_actor_calls'],cache_wall_s=cache['wall_s'],cache_runner_CPU_s=cache['runner_CPU_s'],cache_actor_CPU_s=cache['actor_CPU_s'],new_learning_fits=0,new_source_physics_ticks=0,new_paid_resources=0,actual_cumulative_wrapper_actions=1282569+used,research_remaining=1669-used,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1368238,measurement_scope='Timed execution and cache phases include instrumentation; setup/build/hash/reporting/closure not wholly timed. No pure simulator-only wall claim.')
    verification=dict(passed=True,actual_prefix_actions_exact=126,actual_prefix_input_frames_exact=127,actor_tracker_nominal_memory_captured_physics_accessible_RNG_gate=True,single_lineage_routing_input_only=True,removed_endpoint_actions=filters,tracker_not_deleted=True,all_returned_controls_executed=True,normal_own_nominal_memory=True,no_stored_continuation=True,first_full_control_difference_action=first_action,first_actual_steering_difference_action=first_steer,first_different_input_action=first_pixel,no_postterminal_steps=True,hidden_solver_OpenCV_RNG_not_directly_measured=True)
    if result['actual_DNF']:
        interpretation='The persistent single-lineage routing exclusion did not establish local sufficiency to avoid official retirement. Compare joint contact/progress/termination evidence; no inference that all memory is harmless or speed/lookahead/target-following is the cause.'
    elif result['completed']:
        interpretation='Observed official finish on this one postselected case only; no generalization or promotion. Joint contact/progress/finish evidence must be retained.'
    else:
        interpretation='233-action protocol censor without official finish. Local progress/contact evidence only; neither completion nor definitive later-retirement outcome is observed.'
    public=dict(stage=340,question=p['hypothesis'],verification=verification,comparison=comparison,interpretation=interpretation,cost=cost,
        limits=['Known postselected N2, one new B; existing actual337 A reused. No detector-semantic ground truth, no generalization or automatic promotion.',
                'One change at routing input. Tracker/near scheduling/count/min-distance features preserved; downstream path-derived features, pedals, normal memory and own trajectory may change.',
                'Birth121 selector fixed by immutable339cache and exact live prefix, not selected by output magnitude. No129singlecommand experiment.',
                'Normal avoidance near/far target angles are not defect evidence. This result cannot identify birth/transport/target-following mechanisms uniquely.',
                'GT diagnostic only, hidden solver/OpenCVRNG not directly captured, real occlusion preservation unverified.'],
        preserved334_mixed_evidence=read(R/'stage339/summary-private.json')['preserved334_mixed_evidence'],actual_occlusion_preservation_verified=False,
        next_action='No further native run initiated. Review saved post-intervention route/target/contact chronology at native0 before any new paired proposal.',champion296_preserved=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,authorization_end_utc=p['deadline_utc'])
    save(D/'saved-evidence-verification.json',verification);save(D/'cost.json',cost);save(D/'summary-private.json',public);save(G/'retry/routing340_result.json',public)
    v.update(version=352,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v351.json'),prior_budget_sha256=sha(R/'project-effective-budget-v351.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage340_new_wrapper_actions=used)
    assert not (R/'project-effective-budget-v352.json').exists();save(R/'project-effective-budget-v352.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==340 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(dict(comparison=comparison,verification=verification,cost=cost)),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);close(a.parse_args().private_root)
