"""Close own-state tracker rollout, preserve reference and334 mixed evidence."""
import argparse
import datetime
import json
import math
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.steering333_close import outcome


def rows(path):return [json.loads(s) for s in Path(path).read_text().splitlines()]


def close(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage335';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert not (D/'cost.json').exists()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    result=read(D/'B/result.json');A_result=read(R/'stage331/A/result.json');a=rows(R/'stage331/A/trace-private.jsonl');b=rows(D/'B/trace-private.jsonl');z=np.load(D/'B/raw-pixels-actions-private.npz');reference=np.load(R/'stage331/A/raw-pixels-actions-private.npz');budget=read(D/'native-budget.json');used=budget['actions'];assert used==result['native_actions']<=72
    comparison=None;valid=result['comparison_valid'];diagnostic=None
    if valid:
        assert len(b)==used==len(z['actions']) and len(z['observations'])==used+1;assert all(not x['terminal'] for x in b[:-1])
        assert np.array_equal(z['actions'],np.array([r['returned_action'] for r in b],np.float32));assert np.array_equal(z['actions'],np.array([r['executed'] for r in b],np.float32))
        for row in b:assert row['nominal_memory']==row['policy']['previous_steer'] and np.float32(row['nominal_memory'])==np.float32(row['executed'][0]) and row['audit']['action']==row['executed']
        prefix=result['actual_common_prefix_commands'];assert np.array_equal(z['actions'][:prefix],reference['actions'][:prefix]) and np.array_equal(z['observations'][:prefix+1],reference['observations'][:prefix+1])
        assert next((i+1 for i in range(used) if not np.array_equal(z['actions'][i],reference['actions'][i])),None)==result['first_differences']['command']
        qualified=read(D/'B/common-prefix-qualification-private.json');assert len(qualified)>=prefix+1 and all(r['pixels'] and r['ON_cached_state'] and r['measured_physical_available'] and r['accessible_RNG'] for r in qualified)
        assert result['reaping']['process_reaped'] and result['reaping']['actor_pids_absent']
        common=min(len(a),len(b));comparison=dict(common_actions=common,A=outcome(a,A_result,common),B=outcome(b,result,common),endpoint_position_gap_m=float(np.linalg.norm(np.array(a[common-1]['post']['position'])-b[common-1]['post']['position'])),endpoint_heading_difference_B_minus_A_rad=float(math.atan2(math.sin(b[common-1]['post']['angle']-a[common-1]['post']['angle']),math.cos(b[common-1]['post']['angle']-a[common-1]['post']['angle']))),endpoint_unique_tiles_B_minus_A=int(b[common-1]['post']['unique_tiles']-a[common-1]['post']['unique_tiles']))
        delta=z['actions']-reference['actions'][:used];memory=np.array([r['nominal_memory'] for r in b])-np.array([r['nominal_memory'] for r in a[:used]])
        diagnostic=dict(actual_common_prefix_commands=prefix,common_prefix_input_stacks=prefix+1,first_observed_differences=result['first_differences'],component_names=['steering','gas','brake'],changed_command_counts=(delta!=0).sum(0).tolist(),mean_absolute_command_differences=abs(delta).mean(0).tolist(),maximum_absolute_command_differences=abs(delta).max(0).tolist(),nominal_memory_changed_count=int((memory!=0).sum()),maximum_absolute_nominal_memory_difference=float(abs(memory).max()),ON_tracker_optical_inputs=sum(r['tracker']['affine'] is not None for r in b),ON_tracker_fallback_with_points_inputs=sum(r['tracker']['affine'] is None and bool(r['tracker']['before']) for r in b))
    verification=dict(passed=valid,own_observations_used=True,all_returned_steer_gas_brake_executed=valid,stored_command_override=False,first_difference_not_forced=True,unchanged334_archive_sha256=p['configs']['ON']['archive_sha256'],fresh_OFF72_exact_A=read(D/'cache-receipt.json')['passed'],qualified_actual_prefix=diagnostic,hidden_solver_and_OpenCV_RNG_directly_measured=False,actual_occlusion_preservation_verified=False,new_native_actions_for_saved_verification=0)
    save(D/'independent-verification.json',verification)
    prior=R/'project-effective-budget-v343.json';v=read(prior);assert v['actual_cumulative_wrapper_actions']==1282127 and v['research_remaining']==72 and v['B_operating_cap']==1366199 and v['final_reserved_actions']==84000 and v['final_reserve_used']==0
    cache=read(D/'cache-receipt.json');cost=dict(stage=335,new_wrapper_actions=used,native_cap=72,new_B_runs=1,new_A_runs=0,reused_actual_A_runs=1,additional_research=72,raw_step_ticks=result['raw_step_ticks'],raw_reset_ticks=result['raw_reset_ticks'],native_wall_s=result['wall_s'],runner_CPU_s=result['runner_CPU_s'],actor_CPU_s=result['actor_CPU_s'],cached_actor_calls=144,cache_wall_s=sum(r['wall_s'] for r in cache['receipts']),cache_runner_CPU_s=sum(r['runner_CPU_s'] for r in cache['receipts']),cache_actor_CPU_s=sum(r['actor_CPU_s'] for r in cache['receipts']),new_learning_fits=0,new_source_physics_ticks=0,new_paid_resources=0,actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions']+used,research_remaining=v['research_remaining']-used,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=v['B_operating_cap'])
    save(D/'cost.json',cost);v.update(version=344,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage335_new_wrapper_actions=used)
    assert not (R/'project-effective-budget-v344.json').exists();save(R/'project-effective-budget-v344.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==335 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    old=read(R/'stage334/summary-private.json');raw=old['nearest_association_original']['original6'];subset=old['posthoc_fixture_birth_audit']['aggregate']['original6'];context=dict(original6_nearest_sequential_mean={mode:raw['all']['sequential'][mode]['error']['mean'] for mode in ['OFF','ON']},original6_nearest_single_fallback_RMSE={mode:raw['fallback']['single_interval'][mode]['RMSE'] for mode in ['OFF','ON']},posthoc_fixture_birth_subset_fallback_mean={mode:subset['fallback']['paired'][mode]['mean'] for mode in ['OFF','ON']},posthoc_fixture_birth_subset_fallback_p99={mode:subset['fallback']['paired'][mode]['p99'] for mode in ['OFF','ON']},fixture_birth_coverage=old['posthoc_fixture_birth_audit']['aggregate']['original6']['coverage'],actual_occlusion_preservation_verified=False,original334_immutable=True)
    if not valid:interpretation='Contract mismatch; causal comparison invalid, no repair/reseed or automatic newA.'
    elif comparison['B']['first_contact'] is None and comparison['A']['first_contact'] is not None:interpretation='Fallback-only tracker on its own visited states avoided observed contact through72, while actualA contacted68-72 and crashed72. Local72-action closed-loop evidence; not completion/generalization or champion promotion. Static association ambiguity and unverified occlusion remain.'
    else:interpretation='Assess actual common-interval contact/termination/progress jointly. Damage is not an independent veto. Same/worse refutes this candidate local sufficiency, not every stale-coordinate defect.'
    full296=next(r for r in read(R/'stage330/plan.json')['baseline296']['results'] if r['road']=='N2');assert full296['native_actions']==363 and full296['completed']
    next_proposal=dict(status='Proposed only; not executed, no automatic horizon extension or budget grant',question='Does the frozen tracker candidate retain the local rescue beyond72 and complete the knownN2 lap?',new_B_native_cap=363,measured_horizon_basis='Existing296N2 actual completed363actions/29000ms; this cap is a measured full-lap attempt horizon, not a guarantee candidate completes by it.',new_research_budget_required=363,final_reserve_used=0,
        replay_cost='Actual335 environment closed; cannot resume for free or teleport. New trial starts reset, includes measured72prefix and up to291unseen actions, totalcap363.',A='Reuse qualified330/331A actualDNF72 plus296N2 fullcompletion as distinct references; ifA qualification unclear stop before native and separately report additionalA72 cost, do not launch automatically.',
        qualification='Same unchanged334archive/worker/runtime/case; requalify exact33572prefix observations/actions/controller and tracker state/accessibleRNG/physical measurements. Unexpected mismatch stops, no reseed/retry.',stop='Official completion/retirement,363protocolcap,contractmismatch orauthorizationdeadline; capwithoutcompletion is protocolcensoring, notDNF. No automatic capextension.',interpretation='Official completion required to claimN2 completion rescue. Compare common completed time only to actual296 fullreference. KnownTRAIN onecase remains no generalization or promotion; damage increase alone not veto.',occlusion='Independent visibility/occlusion evidence still needed before general tracker claims; do not call nondetection occlusion.')
    public=dict(stage=335,question=p['question'],design=p['design'],comparison_valid=valid,verification=verification,common_interval_comparison=comparison,control_memory_diagnostic=diagnostic,interpretation=interpretation,preserved334_mixed_evidence=context,cost=cost,next_distinguishing_experiment=next_proposal,
        limitations=['Single postselected knownTRAIN N2,72action local horizon; B protocolstop is neither completion nor actualDNF.',
            'Only fallback component archive changed vs actualA. New own-state control differs in multiple downstream steer/pedal/memory updates;335 is not333single-command experiment.',
            'Actual captured physical states and accessible RNG checked along commonprefix. Earlier basic state reference is independent333 measured sharedprefix, not fabricated historicalA GT.',
            'Hidden Box2D solver state/OpenCV RNG not directly measured; contacttime interval.08seconds and fixture snapshots only wrapperendpoints.',
            '334nearest metrics worsened despite fixture-supported posthoc subset gain; unknown correspondence and actualocclusion preservation unverified.'],champion296_preserved=True,TRAIN_registry_preserved=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,authorization_end_utc=p['deadline_utc'])
    save(D/'summary-private.json',public);save(G/'retry/closed335_result.json',public);print(json.dumps(dict(comparison=comparison,diagnostic=diagnostic,cost=cost,interpretation=interpretation)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',required=True,type=Path);close(p.parse_args().private_root)
