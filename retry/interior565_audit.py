"""Read-only565 audit of immutable source records; no simulator/model calls."""
import ast,hashlib,json,math,subprocess,time
from pathlib import Path
from retry.clip561_core import atomic_write,plain
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response565-private');rd=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();cpu,wall=time.process_time(),time.perf_counter()
c=rd(G/'retry/interior565_contract.json');r=rd(G/'retry/interior565_result.json');cost=rd(G/'retry/interior565_cost.json');checks={};design=rd(G/'retry/interior565_design.json');targets=rd(D/'interior-targets-private.json')
checks['source_and_input_hashes']=all(sha(G/p)==h for p,h in c['source_sha256'].items()) and all(sha(Path(p))==h for p,h in c['inputs_sha256'].items())
checks['single_frozen_empirical_interior_design']=design['source_sha256']==sha(G/'retry/interior565_design.py') and all(sha(Path(p))==h for p,h in design['inputs_sha256'].items()) and design['private_targets_sha256']==sha(D/'interior-targets-private.json')==c['interior_immutable_sha256'] and all(v>0 for k in ['physical','prefix','ratio'] for v in targets[k]) and design['model_ticks']==design['force_calls']==design['geometry_calls']==0
checks['contract_before_exclusive_starts']=rd(D/'STARTED.json')['contract_sha256']==sha(G/'retry/interior565_contract.json') and all(rd(p)['contract_sha256']==sha(G/'retry/interior565_contract.json') for p in D.glob('*-STARTED.json') if p.name!='DESIGN-STARTED.json')
checks['completed_without_technical_error']=r['completed'] and r['error'] is None
saved=rd(Path('/workspace/haic-response551-private/cold-candidate-private.json'));oldprefix=rd(Path('/workspace/haic-response562-private/prefix-modified-private.json'));oldfb=rd(Path('/workspace/haic-response562-private/feedback-suffix-private.json'));seed561=rd(Path('/workspace/haic-response561-private/branch-00-00-private.json'));seed=rd(D/'seed-private.json');prefix=rd(D/'original-prefix-private.json')
checks['prefix_and_seed_fullstate_force_exact']=len(prefix['rows'])==136 and len(seed['rows'])==180 and all(a['root_without_roads']==b['root_without_roads'] and a['forces']==b['forces'] for a,b in zip(prefix['rows'],saved['trace'][:136])) and all(a['root_without_roads']==b['root_without_roads'] and a['forces']==b['forces'] for a,b in zip(seed['rows'],seed561['rows']+oldfb['rows'][:48]))
checks['initial_history_and_handoff_exact']=prefix['checkpoint']['tracking']==[3,160] and rd(D/'finite-incumbent-00-private.json')['handoff']==oldprefix['checkpoint']
def safe(rows,c0=3,n0=160):
 clip,n=c0,n0;oldprogress=None;oldcenter=None
 for row in rows:
  fs=row['forces'];clip+=sum(f['ratio']>1 for f in fs);n+=4
  if any(bool(f['clipped'])!=(f['ratio']>1) for f in fs):return False
  if max(f['ratio'] for f in fs)>1.059 or clip/n>.1 or row.get('margin',-1)<.5 or row.get('path_error',4)>3 or row.get('reference_overspeed',5)>4.85 or row.get('body',100)>=100:return False
  if 'progress_delta' in row and not -.5<=row['progress_delta']<=row['projection_limit']:return False
 return True
trials=[e for e in r['events'] if e.get('evaluated')];finite=list(D.glob('trial-*-feedback-private.json'));linears=[rd(p) for p in sorted(D.glob('linearization-*-private.json'))];fds=list(D.glob('FD-*-private.json'))
checks['bounded_directions_trials_FD_restorations']=len(trials)==r['candidates']<=10 and r['linearizations']==len(linears)<=8 and len(fds)==r['FD_columns']==40*len(linears)<=320 and sum(q['kind']=='restore' for q in linears)==r['restoration_linearizations']<=6 and len(finite)==r['finite_feedback_calls']<=4
checks['restoration_relinearizes_measured_rank_force_active_sets']=all(q['interior_violation']>0 and len(q['FD_steps'])==40 for q in linears if q['kind']=='restore')
checks['exact_program_gate_before_fresh_feedback']=len(finite)==sum(e['local_program_safe'] for e in trials)
checks['feedback_from_changed_program_and_same_history']=True
for p in finite:
 fb=rd(p);local=rd(D/p.name.replace('-feedback-private','-surrogate-private'));rows=local['rows'][:132];clips=3+sum(f['clipped'] for row in rows for f in row['forces']);samples=160+4*len(rows)
 checks['feedback_from_changed_program_and_same_history'] &= safe(rows)
 if fb['rows']:
  first=fb['rows'][0];root=rows[-1]['root_without_roads'];before=first['before_root_without_roads'];root['planar']['steer']=before['planar']['steer'];checks['feedback_from_changed_program_and_same_history'] &= root==before and first['tracking_history_before']==[clips,samples] and first['episode_before_s']==oldprefix['checkpoint']['elapsed']
 checks['feedback_from_changed_program_and_same_history'] &= all(q['detail']['final_recertified'] and next(z for z in q['detail']['reports'] if z['mode']=='FINAL')['ok'] for q in fb['commands'])
checks['only_exact_safe_actual_terminal_gain_adopted']=len(r['steps'])==r['accepted_count']<=2 and all(s['accepted'] and s['feedback_safe'] and s['local_program_safe'] and s['terminal_gain_ms']>.001 for s in r['steps'])
for p in D.glob('finite-incumbent-*-private.json'):
 inc=rd(p)
 if inc['label']=='seed':continue
 local=rd(D/(inc['label']+'-surrogate-private.json'));fb=rd(D/(inc['label']+'-feedback-private.json'));checks['only_exact_safe_actual_terminal_gain_adopted'] &= len(fb['rows'])==48 and fb['stop']=='FINITE_HORIZON' and safe(local['rows'][:132]+fb['rows'])
checks['accepted_handoff_and_actual_feedback_hash_exact']=True
for p in D.glob('finite-incumbent-*-private.json'):
 inc=rd(p)
 if inc['label']=='seed':continue
 fb=rd(D/(inc['label']+'-feedback-private.json'));exact=rd(D/(inc['label']+'-exact-feasible-private.json'));h=hashlib.sha256(json.dumps(inc['handoff'],sort_keys=True,separators=(',',':')).encode()).hexdigest();checks['accepted_handoff_and_actual_feedback_hash_exact'] &= fb['start_hash']==h and exact['handoff']==inc['handoff'] and exact['terminal_checkpoint']==fb['checkpoint']
checks['no_unsafe_numerical_center_adopted']=all('-numerical-center' not in rd(p)['label'] for p in D.glob('finite-incumbent-*-private.json'))
checks['existing_whole_success_preserved']=r['whole_incumbent']=='seed' and r['whole_incumbent_finish_s']==r['seed_whole_finish_s'] or r['whole_incumbent']=='new' and r['whole_attempt_safe_finish'] and r['whole_incumbent_finish_s']<r['seed_whole_finish_s']
starting=rd(D/'starting-restoration-private.json');oldlast=rd(Path('/workspace/haic-response564-private/trial-00-02-surrogate-private.json'))
checks['last564_restoration_state_force_exact']=len(starting['rows'])==180 and all(a['root_without_roads']==b['root_without_roads'] and a['forces']==b['forces'] for a,b in zip(starting['rows'],oldlast['rows']))
checks['targets_unchanged_across_candidates']=all(e['internal_target_sha256']==c['interior_immutable_sha256'] and e['LP']['interior_sha256']==c['interior_immutable_sha256'] for e in trials)
checks['safe_program_and_continuation_counts']=r['safe_programs']==sum(e['local_program_safe'] for e in trials) and r['safe_finite_continuations']==sum(e['feedback_safe'] for e in trials)
checks['rank_membership_disclosed']=r['rank_membership_differences']==[q['rank_membership_difference_vsseed'] for q in linears]
new=r['accepted_count']>0
checks['final_new_candidate_whole_then_exact_replay']=bool(r['independent_verification']) and all(v['fullstate_force_exact'] and v['checkpoint_exact'] for v in r['independent_verification']) if new else not r['independent_verification'] and r['existing_whole_proof_reused'] and r['no_redundant_seed_replay'] and rd(G/'retry/continuation563_audit.json')['passed']
fullpath=D/'final-full-feedback-private.json'
if fullpath.exists():
 full=rd(fullpath);lastinc=rd(sorted(D.glob('finite-incumbent-*-private.json'))[-1]);h=hashlib.sha256(json.dumps(lastinc['handoff'],sort_keys=True,separators=(',',':')).encode()).hexdigest();checks['whole_starts_at_final_actual_handoff']=full['start_hash']==h
 if r['whole_attempt_safe_finish']:
  local=rd(D/(lastinc['label']+'-surrogate-private.json'));rows=prefix['rows']+local['rows'][:132]+full['rows'];lc=ln=tc=tn=0;ok=True;clipmax=0.
  for row in rows:
   fs=row['forces'];peak=max(f['ratio'] for f in fs);clipped=sum(f['clipped'] for f in fs)
   if row['index']<=24:lc+=clipped;ln+=4;ok &= peak<=2.5 and (row['index']<24 or lc/ln<=.15)
   else:tc+=clipped;tn+=4;clipmax=max(clipmax,tc/tn);ok &= peak<=1.059 and tc/tn<=.1 and row['reference_overspeed']<=4.85
   ok &= row['margin']>=.5 and row['path_error']<=3 and row['body']<100
  checks['whole_global_safety_and_original_history']=bool(ok) and full['checkpoint']['tracking']==[tc,tn]
  checks['whole_official_finish_direct_from_tracker']=full['stop']=='SOURCE_FINISH' and r['whole_attempt_finish_s']==full['checkpoint']['tracker']['finish_time_s']-1.02
checks['whole_time_measured_not_finite_gain']=abs(r['whole_gain_vs551_ms']-1000*(saved['summary']['model_finish_episode_s']-r['whole_incumbent_finish_s']))<1e-9
checks['cost_FIRST_and_all_body_ticks']=all(rd(D/(name+'-ledger-private.json'))['label']=='phase-finally-FIRST' and rd(D/(name+'-ledger-private.json'))['cost']==p and p['body_checks']==p['model_ticks'] and p['max_all_model_body']<100 for name,p in cost['phases'].items())
keys=[('model_ticks','model_ticks'),('force_evaluations','force'),('geometry_checks','geometry'),('CPU_s','CPU_s'),('wall_s','wall_s')]
checks['all_phase_and_total_caps']=all(all(p[k]<=c['budgets'][name][cap] for k,cap in keys) for name,p in cost['phases'].items()) and all(cost['total'][k]<=c['aggregate'][cap] for k,cap in keys)
checks['design_plus_model_aggregate_cost']=cost['total']['CPU_s']+design['CPU_s']<=c['aggregate']['CPU_s'] and cost['total']['wall_s']+design['wall_s']<=c['aggregate']['wall_s']
checks['cost_reconciled']=r['cost']==cost['total'] and all(cost['total'][k]==sum(p[k] for p in cost['phases'].values()) for k in ['model_ticks','force_evaluations','internal_wheel_force_evaluations','geometry_checks','body_checks']) and all(cost['total'][k]>=sum(p[k] for p in cost['phases'].values()) for k in ['CPU_s','wall_s'])
checks['no_native_protected_reserve']=all(r[k]==0 for k in ['new_native_actions','new_resets','new_worlds','new_seeds','HOLDOUT_queries','SEALED_queries','reserve_used']) and r['research_remaining']==22758 and r['reserve']==84000 and r['actual_baseline_s']==13.66 and r['no_native_gain_observation'] and r['prior561_aperture_failure_preserved']
checks['main_and_Participants_preserved']=subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31' and not subprocess.check_output(['git','diff','--name-only','main','--','Participants'],cwd=G,text=True).strip()
evidence=[]
for e in trials:
 data=rd(D/(e['label']+'-surrogate-private.json'));rows=data['rows'][:132];clip,n=3,160;first=None;maximum=0.;maxhistory=None
 for row in rows:
  clip+=sum(f['clipped'] for f in row['forces']);n+=4;peak=max(f['ratio'] for f in row['forces']);reasons=[]
  if peak>1.059:reasons.append('FORCE')
  if clip/n>.1:reasons.append('CLIP_HISTORY')
  if row['margin']<.5:reasons.append('FOOTPRINT')
  if row['path_error']>3:reasons.append('PATH')
  if row['reference_overspeed']>4.85:reasons.append('REFERENCE')
  if row['body']>=100:reasons.append('BODY')
  if 'progress_delta' in row and (row['progress_delta']<-.5 or row['progress_delta']>row['projection_limit']):reasons.append('PROJECTION')
  if first is None and reasons:first=dict(index=row['index'],raw=row['raw'],reasons=reasons,tracking_history=[clip,n],force_ratio=peak)
  if clip/n>maximum:maximum=clip/n;maxhistory=[clip,n]
 ratios=data['ratios'][:528];old=seed['ratios'][:528];evidence.append(dict(label=e['label'],first_failure=first,max_clip=maximum,max_clip_history=maxhistory,max_force=max(ratios),min_prefix_order_slack=min(data['order'][:132]),new_clips_vs_seed=sum(a>1 and b<=1 for a,b in zip(ratios,old)),freed_clips_vs_seed=sum(a<=1 and b>1 for a,b in zip(ratios,old))))
checks['rejected_programs_have_exact_measured_violation']=all(q['first_failure'] is not None for q in evidence if not next(e for e in trials if e['label']==q['label'])['local_program_safe'])
summary=[dict(label=e['label'],kind=e['kind'],local_program_safe=e['local_program_safe'],feedback_safe=e['feedback_safe'],accepted=e['accepted'],terminal_gain_ms=e['terminal_gain_ms'],interior_violation=e['trial_interior_violation'],physical_violation=e['trial_global_violation']) for e in trials]
out=dict(passed=all(checks.values()),design_CPU_s=design['CPU_s'],design_wall_s=design['wall_s'],model_plus_design_CPU_s=cost['total']['CPU_s']+design['CPU_s'],model_plus_design_wall_s=cost['total']['wall_s']+design['wall_s'],checks=checks,rejection_evidence=evidence,trial_summary=summary,not_exercised=['fresh_actual_feedback','new_whole_suffix'] if not finite else [],scope_counts=dict(linearizations=len(linears),FD=len(fds),restorations=r['restoration_linearizations'],candidates=len(trials),finite_feedback=len(finite),accepted=r['accepted_count']),model_ticks=0,force_calls=0,geometry_calls=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
atomic_write(G/'retry/interior565_audit.json',out,True);print(json.dumps(plain(out),indent=2));raise SystemExit(0 if out['passed'] else 1)
