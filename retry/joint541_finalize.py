"""Finalize saved541 aggregates without simulator imports or new model calls."""
import datetime,hashlib,json,time
from pathlib import Path

def run():
    cpu=time.process_time();wall=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response541-private');read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    c=read(G/'retry/joint541_contract.json');native=read(G/'retry/joint541_native_result.json');exit=read(D/'native-exit-counters-private.json');audit=read(G/'retry/joint541_audit.json');assert native['practical_effect_gate'] and audit['status']=='SAVED_RECORD_AUDIT_PASS' and exit['counts']==native['counts']
    raw=[read(p) for p in sorted(D.glob('raw-*.json'))];full=read(D/'native-full-records-private.json');split=51+sum(x['raw_ticks'] for x in full[0]['rows']);arms={}
    for arm,rows in zip(native['arms'],(raw[:split],raw[split:])):
        actions=[r for r in rows if r['phase']=='action'];clips=samples=0;peak=0.
        for r in actions:
            assert not r['errors'] and r['body_speed_max']<100
            if r['action']>24:
                clips+=sum(z['ratio']>1 for z in r['forces']);samples+=4;peak=max(peak,clips/samples)
        assert peak<=.1 and len(actions)==sum(x['raw_ticks'] for x in full[0 if arm['budget']=='baseline' else 1]['rows'])
        arms[arm['budget']]=dict(official_finish_s=arm['official_finish_episode_s'],actions=arm['actions'],action_raw_ticks=len(actions),max_body_speed_m_s=max(r['body_speed_max'] for r in rows),max_cumulative_running_clipping=peak,final_running_clipped=clips,final_running_samples=samples,launch=arm['force_groups']['launch'],min_margin_m=arm['min_margin_m'],max_path_error_m=arm['max_path_error_m'],max_reference_overspeed_m_s=arm['max_tracking_overspeed_m_s'])
    assert native['research_remaining']==23107-native['counts']['actions']
    phases={p:read(G/f'retry/joint541_{p}_result.json') for p in ('pilot','cold','carry')};caps=c['aggregate_caps'];core_cpu=sum(r['CPU_s'] for r in phases.values())+exit['CPU_s'];core_wall=sum(r['wall_s'] for r in phases.values())+exit['wall_s'];assert core_cpu<=caps['CPU_s'] and core_wall<=caps['wall_s'] and native['all_geometry_checks']<=caps['geometry']
    assert not (G/'retry/profile539_carry_result.json').exists()
    out=dict(status='JOINT541_ACTUAL_PROMOTED_EXISTING_DEV_ONLY',finalized_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=c['deadline_utc'],actual_baseline_s=arms['baseline']['official_finish_s'],actual_candidate_s=arms['candidate']['official_finish_s'],actual_gain_ms=native['official_finish_gain_ms'],arms=arms,model_phase_passes={p:r['passed'] for p,r in phases.items()},cold_model_s=phases['cold']['case']['model_finish_episode_s'],carry_model_s=phases['carry']['case']['model_finish_episode_s'],carry_gain_vs538_ms=phases['carry']['gain_vs538_ms'],prior539_carry_was_observed=False,component_effects_not_assumed_additive=True,counts=native['counts'],research_remaining=native['research_remaining'],reserve=84000,reserve_used=0,all_model_integrator_ticks=native['all_model_integrator_ticks'],all_integrator_internal_wheel_evaluations=4*native['all_model_integrator_ticks'],all_explicit_force_evaluations=native['all_model_wheel_force_evaluations'],all_geometry_checks=native['all_geometry_checks'],core_CPU_through_native_exit_s=core_cpu,core_wall_through_native_exit_s=core_wall,import_failure_before_world_reset_action=True,actual_scientific_retries=0,new_seeds=0,protected_queries=0,new_model_ticks_in_finalization=0,new_actual_actions_in_finalization=0,supporting_sha256={str(p.relative_to(G)):sha(p) for p in [G/'retry/joint541_contract.json',G/'retry/joint541_gate_result.json',G/'retry/joint541_native_result.json',G/'retry/joint541_audit.json']},finalization_CPU_s=time.process_time()-cpu,finalization_wall_s=time.perf_counter()-wall)
    with (G/'retry/joint541_summary.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__':run()
