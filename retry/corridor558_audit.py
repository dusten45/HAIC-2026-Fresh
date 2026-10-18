"""Read-only audit: a finite joint-solver failure is not infeasibility proof."""
import json,math,subprocess,time
from pathlib import Path
from retry.period556_model import rd,sha
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response558-private');cpu,wall=time.process_time(),time.perf_counter()
c=rd(G/'retry/corridor558_contract.json');r=rd(G/'retry/corridor558_result.json');goal=rd(D/'goals-private.json');log=[json.loads(s) for s in (D/'solver-private.jsonl').read_text().splitlines()];last=rd(D/'latest-checkpoint-private.json');checks={}
checks['source_input_goals_hashes']=all(sha(G/p)==h for p,h in c['source_sha256'].items()) and all(sha(Path(p))==h for p,h in c['private_inputs_sha256'].items()) and sha(D/'goals-private.json')==c['goals_sha256']
checks['started_pin']=rd(D/'STARTED.json')['contract_sha256']==sha(G/'retry/corridor558_contract.json')
checks['same_synthetic_initial']=last['initial']==rd(Path('/workspace/haic-response557-private/fixture0-max-period-private.json'))['initial_root_without_roads']
checks['fixed_time_arc_targets']=goal['primary_T']==.48 and goal['follow_T']==.64 and abs(goal['primary']['station']-goal['initial_station']-goal['initial_speed']*.48)<1e-10 and abs(goal['follow']['station']-goal['initial_station']-goal['initial_speed']*.64)<1e-10
checks['single_run_and_initialization']=(D/'initialization-private.json').exists() and len(list(D.glob('*solver-private.jsonl')))==1 and len(log)==r['cost']['unique_evaluations']<=1100
checks['joint_feasibility_flags']=all(z['feasible']==(z['eq_max']<=1e-8 and z['ineq_min']>=-1e-7) for z in log)
found=any(z['feasible'] for z in log);checks['feasible_report_matches_log']=found==r['feasible_iterate_found']
checks['independent_validation_gate']=found==bool(r.get('validation_executed'))==(D/'independent-validation-private.json').exists()
cost=r['cost'];extra=0;extra_force=0;extra_geometry=0
if found:
 v=rd(D/'independent-validation-private.json');rows=v.get('rows',[]);accepted=[x for x in rows if x['accepted']];extra=4+len(accepted);extra_force=4*sum(not x['accepted'] and 'forces' in x for x in rows);extra_geometry=5+len(accepted)+len(accepted)//4+sum(not x['accepted'] and 'forces' in x for x in rows)
checks['every_complete_rollout_accounted']=cost['model_ticks']==36*len(log)+extra and cost['explicit_wheel_force_evaluations']==4*cost['model_ticks']+extra_force and cost['internal_wheel_force_evaluations']==4*cost['model_ticks'] and cost['body_checks']==cost['model_ticks']
checks['geometry_inside_every_rollout']=cost['geometry_checks']==38*len(log)+extra_geometry
checks['finite_stopping_not_rerun']=((r.get('nit') is not None and r['nit']<=40) or r.get('solver_message')=='UNIQUE_EVALUATION_CAP') and r.get('completed',False)
checks['budget_and_body_domain']=cost['model_ticks']<=42000 and cost['explicit_wheel_force_evaluations']<=175000 and cost['geometry_checks']<=42500 and cost['CPU_s']<=900 and cost['wall_s']<=1000 and cost['max_body_speed']<100
checks['no_false_performance_promotion']=r['actual_baseline_s']==13.66 and r['no_lap_gain_observation']
checks['actual_protected_reserve_zero']=all(r[k]==0 for k in ['new_native_actions','new_resets','new_worlds','new_seeds','HOLDOUT_queries','SEALED_queries','reserve_used']) and r['research_remaining']==22758 and r['reserve']==84000
checks['main_preserved']=subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31'
closest=min(log,key=lambda z:max(z['eq_max']/1e-8,max(0.,-z['ineq_min'])))
diag=dict(unique_evaluations=len(log),feasible_evaluations=sum(z['feasible'] for z in log),minimum_observed_scaled_period_residual=min(z['eq_max'] for z in log),best_observed_min_inequality=max(z['ineq_min'] for z in log),closest_joint_tolerance_violation=dict(call=closest['call'],eq_max=closest['eq_max'],ineq_min=closest['ineq_min'],objective=closest['objective'],detail=closest['detail'],geometry_min=closest['geometry_min'],patherror_max=closest['patherror_max']),last_evaluation=dict(eq_max=log[-1]['eq_max'],ineq_min=log[-1]['ineq_min'],detail=log[-1]['detail'],geometry_min=log[-1]['geometry_min'],patherror_max=log[-1]['patherror_max']),diagnostics_not_executed_candidates=True)
out=dict(passed=all(checks.values()),checks=checks,diagnostics=diag,scientific_cost=cost,audit_source_ticks=0,audit_force_evaluations=0,audit_geometry_evaluations=0,audit_CPU_s=time.process_time()-cpu,audit_wall_s=time.perf_counter()-wall)
with (G/'retry/corridor558_audit.json').open('x') as f:json.dump(out,f,indent=2,allow_nan=False)
with (G/'retry/corridor558_summary.json').open('x') as f:json.dump(dict(audit_passed=out['passed'],completed=r['completed'],solver_success=r.get('solver_success'),solver_status=r.get('solver_status'),solver_message=r.get('solver_message'),nit=r.get('nit'),feasible_iterate_found=found,diagnostics=diag,scientific_cost=cost),f,indent=2,allow_nan=False)
print(json.dumps(dict(passed=out['passed'],checks=checks,diagnostics=diag),indent=2));raise SystemExit(0 if out['passed'] else 1)
