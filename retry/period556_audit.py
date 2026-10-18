"""Read-only complete-state/cost/gate audit; zero new source evaluations."""
import json,hashlib,subprocess,time
from pathlib import Path
from retry.period556_model import difference,load_root
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response556-private')
rd=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cpu,wall=time.process_time(),time.perf_counter();c=rd(G/'retry/period556_contract.json');r=rd(G/'retry/period556_result.json');static=rd(Path('/workspace/haic-response515-private/collected-map-state-private.json'));old=rd(Path('/workspace/haic-response555-recovery-private/source-witnesses-private.json'))
cases=[rd(D/f'fixture{i}-period-private.json') for i in range(2)];checks={};aggregates=[]
checks['source_and_input_hashes']=all(sha(G/p)==h for p,h in c['source_sha256'].items()) and all(sha(Path(p))==h for p,h in c['private_inputs_sha256'].items())
checks['started_pin']=rd(D/'STARTED.json')['contract_sha256']==sha(G/'retry/period556_contract.json')
checks['completed_two_states']=r['completed'] and len(r['periodic_states'])==2 and len(cases)==2
checks['same_synthetic_fixture_poses']=all(z['initial_root_without_roads']['center']==o['initial_root_without_roads']['center'] and z['initial_root_without_roads']['planar']['angle']==o['initial_root_without_roads']['planar']['angle'] for z,o in zip(cases,old))
checks['fullstate_schema_coverage']=all(set(z['initial_root_without_roads'])=={'planar','center','current_contacts','floor','skin'} and set(z['initial_root_without_roads']['planar'])=={'linear','levers','inertia','angular_momentum','yaw','angle','joints','rates','wheel_inertias','steer','steering_multiplier'} and set(z['initial_root_without_roads']['planar']['linear'])=={'velocity','wheels','mass','engine_multiplier'} and all(set(w)=={'omega','gas','heading','friction','offset'} for w in z['initial_root_without_roads']['planar']['linear']['wheels']) for z in cases)
for z in cases:
 initial=load_root(dict(z['initial_root_without_roads'],roads=static['root']['roads']));final=load_root(dict(z['terminal_root_without_roads'],roads=static['root']['roads']));d=difference(final,initial);rows=z['independent_rows'];log=[json.loads(s) for s in (D/f"{z['label']}-solver-private.jsonl").read_text().splitlines()]
 a=dict(label=z['label'],fullstate_difference=d,fullstate_normalized_max=max(v['normalized_max'] for v in d.values()),independent_period_peak=max(f['ratio'] for row in rows for f in row['forces']),independent_period_clipped_wheels=sum(f['clipped'] for row in rows for f in row['forces']),independent_period_wheel_samples=4*len(rows),initial_footprint=z['rows'][0]['margin'],initial_path_error=z['rows'][0]['patherror'],initial_old551_overspeed=z['rows'][0]['old551_overspeed'],road_ids_changed=initial.current_contacts!=final.current_contacts,friction_unchanged=d['friction']['max_abs']==0.,gas_memory_unchanged=d['gas']['max_abs']==0.,joint_rates_unchanged=d['rates']['max_abs']==0.,solver_log_rows=len(log),residual_calls=z['residual_calls'])
 aggregates.append(a)
checks['fullstate_residuals_recomputed']=all(a['fullstate_difference']==z['signature_difference'] and a['fullstate_normalized_max']<=1 for a,z in zip(aggregates,cases))
checks['float32_commands']=all(float(__import__('numpy').float32(x))==x for z in cases for x in z['action'])
checks['independent_four_source_raw']=all(len(z['independent_rows'])==4 and z['independent_raw_completed']==4 for z in cases)
checks['source_force_guard_failed_both']=all(a['independent_period_peak']>1.059 and not z['validation_safe'] and z['first_failure']=='FORCE' and len(z['rows'])==1 and not z['rows'][0]['accepted'] for a,z in zip(aggregates,cases))
checks['clip_distinct_from_force']=sorted(a['independent_period_clipped_wheels'] for a in aggregates)==[4,8]
checks['local_contact_regime_not_global_map_periodicity']=all(a['road_ids_changed'] and a['friction_unchanged'] for a in aggregates)
checks['no_stability_transition_after_gate_failure']=not r['cycles'] and r['transition']=={'executed':False,'reason':'ORIGINAL_PERIODIC_GATE_FAILED'} and not list(D.glob('*cycles-private.json')) and not (D/'transition-private.json').exists()
checks['finite_solver_calls_and_iterations']=all(a['solver_log_rows']==a['residual_calls']<=800 and z['nfev']<=60 for a,z in zip(aggregates,cases))
count=sum(a['residual_calls'] for a in aggregates);cost=r['cost']
checks['cost_reconciles_every_source_tick']=cost['residual_calls']==count and cost['model_ticks']==4*count+8 and cost['body_checks']==cost['model_ticks'] and cost['internal_wheel_force_evaluations']==4*cost['model_ticks'] and cost['explicit_wheel_force_evaluations']==4*cost['model_ticks']+8 and cost['geometry_checks']==2
checks['all_caps']=cost['model_ticks']<=30000 and cost['explicit_wheel_force_evaluations']<=125000 and cost['geometry_checks']<=300 and cost['CPU_s']<=300 and cost['wall_s']<=360 and cost['max_body_speed']<100
checks['no_native_protected_or_reserve']=all(r[k]==0 for k in ['new_native_actions','new_resets','new_worlds','new_seeds','HOLDOUT_queries','SEALED_queries','reserve_used']) and r['research_remaining']==22758 and r['reserve']==84000 and r['actual_baseline_s']==13.66 and r['no_lap_gain_observation']
checks['main_preserved']=subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31'
out=dict(passed=all(checks.values()),checks=checks,cases=aggregates,scientific_cost=cost,audit_model_ticks=0,audit_force_calls=0,audit_CPU_s=time.process_time()-cpu,audit_wall_s=time.perf_counter()-wall)
with (G/'retry/period556_audit.json').open('x') as f:json.dump(out,f,indent=2,allow_nan=False)
print(json.dumps(dict(passed=out['passed'],checks=checks,case_summary=[{k:a[k] for k in ['label','fullstate_normalized_max','independent_period_peak','independent_period_clipped_wheels','road_ids_changed']} for a in aggregates]),indent=2));raise SystemExit(0 if out['passed'] else 1)
