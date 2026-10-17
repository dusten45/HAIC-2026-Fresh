"""453 once-only integrated frozen-policy known-DEV native full-lap pair."""
import datetime,json,os,signal,sys,time,traceback
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.meter453 import Meter453
from retry.qualify_h1_453 import QualifyH1453
from retry.qualify453 import qualify,qualify_pending
from retry.qualify_parent453 import qualify as qualify_parent
from retry.native453 import actual453
from retry.pilot420_backend import GoalLedger,H,ResourceStop
from retry.terminal410_model import from_actual_full
G=Path(__file__).resolve().parents[1]


def prepare453(root):
    d=root/'stage453';assert not d.exists();d.mkdir(mode=0o700)
    old=read(root/'stage452/plan.json');v=read(root/'project-effective-budget-v472.json');proposal=read(G/'retry/next452_design.json');h1=read(root/'stage448/plan.json')
    assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(27436,84000,0)
    assert read(root/'stage452/result.json')['result']['outcome']=='NOMINAL_SAFE_RECOVERY_IN_NEW_SINGLE_DECISION'
    assert proposal['cost']['planned_model_ticks']==83826 and proposal['cost']['actual_wrapper_cap']==440
    deadline=read(root/'research-deadline-current.json')['deadline_utc'];assert deadline==v['authorization_end_utc']=='2026-10-20T10:01:55Z'
    files={Path(f):h for f,h in old['sources'].items()}
    for f in list(G.glob('retry/*453*.py'))+[G/'retry/next452_design.json',G/'retry/decision452_result.json',root/'project-effective-budget-v472.json',root/'stage452/publication-private.json',root/'stage452/result.json',root/'stage442/result.json',root/'stage442/parent-pending-qualification.json',root/'stage442/qualification.json',root/'stage442/pending-qualification.json',root/'stage448/actual_fullgas/trace-private.jsonl']:
        files[f]=sha(f)
    for recipe in ['nominal','fullgas']:
        for f in [Path(h1['original_inputs'][recipe]),Path(h1['archives'][recipe])]:files[f]=sha(f)
    semantic=dict(old['semantic_sources']);semantic.update({str(f):h for f,h in files.items() if str(f).startswith(str(G)) and f.suffix=='.py'})
    p=dict(stage=453,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=deadline,case=read(root/'stage442/plan.json')['case'],fixed_plan=old['fixed_plan'],pace_path=old['pace_path'],root_step=23,horizon=13,original_inputs=h1['original_inputs'],archives=h1['archives'],sources={str(f):h for f,h in files.items()},semantic_sources=semantic,protected=old['protected'],original408_preserve=old['original408_preserve'],model_caps=dict(planned_ticks=83826,planned_worlds=1625,hard_ticks=98304,hard_worlds=1792,CPU_s=3000,wall_s=4200,workers=1),actual_caps=dict(actions=440,arm_actions=220,resets=2,CPU_s=240,wall_s=480,exclusive_of_model=True),source_preflight_caps=dict(ticks=1458,worlds=41),model_arithmetic='396postroot decisions*2recipes*2copies*13*4+1458=83826ticks;396*4+41=1625worlds',native_arithmetic='2*220wrapper*4+2*51reset=1862rawticksmaximum',research_before=27436,research_after_worst=26996,reserve=84000,reserve_used=0,authorization='Explicit453 integrated fixed-policy actual pair once. Static/new routing/type/pending/authority fixtures and fresh source<=1458/41 before any native reset. Native440/reset2; no retry.',policy='22stored actual prefix actions each. Candidate only first pre23 fullgas then own nominal until wrapper containing originalRoot+270m. Thereafter conditionalB nominalH13 repeat2, registered ineligibility=>neutralH13 repeat2. Existing native pending guardian route and own native official finish. No planner ranking/no gain/profile/root/threshold/seed change.',qualification='H1 source216/6 includes nominal442 and fullgas448 factual13, then existing saved423/427/current restores/pending<=1242/35 with destination-only newstage copy. Previous evidence reused by hash/records, not fullH1 policy success. Source qualification only calibration, not selection.',native_binding='Native442/Authority439, current read-only adapter, observed history/pending442, suffix_step fact commit before forecast comparison and no nextdispatch after failure. Every postroot command fresh current native independent model safety/repeat. Native DONE only own successful charged native ticket/official tracker.',stop='First source/prefix/authority/fidelity/ledger/memory/RNG/repeat/selected-parent safety/progress/technical/resource/deadline error stopsboth. Static/preflight failure=>native0. No retry/repair after model opening, no scope/policy/threshold change. Expected unselected registeredphysical/progress rejection only insideB. Missing official finishwithin220=>censor and gainnull.',promotion='Lap contrast only both own native official finishes; target11.99s directly, no local gain sum. KnownDEV GT only, not official server/pixel/generalization. Preserve451censor and all earlier failure/cost evidence.',new_seed_learning_HOLDOUT_SEALED_reserve_paid=0)
    for f,h in files.items():assert sha(f)==h,f
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'progress-private.json',dict(stage=453,phase='PLAN_FROZEN',at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actual_actions=0,resets=0,model_ticks=0,model_worlds=0))
    print(json.dumps(dict(stage=453,plan_sha256=sha(d/'plan.json'),source1458_world41=True,actual440_reset2=True,model_planned83826=True)))


def run453(root):
    d=root/'stage453';p=read(d/'plan.json');assert not(d/'opening.json').exists() and read(d/'static-result.json')['passed']
    assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()==read(d/'static-result.json')['plan_sha256']
    for group in [p['sources'],p['protected'],p['original408_preserve']]:
        for f,h in group.items():assert sha(f)==h,f
    import subprocess
    assert subprocess.check_output(['git','rev-parse','main'],text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31'
    save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),static_sha256=sha(d/'static-result.json')))
    meter=Meter453(d);ex=None;actual=[];status='STARTED';error=None;stage='source_H1'
    def timeout(*args):raise ResourceStop('453_exclusive_time_cap')
    handlers={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]}
    try:
        meter.checkpoint('SOURCE_PREFLIGHT_STARTED',native_reset_allowed=False)
        with meter.model('453_H1_factual_source'):
            ex=QualifyH1453(root,d,meter);ex.qualify_h1_453()
        meter.checkpoint('H1_SOURCE216_PASSED',native_reset_allowed=False)
        stage='source_full_pending'
        with meter.model('453_full_native_pending_source'):
            fixed=ex.fixed;pace=ex.pace;fork=read(root/'stage423/actual_C0/fork-private.json');state=from_actual_full(fork);memory=fork['controller']['before'];row=json.loads((root/'stage423/actual_C0/trace-private.jsonl').read_text().splitlines()[118]);ledger=GoalLedger(row['progress_before'],row['goal_before'],H-(row['deadline_before']-118),round(state['physical']['actual_time']*50))
            qualify(root,meter,fixed,pace,state,memory,ledger);qualify_pending(root,meter,fixed,pace)
            if(meter.b['ticks'],meter.b['worlds'])!=(216+1134,6+32):raise ResourceStop('453_qualification_base_cost')
            meter.qualification_passed=True;qualify_parent(root,meter,fixed,pace)
            if meter.b['ticks']>1458 or meter.b['worlds']!=41:raise ResourceStop('453_preflight1458_world41')
        stage='native_pair';meter.checkpoint('ALL_PREFLIGHT_PASSED',native_reset_allowed=True)
        print('453 all static/current/factual/pending gates passed; opening native pair once.',flush=True)
        actual=actual453(root,meter,fixed,pace);status='NATIVE_FULL_PAIR_COMPLETED' if len(actual)==2 and all(a['completed'] for a in actual) else 'NATIVE_PAIR_CENSORED_STOP'
    except BaseException as e:
        status='STOP';error=type(e).__name__+': '+str(e);save(d/'stop-private.json',dict(stage=stage,error=error,traceback=traceback.format_exc()))
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);meter.end_actual();cc,cw=time.process_time(),time.perf_counter()
        try:
            if ex:
                for c in ex.children:
                    if not c.closed:ex.close(c)
            meter.closeall()
        except BaseException as e:
            save(d/'cleanup-stop-private.json',dict(error=type(e).__name__+': '+str(e),original_error=error))
            if error is None:status='STOP';error=type(e).__name__+': '+str(e)
        finally:
            dc,dw=time.process_time()-cc,time.perf_counter()-cw;meter.mc+=dc;meter.mw+=dw;meter.regions.append(dict(label='453_no_integration_cleanup',CPU_s=dc,wall_s=dw))
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        for s,h in handlers.items():signal.signal(s,h)
        meter.persist()
    if not actual and(d/'actual-results.json').exists():actual=read(d/'actual-results.json')
    gain=None
    if status=='NATIVE_FULL_PAIR_COMPLETED':gain=(actual[0]['lap_ms']-actual[1]['lap_ms'])/1000
    out=dict(stage=453,status=status,error=error,actual=actual,official_lap_gain_s=gain,budget=read(d/'budget.json'),plan_sha256=sha(d/'plan.json'),pixel_generalization_official_server_qualified=False,new_seed_learning_HOLDOUT_SEALED_reserve_paid=0)
    save(d/'result.json',out);meter.checkpoint('CLOSED',status=status,error=error)
    print(json.dumps(dict(stage=453,status=status,error=error,actual_actions=meter.nb['actions'],resets=meter.nb['resets'],model_ticks=meter.b['ticks'],worlds=meter.b['worlds'],lap_gain_s=gain)))

if __name__=='__main__':
    root=Path(sys.argv[2]);prepare453(root) if sys.argv[1]=='prepare' else run453(root)
