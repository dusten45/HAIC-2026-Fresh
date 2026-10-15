"""Summarize complete cached pairs and all flagged births; never run a native test."""
import argparse
import datetime
import json
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.support342_stage import verify
from retry.confidence341_run import observations,label
from retry.fallback334_math import advance


def load(path):
    records=[]
    for row in map(json.loads,Path(path).read_text().splitlines()):
        if 'response' in row:
            assert row['index']==len(records);records.append(row)
        else:
            assert row['index']==len(records)-1 and records[-1]['commit'] is None;records[-1]['commit']=row['commit']
    assert all(q['commit'] is not None for q in records)
    return records


def ranges(values):
    out=[]
    for v in values:
        if out and out[-1][1]+1==v:out[-1][1]=v
        else:out.append([v,v])
    return out


def close(R):
    D=R/'stage342';G=Path(__file__).resolve().parent.parent;p=verify(R);result=read(D/'run-result.json');assert not (D/'cost.json').exists();assert result['passed'] and not result['technical_error'] and not result['supported_losses'];start,cpu=time.perf_counter(),time.process_time()
    assert result['charged_actor_calls']==2630 and result['charged_actor_resets']==10 and result['baseline337_qualified'];pre=read(D/'preflight.json');assert pre['passed']
    summary=[];births=[];all_comparisons=[];supported_direct=supported_retained=0;unchanged_total=0
    for case in p['cases']:
        key=case['key'];_,_,gt=observations(case);a=load(D/key/'baseline/records-private.jsonl');b=load(D/key/'candidate/records-private.jsonl');assert len(a)==len(b)
        keys=['routing_input','path','target','target_speed','pedals','steering','float32_action','nominal_memory'];changed={k:[] for k in keys};details=[];birth_metadata={};labels={};max_delta=np.zeros(3);max_memory=0.
        for i,(aa,bb) in enumerate(zip(a,b)):
            x,y=aa['response'],bb['response'];f=y['routing_evidence'];sr=y['support_record'];assert x['tracker_record']==y['tracker_record'] and x['support_record']==sr
            assert [q['low'] for q in sr['after']]==[q['low'] for q in x['support_record']['after']]
            for item in sr['births']:
                uid=tuple(item['uid']);lab,_=label(item['point'],gt.get(i));labels[uid]=lab
                if lab=='fixture_supported':supported_direct+=1;assert not item['low']
                if item['low']:birth_metadata[uid]=dict(key=key,birth_action=i+1,direct_index=uid[1],component_area=item['component_area'],raw_road_neighbors=item['raw_road_neighbors'],diagnostic_label=lab,selected_actions=[],observed_lifetime_actions=[],last_age=None)
            for j,(point,item) in enumerate(zip(y['tracker_record']['after'],sr['after'])):
                uid=tuple(item['uid'])
                if point[3]>0 and labels[uid]=='fixture_supported':supported_retained+=1;assert j not in f['removed_indices']
                if uid in birth_metadata:
                    m=birth_metadata[uid];m['observed_lifetime_actions'].append(i+1);m['last_age']=point[3]
                    if j in f['removed_indices']:m['selected_actions'].append(i+1)
            flags=dict(routing_input=bool(f['removed_indices']),path=x['pixel_path']!=y['pixel_path'],target=x['features'][:3]!=y['features'][:3],target_speed=x['features'][6]!=y['features'][6],pedals=x['action'][1:]!=y['action'][1:],steering=x['action'][0]!=y['action'][0],float32_action=x['action']!=y['action'],nominal_memory=aa['commit']['memory']!=bb['commit']['memory'])
            for k,v in flags.items():
                if v:changed[k].append(i+1)
            delta=np.asarray(y['action'])-x['action'];memory_delta=bb['commit']['memory']-aa['commit']['memory'];max_delta=np.maximum(max_delta,abs(delta));max_memory=max(max_memory,abs(memory_delta))
            details.append(dict(key=key,action=i+1,changed=flags,action_delta=delta.tolist(),memory_delta=memory_delta,target_before=x['features'][1:3],target_after=y['features'][1:3],target_speed_before=x['features'][6],target_speed_after=y['features'][6]))
        for uid,m in birth_metadata.items():
            last=m['observed_lifetime_actions'][-1];m['right_censored_at_saved_endpoint']=last==len(b)
            if last==len(b):m['end_reason']='saved_endpoint_censor'
            elif m['last_age']>=8:m['end_reason']='original_age_expiry'
            else:
                prev=b[last-1]['response'];next_response=b[last]['response'];old_index=[tuple(q['uid']) for q in prev['support_record']['after']].index(uid);t=next_response['tracker_record'];_,_,transported=advance(t['before'],t['direct'],t['affine'],t['previous_yaw'],t['current_yaw'],t['current_speed'],True);x,y,_,_=transported[old_index]
                m['end_reason']='original_spatial_expiry' if not(abs(x)<=35 and -5<=y<=35) else 'original_direct_dedup'
            m['observed_lifetime_ranges']=ranges(m.pop('observed_lifetime_actions'));m['selected_ranges']=ranges(m.pop('selected_actions'));births.append(m)
        unchanged=[q['action'] for q in details if not q['changed']['float32_action']];unchanged_total+=len(unchanged)
        summary.append(dict(key=key,input_frames=len(a),change_ranges={k:ranges(v) for k,v in changed.items()},change_counts={k:len(v) for k,v in changed.items()},unchanged_float32_action_ranges=ranges(unchanged),unchanged_float32_actions=len(unchanged),maximum_absolute_action_delta=max_delta.tolist(),maximum_absolute_nominal_memory_delta=max_memory,tracker_and_support_lineage_exact=True,supported_point_routing_losses=0))
        all_comparisons+=details
    assert len(births)==7 and all(q['diagnostic_label']=='unresolved' for q in births)
    assert sum(q['input_frames'] for q in summary)==1315
    for key in ['O0','T2959']:assert next(q for q in summary if q['key']==key)['change_counts']['float32_action']==0
    n=next(q for q in summary if q['key']=='N2_337');assert n['change_ranges']['path']==[[127,129]] and n['change_ranges']['target']==[[128,129]]
    untouched=[q for q in pre['cases'] if q.get('all_direct_predicates_false')];assert len(untouched)==6 and sum(q['inputs'] for q in untouched)==1121
    proposal=dict(status='Proposed only; no native scheduled/reserved/executed.',question='Does the only new nonN2cache path effect near the car help or harm actual avoidance on the existing O2road?',
        design='One fresh matched pair on the existingO2case, current frozen334ON/H1 baseline versus exactly the observation rule. Historical O2actual collection used a different policy; do not reuse it as a qualified current baseline. Same reset/road/accessibleRNG, no other changes. Verify commands/pixels/actor/tracker/physics through the first naturally rule-induced full-control difference; then own observations, full controls and normal memory.',
        per_arm_native_cap=160,new_A_runs=1,new_B_runs=1,total_native_cap=320,new_environment_resets_cap=2,maximum_postreset_raw_ticks=1280,expected_total_reset_ticks=102,additional_budget_needed=0,research_remaining_after_maximum=1116,final_reserved_actions=84000,final_reserve_used=0,
        horizon='Bounded local falsification around the146effect observed on historical saved pixels. Current policy may visit different states: no forced146activation or source-prefix assumption. If no natural rule exposure before160, label unexposed/inconclusive; no automatic horizon extension.',
        gates='Freeze the exact legal rule and current archive; preserve342cache gate. Qualify independent pair reset and common prefix before natural branch, pixel-only actor, no GT selection. Missing prefix qualification or supported-point removal stops the candidate as failure, not success.',
        outcomes='Joint first contact fixture/time, damage, touching persistence, unique-tile progress, speed and official retirement/finish. Report every held birth. Any new early contact/blockage or supported loss is a local counterexample; no damage-only or cached-speed win.160survival withoutfinish isprotocolcensor, not completion.',
        limits='O2near-car birth has unresolved material/occlusion label, so cache clearance is not safety proof. This one pair cannot validate all unseen real obstacles or general completion. No new cutoff, extra arm, tuning or automatic promotion.')
    verify(R);v=read(R/'project-effective-budget-v353.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1282802,1436,84000,0)
    cost=dict(stage=342,new_wrapper_actions=0,new_native_actions=0,new_environment_resets=0,new_source_physics_ticks=0,new_learning_fits=0,parameter_sweeps=0,new_paid_resources=0,cached_actor_calls=2630,actor_resets_on_stored_pixels=10,processed_paired_input_frames=1315,untouched_input_frames_checked=1121,execution_wall_s=result['wall_s'],runner_CPU_s=result['runner_CPU_s'],actor_CPU_s=result['actor_CPU_s_known'],closure_wall_s=time.perf_counter()-start,closure_CPU_s=time.process_time()-cpu,technical_recovery_actor_calls=0,technical_recovery_resets=0,technical_error=None,actual_cumulative_wrapper_actions=1282802,research_remaining=1436,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1368238,measurement_scope='Cached execution includes preflight,loading,hash/IPC/journals; actorCPUincludes initialization. Closure separately timed. Initialbuild/coding/interactivechecks/report/gitnot wholly timed; no pure simulator metric.')
    public=dict(stage=342,decision='Registered cached-policy gate passed only. A legal observation rule reproduces the knownN2routing effect and adds a near-car O2effect, with zero captured fixture-supported losses. No actual trajectory improvement or general safety established.',baseline337_qualified=True,actor_call_cap_respected=True,reset_cap_respected=True,supported_direct_detections_checked=supported_direct,supported_birth_retained_point_contexts_checked=supported_retained,supported_routing_losses=0,
        all_flagged_births=births,pairs=summary,untouched_cases=untouched,total_unchanged_float32_actions=unchanged_total,
        rule='Freshcomponent zero raw-road support in immediately adjacent1pixel8-neighbor ring marks low support; exclude only that tracked source lineage hard routing footprint until ordinary source dedup/expiry. Every new direct detection re-evaluates its own pixels. Flags do not use step,coordinates,GT,futureobservations; IDs are audit bookkeeping only.',
        preserved='Detector/tracker/association/dedup/age/expiry, near schedule/count/min-distance definitions, models/controller/lookahead unchanged. Full returned controls and normal own nominal memory on fixed common pixels.',
        interpretation=['N2footprint held121-129without a frame rule, but output first differs127 and path only127-129. Holding121-126has no output effect. No current obstacle suppressed.',
                        'O0andT2959selected births yield identical paths,targets,float32controls and memory throughout. O2changes path/target only146, with later recursive memory/control residue.',
                        'Memory can remain different after float32commands match and after filtering ends. These are fixed-pixel own-memory continuations, not physical trajectories or independent per-frame effects.',
                        'Seven episode births include the same121birth in337/340sharedprefix, corresponding to six deduplicated341observations. All material labels remain unresolved.'],
        limits=['Single rule postselected from341descriptions; no independent generalization or semantic false-positive labels.',
                'No authoritative RGB/material/visibility/occlusion labels. Zero captured supported loss cannot exclude a real clipped/occluded obstacle with no raw-road neighbors.',
                'Six unaffected episodes proved no-op from false birth predicates plus flag-propagation induction, not extra actor replay beyond2630.',
                'Different historical source policy on original roads; baseline337 is the exact full-output reproduction gate. Current-policy tracker matches existing current334ONrecords on source pixels.',
                '340survival233isprotocolcensor,noofficialfinish. No native or champion promotion follows a cache pass.'],
        next_minimum_actual_validation=proposal,preserved334_mixed_evidence=read(R/'stage341/summary-private.json')['preserved334_mixed_evidence'],actual_occlusion_preservation_verified=False,cost=cost,champion296_preserved=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,authorization_end_utc=p['deadline_utc'])
    save(D/'comparisons-private.json',all_comparisons);save(D/'cost.json',cost);save(D/'summary-private.json',public);save(G/'retry/support342_result.json',public)
    save(D/'final-saved-evidence-check.json',dict(passed=True,baseline337_exact=True,actor_calls=2630,stored_pixel_actor_resets=10,pixel_only=True,detector_tracker_lineage_invariant=True,supported_point_losses=0,all7flaggedbirths_reported=True,all_change_and_nochange_ranges_reported=True,untouched6static_noop=True,new_native_actions=0,new_environment_resets=0,technical_recovery_calls=0,next_actual_pair_not_executed=True))
    v.update(version=354,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v353.json'),prior_budget_sha256=sha(R/'project-effective-budget-v353.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,stage342_new_wrapper_actions=0);assert not (R/'project-effective-budget-v354.json').exists();save(R/'project-effective-budget-v354.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==342 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(dict(births=births,pairs=summary,supported_direct=supported_direct,supported_retained=supported_retained,cost=cost,next_native_cap=320)),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);close(a.parse_args().private_root)
