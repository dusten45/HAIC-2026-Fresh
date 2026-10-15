"""Close the single technical-censored episode without an unauthorized reset."""
import argparse
import datetime
import json
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha


def close(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage336';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert not (D/'cost.json').exists();repair=read(D/'serializer-repair-verification.json')
    relocation={}
    for f,h in p['source_hashes'].items():
        if sha(f)==h:continue
        assert Path(f)==G/'retry/episode336_run.py';old=D/'executed-source/episode336_run.py';assert sha(old)==h==repair['original_executed_source_sha256'];assert sha(f)==repair['fixed_public_source_sha256'];relocation[f]=dict(executed_source=str(old),sha256=h)
    result=read(D/'B/result.json');budget=read(D/'native-budget.json');used=budget['actions'];assert used==result['native_actions']==1 and result['censored'] and not result['completed'] and not result['actual_DNF'] and not result['terminated'] and not result['truncated']
    assert result['prefix72_verified']==1 and result['comparison_valid'] is False
    actual=read(D/'actual-reset-contract.json');assert actual['postreset_action_cap']==2038 and actual['elapsed_after_reset']==50 and actual['raw_limit']==8200 and actual['remaining_raw']==8150 and actual['last_action_raw_ticks']==2
    z=np.load(D/'B/frames-actions-private.npz');old=np.load(R/'stage335/B/raw-pixels-actions-private.npz');assert len(z['frames_uint8'])==2 and len(z['actions'])==1 and len(z['prefix_observations'])==2;assert np.array_equal(z['actions'],old['actions'][:1]) and np.array_equal(z['prefix_observations'],old['observations'][:2]);assert (D/'B/trace-private.jsonl').stat().st_size==0
    assert result['raw_step_ticks']==4 and result['raw_reset_ticks']==51 and result['raw_counter_after_reset']==50 and result['raw_counter_at_stop']==54
    assert result['reaping']['process_reaped'] and result['reaping']['actor_pids_absent']
    save(D/'saved-evidence-verification.json',dict(passed=True,actual_action_count=1,prefix_reproduction_verified_before_logging_exception=1,full335prefix72_reproduced=False,stored_initial_and_postaction_stacks_exact=True,returned_command_matches335first=True,raw_counter50_to54=True,finish_flag_absent=True,no_actual_retirement=True,technical_censoring=True,empty_trace_not_fabricated=True,original_executed_source_retained=relocation,repair_native0=True,new_native_actions=0))
    prior=R/'project-effective-budget-v345.json';v=read(prior);assert v['actual_cumulative_wrapper_actions']==1282199 and v['research_remaining']==2038 and v['B_operating_cap']==1368237 and v['final_reserved_actions']==84000 and v['final_reserve_used']==0
    cache=read(D/'cache-receipt.json');synthetic=read(D/'synthetic-contract-verification.json')
    cost=dict(stage=336,new_wrapper_actions=used,registered_native_cap=2038,new_B_resets=1,new_A_runs=0,additional_research=2038,raw_step_ticks=result['raw_step_ticks'],raw_reset_ticks=result['raw_reset_ticks'],native_wall_s=result['wall_s'],runner_CPU_s=result['runner_CPU_s'],actor_CPU_s=result['actor_CPU_s'],capture_wall_s=result['capture_wall_s'],cached_actor_calls=72,cache_wall_s=cache['wall_s'],cache_runner_CPU_s=cache['runner_CPU_s'],cache_actor_CPU_s=cache['actor_CPU_s'],synthetic_nonHAIC_counter_wrapper_calls=2038,synthetic_counter_CPU_s=synthetic['CPU_s'],synthetic_counter_wall_s=synthetic['wall_s'],serializer_test_CPU_s=repair['CPU_s'],serializer_test_wall_s=repair['wall_s'],new_learning_fits=0,new_source_physics_ticks=0,new_paid_resources=0,actual_cumulative_wrapper_actions=1282200,research_remaining=2037,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1368237,
        measurement_scope='Real B one action then diagnostic JSON exception; reset51rawticks andaction4rawticks measured separately. Synthetic wrapper test uses noHAICphysics and no nativebudget. Initial source/hash/data loads before timers, build/report/patch time not fully instrumented.')
    save(D/'cost.json',cost);v.update(version=346,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),actual_cumulative_wrapper_actions=1282200,research_remaining=2037,stage336_new_wrapper_actions=1)
    assert not (R/'project-effective-budget-v346.json').exists();save(R/'project-effective-budget-v346.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==336 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    previous=read(R/'stage335/summary-private.json');context=previous['preserved334_mixed_evidence']
    public=dict(stage=336,status='technical_censored_completion_question_unanswered',actual_outcome=dict(native_actions=1,full_prefix72_verified=False,prefix_actions_verified=1,terminated=False,truncated=False,finish_qualified_time_s=None,finish_time_s=None,lap_ms=None,unique_tiles_after_action_not_persisted=True,damage_after_action_not_persisted=True,actual_DNF=False,censored=True,
        note='First live action/pixels/actor state/memory/physics/RNG comparison passed before JSON failure, but rich row was never written. Do not invent missing GT or call missing fields candidate failure.'),
        limit_contract={k:actual[k] for k in ['elapsed_after_reset','raw_limit','frame_skip','warmup','raw_reset_ticks','remaining_raw','postreset_action_cap','last_action_raw_ticks']},
        termination_contract='CarRacing success uses truncated=True with finish flag. Officiallap uses retroactive center finish_time_s minuspostreset startclock. DefaultCLI2000 differs from verifiedcurrentmake_env2038; no363cut. No completion or failure conclusion from this technicalcensoring.',
        technical_failure='TypeError: DamageEffects dataclass in evaluator info was not JSON serializable. Environment was closed after action1; not a tracker/control failure.',
        repair={k:repair[k] for k in ['passed','original_failure_reproduced_without_env','damage_dataclass_levels_tested','numpy_nested_supported','run_AST_same_except_json_default_keyword','policy_control_physics_timing_unchanged','new_native_actions','new_actor_calls','fixed_source_not_executed_native']},
        no_retry=True,reason_no_retry='Current explicit one-new-B episode, no reseed/no free resume contract. Actual world closed; recreating it would be another reset, not continuation.',
        next_required_step=dict(status='Blocked pending separate replacement-episode instruction; not executed or newly funded',same_candidate_archive_unchanged=True,diagnostic_serializer_fixed=True,
            proposed_new_job='Separate replacement stage, preserve336failedartifacts and guard; do not erase opening marker or masquerade as resumption.',new_B_cap=2038,current_unused_research=2037,minimal_additional_research_if_replacement_authorized=1,would_operating_B=1368238,final_reserve_used=0,
            gates='Run native0serializer regression before reset, qualify samearchive andfresh33572cache; one reset, actualcountervalidatedcap, full72liveprefix thenownpolicy toofficialfinish/terminal/verifiedcap. No363cut, no sweep.',scope='A replacement requires exception to this one-episode restriction. Current336 does not authorize a second B. Paired multi-road validation only if later actualepisode completion established.'),
        preserved334_mixed_evidence=context,actual_occlusion_preservation_verified=False,cost=cost,champion296_preserved=True,TRAIN_registry_preserved=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,authorization_end_utc=p['deadline_utc'])
    save(D/'summary-private.json',public);save(G/'retry/episode336_result.json',public);print(json.dumps(dict(status=public['status'],cost=cost,repair_verified=True,replacement_not_run=True)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',required=True,type=Path);close(p.parse_args().private_root)
