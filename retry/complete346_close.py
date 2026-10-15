"""Official finish feasibility only; no historical baseline ranking."""
import argparse
import datetime
import json
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.complete346_stage import verify
from retry.pair343_close import describe
from retry.confidence341_run import label


def rows(path):return [json.loads(s) for s in Path(path).read_text().splitlines()]


def close(R):
    D=R/'stage346';G=Path(__file__).resolve().parent.parent;p=verify(R);assert not (D/'cost.json').exists();start,cpu=time.perf_counter(),time.process_time();result=read(D/'B/result.json');data=rows(D/'B/trace-private.jsonl');reference=rows(R/'stage345/B/trace-private.jsonl');z=np.load(D/'B/frames-actions-private.npz');old=np.load(R/'stage345/B/frames-actions-private.npz');budget=read(D/'native-budget.json');prefix=read(D/'prefix160-qualification.json')
    used=result['native_actions'];assert budget['actions']==budget['arms']['B']==used==len(data)==len(z['actions'])<=300 and budget['resets']==1 and len(z['frames_uint8'])==used+1
    assert result['technical_error'] is None and result['comparison_valid'] and result['prefix_actions_verified']==160 and prefix['passed'];assert np.array_equal(z['actions'][:160],old['actions']) and np.array_equal(z['frames_uint8'][:161],old['frames_uint8'])
    for a,b in zip(data[:160],reference):
        for key in ['executed','features','audit','tracker','support_record','routing_evidence','pixel_path','actor_state','nominal_memory','policy','pre','post','pre_physical','post_physical','pre_RNG','post_RNG','raw_observations']:assert a[key]==b[key],key
    assert sum(r['raw_ticks'] for r in data)==result['raw_step_ticks']==result['raw_counter_at_stop']-result['raw_counter_after_reset'];assert all(not r['terminated'] and not r['truncated'] for r in data[:-1]);assert result['reaping']['process_reaped'] and result['reaping']['actor_pids_absent']
    labels={};births=[];held=[];supported_losses=[]
    for r in data:
        assert r['executed']==r['returned_action'] and r['nominal_memory']==r['policy']['previous_steer'] and np.float32(r['nominal_memory'])==np.float32(r['executed'][0]);e=r['routing_evidence'];assert e['tracker_preserved'] and e['full_hazards']==r['tracker']['after']
        for q in r['support_record']['births']:
            lab,identity=label(q['point'],r['pre_physical']);labels[tuple(q['uid'])]=dict(label=lab,id=identity)
            if q['low']:births.append(dict(birth_action=r['step'],direct_index=q['uid'][1],component_area=q['component_area'],diagnostic_label=lab))
        if e['removed_indices']:held.append(r['step'])
        for j in e['removed_indices']:
            q=r['support_record']['after'][j]
            if labels[tuple(q['uid'])]['label']=='fixture_supported':supported_losses.append(dict(action=r['step'],uid=q['uid']))
    finish=result['finish'];official=finish['finish_time_s'] is not None
    assert official==result['completed']
    if official:
        assert data[-1]['completed'] and not result['protocol_stop'] and not result['actual_DNF'] and not result['censored']
        assert result['lap_ms']==round((finish['finish_time_s']-result['postreset_start_time'])*1000)
        assert result['raw_counter_at_stop']<8200
    outcome=describe(data,result);outcome.update(terminated=result['terminated'],truncated=result['truncated'],censored=result['censored'],stop_reason=result['stop_reason'],finish_qualified_time_s=finish['finish_qualified_time_s'],finish_time_s=finish['finish_time_s'],declaration_raw_time_s=finish['raw_time'],postreset_start_time_s=result['postreset_start_time'])
    v=read(R/'project-effective-budget-v357.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1283442,796,84000,0)
    fields=['wall_s','runner_CPU_s','actor_CPU_s','reset_wall_s','raw_step_render_wall_s','raw_contact_observer_wall_s','capture_wall_s','journal_wall_s','artifact_wall_s']
    cost=dict(stage=346,new_wrapper_actions=used,native_cap=300,prefix_included_in_cap=True,new_A_runs=0,new_B_runs=1,new_environment_resets=1,additional_research=0,raw_step_ticks=result['raw_step_ticks'],raw_reset_ticks=result['raw_reset_ticks'],new_source_physics_rollout_ticks=0,new_learning_fits=0,parameter_sweeps=0,new_paid_resources=0,technical_error=None,technical_recovery_native=0,technical_recovery_resets=0,actual_cumulative_wrapper_actions=1283442+used,research_remaining=796-used,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1368238,unused_reserved_actions=300-used,measurements={k:result[k] for k in fields},closure_wall_s=time.perf_counter()-start,closure_CPU_s=time.process_time()-cpu,measurement_scope='Rawstep includes simulation+render. Read-only rawcontact/capture/journal/artifact separately timed; totals include other setup/hash/IPC, not wholecoding/report/git. No extra physicsstep.')
    proposal=dict(status='Proposed only; no new episode scheduled/reserved.',question='Relative official completion and lap time on this one fixedO2case after a matched fresh baseline, not generalization or safety.',
        design='One fresh original296baseline A, at most300native including exact replay ofactual345Aprefix160. Reuse fully recorded actual346B as candidate arm; do not rerun B or use a different policy/history as A. Directly verify shared reset and prefix145against346B, and full160baseline prefix against345A, with actor/tracker/physics/accessRNG. Then A own observations/fullcontrols/normalmemory toofficialterminal orcap.',
        total_native_cap=300,new_A_runs=1,new_B_runs=0,new_environment_resets_cap=1,maximum_postreset_raw_ticks=1200,expected_reset_raw_ticks=51,additional_budget_needed=0,research_remaining_after_maximum=cost['research_remaining']-300,final_reserved_actions=84000,final_reserve_used=0,
        value='346answers candidate feasibility only. A single new live-qualified baseline plus existing fully qualified candidate is the smallest new valid paired official-objective comparison; it avoids another candidate run or repeating160-onlypair.',
        gates='Exact original296archive and original baseline config from345A, sameO2case and observerRNGseed. Use fullfreshstate and rawtick prefix checks; no forced146action, no savedpost160controls, no threshold/model/split changes.',
        outcomes='Finishflag first, lap time from retroactive center crossing only if bothofficiallyfinish; actualDNF and protocolcensor separate. Joint contact/damage/tile/speed/termination report. No comparison now in346; future result remains onecase, no safety/generalization/promotion.',
        stop='Officialtermination,300cap,qualification/integrity/deadline stop. No automatic extension or extra budget. Missingfinish atcap remainscensor.')
    public=dict(stage=346,decision='Official completion feasibility observed on this single unchanged candidate/O2episode.' if official else 'Official completion not observed within this episode; classify actual retirement orprotocolcensor explicitly.',outcome=outcome,
        verification=dict(passed=True,prefix_actions_exact=160,prefix_input_frames_exact=161,full_actor_tracker_memory_physics_accessRNG_andrawticks_exact=True,all_returned_controls_executed=True,normal_own_memory=True,own_observations_after160=True,first_officialterminal_stop=True,finish_flag_first=True,no_steps_after_terminal=True,total300cap_includes_prefix=True,hidden_solver_OpenCV_RNG_not_directly_measured=True),flagged_births=births,routing_withheld_actions=held,supported_routing_losses=supported_losses,
        limits=['Standalone feasibility, no freshbaseline comparison made here. No historical baseline superiority, timing improvement, safety, generalization orchampionpromotion claim.',
                'Officialfinish is not alltilesvisited: sourcefinishtracker qualification then center crossing. Lap uses retroactivefinish_time minuspostresetstart, not actioncount or declarationclock.',
                'Damage andcontacts diagnostic only. Semantic material/actualocclusion unverified; zero captured supportedloss doesnotprove safe omission for all real obstacles.',
                '345localpairedcensor,343differentpolicy unexposed,344sourcecacheexposed results remain distinct.'],cost=cost,next_minimum_valid_comparison=proposal,preserved334_mixed_evidence=read(R/'stage345/summary-private.json')['preserved334_mixed_evidence'],actual_occlusion_preservation_verified=False,champion296_preserved=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,authorization_end_utc=p['deadline_utc'])
    verify(R);save(D/'cost.json',cost);save(D/'summary-private.json',public);save(G/'retry/complete346_result.json',public);save(D/'final-saved-evidence-check.json',dict(passed=True,actual_prefix160_exact=True,total_cap300respected=True,actual_actions=used,reset1=True,all_returned_controls_normal_memory=True,official_finish_flag=official,lap_ms=outcome['lap_ms'],no_postterminal_steps=True,supported_losses=len(supported_losses),technical_error=None,next_baseline_not_started=True))
    v.update(version=358,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v357.json'),prior_budget_sha256=sha(R/'project-effective-budget-v357.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage346_new_wrapper_actions=used);assert not (R/'project-effective-budget-v358.json').exists();save(R/'project-effective-budget-v358.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==346 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(dict(outcome=outcome,births=births,supported_losses=supported_losses,cost=cost,next_baseline_cap=300)),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);close(a.parse_args().private_root)
