"""Audit only saved597 bytes and arithmetic; no simulator or geometry calls."""
import time
CPU=time.process_time();WALL=time.perf_counter()
import hashlib,json,math,subprocess
from collections import Counter
from pathlib import Path
from retry.cold597_core import official_raw,MAX_APPLIED,WARMUP,TIME_LIMIT
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response597-private')
rd=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def run():
 r=rd(G/'retry/cold597_result.json');c=rd(G/'retry/cold597_contract.json');rows=rd(D/'applied-rows-private.json');replay=rd(D/'replay-rows-private.json');trials=rd(D/'trials-private.json');choices=rd(D/'choices-private.json');n=r['counts'];checks={};head='0'*64;events=0;kinds=Counter();journal_completed=0;mode_attempts=Counter();mode_completed=Counter();phase='preparation';phase_primitives={};last_event=None
 for line in (D/'journal-private.jsonl').open():
  q=json.loads(line);h=q.pop('sha256');assert q['previous']==head and q['sequence']==events and digest(q)==h,'JOURNAL_CHAIN';head=h;events+=1;kinds[q['kind']]+=1
  if q['kind']=='PHASE_START':phase=q['phase']
  if q['kind']=='BEFORE_FORCE':mode_attempts[phase]+=1
  if q['kind']=='AFTER_TICK':mode_completed[phase]+=1
  last_event=q
 checks['chain_valid_and_closed']=last_event['kind']=='STUDY_END' and last_event['status']==r['status']
 checks['all_private_artifacts_pinned']=all(sha(D/p)==h for p,h in r['private_sha256'].items())
 inputs=dict(static='/workspace/haic-response515-private/collected-map-state-private.json',paths='/workspace/haic-response551-private/frozen-paths-private.json',ledger='/workspace/haic-response519-private/model-ledger-private.json',tape='/workspace/haic-response577-private/final-independent-tape-private.json',case='/workspace/haic-response541-private/approved-case-private.json',source541=str(G/'retry/joint541_cold_result.json'),source577=str(G/'retry/direct577_result.json'),previous=str(G/'retry/feedback596_result.json'),previous_audit=str(G/'retry/feedback596_audit.json'),proposal=str(G/'retry/feedback596_next_proposal.json'),old593=str(G/'retry/cold593_result.json'),old594=str(G/'retry/cold594_result.json'),old595=str(G/'retry/cause595_result.json'))
 checks['inputs_and_old_results_preserved']=all(sha(Path(p))==h for k,p in inputs.items() for h in [c['input_sha256'][k]])
 checks['code_runtime_pins']=all(sha(Path(p) if Path(p).is_absolute() else G/p)==h for p,h in {**c['implementation_sha256'],**c['dependency_sha256']}.items())
 checks['pure_tests_frozen']=rd(G/'retry/cold597_tests.json')['passed'] and sha(G/'retry/cold597_tests.json')==c['tests_sha256']
 checks['timelimit_warmup_unchanged']=c['time_limit']['approved_case_max_elapsed_steps']==1224 and c['time_limit']['warmup_TimeLimit_steps']==50 and c['time_limit']['reset_internal_step_counted_by_TimeLimit']==0 and c['time_limit']['max_policy_applied_raw']==1174
 checks['primitive_journal_counts']=kinds['BEFORE_FORCE']==n.get('model_attempted',0) and kinds['AFTER_TICK']==n.get('model_completed',0) and sum(mode_attempts.values())==sum(v.get('model_attempted',0) for v in r['phase_counts'].values())
 checks['both_force_oracles_charged']=n.get('external_force',0)==4*n.get('model_attempted',0) and n.get('internal_force',0)==4*n.get('model_completed',0) and n.get('total_force',0)==n.get('external_force',0)+n.get('internal_force',0)
 checks['phase_accounting']=all(mode_attempts[p]==v.get('model_attempted',0) and mode_completed[p]==v.get('model_completed',0) for p,v in r['phase_counts'].items() if p in ['main','replay'])
 raw=[q for q in rows if q.get('tick_executed')];ar=[q for q in replay if q.get('tick_executed')];partial=rd(D/'partial-trial-private.json') if (D/'partial-trial-private.json').exists() else None;alltrials=trials+([partial] if partial else [])
 attempts=sum(t['summary']['attempts'] for t in alltrials);ticks=sum(t['summary']['model_ticks'] for t in alltrials)
 checks['all_forecast_prefix_replay_work_charged']=n.get('model_attempted',0)==attempts+len(rows)+len(replay) and n.get('model_completed',0)==ticks+len(raw)+len(ar)
 offset=0;exact=True;keys=['ok','reason','peak','max_reference_overspeed','clipped','samples','model_ticks','min_footprint_margin_m'];byhold={}
 for t in trials:byhold.setdefault(t['hold'],[]).append(t)
 for q in choices:
  detail=q['detail'];old=detail['trials']+[z for z in detail.get('reports',[]) if z['mode']=='FINAL'] if 'trials' in detail else detail.get('reports',[]);new=trials[offset:offset+len(old)];exact &= len(new)==len(old) and all(a[k]==b['summary'][k] for a,b in zip(old,new) for k in keys);offset+=len(old)
 checks['original537_all_completed_summaries_exact']=exact and offset==len(trials) and r['passive537_summaries_exact'] and r['chooser_actual_checkpoints_unchanged']
 initial_queries=2+(2 if (D/'REPLAY_STARTED-private.json').exists() else 0);backup=sum(max(0,(t['summary']['attempts']-1)//4) for t in alltrials);geom=initial_queries+len(alltrials)+2*ticks+6*n.get('chooser_calls',0)+4*backup+2*(len(raw)+len(ar))
 checks['all_geometry_including_internal_nominal']=n['geometry']==geom and n.get('internal_nominal_steering_projection',0)==6*n.get('chooser_calls',0)+4*backup
 checks['original537_cost_matches']=r['original537_cost']['forecast_calls']==len(alltrials) and r['original537_cost']['forecast_ticks']==ticks and r['original537_cost']['force_evaluations']==4*(attempts+len(rows)+len(replay)) and r['original537_cost']['geometry_checks']==len(alltrials)+ticks
 safe=True;firstfailure=None;finalexact=True;prefix_exact=True;old577=rd(Path(inputs['tape']));visited=set(rd(Path(inputs['ledger']))['initial_visited']);initial=rd(D/'initial-checkpoint-private.json');history={'launch':[0,0],'tracking':[0,0]}
 prefix_keys=['before_root_without_roads','root_without_roads','forces','proposed_history','tracker','episode_before_s','episode_after_s','global_raw_before','global_raw_after','tracking_history_before','launch_history_before','visited_count','progress','margin','path_error','reference_overspeed','body']
 for i,q in enumerate(rows):
  group='launch' if q['index']<=24 else 'tracking';forces=q['forces'];before=history[group];proposed=[before[0]+sum(f['ratio']>1 for f in forces),before[1]+4];peak=max(f['ratio'] for f in forces);prefail='FORCE' if peak>(2.5 if group=='launch' else 1.059) else 'CLIP_HISTORY' if (group=='tracking' or q['index']>=24) and proposed[0]/proposed[1]>(.15 if group=='launch' else .1) else None
  safe &= q['proposed_history']==proposed and q['pre_failure']==prefail and q['tracking_history_before']==history['tracking'] and q['launch_history_before']==history['launch'] and all(bool(f['clipped'])==(f['ratio']>1) for f in forces)
  fail=prefail
  if q.get('tick_executed'):
   reasons=[]
   for bad,label in [(q['margin']<.5,'FOOTPRINT'),(q['path_error']>3,'PATH'),(group=='tracking' and q['reference_overspeed']>4.85,'REFERENCE'),(q['progress_delta']<-.5 or q['progress_delta']>q['projection_limit'],'PROJECTION')]:
    if bad:reasons.append(label)
   safe &= q['all_failures']==reasons and q['post_failure']==(reasons[0] if reasons else None) and q['body']<100;fail=fail or (reasons[0] if reasons else None);history[group]=proposed
   if q['index']<=39:
    old=old577['rows'][i]
    for ids in old['root_without_roads']['current_contacts']:visited.update(ids)
    prefix_exact &= all(q[k]==old[k] for k in prefix_keys) and q['visited']==sorted(visited)
   else:
    t=byhold[q['index']][-1];z=t['rows'][q['raw']-1];finalexact &= t['summary']['ok'] and q.get('fresh_FINAL_exact',False) and digest(q['root_without_roads'])==z['root_sha256'] and q['forces']==z['forces'] and proposed==z['history']
  if fail:firstfailure=dict(row=i,reason=fail);safe &= i==len(rows)-1
 checks['applied_gates_histories_and_first_stop_exact']=safe
 checks['prefix577_read_exact']=prefix_exact and r['prefix_rows_exact']==min(156,len(raw))
 checks['fresh_FINAL_first4_applied_exact']=finalexact and r['fresh_FINAL_applied_exact']
 checks['whole_TimeLimit_not_extended']=len(raw)<=MAX_APPLIED and (not raw or WARMUP+raw[-1]['global_raw_after']<=TIME_LIMIT)
 whole=r['whole'];verified=r['whole_source_verified'];replaystart=(D/'REPLAY_STARTED-private.json').exists()
 checks['conditional_replay_only_after_safe_whole']=(not replaystart and not replay and (not whole or not whole['safe'])) or (replaystart and whole is not None and whole['safe'] and whole['status']=='WHOLE_STRICT_SAFE_OFFICIAL_FINISH')
 replay_keys=prefix_keys+['index','raw','action','progress_delta','projection_limit','pre_failure','post_failure','all_failures','visited','checkpoint_sha256']
 checks['independent_replay_exact_or_correctly_skipped']=(not replaystart and not verified) or (verified and len(replay)==len(rows) and all(a[k]==b[k] for a,b in zip(rows,replay) for k in replay_keys) and r['replay']['final_checkpoint_exact'] and r['replay']['official_candidate_raw']==whole['official_candidate_raw'])
 if verified:
  finish=official_raw(rows[-1]['tracker']['finish_time_s']);checks['official_integer_comparison']=finish==whole['official_candidate_raw'] and all(q['candidate_source_raw']==finish and q['gain_raw']==q['baseline_source_raw']-finish and q['gain_ms']==20*q['gain_raw'] and q['strictly_earlier']==(q['gain_raw']>0) for q in r['official_integer_comparison'].values())
 else:checks['no_failed_whole_gain_claim']=all(q['gain_raw'] is None and q['gain_ms'] is None and not q['strictly_earlier'] for q in r['official_integer_comparison'].values())
 checks['caps']=all(n.get(k,0)<=v for k,v in c['caps'].items()) and r['times']['total_CPU_s']<=1200 and r['times']['total_wall_s']<=1500
 checks['native_seed_holdout_sealed_carry_zero']=all(r[k]==0 for k in ['native','worlds','resets','actions','new_seed','HOLDOUT','SEALED','carry'])
 checks['ledger_and_native_incumbent_preserved']=r['research_remaining']==22548 and r['reserve']==84000 and r['reserve_used']==0 and not r['native_incumbent_changed'] and not r['subsequent_native_executed']
 checks['protected_main_and_Participants_preserved']=subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31' and not subprocess.check_output(['git','diff','--name-only','main','--','Participants'],cwd=G,text=True).strip()
 ac=time.process_time()-CPU;aw=time.perf_counter()-WALL;aggregate=dict(r['times']);aggregate['total_CPU_s']+=ac+3;aggregate['total_wall_s']+=aw+3;aggregate['preparation_audit_CPU_s']+=ac+3;aggregate['preparation_audit_wall_s']+=aw+3;checks['aggregate_preparation_audit_caps']=aggregate['total_CPU_s']<=1200 and aggregate['total_wall_s']<=1500 and aggregate['preparation_audit_CPU_s']<=100 and aggregate['preparation_audit_wall_s']<=150
 out=dict(study=597,status='READ_ONLY_AUDIT_PASS' if all(checks.values()) else 'READ_ONLY_AUDIT_FAILURE',checks=checks,geometry_expected=geom,events=events,chain_head=head,CPU_s=ac,wall_s=aw,auxiliary_CPU_wall_charge_s=3,aggregate_time=aggregate,source_ticks=0,force_calls=0,geometry_queries=0,native_calls=0,input_sha256=dict(result=sha(G/'retry/cold597_result.json'),contract=sha(G/'retry/cold597_contract.json'),audit_code=sha(Path(__file__))))
 with (G/'retry/cold597_audit.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()
