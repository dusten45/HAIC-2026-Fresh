"""Saved-evidence audit and actual cost of one pure296 fallback-only run."""
import datetime,json,sys,statistics
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.fallback334_math import advance
from retry.confidence341_run import label
from retry.pair343_close import describe
G=Path(__file__).resolve().parent.parent

def close(R):
 D=R/'stage374';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert not (D/'cost.json').exists()
 for f,h in p['source_hashes'].items():assert sha(f)==h,f
 r=read(D/'B/result.json');b=read(D/'native-budget.json');data=[json.loads(s) for s in (D/'B/trace-private.jsonl').read_text().splitlines()] if (D/'B/trace-private.jsonl').exists() else [];z=np.load(D/'B/frames-actions-private.npz') if (D/'B/frames-actions-private.npz').exists() else None
 valid=not r['technical_error'] and r['comparison_valid'];counts=dict(known_supported_direct_contexts=0,known_birth_supported_retained_contexts=0,supported_direct_losses=0,supported_retained_losses=0,missing_birth_GT_direct=0,missing_birth_GT_retained=0,unresolved_births=0);fallback_intervals=accepted_intervals=transported_fallback_points=0;maxerr=0.;nodes=[]
 if valid:
  assert read(D/'reset-qualification.json')['passed'] and r['native_actions']==b['actions']==len(data)==len(z['actions'])==b['actor_act_calls']==b['actor_commit_calls']<=2000 and len(z['frames_uint8'])==len(data)+1 and b['resets']==b['actor_resets']==1
  assert sum(x['raw_ticks'] for x in data)==r['raw_step_ticks']==r['raw_counter_at_stop']-50 and r['raw_reset_ticks']==51 and r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent'];assert all(not x['terminated'] and not x['truncated'] for x in data[:-1])
  for i,x in enumerate(data):
   t=x['tracker'];assert x['executed']==x['returned_action'] and x['nominal_memory']==x['policy']['previous_steer'] and np.float32(x['nominal_memory'])==np.float32(x['executed'][0]) and len(x['raw_observations'])==x['raw_ticks'];reconstructed,lineage,transported=advance(t['before'],t['direct'],t['affine'],t['previous_yaw'],t['current_yaw'],t['current_speed'],True)
   a=np.asarray(reconstructed).reshape(-1,4);v=np.asarray(t['after']).reshape(-1,4);assert a.shape==v.shape;err=float(np.max(np.abs(a-v))) if a.size else 0.;maxerr=max(maxerr,err);assert err<=1e-12
   if t['before'] and t['affine'] is None:fallback_intervals+=1;transported_fallback_points+=len(t['before'])
   if t['affine'] is not None:accepted_intervals+=1
   e=x['routing_evidence'];assert not e['removed_indices'] and e['full_hazards']==t['after'] and [list(h[:3]) for h in t['after']]==[list(h) for h in e['routing_hazards']]
   newnodes=[]
   for j,parent in enumerate(lineage):
    if parent>=0:node=nodes[parent]
    else:
     lab,idx=label(t['direct'][-parent-1],x['pre_physical']);node=dict(birth_label=lab,fixture_index=idx)
     if lab=='unresolved':counts['unresolved_births']+=1
    newnodes.append(node);age=t['after'][j][3]
    if node['birth_label']=='fixture_supported':counts['known_supported_direct_contexts' if age==0 else 'known_birth_supported_retained_contexts']+=1
    if node['birth_label']=='missing_GT':counts['missing_birth_GT_direct' if age==0 else 'missing_birth_GT_retained']+=1
   nodes=newnodes
  if r['completed']:assert not r['actual_DNF'] and not r['censored'] and r['stop_reason']=='official_finish' and r['lap_ms']==round((r['finish']['finish_time_s']-r['postreset_start_time'])*1000)
  if r['protocol_stop']:assert b['actions']==2000 and r['censored'] and not r['actual_DNF']
 support=dict(audited=bool(valid),passed=bool(valid),**counts,all_tracked_hazards_passed_to_routing=bool(valid),tracking_reconstruction_max_error=maxerr,fallback_intervals_with_retained_points=fallback_intervals,fallback_point_transports=transported_fallback_points,accepted_optical_intervals=accepted_intervals,scope='Posthocbirthcirclelabels,notsemantic/occlusiontruth. No birthfilter/historyexists:allhazardsretainedinrouting. No positive_historytransferscomputed/not365. Unknownbirthsnotfalse-positiveGT.')
 diagnostics=describe(data,r) if valid and data else None;fields=['completed','actual_DNF','censored','technical_error','native_actions','lap_ms','damage','unique_tiles','total_tiles','retire_reason','stop_reason'];old=p['historical296'];judgment=dict(evaluated=bool(valid and not r['censored']),local_rescue_feasibility_pass=bool(valid and not r['censored'] and r['completed']),reason='knownTRAINrescue_finished' if valid and r['completed'] else 'official_DNF_local_rescue_rejected' if valid and r['actual_DNF'] else 'technical_or_protocol_unknown_no_pass',promotion=False,automatic_followup=False)
 measures=['wall_s','runner_CPU_s','actor_CPU_s','reset_wall_s','raw_step_render_wall_s','raw_contact_observer_wall_s','capture_wall_s','journal_wall_s','artifact_wall_s'];v=read(R/'project-effective-budget-v391.json');assert v['research_remaining']==41600 and v['actual_cumulative_wrapper_actions']==1306464
 cost=dict(stage=374,new_wrapper_actions=b['actions'],new_environment_resets=b['resets'],new_actor_resets=b['actor_resets'],new_actor_act_calls=b['actor_act_calls'],new_actor_commit_calls=b['actor_commit_calls'],total_native_cap=2000,additional_research=0,new_cached_actor_calls=0,new_source_physics_rollout_ticks=0,new_learning_fits=0,new_tuning=0,new_paid_resources=0,raw_step_ticks=r['raw_step_ticks'],raw_reset_ticks=r['raw_reset_ticks'],measurements={k:r[k] for k in measures},actual_cumulative_wrapper_actions=1306464+b['actions'],research_remaining=41600-b['actions'],final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1432064,scope='Singleactual374only,allprefixactionsincluded. Historical296notrerun/recharged. Coding/build/closure/gitnotfullytimed.')
 for f,h in p['protected_marker_hashes'].items():assert sha(f)==h,f
 assert all(Path(f).stat().st_mtime_ns==h for f,h in p['excluded_directory_stats'].items());assert not list(R.rglob('SEALED*.opened'))
 report=dict(stage=374,known_TRAIN='T2950',candidate_archive_sha256=p['config']['archive_sha256'],baseline296_archive_sha256=p['base_config']['archive_sha256'],package_difference=p['package_difference'],candidate_modified_after_freeze=False,actual_candidate={k:r.get(k) for k in fields},historical296={k:v for k,v in old.items() if k not in ['initial_observation_sha256','geometry_sha256']},historical_comparison='ExactoldTRAINidentity/initialimage/geometry/obstacles,immutable296base;historical315DNF208/338damage0.2. Nofreshpairedcontrol,nofulloldRNG/agentstate/pixel-prefixqualification. OneknownpostselectedTRAIN,notindependentgeneralization.',judgment=judgment,support_audit=support,diagnostics=diagnostics,cost=cost,H1_OFF=True,fallback_ON=True,birthrouting_OFF=True,no_372_materials_or_new_splits=True,candidate365_rejected_unchanged=True,champion296_unchanged=True,SEALED16_pending_preserved=True,promotion=False)
 save(D/'support-gate.json',support);save(D/'outcome-summary.json',diagnostics);save(D/'cost.json',cost);save(D/'summary-private.json',report);save(G/'retry/fallback374_result.json',report);save(D/'final-report-verification.json',dict(passed=True,actual_run_valid=bool(valid),source_and_candidate_hashes_exact=True,one_reset_no_retry=True,full_returned_controls_normal_memory=True,only_fixedfallback_and_decoder_dependency=True,known_support_audited=bool(valid),no372materials_or_newsplit=True,champion296_and365rejection_preserved=True,budget_actualonly=True))
 v.update(version=392,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v391.json'),prior_budget_sha256=sha(R/'project-effective-budget-v391.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage374_new_wrapper_actions=b['actions']);assert not (R/'project-effective-budget-v392.json').exists();save(R/'project-effective-budget-v392.json',v)
 ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==374 for s in ledger.read_text().splitlines())
 with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
 print(json.dumps(dict(outcome=report['actual_candidate'],judgment=judgment,support=support,cost=cost)),flush=True)
if __name__=='__main__':close(Path(sys.argv[1]).resolve())
