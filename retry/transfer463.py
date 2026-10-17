"""One 463 native pair after one integrated static and fresh qualification."""
import time
WORKER_START=time.perf_counter()
import datetime,json,os,pickle,random,signal,sys,traceback,shutil
from pathlib import Path
import numpy as np
from retry.meter463 import Meter463
from retry.native463 import actual463
from retry.compare462 import root_inputs
from retry.compare460 import qualify_root460
from retry.qualify453 import qualify,qualify_pending
from retry.qualify_parent453 import qualify as qualify_parent
from retry.pilot420_backend import GoalLedger,H,ResourceStop
from retry.terminal410_model import from_actual_full
from retry.ledger439 import require
from retry.loss389_analyze import read,save,sha
from retry.budget463 import calculate
G=Path(__file__).resolve().parents[1]

def contract():return read(G/'retry/design463.json')
def create_meter(d):return Meter463(d,worker_start=WORKER_START)
def qualify_root463(root,meter,fixed,pace,state,memory,ledger,expected):
    return qualify_root460(root,meter,fixed,pace,state,memory,ledger,expected[:13],'463SecantRoot')

def check_storage(c,b):
    free={volume:shutil.disk_usage(volume).free for volume in ['/tmp','/workspace']}
    require(free['/tmp']>=b['model_storage_bytes'],'463_MODEL_STORAGE_PREFLIGHT')
    require(free['/workspace']>=b['native_storage_bytes'],'463_NATIVE_STORAGE_PREFLIGHT')
    return free

def prepare(root):
    d=root/'stage463';store=Path('/tmp/haic-retry-stage463-private');native_dir=root/'stage463-native'
    require(not d.exists() and not d.is_symlink() and not store.exists() and not native_dir.exists() and not(root/'project-effective-budget-v475.json').exists(),'463_ONCE_ONLY')
    c=contract();b=calculate(c);free=check_storage(c,b);old=read(root/'stage453/plan.json');vpath=root/'project-effective-budget-v474.json';v=read(vpath)
    require((v['research_remaining'],v['actual_cumulative_wrapper_actions'],v['final_reserved_actions'],v['final_reserve_used'])==(26695,1321369,84000,0),'463_LEDGER')
    require(read(root/'research-deadline-current.json')['deadline_utc']==c['deadline_utc']=='2026-10-20T10:01:55Z','463_DEADLINE')
    root_inputs(root)
    files=set(G.glob('retry/*463*.py'));files.update([G/'retry/design463.md',G/'retry/design463.json',G/'retry/compare462.py',G/'retry/compare460.py',vpath,root/'research-deadline-current.json',root/'stage417/source-prefix-private.json',root/'stage453/plan.json',root/'stage462/result.json'])
    files.update(Path(f) for f in read(root/'stage462/plan.json')['sources'] if Path(f).suffix=='.py')
    files.update(Path(f) for f in old['sources'] if Path(f).suffix=='.py' and 'analyze453' not in str(f))
    for stage in [423,425,427,433,435]:files.update(f for f in (root/f'stage{stage}').rglob('*') if f.is_file())
    files.update(f for f in (root/'stage458/actual_P').glob('*') if f.is_file())
    files.update(root/('stage458/'+name) for name in ['P_decision14-before-actual-dispatch-private.json','P_decision14_query-before-integration-private.json'])
    files.update(root/f'stage453/candidate_decision{n}-before-actual-dispatch-private.json' for n in range(1,91))
    files.update(root/f'stage458/P_decision{n}-before-actual-dispatch-private.json' for n in range(1,14))
    files.update([Path(old['fixed_plan']),Path(old['pace_path'])])
    semantic=dict(old['semantic_sources']);semantic.update({str(f):sha(f) for f in files if str(f).startswith(str(G)) and f.suffix=='.py'})
    p=dict(stage=463,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),execution=c,deadline_utc=c['deadline_utc'],case=old['case'],fixed_plan=old['fixed_plan'],pace_path=old['pace_path'],caps=c['hard'],model_caps=dict(planned_ticks=b['ticks'],planned_worlds=b['worlds'],hard_ticks=c['hard']['ticks'],hard_worlds=c['hard']['worlds'],CPU_s=1800,wall_s=2400),actual_caps=c['actual'],planned_ticks=b['ticks'],planned_worlds=b['worlds'],budget_fixture=b,prefix_actions=125,policy_parent_cap=70,effective_native_scope_per_arm=195,source_preflight_caps=dict(ticks=1458,worlds=41),native_directory=str(native_dir),storage_start_free_bytes=free,storage_free_stop_bytes=c['storage']['final_dump_reserve_bytes'],budget_before_path=str(vpath),budget_before_sha256=sha(vpath),ledger_path=str(root/'project-effective-budget-v475.json'),sources={str(f):sha(f) for f in sorted(files)},semantic_sources=semantic,protected=old['protected'],original408_preserve=old['original408_preserve'],contract_sha256=sha(G/'retry/design463.md'),contract_json_sha256=sha(G/'retry/design463.json'),authorization='EXPLICIT463_ONCE_PREFIX125_SUFFIX70_FIRST_NOMINAL_OR_SECANT_FULLGAS_THEN_SAME_GUARDIAN_OWN_NATIVE_FINISH',research_before=26695,reserve=84000,reserve_used=0,new_seed_learning_HOLDOUT_SEALED_reserve_paid=0)
    for group in ['protected','original408_preserve']:
        for f,h in p[group].items():require(sha(f)==h,'463_PROTECTED:'+f)
    store.mkdir(mode=0o700);native_dir.mkdir(mode=0o700);d.symlink_to(store,target_is_directory=True)
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(root/'stage463-plan-durable-private.json',p)
    save(d/'progress-private.json',dict(stage=463,phase='PLAN_FROZEN',at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),model_ticks=0,actual_actions=0,resets=0))
    print(json.dumps(dict(stage=463,budget=b,free=free,plan_sha256=sha(d/'plan.json'))))

def run(root):
    d=root/'stage463';p=read(d/'plan.json');require(not(d/'opening.json').exists() and read(d/'static-result.json')['passed'],'463_ONCE_STATIC')
    require(sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()==read(d/'static-result.json')['plan_sha256'],'463_STATIC_BINDING')
    require(p['execution']==contract() and p['caps']==p['execution']['hard'] and calculate(p['execution'])==p['budget_fixture'],'463_SINGLE_CONTRACT')
    for group in ['sources','protected','original408_preserve']:
        for f,h in p[group].items():require(sha(f)==h,'463_SOURCE_CHANGED:'+f)
    check_storage(p['execution'],p['budget_fixture']);require(not Path(p['ledger_path']).exists(),'463_NO_PREVIOUS_CHARGES')
    state,memory,ledger,rng,blob,expected=root_inputs(root);py,npr=pickle.loads(blob);random.setstate(py);np.random.set_state(npr)
    fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(p['pace_path'])['frozen268']);meter=create_meter(d);actual=[];status='STARTED';error=None;stage='fresh_qualification'
    save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(d/'plan.json'),static_sha256=sha(d/'static-result.json')))
    def timeout(*args):raise ResourceStop('463_wholeworker_time_or_deadline')
    handlers={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};meter.timers()
    try:
        meter.checkpoint('FRESH_SOURCE_STARTED',native_reset_allowed=False)
        with meter.model('463_fresh_source_current_pending'):
            fork=read(root/'stage423/actual_C0/fork-private.json');oldstate=from_actual_full(fork);oldmem=fork['controller']['before'];row=json.loads((root/'stage423/actual_C0/trace-private.jsonl').read_text().splitlines()[118]);oldledger=GoalLedger(row['progress_before'],row['goal_before'],H-(row['deadline_before']-118),round(oldstate['physical']['actual_time']*50))
            qualify(root,meter,fixed,pace,oldstate,oldmem,oldledger);qualify_pending(root,meter,fixed,pace);meter.qualification_passed=True;qualify_parent(root,meter,fixed,pace)
            require(meter.b['ticks']<=1242 and meter.b['worlds']==35,'463_SOURCE_GATE_CAP')
            qualify_root463(root,meter,fixed,pace,state,memory,ledger,expected)
            require(meter.b['ticks']<=1458 and meter.b['worlds']==41,'463_COMBINED_GATE_CAP')
        save(d/'preflight-private.json',dict(passed=True,ticks=meter.b['ticks'],worlds=meter.b['worlds'],actual_actions=0,resets=0))
        stage='native_pair';meter.checkpoint('ALL_PREFLIGHT_PASSED',native_reset_allowed=True);actual=actual463(root,meter,fixed,pace)
        status='NATIVE_FULL_PAIR_COMPLETED' if len(actual)==2 and all(x['completed'] for x in actual) else 'NATIVE_PAIR_CENSORED_STOP'
    except BaseException as e:
        status='STOP';error=type(e).__name__+': '+str(e);save(d/'stop-private.json',dict(stage=stage,error=error,traceback=traceback.format_exc(),no_retry=True))
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        # Disable timers for observed-only cleanup; it performs no new integration.
        meter.timers=lambda:None;meter.end_actual();cc,cw=time.process_time(),time.perf_counter()
        try:meter.closeall()
        except BaseException as e:
            save(d/'cleanup-stop-private.json',dict(error=type(e).__name__+': '+str(e),original_error=error));status='STOP'
            if error is None:error=type(e).__name__+': '+str(e)
        finally:
            dc,dw=time.process_time()-cc,time.perf_counter()-cw;meter.mc+=dc;meter.mw+=dw;meter.regions.append(dict(label='463_no_integration_cleanup',CPU_s=dc,wall_s=dw))
        for s,h in handlers.items():signal.signal(s,h)
        meter.persist()
    if not actual and(d/'actual-results.json').exists():actual=read(d/'actual-results.json')
    gain=None if status!='NATIVE_FULL_PAIR_COMPLETED' else(actual[0]['lap_ms']-actual[1]['lap_ms'])/1000
    out=dict(stage=463,status=status,error=error,last_stage=stage,actual=actual,official_lap_gain_s=gain,budget=read(d/'budget.json'),plan_sha256=sha(d/'plan.json'),target_s=11.99,new_seed_learning_HOLDOUT_SEALED_reserve_paid=0,official_server_pixel_generalization_qualified=False,model462_tail_added=False)
    save(d/'result.json',out);meter.checkpoint('CLOSED',status=status,error=error);print(json.dumps(dict(stage=463,status=status,error=error,gain=gain,actions=meter.nb['actions'],resets=meter.nb['resets'],ticks=meter.b['ticks'],worlds=meter.b['worlds'])),flush=True)

if __name__=='__main__':prepare(Path(sys.argv[2])) if sys.argv[1]=='prepare' else run(Path(sys.argv[2]))
