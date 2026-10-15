"""Compare qualified official outcomes; charge only the new baseline."""
import argparse
import datetime
import json
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.compare347_stage import verify
from retry.pair343_close import describe


def rows(path):return [json.loads(s) for s in Path(path).read_text().splitlines()]


def close(R):
    D=R/'stage347';G=Path(__file__).resolve().parent.parent;p=verify(R);assert not (D/'cost.json').exists();start,cpu=time.perf_counter(),time.process_time();a=read(D/'A/result.json');b=read(R/'stage346/B/result.json');ar=rows(D/'A/trace-private.jsonl');br=rows(R/'stage346/B/trace-private.jsonl');az=np.load(D/'A/frames-actions-private.npz');bz=np.load(R/'stage346/B/frames-actions-private.npz');budget=read(D/'native-budget.json');self_gate=read(D/'prefix160-qualification.json');pair_gate=read(D/'paired-prefix-qualification.json')
    used=budget['actions'];assert used==budget['arms']['A']==a['native_actions']==len(ar)==len(az['actions'])<=300 and budget['resets']==1 and len(az['frames_uint8'])==used+1
    qualified=bool(not a['technical_error'] and a['comparison_valid'] and self_gate['passed'] and pair_gate['passed'])
    errors=[]
    try:
        assert np.array_equal(az['actions'][:145],bz['actions'][:145]) and np.array_equal(az['frames_uint8'][:146],bz['frames_uint8'][:146])
        for x,y in zip(ar[:145],br[:145]):
            for key in ['features','tracker','support_record','pixel_path','actor_state','nominal_memory','policy','pre','post','pre_physical','post_physical','pre_RNG','post_RNG','raw_observations']:assert x[key]==y[key],key
        assert ar[145]['pre_physical']==br[145]['pre_physical'] and ar[145]['pre_RNG']==br[145]['pre_RNG'] and ar[145]['executed']!=br[145]['executed']
        assert read(D/'A/initial-scene-private.json')==read(R/'stage346/B/initial-scene-private.json') and read(D/'A/initial-RNG-private.json')==read(R/'stage346/B/initial-RNG-private.json')
    except AssertionError as e:qualified=False;errors.append(str(e) or 'shared prefix/reset mismatch')
    assert sum(r['raw_ticks'] for r in ar)==a['raw_step_ticks']==a['raw_counter_at_stop']-a['raw_counter_after_reset'];assert all(not r['terminated'] and not r['truncated'] for r in ar[:-1]);assert a['reaping']['process_reaped'] and a['reaping']['actor_pids_absent']
    for r in ar:
        assert r['executed']==r['returned_action'] and r['nominal_memory']==r['policy']['previous_steer'] and np.float32(r['nominal_memory'])==np.float32(r['executed'][0]);assert r['routing_evidence']['removed_indices']==[]
    for q in [a,b]:
        if q['completed']:assert q['finish']['finish_time_s'] is not None and not q['censored'] and not q['protocol_stop'] and q['lap_ms']==round((q['finish']['finish_time_s']-q['postreset_start_time'])*1000)
    outcomes=dict(A=describe(ar,a),B_existing346=describe(br,b));ordering=None;delta=None
    if qualified:
        if a['completed'] and b['completed']:
            delta=b['lap_ms']-a['lap_ms'];ordering='baseline_A_faster' if delta>0 else 'candidate_B_faster' if delta<0 else 'official_lap_tie'
        elif a['completed']!=b['completed']:ordering='A_only_observed_finish' if a['completed'] else 'B_only_observed_finish'
        else:ordering='no_both_finish_lap_comparison'
    decision='Comparison invalid; no superiority inference permitted.' if not qualified else 'Both officially finished; on this one matched O2condition baselineA is260msfaster and the candidate doesnotimprove the officialobjective.' if ordering=='baseline_A_faster' else 'Qualified one-condition official comparison only; see outcomes and ordering.'
    phases=None
    if qualified and a['completed'] and b['completed']:
        phases=dict(A_qualified_raw_time_s=a['finish']['finish_qualified_time_s'],B_qualified_raw_time_s=b['finish']['finish_qualified_time_s'],qualification_time_delta_B_minus_A_ms=round((b['finish']['finish_qualified_time_s']-a['finish']['finish_qualified_time_s'])*1000),A_postqualification_to_center_ms=round((a['finish']['finish_time_s']-a['finish']['finish_qualified_time_s'])*1000),B_postqualification_to_center_ms=round((b['finish']['finish_time_s']-b['finish']['finish_qualified_time_s'])*1000),scope='Timestamp decomposition only, not independent causal effects of each withheld lineage or controller variable.')
    held=[r for r in br if r['routing_evidence']['removed_indices']];assert len(held)==12 and all(len(r['routing_evidence']['removed_indices'])==1 for r in held)
    next_step=dict(status='Proposed native0diagnostic and final-readiness handoff only, not executed/reserved.',question='Do the two actually withheld Blineages directly change frozen routing/target on their own recorded states, and where does the paired officialtime gap emerge?',
        design='Use all12actual346Bheld frames, two variants perframe: reproduce exact filtered routing then restore only that one withheld footprint. Exact archived296routing/route_target,samepixels/speed/priorsteer/fullremaininghazards. Originalpath/target reproduction gate first; no Agent calls, no GT selection, no stateful rollout. Separately align existing347A/346Braw tile/qualification/finish timelines.',
        budget=dict(frozen_routing_function_calls=24,frozen_route_target_calls=24,new_actor_calls=0,new_native_actions=0,new_environment_resets=0,new_source_physics_rollout_ticks=0,new_learning_fits=0,parameter_sweeps=0,research_remaining_after=513-used,final_reserved_actions_after=84000),
        value='Distinguishes direct routing relevance of146and203from later coupledtrajectory effects without consuming the remaining research native. It cannot uniquely assign the260msclosed-loop gap or justify tuning a cutoff.',
        readiness='Freeze currentchampion296archive/manifest and non-promotion decision; audit research/finalreserve accounting and protected-split unopened sentinels without reading or opening newcases. Keep remainingresearch for technical contingency. Prepare finalvalidation handoff with exactfrozenartifact/officialfinishmetrics/stops; do not run or schedule it automatically.',
        limits='Single postselected knowncondition, diagnostic surrogates only. No policy repair/sweep/extraactualarm. Finalreserve84000stays separate; generalization/occlusion uncertainty remains.')
    v=read(R/'project-effective-budget-v358.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1283725,513,84000,0)
    measures=['wall_s','runner_CPU_s','actor_CPU_s','reset_wall_s','raw_step_render_wall_s','raw_contact_observer_wall_s','capture_wall_s','journal_wall_s','artifact_wall_s']
    cost=dict(stage=347,new_wrapper_actions=used,native_cap=300,new_A_runs=1,new_B_runs=0,new_environment_resets=1,existing_B_stage=346,existing_B_native_actions=b['native_actions'],existing_B_charged_again=False,additional_research=0,raw_step_ticks=a['raw_step_ticks'],raw_reset_ticks=a['raw_reset_ticks'],new_source_physics_rollout_ticks=0,new_learning_fits=0,parameter_sweeps=0,new_paid_resources=0,technical_error=a['technical_error'],technical_recovery_native=0,technical_recovery_resets=0,measurements={k:a[k] for k in measures},closure_wall_s=time.perf_counter()-start,closure_CPU_s=time.process_time()-cpu,actual_cumulative_wrapper_actions=1283725+used,research_remaining=513-used,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1368238,unused_reserved_actions=300-used,measurement_scope='Only newA charged. Reused346Bretains its prior cost entry. Rawstep includesrender; observers/capture/journal/artifactsubtimers are measurements, not additionalphysics. Setup/hash/IPC/report/git not wholly separatetimed.')
    public=dict(stage=347,decision=decision,paired_comparison_valid=qualified,qualification_errors=errors,identity='Exact original296archive/worker/models/environmentcode/initialization/RNGseed matched to346; only the fixedflag disabled innewA and enabled inexistingB. Shared145commands146inputs and fresh actor/tracker/physics/accessRNG/rawticks validated.',new_A_self_reproduction_prefix=160,shared_pair_prefix_actions=145,shared_pair_input_frames=146,first_natural_full_control_difference=146,existing_B_stage=346,existing_B_reexecuted=False,outcomes=outcomes,official_ordering=ordering,candidate_lap_delta_B_minus_A_ms=delta,finish_phase_timestamps=phases,
        limits=['Single knownTRAINcondition, onecontrol setting and onepair; no populationrate/statisticalgeneralization or safety/occlusion conclusion.',
                'Bothfinish comparison uses official retroactivecentercrossing laptime; uniqueprogress/contact/damage are reported but not substituted for officialordering. Censor/DNF separate.',
                'HigherBtime here doesnot prove the observation rule always harms or identify which lineage or controller mechanism caused the difference.',
                'After146actual scenes/memory differ; temporaldecomposition is descriptive, not independent-variable causal attribution.',
                'Hidden solver/OpenCVRNG not directly measured, only accessible state/RNG and exact shared actualprefix. No new protectedsplit or championpromotion.'],cost=cost,next_minimum_experiment=next_step,preserved334_mixed_evidence=read(R/'stage346/summary-private.json')['preserved334_mixed_evidence'],actual_occlusion_preservation_verified=False,champion296_preserved=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,authorization_end_utc=p['deadline_utc'])
    verify(R);save(D/'cost.json',cost);save(D/'summary-private.json',public);save(G/'retry/compare347_result.json',public);save(D/'final-saved-evidence-check.json',dict(passed=qualified,paired_condition_valid=qualified,new_A_only=True,existing_B_not_recounted=True,sharedprefix145fullstatephysicsRNG=True,baseline160selfreproduction=True,both_officialfinish=bool(a['completed'] and b['completed']),lap_delta_B_minus_A_ms=delta,no_rank_from_damage=True,technical_error=a['technical_error'],no_extra_run_started=True))
    v.update(version=359,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v358.json'),prior_budget_sha256=sha(R/'project-effective-budget-v358.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage347_new_wrapper_actions=used);assert not (R/'project-effective-budget-v359.json').exists();save(R/'project-effective-budget-v359.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==347 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(dict(qualified=qualified,outcomes=outcomes,ordering=ordering,lap_delta_B_minus_A_ms=delta,finish_phases=phases,cost=cost,next_budget=next_step['budget'])),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);close(a.parse_args().private_root)
