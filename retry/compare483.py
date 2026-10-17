"""Register then run the approved483 H6 comparison exactly once; no native API."""
import time
START=time.perf_counter()
import datetime,hashlib,json,os,pickle,random,shutil,signal,sys,traceback
from pathlib import Path
import numpy as np
from retry.compare477 import source_closure,runtime_environment
from retry.root483 import authenticate
from retry.static483 import run as static_gate
from retry.online483 import execute
from retry.meter483 import Meter483
from retry.io483 import Quota,read,load_receipt,canonical,CODEC_KEY
from retry.loss389_analyze import save,sha
from retry.receipt421_io import save_receipt
from retry.ledger439 import require
G=Path(__file__).resolve().parents[1]
RAW=Path('/tmp/haic-retry-stage483-private')
CAPS=dict(ticks=520,worlds=110,CPU_s=480,wall_s=600,actual_actions=0,resets=0,max_integrating=1,max_live=2,wrapper_slots=130,allocator_calls=26)
NAMES=('compare483.py','online483.py','root483.py','static483.py','meter483.py','io483.py','live483.py','history483.py','test_history483.py')
DEV_CHARGE=dict(CPU_s=20.,wall_s=20.,kind='Conservative charge, not measurement, for pre-registration import/stub-fixture corrections and development static checks. New physics0.')

def space():
    out={}
    for v,need in (('/tmp',805065224),('/workspace',603979776)):
        free=shutil.disk_usage(v).free;require(free>=need,'483_STORAGE_PREFLIGHT:'+v);out[v]=dict(free_bytes=free,minimum_required_bytes=need)
    return out

def unchanged(p):
    for group in ('sources','protected','original408_preserve'):
        for name,digest in p[group].items():require(sha(name)==digest,'483_FROZEN_SOURCE:'+name)
    require(sha(p['ledger_path'])==p['ledger_sha256'],'483_GLOBAL_LEDGER_CHANGED')

def prepare(root):
    require(not(root/'stage483').exists() and not(root/'stage483').is_symlink() and not RAW.exists(),'483_ONCE_NEW')
    opening=root/'stage483-preparation-opening-private.json';require(not opening.exists(),'483_PREPARE_ONCE')
    save(opening,dict(stage=483,pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),new_physics=0,development_charge=DEV_CHARGE))
    def failure(*args):raise RuntimeError('483_PREPARATION_RESOURCE_OR_DEADLINE')
    signal.signal(signal.SIGPROF,failure);signal.signal(signal.SIGALRM,failure)
    signal.setitimer(signal.ITIMER_PROF,460);signal.setitimer(signal.ITIMER_REAL,580)
    try:
        contract_path=G/'retry/diagnostic482_contract.json';contract=read(contract_path)
        require(contract['status']=='PROPOSED_ONLY_NOT_REGISTERED_OR_EXECUTED' and contract['hard_caps']['worlds']==110 and contract['hard_caps']['charged_ticks']==520,'483_APPROVED_CONTRACT')
        require(read(root/'research-deadline-current.json')['deadline_utc']==contract['deadline_utc']=='2026-10-20T10:01:55Z','483_DEADLINE_PIN')
        require(sha(root/'stage441/authorization-correction-private.json')=='3b0dc9c16c5356e107e73dbd8a8f88e75a2434f9e24f046358783fbde8307078','483_EXTENSION_PROVENANCE')
        old=read(root/'stage481-plan-durable-private.json');unchanged(old);initial_space=space()
        # Formal integrated static gate is frozen here; any failure stops before
        # root construction or integration. Earlier development fixtures remain
        # explicitly charged and are not physical experiment retries.
        gate=static_gate();require(gate['passed'],'483_STATIC_FAILED:'+gate['failures'])
        rootproof,material=authenticate(root)
        proof_path=root/'stage483-root121-proof-private.json';material_path=root/'stage483-input-material-private.json'
        require(not proof_path.exists() and not material_path.exists(),'483_NEW_DURABLE_INPUTS')
        save_receipt(proof_path,rootproof);save_receipt(material_path,material)
        closure=source_closure([G/'retry'/n for n in NAMES]);semantic=dict(old['semantic_sources']);semantic.update({str(p):sha(p) for p in closure});growth=max(0,len(json.dumps(semantic,indent=2).encode())-len(json.dumps(old['semantic_sources'],indent=2).encode()))
        require(growth<=8192,'483_INLINE_SOURCE_GROWTH8KiB')
        sources=dict(old['sources']);sources.update({str(p):sha(p) for p in closure})
        input_paths=[contract_path,G/'retry/diagnostic482_result.md',G/'retry/diagnostic482_findings.json',root/'stage482-retention-final-private.json',root/'stage482-publication-private.json',root/'stage481-retention-manifest-private.json',root/'stage481-publication-private.json',root/'research-deadline-current.json',proof_path,material_path]
        sources.update({str(p):sha(p) for p in input_paths})
        bound=Quota.STATES_MAX*Quota.STATE_MAX+Quota.NONSTATE_MODEL_MAX;require(bound==156860416,'483_FORMAT_BOUND')
        # The inherited conservative inline-header allowance is not reduced by
        # observed state interning. New source growth is included three times.
        base=sum(max((p.stat().st_size for p in (root/'stage479').glob(pattern)),default=0) for pattern in ('world*-before-constructor-private.json','world*-before-first-step-private.json','*-runtime-link-private.json'))
        estimated_header=base+3*growth+16384;require(estimated_header<=829464,'483_HEADER_ALLOWANCE')
        p=dict(stage=483,authorization='EXPLICIT_USER_ONE_H6_RANKING_ONLY_110WORLD520CHARGED_NO_NATIVE',registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=contract['deadline_utc'],caps=CAPS,scope=dict(ticks=520,worlds=110),contract=contract,contract_sha256=sha(contract_path),root_proof_path=str(proof_path),root_proof_sha256=sha(proof_path),input_material_path=str(material_path),input_material_sha256=sha(material_path),sources=sources,semantic_sources=semantic,protected=old['protected'],original408_preserve=old['original408_preserve'],ledger_path=old['ledger_path'],ledger_sha256=old['ledger_sha256'],storage_free_stop_bytes=512*1024**2,source_manifest_growth_bytes=growth,estimated_header_bytes=estimated_header,header_hard_bytes=829464,model_raw_hard_bytes=201085448,format_bound_bytes=bound,allocator_bytes=16*1024**2,decision_bytes=16*1024**2,temp_bytes=32*1024**2,workspace_metadata_bytes=64*1024**2,storage_preflight_before=initial_space,storage_preflight_final=space(),runtime_environment=runtime_environment(),static=gate,root_auth_actions=121,root_auth_performed_once=True,actual=0,resets=0,HOLDOUT=0,SEALED=0,new_prefix_physics=0,new_archive=False,parallel_integrations=0,max_simultaneous_integrating=1,max_live_physical_worlds=2,live_object_description='One parent preserved while one shadow/repeat is restored. No simultaneous steps/constructors. Closed bodies/joints explicitly destroyed and retained model/stream references cleared after final proof dump.',no_followup=True)
        require(len(json.dumps(p,indent=2).encode())<=2*1024**2,'483_PLAN2MiB')
        require(material_path.stat().st_size+proof_path.stat().st_size+len(json.dumps(p).encode())<64*1024**2,'483_DURABLE_METADATA64MiB')
        unchanged(p)
        RAW.mkdir(mode=0o700);(root/'stage483').symlink_to(RAW,target_is_directory=True)
        save(RAW/'plan.json',p);(RAW/'plan.sha256').write_text(sha(RAW/'plan.json')+'\n');save(root/'stage483-plan-durable-private.json',p)
        save(RAW/'static-result.json',dict(stage=483,passed=True,tests=gate['tests'],new_worlds=0,new_ticks=0,plan_sha256=sha(RAW/'plan.json')))
        prep=dict(measured_CPU_s=time.process_time(),measured_wall_s=time.perf_counter()-START,development_conservative_charge=DEV_CHARGE,CPU_s=time.process_time()+DEV_CHARGE['CPU_s'],wall_s=time.perf_counter()-START+DEV_CHARGE['wall_s'],scope='Formal registration/static/fullsource/root121 authentication/storage/frozeninputs, plus separately identified conservative development charge. No model constructor/step.')
        require(prep['CPU_s']<480 and prep['wall_s']<600,'483_PREP_CAP');save(RAW/'preparation-cost.json',prep)
        print(json.dumps(dict(stage=483,phase='REGISTERED_STATIC_ROOT121_NO_PHYSICS',tests=gate['tests'],root_actions=121,plan_sha256=sha(RAW/'plan.json'),CPU_s=prep['CPU_s'],wall_s=prep['wall_s'],new_worlds=0,new_ticks=0,space=p['storage_preflight_final'],source_growth_bytes=growth)),flush=True)
    except BaseException as e:
        save(root/'stage483-preparation-stop-private.json',dict(stage=483,error=type(e).__name__+':'+str(e),traceback=traceback.format_exc(),CPU_s=time.process_time(),wall_s=time.perf_counter()-START,new_worlds=0,new_ticks=0,no_integration_allowed=True));raise
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)

def run(root):
    d=root/'stage483';p=read(d/'plan.json');oldsave=save
    require(not(d/'opening.json').exists() and read(d/'static-result.json')['passed'],'483_RUN_ONCE_AFTER_STATIC')
    require(sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()==read(d/'static-result.json')['plan_sha256'],'483_PLAN_BINDING')
    require(p['caps']==CAPS,'483_FROZEN_CAPS');unchanged(p);space()
    material=load_receipt(p['input_material_path']);prep=read(d/'preparation-cost.json');meter=Meter483(d,worker_start=START,preparation_CPU_s=prep['CPU_s'],preparation_wall_s=prep['wall_s'])
    meter.quota=Quota(d,201085448,16*1024**2).install();meter.qualification_passed=True
    save(d/'opening.json',dict(stage=483,pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(d/'plan.json'),source_qualification='Unchanged481 source/pending fixture bytes plus registered root121 fullauth and in-first-query source gate; no extra source worlds.'))
    status='STARTED';error=None;outcome=None;inventory=[]
    def timeout(*args):raise RuntimeError('483_WHOLE_CPU480_WALL600_DEADLINE')
    handlers={s:signal.signal(s,timeout) for s in (signal.SIGPROF,signal.SIGALRM)};meter.timers()
    try:
        try:
            with meter.model('483_one_H6_ranking_comparison'):outcome=execute(meter,material)
            status=outcome['status']
        except BaseException as e:
            status='TECHNICAL_STOP';error=type(e).__name__+': '+str(e);save(d/'stop-private.json',dict(error=error,traceback=traceback.format_exc(),no_retry=True))
        finally:
            meter.closeall();meter.persist()
        unchanged(p);require(not meter.live and not meter.streams and meter.closed_worlds==meter.b['confirmed_worlds'],'483_ALL_WORLDS_RELEASED')
        save(d/'result.json',dict(stage=483,status=status,error=error,outcome=outcome,budget=read(d/'budget.json'),new_native=0,new_resets=0,new_HOLDOUT_SEALED=0,no_followup=True))
        for f in sorted(d.iterdir()):
            if not f.is_file():continue
            data=f.read_bytes();digest=hashlib.sha256(data).hexdigest()
            if f.suffix=='.json':
                raw=json.loads(data,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)));read(f)
                if f.name.startswith('state-'):require(canonical(raw['full_state'])==raw['sha256'],'483_STATE_FULL_READBACK')
            again=f.read_bytes();require(len(data)==len(again) and hashlib.sha256(again).hexdigest()==digest,'483_FULL_READBACK:'+f.name)
            inventory.append(dict(path=str(f),bytes=len(data),sha256=digest,full_readbacks=2))
        require(sum(x['bytes'] for x in inventory)<=201085448+32*1024**2,'483_TOTAL_RAW_CAP')
        meter.checkpoint('CLOSED',status=status,error=error)
        result=read(d/'result.json');result['budget']=read(d/'budget.json');result['readback_file_count']=len(inventory);save(d/'result.json',result)
        for record in inventory:
            f=Path(record['path'])
            if f.name in ('result.json','progress-private.json','budget.json'):
                data=f.read_bytes();require(data==f.read_bytes(),'483_FINAL_CONTROL_READBACK');json.loads(data);read(f);record.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        oldsave(root/'stage483-retention-manifest-private.json',dict(stage=483,files=inventory,new_archive=False,workspace_new_raw_copies=0,tmp_loss='Hashes cannot restore lost raw',all_new_files_reopened_twice=True))
        cpu,wall=meter.wholetime();require(cpu<480 and wall<600,'483_FINAL_CAP')
        public_out=None
        if outcome is not None:
            public_out={k:v for k,v in outcome.items() if k!='parents'}
            public_out['parents']=[{k:v for k,v in rec.items() if k not in ('first','undispatched','history_proof','signature','post_signature')} for rec in outcome['parents']]
        public=dict(stage=483,status=status,error=error,outcome=public_out,model_ticks=meter.b['ticks'],charged_ticks=meter.charged_ticks,reserved_ticks=meter.b['reserved_ticks'],worlds=meter.b['worlds'],wrapper_slots=meter.wrapper_slots,allocator_calls=meter.allocator_calls,allocator_CPU_s=meter.allocator_CPU_s,allocator_wall_s=meter.allocator_wall_s,whole_accounted_CPU_s=cpu,whole_accounted_wall_s=wall,preparation=prep,peak_live_worlds=meter.peak_live,peak_integrating_constructor_or_step=meter.peak_integrating,closed_worlds=meter.closed_worlds,readback_files=len(inventory),raw_bytes=sum(x['bytes'] for x in inventory),plan_sha256=sha(d/'plan.json'),static_tests=p['static']['tests'],root121_authenticated_once=True,new_native_actual_reset_HOLDOUT_SEALED=0,research_remaining=26175,reserve=84000,reserve_used=0,best_native_s=13.640,no_followup=True)
        oldsave(G/'retry/diagnostic483_result.json',public);oldsave(root/'stage483-checkpoint-private.json',dict(stage=483,status=status,error=error,CPU_s=cpu,wall_s=wall,charged_ticks=meter.charged_ticks,worlds=meter.b['worlds'],actual=0))
        require(meter.wholetime()[0]<480 and meter.wholetime()[1]<600,'483_AFTER_PUBLIC_CAP')
        print(json.dumps(dict(stage=483,status=status,error=error,verdict=None if outcome is None else outcome['verdict'],ticks=meter.b['ticks'],charged=meter.charged_ticks,worlds=meter.b['worlds'],CPU_s=meter.wholetime()[0],wall_s=meter.wholetime()[1],new_native=0)),flush=True)
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        for s,h in handlers.items():signal.signal(s,h)

if __name__=='__main__':
    root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
