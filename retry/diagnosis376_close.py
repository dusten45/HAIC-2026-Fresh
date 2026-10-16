"""Posthoc saved-input/pose diagnosis; never instantiate a simulator."""
import datetime,json,math,statistics,time,sys
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.fallback334_math import advance,rotation
from retry.fallback334_metrics import centers
from retry.confidence341_run import label
G=Path(__file__).resolve().parent.parent

def rows(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]
def stats(v):return dict(count=len(v),mean=statistics.mean(v) if v else None,median=statistics.median(v) if v else None,p95=float(np.quantile(v,.95)) if v else None,max=max(v) if v else None)
def spans(indices):
 out=[]
 for n in indices:
  if out and n==out[-1][1]+1:out[-1][1]=n
  else:out.append([n,n])
 return out

def close(R):
 D=R/'stage376';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert not (D/'cost.json').exists();start,cpu=time.perf_counter(),time.process_time()
 for f,h in p['source_hashes'].items():assert sha(f)==h,f
 replay=read(D/'replay-result.json');assert replay['passed'];a=rows(D/'296/records-private.jsonl');b=rows(D/'374/records-private.jsonl');actual=rows(p['actual_trace']);old=rows(p['baseline_trace']);assert len(a)==len(b)==len(actual)==303 and len(old)==237
 fields=dict(tracker_before=lambda x:x['response']['tracker_record']['before'],tracker_after=lambda x:x['response']['tracker_record']['after'],optical_matrix=lambda x:x['response']['tracker_record']['affine'],optical_reason=lambda x:x['response']['tracker_record']['optical_reason'],path=lambda x:x['response']['pixel_path'],target=lambda x:x['response']['features'][:3],features=lambda x:x['response']['features'],min_hazard_distance=lambda x:x['response']['features'][12],near_flag=lambda x:x['response']['features'][8],hazard_count=lambda x:x['response']['features'][11],pre_memory=lambda x:x['pre_state']['previous_steer'],post_memory=lambda x:x['commit']['memory'],full_control=lambda x:x['response']['action'],steering=lambda x:x['response']['action'][0],pedals=lambda x:x['response']['action'][1:])
 differences={k:[i+1 for i,(x,y) in enumerate(zip(a,b)) if f(x)!=f(y)] for k,f in fields.items()};first={k:(v[0] if v else None) for k,v in differences.items()};sameoptical=[(x['response']['tracker_record']['affine'],y['response']['tracker_record']['affine']) for x,y in zip(a,b) if x['response']['tracker_record']['affine'] is not None and y['response']['tracker_record']['affine'] is not None];matrix_mismatches=sum(x!=y for x,y in sameoptical)
 actualfirst={name:next((i+1 for i,(x,y) in enumerate(zip(old,actual)) if f(x,y)),None) for name,f in dict(full_control=lambda x,y:x['action']!=y['executed'],steering=lambda x,y:x['action'][0]!=y['executed'][0],pedals=lambda x,y:x['action'][1:]!=y['executed'][1:],features=lambda x,y:x['features']!=y['features'],post_memory=lambda x,y:x['memory']!=y['nominal_memory'],collision=lambda x,y:x['collision']!=y['collision']).items()}
 fixed296_vs_historical_first=next((i+1 for i,(x,y) in enumerate(zip(a,old)) if x['response']['action']!=y['action'] or x['response']['features']!=y['features'] or x['commit']['memory']!=y['memory']),None)
 first_contact=next((x['step'] for x in actual if x['collision']),None)
 intervals=[];points=[];nodes=[];coordinate_maxerr=0.;event=[]
 for i,x in enumerate(actual):
  t=x['tracker'];reconstructed,lineage,transported=advance(t['before'],t['direct'],t['affine'],t['previous_yaw'],t['current_yaw'],t['current_speed'],True);off,off_lineage,off_transport=advance(t['before'],t['direct'],t['affine'],t['previous_yaw'],t['current_yaw'],t['current_speed'],False);assert np.allclose(np.asarray(reconstructed).reshape(-1,4),np.asarray(t['after']).reshape(-1,4),rtol=0,atol=1e-12)
  if i:
   previous=actual[i-1]['pre_physical'];current=x['pre_physical'];hp=previous['hull'];hc=current['hull'];delta=float(math.atan2(math.sin(hc['angle']-hp['angle']),math.cos(hc['angle']-hp['angle'])));displacement=rotation(-hp['angle'])@(np.asarray(hc['position'])-hp['position']);oldcenters=centers(previous);newcenters=centers(current);exact=(rotation(-delta)@(oldcenters-displacement).T).T;coordinate_maxerr=max(coordinate_maxerr,float(np.max(np.abs(exact-newcenters))))
   if t['before'] and t['affine'] is None:
    hud_delta=.08*(t['previous_yaw']+t['current_yaw'])/2;hud_d=np.array([0.,t['current_speed']*.08]);intervals.append(dict(step=i+1,precontact=first_contact is None or i+1<=first_contact,hud_delta=hud_delta,GT_delta=delta,yaw_absolute_error=abs(hud_delta-delta),GT_displacement_old_body=displacement.tolist(),hud_displacement=hud_d.tolist(),displacement_norm_error=float(np.linalg.norm(displacement-hud_d)),lateral_displacement_abs=abs(float(displacement[0])),forward_displacement_error=float(hud_d[1]-displacement[1]),points=len(t['before'])))
    event.append(dict(step=i+1,before=t['before'],ON_after=t['after'],OFF_after_same_ON_before=off,paired296_before=a[i]['response']['tracker_record']['before'],ON_previous_memory=b[i]['pre_state']['previous_steer'],OFF_previous_memory=a[i]['pre_state']['previous_steer']))
    for j,h in enumerate(t['before']):
     if nodes[j]['label']!='fixture_supported':continue
     identity=nodes[j]['fixture_index'];point=np.array(h[:2]);target=newcenters[identity];variants=dict(OFF=point-hud_d,ON=rotation(-hud_delta)@(point-hud_d),GT_yaw_only=rotation(-delta)@(point-hud_d),GT_displacement_only=rotation(-hud_delta)@(point-displacement),GT_exact=rotation(-delta)@(point-displacement));points.append(dict(step=i+1,precontact=first_contact is None or i+1<=first_contact,age=h[3],errors={k:float(np.linalg.norm(v-target)) for k,v in variants.items()}))
  newnodes=[]
  for parent in lineage:
   if parent>=0:node=nodes[parent]
   else:
    lab,identity=label(t['direct'][-parent-1],x['pre_physical']);node=dict(label=lab,fixture_index=identity)
   newnodes.append(node)
  nodes=newnodes
 aggreg={}
 for name,keep in [('all',lambda q:True),('precontact',lambda q:q['precontact']),('postcontact',lambda q:not q['precontact'])]:
  ir=[q for q in intervals if keep(q)];pr=[q for q in points if keep(q)];aggreg[name]=dict(fallback_intervals=len(ir),fixture_birth_supported_point_transports=len(pr),yaw_absolute_error_rad=stats([q['yaw_absolute_error'] for q in ir]),displacement_norm_error_m=stats([q['displacement_norm_error'] for q in ir]),lateral_displacement_abs_m=stats([q['lateral_displacement_abs'] for q in ir]),errors_m={mode:stats([q['errors'][mode] for q in pr]) for mode in ['OFF','ON','GT_yaw_only','GT_displacement_only','GT_exact']})
 firstfallback=intervals[0]['step'] if intervals else None;critical_steps=sorted(set(n for n in [firstfallback,first['tracker_after'],first['features'],first['path'],first['steering'],first['pre_memory'],first_contact] if n is not None));critical=[]
 for n in critical_steps:
  x,y=a[n-1],b[n-1];tx,ty=x['response']['tracker_record'],y['response']['tracker_record'];critical.append(dict(step=n,both_optical=tx['affine'] is not None and ty['affine'] is not None,OFF_optical_reason=tx['optical_reason'],ON_optical_reason=ty['optical_reason'],before_hazards_equal=tx['before']==ty['before'],after_hazards_equal=tx['after']==ty['after'],OFF_hazard_count=len(tx['after']),ON_hazard_count=len(ty['after']),OFF_min_distance=x['response']['features'][12],ON_min_distance=y['response']['features'][12],pre_memory_equal=x['pre_state']['previous_steer']==y['pre_state']['previous_steer'],post_memory_equal=x['commit']['memory']==y['commit']['memory'],path_equal=x['response']['pixel_path']==y['response']['pixel_path'],target_equal=x['response']['features'][:3]==y['response']['features'][:3],OFF_action=x['response']['action'],ON_action=y['response']['action']))
 report=dict(stage=376,read_only_diagnosis=True,policies_immutable=True,new_native_actions=0,new_environment_resets=0,new_candidate_changes=0,no372materials_or_newsplit=True,historical_actual_first_differences=actualfirst,fixed_input_first_differences=first,first_actual374_fallback=firstfallback,fixed_tracker_difference_spans=spans(differences['tracker_after']),fixed296_vs_historical_first_common_output_mismatch=fixed296_vs_historical_first,shared_accepted_optical_matrices=len(sameoptical),shared_accepted_optical_matrix_mismatches=matrix_mismatches,critical_fixed_input_snapshots=critical,posthoc_motion=aggreg,coordinate_exact_GT_static_center_max_error=coordinate_maxerr,old296_snapshot_gap='Historical296237tracehascontrols/features/memoryonly,nopixels/tracker/GTpose/fullRNG. Counterfactual303same374pixelsisnot296actualtrajectory/score,especiallyafter139.',GT_scope='AllGTcomparisonsreadonlyposthoc. GT_yaw/displacementonlyarecomponentdiagnostics,notlegalproposedpoliciesornewcandidate. Birthfixtureidentitiesfixed,unknownexcludedfromerrorandnotcalledfalse.',causal_limit='Onlyfixedinputeffectsidentified. Firstfallbackandfirstoutputdifferencenotautomaticallycausetheactual202contact/303retirement. No freshsimulationorstate-sufficiencetest;nomemory/coordinateerrorclaimedwithoutproof.')
 save(D/'motion-intervals-private.json',intervals);save(D/'fixture-point-error-private.json',points);save(D/'fallback-events-private.json',event);save(D/'diagnosis-private.json',report)
 v=read(R/'project-effective-budget-v393.json');c=replay['counters'];cost=dict(stage=376,new_wrapper_actions=0,new_environment_resets=0,new_actor_act_calls=c['actor_act_calls'],new_actor_commit_calls=c['actor_commit_calls'],stored_pixel_resets=c['pixel_resets'],new_source_physics_rollout_ticks=0,new_learning_fits=0,new_candidate_modifications=0,new_paid_resources=0,actor_act_cap=606,actor_commit_cap=606,pixel_reset_cap=2,replay_wall_s=replay['wall_s'],replay_runner_CPU_s=replay['runner_CPU_s'],actor_CPU_s=sum(q['actor_CPU_s'] for q in replay['receipts']),posthoc_analysis_wall_s=time.perf_counter()-start,posthoc_analysis_CPU_s=time.process_time()-cpu,actual_cumulative_wrapper_actions=1311581,research_remaining=36483,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1432064,scope='Fixedsavedinputs/JSON/posematrixalgebraonly,nosimulatorornewpolicy. Coding/build/report/gitnotfullytimed.')
 assert c['actor_act_calls']==c['actor_commit_calls']==606 and c['pixel_resets']==2 and not c['new_native_actions'] and not c['new_environment_resets'];assert all(q['reaping']['process_reaped'] and q['reaping']['actor_pids_absent'] for q in replay['receipts'])
 for f,h in p['protected_hashes'].items():assert sha(f)==h,f
 assert all(Path(f).stat().st_mtime_ns==h for f,h in p['excluded_directory_stats'].items());assert not list(R.rglob('SEALED*.opened'))
 report['cost']=cost;save(D/'summary-private.json',report);save(D/'cost.json',cost);save(G/'retry/diagnosis376_result.json',report);save(D/'final-report-verification.json',dict(passed=True,candidate374_full_saved_reproduction=True,immutable296_and374=True,source_hashes_exact=True,zero_native_and_candidatechanges=True,calls606_reset2=True,known_snapshot_limit_disclosed=True,protected_budget_and_champion_unchanged=True))
 v.update(version=394,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v393.json'),prior_budget_sha256=sha(R/'project-effective-budget-v393.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,stage376_new_wrapper_actions=0);assert not (R/'project-effective-budget-v394.json').exists();save(R/'project-effective-budget-v394.json',v)
 ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==376 for s in ledger.read_text().splitlines())
 with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
 print(json.dumps(dict(first_actual=actualfirst,first_fixed=first,fallback=firstfallback,optical_shared=len(sameoptical),optical_mismatch=matrix_mismatches,tracker_spans=report['fixed_tracker_difference_spans'],motion=aggreg,cost=cost)),flush=True)
if __name__=='__main__':close(Path(sys.argv[1]).resolve())
