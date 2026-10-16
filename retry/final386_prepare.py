"""Revision386 preparation: synthetic regressions, disabled authority, metadata only."""
import datetime,hashlib,json,os,subprocess,sys,time
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
 assert sys.version.split()[0]=='3.11.16' and Path(sys.executable).absolute()==G/'.venv/bin/python'
 d=root/'stage386';assert d.exists() and not(d/'cost.json').exists() and not(d/'execution-plan-private.json').exists()
 old=root/'project-effective-budget-v404.json';v=read(old);keys=['actual_cumulative_wrapper_actions','research_remaining','final_reserved_actions','final_reserve_used','B_operating_cap']
 assert [v[k] for k in keys]==[1312121,35943,84000,0,1432064]
 b=read(root/'stage384/binding-private.json');assert b['candidate296_zip_sha256']==read(root/'current-champion.json')['archive_sha256']
 assert sha(G/'retry/final382_contract.md')==b['immutable_contract382_sha256']
 assert read(root/'protected-query-ledger-v1.json')['SEALED']==dict(episodes_used=0,future_episode_queries_this_phase_max=0)
 assert not list(root.rglob('SEALED*.opened')) and not(root/'final385-evaluation').exists()
 protected={str(p):sha(p) for p in [old,root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json',root/'preregistered-v1.json',root/'stage384/binding-private.json',G/'retry/final382_contract.md',G/'retry/binding384_result.json',G/'retry/final385_result.json',G/'retry/final385_result.md']}
 files=[Path(__file__),G/'retry/final385_adapter.py',G/'retry/final385_dryrun.py',G/'retry/final386_regression.py',G/'local_runner.py',G/'env_wrapper.py',G/'damage.py',G/'retry/clean_pixel_worker.py',G/'retry/frozen_composite_runtime.py',G/'retry/pixel_sandbox_runtime.py',G/'retry/qualify_pixel_package.py']+list((G/'core').rglob('*.py'))
 sources={str(p):sha(p) for p in files}
 for rel,h in b['execution_sources'].items():assert sha(G/rel)==h
 plan=dict(stage=386,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='DISABLED_REVISION386_NO_OPENING',supersedes_preparation385=True,
  binding384_sha256=sha(root/'stage384/binding-private.json'),frozen_execution_sources=sources,
  frozen_interpreter=str(G/'.venv/bin/python'),policy_zip_sha256=b['candidate296_zip_sha256'],
  original_manifest_reference_sha256=b['original_split_manifest_sha256'],SEALED_identity_block_reference_sha256=b['SEALED_ordered_identity_block_sha256'],
  real_episode_allowance=0,prepared_final_count=16,prepared_final_cap=32000,reserve=b['reserve'],
  fixes=['Dependency schema/count/version/digest bound to384 before installed-file reads','Cap commit recovery with finish priority','Post-act deadline/drift check before step intent','Locked shared-ledger/prior revalidation; independent reconciliation only on drift','Catchable interruption finally settles accounting and closes queries; no hard-kill guarantee'],
  source_archive='before-final385_adapter.py',identity_payload_reads=0,no_real_backend_calls=True)
 save(d/'execution-plan-private.json',plan);save(d/'source-and-protected-hashes.json',dict(source_hashes=sources,protected_hashes=protected))
 start,cpu=time.perf_counter(),time.process_time();tests={}
 for module,name in [('retry.final385_dryrun','final-existing22'),('retry.final386_regression','final-regression')]:
  proc=subprocess.run([str(G/'.venv/bin/python'),'-m',module,str(d/name)],cwd=G,text=True,capture_output=True)
  f=d/(name+'.log');f.write_text(proc.stdout+proc.stderr);f.chmod(0o600);assert proc.returncode==0,proc.stderr
  tests[name]=read(d/name/'verification.json');assert tests[name]['passed']
 cost=dict(stage=386,new_wrapper_actions=0,new_actor_calls=0,new_environment_resets=0,new_environment_creation=0,new_model_forward_calls=0,new_learning_fits=0,new_source_physics_rollout_ticks=0,new_observation_queries=0,new_performance_queries=0,new_terrain_queries=0,new_paid_resources=0,registered_synthetic_wall_s=time.perf_counter()-start,preparation_CPU_s=time.process_time()-cpu,scope='Final registered synthetic subprocesses only; earlier development fixtures/source review/metadata preflight/report/git not fully timed',**{k:v[k] for k in keys})
 result=dict(stage=386,five_defects_fixed=True,existing_fixture_assertions=tests['final-existing22']['fixture_assertions'],regression_fixture_assertions=tests['final-regression']['regression_assertions'],synthetic_tests=tests,adapter_source_sha256=sha(G/'retry/final385_adapter.py'),preparation_plan_sha256=sha(d/'execution-plan-private.json'),supersedes385_readiness=True,requires_preparation_revision=386,query_ledger_unchanged=True,SEALED_evaluation_opened=False,new_experiment=False,authority_disabled=True,hard_termination_scope='SIGKILL/power loss cannot run Python finally; durable prefix plus independent no-reexecution metadata recovery remains necessary. Repeated interruption/storage failure may prevent settlement.',remaining_known_technical_blockers=[],remaining_authority='Explicit final opening approval and exact revision386 source/ledger/budget bindings; no activation here',research_program_terminated=False,cost=cost)
 assert all(sha(p)==h for p,h in protected.items());assert all(sha(p)==h for p,h in sources.items())
 save(d/'cost.json',cost);save(d/'result.json',result);save(G/'retry/final386_result.json',result)
 ledger=root/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==386 for s in ledger.read_text().splitlines())
 v.update(version=405,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(old),prior_budget_sha256=sha(old),cost_path=str(d/'cost.json'),cost_sha256=sha(d/'cost.json'),B_increment=0,stage386_new_wrapper_actions=0)
 new=root/'project-effective-budget-v405.json';assert not new.exists();save(new,v)
 with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
 template=dict(kind='EXPLICIT_FINAL_SEALED_OPENING',authorized=False,user_authorization_reference=None,preparation_stage=386,
  no_concurrent_research=True,case_count=16,native_cap=32000,binding384_sha256=sha(root/'stage384/binding-private.json'),preparation_plan_sha256=sha(d/'execution-plan-private.json'),preservation_receipt_sha256=sha(d/'source-and-protected-hashes.json'),adapter_source_sha256=sha(G/'retry/final385_adapter.py'),original_manifest_sha256=b['original_split_manifest_sha256'],budget_path=str(new),budget_sha256=sha(new),experiment_cost_ledger_sha256=sha(ledger),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'])
 save(d/'authorization-DISABLED-template.json',template)
 # Read-only metadata preflight on a disabled template: never call run_live.
 from retry.final385_adapter import preflight
 t=time.perf_counter();preflight(root,template)
 assert not any(n.split('.')[0] in {'numpy','cv2','gymnasium','Box2D','core','env_wrapper','agent'} for n in sys.modules)
 assert all(sha(p)==h for p,h in protected.items());assert all(sha(p)==h for p,h in sources.items())
 result['metadata_preflight']=dict(passed=True,wall_s=time.perf_counter()-t,template_disabled=True,no_live_entry=True,no_backend_import=True,query_unchanged=True)
 save(d/'result.json',result);save(G/'retry/final386_result.json',result)
 save(d/'verification.json',dict(passed=True,source_and_protected_hashes_unchanged=True,all_synthetic_tests_passed=True,metadata_preflight_passed=True,authority_disabled=True,no_policy_environment_or_native_calls=True,unique_cost_line=True,budget_unchanged=True))
 print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
