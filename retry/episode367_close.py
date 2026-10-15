"""Actual365 N2 outcome and posthoc positive-lineage/support audit."""
import datetime,json
from pathlib import Path
import sys
import numpy as np
from retry.path271_run import read,save,sha
from retry.episode367_stage import G,legacy_support
from retry.package349_run import projection
from retry.pair343_close import describe
from retry.history365_logic import advance_evidence
from retry.lineage339_audit import track
from retry.confidence341_run import label

def rows(path):return [json.loads(s) for s in Path(path).read_text().splitlines()]
def uid(tag):return tuple(map(int,tag.split(':')))

def close(R):
 D=R/'stage367';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert not (D/'cost.json').exists()
 for f,h in p['source_hashes'].items():assert sha(f)==h,f
 r=read(D/'B/result.json');data=rows(D/'B/trace-private.jsonl');old=rows(R/'stage359/B/trace-private.jsonl');oldresult=read(R/'stage359/B/result.json');b=read(D/'native-budget.json');z=np.load(D/'B/frames-actions-private.npz');oz=np.load(R/'stage359/B/frames-actions-private.npz');gate=read(D/'historical-comparison-qualification.json');used=b['actions']
 assert r['technical_error'] is None and r['comparison_valid'] and gate['passed'] and read(D/'reset-qualification.json')['passed']
 assert used==r['native_actions']==len(data)==len(z['actions'])==b['actor_act_calls']==b['actor_commit_calls']<=2000 and len(z['frames_uint8'])==used+1 and b['resets']==b['actor_resets']==1
 assert sum(x['raw_ticks'] for x in data)==r['raw_step_ticks']==r['raw_counter_at_stop']-50 and all(not x['terminated'] and not x['truncated'] for x in data[:-1]);assert r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent']
 for x in data:assert x['executed']==x['returned_action'] and x['nominal_memory']==x['policy']['previous_steer'] and np.float32(x['nominal_memory'])==np.float32(x['executed'][0]) and len(x['raw_observations'])==x['raw_ticks']
 if gate['no_semantic_branch']:
  assert used==len(old)==gate['common_semantic_actions'] and gate['common_qualified_input_stacks']==used+1 and np.array_equal(z['actions'],oz['actions']) and np.array_equal(z['frames_uint8'],oz['frames_uint8'])
  for x,y in zip(data,old):
   for k in ['executed','features','pixel_path','audit','nominal_memory','tracker','pre','post','pre_physical','post_physical','pre_RNG','post_RNG','raw_observations','finish']:assert x[k]==y[k],k
   assert legacy_support(x['support_record'])==y['support_record'] and projection(x['actor_state'])==projection(y['actor_state']) and projection(x['policy'])==projection(y['policy'])
 if r['completed']:assert r['stop_reason']=='official_finish' and not r['censored'] and r['lap_ms']==round((r['finish']['finish_time_s']-r['postreset_start_time'])*1000)
 if r['protocol_stop']:assert used==2000 and r['censored'] and not r['completed'] and not r['actual_DNF']
 lineage=track(data);prev=[];nodes={};direct=retained=missingd=missingr=0;losses=[];edges=[];held=[];restored=[];low=[]
 for i,x in enumerate(data):
  sr=advance_evidence(x['tracker'],prev,i+1,z['frames_uint8'][i].astype(np.float32)/255);assert sr==x['support_record'];prev=sr['after']
  for item in sr['births']:
   ident=tuple(item['uid']);lab,idx=label(item['point'],x['pre_physical']);parents=[a for a in lineage['records'][i]['associations'] if uid(a['new_tag'])==ident];parent=nodes.get(uid(parents[0]['old_tag'])) if len(parents)==1 else None;inherit=bool(parent and parent['positive']);own=item['raw_road_neighbors']>0;assert item['positive_history']==bool(own or inherit);origins=[dict(label=lab,fixture_index=idx)] if own else parent['origins'] if inherit else [];nodes[ident]=dict(label=lab,fixture_index=idx,positive=item['positive_history'],origins=origins)
   if item['low']:low.append(dict(action=i+1,uid=item['uid'],raw_road_neighbors=item['raw_road_neighbors'],area_pixels=item['component_area'],positive_history=item['positive_history'],posthoc_label=lab))
   if inherit:edges.append(dict(action=i+1,uid=item['uid'],parent_uid=list(uid(parents[0]['old_tag'])),distance_m=parents[0]['distance_m'],low_birth=item['low'],positive_history=item['positive_history'],current_label=lab,confirmed_distinct_supported_fixture_transfer=bool(lab=='fixture_supported' and any(o['label']=='fixture_supported' and o['fixture_index']!=idx for o in parent['origins'])),ambiguous=lab!='fixture_supported' or any(o['label']!='fixture_supported' for o in parent['origins'])))
  e=x['routing_evidence'];wanted=[j for j,(h,item) in enumerate(zip(x['tracker']['after'],sr['after'])) if item['low'] and h[3]>0 and not item['positive_history']];assert e['removed_indices']==wanted and e['full_hazards']==x['tracker']['after']
  for j,(h,item) in enumerate(zip(x['tracker']['after'],sr['after'])):
   lab=nodes[tuple(item['uid'])]['label'];excluded=j in wanted
   if lab=='fixture_supported':
    if h[3]==0:direct+=1
    else:retained+=1
    if excluded:losses.append(dict(action=i+1,uid=item['uid'],age=h[3],kind='direct' if h[3]==0 else 'retained'))
   if lab=='missing_GT':
    if h[3]==0:missingd+=1
    else:missingr+=1
   if h[3]==0:assert not excluded
   if excluded:held.append(dict(action=i+1,uid=item['uid'],age=h[3]))
   if item['low'] and h[3]>0 and item['positive_history']:restored.append(dict(action=i+1,uid=item['uid'],age=h[3],posthoc_label=lab))
 core=[]
 for x in data:
  for j,(h,item) in enumerate(zip(x['tracker']['after'],x['support_record']['after'])):
   if item['uid']==[121,0]:core.append(dict(action=x['step'],age=h[3],low=item['low'],positive_history=item['positive_history'],routed=j not in x['routing_evidence']['removed_indices']))
 critical=[x for x in core if 127<=x['action']<=129];birth121=[x for x in low if x['uid']==[121,0]]
 if gate['no_semantic_branch']:assert len(birth121)==1 and not birth121[0]['positive_history'] and len(critical)==3 and [x['age'] for x in critical]==[6,7,8] and all(not x['routed'] for x in critical)
 first=lambda key:next((x['step'] for x,y in zip(data,old) if x[key]!=y[key]),None)
 firsttarget=next((x['step'] for x,y in zip(data,old) if x['features'][:3]!=y['features'][:3]),None)
 outcome=describe(data,r);historic=describe(old,oldresult);delta=r['lap_ms']-oldresult['lap_ms'] if r['completed'] and oldresult['completed'] else None
 v=read(R/'project-effective-budget-v382.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'],v['B_operating_cap'])==(1291467,21938,84000,0,1397405)
 measures=['wall_s','runner_CPU_s','actor_CPU_s','reset_wall_s','raw_step_render_wall_s','raw_contact_observer_wall_s','capture_wall_s','journal_wall_s','artifact_wall_s'];cost=dict(stage=367,new_wrapper_actions=used,new_candidate_runs=1,new_baseline_runs=0,new_environment_resets=1,new_actor_act_calls=b['actor_act_calls'],new_actor_commit_calls=b['actor_commit_calls'],actor_resets=1,episode_cap=2000,reservation_from_existing_research=2000,additional_research=0,new_cached_actor_calls=0,new_standalone_diagnostic_calls=0,new_native_auxiliary=0,new_source_physics_rollout_ticks=0,new_learning_fits=0,new_tuning=0,new_paid_resources=0,raw_step_ticks=r['raw_step_ticks'],raw_reset_ticks=r['raw_reset_ticks'],measurements={k:r[k] for k in measures},actual_cumulative_wrapper_actions=1291467+used,research_remaining=21938-used,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1397405,unused_episode_reservation=2000-used,historical359_reexecuted_or_recounted=False,technical_error=None,scope='Only367freshactual365episodecharged. Posthocsavedlineageauditaddsnoactor/native. Rawstepincludesrender; componenttimersdistinct. Coding/registration/closure/gitnotfullytimed.')
 support=dict(known_supported_direct_contexts=direct,known_birth_supported_retained_contexts=retained,supported_direct_losses=sum(x['kind']=='direct' for x in losses),supported_retained_losses=sum(x['kind']=='retained' for x in losses),losses=losses,missing_birth_GT_direct=missingd,missing_birth_GT_retained=missingr,low_births=low,retained_exclusions=held,newly_preserved_low_retained=restored,gate_passed=not losses,scope='Onlythisactualepisode;birthcirclecorrespondenceposthoc,notsemanticmaterialorocclusiontruth.')
 report=dict(stage=367,candidate_archive_sha256=p['config']['archive_sha256'],candidate_modified=False,official_outcome=outcome,stop_reason=r['stop_reason'],comparison_qualification=gate,historical359_357=dict(reused_not_new=True,outcome=historic,lap_difference_new_minus_historical_ms=delta,same_case_init_RNG_environment_runtime_models_and_observer=True),first_differences=dict(diagnostic_support_metadata=first('support_record'),routing_membership=r['first_routing_membership_difference'],path=first('pixel_path'),target=firsttarget,semantic_output=r['first_semantic_output_difference'],full_control=r['first_full_control_difference'],scope='Newpositive_historyfielddiagnosticdifferenceisreportedseparately. Striponlythisfieldfororiginalsupportcomparison; originalstateprojectionexcludesagentpickledigest.'),support_audit=support,positive_history_audit=dict(N2_birth121=birth121,N2_retained121_life=core,N2_critical127to129=critical,all_positive_transfer_edges=len(edges),ambiguous_transfer_edges=sum(e['ambiguous'] for e in edges),confirmed_distinct_supported_fixture_transfers=sum(e['confirmed_distinct_supported_fixture_transfer'] for e in edges),ambiguous_low_birth_edges=sum(e['ambiguous'] and e['low_birth'] for e in edges),metadata_reconstructed_inputs=used,prior365_62ambiguous_edges_remain_unresolved=True,prior365_missing_GT_direct12_retained16_remain_unresolved=True,scope='Oneknownactualconditiondoesnotresolvepriorcacheuncertainty; GTnotruntimefeature.'),finish=dict(qualification_raw_time_s=r['finish']['finish_qualified_time_s'],center_crossing_raw_time_s=r['finish']['finish_time_s'],declaration_raw_time_s=r['finish']['raw_time'],postreset_start_time_s=r['postreset_start_time'],official_lap_ms=r['lap_ms']),cost=cost,promotion=False,new_DEV_opening=False,new_HOLDOUT_opening=False,new_SEALED_opening=False,limits=['Oneactual365N2episodeonly;not18condition365evaluation. Historical35718/18andoriginalretainedfailureremainpreservedseparately.', 'No newpairedbaseline orisolatedwhole-populationcausality. Fullcommand/pixel/physics/accessRNGmatchingcheckedwherecommon; hidden solver/OpenCV RNG/warmstart/islandstate notfullycaptured.', 'Existing62ambiguousedgesandmissingGTremainunknown; unique2mdedupnottrueobjectidentity, unseenocclusionsandaliasingunproven. No othercandidate,splitopening,fit,tuningorretry.'],next_step='Preservefixed365andcondition-specificevidence; no automaticnextworldepisode,budgetextensionorpromotion.')
 assert read(R/'stage366/plan.json')['config']['archive_sha256']==p['config']['archive_sha256']
 report['actual365_measured_conditions']=['T29510','N2']
 assert sha(R/'stage296/submission296.zip')=='0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937' and sha(R/'stage296/champion-manifest.json')=='b92fe5307a491bfb9d1f5081bf97c9c1d4646dcf9c8511fb169bc48c8f9349e5'
 for name in ['DEV','screen-opening.json','DEV-opened-by309.json']:assert not (R/'stage297'/name).exists()
 save(D/'positive-transfer-edges-private.json',edges);save(D/'cost.json',cost);save(D/'summary-private.json',report);save(G/'retry/episode367_result.json',report);save(D/'final-report-verification.json',dict(passed=True,actual365episode=True,historical357_not_new=True,known_support_gate=not losses,N2_birth121_no_positive_history=bool(birth121 and not birth121[0]['positive_history']),N2critical_exclusion_verified=len(critical)==3 and all(not x['routed'] for x in critical),uncertainty_preserved=True,research_remaining=21938-used,reserve=84000))
 v.update(version=383,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v382.json'),prior_budget_sha256=sha(R/'project-effective-budget-v382.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage367_new_wrapper_actions=used);assert not (R/'project-effective-budget-v383.json').exists();save(R/'project-effective-budget-v383.json',v)
 ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==367 for s in ledger.read_text().splitlines())
 with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
 print(json.dumps(dict(outcome=outcome,delta_ms=delta,support=support,positive_history=report['positive_history_audit'],first_differences=report['first_differences'],cost=cost)),flush=True)
if __name__=='__main__':close(Path(sys.argv[1]).resolve())
