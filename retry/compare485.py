"""One registered two-DEV attempt, all preparation included; fail closed."""
import time
START=time.perf_counter()
import datetime,hashlib,json,os,resource,shutil,signal,subprocess,sys,traceback
from pathlib import Path

G=Path(__file__).resolve().parents[1]
RAW=Path('/tmp/haic-retry-stage485-private')
DEADLINE='2026-10-20T10:01:55Z'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(x,msg):
    if not x:raise RuntimeError(msg)
def space():
    out={}
    for path,minimum in (('/tmp',1645413040),('/workspace',603979776)):
        free=shutil.disk_usage(path).free;require(free>=minimum,'485_FRESH_SPACE:'+path);out[path]=dict(free=free,minimum=minimum)
    return out
def unchanged(p):
    for group in ('sources','protected','original408_preserve'):
        for path,h in p[group].items():require(sha(path)==h,'485_FROZEN:'+path)
    require(sha(p['ledger_path'])==p['ledger_sha256'],'485_PRIOR_LEDGER')

def prepare(root):
    from retry.quota485 import RunQuota
    root=Path(root);d=root/'stage485'
    require(not d.exists() and not RAW.exists(),'485_ONCE_NEW')
    require(read(root/'research-deadline-current.json')['deadline_utc']==DEADLINE,'485_DEADLINE')
    require(datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(DEADLINE.replace('Z','+00:00')),'485_EXPIRED')
    old=read(root/'stage483-plan-durable-private.json');unchanged(old);before=space()
    auditpath=root/'stage485-identity-audit-revision1-private/audit-private.json'
    audit=read(auditpath)
    require(audit.get('passed') is True,'485_IDENTITY_AUDIT_NOT_PASSED')
    audit_sources=audit['artifacts']['sources-private.json']
    require(sha(audit_sources['path'])==audit_sources['sha256'],'485_AUDIT_SOURCES_PIN')
    audit_pins=read(audit_sources['path'])
    for path,h in audit_pins.items():require(sha(path)==h,'485_CURRENT_IDENTITY_SOURCE:'+path)
    exclusions=auditpath.parent/'exclusions-private.json'
    require(sha(exclusions)=='a8b6978dac1c574181f412527d6ad11a8f371d02ca7527701d40f4743479a4ac','485_EXCLUSIONS_PIN')
    # Register immutable implementation before selection. Static tests run in
    # their own process with constructors/steps forbidden by the gate module.
    test=subprocess.run([sys.executable,'-m','retry.static485'],cwd=G,text=True,capture_output=True)
    require(test.returncode==0,'485_STATIC_FAILED:'+test.stdout[-12000:]+test.stderr[-3000:])
    static=json.loads(test.stdout.strip().splitlines()[-1]);require(static['passed'],'485_STATIC_RESULT')
    from retry.compare477 import source_closure,runtime_environment
    names=['compare485.py','select485.py','meter485.py','online485.py','live485.py','source485.py','bootstrap485.py','history485.py','quota485.py','identity485.py','static485.py','test_policy485.py','test_history485.py','test_quota485.py','test_bootstrap485.py']
    require(all((G/'retry'/n).is_file() for n in names),'485_IMPLEMENTATION_INCOMPLETE')
    closure=source_closure([G/'retry'/n for n in names]);sources=dict(old['sources']);sources.update(audit_pins);sources.update({str(path):sha(path) for path in closure})
    sources.update({str(path):sha(path) for path in (auditpath,exclusions,G/'retry/independent484_contract.json',root/'research-deadline-current.json',root/'stage16/source_only_geometry.py')})
    semantic=dict(old['semantic_sources']);semantic.update({str(path):sha(path) for path in closure})
    growth=len(json.dumps(semantic,indent=2).encode())-len(json.dumps(old['semantic_sources'],indent=2).encode());require(growth<=8192,'485_HEADER_SOURCE_GROWTH')
    d.mkdir(mode=0o700);RAW.mkdir(mode=0o700)
    workspace_existing=[f for folder in root.glob('stage485-identity-audit*') for f in folder.rglob('*') if f.is_file()]
    q=RunQuota(RAW/'model',RAW/'native',workspace_paths=workspace_existing)
    for path in (d/'plan-private.json',d/'static-private.json',d/'preparation-private.json'):q.register_workspace(path)
    p=dict(stage=485,authorization='EXPLICIT_USER_SINGLE_TWO_FRESH_DEV_QUARTER_H6_256ACTUAL_2RESET_226MODEL1064T',deadline_utc=DEADLINE,contract_path=str(G/'retry/independent484_contract.json'),contract_sha256=sha(G/'retry/independent484_contract.json'),static_passed=True,authorized_to_select=True,identity_audit_path=str(auditpath),identity_audit_sha256=sha(auditpath),exclusions_path=str(exclusions),exclusions_sha256=sha(exclusions),sources=sources,semantic_sources=semantic,protected=old['protected'],original408_preserve=old['original408_preserve'],ledger_path=old['ledger_path'],ledger_sha256=old['ledger_sha256'],scope=dict(ticks=1064,worlds=226),caps=dict(ticks=1064,worlds=226,CPU_s=2400,wall_s=3000,actual_actions=256,resets=2),model_dir=str(q.model_dir),native_dir=str(q.native_dir),workspace_existing_paths=[str(f) for f in workspace_existing],space_before=before,space_final=space(),source_growth=growth,runtime_environment=runtime_environment(),no_followup=True)
    q.save_receipt(d/'plan-private.json',p);q.save_receipt(d/'static-private.json',static)
    q.save_receipt(q.model_dir/'plan.json',p)
    selection=subprocess.run([sys.executable,'-m','retry.select485',str(root)],cwd=G,text=True,capture_output=True)
    child=resource.getrusage(resource.RUSAGE_CHILDREN)
    q=RunQuota(RAW/'model',RAW/'native',workspace_paths=[*[f for f in d.rglob('*') if f.is_file()],*p.get('workspace_existing_paths',[])])
    q.register_workspace(d/'preparation-private.json')
    prep=dict(CPU_s=time.process_time()+child.ru_utime+child.ru_stime,wall_s=time.perf_counter()-START,development_conservative_CPU_s=60,development_conservative_wall_s=60,conservative_is_not_measurement=True,selection_exit=selection.returncode)
    q.save_receipt(d/'preparation-private.json',prep)
    require(selection.returncode==0,'485_SELECTION_STOP:'+selection.stderr[-3000:])
    print(json.dumps(dict(stage=485,phase='REGISTERED_TWO_IDENTITIES_FROZEN_NO_PHYSICS',static_tests=static['tests'],CPU_s=prep['CPU_s'],wall_s=prep['wall_s'],new_actual=0,new_resets=0,new_model=0)),flush=True)

def run(root):
    root=Path(root);d=root/'stage485';p=read(d/'plan-private.json');unchanged(p)
    from retry.quota485 import RunQuota
    from retry.io481 import load_receipt,read as decoded_read
    from retry.meter485 import Meter485
    from retry.bootstrap485 import prepare_case
    from retry.source485 import qualify
    from retry.online485 import execute
    from retry.history485 import finish_root_proof
    from retry.select485 import verify_live_identity
    model=Path(p['model_dir']);native=Path(p['native_dir']);require(not(model/'opening.json').exists(),'485_RUN_ONCE')
    # Selection already consumed only metadata space; the exact original full
    # minimum must still be available immediately before all physics.
    space();prep=read(d/'preparation-private.json')
    q=RunQuota(model,native,workspace_paths=[*[f for f in d.rglob('*') if f.is_file()],*p.get('workspace_existing_paths',[])])
    ledgerpath=root/'project-effective-budget-v485.json'
    checkpoint=d/'stage485-checkpoint-private.json'
    for path in (ledgerpath,checkpoint,d/'retention-manifest-private.json'):q.register_workspace(path)
    q.save_receipt(model/'opening.json',dict(stage=485,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(d/'plan-private.json')))
    codec=q.model_quota().install()
    meter=Meter485(model,worker_start=START,preparation_CPU_s=prep['CPU_s']+prep['development_conservative_CPU_s'],preparation_wall_s=prep['wall_s']+prep['development_conservative_wall_s'])
    meter.durable_checkpoint=lambda x:q.save(checkpoint,x)
    original=read(p['ledger_path']);journal=[]
    def charge(kind,slot,number):
        entry=dict(kind=kind,slot=slot,number=number,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        journal.append(entry)
        if kind in ('reset','action'):
            actions=meter.nb['actions']+(kind=='action')
            current={**original,'version':485,'prior_budget_path':p['ledger_path'],'prior_budget_sha256':p['ledger_sha256'],'research_remaining':26175-actions,'actual_cumulative_wrapper_actions':original['actual_cumulative_wrapper_actions']+actions,'stage485_new_wrapper_actions':actions,'stage485_native_resets':meter.nb['resets']+(kind=='reset'),'stage485_status':'SINGLE_ATTEMPT_ACTIVE','research_status':'STAGE485_SINGLE_REGISTERED_ATTEMPT','current_stage_execution_cap':'256actual/reset2/model226world1064ticks','charged_attempts_no_refund':True,'owner':dict(stage=485,pid=os.getpid(),plan_sha256=sha(d/'plan-private.json'))}
            require(current['research_remaining']>=25919 and current['final_reserved_actions']==84000 and current['final_reserve_used']==0,'485_LEDGER_BALANCE')
            q.save(ledgerpath,current)
        q.save(native/'charge-journal-private.json',dict(stage=485,events=journal))
    meter.native_charge_hook=charge
    def timeout(*_):raise RuntimeError('485_RESOURCE_OR_DEADLINE_STOP')
    signal.signal(signal.SIGPROF,timeout);signal.signal(signal.SIGALRM,timeout);meter.timers()
    outcomes=[];status='STARTED';error=None
    try:
        split=read(d/'split-private.json');require(len(split['cases'])==2,'485_TWO_ASSIGNED_CASES')
        for case in split['cases']:
            totals=q.summary()['bytes']
            remaining_tmp=512*1024**2+32*1024**2+sum(cap-totals[k] for k,cap in [('model',392471929),('native',648961335),('allocator',16*1024**2),('decision',16*1024**2)])
            require(shutil.disk_usage('/tmp').free>=remaining_tmp,'485_REMAINING_TMP_PREFLIGHT')
            require(shutil.disk_usage('/workspace').free>=512*1024**2+64*1024**2-totals['workspace'],'485_REMAINING_WORKSPACE_PREFLIGHT')
            meter.checkpoint('CASE_PREPARATION',slot=case['slot'])
            material=prepare_case(case,meter,q,root,coefficients_path=root/'stage268/selected-private.json',identity_check=verify_live_identity)
            meter.end_actual()
            if material['status']!='NATIVE_ROOT_AND_WITNESS_OBSERVED':
                status='PREPARATION_INELIGIBLE';error=material.get('error');break
            material.update(actual_root_ledger=material['context']['actual_ledger'],witness_row=material['witness']['row'],witness_posts=material['witness']['posts'],root_context_sha256=material['prefixproof']['root_context_sha256'],arm_order=case['arm_order'],prefix_proof=material['prefixproof'])
            with meter.model('485_'+case['slot']+'_source'):
                gatepath,gatehash=qualify(meter,material)
                proof=finish_root_proof(material['prefix_proof'],gatepath,gatehash)
                proofpath=model/(case['slot']+'-root-authority-private.json')
                codec.save_receipt(proofpath,proof)
                meter.p['root_proof_path']=str(proofpath);meter.p['root_proof_sha256']=sha(proofpath)
            meter.qualification_passed=True
            with meter.model('485_'+case['slot']+'_H6'):
                outcome=execute(meter,material)
            outcomes.append(outcome)
            meter.checkpoint('CASE_CLOSED',slot=case['slot'],verdict=outcome['verdict'])
            if outcome['reject']:status='REJECT';break
        else:status='TWO_CASE_BOUNDED_GATE_PASSED' if len(outcomes)==2 and all(o['success'] for o in outcomes) else 'NO_INFORMATION'
    except BaseException as e:
        status='TECHNICAL_OR_PREPARATION_STOP';error=type(e).__name__+': '+str(e)
        codec.save(model/'stop-private.json',dict(error=error,traceback=traceback.format_exc(),no_retry=True))
    finally:
        meter.end_actual();meter.closeall();meter.persist()
    unchanged(p)
    result=dict(stage=485,status=status,error=error,outcomes=outcomes,actual_actions=meter.nb['actions'],resets=meter.nb['resets'],native_raw=meter.raw_counts,model_worlds=meter.b['worlds'],model_ticks=meter.b['ticks'],model_charged_ticks=meter.charged_ticks,CPU_s=meter.wholetime()[0],wall_s=meter.wholetime()[1],research_remaining=26175-meter.nb['actions'],reserve=84000,reserve_used=0,quota=q.summary(),no_followup=True)
    codec.save(model/'result.json',result)
    if ledgerpath.exists():
        ledger=read(ledgerpath);ledger.update(stage485_status='CLOSED_NO_RETRY',research_status='STAGE485_CLOSED_'+status);q.save(ledgerpath,ledger)
    meter.checkpoint('CLOSED',status=status,error=error)
    inventory=[]
    for path in sorted(RAW.rglob('*')):
        if not path.is_file():continue
        b=path.read_bytes();h=hashlib.sha256(b).hexdigest();require(b==path.read_bytes(),'485_READBACK_BYTES')
        if path.suffix=='.json':
            obj=json.loads(b,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)));decoded_read(path);decoded_read(path)
            from retry.io481 import canonical
            decoded_hash=canonical(load_receipt(path))
            if path.name.startswith('state-'):require(canonical(obj['full_state'])==obj['sha256'],'485_FULL_STATE_OBJECT_DIGEST')
        else:decoded_hash=None
        inventory.append(dict(path=str(path),bytes=len(b),sha256=h,decoded_sha256=decoded_hash,readbacks=2))
    result.update(CPU_s=meter.wholetime()[0],wall_s=meter.wholetime()[1],quota=q.summary(),complete_raw_readback=True)
    codec.save(model/'result.json',result)
    for entry in inventory:
        if entry['path']==str(model/'result.json'):
            path=Path(entry['path']);data=path.read_bytes();require(data==path.read_bytes(),'485_FINAL_RESULT_READBACK');decoded_read(path);decoded_read(path);entry.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),decoded_sha256=canonical(load_receipt(path)))
    q.save(d/'retention-manifest-private.json',dict(stage=485,files=inventory,single_raw_copy=True,tmp_loss_not_recoverable_from_hashes=True))
    # No further mutable raw controls after final manifest authentication.
    meter.check_storage();require(meter.wholetime()[0]<2400 and meter.wholetime()[1]<3000,'485_FINAL_WHOLE_CAP')
    signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
    print(json.dumps(dict(stage=485,status=status,error=error,actual=meter.nb['actions'],resets=meter.nb['resets'],worlds=meter.b['worlds'],ticks=meter.b['ticks'],charged=meter.charged_ticks,CPU_s=meter.wholetime()[0],wall_s=meter.wholetime()[1])),flush=True)

if __name__=='__main__':
    prepare(Path(sys.argv[2])) if sys.argv[1]=='prepare' else run(Path(sys.argv[2]))
