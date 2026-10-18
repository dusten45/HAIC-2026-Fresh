"""Read-only records/hash/kinematic audit; no force calls or propagation."""
import hashlib,json,math,subprocess,time
from pathlib import Path
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response555-recovery-private')
rd=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cpu,wall=time.process_time(),time.perf_counter();checks={}
c=rd(G/'retry/drift555_contract.json');r=rd(G/'retry/drift555_result.json')
cr=rd(G/'retry/drift555_recovery_contract.json');rr=rd(G/'retry/drift555_recovery_result.json')
dc=rd(G/'retry/drift555_diagnostic_contract.json');dr=rd(G/'retry/drift555_diagnostic.json')
b=rd(D/'steady-branches-private.json');w=rd(D/'source-witnesses-private.json')
path=rd(Path('/workspace/haic-response551-private/frozen-paths-private.json'))['candidate']
checks['original_source_and_inputs_pinned']=all(sha(G/p)==h for p,h in c['source_sha256'].items()) and all(sha(Path(p))==h for p,h in c['private_inputs_sha256'].items())
checks['recovery_source_and_inputs_pinned']=all(sha(G/p)==h for p,h in cr['source_sha256'].items()) and all(sha(Path(p))==h for p,h in cr['private_inputs_sha256'].items())
checks['both_started_pins']=rd(Path('/workspace/haic-response555-private/STARTED.json'))['contract_sha256']==sha(G/'retry/drift555_contract.json') and rd(D/'STARTED.json')['contract_sha256']==sha(G/'retry/drift555_recovery_contract.json')
checks['executed_recovery_source_pinned']=rd(D/'STARTED.json')['executed_source_sha256']==sha(D/'executed-source-private.py')
checks['original_numerical_failure_preserved']=r['error']=='RuntimeError:LOW_SPEED_BRANCH_NOT_FOUND' and r['cost']['model_ticks']==0 and cr['original_contract_sha256']==sha(G/'retry/drift555_contract.json')
checks['physical_and_effect_gates_unchanged']=c['constants']==cr['constants'] and c['stop_promotion']==cr['stop_promotion']
checks['diagnostic_inputs_pinned']=all(sha(Path(p))==h for p,h in dc['inputs_sha256'].items()) and dc['source_sha256']==sha(G/'retry/drift555_diagnose.py')
checks['all283_finite_equilibria']=len(b)==len(path['ds'])==283 and all(z['admitted'] and z['equilibrium_residual']<=1e-7 and max(z['ratios'])<=.999 and z['speed']<=90 and abs(z['delta'])<=.4 and abs(z['beta'])<=.6 for z in b)
clock=sum(2*d/(b[i]['speed']+b[(i+1)%len(b)]['speed']) for i,d in enumerate(path['ds']))
checks['optimistic_clock_recomputed']=abs(clock-rr['optimistic_station_clock_s'])<1e-12 and (clock<=12.22)==rr['optimistic_clock_gate']
ids=sorted(set([max(range(len(b)),key=lambda i:abs(b[i]['beta'])),max(range(len(b)),key=lambda i:max(b[i]['ratios']))]))
checks['predeclared_two_extreme_fixtures']=ids==[x['station'] for x in w]
checks['actual_source_force_matches_initial_algebra']=all(z['initial_analytic_source_vector_error_N']<1e-6 for z in dr['cases'])
checks['two_failures_after_one_tick']=len(w)==2 and all(len(x['rows'])==1 and not x['passed'] and x['first_failure']=='SOURCE_FORCE_OR_CLIP' for x in w) and rr['cost']['model_ticks']==2
checks['one_force_failure_one_clip_only']=sorted(z['global_force_guard_pass'] for z in dr['cases'])==[False,True] and all(z['rejected_clipped_wheels']>0 for z in dr['cases'])
euler=[]
for x in w:
    before=x['initial_root_without_roads']['planar'];after=x['rows'][0]['root_without_roads']['planar'];v=math.hypot(*before['linear']['velocity']);u=math.hypot(*after['linear']['velocity'])
    predicted=v*math.sqrt(1+(.02*before['yaw'])**2)-v
    discrete_tangential_force=before['linear']['mass']*v*(math.cos(.02*before['yaw'])-1)/.02
    euler.append(dict(observed_speed_drift_m_s=u-v,continuous_normal_force_euler_speed_drift_m_s=predicted,absolute_drift_error_m_s=abs((u-v)-predicted),exact_discrete_turn_required_tangential_force_N=discrete_tangential_force))
checks['discrete_speed_drift_explained']=all(z['absolute_drift_error_m_s']<1e-7 for z in euler)
cost=dict(analytic_wheel_evaluations=r['cost']['analytic_wheel_evaluations']+rr['cost']['analytic_wheel_evaluations'],explicit_source_wheel_evaluations=rr['cost']['explicit_source_wheel_evaluations']+dr['cost']['explicit_source_wheel_evaluations'],model_ticks=rr['cost']['model_ticks'],internal_wheel_evaluations=4*rr['cost']['model_ticks'],geometry=rr['cost']['geometry'],nonlinear_solves=r['cost']['nonlinear_solves']+rr['cost']['nonlinear_solves'],CPU_s=r['CPU_s']+rr['CPU_s']+dr['cost']['CPU_s'],wall_s=r['wall_s']+rr['wall_s']+dr['cost']['wall_s'])
checks['original_aggregate_caps_respected']=cost['analytic_wheel_evaluations']<=2000000 and cost['explicit_source_wheel_evaluations']<=40 and cost['model_ticks']<=8 and cost['geometry']<=10 and cost['CPU_s']<=90 and cost['wall_s']<=120
checks['no_deep_actual_protected_or_reserve']=rr['deep_phases_executed']==0 and rr['new_native_actions']==rr['new_resets']==rr['new_worlds']==rr['new_seeds']==rr['HOLDOUT_queries']==rr['SEALED_queries']==rr['reserve_used']==0 and rr['research_remaining']==22758 and rr['reserve']==84000
checks['main_preserved']=subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31'
out=dict(passed=all(checks.values()),checks=checks,scientific_cost=cost,source_discrete_turn_diagnostics=euler,no_additional_force_calls_or_model_ticks=True,audit_CPU_s=time.process_time()-cpu,audit_wall_s=time.perf_counter()-wall)
with (G/'retry/drift555_audit.json').open('x') as f:json.dump(out,f,indent=2,allow_nan=False)
print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed'] else 1)
