"""458 once-only integrated static/source/native transfer of frozen457 policy."""
import datetime,json,os,pickle,random,signal,sys,time,traceback
from pathlib import Path
import numpy as np
from retry.meter458 import Meter458 as TransferMeter458
from retry.native458 import actual458
from retry.compare457 import root_inputs,qualify_root457 as qualify_root458
from retry.qualify453 import qualify,qualify_pending
from retry.qualify_parent453 import qualify as qualify_parent
from retry.pilot420_backend import GoalLedger,H,ResourceStop
from retry.terminal410_model import from_actual_full
from retry.loss389_analyze import read,save,sha
G=Path(__file__).resolve().parents[1]
PLAN_CAPS=dict(ticks=212992,worlds=1792,CPU_s=6000,wall_s=9000,max_parallel=1)

def create_meter(d):return TransferMeter458(d)

def prepare(root):
    d=root/'stage458';assert not d.exists();d.mkdir(mode=0o700)
    old=read(root/'stage457/plan.json');native=read(root/'stage453/plan.json');v=read(root/'project-effective-budget-v473.json');deadline=read(root/'research-deadline-current.json')['deadline_utc']
    assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(27059,84000,0)
    assert deadline==v['authorization_end_utc']=='2026-10-20T10:01:55Z'
    assert read(root/'stage457/result.json')['status']=='FOUR_MODEL_PARENTS_COMPLETED_REPEAT_EXACT'
    files={Path(f) for f in old['sources']};files.update(G.glob('retry/*458*.py'));files.update([G/'retry/design458.md',G/'retry/saved458_diagnosis.json',root/'stage457/result.json',root/'stage457/publication-private.json',root/'stage456/result.json',root/'stage456/plan.json',root/'stage456/worker-private.log',root/'stage417/source-prefix-private.json'])
    # Prefix source frames were already observed/verified in453. They qualify
    # fixed replay only; no stored command beyond112 is supplied to selection.
    files.update(root/f'stage453/candidate_decision{n}-before-actual-dispatch-private.json' for n in range(1,91))
    semantic=dict(old['semantic_sources']);semantic.update({str(f):sha(f) for f in files if str(f).startswith(str(G)) and f.suffix=='.py'})
    p=dict(stage=458,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=deadline,case=native['case'],fixed_plan=old['fixed_plan'],pace_path=old['pace_path'],caps=PLAN_CAPS,model_caps=dict(planned_ticks=103026,planned_worlds=857,hard_ticks=212992,hard_worlds=1792,CPU_s=6000,wall_s=9000),actual_caps=dict(actions=440,arm_actions=220,resets=2,CPU_s=240,wall_s=480,exclusive_of_model=True),policy_parent_cap=100,prefix_actions=112,effective_native_scope_per_arm=212,source_preflight_caps=dict(ticks=1458,worlds=41),sources={str(f):sha(f) for f in sorted(files)},semantic_sources=semantic,protected=old['protected'],original408_preserve=old['original408_preserve'],contract_sha256=sha(G/'retry/design458.md'),authorization='Explicit458 integrated transfer once after static+fresh source gates; native440/reset2 e220, policy100suffix/e212. First unexpected error stops both; no retry.',research_before=27059,reserve=84000,reserve_used=0,new_seed_learning_HOLDOUT_SEALED_reserve_paid=0)
    for group in ['protected','original408_preserve']:
        for f,h in p[group].items():assert sha(f)==h,f
    root_inputs(root,p);save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n')
    save(d/'progress-private.json',dict(stage=458,phase='PLAN_FROZEN',at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),model_ticks=0,actual_actions=0,resets=0))
    print(json.dumps(dict(stage=458,plan_sha256=sha(d/'plan.json'),planned_ticks=103026,planned_worlds=857,actual_hard440_reset2=True)))

def run(root):
    d=root/'stage458';p=read(d/'plan.json');assert not(d/'opening.json').exists() and read(d/'static-result.json')['passed']
    assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()==read(d/'static-result.json')['plan_sha256']
    for group in ['sources','protected','original408_preserve']:
        for f,h in p[group].items():assert sha(f)==h,f
    state,memory,ledger,rng,blob,expected=root_inputs(root,p);py,npr=pickle.loads(blob);random.setstate(py);np.random.set_state(npr)
    fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(p['pace_path'])['frozen268']);meter=create_meter(d);actual=[];status='STARTED';error=None;stage='fresh_qualification'
    save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),static_sha256=sha(d/'static-result.json')))
    def timeout(*args):raise ResourceStop('458_exclusive_time_or_deadline')
    handlers={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]}
    try:
        meter.checkpoint('FRESH_SOURCE_STARTED',native_reset_allowed=False)
        with meter.model('458_fresh_source_current_pending'):
            fork=read(root/'stage423/actual_C0/fork-private.json');oldstate=from_actual_full(fork);oldmem=fork['controller']['before'];row=json.loads((root/'stage423/actual_C0/trace-private.jsonl').read_text().splitlines()[118]);oldledger=GoalLedger(row['progress_before'],row['goal_before'],H-(row['deadline_before']-118),round(oldstate['physical']['actual_time']*50))
            qualify(root,meter,fixed,pace,oldstate,oldmem,oldledger);qualify_pending(root,meter,fixed,pace);meter.qualification_passed=True;qualify_parent(root,meter,fixed,pace)
            if meter.b['ticks']>1242 or meter.b['worlds']!=35:raise ResourceStop('458_old_source_cap')
            qualify_root458(root,meter,fixed,pace,state,memory,ledger,expected)
            if meter.b['ticks']>1458 or meter.b['worlds']!=41:raise ResourceStop('458_combined_fresh_gate_cap')
        save(d/'preflight-private.json',dict(passed=True,ticks=meter.b['ticks'],worlds=meter.b['worlds'],actual_actions=0,resets=0))
        stage='native_pair';meter.checkpoint('ALL_PREFLIGHT_PASSED',native_reset_allowed=True);actual=actual458(root,meter,fixed,pace)
        status='NATIVE_FULL_PAIR_COMPLETED' if len(actual)==2 and all(x['completed'] for x in actual) else 'NATIVE_PAIR_CENSORED_STOP'
    except BaseException as e:
        status='STOP';error=type(e).__name__+': '+str(e);save(d/'stop-private.json',dict(stage=stage,error=error,traceback=traceback.format_exc(),no_retry=True))
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);meter.end_actual();cc,cw=time.process_time(),time.perf_counter()
        try:meter.closeall()
        except BaseException as e:
            save(d/'cleanup-stop-private.json',dict(error=type(e).__name__+': '+str(e),original_error=error));status='STOP'
            if error is None:error=type(e).__name__+': '+str(e)
        finally:
            dc,dw=time.process_time()-cc,time.perf_counter()-cw;meter.mc+=dc;meter.mw+=dw;meter.regions.append(dict(label='458_no_integration_cleanup',CPU_s=dc,wall_s=dw))
        for s,h in handlers.items():signal.signal(s,h)
        meter.persist()
    if not actual and(d/'actual-results.json').exists():actual=read(d/'actual-results.json')
    gain=None if status!='NATIVE_FULL_PAIR_COMPLETED' else(actual[0]['lap_ms']-actual[1]['lap_ms'])/1000
    out=dict(stage=458,status=status,error=error,last_stage=stage,actual=actual,official_lap_gain_s=gain,budget=read(d/'budget.json'),plan_sha256=sha(d/'plan.json'),target_s=11.99,new_seed_learning_HOLDOUT_SEALED_reserve_paid=0,official_server_pixel_generalization_qualified=False)
    save(d/'result.json',out);meter.checkpoint('CLOSED',status=status,error=error);print(json.dumps(dict(stage=458,status=status,error=error,gain=gain,actions=meter.nb['actions'],resets=meter.nb['resets'],ticks=meter.b['ticks'],worlds=meter.b['worlds'])),flush=True)

if __name__=='__main__':prepare(Path(sys.argv[2])) if sys.argv[1]=='prepare' else run(Path(sys.argv[2]))
