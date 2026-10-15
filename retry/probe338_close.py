"""Compare true common interval; no extrapolation beyond B official crash."""
import argparse
import datetime
import json
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha


def rows(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]


def describe(data,limit):
    sample=data[:limit];last=sample[-1];pairs=[];touch=[]
    for r in sample:
        contact=r['post_physical']['touching_obstacle_contacts']
        if any(p[0]==2 and p[2]==0 for p in contact):touch.append(r['step'])
        for p in contact:
            if p not in pairs:pairs.append(p)
    return dict(observed_actions=len(sample),first_collision_event=next((r['step'] for r in sample if r['collision']),None),collision_event_actions=[r['step'] for r in sample if r['collision']],endpoint_fixture_pairs=pairs,hull_obstacle2_touching_endpoint_actions=touch,damage=last['damage'],unique_tiles=last['post']['unique_tiles'],progress_beyond132_tiles=last['post']['unique_tiles']-132,speed_m_s=last['post']['speed_m_s'],off_track_counter=last['post']['off_track_counter'],actual_terminated=last['terminated'],actual_truncated=last['truncated'],completed=last['completed'],retire_reason=last['retire_reason'])


def close(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage338';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert not (D/'cost.json').exists()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    r=read(D/'B/result.json');a=rows(R/'stage337/B/trace-private.jsonl');b=rows(D/'B/trace-private.jsonl');z=np.load(D/'B/frames-actions-private.npz');ref=np.load(R/'stage337/B/frames-actions-private.npz');budget=read(D/'native-budget.json');used=budget['actions'];assert used==r['native_actions']==len(b)==len(z['actions'])<=233 and len(z['frames_uint8'])==used+1
    assert r['comparison_valid'] and not r['technical_error'] and r['prefix127_verified']==127;assert np.array_equal(z['actions'][:127],ref['actions'][:127]) and np.array_equal(z['frames_uint8'][:128],ref['frames_uint8'][:128]);assert read(D/'preprobe127-qualification.json')['passed']
    assert all(not row['terminated'] and not row['truncated'] for row in b[:-1]);assert sum(x['raw_ticks'] for x in b)==r['raw_step_ticks'];assert r['raw_counter_at_stop']-r['raw_counter_after_reset']==r['raw_step_ticks']
    for i,row in enumerate(b):
        original=np.array(row['returned_action'],np.float32);executed=np.array(row['executed'],np.float32);assert np.array_equal(executed[1:],original[1:]);assert row['nominal_memory']==row['policy']['previous_steer'] and np.float32(row['nominal_memory'])==original[0]
        if i!=127:assert np.array_equal(executed,original)
        else:
            assert executed[0]!=original[0] and row['nominal_memory']==a[i]['nominal_memory'];assert row['probe']['state_preserved'] and row['probe']['tracker_unchanged'] and row['tracker']==a[i]['tracker']
            assert row['probe']['variants']['original']['steering']==row['returned_action'][0] and np.float32(row['probe']['variants']['direct']['steering'])==executed[0]
    cache=read(D/'cache-receipt.json');assert cache['first_fixed_window_actual_dtype_difference']==128 and cache['float32_difference_real'];probes=read(D/'cache/probes-private.json');assert [x['step'] for x in probes if x['dtype_diff']]==[128]
    assert r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent']
    common=min(len(a),len(b));comparison=dict(common_actions=common,A=describe(a,common),B=describe(b,common),A_full_episode=dict(native_actions=233,actual_DNF=True,retire_reason='off_track',damage=.2,unique_tiles=132),B_actual_DNF=r['actual_DNF'],B_censored=r['censored'],B_protocol_stop=r['protocol_stop'],B_finish_time_s=r['finish']['finish_time_s'],B_lap_ms=r['lap_ms'])
    intervention=b[127];delta=float(np.float32(intervention['executed'][0])-np.float32(intervention['returned_action'][0]));verification=dict(passed=True,actual_prefix_actions_exact=127,actual_prefix_pixel_frames_exact=128,actor_tracker_nominal_memory_captured_physics_accessible_RNG_gate=True,frozen_package_original_routing_controller_reproduced=True,actual_dtype='float32',first_window_dtype_difference=128,executed_steering_delta_at128=delta,only_execution_override_action=128,only_execution_override_component='steering',same128pedals=True,same128original_nominal_memory_update=True,tracker_not_deleted=True,after128_candidate_returned_outputs_on_own_inputs=True,no_stored_continuation=True,no_postterminal_steps=True,hidden_solver_OpenCV_RNG_not_directly_measured=True,new_native_actions=0)
    save(D/'saved-evidence-verification.json',verification)
    prior=R/'project-effective-budget-v349.json';v=read(prior);assert v['actual_cumulative_wrapper_actions']==1282433 and v['research_remaining']==1805 and v['B_operating_cap']==1368238 and v['final_reserved_actions']==84000 and v['final_reserve_used']==0
    cost=dict(stage=338,new_wrapper_actions=used,native_cap=233,new_B_runs=1,new_A_runs=0,additional_research=0,raw_step_ticks=r['raw_step_ticks'],raw_reset_ticks=r['raw_reset_ticks'],native_wall_s=r['wall_s'],runner_CPU_s=r['runner_CPU_s'],actor_CPU_s=r['actor_CPU_s'],capture_wall_s=r['capture_wall_s'],cached_actor_calls=cache['cached_actor_calls'],cache_wall_s=cache['wall_s'],cache_runner_CPU_s=cache['runner_CPU_s'],cache_actor_CPU_s=cache['actor_CPU_s'],cached_frozen_routing_controller_calls=cache['frozen_package_routing_controller_calls'],native_probe_routing_controller_calls=2,new_learning_fits=0,new_source_physics_ticks=0,new_paid_resources=0,actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions']+used,research_remaining=v['research_remaining']-used,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=v['B_operating_cap'],measurement_scope='Native/capture/actor/cachedcalls measured; initialhash/data load,build,final saved-evidence/report not wholly timed. Captureoverhead notpure simulatorstep cost.')
    save(D/'cost.json',cost);v.update(version=350,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage338_new_wrapper_actions=used)
    assert not (R/'project-effective-budget-v350.json').exists();save(R/'project-effective-budget-v350.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==338 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    public=dict(stage=338,question=p['hypothesis'],verification=verification,comparison=comparison,interpretation='Singlefirstdtype-realsteering128 intervention doesnotresolvefirstcontact132/officialretirement: Bcrashes136, whileAisnonterminalwithdamage.2atcommon136andlaterstalls/off_track233. Bmakes2moretiles,buthas5collisioneventactionsandearlierofficialcrash. Rejects sufficiencyofthisparticularintervention only; notallretainedpoints harmless,notproofspeed/lookahead cause. Damagealone isnotveto; physicaleventpattern,progress andofficialtermination arejointlyreported.',
        limits=['KnownpostselectedN2,onecommand/oneB. No completion/generalization/promotion.',
            'OriginalA233fullrecordqualified; commoncomparisonstops136atBterminal. No Bobservations/actions synthesizedto233.',
            'Bchangedphysicalstateafter128,so129+originalpolicyreturneddifferentcontrols. Oneexecutionoverride isnotafull direct-onlytrackingpolicy.',
            'Near-path/far-target .549rad difference canbenormaloncurvedpath andwasnotusedasdefectcriterion.',
            'GT evaluatoronly; actualocclusion remainsunverified, hidden solver/OpenCVRNG notdirectlymeasured.'],cost=cost,preserved334_mixed_evidence=read(R/'stage337/summary-private.json')['preserved334_mixed_evidence'],actual_occlusion_preservation_verified=False,
        next_action_proposal=dict(status='Notexecuted; do notautomaticallymoveprobe129orpicklargermagnitude.',focus='Native0 audit of unresolved detection birth/retention and route history on fixed recordedapproach, separating geometriccorrespondence from visibility and temporaltransport. No newthreshold,lookahead,pedalchange orcausalclaimfromnear/farangle. Any longer/multi-command memoryintervention needs separate pairedcontract; thissinglecommandresult cannot settle it.'),champion296_preserved=True,TRAIN_registry_preserved=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,authorization_end_utc=p['deadline_utc'])
    save(D/'summary-private.json',public);save(G/'retry/probe338_result.json',public);print(json.dumps(dict(comparison=comparison,verification=verification,cost=cost),ensure_ascii=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',required=True,type=Path);close(p.parse_args().private_root)
