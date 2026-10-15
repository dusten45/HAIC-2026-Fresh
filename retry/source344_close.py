"""Report source-policy exposure without converting cached differences to wins."""
import argparse
import datetime
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.source344_stage import verify
from retry.confidence341_run import label


def ranges(items):
    out=[]
    for i in items:
        if out and out[-1][1]+1==i:out[-1][1]=i
        else:out.append([i,i])
    return out


def close(R):
    D=R/'stage344';G=Path(__file__).resolve().parent.parent;p=verify(R);assert not (D/'cost.json').exists();start,cpu=time.perf_counter(),time.process_time();assert read(D/'baseline-qualified.json')['passed'];receipts={mode:read(D/mode/'receipt.json') for mode in ['baseline','candidate']};records={mode:read(D/mode/'records-private.json') for mode in receipts};budget=read(D/'call-budget.json');assert budget['actor_calls']==320 and budget['resets']==2
    assert all(q['technical_error'] is None and q['returned_actor_calls']==q['committed_calls']==160 and q['reaping']['process_reaped'] and q['reaping']['actor_pids_absent'] for q in receipts.values())
    gt={int(k):v for k,v in read(R/'stage334/O2/GT-private.json').items()};birth_labels={};births=[];losses=[];diff={k:[] for k in ['routing_input','path','target','target_speed','pedals','steering','float32_action','nominal_memory']};detail=[];max_action=np.zeros(3);max_memory=0.;held=[];supported_direct=supported_retained=0
    for i,(a,b) in enumerate(zip(records['baseline'],records['candidate'])):
        x,y=a['response'],b['response'];assert x['tracker_record']==y['tracker_record'] and x['support_record']==y['support_record'];assert y['routing_evidence']['tracker_preserved']
        fixed=[3,8,11,12];assert [x['features'][k] for k in fixed]==[y['features'][k] for k in fixed]
        if not x['features'][0] and not y['features'][0]:assert x['features'][4]==y['features'][4]
        for birth in y['support_record']['births']:
            lab,identity=label(birth['point'],gt.get(i));uid=tuple(birth['uid']);birth_labels[uid]=dict(label=lab,id=identity)
            if lab=='fixture_supported':supported_direct+=1
            if birth['low']:births.append(dict(birth_action=i+1,direct_index=uid[1],component_area=birth['component_area'],raw_road_neighbors=birth['raw_road_neighbors'],diagnostic_label=lab))
        for j,(point,item) in enumerate(zip(y['tracker_record']['after'],y['support_record']['after'])):
            lab=birth_labels[tuple(item['uid'])]['label']
            if point[3]>0 and lab=='fixture_supported':supported_retained+=1
            if j in y['routing_evidence']['removed_indices']:
                held.append(i+1)
                if lab=='fixture_supported':losses.append(dict(action=i+1,uid=item['uid'],age=point[3]))
        flags=dict(routing_input=bool(y['routing_evidence']['removed_indices']),path=x['pixel_path']!=y['pixel_path'],target=x['features'][:3]!=y['features'][:3],target_speed=x['features'][6]!=y['features'][6],pedals=x['action'][1:]!=y['action'][1:],steering=x['action'][0]!=y['action'][0],float32_action=x['action']!=y['action'],nominal_memory=a['commit']['memory']!=b['commit']['memory'])
        for k,v in flags.items():
            if v:diff[k].append(i+1)
        delta=np.asarray(y['action'])-x['action'];memory_delta=b['commit']['memory']-a['commit']['memory'];max_action=np.maximum(max_action,abs(delta));max_memory=max(max_memory,abs(memory_delta));detail.append(dict(action=i+1,changed=flags,action_delta=delta.tolist(),memory_delta=memory_delta))
    assert births==[dict(birth_action=146,direct_index=0,component_area=4,raw_road_neighbors=0,diagnostic_label='unresolved')];assert held==[146,147,148]
    assert diff['path']==diff['target']==diff['target_speed']==[146] and diff['float32_action']==list(range(146,154)) and diff['nominal_memory']==list(range(146,161))
    snapshots=[]
    for step in [145,146,147,148,149,153,154,160]:
        a=records['baseline'][step-1];b=records['candidate'][step-1];snapshots.append(dict(action=step,baseline_target=a['response']['features'][1:3],candidate_target=b['response']['features'][1:3],baseline_target_speed=a['response']['features'][6],candidate_target_speed=b['response']['features'][6],baseline_control=a['response']['action'],candidate_control=b['response']['action'],nominal_memory_delta=b['commit']['memory']-a['commit']['memory']))
    v=read(R/'project-effective-budget-v355.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1283122,1116,84000,0)
    cost=dict(stage=344,new_wrapper_actions=0,new_native_actions=0,new_environment_resets=0,new_source_physics_ticks=0,new_learning_fits=0,parameter_sweeps=0,new_paid_resources=0,cached_actor_calls=320,actor_resets_on_stored_pixels=2,technical_recovery_actor_calls=0,technical_recovery_resets=0,technical_error=None,execution_wall_s=sum(q['wall_s'] for q in receipts.values()),runner_CPU_s=sum(q['runner_CPU_s'] for q in receipts.values()),actor_CPU_s=sum(q['actor_CPU_s'] for q in receipts.values()),closure_wall_s=time.perf_counter()-start,closure_CPU_s=time.process_time()-cpu,actual_cumulative_wrapper_actions=1283122,research_remaining=1116,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1368238,measurement_scope='Actor phases timed including journals and finaldata save; preflight,sourceidentification,build,offlinequalification,interactiveinspection,report/git not wholly timed. No simulator call or physics timing.')
    proposal=dict(status='Proposal only; no native scheduled/reserved.',question='Does the identical observation rule cause local harm at the now source-policy-qualified reachable O2near-car exposure?',
        design='Two fresh O2arms using exact frozen296source-policy baseline and the unchanged342rule, max160native each. Historical collection has no original full actor pickle or accessibleRNGsnapshot; use fresh independent A/B to qualify those live common-prefix fields rather than claim they were stored. Current334ON/H1is not substituted.',
        gates='Freeze original296archive and source original tracker/controller/models; onlyflag bookkeeping may follow that existing straight fallback. Verify reset,commands,pixels,actor/tracker/capturedphysics/accessRNG until first naturally different fullcontrol. Historical storedprefix and344qualifiedbaseline provide extra reference, not forced146intervention. Both thereafter own observations/fullcontrols/normalmemory.',
        budget=dict(per_arm_cap=160,total_native_cap=320,new_A_runs=1,new_B_runs=1,new_environment_resets_cap=2,maximum_postreset_raw_ticks=1280,expected_reset_raw_ticks=102,additional_budget_needed=0,research_remaining_after_maximum=796,final_reserved_actions=84000,final_reserve_used=0),
        stop='Officialterminal,160cap,qualification/integrity/deadline failure. If exposure does not occur naturally, label unexposed without extension. No new cutoff,extraarm,fit,protectedsplit orpromotion.',
        outcomes='Joint fixture/time/touching,damage,tileprogress,speed,officialretirement/finish andposthoc supportedpoint withholding. New earlier contact/blockage or supportedloss is local counterexample; damagealone isnot officialscore.160survival nofinish isprotocolcensor.',
        value='344removes the policy/visitation mismatch that made343unexposed. This is the smallest fully live-qualified two-arm local check within the agreed160horizon; reuse of old A would leave unrecorded original actor/RNG fields unverified. It tests this source-policy context only, not currentH1or global safety.')
    public=dict(stage=344,decision='Source-policy cached exposure established; no supported-point loss observed. This is not an actual avoidance/safety/completion result and does not change343current-policy unexposed conclusion.',policy_identity=dict(archive_sha256=p['original_config']['archive_sha256'],original_worker_sha256=p['original_config']['worker_sha256'],historical_loaded_module_hashes_exact=True,source='Historical306O2collection frozen296, original straight HUDspeed fallback. NoH1/current334ONsubstitution.'),
        verification=read(D/'baseline-qualified.json'),source_state_limit='Historical trace stores nominal memory/features/actions, no full actor pickle/RNG snapshot. Five-field original worker contract is independently reconstructed from source pixels, qualified334OFFtracker, sourceconstants and original history, not falsely claimed as stored full state.',
        flagged_births=births,routing_withheld_actions=held,changed_ranges={k:ranges(a) for k,a in diff.items()},unchanged_float32_action_ranges=[[1,145],[154,160]],unchanged_float32_actions=152,maximum_absolute_action_delta=max_action.tolist(),maximum_absolute_nominal_memory_delta=max_memory,nominal_memory_difference_right_censored_at160=True,selected_aggregate_comparison=snapshots,
        tracker_and_support_lineage_exact=True,supported_direct_detections_checked=supported_direct,supported_birth_retained_contexts_checked=supported_retained,supported_routing_losses=len(losses),supported_loss_details=losses,cache_gate_passed=not losses,
        interpretation=['Original sourcepolicy reaches the near-car146birth and samepixelrule changes path,target,speedgoal,fullcontrol andnormalmemory146. No forcedstep orcoordinate condition.',
                        'Footprint held146-148; path/target differonly146. Control recursion differs146-153; float64memory still differs through160evenwhen154-160float32commands match. Laterconvergence isunobserved.',
                        '343usedcurrent334ON/H1andwascontrol-unexposedat160despite137predicate. Sourcepolicy and visitingpixels differ; results are complementary, not a reclassification of343.',
                        'Birth remains unresolved, not semantic falsepositive. The actualsourceO2historical trajectory belongs tobaseline only; candidate cached controls do not provide a new actual trajectory.'],
        limits=['One rule selected posthoc in341, one known source-road cache; no independent generalization or real occlusion/material labels.',
                'Exact original archive and original worker identified; metadata adapts only to existing originalstraight fallback. Birthrule unchanged, not a new motion model.',
                'Missing original full pickle/RNG remains explicit. Only available stored state and independently reconstructed originalstate contract reproduced.',
                'Zero captured supported loss cannot prove absence of dangerous real clipped/occluded obstacles. No actual completion, native or promotion in344.'],cost=cost,next_minimum_actual_validation=proposal,preserved334_mixed_evidence=read(R/'stage343/summary-private.json')['preserved334_mixed_evidence'],actual_occlusion_preservation_verified=False,champion296_preserved=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,authorization_end_utc=p['deadline_utc'])
    verify(R);save(D/'comparisons-private.json',detail);save(D/'cost.json',cost);save(D/'summary-private.json',public);save(G/'retry/source344_result.json',public);save(D/'final-saved-evidence-check.json',dict(passed=True,actor320cap_exact=True,stored_pixel_resets2=True,original_source_policy_identified=True,original_available_state_and_commands_reproduced=True,full_original_pickle_unavailable_explicit=True,first_natural_cache_difference146=True,tracker_lineage_unchanged=True,supported_losses=len(losses),new_native_actions=0,new_environment_resets=0,next_actual_pair_not_started=True))
    v.update(version=356,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v355.json'),prior_budget_sha256=sha(R/'project-effective-budget-v355.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,stage344_new_wrapper_actions=0);assert not (R/'project-effective-budget-v356.json').exists();save(R/'project-effective-budget-v356.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(__import__('json').loads(s).get('stage')==344 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(__import__('json').dumps(cost)+'\n')
    print(__import__('json').dumps(dict(changes=public['changed_ranges'],snapshots=snapshots,supported_direct=supported_direct,supported_retained=supported_retained,losses=losses,cost=cost,next_actual_native_cap=320)),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);close(a.parse_args().private_root)
