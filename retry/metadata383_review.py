"""Status and existing manifest/exposure metadata only; no condition execution."""
import datetime,hashlib,json,os,subprocess,sys,time
from pathlib import Path
G=Path(__file__).resolve().parent.parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,obj):
 p=Path(p);t=p.with_suffix(p.suffix+'.tmp')
 with t.open('x') as f:
  os.chmod(t,0o600);json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 t.replace(p)
def stat(p):
 s=Path(p).stat();return dict(size=s.st_size,mtime_ns=s.st_mtime_ns)
def duplicate_keys(path):
 duplicates=[]
 def pairs(values):
  result={}
  for k,v in values:
   if k in result:duplicates.append(k)
   result[k]=v
  return result
 json.loads(Path(path).read_text(),object_pairs_hook=pairs)
 return len(duplicates)
def active():
 found=[]
 for line in subprocess.check_output(['ps','-eo','pid=,stat=,comm=,args='],text=True).splitlines():
  fields=line.split(None,3)
  if len(fields)<4:continue
  pid,state,comm,args=fields
  if state.startswith('Z'):continue
  if int(pid)==os.getpid() or 'metadata383_review' in args:continue
  if comm.startswith('python') and any(x in args for x in ['-m retry.','/retry/','worker.py']):found.append(int(pid))
  elif comm.startswith('pixel-read-sand'):found.append(int(pid))
 return found

def run(root):
 d=root/'stage383';assert not d.exists(),'383 already exists; inspect instead of rerun'
 vpath=root/'project-effective-budget-v400.json';v=read(vpath)
 keys=['actual_cumulative_wrapper_actions','research_remaining','final_reserved_actions','final_reserve_used','B_operating_cap']
 assert [v[k] for k in keys]==[1312121,35943,84000,0,1432064]
 assert not active(),'Unexpected live experiment; do not start metadata closure'
 champ=root/'current-champion.json';manifest=root/'stage296/champion-manifest.json';ledger=root/'protected-query-ledger-v1.json'
 assert sha(champ)==sha(manifest)=='b92fe5307a491bfb9d1f5081bf97c9c1d4646dcf9c8511fb169bc48c8f9349e5'
 c=read(champ);assert c['adopted_after_stage']==296 and c['G5_SEALED']=='PENDING_CLOSED'
 assert sha(c['archive_path'])==c['archive_sha256']
 assert sha(c['immediate_rollback']['archive_path'])==c['immediate_rollback']['archive_sha256']
 assert read(ledger)['SEALED']==dict(episodes_used=0,future_episode_queries_this_phase_max=0)
 markers=list(root.rglob('SEALED*.opened'));assert not markers
 p382=read(root/'stage382/plan.json')
 original=root/'preregistered-v1.json'
 assert stat(original)==p382['closed_files_stat_only'][str(original)]
 # Stored hash metadata, not a new hash/read of original condition content.
 stored_hash=(root/'preregistered-v1.sha256').read_text().split()[0]
 parent=read(root/'stage2/preregistered-v1.json')['parent_plan_sha256']
 assert stored_hash==parent and len(stored_hash)==64
 excluded={str(root/n):(root/n).stat().st_mtime_ns for n in ['stage372','stage297']}
 protected={str(p):sha(p) for p in [champ,manifest,ledger,vpath,root/'stage373/candidate365-rejected-locked.json',G/'retry/final382_contract.md',G/'retry/final382_result.json']}
 sources=[Path(__file__),root/'preregistered-v1.sha256',root/'stage2/preregistered-v1.json',root/'stage296/exclusion-final.json',root/'stage382/exposure-metadata.json',root/'stage382/verification.json',root/'stage16/split-review-ko.txt']
 hashes={str(p):sha(p) for p in sources}
 d.mkdir(mode=0o700);start,cpu=time.perf_counter(),time.process_time()
 metadata=read(root/'stage296/exclusion-final.json');counts={}
 for k,values in metadata.items():
  if k.startswith('excluded_') and isinstance(values,list):
   n=len({json.dumps(x,sort_keys=True,separators=(',',':')) for x in values})
   counts[k]=dict(entries=len(values),unique=n,duplicate_entries=len(values)-n)
 keychecks={name:duplicate_keys(root/path) for name,path in [('current_manifest','current-champion.json'),('champion_manifest','stage296/champion-manifest.json'),('query_ledger','protected-query-ledger-v1.json'),('historical_exclusions','stage296/exclusion-final.json')]}
 assert all(n==0 for n in keychecks.values())
 result=dict(stage=383,request_status='No earlier383request/artifact recorded here; received and completed metadata-only task from current parent message',
  active_experiment_or_actor_processes=0,prior383_artifact_exists=False,new_experiment=False,
  historical_orphan_sandbox_zombies=2,zombie_scope='PID1 adopted exited Z processes about5days old, no live computation; not current381 actor and not reapable by this process',
  SEALED_count_from_existing_contract=16,SEALED_episodes_used=0,SEALED_phase_queries_allowed=0,SEALED_opened_markers=0,
  original_manifest_content_read_or_rehashed=False,original_manifest_stat_unchanged_since382=True,
  original_stored_hash_metadata_matches_stage2_parent_reference=True,
  metadata_duplicate_JSON_keys=keychecks,historical296_exclusion_internal_duplicates=counts,
  current_and296_manifest_identical_intentional_alias=True,
  historical_exclusion_scope='Existing296snapshot only; internal list uniqueness is not SEALED intersection proof',
  current_SEALED_vs_all_exposure_intersection_verified=False,
  blocker='No separately keyed opaque SEALED16 identity/geometry-to-current-full-exposure receipt found in inspected metadata inventory. Cannot infer current intersection0 from pooled blacklist uniqueness, unopened markers or query0.',
  remaining_action='Produce private aggregate opaque-identity/exposure intersection receipt under an explicit metadata boundary; do not regenerate conditions, open performance, substitute seeds or declare pass without it',
  no372_individual_data_or_newsplit=True,champion296_and_contract382_preserved=True,
  reserve84000_preserved=True,allocation382_proposal=dict(primary296=32000,unused=52000,automatic_retry=0),
  research_program_terminated=False)
 cost=dict(stage=383,new_wrapper_actions=0,new_actor_calls=0,new_environment_resets=0,new_environment_creation=0,new_model_forward_calls=0,new_learning_fits=0,new_source_physics_rollout_ticks=0,new_condition_observation_queries=0,new_performance_queries=0,new_paid_resources=0,audit_wall_s=time.perf_counter()-start,audit_CPU_s=time.process_time()-cpu,scope='Existing manifest/hash-reference/ledger/exclusion metadata assembly; inventory/review/report/git not fully timed',**{k:v[k] for k in keys})
 result['cost']=cost
 plan=dict(stage=383,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_hashes=hashes,protected_hashes=protected,original_manifest_stat_only=stat(original),excluded_directory_stats=excluded,scope='Metadata only, no environment/policy imports or calls; no original SEALED condition payload read, no performance/observations')
 save(d/'plan.json',plan);save(d/'cost.json',cost);save(d/'summary.json',result);save(G/'retry/metadata383_result.json',result)
 assert all(sha(p)==h for p,h in hashes.items());assert all(sha(p)==h for p,h in protected.items())
 assert stat(original)==plan['original_manifest_stat_only'];assert all(Path(p).stat().st_mtime_ns==n for p,n in excluded.items());assert not active()
 lines=root/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==383 for s in lines.read_text().splitlines())
 v.update(version=401,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(vpath),prior_budget_sha256=sha(vpath),cost_path=str(d/'cost.json'),cost_sha256=sha(d/'cost.json'),B_increment=0,stage383_new_wrapper_actions=0)
 assert not (root/'project-effective-budget-v401.json').exists();save(root/'project-effective-budget-v401.json',v)
 with lines.open('a') as f:f.write(json.dumps(cost)+'\n')
 save(d/'verification.json',dict(passed=True,protected_source_contract382_unchanged=True,original_condition_manifest_stat_only_unchanged=True,excluded_directories_unchanged=True,budget_unchanged=True,unique_cost_line=True,SEALED_not_opened=True,current_intersection_not_claimed=True))
 print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
