"""One explicit492 known-first485 diagnostic; no retry, selection or optimization."""
import time
START=time.perf_counter()
import ast,copy,datetime,hashlib,json,os,resource,shutil,signal,sys,traceback
from pathlib import Path
from types import SimpleNamespace as NS

G=Path(__file__).resolve().parents[1]
R=Path('/workspace/haic-private-retry-20261009')
D=R/'stage492'
RAW=Path('/tmp/haic-retry-stage492-private')
INPUT=Path('/tmp/haic-retry-stage490-private/input-manifest-private.json')
INITIAL=Path('/tmp/haic-retry-stage485-private/native/D485-A/initial-full-private.json')
DEADLINE='2026-10-20T10:01:55Z'

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(v,msg):
    if not v:raise RuntimeError('492_'+msg)
def syncdir(p):
    f=os.open(p,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(f)
    finally:os.close(f)
def space():
    out={}
    for path,minimum in (('/tmp',1031798784),('/workspace',553648128)):
        free=shutil.disk_usage(path).free;require(free>=minimum,'FRESH_SPACE:'+path);out[path]=dict(free=free,minimum=minimum)
    return out

def first_case_only(path):
    # Stop reading at the first case's closing brace. Second case is never read.
    prefix='';obj='';level=0;string=False;escaped=False;started=False
    with Path(path).open() as f:
        while '"cases"' not in prefix:
            char=f.read(1);require(bool(char),'CASE_FIELD');prefix+=char
        while True:
            char=f.read(1);require(bool(char),'FIRST_CASE')
            if not started:
                if char!='{':continue
                started=True
            obj+=char
            if string:
                if escaped:escaped=False
                elif char=='\\':escaped=True
                elif char=='"':string=False
            elif char=='"':string=True
            elif char=='{':level+=1
            elif char=='}':
                level-=1
                if level==0:break
    result=json.loads(obj);require(result['slot']=='D485-A' and result['split']=='DEV','KNOWN_FIRST_ONLY')
    result.update(slot='D492-A',original_slot='D485-A',known_exposed_DEV=True,fresh_DEV_identity=False)
    return result

def preservation():
    old=read(R/'stage485/plan-private.json');count=0
    for group in ('sources','protected','original408_preserve'):
        for path,digest in old[group].items():require(sha(path)==digest,'PRESERVED:'+path);count+=1
    require(sha(old['ledger_path'])==old['ledger_sha256'],'OLD_LEDGER_PIN')
    prior=read(R/'stage491-retention-final-private.json')
    for row in prior['files']:require(sha(row['path'])==row['sha256'],'491_PRESERVED:'+row['path']);count+=1
    return dict(entries=count,main_expected='dfb7a2de2178825ca5c5ce20bab01ba67052ba31',old397_417_and490_unchanged=True)

def run():
    require(not D.exists() and not RAW.exists(),'SINGLE_ONCE_NEW_ROOT')
    require(read(R/'research-deadline-current.json')['deadline_utc']==DEADLINE,'LATEST_DEADLINE')
    require(datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(DEADLINE.replace('Z','+00:00')),'EXPIRED')
    before=space();preserve=preservation()
    import numpy as np
    from retry.executor490_input import load,array_sha
    from retry.runtime492 import Graph,canonical_projection,CoherentExecutor491,ExecutorDomainError
    from retry.quota492 import RunQuota
    from retry.meter492 import bind_dependencies
    from retry.history492 import install
    from retry.bootstrap492 import prepare_case
    from retry.source492 import qualify
    from retry.static492 import run as static
    require(sha(INPUT)=='8352db032e5083830d976adfaf713af87c0b22e6df6e23744ebc8f7ccfbab13b','INPUT_SHA')
    frozen,pace,nodes=load(INPUT)
    def plain(v):
        if isinstance(v,np.ndarray):return plain(v.tolist())
        if isinstance(v,np.generic):return v.item()
        if isinstance(v,dict):return {k:plain(x) for k,x in v.items()}
        if isinstance(v,(list,tuple)):return [plain(x) for x in v]
        return v
    fixed=plain(frozen);require(array_sha(fixed['line'])==array_sha(frozen['line']),'CONTAINER_LINE_BYTES')
    binding=dict(input_manifest_sha256=sha(INPUT),projection491_sha256=sha(G/'retry/projection491.py'),runtime492_sha256=sha(G/'retry/runtime492.py'),line_sha256=array_sha(fixed['line']),nodes_sha256=array_sha(nodes))
    runtime=Graph(binding,fixed,pace,nodes).install();runtime.input_manifest_path=str(INPUT);runtime.graph=runtime
    history=install(runtime)
    names=('online485','live485','observer435','law477','pilot420_backend','ledger439','geometry439','online481','planner419','planner419_model_ledger','mechanism479','receipt421_io','loss389_analyze','authority439','paired417_common','fork394_run','terminal410_model','loss389_replay','meter453','paired442_meter','capture434','io481','executor490_input')
    modules={name:runtime.import_module(name) for name in names}
    # Load source helper closure before installing the cloned writers.
    runtime.audit()
    codec_module=modules['io481']
    D.mkdir(mode=0o700);RAW.mkdir(mode=0o700);syncdir(R);syncdir(RAW.parent)
    workspace=[G/'retry'/name for name in ('runtime492.py','quota492.py','meter492.py','history492.py','source492.py','bootstrap492.py','static492.py','compare492.py','diagnostic492_contract.json')]
    q=RunQuota(RAW/'model',RAW/'native',workspace_paths=workspace,codec_module=codec_module,install_modules=runtime.modules.values())
    syncdir(RAW);syncdir(q.model_dir);syncdir(q.native_dir)
    for name in ('plan-private.json','knowncase-reference-private.json','static-private.json','stage492-checkpoint-private.json','retention-manifest-private.json','final-control-private.json'):
        q.register_workspace(D/name)
    ledgerpath=R/'project-effective-budget-v492.json';q.register_workspace(ledgerpath)
    sources={row['path']:row['source_sha256'] for row in runtime.records.values()}
    sources.update({str(p):sha(p) for p in workspace})
    sources.update({str(p):sha(p) for p in (G/'core').rglob('*.py')})
    sources[str(INPUT)]=sha(INPUT)
    p=dict(stage=492,authorization='EXPLICIT_SINGLE_KNOWN_FIRST485_FIXED490_OPTIN491_LIMITED_FAIL_CLOSED',deadline_utc=DEADLINE,binding=binding,contract_path=str(G/'retry/diagnostic492_contract.json'),contract_sha256=sha(G/'retry/diagnostic492_contract.json'),semantic_sources=sources,sources=sources,scope=dict(ticks=536,worlds=113),caps=dict(ticks=536,worlds=113,CPU_s=900,wall_s=1200,actual_actions=129,resets=1),model_dir=str(q.model_dir),native_dir=str(q.native_dir),input_manifest_path=str(INPUT),input_manifest_sha256=sha(INPUT),ledger_path=str(R/'project-effective-budget-v485.json'),ledger_sha256=sha(R/'project-effective-budget-v485.json'),source_namespace_audit=runtime.audit(),space_before=before,preservation=preserve,no_followup=True,static_passed=False)
    q.save_receipt(D/'plan-private.json',p)
    q.save_receipt(q.model_dir/'plan.json',p)
    codec=q.model_quota().install();runtime.codec=codec
    Meter=bind_dependencies(modules)
    meter=Meter(q.model_dir,worker_start=START)
    meter.durable_checkpoint=lambda value:q.save(D/'stage492-checkpoint-private.json',value)
    # Frozen492 allocator bound before imported online485 captures the function.
    live=modules['live485'];old_allocate=live.allocate_current
    def bounded_allocate(child,nominal,index):
        if child.meter.allocator_calls>=26:raise modules['pilot420_backend'].ResourceStop('492_allocator26')
        return old_allocate(child,nominal,index)
    live.allocate_current=bounded_allocate;modules['online485'].allocate_current=bounded_allocate
    for key,modname in [('ActualC','paired417_common'),('Trace','paired417_common'),('NativeAuthority439','authority439'),('complete_state','fork394_run'),('from_actual_full','terminal410_model'),('sensor','loss389_replay'),('GoalLedger','planner419'),('ForecastLedger','planner419_model_ledger'),('TechnicalStop','pilot420_backend'),('ResourceStop','pilot420_backend'),('fingerprint','pilot420_backend'),('sha','loss389_analyze'),('require','ledger439'),('LedgerStop439','ledger439')]:setattr(runtime,key,getattr(modules[modname],key))
    runtime.canonical_projection=canonical_projection;runtime.ExecutorDomainError=ExecutorDomainError
    # Existing diagnose factory is reached through the isolated graph only.
    runtime.make_env=runtime.import_module('diagnose').make_env
    initial=read(INITIAL);runtime.expected_initial_observation_sha256=initial['observation_sha256']
    original=read(p['ledger_path']);require(original['research_remaining']==26175 and original['final_reserved_actions']==84000 and original['final_reserve_used']==0,'BUDGET_OPEN')
    journal=[];append_log=b''
    def charge(kind,slot,number):
        nonlocal append_log
        entry=dict(sequence=len(journal)+1,kind=kind,slot=slot,number=number,binding=binding,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),precharged=True)
        journal.append(entry)
        actions=meter.nb['actions']+int(kind=='action');resets=meter.nb['resets']+int(kind=='reset')
        current={**original,'version':492,'prior_budget_path':p['ledger_path'],'prior_budget_sha256':p['ledger_sha256'],'research_remaining':26175-actions,'actual_cumulative_wrapper_actions':original['actual_cumulative_wrapper_actions']+actions,'stage492_new_wrapper_actions':actions,'stage492_native_resets':resets,'stage492_status':'SINGLE_ATTEMPT_ACTIVE','research_status':'STAGE492_SINGLE_REGISTERED_ATTEMPT','charged_attempts_no_refund':True,'owner':dict(stage=492,pid=os.getpid(),plan_sha256=sha(D/'plan-private.json'))}
        require(current['research_remaining']>=26046 and current['final_reserved_actions']==84000 and current['final_reserve_used']==0,'BUDGET_FLOOR')
        # Logical append-only journal: prior bytes are an immutable prefix; the
        # atomic durable publication retains one copy within the file cap.
        logpath=q.native_dir/'global-charge-journal-private.jsonl'
        require(not logpath.exists() or logpath.read_bytes()==append_log,'CHARGE_LOG_PREFIX')
        append_log+=(json.dumps(entry,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
        q.write_bytes(logpath,append_log)
        q.save(ledgerpath,current)
        q.save(q.native_dir/'charge-journal-private.json',dict(stage=492,binding=binding,events=journal))
        syncdir(q.native_dir);syncdir(R)
    meter.native_charge_hook=charge
    def timeout(*_):raise RuntimeError('492_RESOURCE_OR_DEADLINE_STOP')
    signal.signal(signal.SIGPROF,timeout);signal.signal(signal.SIGALRM,timeout);meter.timers()
    status='STATIC_PREPARATION';error=None;outcome=None;static_result=None;material=None
    def identity_check(case,env):
        raw=env.unwrapped
        road=array_sha(np.asarray(raw.track,dtype='<f8'));obs=array_sha([[*body.position,body.fixtures[0].shape.radius] for body in raw.obstacles])
        require(road==case['road_geometry_sha256'] and obs==case['expected_physical_obstacles_sha256'],'KNOWN_LIVE_IDENTITY')
        return dict(road_geometry_sha256=road,physical_obstacles_sha256=obs,old_first485_identity=True)
    try:
        static_result=static(runtime,q,Meter,initial,fixed,pace,nodes)
        require(static_result['passed'],'STATIC_FAILED')
        q.save_receipt(D/'static-private.json',static_result)
        case=first_case_only(R/'stage485/split-private.json')
        q.save_receipt(D/'knowncase-reference-private.json',dict(case=case,first_case_only_streamed=True,second_condition_read=False,binding=binding,original_initial_path=str(INITIAL),original_initial_sha256=sha(INITIAL)))
        # Final pin closure includes lazy imports and static source; immutable plan
        # is revised only before physics, never after native facts appear.
        sources.update({row['path']:row['source_sha256'] for row in runtime.records.values()})
        p.update(static_passed=True,static_path=str(D/'static-private.json'),static_sha256=sha(D/'static-private.json'),space_final=space(),source_namespace_audit=runtime.audit())
        q.save(D/'plan-private.json',p);codec.save(q.model_dir/'plan.json',p);meter.p=copy.deepcopy(p);meter.plan_sha=sha(q.model_dir/'plan.json')
        meter.checkpoint('ALL_STATIC_GATES_PASSED_NO_PHYSICS',static_tests=static_result.get('tests'),case_identity_digest=case['case_identity_digest'])
        for path,digest in sources.items():require(sha(path)==digest,'PREPHYSICS_SOURCE_PIN:'+path)
        q.full_readback();space();syncdir(q.native_dir)
        material=prepare_case(case,meter,q,R,fixed=fixed,pace=pace,nodes=nodes,input_manifest_sha256=sha(INPUT),identity_check=identity_check,runtime=runtime)
        if material['status']!='NATIVE_ROOT_AND_TWO_WITNESSES_OBSERVED':
            status=material['status'];error=material.get('error')
        else:
            material['arm_order']=case['arm_order']
            with meter.model('492_SOURCE_COLD_AND_GENUINE_WARM'):
                gatepath,gatehash=qualify(meter,material,runtime=runtime)
                proof=history.finish_root_proof(material['prefixproof'],gatepath,gatehash)
                proofpath=q.model_dir/'D492-A-root-authority-private.json';codec.save_receipt(proofpath,proof)
                history.authenticate_root492(proof,material['state'],material['context']['ledger'],material['before'],fixed['line'])
                meter.p.update(root_proof_path=str(proofpath),root_proof_sha256=sha(proofpath))
            meter.qualification_passed=True
            with meter.model('492_H6_TWO_RANKS'):
                outcome=modules['online485'].execute(meter,material)
            status=outcome['verdict']
    except BaseException as exc:
        status='TECHNICAL_OR_GATE_STOP';error=type(exc).__name__+': '+str(exc)
        codec.save(q.model_dir/'stop-private.json',dict(stage=492,binding=binding,status=status,error=error,traceback=traceback.format_exc(),no_retry=True))
    finally:
        meter.end_actual();meter.closeall();meter.persist()
    # No retry, replacement root, posthoc source repair or new condition.
    preserved=preservation();audit=runtime.audit()
    if ledgerpath.exists():
        current=read(ledgerpath);current.update(stage492_status='CLOSED_NO_RETRY',research_status='STAGE492_CLOSED_'+status);q.save(ledgerpath,current)
    meter.checkpoint('CLOSED',status=status,error=error)
    result=dict(stage=492,status=status,error=error,binding=binding,static=static_result,outcome=outcome,actual_actions=meter.nb['actions'],resets=meter.nb['resets'],native_raw=meter.raw_counts,model_worlds=meter.b['worlds'],model_ticks=meter.b['ticks'],model_charged_ticks=meter.charged_ticks,model_wrapper_slots=meter.wrapper_slots,allocator_calls=meter.allocator_calls,model_time=dict(zip(('CPU_s','wall_s'),meter.modeltime())),native_time=dict(zip(('CPU_s','wall_s'),meter.nativetime())),CPU_s=meter.wholetime()[0],wall_s=meter.wholetime()[1],RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,research_remaining=26175-meter.nb['actions'],reserve=84000,reserve_used=0,quota=q.summary(),preservation=preserved,source_alias_audit=dict(modules=audit['modules'],all_canonical_exports_491=True),new_geometry_profile_P4_seed_conditions_HOLDOUT_SEALED=0,native_promotion=False,no_followup=True)
    codec.save(q.model_dir/'result.json',result)
    inventory=q.full_readback()
    for path,record in inventory.items():
        require(sha(path)==record['sha256'],'SECOND_FULL_READBACK')
        if Path(path).suffix=='.json':
            if q.model_dir in Path(path).parents:
                a=codec_module.load_receipt(path);b=codec_module.load_receipt(path)
                require(codec_module.canonical(a)==codec_module.canonical(b),'DECODED_READBACK')
            else:json.loads(Path(path).read_bytes(),parse_constant=lambda value:(_ for _ in ()).throw(ValueError(value)))
    result.update(CPU_s=meter.wholetime()[0],wall_s=meter.wholetime()[1],quota=q.summary(),full_raw_readbacks=2)
    codec.save(q.model_dir/'result.json',result)
    inventory=q.full_readback()
    q.save(D/'retention-manifest-private.json',dict(stage=492,files=inventory,no_raw_copies=True,binding=binding))
    q.save(D/'final-control-private.json',dict(stage=492,status=status,error=error,result_path=str(q.model_dir/'result.json'),result_sha256=sha(q.model_dir/'result.json'),retention_sha256=sha(D/'retention-manifest-private.json'),no_retry=True,deadline_utc=DEADLINE,CPU_s=meter.wholetime()[0],wall_s=meter.wholetime()[1]))
    q.full_readback();meter.check_storage()
    require(meter.wholetime()[0]<900 and meter.wholetime()[1]<1200,'FINAL_WHOLE_CAP')
    signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
    print(json.dumps({k:result[k] for k in ('stage','status','error','actual_actions','resets','native_raw','model_worlds','model_ticks','model_charged_ticks','allocator_calls','CPU_s','wall_s','research_remaining','no_followup')}),flush=True)

if __name__=='__main__':run()
