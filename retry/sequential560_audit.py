"""Read-only scientific audit with explicit unrecoverable main-CPU coverage gap."""
import json,math,subprocess,time
from pathlib import Path
import numpy as np
from retry.period556_model import rd,sha
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response560-private');cpu,wall=time.process_time(),time.perf_counter()
c=rd(G/'retry/sequential560_contract.json');summary=rd(G/'retry/sequential560_summary.json');failed=rd(D/'failure-private.json');segment=rd(D/'segment-private.json');base=rd(D/'baseline-private.json');final=rd(D/'final-repaired-private.json');records=summary['trials'];trials=[rd(D/f'trial-00-{i:02d}-private.json') for i in range(3)];fd=[rd(D/f'FD-00-{i:02d}-private.json') for i in range(40)];checks={}
checks['original_source_inputs_segment_pinned']=all(sha(G/p)==h for p,h in c['source_sha256'].items()) and all(sha(Path(p))==h for p,h in c['private_inputs_sha256'].items()) and sha(D/'segment-private.json')==c['segment_sha256']
checks['all_started_contract_pins']=all(rd(D/fn)['contract_sha256']==sha(G/cn) for fn,cn in [('STARTED.json','retry/sequential560_contract.json'),('recovery-STARTED.json','retry/sequential560_recovery_contract.json'),('finalization-STARTED.json','retry/sequential560_finalization_contract.json')])
checks['recovery_sources_pinned']=all(all(sha(G/p)==h for p,h in rd(G/cn)['source_sha256'].items()) for cn in ['retry/sequential560_recovery_contract.json','retry/sequential560_finalization_contract.json'])
checks['thirtythree_node_exact_transcription']=all(all(r['exact'] for r in rd(D/f'node-{i:02d}-private.json')['rows']) for i in range(33)) and failed['cost']['node_ticks']==132
source=rd(Path('/workspace/haic-response551-private/cold-candidate-private.json'));expected=[r for r in source['trace'] if 35<=r['index']<=67]
checks['baseline_fullworld_contacts_forces_exact']=len(expected)==132 and all(a['root_without_roads']==b['root_without_roads'] and a['forces']==b['forces'] for a,b in zip(base['rows'],expected)) and segment['history']==[3,160]
checks['fixed_window_and_follow']=segment['entry_action']==35 and segment['optimized_holds']==20 and segment['follow_holds']==12 and segment['measurement_buffer_holds']==1 and len(segment['commands'])==33
x=np.array(base['x']);times=lambda v:np.array([g['time'] for g in v['crossings']]);steps=[f['x'][i]-x[i] for i,f in enumerate(fd)];T=np.array([(times(f)-times(base))/steps[i] for i,f in enumerate(fd)]).T;J=np.array([(np.array(f['g'])-base['g'])/steps[i] for i,f in enumerate(fd)]).T
checks['predictions_actuals_reconstructed']=all(np.max(abs(-1000*T@(np.array(t['x'])-x)-rec['predicted_gain_ms']))<1e-10 and np.max(abs(1000*(times(base)-times(t))-rec['actual_gain_ms']))<1e-10 for t,rec in zip(trials,records))
linear=[];prefix=[]
for label,v in [('baseline',base),*[(f'trial{i}',t) for i,t in enumerate(trials)]]:
 clips,samples=segment['history'];peak=(clips/samples,0,clips,samples)
 for i,row in enumerate(v['rows']):
  clips+=sum(f['clipped'] for f in row['forces']);samples+=4
  if clips/samples>peak[0]:peak=(clips/samples,i+1,clips,samples)
 prefix.append(dict(label=label,max_fraction=peak[0],peak_raw=peak[1],clips_at_peak=peak[2],samples_at_peak=peak[3],final_fraction=clips/samples))
 if label!='baseline':
  delta=np.array(v['x'])-x;predg=np.array(base['g'])+J@delta;linear.append(dict(label=label,minimum_predicted_constraint=float(min(predg)),minimum_actual_constraint=float(min(v['g'])),predicted_clip_min=float(min(g for g,n in zip(predg,v['labels']) if n=='clip')),actual_clip_min=float(min(g for g,n in zip(v['g'],v['labels']) if n=='clip'))))
checks['all_rejections_independently_unsafe']=all(not t['physical_safe'] and not t['feasible'] and p['max_fraction']>.1 for t,p in zip(trials,prefix[1:]))
checks['recovery_rule_three_halved_trials']=summary['scientific_stop_reason']=='THREE_REJECTED_TRIALS' and [t['radius'] for t in records]==[1.,.5,.25] and all(not t['accepted'] and t['incumbent_preserved_on_reject'] for t in records) and failed['cost']['direction_attempts']==1 and failed['cost']['LP_solves']==3
checks['zero_acceptance_immutable_incumbent']=len(list(D.glob('incumbent-*-private.json')))==1 and rd(D/'incumbent-00-private.json')['evaluation_sha256']==sha(D/'baseline-private.json') and summary['accepted_count']==0 and summary['cumulative_gain_ms']==[0.,0.]
checks['no_yaw_mask_periodic_admissibility']=not any(n in {'yaw','no_new_clip','periodic'} for n in base['labels']) and all(t['branch_changes']['new_clipped_samples']>0 and t['branch_changes']['contact_raw_changes']>0 for t in records)
checks['final_fresh_replay_fullstate_force_exact']=len(final['rows'])==132 and all(r['exact_baseline_match'] and r['root_without_roads']==b['root_without_roads'] and r['forces']==b['forces'] for r,b in zip(final['rows'],base['rows'])) and final['exact'] and final['safe'] and summary['final_fresh_replay_exact']
checks['final_global_safety']=summary['final_stats']['min_margin']>=.5 and summary['final_stats']['max_path']<=3 and summary['final_stats']['max_reference_overspeed']<=4.85 and summary['final_stats']['max_force']<=1.059 and summary['final_stats']['max_clip_fraction']<=.1 and summary['final_stats']['max_body']<100
states=[segment['initial']]+[r['root_without_roads'] for r in final['rows']];arrivals=[]
for g in segment['gates']:
 signed=[sum((s['center'][k]-g['point'][k])*g['normal'][k] for k in range(2)) for s in states];i=next(i for i in range(1,len(states)) if signed[i-1]<0<=signed[i]);f=-signed[i-1]/(signed[i]-signed[i-1]);arrivals.append(.02*(i-1+f))
checks['final_same_space_time_and_follow']=arrivals==summary['final_times_s']==[1.6,2.56] and states[80]==base['rows'][79]['root_without_roads'] and states[128]==base['rows'][127]['root_without_roads']
cost=summary['cost'];checks['all_model_force_geometry_reconciled']=cost['main_model_ticks']==132+132*(1+40+3)==5940 and cost['model_ticks']==5940+132+132==6204 and cost['explicit_wheel_force_evaluations']==cost['internal_wheel_force_evaluations']==4*6204 and cost['geometry_checks']==133*(1+40+3)+133==5985 and cost['body_checks']==6204
checks['original_work_caps_and_recovery_caps']=cost['model_ticks']<=36000 and cost['explicit_wheel_force_evaluations']<=150000 and cost['geometry_checks']<=36000 and cost['first_recovery']['CPU_s']<=10 and cost['first_recovery']['wall_s']<=20 and cost['finalization']['CPU_s']<=10 and cost['finalization']['wall_s']<=20
checks['both_failures_preserved']=failed['error']=='TypeError:Object of type int64 is not JSON serializable' and rd(G/'retry/sequential560_result.json')['recovery_error']=='RuntimeError:RECOVERY_WORK_CAP' and (D/'recovery-error-private.json').exists()
checks['CPU_gap_explicit_not_fabricated']=cost['main_measured_CPU_s'] is None and cost['aggregate_measured_CPU_s'] is None and cost['aggregate_CPU600_independently_verified'] is False
checks['no_native_protected_reserve']=all(summary[k]==0 for k in ['new_native_actions','new_resets','new_worlds','new_seeds','HOLDOUT_queries','SEALED_queries','reserve_used']) and summary['research_remaining']==22758 and summary['reserve']==84000 and summary['actual_baseline_s']==13.66 and summary['no_lap_gain_observation']
checks['main_preserved']=subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31'
out=dict(scientific_evidence_audit_passed=all(checks.values()),checks=checks,prefix_clipping=prefix,linearized_versus_actual_constraints=linear,scientific_cost=cost,all_requested_accounting_complete=False,limitation='Original main CPU and perf-wall measurements lost to serialization error; aggregateCPU600 independently unverified. Recovery CPU/wall and all work counts recorded. Wall timestamp estimate is not measured CPU.',audit_source_ticks=0,audit_force_evaluations=0,audit_geometry_evaluations=0,audit_CPU_s=time.process_time()-cpu,audit_wall_s=time.perf_counter()-wall)
with (G/'retry/sequential560_audit.json').open('x') as f:json.dump(out,f,indent=2,allow_nan=False)
print(json.dumps(dict(scientific_evidence_audit_passed=out['scientific_evidence_audit_passed'],checks=checks,prefix_clipping=prefix,linearized_versus_actual_constraints=linear,all_requested_accounting_complete=False),indent=2));raise SystemExit(0 if all(checks.values()) else 1)
