"""Close seed-only metadata audit; no simulator/policy/performance access."""
import datetime,hashlib,json,os,sys,time
from pathlib import Path
G=Path(__file__).resolve().parent.parent

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p=Path(p);t=p.with_suffix(p.suffix+'.tmp')
 with t.open('x') as f:
  os.chmod(t,0o600);json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 t.replace(p)
def run(root):
 d=root/'stage383/seed-followup';assert not (d/'cost.json').exists(),'No duplicate closure'
 vpath=root/'project-effective-budget-v401.json';v=read(vpath);keys=['actual_cumulative_wrapper_actions','research_remaining','final_reserved_actions','final_reserve_used','B_operating_cap']
 assert [v[k] for k in keys]==[1312121,35943,84000,0,1432064]
 protected={str(p):sha(p) for p in [root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json',root/'stage373/candidate365-rejected-locked.json',G/'retry/final382_contract.md',G/'retry/final382_result.json',vpath]}
 base=read(root/'stage383/plan.json')
 assert all(sha(p)==h for p,h in base['protected_hashes'].items())
 assert read(root/'protected-query-ledger-v1.json')['SEALED']==dict(episodes_used=0,future_episode_queries_this_phase_max=0)
 assert not list(root.rglob('SEALED*.opened'))
 sourcefiles=[Path(__file__),G/'retry/seed383_followup.py',G/'retry/seed383_result.md',d/'inspection-summary.json',d/'pass2/inspection-summary.json',d/'pass3/inspection-summary.json',d/'pass3/coverage-private.json',d/'pass3/source-hashes-private.json',d/'pass3/identity-rows-private.json',d/'pass3/offline101-seed-provenance-private.json']
 sources={str(p):sha(p) for p in sourcefiles}
 assert all(sha(p)==h for p,h in read(d/'pass3/source-hashes-private.json').items())
 start,cpu=time.perf_counter(),time.process_time()
 records=read(d/'pass3/identity-rows-private.json');metadata=read(d/'pass3/inspection-summary.json');coverage=read(d/'pass3/coverage-private.json')
 assert sha(root/'preregistered-v1.json')==(root/'preregistered-v1.sha256').read_text().split()[0]
 original=read(root/'preregistered-v1.json');sealed=original['split']['SEALED'];sseed={x['seed'] for x in sealed};spair={(x['track_id'],x['seed']) for x in sealed};assert len(sealed)==len(sseed)==len(spair)==16
 seed={x['seed'] for x in records};pairs={(x['track_id'],x['seed']) for x in records if x['track_id'] is not None}
 excluded=set();files={}
 for p in root.rglob('*.json'):
  if d in p.parents or p.name not in {'exclusion-snapshot.json','exclusion-after-registration.json','exclusion-final.json','diagnostic-DEV-exclusion.json','exclusions-private.json'}:continue
  x=read(p)
  if isinstance(x,dict) and isinstance(x.get('excluded_seeds'),list):
   excluded.update(y for y in x['excluded_seeds'] if isinstance(y,int));files[str(p)]=sha(p)
 unattributed=excluded-sseed-seed
 # Opaque blacklist values absent from case provenance are retained, never dropped.
 conservative=seed|unattributed
 assert not (sseed&seed) and not(spair&pairs) and not(sseed&conservative)
 assert metadata['uncovered_exposure_stages']==[] and metadata['metadata_parse_errors']==0 and metadata['unsupported_seed_containers']==0
 missing_nonsealed=excluded-sseed-conservative;assert not missing_nonsealed
 save(d/'final-identity-union-private.json',dict(SEALED_pairs=sealed,manifest_identity_rows=records,unattributed_blacklist_seeds=sorted(unattributed),conservative_seed_union=sorted(conservative),excluded_source_hashes=files,original_manifest_sha256=sha(root/'preregistered-v1.json')))
 label='383-seed-followup'
 result=dict(stage=label,metadata_only=True,seed_intersection_verified=True,seed_intersection_count=0,pair_intersection_count=0,
  SEALED_unique_seeds=16,SEALED_unique_pairs=16,metadata_files_examined=metadata['metadata_files'],manifest_identity_rows=metadata['identity_rows'],manifest_unique_seed_values=len(seed),manifest_unique_pairs=len(pairs),unattributed_blacklist_seed_values_retained=len(unattributed),conservative_exposure_seed_upper_set=len(conservative),exclusion_metadata_files=len(files),nonSEALED_exclusion_values_uncovered=0,
  exposure_stages_with_provenance=metadata['covered_exposure_stages'],uncovered_exposure_stages=[],metadata_parse_errors=0,unsupported_seed_containers=0,
  offline101_provenance='Existing contracts reference prior91/95/98 cached data; seed identities inherited without opening referenced observations/results',
  stage372_access='Frozen case manifest seed/track identity fields only, newly authorized metadata scope; no outcomes/observations/condition geometry read',
  original_manifest_access='New explicit authority permits identity fields only; no simulation, performance, terrain generation or SEALED evaluation',
  performance_queries=0,observation_queries=0,terrain_queries=0,new_simulation=False,SEALED_evaluation_opened=False,SEALED_phase_query_allowance=0,
  independence_scope='Zero shared seed and (track_id,seed) within preserved designated-cloud metadata and exposure/native-ledger coverage; conservative registrations included; not geometry equality, population independence, or evidence outside preserved workspace',
  unattributed_scope='Two opaque exclusion values lack per-episode provenance; retained as possibly exposed seeds. They are distinct from SEALED, so no false-zero removal.',
  protected_declaration_scope='SEALED seed entries in original split/exclusion blacklist are reservations, not evidence of evaluation; actual experiment manifest identities were independently compared before blacklist supplementation',
  champion296_retained=True,contract382_unchanged=True,geometry_collision_verification=False,official_server_and_new_machine_verification=False,
  final_opening_authorized=False,remaining_final_actions=['Explicit final evaluation authority and frozen query/execution/error accounting contract; no automatic opening','Report seed scope separately from untested geometry/policy generalization'],research_program_terminated=False)
 timing=read(d/'inspection-summary.json')['audit_wall_s']+read(d/'pass2/inspection-summary.json')['audit_wall_s']+metadata['audit_wall_s']
 cpu_total=read(d/'inspection-summary.json')['audit_CPU_s']+read(d/'pass2/inspection-summary.json')['audit_CPU_s']+metadata['audit_CPU_s']
 cost=dict(stage=label,new_wrapper_actions=0,new_actor_calls=0,new_environment_resets=0,new_environment_creation=0,new_model_forward_calls=0,new_learning_fits=0,new_source_physics_rollout_ticks=0,new_observation_queries=0,new_performance_queries=0,new_terrain_queries=0,new_paid_resources=0,metadata_audit_three_pass_wall_sum_s=timing,metadata_audit_three_pass_CPU_sum_s=cpu_total,close_metadata_wall_s=time.perf_counter()-start,close_metadata_CPU_s=time.process_time()-cpu,scope='Metadata passes and closure only; discovery/manual inspection/report/git not fully timed',**{k:v[k] for k in keys})
 result['cost']=cost
 save(d/'plan-final.json',dict(stage=label,source_hashes=sources,protected_hashes=protected,original_manifest_identity_access_explicitly_authorized=True,metadata_only=True,excluded_metadata_hashes=files));save(d/'cost.json',cost);save(d/'summary.json',result);save(G/'retry/seed383_result.json',result)
 assert all(sha(p)==h for p,h in protected.items());assert all(sha(p)==h for p,h in sources.items());assert all(sha(p)==h for p,h in files.items())
 ledger=root/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==label for s in ledger.read_text().splitlines())
 v.update(version=402,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(vpath),prior_budget_sha256=sha(vpath),cost_path=str(d/'cost.json'),cost_sha256=sha(d/'cost.json'),B_increment=0,stage383_seed_followup_new_wrapper_actions=0)
 assert not(root/'project-effective-budget-v402.json').exists();save(root/'project-effective-budget-v402.json',v)
 with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
 save(d/'verification.json',dict(passed=True,source_and_protected_hashes_unchanged=True,seed_and_pair_intersection_zero=True,complete_detected_stage_coverage=True,all_blacklisted_nonSEALED_seeds_in_upper_set=True,geometry_and_statistical_independence_not_claimed=True,SEALED_evaluation_not_opened=True,query_allowance_unchanged=True,budget_unchanged=True,unique_cost_line=True))
 print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
