"""Read old TRAIN evidence and runtime metadata only; no actor or environment."""
import datetime,json,sys,time,zipfile,hashlib
from pathlib import Path
from retry.path271_run import read,save,sha
G=Path(__file__).resolve().parent.parent

def rows(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]
def run(R):
 D=R/'stage373';assert not D.exists();D.mkdir(mode=0o700);start,cpu=time.perf_counter(),time.process_time();v=read(R/'project-effective-budget-v390.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'],v['B_operating_cap'])==(1306464,41600,84000,0,1432064)
 # No content access to stage372, the exposed297case set, HOLDOUT or SEALED.
 excluded=[R/'stage372',R/'stage297'];excluded_stats={str(p):dict(mtime_ns=p.stat().st_mtime_ns) for p in excluded};cfg=read(R/'stage334/configs-private.json');sources=[G/'retry/review373_audit.py',R/'stage334/configs-private.json',R/'project-effective-budget-v390.json',R/'current-champion.json',R/'stage296/champion-manifest.json',R/'protected-query-ledger-v1.json']
 names=['diagnosis300','guard301','targetloss302','guard303','wheel304','reference305','pedal306','diagnosis307','phase308','speed309','route310','endpoints311','coupling312','predictor313','structure314','paired315','asymmetric316','asym317','state318','shield319','shield320','pulse321','brake322','motion323','history324','dynamics325','extrapolation326','intervention327','hybrid328','h1_329','h1_330','pedal331','diagnostic332','steering333','fallback334','closed335','episode336','episode337','probe338','lineage339','confidence341','support342','source344','compare347','package349','guard357','episode361','evaluation363','history365','evaluation368','dev370']
 for n in names:
  p=G/'retry'/(n+'_result.md')
  if p.exists():sources.append(p)
 for n in ['fallback334_stage','fallback334_run','fallback334_close','closed335_stage','episode336_stage','episode337_stage','history365_stage','guard357_stage']:
  p=G/'retry'/(n+'.py')
  if p.exists():sources.append(p)
 fingerprints={};archives={}
 for h in ['OFF','ON']:
  for f in ['OFF','ON']:
   c=cfg[h][f];assert sha(c['archive_path'])==c['archive_sha256'];sources.append(Path(c['archive_path']))
   with zipfile.ZipFile(c['archive_path']) as z:
    assert all(hashlib.sha256(z.read(n)).hexdigest()==expected for n,expected in c['members_sha256'].items());model=z.read('retry/h1_330_model.py').decode();assert ('ENABLED = True' in model or 'ENABLED=True' in model)==(h=='ON')
   fingerprints[(c['members_sha256']['retry/h1_330_model.py'],c['members_sha256']['retry/temporal_agent.py'])]='H'+str(int(h=='ON'))+'F'+str(int(f=='ON'));archives['H'+str(int(h=='ON'))+'F'+str(int(f=='ON'))]=c['archive_sha256']
 # Repacked ZIPs/workers are matched by loaded policy member hashes, not filename.
 inventory=[];readyfiles=0;unknown_fallback=[]
 f1=cfg['OFF']['ON']['members_sha256']['retry/temporal_agent.py']
 for stage in range(334,372):
  root=R/f'stage{stage}'
  if not root.exists():continue
  for path in sorted(root.rglob('*ready*.json')):
   if any('SEALED' in x or 'HOLDOUT' in x or 'freshDEV' in x or x=='registration' for x in path.parts):continue
   m=read(path);mods=m.get('policy_module_sha256')
   if not isinstance(mods,dict):continue
   readyfiles+=1;signature=(mods.get('retry.h1_330_model'),mods.get('retry.temporal_agent'));cell=fingerprints.get(signature)
   if mods.get('retry.temporal_agent')==f1 and cell is None:unknown_fallback.append(str(path))
   if cell is None:continue
   sources.append(path);resultpath=path.parent/'result.json';native=False;summary=None
   if resultpath.exists():
    result=read(resultpath);sources.append(resultpath);native=isinstance(result.get('native_actions'),int) and result['native_actions']>0 and result.get('raw_step_ticks',0)>0;summary={k:result.get(k) for k in ['native_actions','raw_step_ticks','completed','actual_DNF','censored','technical_error','lap_ms']}
   inventory.append(dict(ready_path=str(path),stage=stage,cell=cell,actual_native_sibling=native,result_path=str(resultpath) if resultpath.exists() else None,result_summary=summary,nominal_member_sha256=mods.get('retry.nominal238_base'),support_member_loaded='retry.support342_logic' in mods))
 assert not unknown_fallback,unknown_fallback
 # All six original296 TRAIN cached paths, including both failing/successful roads.
 cache=[]
 for key in ['T2950','T2953','T2956','T2959','O0','O2']:
  a=rows(R/'stage334'/key/'OFF-private.jsonl');b=rows(R/'stage334'/key/'ON-private.jsonl');assert len(a)==len(b)
  diff=[i+1 for i,(x,y) in enumerate(zip(a,b)) if x['action']!=y['action']];steer=[i+1 for i,(x,y) in enumerate(zip(a,b)) if x['action'][0]!=y['action'][0]];pathdiff=[i+1 for i,(x,y) in enumerate(zip(a,b)) if x['pixel_path']!=y['pixel_path']];firstcontact=next((x['index']+1 for x in a if x['collision_after']),None)
  cache.append(dict(TRAIN=key,rows=len(a),changed_returned_controls=len(diff),first_control_difference=diff[0] if diff else None,changed_steering=len(steer),first_steering_difference=steer[0] if steer else None,changed_paths=len(pathdiff),first_path_difference=pathdiff[0] if pathdiff else None,original_first_contact=firstcontact,first_change_before_original_contact=bool(diff and firstcontact and diff[0]<firstcontact),scope='Previouslycomputed334fixed296pixels;storedphysicalcommandscommitted,notnewclosedloop/nopolicycalls.'))
  sources += [R/'stage334'/key/(m+'-private.jsonl') for m in ['OFF','ON']]
 native={cell:[x for x in inventory if x['cell']==cell and x['actual_native_sibling']] for cell in archives};assert not native['H0F1'];assert native['H1F1']
 prior=read(G/'retry/fallback334_result.json');assert prior['verification']['OFF_actor_rows_reproduced']==1970 and prior['verification']['shared_accepted_optical_matrices_exact']==596
 protected={str(p):sha(p) for p in [R/'current-champion.json',R/'stage296/champion-manifest.json',R/'protected-query-ledger-v1.json',R/'project-effective-budget-v390.json']};assert read(R/'current-champion.json')['adopted_after_stage']==296 and read(R/'protected-query-ledger-v1.json')['SEALED']['episodes_used']==0
 plan=dict(stage=373,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='ReadoldTRAIN/publicoldDEVreports,334savedoutputJSONand334-371readymodule/resultmetadataonly. No372contents/trajectories/conditionfailuresread,297casesorHOLDOUT/SEALEDcontents. No actor/env/routing/model/learning calls.365rejectedbyexplicitparentinstructiononly.',source_hashes={str(p):sha(p) for p in sources},protected_hashes=protected,excluded_directory_stats=excluded_stats)
 save(D/'plan.json',plan);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'runtime-inventory-private.json',dict(ready_files_examined=readyfiles,records=inventory,unknown_exact_fallback_signature_paths=unknown_fallback));save(D/'old-TRAIN-cache-summary.json',cache)
 report=dict(stage=373,review_only=True,candidate365_status='Rejected;fixedbyparent372failuredecision,notusedfornewdesign.',champion296_unchanged=True,new_simulation=0,new_actor_calls=0,new_environment_resets=0,new_routing_calls=0,new_model_calls=0,new_fits=0,read_372_case_results_or_trajectories=False,archive_cells=archives,readiness_metadata_inventory=dict(stages=[334,371],ready_files_examined=readyfiles,matching_records=len(inventory),native_records_by_exact_loaded_cell={cell:len(xs) for cell,xs in native.items()},unknown_exact_fallback_signatures=0,scope='Exactloadedmodel+temporalhashsignaturewithinrecordedinventory;notallpossiblehistoricalpatchesorproofeveryunusedcombinationwouldimprove.349/357/365temporalmembersdifferandarehandledbytheirseparatelineageevidence.'),old_TRAIN_fixed_pixel_fallback_only_cache=cache,missing_cell=dict(cell='H0F1R0',meaning='Existing334fallbackON,H1OFF,birthroutingOFF;oldTRAINcacheexists,butnoactualepisodeforthisexactloadedcellfound.',new_policy_rule=False,existing_rule_unmeasured_closedloop=True,not_335_337='ThoseactualN2episodesuseH1ON/fallbackON.',minimal_composition_benefit_not_proven=True),prior_safety_counterexamples_preserved=True,protected_splits_opened=False,SEALED16_pending_preserved=True,research_remaining=41600,final_reserved_actions=84000)
 cost=dict(stage=373,new_wrapper_actions=0,new_actor_calls=0,new_environment_resets=0,new_routing_calls=0,new_model_calls=0,new_learning_fits=0,new_source_physics_rollout_ticks=0,new_paid_resources=0,audit_wall_s=time.perf_counter()-start,audit_CPU_s=time.process_time()-cpu,actual_cumulative_wrapper_actions=1306464,research_remaining=41600,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1432064,scope='Read-onlymetadata/savedJSONarithmetic;noactor/env/imports. Coding/report/gitnotfullytimed. No budgetgrant/reservation.')
 report['cost']=cost
 assert all(sha(p)==h for p,h in plan['protected_hashes'].items());assert all(p.stat().st_mtime_ns==excluded_stats[str(p)]['mtime_ns'] for p in excluded)
 save(D/'summary-private.json',report);save(D/'cost.json',cost);save(G/'retry/review373_result.json',report);save(D/'final-report-verification.json',dict(passed=True,no_native_actor_fit=True,no_372_content_reads=True,known_ablation_gap_not_duplicate=True,protected_and_budget_unchanged=True))
 v.update(version=391,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v390.json'),prior_budget_sha256=sha(R/'project-effective-budget-v390.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,stage373_new_wrapper_actions=0);assert not (R/'project-effective-budget-v391.json').exists();save(R/'project-effective-budget-v391.json',v)
 ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==373 for s in ledger.read_text().splitlines())
 with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
 print(json.dumps(dict(inventory=report['readiness_metadata_inventory'],TRAINcache=cache,cost=cost)),flush=True)
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
