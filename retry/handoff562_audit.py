"""Read-only full-source handoff/finish/cost audit; uses saved diagnostic only."""
import json,math,subprocess,time
from pathlib import Path
from retry.period556_model import rd,sha
from retry.clip561_core import atomic_write
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response562-private');cpu,wall=time.process_time(),time.perf_counter();c=rd(G/'retry/handoff562_contract.json');r=rd(G/'retry/handoff562_result.json');cost=rd(G/'retry/handoff562_cost.json');diag=rd(G/'retry/handoff562_diagnostic.json');dc=rd(G/'retry/handoff562_diagnostic_contract.json');prep=rd(D/'prefix-modified-private.json');fixed=rd(D/'fixed-suffix-private.json');handoff=rd(D/'altered-handoff-private.json');saved=rd(Path('/workspace/haic-response551-private/cold-candidate-private.json'));candidate=rd(Path('/workspace/haic-response561-private/branch-00-00-private.json'));segment=rd(Path('/workspace/haic-response560-private/segment-private.json'));checks={}
checks['source_and_inputs_pinned']=all(sha(G/p)==h for p,h in c['source_sha256'].items()) and all(sha(Path(p))==h for p,h in c['private_inputs_sha256'].items())
checks['diagnostic_pinned_no_physics']=dc['source_sha256']==sha(G/'retry/handoff562_diagnose.py') and all(sha(Path(p))==h for p,h in dc['inputs_sha256'].items()) and diag['model_ticks']==diag['force_calls']==0 and diag['geometry_components']==2
checks['phase_start_and_finally_ledgers']=all(rd(D/f'{name}-STARTED.json')['contract_sha256']==sha(G/'retry/handoff562_contract.json') and rd(D/f'{name}-cost-ledger-private.json')['label']=='phase-finally-FIRST' and all(rd(D/f'{name}-cost-ledger-private.json')['cost'][k]==v for k,v in phase.items() if k!='error') for name,phase in cost['phases'].items())
checks['completed_driver_and_tracker_semantics']=r['completed'] and r['error'] is None and all(r['checks'].values()) and r['checks']['saved551_tracker_exact']
checks['original_prefix_state_force_exact']=len(prep['rows'])==268 and all(a['root_without_roads']==b['root_without_roads'] and a['forces']==b['forces'] for a,b in zip(prep['rows'][:136],saved['trace'][:136]))
checks['modified561_state_force_exact']=all(a['root_without_roads']==b['root_without_roads'] and a['forces']==b['forces'] for a,b in zip(prep['rows'][136:],candidate['rows']))
commands={x['index']:x['action'] for x in prep['commands']};checks['modified_commands_exact_and_only20holds']=all(commands[35+j]==[candidate['x'][2*j],max(0.,candidate['x'][2*j+1]),max(0.,-candidate['x'][2*j+1])] for j in range(20)) and all(commands[i]==segment['commands'][i-35] for i in range(55,68))
checks['same_altered_handoff_no_history_reset']=fixed['start_hash']==handoff['hash'] and handoff['checkpoint']==prep['checkpoint'] and handoff['checkpoint']['tracking']==[30,688]
checks['fixed_first_real_failure']=fixed['stop']=='FOOTPRINT' and fixed['failure']['index']==72 and fixed['failure']['raw']==2 and fixed['failure']['row']['margin']<.5 and fixed['failure']['row']['path_error']<=3 and max(f['ratio'] for f in fixed['failure']['row']['forces'])<=1.059
checks['obstacle_component_not_comparative_aperture']=diag['recorded_component_matches'] and diag['first_component']=='OBSTACLE' and diag['road_margin_m']>.5 and diag['obstacle_margin_m']<0 and diag['baseline_sameclock_margin_m']>.5
feedback=rd(D/'feedback-suffix-private.json') if (D/'feedback-suffix-private.json').exists() else None
if feedback:
 checks['feedback_conditional_from_identical_altered_state']=not r['fixed']['safe_finish'] and feedback['start_hash']==handoff['hash']
 checks['unchanged_feedback_fresh_FINAL']=all(x['detail']['final_recertified'] and next(q for q in x['detail']['reports'] if q['mode']=='FINAL')['ok'] for x in feedback['commands'])
checks['independent_last_tape_verification']=len(r['independent_verification'])==(1 if r['winning_suffix'] else 2) and all(v['fullstate_force_exact'] and v['checkpoint_exact'] and v['finish_same'] for v in r['independent_verification'])
case=feedback if r['winning_suffix']=='feedback-suffix' else fixed if r['winning_suffix'] else None
if case:
 allrows=prep['rows']+case['rows'];tracking_clips=tracking_samples=launch_clips=launch_samples=0;maxclip=0.;all_safe=True
 for row in allrows:
  assert 'root_without_roads' in row
  peak=max(f['ratio'] for f in row['forces']);clipped=sum(f['clipped'] for f in row['forces'])
  if row['index']<=24:
   launch_clips+=clipped;launch_samples+=4;all_safe &=peak<=2.5 and (row['index']<24 or launch_clips/launch_samples<=.15)
  else:
   tracking_clips+=clipped;tracking_samples+=4;maxclip=max(maxclip,tracking_clips/tracking_samples);all_safe &=peak<=1.059 and tracking_clips/tracking_samples<=.1 and row['reference_overspeed']<=4.85
  all_safe &=row['margin']>=.5 and row['path_error']<=3 and row['body']<100
 checks['whole_combined_global_safety']=bool(all_safe) and tracking_clips==case['checkpoint']['tracking'][0] and tracking_samples==case['checkpoint']['tracking'][1]
 finish=case['checkpoint']['tracker']['finish_time_s']-1.02
 checks['whole_time_measured_not_local_gain_sum']=r['whole_source_finish_s']==finish and abs(r['baseline551_source_finish_s']-13.22)<1e-9 and abs(r['whole_source_gain_ms']-1000*(r['baseline551_source_finish_s']-finish))<1e-9 and case['stop']=='SOURCE_FINISH'
else:
 checks['no_whole_finish_or_gain_invented']=r['whole_source_finish_s'] is None and r['whole_source_gain_ms'] is None
checks['phase_costs_and_all_forecast_bodies_charged']=all(p['body_checks']==p['model_ticks'] and p['model_ticks']==p['forecast_ticks']+sum(1 for row in rd(D/({'preparation':'prefix-modified','fixed':'fixed-suffix','feedback':'feedback-suffix'}.get(name,'unused')+'-private.json'))['rows'] if 'root_without_roads' in row) if name!='verification' else p['body_checks']==p['model_ticks'] for name,p in cost['phases'].items())
checks['phase_and_aggregate_budgets']=all(all(p[k]<=c['phase_caps'][name][cap] for k,cap in [('model_ticks','model_ticks'),('force_evaluations','force'),('geometry_checks','geometry'),('CPU_s','CPU_s'),('wall_s','wall_s')]) and p['max_all_model_body']<100 for name,p in cost['phases'].items()) and cost['total']['model_ticks']<=c['aggregate_caps']['model_ticks'] and cost['total']['force_evaluations']<=c['aggregate_caps']['force'] and cost['total']['geometry_checks']+2<=c['aggregate_caps']['geometry'] and cost['total']['CPU_s']+diag['CPU_s']<=c['aggregate_caps']['CPU_s'] and cost['total']['wall_s']+diag['wall_s']<=c['aggregate_caps']['wall_s']
checks['cost_totals_reconciled']=r['cost']==cost['total'] and all(v==sum(p[k] for p in cost['phases'].values()) for k,v in cost['total'].items())
checks['prior561_aperture_failure_preserved']=r['prior561_aperture_failure_preserved'] and rd(G/'retry/mode561_result.json')['accepted_count']==0
checks['no_native_protected_reserve']=all(r[k]==0 for k in ['new_native_actions','new_resets','new_worlds','new_seeds','HOLDOUT_queries','SEALED_queries','reserve_used']) and r['research_remaining']==22758 and r['reserve']==84000 and r['actual_baseline_s']==13.66 and r['no_native_gain_observation']
checks['main_preserved']=subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31'
out=dict(passed=all(checks.values()),checks=checks,driver_cost=cost['total'],additional_geometry_diagnostic_cost={k:diag[k] for k in ['model_ticks','force_calls','geometry_components','CPU_s','wall_s']},all_analysis_CPU_s=cost['total']['CPU_s']+diag['CPU_s'],summed_timed_wall_s=cost['total']['wall_s']+diag['wall_s'],wall_note='Sum of scoped timed windows,including tiny concurrent diagnostic; not end-to-end task duration.',audit_source_ticks=0,audit_force_calls=0,audit_geometry_calls=0,audit_CPU_s=time.process_time()-cpu,audit_wall_s=time.perf_counter()-wall)
atomic_write(G/'retry/handoff562_audit.json',out);print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed'] else 1)
