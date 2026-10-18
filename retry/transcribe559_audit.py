"""Recompute559 records, LP prediction and common-space gates; no new physics."""
import json,math,subprocess,time
from pathlib import Path
import numpy as np
from retry.period556_model import rd,sha
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response559-private');cpu,wall=time.process_time(),time.perf_counter()
c=rd(G/'retry/transcribe559_contract.json');r=rd(G/'retry/transcribe559_result.json');s=rd(D/'selected-segment-private.json');base=rd(D/'baseline-private.json');cand=rd(D/'candidate-private.json');direction=rd(D/'direction-private.json');source=rd(Path('/workspace/haic-response551-private/cold-candidate-private.json'));rows=[x for x in source['trace'] if s['entry_action']<=x['index']<s['entry_action']+9];checks={}
checks['source_inputs_segment_pinned']=all(sha(G/p)==h for p,h in c['source_sha256'].items()) and all(sha(Path(p))==h for p,h in c['private_inputs_sha256'].items()) and sha(D/'selected-segment-private.json')==c['segment_sha256']
checks['started_pin']=rd(D/'STARTED.json')['contract_sha256']==sha(G/'retry/transcribe559_contract.json')
path=rd(Path('/workspace/haic-response551-private/frozen-paths-private.json'))['candidate'];trace=source['trace'];j=next(i for i,x in enumerate(trace) if i and x['index']>24 and x['raw']==1 and trace[i-1]['progress']>=path['arcs'][37])
checks['predeclared_first_crossing_selection']=trace[j]['index']==s['entry_action']==35 and s['initial']==trace[j-1]['root_without_roads'] and rows==trace[j:j+36] and source['summary']['pass_safety']
past=[x for x in trace[:j] if x['index']>24];checks['true_tracking_history']=s['history']==[sum(f['clipped'] for x in past for f in x['forces']),4*len(past)]==[3,160]
checks['independent_node_defects_exact']=all(rd(D/f'node-{i:02d}-private.json')['terminal_defect_exact_zero'] and all(x['fullstate_and_force_exact'] and x['root_without_roads']==rows[4*i+k]['root_without_roads'] and x['forces']==rows[4*i+k]['forces'] for k,x in enumerate(rd(D/f'node-{i:02d}-private.json')['rows'])) for i in range(9))
checks['sequential_fullstate_force_exact']=all(x['root_without_roads']==z['root_without_roads'] and x['forces']==z['forces'] for x,z in zip(base['rows'],rows)) and len(base['rows'])==36 and r['transcription']['exact_feasible']
previous=trace[j-1];checks['saved_world_safety_reproduced']=abs(base['min_margin']-min(previous['margin'],*(x['margin'] for x in rows)))<1e-12 and abs(base['max_path']-max(previous['path_error'],*(x['path_error'] for x in rows)))<1e-12
fd=[rd(D/f'FD-{i:02d}-private.json') for i in range(12)];steps=np.array(direction['FD_steps']);J=np.array([(np.array(x['g'])-base['g'])/steps[i] for i,x in enumerate(fd)]).T;T=np.array([(np.array([z['time'] for z in x['crossings']])-np.array([z['time'] for z in base['crossings']]))/steps[i] for i,x in enumerate(fd)]).T;delta=np.array(direction['delta']);pred=-1000*T@delta
checks['one_sensitivity_direction_one_candidate']=len(fd)==r['cost']['FD_rollouts']==12 and r['cost']['candidate_rollouts']==1 and direction['success'] and direction['status']==0 and len(list(D.glob('candidate-private.json')))==1
checks['LP_prediction_recomputed']=np.max(abs(pred-r['direction']['predicted_gain_ms']))<1e-10 and abs(float(min(J@delta+.5*np.array(base['g'])))-r['direction']['linear_min_slack'])<1e-12
checks['zero_direction_feasible']=min(base['g'])>=-1e-10 and direction['zero_direction_linear_feasible']
def crossing_times(data):
 states=[s['initial']]+[x['root_without_roads'] for x in data['rows']];out=[]
 for goal in s['gates']:
  signed=[sum((x['center'][k]-goal['point'][k])*goal['normal'][k] for k in range(2)) for x in states]
  i=next(i for i in range(1,len(states)) if signed[i-1]<0<=signed[i]);f=-signed[i-1]/(signed[i]-signed[i-1]);out.append(dict(time=.02*(i-1+f),raw_bracket=[.02*(i-1),.02*i]))
 return out
bt=crossing_times(base);ct=crossing_times(cand);gains=[1000*(a['time']-b['time']) for a,b in zip(bt,ct)]
checks['same_physical_plane_times_recomputed']=all(abs(a-b)<1e-12 for a,b in zip(gains,r['candidate_gain_ms'])) and [x['raw_bracket'] for x in ct]==r['candidate_raw_brackets'] and [x['time'] for x in bt]==[.48,.64]
checks['overlapping_raw_brackets_preserved']=all(a['raw_bracket']==b['raw_bracket'] for a,b in zip(bt,ct))
mask=[f['clipped'] for row in base['rows'] for f in row['forces']];newmask=[f['clipped'] for row in cand['rows'] for f in row['forces']]
checks['candidate_unchanged_global_safety']=cand['min_margin']>=.5 and cand['max_path']<=3 and cand['max_reference_overspeed']<=4.85 and cand['max_force']<=1.059 and cand['max_clip_fraction']<=.1 and r['candidate_stats']['max_body']<100
checks['no_new_clipping_and_gate_comparison']=all(not b or a for a,b in zip(mask,newmask)) and min(cand['g'])>=-1e-9 and r['candidate_comparison_pass'] and max(r['candidate_gate_position_errors_m'])<=.15
checks['effect_failure_not_transcription_failure']=r['transcription']['exact_feasible'] and r['candidate_physical_safe'] and min(gains)<5 and not r['improvement_gate_pass']
cost=r['cost'];checks['all_source_force_geometry_reconciled']=cost['node_ticks']==36 and cost['model_ticks']==36+36*(1+12+1)==540 and cost['explicit_wheel_force_evaluations']==cost['internal_wheel_force_evaluations']==4*540 and cost['geometry_checks']==37*14==518 and cost['body_checks']==540
checks['caps_and_domain']=cost['model_ticks']<=800 and cost['explicit_wheel_force_evaluations']<=4000 and cost['geometry_checks']<=700 and cost['CPU_s']<=90 and cost['wall_s']<=120 and cost['max_body_speed']<100
checks['native_protected_reserve_zero']=all(r[k]==0 for k in ['new_native_actions','new_resets','new_worlds','new_seeds','HOLDOUT_queries','SEALED_queries','reserve_used']) and r['research_remaining']==22758 and r['reserve']==84000 and r['actual_baseline_s']==13.66 and r['no_lap_gain_observation']
checks['main_preserved']=subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31'
out=dict(passed=all(checks.values()),checks=checks,predicted_gain_ms=pred.tolist(),observed_interpolated_gain_ms=gains,prediction_error_ms=(np.array(gains)-pred).tolist(),baseline_crossings=bt,candidate_crossings=ct,scientific_cost=cost,audit_source_ticks=0,audit_force_evaluations=0,audit_geometry_evaluations=0,audit_CPU_s=time.process_time()-cpu,audit_wall_s=time.perf_counter()-wall)
with (G/'retry/transcribe559_audit.json').open('x') as f:json.dump(out,f,indent=2,allow_nan=False)
print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed'] else 1)
