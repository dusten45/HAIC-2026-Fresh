"""Bind final contract metadata to qualified artifacts; never run an Agent/env."""
import datetime,hashlib,importlib.metadata,json,os,sys,time
from pathlib import Path
G=Path(__file__).resolve().parent.parent

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def save(p,obj):
 p=Path(p);t=p.with_suffix(p.suffix+'.tmp')
 with t.open('x') as f:
  os.chmod(t,0o600);json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 t.replace(p)
def distribution(name,version):
 dist=importlib.metadata.distribution(name);assert dist.version==version
 hashes={};missing=[]
 for f in dist.files:
  if str(f).endswith('.pyc') or '__pycache__' in Path(f).parts:continue
  p=Path(dist.locate_file(f))
  if not p.is_file():missing.append(str(f));continue
  hashes[str(f)]=sha(p)
 assert not missing,(name,'Missing installed distribution files')
 return dict(version=version,file_count=len(hashes),content_manifest_sha256=digest(hashes),files_sha256=hashes,scope='Current installed distribution files excluding generated pyc; not retrospective381 binary proof or full OS image')

def run(root):
 assert sys.version.split()[0]=='3.11.16','Use existing qualified .venv/bin/python, never ambient python'
 assert Path(sys.executable).absolute()==G/'.venv/bin/python'
 d=root/'stage384';assert not d.exists(),'Duplicate preparation prohibited'
 old=root/'project-effective-budget-v402.json';v=read(old);keys=['actual_cumulative_wrapper_actions','research_remaining','final_reserved_actions','final_reserve_used','B_operating_cap']
 assert [v[k] for k in keys]==[1312121,35943,84000,0,1432064]
 sources=[Path(__file__),G/'retry/final382_contract.md',G/'retry/final382_result.json',G/'retry/qualification381_result.json',G/'retry/seed383_result.json',root/'stage381/plan.json',root/'stage381/ready-private.json',root/'stage381/final-review-receipt.json',root/'stage383/seed-followup/plan-final.json',root/'stage383/seed-followup/summary.json',root/'stage383/seed-followup/final-identity-union-private.json',root/'stage296/cost.json',root/'stage375/cost.json',root/'stage377/cost.json',G/'README.md',G/'local_runner.py',G/'env_wrapper.py',G/'core/finish_line.py',root/'research-deadline-current.json']
 protected={str(p):sha(p) for p in [root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json',G/'retry/final382_contract.md',G/'retry/final382_result.json',old]}
 source_hashes={str(p):sha(p) for p in sources}
 original=root/'preregistered-v1.json';original_hash=sha(original);assert original_hash==(root/'preregistered-v1.sha256').read_text().split()[0]
 champ=read(root/'current-champion.json');rollback=champ['immediate_rollback'];config=champ['configuration']
 assert champ['adopted_after_stage']==296 and champ['G5_SEALED']=='PENDING_CLOSED'
 assert sha(champ['archive_path'])==champ['archive_sha256'] and sha(rollback['archive_path'])==rollback['archive_sha256']
 q=read(root/'stage381/plan.json');qr=read(root/'stage381/final-review-receipt.json');ready=read(root/'stage381/ready-private.json');report381=read(G/'retry/qualification381_result.json')
 assert sha(root/'stage381/plan.json')==qr['plan_sha256'];assert sha(G/'retry/qualification381_result.json')==qr['public_json_sha256']
 assert q['source_hashes'][champ['archive_path']]==champ['archive_sha256']
 assert all(sha(p)==h for p,h in q['source_hashes'].items())
 for name,h in ready['policy_module_sha256'].items():
  file=Path(ready['policy_modules'][name]);package=root/'stage381/cpu/package'
  relative=str(file.relative_to(package));assert config['members_sha256'][relative]==h
 assert report381['passed'] and report381['saved_TRAIN_actions_matched']==237 and report381['post_reset_prefix_actions_matched']==16
 proof=read(root/'stage383/seed-followup/summary.json');identity=read(root/'stage383/seed-followup/final-identity-union-private.json');p383=read(root/'stage383/seed-followup/plan-final.json')
 assert identity['original_manifest_sha256']==original_hash
 assert proof['seed_intersection_verified'] and proof['seed_intersection_count']==proof['pair_intersection_count']==0
 assert all(sha(p)==h for p,h in p383['source_hashes'].items())
 sealed_hash=digest(identity['SEALED_pairs'])
 assert read(root/'protected-query-ledger-v1.json')['SEALED']==dict(episodes_used=0,future_episode_queries_this_phase_max=0)
 assert not list(root.rglob('SEALED*.opened'))
 d.mkdir(mode=0o700);start,cpu=time.perf_counter(),time.process_time()
 deps={n:distribution(n,ver) for n,ver in [('numpy','1.26.0'),('opencv-python','4.8.1.78')]}
 runtime=dict(interpreter_path=str(G/'.venv/bin/python'),resolved_interpreter_path=str(Path(sys.executable).resolve()),interpreter_sha256=sha(Path(sys.executable).resolve()),python_version=sys.version.split()[0],distributions={k:{a:b for a,b in val.items() if a!='files_sha256'} for k,val in deps.items()},retrospective381_distribution_byte_hashes_recorded=False)
 save(d/'dependency-files-private.json',deps)
 measured=[]
 for stage,wallfield in [(296,'total_search_wall_s'),(375,'batch_wall_s')]:
  c=read(root/f'stage{stage}/cost.json');actions=c['new_wrapper_actions'];wall=c[wallfield];measured.append(dict(stage=stage,native_actions=actions,wall_s=wall,wall_per_native_s=wall/actions,full32000_projection_minutes=32000*wall/actions/60))
 c=read(root/'stage377/cost.json');actions=c['new_wrapper_actions'];wall=c['measurements']['wall_s'];measured.append(dict(stage=377,native_actions=actions,wall_s=wall,wall_per_native_s=wall/actions,full32000_projection_minutes=32000*wall/actions/60))
 rates=[x['wall_per_native_s'] for x in measured]
 estimate=dict(existing_measurements=measured,fullcap32000_minutes=[32000*min(rates)/60,32000*max(rates)/60],conditional_4000to5000_native_minutes=[4000*min(rates)/60,5000*max(rates)/60],scope='Observed samehost historical rates, reset/startup overhead already included; different observer/IO/policy paths; no SEALED prediction, no new benchmark, not hard wall guarantee')
 binding=dict(stage=384,status='PREPARED_NOT_EXECUTABLE_NOT_OPENED',final_opening_authorized=False,
  immutable_contract382_sha256=sha(G/'retry/final382_contract.md'),candidate296_zip_sha256=champ['archive_sha256'],candidate_member_manifest_sha256=digest(config['members_sha256']),candidate_members=18,
  rollback240_zip_sha256=rollback['archive_sha256'],qualification381_plan_sha256=sha(root/'stage381/plan.json'),qualification381_result_sha256=sha(G/'retry/qualification381_result.json'),qualified_archive_exact=True,qualified_loaded_policy_modules=17,
  original_split_manifest_sha256=original_hash,SEALED_ordered_identity_block_sha256=sealed_hash,SEALED_case_count=16,seed383_proof_sha256=sha(root/'stage383/seed-followup/summary.json'),seed383_proof_plan_sha256=sha(root/'stage383/seed-followup/plan-final.json'),
  seed383_scope='Seed/pair overlap0 vs conservative339 within preserved metadata,224exposurestages;2unattributed retained; no geometry/statistical/server/newmachine independence proof',
  runtime=runtime,execution_sources={str(p.relative_to(G)):sha(p) for p in [G/'retry/clean_pixel_worker.py',G/'retry/frozen_composite_runtime.py',G/'retry/pixel_sandbox_runtime.py',G/'retry/qualify_pixel_package.py',G/'local_runner.py',G/'env_wrapper.py',G/'core/finish_line.py']},native_sandbox_sha256=sha(root/'stage88/pixel-read-sandbox'),
  execution=dict(candidates=1,cases=16,max_steps_per_case=2000,frame_skip=4,raw_TimeLimit=8200,warmup_elapsed_steps=50,raw_reset_ticks=51,input='reset/act + official pixels only',policy_changes=0,new_splits=0,new_condition_selection=0,actor_and_reset='Independent unchanged actor per case, full normal reset; no carryover state or privileged diagnostics'),
  failure_rule='Frozen clean worker: exact shape3,finite,in-range actions; first qualification/runtime/invalid/IPC/source/deadline failure aborts batch and yields technical/censor classification, no retry/no fabricated official-server DNF. Local runner flatten/finiteclip/no-op/thread-timeout paths are source reference only, not identical to this strict adapter.',
  aggregate_rule='Finish_time present wins even if truncated; local2000cap without finish is max_steps DNF. Report16 planned denominator and observed/unobserved/censored separately,completioncount first; lap mean/median only completed, no fake DNFtimes; damage/runtime separate. No240SEALEDcomparison/posthocpolicyselection/newpass threshold.',
  reserve=dict(total=84000,primary296_cap=32000,automatic_retry=0,rollback_comparison=0,unallocated=52000,current_used=0),
  remaining=['Explicit final opening authorization and frozen claim/query/error-cost ledger binding','Final executor/report adapter must consume these exact hashes and strict abort/aggregation rules; no invocation now','Recheck snapshot freshness without inference before opening; no package/ZIP change or automatic requalification'],
  same_machine_only=True,official_server_equivalence=False,new_machine_equivalence=False,consumer_original_document_full_read=False,parent_original_full_read_relay_recorded=True)
 save(d/'binding-private.json',binding)
 result=dict(stage=384,contract_binding=binding,time_estimate=estimate,new_experiment=False,SEALED_evaluation_opened=False,research_program_terminated=False)
 cost=dict(stage=384,new_wrapper_actions=0,new_actor_calls=0,new_environment_resets=0,new_environment_creation=0,new_model_forward_calls=0,new_learning_fits=0,new_source_physics_rollout_ticks=0,new_observation_queries=0,new_performance_queries=0,new_terrain_queries=0,new_paid_resources=0,metadata_binding_wall_s=time.perf_counter()-start,metadata_binding_CPU_s=time.process_time()-cpu,scope='Dependency hashing/binding/timing arithmetic; earlier source review and report/git not fully timed',**{k:v[k] for k in keys})
 result['cost']=cost
 # Public binding omits local source paths of private artifacts and every seed.
 public=json.loads(json.dumps(result));public['contract_binding']['runtime'].pop('resolved_interpreter_path')
 save(d/'result.json',result);save(d/'cost.json',cost);save(G/'retry/binding384_result.json',public)
 save(d/'plan.json',dict(stage=384,source_hashes=source_hashes,protected_hashes=protected,original_manifest_sha256=original_hash,metadata_only=True,policy_and_environment_calls=0))
 assert all(sha(p)==h for p,h in source_hashes.items());assert all(sha(p)==h for p,h in protected.items())
 ledger=root/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==384 for s in ledger.read_text().splitlines())
 v.update(version=403,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(old),prior_budget_sha256=sha(old),cost_path=str(d/'cost.json'),cost_sha256=sha(d/'cost.json'),B_increment=0,stage384_new_wrapper_actions=0)
 assert not(root/'project-effective-budget-v403.json').exists();save(root/'project-effective-budget-v403.json',v)
 with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
 save(d/'verification.json',dict(passed=True,qualified381_archive_and_loaded_modules_match=True,proof383_same_manifest_match=True,protected_contract382_unchanged=True,dependency_snapshot_current_not_retroactive=True,budget_unchanged=True,unique_cost_line=True,SEALED_not_opened=True))
 print(json.dumps(dict(runtime=public['contract_binding']['runtime'],estimate=estimate,cost=cost),ensure_ascii=False),flush=True)
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
