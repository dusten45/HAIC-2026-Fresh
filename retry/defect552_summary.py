"""Aggregate saved552 evidence without propagation or policy execution."""
import hashlib,json,time
from pathlib import Path
import numpy as np
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response552-private')
def stats(v):
 a=np.asarray(v,float);return dict(min=float(min(a)),median=float(np.median(a)),p95=float(np.quantile(a,.95)),max=float(max(a)))
def run():
 cpu=time.process_time();rd=lambda p:json.loads(p.read_text());analysis=rd(G/'retry/defect552_analysis.json');probe=rd(G/'retry/defect552_probe_result.json');audit=rd(G/'retry/defect552_audit.json');assert audit['passed'];details=rd(D/'analysis-detail-private.json');ranges={}
 for arm,rows in details.items():
  records=rows['full_before_hold_ranges'];ranges[arm]=dict(sampled_before_hold_states=len(records),instant_grid_min_acceleration_m_s2=stats([r['instant_min_accel'] for r in records]),instant_grid_max_acceleration_m_s2=stats([r['instant_max_accel'] for r in records]),not_multitick_capacity=True,finite_19_pedal_algebra_only=True)
 out=dict(status='POSITIVE_SOURCE_STATE_BRAKING_REACHABILITY_WITNESS',chosen_structure='Source-state-dependent braking reachability for retiming; no uniform brake constant/cap/gain replacement.',source551_whole_model_s=13.22,actual_champion541_s=13.66,prior551_gain_ms=440,prior551_500ms_gate_passed=False,source_surrogate_gain_s=analysis['surrogate_gain_s'],source_whole_observed_gain_s=.44,source_compatible_scalar80_lower_distance_m=audit['source_compatible_scalar80_Euler_lower_distance_m'],source_COM_distance_upper_m=audit['source_COM_distance_upper_with_guard_m'],conservative_stopping_distance_advantage_m=audit['conservative_COM_vs_discrete80_advantage_m'],old_design_progress_gate_passed=probe['passed'],physical_bounds_and_current551_reference_preserved=probe['safe_source_stopping_witness'],whole_lap_time_gain_from_probe_s=None,new_racing_candidate=False,actual_promotion=False,range_algebra=ranges,aligned_lateral_force_mismatch=audit['aligned_normal_force_mismatch'],science_cost=dict(analysis_model_ticks=0,probe_model_ticks=probe['model_ticks'],analysis_force_algebra_evaluations=analysis['cost']['force_evaluations'],probe_explicit_force_evaluations=probe['cost']['force_evaluations'],probe_integrator_wheel_evaluations=4*probe['model_ticks'],probe_geometry_checks=probe['cost']['geometry_checks'],analysis_CPU_s=analysis['CPU_s'],probe_CPU_s=probe['CPU_s']),new_native_actions=0,new_resets=0,new_seeds=0,protected_queries=0,research_remaining=22758,reserve=84000,reserve_used=0,conditional_actual_max_actions=1000,conditional_actual_max_resets=2,deadline_utc='2026-10-20T10:01:55+00:00',summary_CPU_s=time.process_time()-cpu)
 with (G/'retry/defect552_summary.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()
