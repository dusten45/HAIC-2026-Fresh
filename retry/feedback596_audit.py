"""Read saved596 evidence only: no simulation, force or geometry imports/calls."""
import time
CPU=time.process_time();WALL=time.perf_counter()
import hashlib,json,math
from pathlib import Path
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response596-private')
rd=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def run():
 r=rd(G/'retry/feedback596_result.json');c=rd(G/'retry/feedback596_contract.json');rows=rd(D/'applied-rows-private.json');trials=rd(D/'trials-private.json');choices=rd(D/'choices-private.json');initial=rd(D/'initial-checkpoint-private.json');final=rd(D/'final-checkpoint-private.json');n=r['counts'];checks={}
 head='0'*64;events=0;kinds={};extbefore=completed=0
 for line in (D/'journal-private.jsonl').open():
  q=json.loads(line);h=q.pop('sha256');assert q['previous']==head and q['sequence']==events and digest(q)==h,'JOURNAL_CHAIN';head=h;events+=1;kinds[q['kind']]=kinds.get(q['kind'],0)+1
 checks['chain_valid']=head==r['journal']['head'] and events==r['journal']['events']
 checks['pins_inputs']=all(sha(Path(p))==r['input_sha256'][k] for k,p in dict(checkpoint='/workspace/haic-response595-private/checkpoint-private.json',static='/workspace/haic-response515-private/collected-map-state-private.json',paths='/workspace/haic-response551-private/frozen-paths-private.json',ledger='/workspace/haic-response519-private/model-ledger-private.json',tape='/workspace/haic-response577-private/final-independent-tape-private.json',fixed595='/workspace/haic-response595-private/diagnostic-rows-private.json',gate=str(G/'retry/cause595_checkpoint_gate.json'),previous=str(G/'retry/cause595_result.json'),proposal=str(G/'retry/cause595_next_proposal.json')).items())
 checks['code_runtime_pins']=all(sha(Path(p) if Path(p).is_absolute() else G/p)==h for p,h in {**c['implementation_sha256'],**c['dependency_sha256']}.items())
 checks['private_artifacts_pinned']=all(sha(D/p)==h for p,h in r['private_sha256'].items())
 checks['tests_before_source']=rd(G/'retry/feedback596_tests.json')['passed'] and sha(G/'retry/feedback596_tests.json')==c['tests_sha256']
 checks['original537_summary_exact']=r['all_passive537_summaries_exact'] and all(q['passive_summaries_exact'] and q['actual_checkpoint_unchanged'] for q in choices)
 keys=['ok','reason','peak','max_reference_overspeed','clipped','samples','model_ticks','min_footprint_margin_m'];offset=0
 for q in choices:
  detail=q['detail'];old=detail['trials']+[z for z in detail.get('reports',[]) if z['mode']=='FINAL'] if 'trials' in detail else detail.get('reports',[]);new=trials[offset:offset+len(old)];assert len(new)==len(old)
  for a,b in zip(old,new):assert all(a[k]==b['summary'][k] for k in keys),'SUMMARY'
  offset+=len(old)
 checks['all_trial_summaries_stored_exact']=offset==len(trials)
 attempts=sum(t['summary']['attempts'] for t in trials);ticks=sum(t['summary']['model_ticks'] for t in trials);raw=[q for q in rows if q.get('tick_executed')]
 checks['full_attempt_completion_accounting']=n.get('model_attempted',0)==attempts+len(rows) and n.get('model_completed',0)==ticks+len(raw)==n.get('body_checks',0)
 checks['both_force_oracles_accounted']=n.get('external_force',0)==4*n.get('model_attempted',0) and n.get('internal_force',0)==4*n.get('model_completed',0) and n.get('total_force',0)==n.get('external_force',0)+n.get('internal_force',0)
 checks['journal_primitive_counts']=kinds.get('BEFORE_FORCE',0)==n.get('model_attempted',0) and kinds.get('AFTER_TICK',0)==n.get('model_completed',0)
 backup=sum(max(0,(t['summary']['attempts']-1)//4) for t in trials);expected_geometry=2+len(trials)+2*ticks+6*len(choices)+4*backup+2*len(raw)
 checks['all_geometry_including_internal_nominal']=n['geometry']==expected_geometry and n.get('internal_nominal_steering_projection',0)==6*len(choices)+4*backup
 checks['original537_cost_matches']=r['original537_cost']['forecast_calls']==len(trials) and r['original537_cost']['forecast_ticks']==ticks and r['original537_cost']['force_evaluations']==4*(attempts+len(rows)) and r['original537_cost']['geometry_checks']==len(trials)+ticks
 safe=True;fresh=True;split=True;history=initial['tracking'].copy()
 byhold={}
 for t in trials:byhold.setdefault(t['hold'],[]).append(t)
 for q in rows:
  forces=q['forces'];proposed=[history[0]+sum(f['ratio']>1 for f in forces),history[1]+4]
  safe &= proposed==q['proposed_history'] and q['tracking_history_before']==history and max(f['ratio'] for f in forces)<=1.059 and proposed[0]/proposed[1]<=.1 and all(f['clipped']==(f['ratio']>1) for f in forces)
  if q.get('tick_executed'):
   safe &= q['margin']>=.5 and q['path_error']<=3 and q['reference_overspeed']<=4.85 and -.5<=q['progress_delta']<=q['projection_limit'] and q['body']<100 and not q['all_failures']
   t=byhold[q['index']][-1];z=t['rows'][q['raw']-1];fresh &= t['summary']['ok'] and digest(q['root_without_roads'])==z['root_sha256'] and q['forces']==z['forces'] and proposed==z['history']
   flags=dict(FOOTPRINT=q['margin']<.5,REFERENCE=q['reference_overspeed']>4.85,PATH=q['path_error']>3,PROJECTION_BACKWARD=q['progress_delta']<-.5,PROJECTION_FORWARD=q['progress_delta']>q['projection_limit']);split &= flags==q['split_flags'];history=proposed
 checks['applied_safety_or_recorded_terminal_failure']=safe or (r['status']=='APPLIED_STRICT_FAILURE' and r['failure'] is not None and bool(rows[-1].get('pre_failure') or rows[-1].get('post_failure')))
 checks['fresh_FINAL_first4_exact']=fresh and (r['fresh_FINAL_applied_exact'] if raw else True)
 checks['applied_split_telemetry']=split
 checks['actual_histories_preserved']=final['tracking']==history and initial['tracking']==[15,240] and final['launch']==initial['launch']
 checks['declared_local_scope_and_first_stop']=(len(raw)==48 and r['status']=='LOCAL48_STRICT_SAFE_PROGRESS' and final['global_raw']==204 and len(choices)==12 and r['progress_gain']>0) or (r['status']=='NO_ADMISSIBLE_ACTION' and choices[-1]['action'] is None and r['failure']['hold']==choices[-1]['hold'] and len(raw)==4*(len(choices)-1)) or (r['status']=='APPLIED_STRICT_FAILURE' and bool(rows[-1].get('pre_failure') or rows[-1].get('post_failure')))
 checks['no_extra_applied_raw']=len(raw)<=48 and final['global_raw']==156+len(raw)
 checks['caps']=all(n.get(k,0)<=v for k,v in c['caps'].items()) and all(r['times'][k]<=v for k,v in c['time_caps'].items())
 checks['native_holdout_sealed_zero']=all(r[k]==0 for k in ['native','worlds','resets','actions','HOLDOUT','SEALED'])
 checks['ledger_reserve_preserved']=r['research_remaining']==22548 and r['reserve']==84000 and r['reserve_used']==0
 checks['no_unearned_promotion']=not any(r[k] for k in ['whole_finish_claim','native_gain_claim','carry_claim','incumbent_promotion','subsequent_experiment_executed'])
 out=dict(study=596,status='READ_ONLY_AUDIT_PASS' if all(checks.values()) else 'READ_ONLY_AUDIT_FAILURE',checks=checks,geometry_expected=expected_geometry,events=events,source_ticks=0,force_calls=0,geometry_queries=0,native_calls=0,input_sha256=dict(result=sha(G/'retry/feedback596_result.json'),contract=sha(G/'retry/feedback596_contract.json'),audit_code=sha(Path(__file__))),CPU_s=time.process_time()-CPU,wall_s=time.perf_counter()-WALL)
 # Extra2secondsconservativechargecoversaggregation and result/report extraction; actualauditmeasuredabove.
 out['auxiliary_CPU_wall_charge_s']=2.;out['aggregate_time']={k:r['times'][k]+(out['CPU_s']+2 if k in ['preparation_audit_CPU_s','total_CPU_s'] else out['wall_s']+2 if k in ['preparation_audit_wall_s','total_wall_s'] else 0) for k in r['times']};out['checks']['aggregate_time_caps']=all(out['aggregate_time'][k]<=v for k,v in c['time_caps'].items());out['status']='READ_ONLY_AUDIT_PASS' if all(out['checks'].values()) else 'READ_ONLY_AUDIT_FAILURE'
 target=G/'retry/feedback596_audit.json'
 with target.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()
