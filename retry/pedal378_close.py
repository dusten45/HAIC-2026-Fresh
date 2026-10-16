"""Close one139pedalpulse; observedprefixqualification and diagnostic-onlyresult."""
import datetime,json,sys
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.fallback334_math import advance
from retry.confidence341_run import label
from retry.pair343_close import describe
G=Path(__file__).resolve().parent.parent

def rows(p):return [json.loads(s) for s in Path(p).read_text().splitlines()] if Path(p).exists() else []
def first_differences(a,b,z,zz):
 funcs=dict(executed=lambda x:x['executed'],returned_candidate_control=lambda x:x['returned_action'],features=lambda x:x['features'],tracker_before=lambda x:x['tracker']['before'],tracker_after=lambda x:x['tracker']['after'],path=lambda x:x['pixel_path'],target=lambda x:x['features'][:3],pre_memory=lambda x:x['features'][7],post_memory=lambda x:x['nominal_memory'],pre_physics=lambda x:x['pre_physical'],post_physics=lambda x:x['post_physical'],raw_observations=lambda x:x['raw_observations'],pre_RNG=lambda x:x['pre_RNG'],post_RNG=lambda x:x['post_RNG'])
 out={k:next((i+1 for i,(x,y) in enumerate(zip(a,b)) if fn(x)!=fn(y)),None) for k,fn in funcs.items()}
 out['input_pixels']=next((i+1 for i in range(min(len(a),len(b))) if not np.array_equal(z['frames_uint8'][np.maximum(np.arange(i-3,i+1),0)],zz['frames_uint8'][np.maximum(np.arange(i-3,i+1),0)])),None) if z is not None else None
 return out

def close(R):
 D=R/'stage378';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert not (D/'cost.json').exists()
 for f,h in p['source_hashes'].items():assert sha(f)==h,f
 F=D/'B';r=read(F/'result.json');a=rows(F/'trace-private.jsonl');b=rows(R/'stage375/T29510/B/trace-private.jsonl');old=rows(R/'stage377/A/trace-private.jsonl');budget=read(D/'native-budget.json');z=np.load(F/'frames-actions-private.npz') if (F/'frames-actions-private.npz').exists() else None;cz=np.load(R/'stage375/T29510/B/frames-actions-private.npz');oz=np.load(R/'stage377/A/frames-actions-private.npz');valid=not r['technical_error'] and r['comparison_valid'];changed=[x['step'] for x in a if x['executed']!=x['returned_action']];applied=r['intervention_applied'];qualified=read(D/'pre-intervention-qualification.json') if (D/'pre-intervention-qualification.json').exists() else None
 counts=dict(known_supported_direct_contexts=0,known_birth_supported_retained_contexts=0,supported_direct_losses=0,supported_retained_losses=0,missing_birth_GT_direct=0,missing_birth_GT_retained=0,unresolved_births=0);nodes=[];maxerr=0.
 if valid:
  assert len(a)==r['native_actions']==budget['actions']==budget['actor_act_calls']==budget['actor_commit_calls']==len(z['actions'])<=2000 and len(z['frames_uint8'])==len(a)+1 and budget['resets']==budget['actor_resets']==1
  assert sum(x['raw_ticks'] for x in a)==r['raw_step_ticks']==r['raw_counter_at_stop']-50 and r['raw_reset_ticks']==51 and r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent'];assert changed==([139] if applied else [])
  for x in a:
   t=x['tracker'];after,lin,_=advance(t['before'],t['direct'],t['affine'],t['previous_yaw'],t['current_yaw'],t['current_speed'],True);aa=np.asarray(after).reshape(-1,4);bb=np.asarray(t['after']).reshape(-1,4);assert aa.shape==bb.shape;err=float(np.max(np.abs(aa-bb))) if aa.size else 0.;maxerr=max(maxerr,err);assert err<=1e-12;e=x['routing_evidence'];assert not e['removed_indices'] and e['full_hazards']==t['after'] and [list(h[:3]) for h in t['after']]==[list(h) for h in e['routing_hazards']];assert x['nominal_memory']==x['policy']['previous_steer'] and np.float32(x['nominal_memory'])==np.float32(x['executed'][0]) and len(x['raw_observations'])==x['raw_ticks'];new=[]
   for j,parent in enumerate(lin):
    if parent>=0:node=nodes[parent]
    else:
     lab,idx=label(t['direct'][-parent-1],x['pre_physical']);node=dict(label=lab,fixture_index=idx)
     if lab=='unresolved':counts['unresolved_births']+=1
    new.append(node);age=t['after'][j][3]
    if node['label']=='fixture_supported':counts['known_supported_direct_contexts' if age==0 else 'known_birth_supported_retained_contexts']+=1
    if node['label']=='missing_GT':counts['missing_birth_GT_direct' if age==0 else 'missing_birth_GT_retained']+=1
   nodes=new
  if applied:
   assert qualified['passed'] and qualified['prefix_actions']==r['qualified_prefix_actions']==138;assert a[138]['executed'][0]==a[138]['returned_action'][0] and a[138]['executed'][1:]==p['intervention']['gas_brake_from377'];assert a[138]['actor_state']['agent_pickle_sha256']==a[138]['policy']['agent_pickle_sha256']
  if r['completed']:assert not r['actual_DNF'] and not r['censored'] and r['lap_ms']==round((r['finish']['finish_time_s']-r['postreset_start_time'])*1000)
 support=dict(audited=bool(valid),passed=bool(valid),**counts,all_tracked_hazards_routed=bool(valid),tracking_reconstruction_max_error=maxerr,scope='Original374tracker/routingonownchangedobservations;no head/controller/tracker/memorymodification. Posthoccirclebirthlabelsnotsemantic/occlusiontruth.')
 comparisons=dict(against375_untreated374=first_differences(a,b,z,cz),against377_unchanged296=first_differences(a,old,z,oz));post139=None
 if applied and len(a)>=139:post139=dict(executed139_equals296=a[138]['executed']==old[138]['executed'],post139_physics_equals296=a[138]['post_physical']==old[138]['post_physical'],post139_RNG_equals296=a[138]['post_RNG']==old[138]['post_RNG'],input140_pixels_equals296=bool(np.array_equal(z['frames_uint8'][139],oz['frames_uint8'][139])),candidate139_tracker_preserved=a[138]['tracker']==b[138]['tracker'],candidate139_nominal_memory_preserved=a[138]['nominal_memory']==b[138]['nominal_memory'])
 outcomes={};diagnostics={};fields=['completed','actual_DNF','censored','technical_error','native_actions','lap_ms','damage','unique_tiles','total_tiles','retire_reason','stop_reason']
 for name,rr,dd in [('378_diagnostic',r,a),('375_untreated374',read(R/'stage375/T29510/B/result.json'),b),('377_unchanged296',read(R/'stage377/A/result.json'),old)]:
  outcomes[name]={k:rr.get(k) for k in fields}
  if dd:
   raw=describe(dd,rr);diagnostics[name]={k:raw[k] for k in ['collision_event_actions','raw_collision_flags','raw_observation_count','damage','unique_tiles','speed_m_s','off_track_counter','last_tile_growth_action','completed','actual_DNF','protocol_stop','lap_ms','retire_reason']};diagnostics[name].update(touching_fixture_pair_count=len(raw['fixture_touching']),touching_raw_endpoint_count=sum(q['touching_raw_endpoint_count'] for q in raw['fixture_touching']))
 measures=['wall_s','runner_CPU_s','actor_CPU_s','reset_wall_s','raw_step_render_wall_s','raw_contact_observer_wall_s','capture_wall_s','journal_wall_s','artifact_wall_s'];cost=dict(stage=378,new_wrapper_actions=budget['actions'],new_environment_resets=budget['resets'],new_actor_resets=budget['actor_resets'],new_actor_act_calls=budget['actor_act_calls'],new_actor_commit_calls=budget['actor_commit_calls'],total_native_cap=2000,additional_research=0,new_cached_actor_calls=0,new_source_physics_rollout_ticks=0,new_learning_fits=0,new_policy_archive_changes=0,new_paid_resources=0,raw_step_ticks=r['raw_step_ticks'],raw_reset_ticks=r['raw_reset_ticks'],measurements={k:r[k] for k in measures},actual_cumulative_wrapper_actions=1311818+budget['actions'],research_remaining=36246-budget['actions'],final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1432064,scope='One378diagnosticactualrunonlyincluding138prefix;references375/377notrerun/recharged. Coding/registration/closure/gitnotfullytimed.')
 report=dict(stage=378,diagnostic_only_not_deployable_policy=True,not_improvement_candidate=True,policy374_archive_sha256=p['config']['archive_sha256'],policy_archive_unchanged=True,qualified_prefix_actions=r['qualified_prefix_actions'],pre_intervention_qualification=qualified,intervention_applied=applied,only_explicit_override_actions=changed,steering_tracker_nominal_memory_preserved_at139=bool(applied and post139 and post139['candidate139_tracker_preserved'] and post139['candidate139_nominal_memory_preserved']),post139_comparison=post139,outcomes=outcomes,diagnostics=diagnostics,first_actual_differences=comparisons,support_audit=support,cost=cost,local_result='Qualifiedsingle139pedalreplacementfollowedbyofficialfinish' if valid and applied and r['completed'] else 'Qualifiedsingle139pedalreplacementdidnotrescueofficialDNF' if valid and applied and r['actual_DNF'] else 'Noqualifiedoutcome_due_to_technical_or_protocolstop',causal_limit='OnepostselectedknownTRAINintervention,notuniquesufficientcause/generalization/safety. After139ownobservationsandnormal374wholecontrolscouple. No secondtime/value/interventionorpolicyupdate.',no372materials_or_other_split=True,champion296_unchanged=True,candidate365_rejected_unchanged=True,SEALED16_pending_preserved=True,promotion=False,automatic_followup=False)
 for f,h in p['protected_hashes'].items():assert sha(f)==h,f
 assert all(Path(f).stat().st_mtime_ns==h for f,h in p['excluded_directory_stats'].items());assert not list(R.rglob('SEALED*.opened'));v=read(R/'project-effective-budget-v395.json');assert v['research_remaining']==36246 and v['actual_cumulative_wrapper_actions']==1311818
 save(D/'support-gate.json',support);save(D/'cost.json',cost);save(D/'summary-private.json',report);save(G/'retry/pedal378_result.json',report);save(D/'final-report-verification.json',dict(passed=True,actual_run_valid=bool(valid),prefix_qualified_before_pulse=bool(applied and qualified and qualified['passed']),only_one_explicit139_override=changed==[139],archive_unchanged=True,not_deployable_or_candidate=True,resource_actual_only=True))
 v.update(version=396,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v395.json'),prior_budget_sha256=sha(R/'project-effective-budget-v395.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage378_new_wrapper_actions=budget['actions']);assert not (R/'project-effective-budget-v396.json').exists();save(R/'project-effective-budget-v396.json',v)
 ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==378 for s in ledger.read_text().splitlines())
 with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
 print(json.dumps(dict(outcomes=outcomes,applied=applied,qualified_prefix=r['qualified_prefix_actions'],first=comparisons,post139=post139,cost=cost)),flush=True)
if __name__=='__main__':close(Path(sys.argv[1]).resolve())
