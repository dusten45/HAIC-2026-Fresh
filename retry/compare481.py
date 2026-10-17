"""481 once-only registered mechanism runner, full readback included in caps."""
import time
WORKER_START=time.perf_counter()
import ast,copy,datetime,hashlib,json,os,pickle,random,shutil,signal,sys,traceback
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.compare477 import source_closure,runtime_environment
from retry.law477 import root_inputs477
from retry.meter481 import Meter481
from retry.online481 import execute
from retry.io481 import Quota
from retry.loss389_analyze import read,save,sha
from retry.receipt421_io import save_receipt
from retry.ledger439 import require
from retry.pilot420_backend import ResourceStop
G=Path(__file__).resolve().parents[1]
RAW=Path('/tmp/haic-retry-stage481-private')
CAPS=dict(ticks=4840,worlds=812,CPU_s=900,wall_s=1200,actual_actions=0,resets=0,max_parallel=1)
NAMES=('compare481.py','online481.py','meter481.py','live481.py','io481.py','history481.py','test_history481.py','static481.py')

def space(p):
    s=p['storage_forecast'];out={}
    for v,need in [('/tmp',s['tmp_required_bytes']),('/workspace',s['workspace_required_bytes'])]:
        free=shutil.disk_usage(v).free;require(free>=need,'481_STORAGE_PREFLIGHT:'+v)
        out[v]=dict(free_bytes=free,required_bytes=need)
    return out

def prepare(root):
    from retry.static481 import run as integrated_static
    d=root/'stage481';require(not d.exists() and not d.is_symlink() and not RAW.exists(),'481_ONCE_FRESH')
    gate=integrated_static();require(gate['passed'],'481_INTEGRATED_STATIC_FAILED:'+gate['failures'])
    old=read(root/'stage479-plan-durable-private.json');contract=read(G/'retry/online480_contract.json')
    require(contract['selected']['id']=='B200' and contract['selected']['counts']['charged_ticks']==4840 and contract['selected']['counts']['worlds']==812,'481_APPROVED_SCOPE')
    require(read(root/'research-deadline-current.json')['deadline_utc']==contract['deadline_utc']=='2026-10-20T10:01:55Z','481_DEADLINE_PIN')
    require(sha(root/'stage441/authorization-correction-private.json')=='3b0dc9c16c5356e107e73dbd8a8f88e75a2434f9e24f046358783fbde8307078','481_EXPLICIT_EXTENSION')
    for group in ('sources','protected','original408_preserve'):
        for f,h in old[group].items():require(sha(f)==h,'481_FROZEN_SOURCE_CHANGED:'+f)
    state,memory,ledger,rng,blob,expected=root_inputs477(root)
    sources=dict(old['sources']);closure=source_closure([G/'retry'/n for n in NAMES]);sources.update({str(f):sha(f) for f in closure})
    semantic=dict(old['semantic_sources']);semantic.update({str(f):sha(f) for f in closure})
    growth=max(0,len(json.dumps(semantic,indent=2).encode())-len(json.dumps(old['semantic_sources'],indent=2).encode()))
    require(growth<=8192,'481_MANIFEST_GROWTH8KiB')
    paths=[G/'retry/online480_contract.json',G/'retry/online480_result.md',root/'stage480-plan-durable-private.json',root/'stage480-retention-manifest-private.json',root/'stage479-retention-manifest-private.json',root/'stage479-publication-private.json',root/'research-deadline-current.json']
    stop=read(root/'stage435/parent_P-observer-private.json');n=stop['link']['world_number']
    paths += [root/p for p in ['stage435/P_decision55-context-stop-private.json','stage435/parent_P-private.json','stage435/parent_P-observer-private.json',f'stage435/world{n}-before-constructor-private.json']]
    sources.update({str(f):sha(f) for f in paths})
    s=contract['selected']['storage'];model=s['model_raw_hard_bytes']
    require(Quota.STATE_MAX*Quota.STATES_MAX+Quota.NONSTATE_MODEL_MAX<=model,'481_NEW_FORMAT_WORST_BOUND')
    # No speculative saving: retain the approved model/proof/decision/temp/reserve caps.
    p=dict(stage=481,authorization='EXPLICIT_USER_B200_ONCE_AFTER_INTEGRATED_STATIC_NO_NATIVE',registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=contract['deadline_utc'],contract480_sha256=sha(G/'retry/online480_contract.json'),caps=CAPS,scope=dict(ticks=4840,worlds=812),contract=contract,counts=contract['selected']['counts'],
        fixed_plan=old['fixed_plan'],pace_path=old['pace_path'],projection_path=old['projection_path'],sources=sources,semantic_sources=semantic,protected=old['protected'],original408_preserve=old['original408_preserve'],ledger_path=old['ledger_path'],ledger_sha256=old['ledger_sha256'],storage_free_stop_bytes=512*1024**2,
        nominal_once='SourceC once perownboundary. Prepared after-memory in shadow, before-memory inrow. Fullledger beforeStream. Both FIRST_LAP/FINISH_CONFIRM checked; only ownphysicalfinish marksDONE.',parent_isolation='Full physical/memory/ledger/RNG/nodes/rows/status before/after eachone-passforecast and selected independent repeat.',source_closure='All local AST imports+old477/479qualification retained, no35/H13rerun. Integrated static poisons model constructors/steps.',
        raw_directory=str(RAW),runtime_environment=runtime_environment(),actual=0,resets=0,HOLDOUT=0,SEALED=0,no_followup=True,
        state_codec=dict(version=1,scope='New full state objects only; unchanged inline source maps. Lossless original decoded payload SHA checked onread; no old evidence rewrite.',state_object_limit=Quota.STATES_MAX,state_object_bytes=Quota.STATE_MAX,nonstate_model_bytes=Quota.NONSTATE_MODEL_MAX,total_format_upper_bytes=Quota.STATE_MAX*Quota.STATES_MAX+Quota.NONSTATE_MODEL_MAX,unique_bound='<=two snapshots/world plusone/currentallocatorcontext and4fixedsource roots; no early-stop or commanddedup assumption. Model cap unchanged.',currentroot_RNG_input_checks_preserved=True))
    p['storage_forecast']=dict(model_payload_bytes=model,allocator_extra_bytes=s['allocator_proof_hard_budget_bytes'],selection_extra_bytes=s['selection_summary_hard_budget_bytes'],tmp_required_bytes=s['tmp_required_bytes'],workspace_required_bytes=s['workspace_required_bytes'],semantic_actual_growth_bytes=growth,semantic_growth_hard_allowance_bytes=8192,selection_summary_bytes_each=65536,temp_bytes=s['temp_bytes'],reserve_bytes_each_volume=s['reserve_each_bytes'],new_archive=False,workspace_new_raw_archive_copy=False)
    # Existinginline header estimate still fits registered829,464B allowance.
    base=sum(max((f.stat().st_size for f in (root/'stage479').glob(pattern)),default=0) for pattern in ['world*-before-constructor-private.json','world*-before-first-step-private.json','*-runtime-link-private.json'])
    p['estimated_header_without_state_intern_saving']=base+3*growth+16384
    require(p['estimated_header_without_state_intern_saving']<=s['header_hard_each_bytes'],'481_HEADER_GROWTH_BOUND')
    p['storage_preflight']=space(p)
    material=root/'stage481-input-material-private.json';require(not material.exists(),'481_NEW_INPUT_ONLY')
    save_receipt(material,dict(state=state,memory=memory,ledger=asdict(ledger),RNG_blob=blob,RNG_source=rng,expected=expected,fixed=read(old['fixed_plan']),pace=read(old['pace_path']),projected_nodes=read(old['projection_path'])['projected_nodes']))
    p['input_material_path']=str(material);p['input_material_sha256']=sha(material);p['sources'][str(material)]=sha(material)
    require(material.stat().st_size+len(json.dumps(p).encode())<64*1024**2,'481_WORKSPACE_METADATA64MiB');require(len(json.dumps(p,indent=2).encode())<=2*1024**2,'481_PLAN2MiB')
    RAW.mkdir(mode=0o700);d.symlink_to(RAW,target_is_directory=True);save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(root/'stage481-plan-durable-private.json',p)
    save(d/'static-result.json',dict(stage=481,passed=True,plan_sha256=sha(d/'plan.json'),gate=gate,new_worlds=0,new_physics=0))
    save(d/'preparation-cost.json',dict(CPU_s=time.process_time(),wall_s=time.perf_counter()-WORKER_START,scope='Registration+integratedstatic+source/input/space verification andimports; added to worker caps'))
    print(json.dumps(dict(stage=481,phase='STATIC_REGISTERED_NO_PHYSICS',tests=gate['tests'],plan_sha256=sha(d/'plan.json'),source_manifest_growth=growth,format_bound=p['state_codec'],storage=p['storage_preflight'])),flush=True)

def run(root):
    d=root/'stage481';p=read(d/'plan.json');oldsave=save
    require(not(d/'opening.json').exists() and read(d/'static-result.json')['passed'],'481_ONCE_STATIC')
    require(sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()==read(d/'static-result.json')['plan_sha256'],'481_PLAN_BINDING')
    for group in ('sources','protected','original408_preserve'):
        for f,h in p[group].items():require(sha(f)==h,'481_RUN_SOURCE:'+f)
    require(p['caps']==CAPS and p['scope']==dict(ticks=4840,worlds=812),'481_RUN_FIXED_SCOPE');space(p)
    state,memory,ledger,rng,blob,expected=root_inputs477(root);py,npr=pickle.loads(blob);random.setstate(py);np.random.set_state(npr)
    fixed=read(p['fixed_plan']);pace=np.asarray(read(p['pace_path'])['frozen268']);prep=read(d/'preparation-cost.json');meter=Meter481(d,worker_start=WORKER_START,preparation_CPU_s=prep['CPU_s'],preparation_wall_s=prep['wall_s'])
    meter.quota=Quota(d,p['storage_forecast']['model_payload_bytes'],p['storage_forecast']['allocator_extra_bytes'],p['storage_forecast']['selection_extra_bytes']).install()
    status='STARTED';error=None;outcome=None;inventory=[]
    save(d/'opening.json',dict(stage=481,pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(d/'plan.json')))
    def timeout(*args):raise ResourceStop('481_WHOLE_CPU900_WALL1200_DEADLINE')
    handlers={s:signal.signal(s,timeout) for s in (signal.SIGPROF,signal.SIGALRM)};meter.timers()
    try:
        with meter.model('481_B200_one_model_pair'):
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
            for f,h in p[group].items():require(sha(f)==h,'481_FINAL_SOURCE:'+f)
        require(sha(p['ledger_path'])==p['ledger_sha256'],'481_GLOBAL_LEDGER_CHANGED')
        save(d/'result.json',dict(stage=481,status=status,error=error,outcome=outcome,budget=read(d/'budget.json'),new_native=0,new_resets=0,new_HOLDOUT_SEALED=0,no_followup=True))
        for f in sorted(d.iterdir()):
            if not f.is_file():continue
            data=f.read_bytes();digest=hashlib.sha256(data).hexdigest()
            if f.suffix=='.json':
                raw=json.loads(data,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)));decoded=read(f)
                if f.name.startswith('state-'):
                    from retry.io481 import canonical
                    require(canonical(raw['full_state'])==raw['sha256'],'481_STATE_OBJECT_READBACK')
            again=f.read_bytes();require(len(data)==len(again) and hashlib.sha256(again).hexdigest()==digest,'481_FULL_READBACK:'+f.name)
            inventory.append(dict(path=str(f),bytes=len(data),sha256=digest,full_readbacks=2))
        oldsave(root/'stage481-retention-manifest-private.json',dict(stage=481,files=inventory,new_archive=False,workspace_new_raw_copies=0,tmp_loss='Hashes cannot reconstruct lost raw'))
        # Result/closed budget are final control records; their final hashes are
        # stored durably after their own complete readbacks.
        meter.checkpoint('CLOSED',status=status,error=error)
        result=read(d/'result.json');result['budget']=read(d/'budget.json');result['readback_file_count']=len(inventory);save(d/'result.json',result)
        manifest=read(root/'stage481-retention-manifest-private.json')
        for record in manifest['files']:
            f=Path(record['path'])
            if f.name in ('result.json','progress-private.json','budget.json'):
                data=f.read_bytes();a=f.read_bytes();require(data==a,'481_FINAL_CONTROL_READBACK');json.loads(data);record.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        oldsave(root/'stage481-retention-manifest-private.json',manifest)
        cpu,wall=meter.wholetime();require(cpu<900 and wall<1200,'481_FINAL_WHOLE_CAP')
        public_outcome=None if outcome is None else {k:v for k,v in outcome.items() if k!='online_queries'}
        if outcome is not None:
            from collections import Counter
            qq=outcome.get('online_queries',[]);aliases=Counter(alias for q in qq for alias in q.get('selected_aliases',[]))
            public_outcome['online_query_aggregate']=dict(queries=len(qq),selected_alias_counts=dict(aliases),own_holds=sum('own_M80' in q for q in qq),empty_domain_queries=sum(q.get('status')=='EMPTY_FINITE_CANDIDATE_DOMAIN' for q in qq),max_own_M80=max((q['own_M80'] for q in qq if 'own_M80' in q),default=None),max_own_post_path_error_m=max((q['path_error_m'] for q in qq if 'path_error_m' in q),default=None),unselected_independent_repeats=False,unselected_warm_counterfactual_observed=False)
        public=dict(stage=481,status=status,error=error,outcome=public_outcome,model_ticks=meter.b['ticks'],reserved_ticks=meter.b['reserved_ticks'],charged_ticks=meter.charged_ticks,model_worlds=meter.b['worlds'],allocator_calls=meter.allocator_calls,preparation_cost=prep,allocator_CPU_s=meter.allocator_CPU_s,allocator_wall_s=meter.allocator_wall_s,whole_CPU_s=cpu,whole_wall_s=wall,readback_files=len(inventory),raw_bytes=sum(x['bytes'] for x in manifest['files']),new_actual_native_reset_HOLDOUT_SEALED=0,no_policy_or_native_promotion=True,no_followup=True,best_native_s=13.640,research_remaining=26175,reserve=84000,reserve_used=0,plan_sha256=sha(d/'plan.json'))
        oldsave(G/'retry/online481_result.json',public)
        oldsave(root/'stage481-checkpoint-private.json',dict(status=status,error=error,model_ticks=meter.b['ticks'],model_worlds=meter.b['worlds'],actual=0,wall_s=wall,CPU_s=cpu))
        require(meter.wholetime()[0]<900 and meter.wholetime()[1]<1200,'481_AFTER_PUBLIC_CAP')
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        for s,h in handlers.items():signal.signal(s,h)
    print(json.dumps(dict(stage=481,status=status,error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds'],CPU_s=meter.wholetime()[0],wall_s=meter.wholetime()[1],actual=0)),flush=True)

if __name__=='__main__':
    root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
