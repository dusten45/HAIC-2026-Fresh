"""Publication/accounting audit only; no new model or native calls."""
import hashlib,json,time
from pathlib import Path
G=Path(__file__).resolve().parents[1];A=Path('/workspace/haic-response535-private');B=Path('/workspace/haic-response535-recovery-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();native=json.loads((G/'retry/footprint535_native_result.json').read_text());pref=json.loads((G/'retry/footprint535_recovery_result.json').read_text());stop=json.loads((G/'retry/footprint535_stop_diagnostic.json').read_text());registration=json.loads((B/'native-registration-private.json').read_text());all_reports=[];body=0
    def reports(detail):
        if 'trials' in detail:return detail['trials']+[x for x in detail.get('reports',[]) if x['mode']=='FINAL']
        return detail.get('reports',[])
    for i in (165,164,153,141):
        x=json.loads((A/f'diagnostic-root-{i}-private.json').read_text());all_reports+=reports(x['old_detail'])+reports(x['new_detail']);all_reports += [x['summary']['old_action_geometry_certificate']] if x['summary']['old_action_geometry_certificate'] is not None else [];all_reports += [z['report'] for z in x['grid']]
    for file in ('early-recovery-private.json','regression-obstacle-private.json','regression-curvature-private.json','cold-candidate-model-private.json','carry-baseline528-model-private.json'):
        x=json.loads((A/file).read_text());body+=len(x['trace'])
        for command in x['commands']:all_reports+=reports(command['detail'])
    forecast=sum(x['model_ticks'] for x in all_reports);known=body+forecast;force=4*body+sum(4*x['model_ticks']+(4 if x['reason'] in ('FORCE_PEAK','CLIP_HISTORY') else 0) for x in all_reports);geometry=sum(1+x['model_ticks'] for x in all_reports if 'min_footprint_margin_m' in x)
    assert known<=120000 and force<=600000 and geometry<=130000
    currentmeasured=native['all_model_integrator_ticks']+stop['model_integrator_ticks'];force_new=native['all_model_wheel_force_evaluations']+stop['explicit_force_evaluations'];geonew=native['all_geometry_checks']+stop['cost']['geometry_checks']
    charges=[json.loads(p.read_text()) for p in sorted(B.glob('charge-*.json'))];assert len(charges)==native['counts']['actions']==262
    assert all(x['attempted_actual_actions']==i and x['research_remaining']==24155-i for i,x in enumerate(charges,1));assert native['research_remaining']==23893 and native['counts']['resets']==2 and native['counts']['worlds']==native['counts']['closed']==2
    records=[json.loads(p.read_text())['record'] for p in B.glob('action-*-*.json')];assert len(records)==262 and all(not x['flags'] for x in records)
    assert hashlib.sha256((G/'retry/footprint535_native_fixed.py').read_bytes()).hexdigest()==registration['native_source_sha256'];assert hashlib.sha256((B/'frozen-paths-private.json').read_bytes()).hexdigest()==registration['paths_sha256'];pins=True
    for name in ('footprint535_contract.json','footprint535_recovery_contract.json','footprint535_stop_contract.json'):
        c=json.loads((G/'retry'/name).read_text());pins &= all(hashlib.sha256((G/z).read_bytes()).hexdigest()==h for z,h in c['source_sha256'].items());pins &= all(hashlib.sha256(Path(z).read_bytes()).hexdigest()==h for z,h in c['private_inputs_sha256'].items())
    assert pins
    old525=json.loads((G/'retry/governor525b_native_result.json').read_text())['arms'][1];base=native['arms'][0];matches=all(base[k]==old525[k] for k in ('official_finish_episode_s','min_margin_m','max_path_error_m','force_groups','mode_counts'))
    out=dict(native_actions_precharged=262,research_remaining=23893,reserve=84000,reserve_used=0,worlds_created=2,worlds_closed=2,resets=2,world_cleanup_assertions_passed=True,all_action_guard_flags_empty=True,baseline525_saved_metrics_identical=matches,source_input_and_active_entry_pins_verified=True,known_completed_original535_execution_ticks=body,known_completed_original535_forecast_ticks=forecast,known_completed_original535_ticks=known,known_completed_original535_explicit_force=force,known_completed_original535_geometry_checks=geometry,original535_partial_carry_counts_exact=False,original535_reserved_ticks=120000,original535_reserved_explicit_force=600000,original535_CPU_cap_reached_s=600,new_recovery_native_stop_measured_ticks=currentmeasured,new_recovery_native_stop_measured_explicit_force=force_new,new_recovery_native_stop_measured_geometry_checks=geonew,total_model_ticks_lower_bound=known+currentmeasured,total_model_ticks_upper_bound=120000+currentmeasured,total_explicit_force_lower_bound=force+force_new,total_explicit_force_upper_bound=600000+force_new,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,extra_model_ticks=0,extra_force_evaluations=0,native_calls=0,scope='OriginalCPU-stopmissingcountertruthfullybounded,notclaimedexact.Onlyoneactualpair;safeSTOPnotfinish/gain. Noadditionalcase/policy/world.')
    with (G/'retry/footprint535_final_audit.json').open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
