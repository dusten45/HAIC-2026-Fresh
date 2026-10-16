"""Qualify immutable296 on saved TRAIN pixels; never create/import an environment."""
import ast
import datetime
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time
import zipfile
import numpy as np
from retry.frozen_composite_runtime import prepare, validate_response

G = Path(__file__).resolve().parent.parent

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def read(p):
    return json.loads(Path(p).read_text())

def save(p, obj):
    p = Path(p)
    tmp = p.with_suffix(p.suffix+'.tmp')
    with tmp.open('x') as f:
        os.chmod(tmp, 0o600)
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')
    tmp.replace(p)

def observation(frames, index):
    return frames[[max(0, index-j) for j in [3,2,1,0]]].astype(np.float32)/255

def run(root):
    d = root/'stage381'
    assert not d.exists(), 'No replay/recharge of completed qualification'
    vpath = root/'project-effective-budget-v398.json'
    budget = read(vpath)
    keys = ['actual_cumulative_wrapper_actions', 'research_remaining', 'final_reserved_actions', 'final_reserve_used', 'B_operating_cap']
    assert [budget[k] for k in keys] == [1312121,35943,84000,0,1432064]
    deadline = read(root/'research-deadline-current.json')['deadline_utc']
    def check_time():
        assert datetime.datetime.now(datetime.timezone.utc) < datetime.datetime.fromisoformat(deadline.replace('Z','+00:00'))
    check_time()
    config = read(root/'stage296/champion-config.json')
    prior = read(root/'stage377/plan.json')
    sandbox = Path(prior['sandbox_path'])
    assert sha(sandbox) == prior['source_hashes'][str(sandbox)]
    assert sha(config['archive_path']) == config['archive_sha256'] == '0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937'
    assert sha(config['worker_path']) == config['worker_sha256']
    assert config['assets'] == {} and config['constants'] == {}
    imports, sensitive = set(), []
    with zipfile.ZipFile(config['archive_path']) as z:
        assert len(z.namelist()) == len(set(z.namelist())) == len(config['members_sha256'])
        assert set(z.namelist()) == set(config['members_sha256'])
        for name, expected in config['members_sha256'].items():
            assert sha_bytes(z.read(name)) == expected
            if not name.endswith('.py'): continue
            for node in ast.walk(ast.parse(z.read(name))):
                if isinstance(node, ast.Import): imports.update(x.name for x in node.names)
                if isinstance(node, ast.ImportFrom): imports.add(node.module or '')
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {'open','exec','eval','compile','__import__'}:
                    sensitive.append([name,node.lineno,node.func.id])
    assert not sensitive
    assert all(n.split('.')[0] in {'retry','numpy','cv2','heapq'} for n in imports)
    protected = [root/'current-champion.json',root/'stage296/champion-manifest.json',root/'stage373/candidate365-rejected-locked.json',root/'protected-query-ledger-v1.json',vpath]
    protected_hashes = {str(p):sha(p) for p in protected}
    excluded = {str(root/n):(root/n).stat().st_mtime_ns for n in ['stage372','stage297']}
    sources = [Path(__file__),G/'retry/clean_pixel_worker.py',G/'retry/pixel_sandbox_runtime.py',G/'retry/frozen_composite_runtime.py',G/'retry/qualify_pixel_package.py',G/'retry/pixel_read_sandbox.c',G/'README.md',G/'local_runner.py',sandbox,Path(config['archive_path']),root/'stage296/champion-config.json',root/'stage296/package-verification.json',root/'stage377/A/frames-actions-private.npz',root/'stage377/A/result.json',root/'stage377/reset-qualification.json']
    hashes = {str(p):sha(p) for p in sources}
    d.mkdir(mode=0o700)
    plan = dict(stage=381,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=deadline,
                scope='Samehost independent unchanged clean pixel process, stored377 TRAIN episode only; no world/env creation/native/reset/step/GT/seed/info/log input to actor; no protected split access',
                actor_act_cap=253,actor_reset_cap=2,native_cap=0,reset_replay_prefix=16,
                stops='First integrity/input/action parity/limit/isolation/deadline/technical failure; no retry or policy change. Full 237 saved actions once then reset and first16 once.',
                limits=dict(cold_start_ms=10000,reset_ms=5000,act_ms=5000,memory_bytes=1024000000),
                document_provenance='Parent reports full24chapters+applicationplan reread and supplies sections10/15/18.2G5; valid relayed authority, consumer direct original access/fullread unverified. No originals transferred.',
                source_hashes=hashes,protected_hashes=protected_hashes,excluded_directory_stats=excluded)
    save(d/'plan.json',plan)
    save(d/'package-static-audit.json',dict(member_hashes_exact=True,imports=sorted(imports),sensitive_calls=sensitive,extra_requirements=False,
         worker_request_keys=['op','observation'],worker_ops=['reset','act'],
         access_scope='Native read-root/open restrictions and seccomp deny network/children, Python imports/open audit, closefds/sanitizedenv/isolatedPython. Metadata syscalls not hidden; not hostile-code/freshmachine/server proof.'))
    start,cpu=time.perf_counter(),time.process_time()
    acts=resets=0;worker=None;responses=[];reset_ms=[];latencies=[];compute=[];error=None;reaping=None;ready=None;cold=None;peak=0;actor_cpu=0;matches=0;reset_matches=0
    try:
        saved=np.load(root/'stage377/A/frames-actions-private.npz',allow_pickle=False)
        frames,expected=saved['frames_uint8'],saved['actions']
        assert frames.shape==(238,84,84) and expected.shape==(237,3) and expected.dtype==np.float32
        worker=prepare(config,d/'cpu',sandbox)
        ready=worker.ready;cold=worker.cold_start_ms
        save(d/'ready-private.json',ready)
        assert ready['python_version']=='3.11.16' and ready['numpy_version']=='1.26.0' and ready['opencv_version']=='4.8.1'
        assert set(worker.runtime_environment)=={'PATH','HOME','TMPDIR','LANG','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','CUDA_VISIBLE_DEVICES','SDL_VIDEODRIVER','SDL_AUDIODRIVER'}
        for prefix in [237,16]:
            check_time();obs=observation(frames,0);resets+=1
            response,ms=worker.call('reset',obs);validate_response(response,config,obs,'reset');reset_ms.append(ms);peak=max(peak,response['rss_mib']);actor_cpu=response['actor_cumulative_CPU_s']
            for i in range(prefix):
                check_time();obs=observation(frames,i);acts+=1
                response,ms=worker.call('act',obs);actual=validate_response(response,config,obs,'act')
                assert actual.tobytes()==expected[i].tobytes(), f'Action parity failed at prefix{prefix} index{i}'
                latencies.append(ms);compute.append(response['act_compute_ms']);peak=max(peak,response['rss_mib']);actor_cpu=response['actor_cumulative_CPU_s']
                if prefix==237:matches+=1
                else:reset_matches+=1
        assert max(latencies)<5000 and max(reset_ms)<5000 and cold<10000
        assert peak*1024*1024 <= 1024000000
    except BaseException as exc:
        error=type(exc).__name__+': '+str(exc)
        save(d/'error-private.json',dict(error=error,traceback=__import__('traceback').format_exc()))
    finally:
        if worker:
            reaping=worker.close();peak=max(peak,worker.observed_peak_rss_bytes/1024/1024)
    assert acts<=253 and resets<=2
    def stats(values):
        return dict(n=len(values),median=float(np.median(values)),p95=float(np.percentile(values,95)),max=max(values)) if values else None
    dependencies={n:importlib.metadata.version(n) for n in ['numpy','opencv-python']}
    result=dict(stage=381,passed=error is None and bool(reaping and reaping['process_reaped']),technical_error=error,
        archive_sha256=config['archive_sha256'],member_count=len(config['members_sha256']),member_hashes_exact=True,
        unchanged_policy=True,independent_process_same_machine=True,new_machine_reproduction=False,official_server_equivalence=False,
        consumer_direct_original_full_read=False,parent_full_read_and_excerpts_recorded=True,
        saved_TRAIN_actions_matched=matches,post_reset_prefix_actions_matched=reset_matches,
        actor_act_calls=acts,actor_reset_calls=resets,new_native_actions=0,new_env_creation=0,
        cold_start_ms=cold,reset_including_IPC_ms=reset_ms,act_including_IPC_ms=stats(latencies),act_compute_ms=stats(compute),
        observed_peak_RSS_MiB=peak,memory_limit_bytes=1024000000,actor_CPU_s=actor_cpu,
        dependency_versions=dependencies,python_version=sys.version.split()[0],libc=platform.libc_ver(),
        input_boundary='Only op+float32(4,84,84) pixels, no env object/seed/info/evaluation logs. Savedframes read by supervisor only.',
        metadata_syscalls_hidden=False,hostile_code_security_proof=False,
        process_reaped=bool(reaping and reaping['process_reaped']),SEALED_opened=False,manifest_updated=False)
    save(d/'reaping-private.json',reaping)
    cost=dict(stage=381,new_wrapper_actions=0,new_environment_resets=0,new_environment_creation=0,
        new_actor_calls=acts,new_actor_reset_calls=resets,new_model_forward_calls=acts,
        model_forward_scope='Existing affine policy head evaluated during each act; no training or new model',
        new_learning_fits=0,new_source_physics_rollout_ticks=0,new_candidate_implementations=0,new_paid_resources=0,
        qualification_wall_s=time.perf_counter()-start,supervisor_CPU_s=time.process_time()-cpu,actor_CPU_s=actor_cpu,
        **{k:budget[k] for k in keys})
    result['cost']=cost
    save(d/'result.json',result);save(d/'cost.json',cost);save(G/'retry/qualification381_result.json',result)
    assert all(sha(p)==h for p,h in hashes.items())
    assert all(sha(p)==h for p,h in protected_hashes.items())
    assert all(Path(p).stat().st_mtime_ns==n for p,n in excluded.items())
    ledger=root/'experiment-cost-lines.jsonl'
    assert not any(json.loads(s).get('stage')==381 for s in ledger.read_text().splitlines())
    budget.update(version=399,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(vpath),prior_budget_sha256=sha(vpath),cost_path=str(d/'cost.json'),cost_sha256=sha(d/'cost.json'),B_increment=0,stage381_new_wrapper_actions=0)
    assert not (root/'project-effective-budget-v399.json').exists()
    save(root/'project-effective-budget-v399.json',budget)
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    save(d/'preservation-verification.json',dict(passed=True,source_and_protected_hashes_unchanged=True,excluded_directory_stats_unchanged=True,balance_unchanged=True,unique_cost_line=True))
    print(json.dumps(result,ensure_ascii=False),flush=True)
    if error:raise RuntimeError('Qualification stopped, no automatic retry: '+error)

def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()

if __name__=='__main__':run(Path(sys.argv[1]).resolve())
