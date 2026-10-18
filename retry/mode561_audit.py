"""Read-only gate/count/lineage/cost audit; no source/force/geometry execution."""
import json,math,subprocess,time
from pathlib import Path
import numpy as np
from retry.clip561_core import prefix_slacks,nonexempt_branch
from retry.period556_model import rd,sha
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response561-private');cpu,wall=time.process_time(),time.perf_counter();c=rd(G/'retry/mode561_contract.json');r=rd(G/'retry/mode561_result.json');pre=rd(G/'retry/mode561_preflight.json');cost=rd(G/'retry/mode561_cost.json');checks={}
checks['source_input_hashes']=all(sha(G/p)==h for p,h in c['source_sha256'].items()) and all(sha(Path(p))==h for p,h in c['private_inputs_sha256'].items())
checks['started_and_cost_atomic_ledger']=rd(D/'STARTED.json')['contract_sha256']==sha(G/'retry/mode561_contract.json') and cost==r['cost']==rd(D/'cost-ledger-private.json')['cost'] and rd(D/'cost-ledger-private.json')['label']=='outer-finally-cost-FIRST'
checks['writer_fault_and_finally_tests_pass']=all(pre['checks'][k] for k in ['numpy_basic_roundtrip','nonfinite_preserves_old','atomic_replace_failure_preserves_old','exclusive_preserves_old','finally_numpy_cost_survives_exception'])
checks['strict_count_f32_ties_history_tests_pass']=pre['passed'] and pre['synthetic_equivalence_cases']==81229 and all(pre['checks'][k] for k in ['strict_ties_f32_history_denominator_equivalence','exact1_unclipped','nextafter_above1_clipped','active_identity_can_swap'])
checks['saved560_classification_no_new_model']=pre['model_ticks']==pre['force_calls']==pre['geometry_calls']==0 and pre['saved_cases'][0]['order_all_pass'] and all(not z['order_all_pass'] and z['order_all_pass']==z['count_all_pass'] for z in pre['saved_cases'][1:])
b=rd(D/'baseline-private.json');old=rd(Path('/workspace/haic-response560-private/baseline-private.json'));f=rd(D/'final-private.json');segment=rd(Path('/workspace/haic-response560-private/segment-private.json'))
checks['fresh_baseline_fullstate_force_exact']=r['exact_feasible_initialization'] and all(x['root_without_roads']==z['root_without_roads'] and x['forces']==z['forces'] for x,z in zip(b['rows'],old['rows']))
checks['old_fixed_planes_history_preserved']=segment['history']==[3,160] and [g['time'] for g in b['crossings']]==r['baseline_times_s']==[1.6,2.56] and segment['optimized_holds']==20 and segment['follow_holds']==12
labels=['baseline','branch-00-00','branch-00-01','poll-00-00','poll-00-01','final'];data=[rd(D/(name+'-private.json')) for name in labels]
for z in data:
 ratios=np.array([q['ratio'] for row in z['rows'] for q in row['forces']]);ss=prefix_slacks(ratios,3,160)
 assert np.array_equal(ratios,np.array(z['ratios'])) and np.array_equal(ss,np.array(z['order_slacks']))
 assert all((q['ratio']>1)==q['clipped'] for row in z['rows'] for q in row['forces'])
 assert bool(np.all(ss>=0))==(z['stats']['max_clip_fraction']<=.1)
checks['all_new_source_count_order_equivalence']=True
events=r['directions'][0]['proposals'];first=data[1];rebuilt=data[2];timepoll=data[3];relief=data[4]
checks['one_direction_two_branches_two_polls']=len(r['directions'])==1 and len(events)==4 and cost['LP_branches']==2 and cost['polls']==2 and cost['source_proposals']==4 and all(x['success'] for x in r['directions'][0]['LP_statuses'])
base_mask=np.array([q['clipped'] for row in b['rows'] for q in row['forces']]);ids0=nonexempt_branch(b['ratios'],3,160);ids1=nonexempt_branch(first['ratios'],3,160);e0=np.ones(528,bool);e1=e0.copy();e0[ids0]=False;e1[ids1]=False
checks['rank_branch_reconstruction_can_change_identity']=not np.array_equal(e0,e1) and np.sum(e1&~base_mask)>0
checks['new_clipping_physically_admitted_not_mask_veto']=first['physical_safe'] and events[0]['physical_safe'] and events[0]['branch_changes']['new_clipped_samples']==4 and events[0]['branch_changes']['freed_clipped_samples']==5 and np.min(first['order_slacks'])>=0
checks['first_rejection_is_handoff_design']=not first['feasible'] and first['physical_safe'] and min(g for g,n in zip(first['g'],first['labels']) if n!='gate_position')>=-1e-10 and min(g for g,n in zip(first['g'],first['labels']) if n=='gate_position')<0
checks['rebuilt_and_timepoll_actual_global_fail']=not rebuilt['physical_safe'] and rebuilt['stats']['max_clip_fraction']>.1 and not timepoll['physical_safe'] and timepoll['stats']['max_reference_overspeed']>4.85
checks['relief_poll_feasible_but_slower']=relief['feasible'] and relief['physical_safe'] and all(z['time']>base['time'] for z,base in zip(relief['crossings'],b['crossings'])) and not events[3]['accepted']
fd=[rd(Path(f'/workspace/haic-response560-private/FD-00-{i:02d}-private.json')) for i in range(40)];x=np.array(b['x']);times=lambda z:np.array([q['time'] for q in z['crossings']]);T=np.array([(times(q)-times(b))/(q['x'][i]-x[i]) for i,q in enumerate(fd)]).T
checks['cached_force_time_lineage_no_count_derivative']=cost['reused_FD_columns']==40 and cost['fresh_FD_columns']==0 and all(np.max(abs(-1000*T@(np.array(z['x'])-x)-event['predicted_gain_ms']))<1e-10 and np.max(abs(1000*(times(b)-times(z))-event['actual_gain_ms']))<1e-10 for z,event in zip(data[1:5],events))
checks['final_immutable_baseline_and_zero_gain']=r['accepted_count']==0 and r['cumulative_gain_ms']==[0.,0.] and r['stop_reason']=='NO_ACCEPTED_BRANCH_OR_TWO_POLLS' and len(list(D.glob('incumbent-*-private.json')))==1 and rd(D/'incumbent-00-private.json')['evaluation_sha256']==sha(D/'baseline-private.json')
checks['fresh_final_fullstate_follow_exact']=r['final_fresh_replay_exact'] and r['final_feasible'] and all(a['root_without_roads']==z['root_without_roads'] and a['forces']==z['forces'] for a,z in zip(f['rows'],b['rows'])) and len(f['rows'])==132 and times(f).tolist()==[1.6,2.56]
checks['every_tick_force_geometry_body_charged']=cost['evaluations']==6 and cost['model_ticks']==6*132==792 and cost['explicit_wheel_force_evaluations']==cost['internal_wheel_force_evaluations']==4*792 and cost['body_checks']==792 and cost['geometry_checks']==6*133==798
checks['complete_CPU_wall_current_run_within_caps']=isinstance(cost['CPU_s'],float) and isinstance(cost['wall_s'],float) and 0<cost['CPU_s']<=400 and 0<cost['wall_s']<=480 and cost['model_ticks']<=20000 and cost['explicit_wheel_force_evaluations']<=85000 and cost['geometry_checks']<=20000 and cost['max_body_speed']<100
checks['old560_CPU_gap_untouched']=rd(G/'retry/sequential560_summary.json')['cost']['aggregate_CPU600_independently_verified'] is False
checks['no_actual_protected_reserve']=all(r[k]==0 for k in ['new_native_actions','new_resets','new_worlds','new_seeds','HOLDOUT_queries','SEALED_queries','reserve_used']) and r['research_remaining']==22758 and r['reserve']==84000 and r['actual_baseline_s']==13.66 and r['no_lap_gain_observation']
checks['main_preserved']=subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31'
out=dict(passed=all(checks.values()),checks=checks,initial_rank_exempt_equals_baseline_mask=bool(np.array_equal(e0,base_mask)),reconstructed_exemption_membership_changes=int(sum(e0!=e1)),reconstructed_exempt_baseline_unclipped=int(sum(e1&~base_mask)),cost=cost,audit_source_ticks=0,audit_force_calls=0,audit_geometry_calls=0,audit_CPU_s=time.process_time()-cpu,audit_wall_s=time.perf_counter()-wall)
from retry.clip561_core import atomic_write,plain
atomic_write(G/'retry/mode561_audit.json',out);print(json.dumps(plain(out),indent=2));raise SystemExit(0 if out['passed'] else 1)
