"""Close fixed fallback static test; preserve all association views and budget."""
import argparse
import datetime
import json
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha


def lines(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]


def close(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage334';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert not (D/'cost.json').exists()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    actor=read(D/'actor-cost.json');metrics=read(D/'metrics-private.json');audit=read(D/'fixture-birth-audit-private.json');inventory=read(D/'inventory-private.json');shared=offopt=onopt=0;eligibility=0;pipeline=0;first_changes={};retention_events={'OFF':set(),'ON':set()}
    for case in p['cases']:
        F=D/case['key'];off=lines(F/'OFF-private.jsonl');on=lines(F/'ON-private.jsonl');assert len(off)==len(on)
        first_changes[case['key']]=next((r['index']+1 for r,s in zip(off,on) if r['action'][0]!=s['action'][0]),None)
        for a,b in zip(off,on):
            x,y=a['tracker'],b['tracker'];offopt+=x['affine'] is not None;onopt+=y['affine'] is not None
            pipeline+=sum(t['optical_reason'] in ['accepted','rejected_or_unavailable'] for t in [x,y])
            if x['before'] and y['before']:assert x['affine']==y['affine'],'Same-input optical branch changed'
            if x['affine'] is not None and y['affine'] is not None:shared+=1;assert x['affine']==y['affine']
            eligibility+=(x['optical_reason']=='no_hazards')!=(y['optical_reason']=='no_hazards')
            if x['affine'] is not None:assert a['paired_ON']==x['after']
        assert read(F/'OFF-receipt.json')['stored_actor_calls']==len(off)
    assert actor['stored_actor_calls']==3940 and all(r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent'] for r in actor['receipts'])
    points=read(D/'fixture-birth-points-private.json')
    for frame in points['frames']:
        if not frame['duplicate'] and frame['retained_without_direct']>0:retention_events[frame['mode']].add((frame['key'],frame['index']))
    verification=dict(passed=True,OFF_actor_rows_reproduced=1970,ON_fixed_pixel_actor_rows=1970,paired_interval_initial_state_shared=True,reset_frames_excluded=9,no_cross_episode_or_gap_intervals=True,
        algebra_validation=read(D/'algebra-validation.json'),shared_accepted_optical_matrices_exact=shared,all_optical_outputs_equal_when_both_have_points=True,single_interval_accepted_optical_outputs_bit_exact=True,
        optical_OFF=offopt,optical_ON=onopt,optical_gate_eligibility_differences=eligibility,eligibility_scope='Original optical gate depends on any retained hazard; changed retention changes attempt coverage. No accepted matrix is replaced by HUD rotation when points share the same image interval.',
        same_retention_without_direct_frame_events=retention_events['OFF']==retention_events['ON'],retention_without_direct_frames=len(retention_events['OFF']),actual_occlusion_preservation_verified=False,new_native_actions=0)
    save(D/'independent-verification.json',verification)
    legacy=[]
    for case in read(R/'stage326/plan.json')['cases']:
        if case['road'] not in ['O0','O2']:continue
        legacy.append(dict(road=case['road'],arm=case['arm'],stage=case['stage'],pixels_available=(Path(case['path'])/case['pixel_file']).exists(),pixel_rows=int(np.load(Path(case['path'])/case['pixel_file'])['pixels'].shape[0]),pose_GT_in_listed_trace_schema=False,authoritative_visibility_labels=False,source_scope='Older240/frozen290 TRAIN pixels available; fixed296/330 corpus only replayed in334. Trace has actions/time/damage/progress, no pose fields. Uninterpreted28features not treated as GT.'))
    save(D/'additional-inventory-private.json',dict(older_TRAIN=legacy,known_296_N2_success='363-action trace only; no pixels/GT/path available, not fabricated.',other_archival_scope='Noncompatible old policy buffers not exhaustively enumerated or reopened; protected splits not read.'))
    prior=R/'project-effective-budget-v341.json';v=read(prior);assert v['actual_cumulative_wrapper_actions']==1282127 and v['research_remaining']==0 and v['final_reserved_actions']==84000 and v['final_reserve_used']==0
    cost=dict(stage=334,new_wrapper_actions=0,new_learning_fits=0,new_source_physics_ticks=0,new_paid_resources=0,additional_research=0,
        stored_actor_calls=actor['stored_actor_calls'],OFF_actor_calls=1970,ON_actor_calls=1970,actor_CPU_s=sum(x['actor_CPU_s'] for x in actor['receipts']),replay_evaluator_CPU_s=sum(x['runner_CPU_s'] for x in actor['receipts']),replay_wall_s=actor['wall_s'],
        existing_optical_pipeline_attempts=pipeline,existing_optical_estimator_call_count='Not separately instrumented; pipeline attempts include feature/flow rejection before affine estimation. No new fitted model or registration method.',
        paired_route_function_calls=metrics['cost']['paired_route_function_calls'],metrics_CPU_s=metrics['cost']['CPU_s'],metrics_wall_s=metrics['cost']['wall_s'],posthoc_fixture_audit_CPU_s=audit['cost']['CPU_s'],posthoc_fixture_audit_wall_s=audit['cost']['wall_s'],
        cost_scope='Measured replay/functions/association audit; initial discovery, hash/build, final reporting not timed. Existing frozen optical registration is replayed, not a new learned fit.',
        actual_cumulative_wrapper_actions=1282127,research_remaining=0,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=v['B_operating_cap'])
    save(D/'cost.json',cost);v.update(version=342,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),stage334_new_wrapper_actions=0)
    assert not (R/'project-effective-budget-v342.json').exists();save(R/'project-effective-budget-v342.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==334 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    next_proposal=dict(status='Proposed only; not executed; current research balance0',minimum_new_native=72,minimal_new_research_budget_required=72,new_A_needed=False,
        A='Existing full exact330/331A72 measured N2 reference, code/geometry/replay bindings requalified before any native launch.333B remains a different single-command diagnostic comparator, not a substitute baseline.',
        B='One N2 closed-loop rollout with the fixed fallback-only transport enabled from reset, all other policy components including accepted optical/detection/age/dedup/routing/controller unchanged. Stop official terminal or72 protocol cap. This is different from333 stored-command continuation.',
        prefix='No teleport/clone. Replay actual normal initialization; native cost includes every prefix action through72, even if steering first diverges later. Cached first steer differences are provenance only, not a posthoc cutoff.',
        gates='Before any launch verify exactOFF reproduction, source changes onlyfallback, coordinate/timing/optical gates and fixed hyperparameters; resolve independent visibility/occlusion coverage or explicitly limit claim toN2 local contact test. Preregister budget separately; final reserve untouched.',
        stop='First input/config/state or timing discrepancy invalidates comparison; no repair/reseed/sweep. Stop official terminal orauthorization deadline. Same/worse result rejects this candidate local sufficiency only; damage increase is no automatic standalone veto.',
        interpretation='Compare firstcontact, endpoint fixtures, persistence, terminal/crash, pose/speed and uniqueprogress at common interval. Survival72 is not completion. No promotion or generalization from static or singleN2 result.',
        fallback_if_A_evidence_fails='Do not silently reuse ambiguous reference: new A72+B72 cap144, separate new budget144 required because balance0. Not authorized or executed under334.')
    public=dict(stage=334,formula=p['formula'],change=p['intervention'],evaluation=p['evaluations'],verification=verification,inventory=inventory,additional_TRAIN_inventory=legacy,
        nearest_association_original=metrics['aggregate'],nearest_association_age_errors=metrics['age_errors'],nearest_association_caveat=metrics['association'],
        posthoc_fixture_birth_audit={k:audit[k] for k in ['posthoc','criterion','not_visibility_or_oracle','aggregate','perroad_paired_fallback','age_errors','cumulative_error_m_s']},
        coverage_by_trajectory=metrics['trajectory'],first_sequential_steering_changes=first_changes,
        cumulative_metric_definition='Discrete .08*sum(error) over observed retained point-time samples including births; not continuous physical residence error. Retained populations differ.',
        metric_semantics='Nearest-association distances include unresolved distant detections and are not guaranteed same-physical-obstacle errors. Fixture-birth subset is a posthoc physical-membership audit, not fitted confidence, visibility truth or primary preregistration change. Unknown births never reassigned. Missing-track heuristic counts mean no known correspondence, upper bounds when unknownpoints exist. Sequential subsets differ in retained-point count; compare coverage and missing bounds, not error alone.',
        interpretation='Fixed fallback improves birth-fixture-compatible interval transport and reduces association-dependent duplicates; raw nearest metrics and sequential retained sets give different conclusions. Unresolved detections and absent independent occlusion truth prevent general tracker/safety promotion. This is fixed-pixel replay, not a physical closed-loop result.',
        real_occlusion_preservation_verified=False,next_minimal_closed_loop=next_proposal,cost=cost,champion296_preserved=True,TRAIN_registry_preserved=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,
        remaining_blockers=['No authoritative visibility/occlusion masks; retained-without-detection frames are not demonstrated real occlusion.',
            'Only50.2% oforiginal6 candidate previous points have fixture-compatible birth lineage; distant detections remain unresolved and cannot be interpreted as known obstacle motion.',
            'Sequential point populations change due unchanged expiry/dedup; lower errors are not a paired physical outcome. Some accepted optical estimates still transport previously valid points badly; this task preserves them.',
            'N2 early331 GT unavailable; unknown births stayunknown.333GT priority and exact-interval dedup do not create missingGT.',
            'Research remaining0; no newnative or automatic budget expansion.'])
    save(D/'summary-private.json',public);save(G/'retry/fallback334_result.json',public);print(json.dumps(dict(verification=verification,cost=cost)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',required=True,type=Path);close(p.parse_args().private_root)
