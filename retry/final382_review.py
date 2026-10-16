"""Metadata/source-only final contract audit. No simulator or policy imports."""
import datetime
import hashlib
import json
from pathlib import Path
import os
import sys
import time
import zipfile
G=Path(__file__).resolve().parent.parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,obj):
    p=Path(p);tmp=p.with_suffix(p.suffix+'.tmp')
    with tmp.open('x') as f:
        os.chmod(tmp,0o600);json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    tmp.replace(p)
def stat(p):
    s=Path(p).stat();return dict(size=s.st_size,mtime_ns=s.st_mtime_ns)

def run(root):
    d=root/'stage382';assert not d.exists(),'No duplicate closure'
    before=root/'project-effective-budget-v399.json';v=read(before)
    keys=['actual_cumulative_wrapper_actions','research_remaining','final_reserved_actions','final_reserve_used','B_operating_cap']
    assert [v[k] for k in keys]==[1312121,35943,84000,0,1432064]
    champ=read(root/'current-champion.json');assert champ['adopted_after_stage']==296 and champ['G5_SEALED']=='PENDING_CLOSED'
    for item in [champ,champ['immediate_rollback']]:
        assert sha(item['archive_path'])==item['archive_sha256']
        with zipfile.ZipFile(item['archive_path']) as z:
            assert set(z.namelist())==set(item['configuration']['members_sha256'])
            assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in item['configuration']['members_sha256'].items())
    ledger=read(root/'protected-query-ledger-v1.json');assert ledger['SEALED']==dict(episodes_used=0,future_episode_queries_this_phase_max=0)
    assert not list(root.rglob('SEALED*.opened'))
    contract=(root/'CONTRACT.txt').read_text();assert 'DEV 8 / HOLDOUT 8 / SEALED 16' in contract
    # Never read/hash/parse the original condition manifest or stage372 cases.
    closed={str(root/'preregistered-v1.json'):stat(root/'preregistered-v1.json')}
    excluded={str(root/n):(root/n).stat().st_mtime_ns for n in ['stage372','stage297']}
    protected={str(p):sha(p) for p in [root/'current-champion.json',root/'stage296/champion-manifest.json',root/'stage373/candidate365-rejected-locked.json',root/'protected-query-ledger-v1.json',before]}
    sources=[Path(__file__),G/'retry/final382_contract.md',G/'retry/research382_explanation.md',G/'retry/methods380_result.md',G/'retry/qualification381_result.md',G/'retry/qualification381_result.json',G/'retry/reliability296_result.json',G/'local_runner.py',G/'env_wrapper.py',G/'core/finish_line.py',G/'core/vendor/car_racing.py',G/'README.md',root/'CONTRACT.txt',root/'stage16/split-review-ko.txt',root/'stage296/exclusion-final.json',root/'stage381/final-review-receipt.json']
    hashes={str(p):sha(p) for p in sources}
    d.mkdir(mode=0o700);start,cpu=time.perf_counter(),time.process_time()
    snapshot=read(root/'stage296/exclusion-final.json')
    metadata=dict(SEALED_count=16,ledger_episodes_used=0,current_phase_queries_allowed=0,opened_markers=0,
        original_condition_manifest_stat_only=True,original_condition_contents_or_geometry_read=False,
        historical_HOLDOUT_opened_marker=(root/'HOLDOUT.opened').exists(),
        original_contract_reports_pair_seed_disjoint=True,
        later_full_exposure_intersection_verified=False,
        required='Opaque original SEALED identity/geometry fingerprint intersection against full current exposure metadata; counts+provenance only, no policy exposure or new environment',
        historical296_exclusion_counts={k:len(val) for k,val in snapshot.items() if k.startswith('excluded_') and isinstance(val,list)},
        scope='Historical exclusion counts are not a current complete anti-overlap certificate')
    proposal=dict(status='PROPOSAL_ONLY_NOT_EXECUTABLE',opening_authorized=False,policy='unchanged296',rollback='preserved240_noSEALEDcomparison',
        conditions=16,max_wrapper_actions_per_case=2000,frame_skip=4,raw_TimeLimit=8200,warmup_TimeLimit_elapsed=50,
        raw_reset_ticks=51,internal_wrapper_capacity_ceiling=2038,actual_outer_loop_cap=2000,
        reserve_allocation=dict(primary296=32000,automatic_retries=0,rollback_comparison=0,unallocated_preserved=52000,total=84000),
        no_retry_resample_or_post_exposure_policy_change=True,
        invalid_timeout_technical_failure='Stop whole final qualification, preserve partial/censor, do not fabricate official-server DNF; local safe_act fallback differs on timeout',
        primary_classification='Finish_time present wins; local max_steps2000 without finish is local DNF; early technical/protocol/deadline abort is incomplete/censor',
        remaining=['Final opening authority and query ledger contract','Opaque up-to-date SEALED overlap/exposure receipt','Bind final source/runtime/manifest and actual-cost/error ledger hashes'],
        official_server_and_new_machine_equivalence=False)
    plan=dict(stage=382,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Read existing source and aggregate/metadata only; no policy/env/model/training/condition construction/calls',source_hashes=hashes,protected_hashes=protected,closed_files_stat_only=closed,excluded_directory_stats=excluded)
    save(d/'plan.json',plan);f=d/'plan.sha256';f.write_text(sha(d/'plan.json')+'\n');f.chmod(0o600)
    cost=dict(stage=382,new_wrapper_actions=0,new_actor_calls=0,new_environment_resets=0,new_environment_creation=0,new_model_forward_calls=0,new_learning_fits=0,new_source_physics_rollout_ticks=0,new_candidate_implementations=0,new_paid_resources=0,new_condition_content_reads=0,new_performance_queries=0,future_native_reserved=0,audit_wall_s=time.perf_counter()-start,audit_CPU_s=time.process_time()-cpu,scope='Small metadata assembly only; source reading/coding/report/git time not fully timed',**{k:v[k] for k in keys})
    result=dict(stage=382,contract_only=True,execution_authorized=False,proposal=proposal,SEALED_metadata=metadata,
        parent_document_full_read_and_excerpts=True,consumer_original_full_read=False,originals_or_private_reflections_published=False,
        champion296_unchanged=True,rollback240_unchanged=True,research_program_terminated=False,new_experiment=False,cost=cost)
    assert all(sha(p)==h for p,h in hashes.items());assert all(sha(p)==h for p,h in protected.items())
    assert all(stat(p)==s for p,s in closed.items());assert all(Path(p).stat().st_mtime_ns==n for p,n in excluded.items())
    save(d/'exposure-metadata.json',metadata);save(d/'final-execution-proposal.json',proposal);save(d/'cost.json',cost);save(d/'summary.json',result);save(G/'retry/final382_result.json',result)
    lines=root/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==382 for s in lines.read_text().splitlines())
    v.update(version=400,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(before),prior_budget_sha256=sha(before),cost_path=str(d/'cost.json'),cost_sha256=sha(d/'cost.json'),B_increment=0,stage382_new_wrapper_actions=0)
    assert not (root/'project-effective-budget-v400.json').exists();save(root/'project-effective-budget-v400.json',v)
    with lines.open('a') as f:f.write(json.dumps(cost)+'\n')
    save(d/'verification.json',dict(passed=True,source_and_protected_hashes_unchanged=True,closed_files_stat_only_unchanged=True,excluded_directories_unchanged=True,budget_unchanged=True,unique_cost_line=True,SEALED_not_opened=True))
    print(json.dumps(dict(proposal=proposal,metadata=metadata,cost=cost),ensure_ascii=False),flush=True)

if __name__=='__main__':run(Path(sys.argv[1]).resolve())
