"""Saved598 evidence audit only; native/model/force/geometry calls forbidden by design."""
import time
CPU=time.process_time();WALL=time.perf_counter()
import hashlib,json,subprocess
from pathlib import Path
from collections import Counter
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response598-private')
rd=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def run():
 r=rd(G/'retry/cold598_result.json');c=rd(G/'retry/cold598_contract.json');n=r['cost'];checks={};events=0;head='0'*64;kinds=Counter();armkinds={};actions=[];native_rows={};models=0;ticks=0;geomparts=Counter();prefix_started=0;anchor_trials=0;geometry_failure_rows=[]
 for line in (D/'journal-private.jsonl').open():
  q=json.loads(line);h=q.pop('sha256');assert q['sequence']==events and q['previous']==head and digest(q)==h,'CHAIN';head=h;events+=1;kinds[q['kind']]+=1;label=q.get('label');armkinds.setdefault(label,Counter())[q['kind']]+=1
  if q['kind']=='ACTION_CHARGED':actions.append((label,q['index'],q['payload_bits'],q['research_remaining']));assert q['research_remaining']==22548-len(actions)
  if q['kind']=='AFTER_NATIVE_RAW':native_rows.setdefault(q['record']['label'],[]).append(q['record'])
  if q['kind']=='PREFIX_FORECAST_RAW' and q['row'].get('first_failure'):geometry_failure_rows.append(q['row'])
 checks['journal_chain_exact']=head==r['journal']['head'] and events==r['journal']['events'] and r['journal']['valid']
 checks['private_files_pinned']=all(sha(D/p)==h for p,h in r['private_sha256'].items())
 inputs=dict(tape=Path('/workspace/haic-response577-private/final-independent-tape-private.json'),case=Path('/workspace/haic-response541-private/approved-case-private.json'),baseline_paths=Path('/workspace/haic-response541-private/frozen-paths-private.json'),candidate_paths=Path('/workspace/haic-response551-private/frozen-paths-private.json'),static=Path('/workspace/haic-response515-private/collected-map-state-private.json'),ledger=Path('/workspace/haic-response519-private/model-ledger-private.json'),baseline_contract=G/'retry/joint541_contract.json',carry_failure=G/'retry/carry592_result.json',source597_contract=G/'retry/cold597_contract.json',source597_audit=G/'retry/cold597_audit.json',proposal=G/'retry/cold597_next_review.json');inputs.update({f'old{x}':G/f'retry/{name}_result.json' for x,name in [(593,'cold593'),(594,'cold594'),(595,'cause595'),(596,'feedback596'),(597,'cold597')]})
 checks['input_and_old_result_pins']=all(sha(p)==c['input_sha256'][k] for k,p in inputs.items())
 checks['code_runtime_pins']=all(sha(Path(p) if Path(p).is_absolute() else G/p)==h for p,h in {**c['implementation_sha256'],**c['dependency_sha256']}.items())
 checks['tests_frozen_before_worlds']=rd(G/'retry/cold598_tests.json')['passed'] and sha(G/'retry/cold598_tests.json')==c['tests_sha256']
 checks['world_reset_reserved_vs_called']=n.get('worlds',0)==kinds['WORLD_CHARGED'] and n.get('resets',0)==kinds['RESET_CHARGED'] and n.get('world_constructor_calls',0)<=n.get('worlds',0) and n.get('reset_calls',0)<=n.get('resets',0)
 checks['raw_reserved_called_completed']=kinds['BEFORE_NATIVE_RAW']==n.get('raw_attempts',0) and kinds['AFTER_NATIVE_RAW']==n.get('raw_completed',0) and n.get('raw_completed',0)<=n.get('native_raw_calls',0)<=n.get('raw_attempts',0)
 checks['native_wheel_separate']=n.get('native_wheel_reserved',0)==4*n.get('raw_attempts',0) and n.get('native_wheel_observed',0)==4*n.get('raw_completed',0)
 checks['model_attempt_completed']=kinds['BEFORE_MODEL_FORCE']==n.get('model_attempted',0) and kinds['AFTER_MODEL_TICK']==n.get('model_completed',0)==n.get('model_tick_attempts',0)
 checks['force_all_oracles']=n.get('external_force',0)==4*n.get('model_attempted',0)+4*n.get('native_oracle_groups',0) and n.get('internal_force',0)==4*n.get('model_completed',0) and n.get('total_force',0)==n.get('external_force',0)+n.get('internal_force',0)
 checks['all_geometry_including_internal']=n.get('geometry',0)==sum(v for k,v in n.items() if k.startswith('geometry_'))+n.get('raw_completed',0)
 trials=rd(D/'tracking-trial-summaries-private.json');keys=['ok','reason','peak','max_reference_overspeed','clipped','samples','model_ticks','min_footprint_margin_m'];checks['passive537_summary_exact']=len(trials)==r['tracking_trial_summaries'] and all(t['exact'] and all(t['original'][k]==t['summary'][k] for k in keys) for t in trials) and r['all_tracking_passive_summaries_exact']
 checks['action_ledger_no_refunds']=len(actions)==n.get('actions',0)==kinds['ACTION_CHARGED'] and n.get('action_calls',0)<=n.get('actions',0) and r['research_remaining']==22548-n.get('actions',0) and r['reserve']==84000 and r['reserve_used']==0
 checks['caps']=all(n.get(k,0)<=v for k,v in c['caps'].items()) and all(r['time'][k]<=v for k,v in c['time_caps'].items())
 checks['finally_all_closed_body_joint0']=n.get('closed',0)==n.get('world_constructor_calls',0) and all(a['cleanup']==dict(body=0,joint=0) for a in r['arms'])
 checks['baseline_before_candidate']=len(r['arms'])<=1 or (r['arms'][0]['label']=='baseline' and r['arms'][0]['stop']=='OFFICIAL_FINISH' and r['arms'][0]['official_finish_raw']==683 and r['arms'][0]['counts']['raw_completed']-51==683 and r['arms'][0]['initial_identity'] and not r['arms'][0]['flags'] and r['arms'][0]['error'] is None)
 prefix=json.loads((D/'frozen-prefix-command-bytes-private.json').read_text());checks['actual_candidate_prefix_bytes']=all(bits==prefix[str(h)] for label,h,bits,credit in actions if label=='candidate' and h<=39)
 checks['no_candidate_fixed_tape_after39']='self.commands[i+1]' not in (G/'retry/cold598_native.py').read_text() and 'self.candidate_select(root,path,st,i,raw,skin)' in (G/'retry/cold598_native.py').read_text()
 checks['actual_candidate_feedback_dispatch_count']=n.get('actual_feedback_choosers',0)>=len([1 for label,h,bits,credit in actions if label=='candidate' and h>=40])
 checks['at_most11_future_transition_anchors']=n.get('transition_anchor_choosers',0)<=11
 checks['native_detailed_geometry_flags']=all(q['native_geometry_flags']==dict(FOOTPRINT=q['margin']<.25,PATH=q['path_error']>3,PROJECTION_BACKWARD=q['projection_delta']<q['projection_lower'],PROJECTION_FORWARD=q['projection_delta']>q['projection_upper']) for rows in native_rows.values() for q in rows)
 checks['actual_native_safety_or_first_recorded_failure']=all(not any(q['errors'] for q in rows[:-1]) for rows in native_rows.values()) and all(not a['flags'] for a in r['arms'] if a['stop']=='OFFICIAL_FINISH')
 gain=683-r['arms'][1]['official_finish_raw'] if len(r['arms'])==2 and r['arms'][1]['stop']=='OFFICIAL_FINISH' else None;checks['integer_gain_only']=r['cold_native_gain_raw']==gain and r['cold_native_gain_s']==(gain*.02 if gain is not None else None)
 checks['carry_combined_general_closed']=not r['combined_promotion'] and not r['general_policy_promotion'] and not r['incumbents_changed'] and all(r[k]==0 for k in ['carry_actions','new_conditions','HOLDOUT','SEALED','new_profiles','new_FD','new_solver','paid_compute'])
 checks['main_Participants_preserved']=subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31' and not subprocess.check_output(['git','diff','--name-only','main','--','Participants'],cwd=G,text=True).strip()
 ac=time.process_time()-CPU;aw=time.perf_counter()-WALL;aggregate={k:v+(ac+5 if k in ['preparation_audit_CPU_s','total_CPU_s'] else aw+5 if k in ['preparation_audit_wall_s','total_wall_s'] else 0) for k,v in r['time'].items()};checks['prep_execution_total_time_caps']=all(aggregate[k]<=v for k,v in c['time_caps'].items())
 out=dict(study=598,status='READ_ONLY_AUDIT_PASS' if all(checks.values()) else 'READ_ONLY_AUDIT_FAILURE',checks=checks,events=events,CPU_s=ac,wall_s=aw,auxiliary_CPU_wall_charge_s=5,aggregate_time=aggregate,source_ticks=0,native_calls=0,force_calls=0,geometry_queries=0,input_sha256=dict(result=sha(G/'retry/cold598_result.json'),contract=sha(G/'retry/cold598_contract.json'),audit=sha(Path(__file__))))
 with (G/'retry/cold598_audit.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()
