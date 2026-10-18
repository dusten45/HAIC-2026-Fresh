"""Read-only audit of frozen563 records; no simulator/model/geometry calls."""
import hashlib,json,subprocess,time
from pathlib import Path
from retry.clip561_core import atomic_write,plain
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response563-private')
rd=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cpu,wall=time.process_time(),time.perf_counter()
c=rd(G/'retry/continuation563_contract.json');r=rd(G/'retry/continuation563_result.json');cost=rd(G/'retry/continuation563_cost.json');checks={}
checks['sources_and_inputs_unchanged']=all(sha(G/p)==h for p,h in c['source_sha256'].items()) and all(sha(Path(p))==h for p,h in c['private_inputs_sha256'].items())
checks['registered_before_evaluations']=rd(D/'STARTED.json')['contract_sha256']==sha(G/'retry/continuation563_contract.json') and all(rd(p)['contract_sha256']==sha(G/'retry/continuation563_contract.json') for p in D.glob('*-STARTED.json'))
checks['completed_without_technical_error']=r['completed'] and r['error'] is None
saved=rd(Path('/workspace/haic-response551-private/cold-candidate-private.json'));seed561=rd(Path('/workspace/haic-response561-private/branch-00-00-private.json'));oldfb=rd(Path('/workspace/haic-response562-private/feedback-suffix-private.json'));oldprep=rd(Path('/workspace/haic-response562-private/prefix-modified-private.json'));prefix=rd(D/'original-prefix-private.json');seed=rd(D/'seed-private.json')
checks['exact_original_prefix']=len(prefix['rows'])==136 and all(a['root_without_roads']==b['root_without_roads'] and a['forces']==b['forces'] for a,b in zip(prefix['rows'],saved['trace'][:136]))
checks['exact_seed_180raw']=len(seed['rows'])==180 and all(a['root_without_roads']==b['root_without_roads'] and a['forces']==b['forces'] for a,b in zip(seed['rows'],seed561['rows']+oldfb['rows'][:48]))
checks['initial_history_preserved']=prefix['checkpoint']['tracking']==[3,160] and rd(D/'finite-incumbent-00-private.json')['handoff']==oldprep['checkpoint']
records=list(D.glob('*-program-private.json'));finite=list(D.glob('proposal-*-feedback-private.json'))+list(D.glob('poll-*-feedback-private.json'))
checks['FD_and_proposal_caps']=len(list(D.glob('FD-*-private.json')))<=120 and len(records)<=9 and len(r['directions'])<=3 and r['accepted_count']<=3
checks['fresh_feedback_for_locally_safe_programs']=len(finite)==sum(p['local_program_safe'] for d in r['directions'] for p in d['proposals'])==r['feedback_finite_calls']
checks['feedback_program_root_history_and_fresh_FINAL']=True
for p in finite:
 f=rd(p);program=rd(D/p.name.replace('-feedback-private','-program-private'));rows=program['rows'];clips=3+sum(z['clipped'] for row in rows for z in row['forces']);samples=160+4*len(rows)
 # local stores the full program terminal root; actual feedback records its hash and first pre-state.
 if f['rows']:
  first=f['rows'][0];checks['feedback_program_root_history_and_fresh_FINAL'] &= first['tracking_history_before']==[clips,samples] and first['episode_before_s']==oldprep['checkpoint']['elapsed']
  root=program['terminal_root_without_roads'];before=first['before_root_without_roads'];root['planar']['steer']=before['planar']['steer'];checks['feedback_program_root_history_and_fresh_FINAL'] &= root==before
 checks['feedback_program_root_history_and_fresh_FINAL'] &= all(q['detail']['final_recertified'] and next(z for z in q['detail']['reports'] if z['mode']=='FINAL')['ok'] for q in f['commands'])
def safe(rows,initial=(3,160)):
 clip,n=initial
 for row in rows:
  fs=row['forces'];clip+=sum(f['ratio']>1 for f in fs);n+=4
  if any(bool(f['clipped'])!=(f['ratio']>1) for f in fs):return False
  if max(f['ratio'] for f in fs)>1.059 or clip/n>.1 or row['margin']<.5 or row['path_error']>3 or row['reference_overspeed']>4.85 or row['body']>=100:return False
 return True
checks['accepted_actual_terminal_gain_and_global_safety']=all(s['accepted'] and s['feedback_safe'] and s['local_program_safe'] and s['terminal_gain_ms']>.001 for s in r['steps'])
for p in D.glob('finite-incumbent-*-private.json'):
 inc=rd(p)
 if inc['label']=='seed':continue
 program=rd(D/(inc['label']+'-program-private.json'));fb=rd(D/(inc['label']+'-feedback-private.json'));checks['accepted_actual_terminal_gain_and_global_safety'] &= safe(program['rows']+fb['rows']) and fb['stop']=='FINITE_HORIZON' and len(fb['rows'])==48
checks['whole_best_retention']=r['whole_incumbent']=='seed' and r['whole_incumbent_finish_s']==r['seed_whole_finish_s'] or r['whole_incumbent']=='new' and r['whole_attempt_safe_finish'] and r['whole_incumbent_finish_s']<r['seed_whole_finish_s']
checks['whole_finish_measured_separately']=abs(r['whole_gain_vs551_ms']-1000*(saved['summary']['model_finish_episode_s']-r['whole_incumbent_finish_s']))<1e-9
checks['independent_whole_tape_replay']=bool(r['independent_verification']) and all(v['fullstate_force_exact'] for v in r['independent_verification']) and any(v['safe_finish'] and v['finish_s']==r['whole_incumbent_finish_s'] for v in r['independent_verification'])
checks['phase_finally_cost_FIRST']=all(rd(D/(name+'-ledger-private.json'))['label']=='phase-finally-FIRST' and rd(D/(name+'-ledger-private.json'))['cost']==p for name,p in cost['phases'].items())
keys=[('model_ticks','model_ticks'),('force_evaluations','force'),('geometry_checks','geometry'),('CPU_s','CPU_s'),('wall_s','wall_s')]
checks['phase_and_aggregate_caps']=all(all(p[k]<=c['budgets'][name][cap] for k,cap in keys) and p['body_checks']==p['model_ticks'] and p['max_all_model_body']<100 for name,p in cost['phases'].items()) and all(cost['total'][k]<=c['aggregate'][cap] for k,cap in keys)
checks['cost_reconciled']=r['cost']==cost['total'] and all(cost['total'][k]==sum(p[k] for p in cost['phases'].values()) for k in ['model_ticks','force_evaluations','internal_wheel_force_evaluations','geometry_checks','body_checks']) and all(cost['total'][k]>=sum(p[k] for p in cost['phases'].values()) for k in ['CPU_s','wall_s'])
checks['prior_failures_and_baseline_preserved']=r['prior561_aperture_failure_preserved'] and rd(G/'retry/mode561_result.json')['accepted_count']==0 and r['actual_baseline_s']==13.66 and r['no_native_gain_observation']
checks['no_native_protected_reserve']=all(r[k]==0 for k in ['new_native_actions','new_resets','new_worlds','new_seeds','HOLDOUT_queries','SEALED_queries','reserve_used']) and r['research_remaining']==22758 and r['reserve']==84000
checks['main_and_Participants_preserved']=subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31' and not subprocess.check_output(['git','diff','--name-only','main','--','Participants'],cwd=G,text=True).strip()
rejection_evidence=[]
for p in sorted(records):
 data=rd(p);clip,n=3,160;first=None;new=freed=0
 for k,row in enumerate(data['rows']):
  for f,b in zip(row['forces'],seed['rows'][k]['forces']):new+=bool(f['clipped'] and not b['clipped']);freed+=bool(b['clipped'] and not f['clipped'])
  clip+=sum(f['clipped'] for f in row['forces']);n+=4;reasons=[]
  if clip/n>.1:reasons.append('CLIP_HISTORY')
  if max(f['ratio'] for f in row['forces'])>1.059:reasons.append('FORCE')
  if reasons and first is None:first=dict(index=row['index'],raw=row['raw'],reasons=reasons,history=[clip,n],force_ratio=max(f['ratio'] for f in row['forces']))
 rejection_evidence.append(dict(case=p.name,first_failure=first,new_clips_vs_seed=new,freed_clips_vs_seed=freed,final_history=[clip,n]))
checks['rejected_proposals_have_measured_force_or_history_violation']=len(rejection_evidence)==2 and all(q['first_failure'] is not None for q in rejection_evidence)
out=dict(passed=all(checks.values()),checks=checks,rejection_evidence=rejection_evidence,scope_counts=dict(FD=len(list(D.glob('FD-*-private.json'))),actual_proposals=len(records),finite_feedback_runs=len(finite),accepted=r['accepted_count']),not_exercised=['fresh_feedback_candidate_continuation','new_candidate_whole_suffix'] if not finite else [],model_ticks=0,force_calls=0,geometry_calls=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
atomic_write(G/'retry/continuation563_audit.json',out,True);print(json.dumps(plain(out),indent=2));raise SystemExit(0 if out['passed'] else 1)
