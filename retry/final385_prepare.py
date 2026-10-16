"""Prepare disabled final adapter contract and run synthetic fixtures only."""
import datetime,hashlib,json,os,subprocess,sys,time
from pathlib import Path
G=Path(__file__).resolve().parent.parent

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p=Path(p);tmp=p.with_suffix(p.suffix+'.tmp')
 with tmp.open('x') as f:
  os.chmod(tmp,0o600);json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 tmp.replace(p)
def run(root):
 assert sys.version.split()[0]=='3.11.16' and Path(sys.executable).absolute()==G/'.venv/bin/python'
 d=root/'stage385';assert not d.exists(),'Preparation already exists, do not duplicate'
 old=root/'project-effective-budget-v403.json';v=read(old);keys=['actual_cumulative_wrapper_actions','research_remaining','final_reserved_actions','final_reserve_used','B_operating_cap']
 assert [v[k] for k in keys]==[1312121,35943,84000,0,1432064]
 b=read(root/'stage384/binding-private.json');assert b['candidate296_zip_sha256']==read(root/'current-champion.json')['archive_sha256']
 assert sha(G/'retry/final382_contract.md')==b['immutable_contract382_sha256']
 assert read(root/'protected-query-ledger-v1.json')['SEALED']==dict(episodes_used=0,future_episode_queries_this_phase_max=0)
 assert not list(root.rglob('SEALED*.opened'))
 protected={str(p):sha(p) for p in [old,root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json',root/'preregistered-v1.json',root/'stage384/binding-private.json',G/'retry/final382_contract.md',G/'retry/binding384_result.json']}
 files=[G/'retry/final385_adapter.py',G/'retry/final385_dryrun.py',Path(__file__),G/'local_runner.py',G/'env_wrapper.py',G/'damage.py',G/'retry/clean_pixel_worker.py',G/'retry/frozen_composite_runtime.py',G/'retry/pixel_sandbox_runtime.py',G/'retry/qualify_pixel_package.py']+list((G/'core').rglob('*.py'))
 sources={str(p):sha(p) for p in files}
 for rel,h in b['execution_sources'].items():assert sha(G/rel)==h
 d.mkdir(mode=0o700)
 plan=dict(stage=385,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='DISABLED_PREPARATION_NO_OPENING_AUTHORITY',
  binding384_sha256=sha(root/'stage384/binding-private.json'),frozen_execution_sources=sources,
  frozen_interpreter=str(G/'.venv/bin/python'),policy_zip_sha256=b['candidate296_zip_sha256'],
  original_manifest_reference_sha256=b['original_split_manifest_sha256'],SEALED_identity_block_reference_sha256=b['SEALED_ordered_identity_block_sha256'],
  identity_payload_reads=0,scope='Existing binding hashes only; synthetic fixture test; no Agent/env imports or real observation/performance/terrain access',
  real_episode_allowance=0,prepared_final_count=16,prepared_final_cap=32000,prepared_reserve_allocation=b['reserve'],
  mandatory_final_state='Explicit new authority reference, authorized=true, exclusive final phase and exact source/budget/cost-ledger hashes; no auto activation',
  stops='First invalid/runtime/IPC/memory/integrity/deadline failure aborts batch; no retries/resume; independent metadata recovery only',
  journal='Exclusive fresh directory, fsync hash-chained intent/commit records; pending step counted as unresolved reservation not exact native debit',
  summary='16 planned cases always retained, finish metrics before truncation classification, exact confirmed costs and unresolved upper, no DNF lap imputation')
 save(d/'execution-plan-private.json',plan);save(d/'initial-query-snapshot-private.json',dict(SEALED=dict(episodes_used=0,future_episode_queries_this_phase_max=0),actual_ledger_sha256=sha(root/'protected-query-ledger-v1.json'),actual_ledger_modified=False))
 start,cpu=time.perf_counter(),time.process_time()
 process=subprocess.run([str(G/'.venv/bin/python'),'-m','retry.final385_dryrun',str(d/'synthetic')],cwd=G,text=True,capture_output=True)
 log=d/'synthetic-run.log';log.write_text(process.stdout+process.stderr);log.chmod(0o600)
 assert process.returncode==0,process.stderr
 tests=read(d/'synthetic/verification.json');assert tests['passed'] and tests['SEALED_reads']==tests['real_native_actions']==tests['real_actor_calls']==tests['real_environment_creation']==0
 cost=dict(stage=385,new_wrapper_actions=0,new_actor_calls=0,new_environment_resets=0,new_environment_creation=0,new_model_forward_calls=0,new_learning_fits=0,new_source_physics_rollout_ticks=0,new_observation_queries=0,new_performance_queries=0,new_terrain_queries=0,new_paid_resources=0,synthetic_verification_wall_s=time.perf_counter()-start,preparation_supervisor_CPU_s=time.process_time()-cpu,scope='Final registered synthetic fixture subprocess and small preparation arithmetic; prior development fixtures/coding/review/git not fully timed',**{k:v[k] for k in keys})
 result=dict(stage=385,adapter_connected=True,synthetic_dryrun=tests,
  candidate296_unchanged=True,contracts382_384_unchanged=True,SEALED_evaluation_opened=False,query_ledger_unchanged=True,
  prepared_plan_sha256=sha(d/'execution-plan-private.json'),adapter_source_sha256=sha(G/'retry/final385_adapter.py'),dryrun_source_sha256=sha(G/'retry/final385_dryrun.py'),
  execution_ready_scope='Prepared implementation and synthetic transaction/failure tests passed; real backend never instantiated in385. Existing381 qualifies normal Agent. No claim of official-server/newmachine or untested infrastructure-failure equivalence.',
  remaining_technical_blockers=[],remaining_authority='Explicit final opening authorization with exact preparation/runtime/manifest/budget/cost hashes and exclusive final phase; this task does not grant it',
  live_authority_created=False,disabled_authority_template_only=True,automatic_retry=False,automatic_schedule_created=False,
  recovery='Journal-only report and idempotent metadata accounting, unresolved step held, no environment/actor/reset or condition replay',research_program_terminated=False,cost=cost)
 assert all(sha(p)==h for p,h in protected.items());assert all(sha(p)==h for p,h in sources.items())
 save(d/'source-and-protected-hashes.json',dict(source_hashes=sources,protected_hashes=protected));save(d/'cost.json',cost);save(d/'result.json',result);save(G/'retry/final385_result.json',result)
 ledger=root/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==385 for s in ledger.read_text().splitlines())
 v.update(version=404,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(old),prior_budget_sha256=sha(old),cost_path=str(d/'cost.json'),cost_sha256=sha(d/'cost.json'),B_increment=0,stage385_new_wrapper_actions=0)
 new=root/'project-effective-budget-v404.json';assert not new.exists();save(new,v)
 with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
 template=dict(kind='EXPLICIT_FINAL_SEALED_OPENING',authorized=False,user_authorization_reference=None,
  no_concurrent_research=True,case_count=16,native_cap=32000,binding384_sha256=sha(root/'stage384/binding-private.json'),preparation_plan_sha256=sha(d/'execution-plan-private.json'),preservation_receipt_sha256=sha(d/'source-and-protected-hashes.json'),adapter_source_sha256=sha(G/'retry/final385_adapter.py'),original_manifest_sha256=b['original_split_manifest_sha256'],budget_path=str(new),budget_sha256=sha(new),experiment_cost_ledger_sha256=sha(ledger),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'])
 save(d/'authorization-DISABLED-template.json',template)
 save(d/'verification.json',dict(passed=True,source_and_protected_hashes_unchanged=True,synthetic_fixture_assertions=tests['fixture_assertions'],actual_query_ledger_unchanged=True,no_actual_policy_or_environment_called=True,unique_cost_line=True,budget_unchanged=True,authority_disabled=True))
 print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
