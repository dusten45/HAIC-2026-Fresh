"""479 once-only registered mechanism runner, full readback included in caps."""
import time
WORKER_START=time.perf_counter()
import ast,copy,datetime,hashlib,json,os,pickle,random,shutil,signal,sys,traceback
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.compare477 import source_closure,runtime_environment
from retry.law477 import root_inputs477
from retry.meter479 import Meter479
from retry.mechanism479 import execute
from retry.quota477 import Quota
from retry.loss389_analyze import read,save,sha
from retry.receipt421_io import save_receipt
from retry.ledger439 import require
from retry.pilot420_backend import ResourceStop
G=Path(__file__).resolve().parents[1]
RAW=Path('/tmp/haic-retry-stage479-private')
CAPS=dict(ticks=328,worlds=14,CPU_s=180,wall_s=300,actual_actions=0,resets=0,max_parallel=1)
NAMES=('compare479.py','mechanism479.py','meter479.py','live479.py')

def space(p):
    s=p['storage_forecast'];out={}
    for v,need in [('/tmp',s['tmp_required_bytes']),('/workspace',s['workspace_required_bytes'])]:
        free=shutil.disk_usage(v).free;require(free>=need,'479_STORAGE_PREFLIGHT:'+v)
        out[v]=dict(free_bytes=free,required_bytes=need)
    return out

def prepare(root):
    d=root/'stage479';require(not d.exists() and not d.is_symlink() and not RAW.exists(),'479_ONCE_FRESH')
    old=read(root/'stage477-revision1/plan.json');contract=read(G/'retry/audit478_contract.json');prior=read(root/'stage477-revision1/integrated-qualification.json')
    require(prior['passed'] and sha(root/'stage441/authorization-correction-private.json')==contract['extension_sha256'],'479_OLD_QUALIFICATION_AUTHORIZATION')
    require(read(root/'research-deadline-current.json')['deadline_utc']==contract['deadline_utc'],'479_DEADLINE_PIN')
    state,memory,ledger,rng,blob,expected=root_inputs477(root)
    for group in ('sources','protected','original408_preserve'):
        for f,h in old[group].items():require(sha(f)==h,'479_FROZEN477_SOURCE_CHANGED:'+f)
    for f,h in contract['source_sha256'].items():require(sha(f)==h,'479_FROZEN478_SOURCE_CHANGED:'+f)
    sources={str(f):sha(f) for f in source_closure([G/'retry'/n for n in NAMES])}
    semantic=dict(old['semantic_sources']);semantic.update(sources)
    extra_manifest=max(0,len(json.dumps(semantic,indent=2).encode())-len(json.dumps(old['semantic_sources'],indent=2).encode()))
    require(extra_manifest<=8192,'479_NEW_SOURCE_MANIFEST_ALLOWANCE')
    paths=[G/'retry/audit478_contract.json',root/'research-deadline-current.json',root/'stage441/authorization-correction-private.json',root/'stage477-revision1/integrated-qualification.json',root/'stage477-revision1/whole_AllocationP4-private.json',root/'stage477-revision1/whole_AllocationP4-observer-private.json',root/'stage477-retention-manifest-private.json',root/'stage478-plan-durable-private.json']
    sources.update({str(f):sha(f) for f in paths});sources.update(old['sources'])
    sources.update({str(G/'retry'/n):sha(G/'retry'/n) for n in NAMES})
    p=dict(stage=479,authorization='Inherited explicit479 approval: one finite80ms mechanism experiment per frozen478; no followup',registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=contract['deadline_utc'],contract478_sha256=sha(G/'retry/audit478_contract.json'),caps=CAPS,scope=dict(ticks=328,worlds=14),contract=contract,
        fixed_plan=old['fixed_plan'],pace_path=old['pace_path'],projection_path=old['projection_path'],sources=sources,semantic_sources=semantic,protected=old['protected'],original408_preserve=old['original408_preserve'],ledger_path=old['ledger_path'],ledger_sha256=old['ledger_sha256'],storage_free_stop_bytes=512*1024**2,
        nominal_once='prepare calls SourceC.act once; after-memory to fresh shadows/held47; before-memory and prepared nominal to all one calls. Prefix47 reuses same context. Shadow/held no allocator search.',parent_isolation='snapshot/controller/ledger/RNG/reference/rows/status hash before and after every shadow and held47. Prefix itself is held69.',source_closure='All local AST imports plus frozen477 semantic/input closure; old35/H13/pending evidence reused; no rerun',
        raw_directory=str(RAW),runtime_environment=runtime_environment(),new_seed_learning_HOLDOUT_SEALED_reserve_paid=0,actual=0,resets=0,no_followup=True)
    s=contract['storage'];p['storage_forecast']=dict(model_payload_bytes=s['model_raw_hard_forecast_bytes'],allocator_extra_bytes=s['extra_fullproof_budget_bytes'],tmp_required_bytes=s['tmp_required_bytes'],workspace_required_bytes=s['workspace_required_bytes'],semantic_actual_growth_bytes=extra_manifest,semantic_growth_hard_allowance_bytes=8192,selection_summary_bytes_each=65536,temp_bytes=s['temp_bytes'],reserve_bytes_each_volume=s['reserve_each_bytes'],new_archive=False,workspace_new_raw_archive_copy=False)
    p['storage_preflight']=space(p)
    material=root/'stage479-input-material-private.json';require(not material.exists(),'479_NEW_INPUT_ONLY')
    save_receipt(material,dict(state=state,memory=memory,ledger=asdict(ledger),RNG_blob=blob,RNG_source=rng,expected=expected,fixed=read(old['fixed_plan']),pace=read(old['pace_path']),projected_nodes=read(old['projection_path'])['projected_nodes']))
    p['input_material_path']=str(material);p['input_material_sha256']=sha(material);p['sources'][str(material)]=sha(material)
    require(material.stat().st_size+len(json.dumps(p).encode())<64*1024**2,'479_WORKSPACE_METADATA64MiB')
    require(len(json.dumps(p,indent=2).encode())<=2*1024**2,'479_PLAN2MiB')
    RAW.mkdir(mode=0o700);d.symlink_to(RAW,target_is_directory=True)
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(root/'stage479-plan-durable-private.json',p)
    static(root)
    save(d/'preparation-cost.json',dict(CPU_s=time.process_time(),wall_s=time.perf_counter()-WORKER_START,scope='Registration process including imports, source hashing, input receipt, storage preflight and static gate; added to worker caps'))
    print(json.dumps(dict(stage=479,phase='STATIC_REGISTERED_NO_PHYSICS',plan_sha256=sha(d/'plan.json'),source_manifest_growth=extra_manifest,storage=p['storage_preflight'])),flush=True)

def static(root):
    d=root/'stage479';p=read(d/'plan.json');require(p['caps']==CAPS and p['scope']==dict(ticks=328,worlds=14),'479_STATIC_CAPS')
    for group in ('sources','protected','original408_preserve'):
        for f,h in p[group].items():require(sha(f)==h,'479_STATIC_HASH:'+f)
    tree=ast.parse((G/'retry/mechanism479.py').read_text());prep=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepare')
    require(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='act' for n in ast.walk(prep))==1,'479_STATIC_NOMINAL_ONCE')
    for n in tree.body:
        if isinstance(n,ast.FunctionDef) and n.name!='prepare':
            require(not any(isinstance(k,ast.Call) and isinstance(k.func,ast.Attribute) and k.func.attr=='act' for k in ast.walk(n)),'479_NO_SHADOW_SECOND_ACT')
    for name in NAMES:compile((G/'retry'/name).read_text(),name,'exec')
    require(Meter479.HARD_TICKS==328 and Meter479.HARD_WORLDS==14,'479_STATIC_HARD_METER')
    save(d/'static-result.json',dict(passed=True,stage=479,plan_sha256=sha(d/'plan.json'),nominal_once_AST=True,prepared_context_and_full_ledger_before_stream=True,source_closure_hashes_verified=True,new_worlds=0,new_ticks=0))

def run(root):
    d=root/'stage479';p=read(d/'plan.json');oldsave=save
    require(not(d/'opening.json').exists() and read(d/'static-result.json')['passed'],'479_ONCE_STATIC')
    require(sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()==read(d/'static-result.json')['plan_sha256'],'479_PLAN_BINDING')
    for group in ('sources','protected','original408_preserve'):
        for f,h in p[group].items():require(sha(f)==h,'479_RUN_SOURCE:'+f)
    require(p['caps']==CAPS and p['scope']==dict(ticks=328,worlds=14),'479_RUN_FIXED_SCOPE');space(p)
    state,memory,ledger,rng,blob,expected=root_inputs477(root);py,npr=pickle.loads(blob);random.setstate(py);np.random.set_state(npr)
    fixed=read(p['fixed_plan']);pace=np.asarray(read(p['pace_path'])['frozen268']);prep=read(d/'preparation-cost.json');meter=Meter479(d,worker_start=WORKER_START,preparation_CPU_s=prep['CPU_s'],preparation_wall_s=prep['wall_s'])
    meter.quota=Quota(d,p['storage_forecast']['model_payload_bytes'],p['storage_forecast']['allocator_extra_bytes']).install()
    status='STARTED';error=None;outcome=None;inventory=[]
    save(d/'opening.json',dict(stage=479,pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(d/'plan.json')))
    def timeout(*args):raise ResourceStop('479_WHOLE_CPU180_WALL300_DEADLINE')
    handlers={s:signal.signal(s,timeout) for s in (signal.SIGPROF,signal.SIGALRM)};meter.timers()
    try:
        with meter.model('479_one_finite_80ms_mechanism'):
            outcome=execute(root,meter,fixed,pace,state,memory,ledger)
        status=outcome['status']
    except BaseException as exc:
        status='TECHNICAL_STOP';error=type(exc).__name__+': '+str(exc)
        save(d/'stop-private.json',dict(error=error,traceback=traceback.format_exc(),no_retry=True))
    finally:
        meter.closeall();meter.persist()
    # Source/protection checks, final serialization and full readback all remain
    # inside the same worker deadline, with no uncharged postprocessing process.
    try:
        for group in ('sources','protected','original408_preserve'):
            for f,h in p[group].items():require(sha(f)==h,'479_FINAL_SOURCE:'+f)
        require(sha(p['ledger_path'])==p['ledger_sha256'],'479_GLOBAL_LEDGER_CHANGED')
        save(d/'result.json',dict(stage=479,status=status,error=error,outcome=outcome,budget=read(d/'budget.json'),new_native=0,new_resets=0,new_HOLDOUT_SEALED=0,no_followup=True))
        for f in sorted(d.iterdir()):
            if not f.is_file():continue
            data=f.read_bytes();digest=hashlib.sha256(data).hexdigest()
            if f.suffix=='.json':json.loads(data,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
            again=f.read_bytes();require(len(data)==len(again) and hashlib.sha256(again).hexdigest()==digest,'479_FULL_READBACK:'+f.name)
            inventory.append(dict(path=str(f),bytes=len(data),sha256=digest,full_readbacks=2))
        oldsave(root/'stage479-retention-manifest-private.json',dict(stage=479,files=inventory,new_archive=False,workspace_new_raw_copies=0,tmp_loss='Hashes cannot reconstruct lost raw'))
        # Result/closed budget are final control records; their final hashes are
        # stored durably after their own complete readbacks.
        meter.checkpoint('CLOSED',status=status,error=error)
        result=read(d/'result.json');result['budget']=read(d/'budget.json');result['readback_file_count']=len(inventory);save(d/'result.json',result)
        manifest=read(root/'stage479-retention-manifest-private.json')
        for record in manifest['files']:
            f=Path(record['path'])
            if f.name in ('result.json','progress-private.json','budget.json'):
                data=f.read_bytes();a=f.read_bytes();require(data==a,'479_FINAL_CONTROL_READBACK');json.loads(data);record.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        oldsave(root/'stage479-retention-manifest-private.json',manifest)
        cpu,wall=meter.wholetime();require(cpu<180 and wall<300,'479_FINAL_WHOLE_CAP')
        public=dict(stage=479,status=status,error=error,outcome=outcome,model_ticks=meter.b['ticks'],reserved_ticks=meter.b['reserved_ticks'],model_worlds=meter.b['worlds'],allocator_calls=meter.allocator_calls,preparation_cost=prep,allocator_CPU_s=meter.allocator_CPU_s,allocator_wall_s=meter.allocator_wall_s,whole_CPU_s=cpu,whole_wall_s=wall,readback_files=len(inventory),raw_bytes=sum(x['bytes'] for x in manifest['files']),new_actual_native_reset_HOLDOUT_SEALED=0,no_policy_or_native_promotion=True,no_followup=True,best_native_s=13.640,research_remaining=26175,reserve=84000,reserve_used=0,plan_sha256=sha(d/'plan.json'))
        oldsave(G/'retry/mechanism479_result.json',public)
        oldsave(root/'stage479-checkpoint-private.json',dict(status=status,error=error,model_ticks=meter.b['ticks'],model_worlds=meter.b['worlds'],actual=0,wall_s=wall,CPU_s=cpu))
        require(meter.wholetime()[0]<180 and meter.wholetime()[1]<300,'479_AFTER_PUBLIC_CAP')
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        for s,h in handlers.items():signal.signal(s,h)
    print(json.dumps(dict(stage=479,status=status,error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds'],CPU_s=meter.wholetime()[0],wall_s=meter.wholetime()[1],actual=0)),flush=True)

if __name__=='__main__':
    root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
