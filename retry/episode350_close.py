"""Close the one actual episode, retain historical comparators and grant ledger."""
import datetime
import json
from pathlib import Path
import sys
import numpy as np
from retry.path271_run import read,save,sha
from retry.episode350_stage import verify,G
from retry.package349_run import rows,projection
from retry.probe338_stage import stack
from retry.pair343_close import describe
from retry.confidence341_run import label


def close(R):
    D=R/'stage350';p=verify(R,True);assert not (D/'cost.json').exists();r=read(D/'B/result.json');data=rows(D/'B/trace-private.jsonl');b=read(D/'native-budget.json');z=np.load(D/'B/frames-actions-private.npz');old=rows(R/'stage340/B/trace-private.jsonl');a=rows(R/'stage337/B/trace-private.jsonl');az=np.load(R/'stage337/B/frames-actions-private.npz');aresult=read(R/'stage337/B/result.json')
    used=b['actions'];assert used==r['native_actions']<=p['episode_cap']==2000 and used<=p['total_native_cap']==2038;assert b['resets']==1 and b['actor_resets']==1 and b['actor_act_calls']<=2000
    assert not r['technical_error'] and r['comparison_valid'] and read(D/'prefix233-qualification.json')['passed']
    assert len(data)==len(z['actions'])==used and len(z['frames_uint8'])==used+1 and b['actor_act_calls']==used
    assert r['prefix_actions_verified']==233 and used>=233;assert all(not x['terminated'] and not x['truncated'] for x in data[:-1]);assert sum(x['raw_ticks'] for x in data)==r['raw_step_ticks']==r['raw_counter_at_stop']-50
    assert r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent'];assert read(R/'stage337/plan.json')['case']==p['case'] and read(R/'stage340/plan.json')['observer_rng_seed']==p['observer_rng_seed']
    for i,x in enumerate(data):
        assert x['executed']==x['returned_action'] and x['nominal_memory']==x['policy']['previous_steer'] and np.float32(x['nominal_memory'])==np.float32(x['executed'][0])
        assert len(x['raw_observations'])==x['raw_ticks']
        if i<233:
            assert x['executed']==old[i]['executed'] and x['pre_physical']==old[i]['pre_physical'] and x['post_physical']==old[i]['post_physical'] and projection(x['policy'])==projection(old[i]['policy'])
        if i<126:
            for key in ['executed','features','pixel_path','nominal_memory','tracker','pre','post','pre_physical','post_physical']:assert x[key]==a[i][key],(i,key)
            assert projection(x['policy'])==projection(a[i]['policy'])
    assert np.array_equal(z['actions'][:126],az['actions'][:126]) and np.array_equal(z['frames_uint8'][:127],az['frames_uint8'][:127])
    assert data[126]['executed']!=a[126]['executed'] and data[126]['executed'][0]==a[126]['executed'][0]
    assert not np.array_equal(z['frames_uint8'][127],az['frames_uint8'][127])
    assert r['completed'] and r['stop_reason']=='official_finish' and not r['censored'] and not r['protocol_stop'] and not r['actual_DNF']
    assert r['lap_ms']==round((r['finish']['finish_time_s']-r['postreset_start_time'])*1000)
    outcome=describe(data,r);births=[];held=[];supported_losses=[];birth_labels={}
    for x in data:
        for item in x['support_record']['births']:
            lab,_=label(item['point'],x['pre_physical']);birth_labels[tuple(item['uid'])]=lab
            if item['low']:births.append(dict(birth_action=item['uid'][0],direct_index=item['uid'][1],area_pixels=item['component_area'],posthoc_geometric_label=lab))
        for item in x['routing_evidence']['removed_evidence']:
            held.append(dict(action=x['step'],uid=item['uid']))
            if birth_labels[tuple(item['uid'])]=='fixture_supported':supported_losses.append(dict(action=x['step'],uid=item['uid']))
    v=read(R/'project-effective-budget-v362.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'],v['B_operating_cap'])==(1284005,2038,84000,0,1370043)
    assert read(D/'budget-extension.json')['additional_research_actions']==1805
    measures=['wall_s','runner_CPU_s','actor_CPU_s','reset_wall_s','raw_step_render_wall_s','raw_contact_observer_wall_s','capture_wall_s','journal_wall_s','artifact_wall_s']
    cost=dict(stage=350,new_wrapper_actions=used,new_candidate_runs=1,new_baseline_runs=0,new_environment_resets=1,cached_actor_calls=0,actual_actor_calls=b['actor_act_calls'],actual_actor_resets=1,new_native_auxiliary=0,total_native_accounting_cap=2038,episode_cap=2000,additional_research_registered_before_native=1805,raw_step_ticks=r['raw_step_ticks'],raw_reset_ticks=r['raw_reset_ticks'],new_source_physics_rollout_ticks=0,new_learning_fits=0,new_tuning=0,new_paid_resources=0,technical_error=r['technical_error'],technical_recovery_native=0,technical_recovery_resets=0,measurements={k:r[k] for k in measures},actual_cumulative_wrapper_actions=1284005+used,research_remaining=2038-used,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1370043,unused_registered_native=2038-used,old340_native_charged_again=False,old337_native_charged_again=False,measurement_scope='Only350actual episode charged;233prefix included within292total, not extra replay. Raw-step includes render; read-only contact/capture/journal/artifact separately timed. Startup/hash/coding/closure/git not wholly represented by named subtimers.')
    assert sha(R/'stage296/submission296.zip')=='0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937' and sha(R/'stage296/champion-manifest.json')=='b92fe5307a491bfb9d1f5081bf97c9c1d4646dcf9c8511fb169bc48c8f9349e5'
    for path in ['DEV','screen-opening.json','DEV-opened-by309.json']:assert not (R/'stage297'/path).exists()
    next_compare=dict(status='Proposal only; not executed or reserved.',context='Only frozen334ON/H1 baseline versus unchanged349candidate. No296pooling.',
        minimum='Native0fixed-pixel regression comparison on existing O0first190inputs, to cover its known181birth, retained181-189andexpiry190. Two unchanged private artifacts, normal ownmemory, same stored observations; reproduce saved334/342baseline/candidate evidence first.380actor calls and2pixel resets maximum, native/environment reset/fit/tuning0. No newcase orprotected split.',
        gate='Freeze input/artifact/source hashes and stop on input/reset/output/tracker/state projection mismatch. Known cached rule has no routing/control change onO0; confirm or falsify packaged equivalence, do not optimize a cutoff. If no control exposure, record no-effect and do not spend native repeating it.',
        purpose='Independent saved-road regression check of the packaged fixed rule after one knownN2completion, not an actual generalization result. Pixels originally collected under another policy, so off-policy replay limits remain explicit.',
        later_actual='Only a separately registered actual paired comparison on already permitted TRAIN inputs with justified exposure and budget may follow. Current1746research cannot reserve even one2000actionfullcap without254more; paired2000+2000would need2254more. No grant, run, holdout, sealed opening orpromotion is made here.',research_remaining=2038-used,final_reserve=84000)
    result=dict(stage=350,decision='One knownTRAIN N2 actual feasibility confirmed; no champion promotion or generalization claim.',candidate_archive_sha256=p['config']['archive_sha256'],candidate_worker_sha256=p['config']['worker_sha256'],candidate_modified=False,official_outcome=outcome,finish=dict(qualification_raw_time_s=r['finish']['finish_qualified_time_s'],center_crossing_raw_time_s=r['finish']['finish_time_s'],declaration_raw_time_s=r['finish']['raw_time'],postreset_start_time_s=r['postreset_start_time'],official_lap_ms=r['lap_ms'],truncated_due_to_official_finish=True,time_limit_or_protocol_censor=False),
        verified_prefix=dict(actual_actions=233,input_stacks=234,comparison='Historical340prefix exactly reproduced;340notrerunorrelabelled.350then59newcontinuationactions.',commands_pixels_tracker_features_path_audit_nominalmemory_originalstatephysics_exact=True,full_packaged349replay_state_exact=True,actor_accessible_RNG_exact=True,evaluator_RNG_scope=p['RNG']),
        historical_baseline337=dict(reused_not_new=True,actual_actions=aresult['native_actions'],completed=aresult['completed'],actual_DNF=aresult['actual_DNF'],retire_reason=aresult['retire_reason'],unique_tiles=aresult['unique_tiles'],total_tiles=aresult['total_tiles'],damage=aresult['damage'],first_contact=aresult['first_contact'],same_initialization_and_common126controls=True,common_input_stacks=127,first_full_control_difference=127,first_different_input_action=128,comparison='Completion versus historicalDNF only; no paired lap delta because baseline didnotfinish. Bothactualsource contexts334ON/H1,onlyfixedroutingrule differs; candidate metadata bookkeeping adds expected fullpickle differences.'),
        posthoc_rule_audit=dict(low_births=births,withheld_action_count=len(held),withheld_actions=sorted({x['action'] for x in held}),fixture_supported_withheld_count=len(supported_losses),semantic_material_and_actual_occlusion_verified=False,GT_policy_input=False),
        limits=['One previously observed TRAINcondition, no population/generalization/safety orchampion promotion. Existing334mixed aggregate evidence remains unchanged.',
        '340is an earlier233protocol-censored diagnostic, not evidence itfinished.350is a new292actionepisodeincludingprefix; only59actions are beyondprevious340horizon.',
        'Historical340evaluatorRNGsnapshots after127absent; liveconstant/referenceandnodrawsource plus exactphysics used. Hidden solver/OpenCV RNG and omitted warmstart/contactisland state are not directly captured.',
        'Three zero-ringbirths remain geometrically unresolved; no semantic false-positive or occlusion preservation claim. No new fit, threshold, control tuning or extraarm.'],cost=cost,next_frozen_comparison=next_compare,champion296_preserved=True,new_DEV_opening=False,new_HOLDOUT_opening=False,new_SEALED_opening=False,promotion=False,authorization_end_utc=p['deadline_utc'])
    save(D/'cost.json',cost);save(D/'summary-private.json',result);save(G/'retry/episode350_result.json',result)
    save(D/'final-report-verification.json',dict(passed=True,prefix233_exact=True,single_actual_candidate_only=True,official_finish=True,native_actions=used,old340_not_new_or_recounted=True,grant1805_pre_registered=True,totalcap2038_episode_cap2000_respected=True,candidate_archive_andworker_unchanged=True,research_remaining=2038-used,final_reserve=84000,next_comparison_not_executed=True))
    v.update(version=363,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v362.json'),prior_budget_sha256=sha(R/'project-effective-budget-v362.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage350_new_wrapper_actions=used);assert not (R/'project-effective-budget-v363.json').exists();save(R/'project-effective-budget-v363.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==350 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(dict(official_outcome=outcome,cost=cost,posthoc_low_births=births)),flush=True)


if __name__=='__main__':close(Path(sys.argv[1]).resolve())
