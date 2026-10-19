"""Post-execution arithmetic on saved native records; no native/model/geometry execution."""
import json,hashlib,time
from pathlib import Path
CPU=time.process_time();WALL=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response598-private')
rd=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run():
 r=rd(G/'retry/cold598_result.json');a=rd(G/'retry/cold598_audit.json');arms={};derived_geo={}
 for summary in r['arms']:
  label=summary['label'];rows=rd(D/f'arm-{label}-private.json')['raw_records'];groups={g:dict(clipped=0,samples=0,peak=0.) for g in ['launch','running']};maximum_tracking_clip=0.;launch_end_clip=None;numeric=True;drive=0
  for q in rows:
   numeric &= q['body_speed_max']<100 and q['margin']>=.25
   if q['phase']!='action':continue
   drive+=1;group='launch' if q['action']<=24 else 'running';z=groups[group];z['clipped']+=sum(f['ratio']>1 for f in q['forces']);z['samples']+=4;z['peak']=max(z['peak'],max(f['ratio'] for f in q['forces']));fraction=z['clipped']/z['samples']
   if group=='running':maximum_tracking_clip=max(maximum_tracking_clip,fraction);numeric &= z['peak']<=1.25 and fraction<=.10 and q['speed']-q['reference_speed']<=5
   else:
    numeric &= z['peak']<=2.5
    if z['samples']==384:launch_end_clip=fraction;numeric &= fraction<=.15
   numeric &= q['path_error']<=3 and q['projection_lower']<=q['projection_delta']<=q['projection_upper'] and q['force_oracle_vector_error_N']<=.05 and q['COM_impulse_error_m_s']<=.01
   e=q['forecast_error'];numeric &= e['position_m']<=.10 and abs(e['speed_m_s'])<=.15 and abs(e['angle_rad'])<=.02 and abs(e['yaw_rad_s'])<=.05 and e['max_force_ratio_error']<=.19
  assert numeric and groups==summary['force_groups'] and drive==summary['counts']['raw_completed']-51
  arms[label]=dict(all_saved_numeric_native_gates=True,drive_raw=drive,tracking_clip_prefix_max=maximum_tracking_clip,launch_clip_at_end24=launch_end_clip,force_groups_exact=True,final_groups=groups)
  # The frozen primary counter uses margin/projection packs. Count the four explicit
  # native sensor indexed_contacts calls per completed raw separately and conservatively.
  raw=summary['counts']['native_raw_calls'];sensor=4*raw;primary=summary['counts']['geometry'];derived_geo[label]=dict(primary_margin_projection_packs=primary,explicit_native_sensor_contact_queries=sensor,conservative_sum=primary+sensor,arm_cap=300000,under_arm_cap=primary+sensor<=300000)
 total_sensor=sum(v['explicit_native_sensor_contact_queries'] for v in derived_geo.values());grand=r['cost']['geometry']+total_sensor;assert grand<=600000 and all(v['under_arm_cap'] for v in derived_geo.values())
 bounds=dict(ordinary_feedback_with_sensors=32*(49+48+44)+6+4+12+16,transition_anchor_with_outer_and_sensors=32*(49+48+44)+6+49+48+40+4+12+16,cheap_prefix_with_sensors=49+48+4+12+16)
 assert bounds['ordinary_feedback_with_sensors']<=5000 and bounds['transition_anchor_with_outer_and_sensors']<=5000 and bounds['cheap_prefix_with_sensors']<=300
 out=dict(study=598,status='POST_EXECUTION_READ_ONLY_ARITHMETIC_NO_GATE_CHANGE',native_numeric_summary=arms,geometry_unit_note='Frozenprimarycountercountsapplicationmargin/projectionpacks;integratorandnativephysicscontactinternalsarechargedbytick/raw. Thisseparatesadditionalexplicitnativeinput-sensorcontactqueries;primarycontract/resultunchanged. Fourqueriesperrawverifiedbyfrozenstepcomprehensionandall1447successfuldispatches;noqueriesexecutedbythisreview.',geometry=derived_geo,primary_geometry=r['cost']['geometry'],explicit_native_sensor_contact_queries=total_sensor,conservative_application_geometry_sum=grand,geometry_cap=600000,conservative_under_cap=True,per_hold_conservative_bounds_including_sensors=bounds,monitor_recovery=dict(existing_process_pid=36837,original_run_retained=True,interrupt_signals_sent=0,duplicate_science_executions=0,only_original_two_authorized_worlds=True,private_evidence_sha256=r['private_sha256']['monitor-recovery-private.json']),limits=dict(cold_only_privileged_DEV=True,pixel_policy_validated=False,Agent_act_5s_validated=False,other_initialization_validated=False,carry_combined_general_promotion=False,eleven_second_target_achieved=False,whole_policy_bundle_comparison_not_component_causality=True),next_action='Preserveonecold-onlynativepositivebenchmarkandclosedcarry/combined/generalstatus. Anyfurtherexperimentneedsseparatescopeandpredeclaredgates. Firstreviewpixel-observation/5sdeploymentboundaryand11secondbottleneckusingstoredtraces;noadditionalnativeornewseedstarted.',source_ticks=0,native_calls=0,force_calls=0,geometry_queries=0,input_sha256=dict(result=sha(G/'retry/cold598_result.json'),audit=sha(G/'retry/cold598_audit.json'),review_code=sha(Path(__file__))),CPU_s=time.process_time()-CPU,wall_s=time.perf_counter()-WALL,time_accounting='Coveredbyaudit5CPU/wallauxiliarycharge;noextraexperiment.')
 with (G/'retry/cold598_review.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()
