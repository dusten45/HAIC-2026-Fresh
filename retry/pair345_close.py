"""Close an exposed fresh source-policy pair without treating censoring as finish."""
import argparse
import datetime
import json
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.pair345_stage import verify
from retry.pair343_close import describe
from retry.confidence341_run import label


def rows(path):return [json.loads(s) for s in Path(path).read_text().splitlines()]


def close(R):
    D=R/'stage345';G=Path(__file__).resolve().parent.parent;p=verify(R);assert not (D/'cost.json').exists();start,cpu=time.perf_counter(),time.process_time();result={arm:read(D/arm/'result.json') for arm in ['A','B']};data={arm:rows(D/arm/'trace-private.jsonl') for arm in result};z={arm:np.load(D/arm/'frames-actions-private.npz') for arm in result};budget=read(D/'native-budget.json');prefix=read(D/'natural-prefix-qualification.json')
    assert budget['actions']==320 and budget['resets']==2 and budget['arms']==dict(A=160,B=160)
    assert prefix['passed'] and prefix['prefix_actions']==145 and prefix['input_stacks']==146 and prefix['first_natural_full_control_difference']==146
    assert np.array_equal(z['A']['actions'][:145],z['B']['actions'][:145]) and np.array_equal(z['A']['frames_uint8'][:146],z['B']['frames_uint8'][:146])
    for arm in result:
        q=result[arm];assert q['technical_error'] is None and q['reaping']['process_reaped'] and q['reaping']['actor_pids_absent'];assert q['native_actions']==len(data[arm])==len(z[arm]['actions'])==160 and len(z[arm]['frames_uint8'])==161
        assert q['raw_step_ticks']==sum(r['raw_ticks'] for r in data[arm])==q['raw_counter_at_stop']-q['raw_counter_after_reset']==640 and q['raw_reset_ticks']==51
        assert q['protocol_stop'] and not q['actual_DNF'] and not q['completed'];assert all(not r['terminated'] and not r['truncated'] for r in data[arm])
        for r in data[arm]:assert r['executed']==r['returned_action'] and r['nominal_memory']==r['policy']['previous_steer'] and np.float32(r['nominal_memory'])==np.float32(r['executed'][0])
    for a,b in zip(data['A'][:145],data['B'][:145]):
        for k in ['features','audit','tracker','support_record','pixel_path','actor_state','nominal_memory','policy','pre','post','pre_physical','post_physical','pre_RNG','post_RNG','raw_observations']:assert a[k]==b[k],k
    first_pixels=next((i+1 for i,(a,b) in enumerate(zip(z['A']['frames_uint8'],z['B']['frames_uint8'])) if not np.array_equal(a,b)),None);assert first_pixels==147
    comparison={arm:describe(data[arm],result[arm]) for arm in result};support_losses=[];births={};held={};direct_support={};retained_support={}
    for arm in ['A','B']:
        labels={};births[arm]=[];held[arm]=[];direct_support[arm]=retained_support[arm]=0
        for r in data[arm]:
            for q in r['support_record']['births']:
                lab,identity=label(q['point'],r['pre_physical']);labels[tuple(q['uid'])]=dict(label=lab,id=identity)
                if lab=='fixture_supported':direct_support[arm]+=1
                if q['low']:births[arm].append(dict(birth_action=r['step'],direct_index=q['uid'][1],component_area=q['component_area'],raw_road_neighbors=q['raw_road_neighbors'],diagnostic_label=lab))
            e=r['routing_evidence'];assert e['tracker_preserved'] and e['full_hazards']==r['tracker']['after'] and r['features'][11]==len(e['full_hazards'])
            if e['removed_indices']:held[arm].append(r['step'])
            for j,(point,q) in enumerate(zip(r['tracker']['after'],r['support_record']['after'])):
                lab=labels[tuple(q['uid'])]['label']
                if point[3]>0 and lab=='fixture_supported':retained_support[arm]+=1
                if j in e['removed_indices'] and lab=='fixture_supported':support_losses.append(dict(arm=arm,action=r['step'],uid=q['uid'],age=point[3]))
    assert not support_losses and held['A']==[] and held['B']==[146,147,148]
    assert births['A']==births['B']==[dict(birth_action=146,direct_index=0,component_area=4,raw_road_neighbors=0,diagnostic_label='unresolved')]
    exposure=dict(first_natural_full_control_difference=146,prefix_actions_exact=145,prefix_input_frames_exact=146,first_different_input_action=first_pixels,rule_birth146_not_forced=True,held_actions=held,postbranch_controls_on_own_observations=True,normal_own_memory=True,full_fresh_actor_pickle_controller_tracker_physics_accessRNG_gate=True)
    postbranch={arm:dict(collision_actions=[r['step'] for r in data[arm][145:] if r['collision']],touching_raw_endpoints=sum(bool(t['pairs']) for r in data[arm][145:] for t in r['raw_observations']),tiles_at_prefix=data[arm][144]['post']['unique_tiles'],tiles_at_stop=data[arm][-1]['post']['unique_tiles'],progress_tiles=data[arm][-1]['post']['unique_tiles']-data[arm][144]['post']['unique_tiles'],damage_at_prefix=data[arm][144]['damage'],damage_at_stop=data[arm][-1]['damage']) for arm in result}
    assert all(not q['collision_actions'] and q['touching_raw_endpoints']==0 for q in postbranch.values())
    shared_contact=comparison['A']['fixture_touching'];assert shared_contact==comparison['B']['fixture_touching'];assert comparison['A']['collision_event_actions']==comparison['B']['collision_event_actions']==[46]
    difference_summary=dict(final_position_separation_m=float(np.linalg.norm(np.array(data['A'][-1]['post']['position'])-data['B'][-1]['post']['position'])),maximum_postbranch_position_separation_m=max(float(np.linalg.norm(np.array(a['post']['position'])-b['post']['position'])) for a,b in zip(data['A'][145:],data['B'][145:])),comparison_scope='After146 the scenes and normal memory may differ. Joint outcomes are paired closed-loop effects, not independent per-frame steering/pedal effects.')
    v=read(R/'project-effective-budget-v356.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1283122,1116,84000,0)
    measures=['wall_s','runner_CPU_s','actor_CPU_s','reset_wall_s','raw_step_render_wall_s','raw_contact_observer_wall_s','capture_wall_s','journal_wall_s','artifact_wall_s']
    cost=dict(stage=345,new_wrapper_actions=320,new_A_runs=1,new_B_runs=1,new_environment_resets=2,per_arm_cap=160,total_cap=320,additional_research=0,raw_step_ticks=1280,raw_reset_ticks=102,new_source_physics_rollout_ticks=0,new_learning_fits=0,parameter_sweeps=0,new_paid_resources=0,technical_error=None,technical_recovery_native=0,technical_recovery_resets=0,per_arm={arm:{k:result[arm][k] for k in measures} for arm in result},totals={k:sum(result[arm][k] for arm in result) for k in measures},closure_wall_s=time.perf_counter()-start,closure_CPU_s=time.process_time()-cpu,actual_cumulative_wrapper_actions=1283442,research_remaining=796,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1368238,measurement_scope='Rawstep wall includes simulator+render; read-onlycontact/capture/journal/artifactsubtimers separate. Setup/hash/IPC included in total or outside namedsubtimers; report/gitnot whollytimed. No pure solver cost or extra world advancement.')
    proposal=dict(status='Proposal only; no new episode scheduled/reserved.',question='Can the unchanged exposed candidate reach an official O2finish beyond the160censor? Absolute completion feasibility only, not relative superiority.',
        why='345already supplies a fresh exposed local pair with no observed harmful counterexample. The cheapest remaining distinction is candidate officialfinish versus laterretirement/censor, without paying for a second baseline to answer a binary feasibility question.',
        design='One fresh candidate-only episode, sameO2and exact345Bconfig/initialconditions. Replay and verify the actual345Bprefix160commands/161pixels/fullactor/tracker/physics/accessRNG, then continue its own observations/fullreturnedcontrols/normalmemory. Prefix replay is charged inside300. Closed345world cannot be resumed from incomplete solver snapshots. No A substitute or comparative win is claimed.',
        per_arm_native_cap=300,total_native_cap=300,new_A_runs=0,new_B_runs=1,new_environment_resets_cap=1,maximum_postreset_raw_ticks=1200,expected_reset_raw_ticks=51,additional_budget_needed=0,research_remaining_after_maximum=496,final_reserved_actions=84000,final_reserve_used=0,
        cap_basis='Historical qualified sourcebaseline finished at280;300provides20actions of prespecified margin. It is an evaluation horizon only, not a control threshold. Stop at official finish/retirement or300; no implicit extension.',
        gates='Exact original296archive/source tracker/single342rule and exact345BobserverRNGseed for the replay gate. Fullpixel/state/physics/accessRNG checks, no forcedpost160controls. No model/threshold/split changes.',
        outcomes='Officialfinish flag first, retroactive center-crossing lap time iffinished; actualretirement vsprotocolcensor separate. Jointly report contacts/touching/progress/speed/damage and supportedloss. No freshAin this feasibility check, so no paired timing/non-regression or officialrank improvement claim.',
        value='Costs at most300of796research native with one reset, leaves496and preservesfinalreserve. Resolves absolute completion feasibility rather than repeating a160localpair. A finish still doesnot establish comparative improvement, generalization, occlusion safety or championpromotion.')
    public=dict(stage=345,decision='Natural source-policy exposure qualified; no local harmful counterexample observed in the160window. Both arms remain protocolcensored withoutfinish, so completion/non-regression and general safety are unresolved.',exposure=exposure,comparison=comparison,postbranch=postbranch,flagged_births=births,supported_direct_detections_checked=direct_support,supported_birth_retained_contexts_checked=retained_support,supported_routing_losses=support_losses,trajectory_difference=difference_summary,
        shared_prebranch_contact='Both hit obstacle0 via carbody4(wheelindex3),fixture0 before the rule146branch. Firsthitrawinterval is recorded separately; touching sampled at4.70/4.72s. Damage.2is shared prebranch history, not candidate-induced extra damage.',
        limits=['Fresh actual A/B, not344cachedcontrols or historicalA substitute. All executed commands equal each own returned fullcontrol; no forced146intervention or memoryoverride.',
                'Touching duration is sampled raw0.02sendpoints, not exact hidden solver contact duration. Hidden solver/OpenCVRNG states not directly inspected.',
                'Selected point remains unresolved semantic material. Zero captured supportedloss cannot establish real occlusion safety.',
                'One knownTRAIN source-policy road, not current334ON/H1or broad completionrate.343differentpolicy unexposed and344cachedexposed conclusions both preserved.',
                '160censors prevent official completion/lap comparison; no automatic extension/native/adoption.'],cost=cost,next_minimum_experiment=proposal,preserved334_mixed_evidence=read(R/'stage344/summary-private.json')['preserved334_mixed_evidence'],actual_occlusion_preservation_verified=False,champion296_preserved=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,authorization_end_utc=p['deadline_utc'])
    verify(R);save(D/'cost.json',cost);save(D/'summary-private.json',public);save(G/'retry/pair345_result.json',public);save(D/'final-saved-evidence-check.json',dict(passed=True,fresh_A_and_B=True,exact_natural_prefix145_commands146inputs=True,full_fresh_actorstate_tracker_physics_accessRNG_gate=True,first_control146_firstinput147=True,normal_own_returned_controls_memory=True,no_new_postbranch_contact=True,supported_losses=0,both160protocolcensors=True,no_official_finish_claim=True,technical_error=None,next_pair_not_started=True))
    v.update(version=357,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v356.json'),prior_budget_sha256=sha(R/'project-effective-budget-v356.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,actual_cumulative_wrapper_actions=1283442,research_remaining=796,stage345_new_wrapper_actions=320);assert not (R/'project-effective-budget-v357.json').exists();save(R/'project-effective-budget-v357.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==345 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(dict(exposure=exposure,comparison=comparison,postbranch=postbranch,difference=difference_summary,cost=cost,next_native_cap=300)),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);close(a.parse_args().private_root)
