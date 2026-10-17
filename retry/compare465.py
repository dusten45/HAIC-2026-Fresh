"""One authorized464 small falsification; model only, no native entrypoint."""
import time
WORKER_START=time.perf_counter()
import copy,datetime,json,os,pickle,random,signal,sys,traceback,shutil
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.meter465 import Meter465
from retry.law465 import root_h13
from retry.compare462 import root_inputs as prior_root_inputs
from retry.qualify453 import qualify,qualify_pending
from retry.qualify_parent453 import qualify as qualify_parent
from retry.pilot420_backend import GoalLedger,H,ResourceStop
from retry.terminal410_model import from_actual_full
from retry.receipt421_io import load_receipt
from retry.ledger439 import require
from retry.loss389_analyze import read,save,sha
from retry.design464_math import calculate
G=Path(__file__).resolve().parents[1]

def contract():return read(G/'retry/design464_next.json')
def create_meter(d):return Meter465(d,worker_start=WORKER_START)

def root_inputs(root):
    state,memory,ledger,rng,blob,_=prior_root_inputs(root)
    folder=root/'stage463-native/actual_SecantOnce'
    native=load_receipt(folder/'SecantOnce_step126-before-native-private.json')
    rows=[json.loads(s) for s in (folder/'trace-private.jsonl').read_text().splitlines()];expected=rows[125:138]
    require(len(expected)==13 and state==from_actual_full(native['full_pre_before_nominal']) and memory==expected[0]['memory_before'] and asdict(ledger)==native['actual_ledger_before'],'465_ROOT463_EXACT')
    require(expected[0]['command'][1:]==[1.,0.] and all(r['command']==r['nominal'] for r in expected[1:]),'465_PULSEONCE_FACTUAL_CONTROL')
    return state,memory,ledger,rng,blob,expected

def storage_forecast(c,semantic,oldsemantic,plan_bytes):
    base=calculate(c);s=c['storage'];growth=max(0,len(json.dumps(semantic,indent=2).encode())-len(json.dumps(oldsemantic,indent=2).encode()))
    world_fixed=s['observed_fixed_bytes_per_world']+3*growth+16384
    # Explicitly include full new private plan and 16MiB raw metadata allowance.
    payload=c['selected_contract']['hard']['ticks']*s['observed_max_model_bytes_per_tick']*s['empirical_margin']+base['worlds']*world_fixed+plan_bytes+16*1024**2
    archive=payload*s['archive_payload_margin']+s['archive_metadata_allowance_bytes']
    workspace=archive+s['reserve_bytes']+plan_bytes
    return dict(observed_bytes_per_tick=s['observed_max_model_bytes_per_tick'],old_fixed_bytes_per_world=s['observed_fixed_bytes_per_world'],source_manifest_growth_bytes=growth,new_fixed_bytes_per_world_allowance=world_fixed,full_private_plan_bytes_allowance=plan_bytes,raw_metadata_allowance_bytes=16*1024**2,model_payload_bytes=payload,archive_forecast_bytes=archive,model_required_bytes=payload+s['reserve_bytes'],workspace_required_bytes=workspace,scope_ticks=base['ticks'],scope_worlds=base['worlds'],estimates_not_guaranteed=True)

def check_storage(p):
    free={volume:shutil.disk_usage(volume).free for volume in ['/tmp','/workspace']};s=p['storage_forecast']
    require(free['/tmp']>=s['model_required_bytes'],'465_MODEL_STORAGE_PREFLIGHT')
    require(free['/workspace']>=s['workspace_required_bytes'],'465_RAW_RETENTION_STORAGE_PREFLIGHT')
    return free

def prepare(root):
    d=root/'stage465';store=Path('/tmp/haic-retry-stage465-private')
    require(not d.exists() and not d.is_symlink() and not store.exists(),'465_ONCE')
    c=contract();cost=calculate(c);require((cost['ticks'],cost['worlds'])==(1458,41),'465_FROZEN_COST')
    old=read(root/'stage463/plan.json');ledger_path=root/'project-effective-budget-v475.json';v=read(ledger_path)
    require(v['stage463_status']=='CLOSED' and (v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(26346,84000,0),'465_LEDGER_UNCHANGED')
    require(read(root/'research-deadline-current.json')['deadline_utc']==c['deadline_utc']=='2026-10-20T10:01:55Z','465_DEADLINE')
    root_inputs(root)
    files={Path(f) for f in old['sources']};files.update(G/'retry'/name for name in ['compare465.py','law465.py','meter465.py','static465.py','test_compare465.py']);files.update([G/'retry/design464_next.md',G/'retry/design464_next.json',G/'retry/design464_math.py',G/'retry/static464.py',G/'retry/structural464_result.json',G/'retry/compare462.py',ledger_path,root/'stage463-plan-durable-private.json'])
    files.update(f for f in (root/'stage463-native/actual_SecantOnce').glob('*') if f.is_file())
    semantic=dict(old['semantic_sources']);semantic.update({str(f):sha(f) for f in files if str(f).startswith(str(G)) and f.suffix=='.py'})
    p=dict(stage=465,execution=c,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=c['deadline_utc'],caps=c['selected_contract']['hard'],scope=dict(ticks=1458,worlds=41),budget_fixture=cost,fixed_plan=old['fixed_plan'],pace_path=old['pace_path'],sources={str(f):sha(f) for f in sorted(files)},semantic_sources=semantic,protected=old['protected'],original408_preserve=old['original408_preserve'],contract_sha256=sha(G/'retry/design464_next.md'),contract_json_sha256=sha(G/'retry/design464_next.json'),storage_free_stop_bytes=512*1024**2,ledger_path=str(ledger_path),ledger_sha256=sha(ledger_path),authorization='EXPLICIT465_ONE_464_PULSEONCE_S13_H13_PAIR_REPEAT2_HELDFIRST1_EACH_SCOPE1458_41_ACTUAL_RESET0_NOFOLLOWUP',new_seed_learning_HOLDOUT_SEALED_reserve_paid=0)
    planbytes=len(json.dumps(p,indent=2).encode())+65536;p['storage_forecast']=storage_forecast(c,semantic,old['semantic_sources'],planbytes);p['storage_start_free_bytes']=check_storage(p)
    require(len(json.dumps(p,indent=2).encode())<=planbytes,'465_PLAN_BYTES_ALLOWANCE')
    for group in ['protected','original408_preserve']:
        for f,h in p[group].items():require(sha(f)==h,'465_PROTECTED:'+f)
    store.mkdir(mode=0o700);d.symlink_to(store,target_is_directory=True);save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(root/'stage465-plan-durable-private.json',p)
    save(d/'progress-private.json',dict(stage=465,phase='PLAN_FROZEN',at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),model_ticks=0,model_worlds=0,actual_actions=0,resets=0))
    print(json.dumps(dict(stage=465,plan_sha256=sha(d/'plan.json'),cost=cost,storage_forecast=p['storage_forecast'],free=p['storage_start_free_bytes'])))

def run(root):
    d=root/'stage465';p=read(d/'plan.json');require(not(d/'opening.json').exists() and read(d/'static-result.json')['passed'],'465_ONCE_STATIC')
    require(sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()==read(d/'static-result.json')['plan_sha256'],'465_PLAN_STATIC_BINDING')
    require(p['execution']==contract() and p['caps']==contract()['selected_contract']['hard'] and p['budget_fixture']==calculate(contract()) and p['scope']==dict(ticks=1458,worlds=41),'465_SINGLE_CONTRACT_SCOPE')
    for group in ['sources','protected','original408_preserve']:
        for f,h in p[group].items():require(sha(f)==h,'465_SOURCE_CHANGED:'+f)
    check_storage(p);state,memory,ledger,rng,blob,expected=root_inputs(root);py,npr=pickle.loads(blob);random.setstate(py);np.random.set_state(npr)
    fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(p['pace_path'])['frozen268']);meter=create_meter(d);cohorts=[];cohort_result=None;status='STARTED';error=None;stage='fresh_source'
    save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(d/'plan.json'),static_sha256=sha(d/'static-result.json')))
    def timeout(*args):raise ResourceStop('465_whole_CPU180_wall300_or_deadline')
    handlers={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};meter.timers()
    try:
        meter.checkpoint('FRESH_SOURCE_STARTED')
        with meter.model('465_source_and_single_falsification'):
            fork=read(root/'stage423/actual_C0/fork-private.json');oldstate=from_actual_full(fork);oldmem=fork['controller']['before'];row=json.loads((root/'stage423/actual_C0/trace-private.jsonl').read_text().splitlines()[118]);oldledger=GoalLedger(row['progress_before'],row['goal_before'],H-(row['deadline_before']-118),round(oldstate['physical']['actual_time']*50))
            qualify(root,meter,fixed,pace,oldstate,oldmem,oldledger);qualify_pending(root,meter,fixed,pace);meter.qualification_passed=True;qualify_parent(root,meter,fixed,pace)
            require(meter.b['ticks']<=1242 and meter.b['worlds']==35,'465_OLD_SOURCE_SCOPE')
            save(d/'preflight-private.json',dict(passed=True,ticks=meter.b['ticks'],worlds=meter.b['worlds'],actual_actions=0,resets=0));meter.checkpoint('OLD_SOURCE_PASSED')
            stage='PulseOnce_vs_S13';cohort_result=root_h13(root,meter,fixed,pace,state,memory,ledger,expected);cohorts=cohort_result['cohorts']
            require(meter.b['ticks']<=1458 and meter.b['worlds']<=41,'465_REGISTERED_SCOPE')
            status='H13_COMPARISON_COMPLETE' if cohort_result['passed'] else 'H13_NEGATIVE_OR_SCOPE_STOP'
    except BaseException as exc:
        status='STOP';error=type(exc).__name__+': '+str(exc);save(d/'stop-private.json',dict(stage=stage,error=error,traceback=traceback.format_exc(),no_retry=True))
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);meter.timers=lambda:None;cc,cw=time.process_time(),time.perf_counter()
        try:meter.closeall()
        except BaseException as exc:
            status='STOP';error=error or type(exc).__name__+': '+str(exc);save(d/'cleanup-stop-private.json',dict(error=str(exc)))
        meter.mc+=time.process_time()-cc;meter.mw+=time.perf_counter()-cw
        for sig,handler in handlers.items():signal.signal(sig,handler)
        meter.persist()
    if not cohorts and(d/'cohortresults.json').exists():cohorts=read(d/'cohortresults.json')
    require(sha(p['ledger_path'])==p['ledger_sha256'],'465_GLOBAL_LEDGER_CHANGED')
    result=dict(stage=465,status=status,error=error,last_stage=stage,cohorts=cohorts,cohort_result=cohort_result,budget=read(d/'budget.json'),plan_sha256=sha(d/'plan.json'),new_actual_actions=0,new_resets=0,new_seed_learning_HOLDOUT_SEALED_reserve_paid=0,no_followup=True)
    save(d/'result.json',result);meter.checkpoint('CLOSED',status=status,error=error);print(json.dumps(dict(stage=465,status=status,error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds'],actual=0,resets=0)),flush=True)

if __name__=='__main__':prepare(Path(sys.argv[2])) if sys.argv[1]=='prepare' else run(Path(sys.argv[2]))
