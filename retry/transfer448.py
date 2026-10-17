"""Freeze then execute exactly one explicitly authorized known-DEV transfer pair."""
import datetime,json,os,signal,sys,time,traceback
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.meter448 import Meter448
from retry.qualify448 import Qualify448
from retry.native448 import actual448
from retry.pilot420_backend import ResourceStop
G=Path(__file__).resolve().parents[1]


def prepare(root):
    d=root/'stage448';assert not d.exists();d.mkdir(mode=0o700)
    old=read(root/'stage447/plan.json');v=read(root/'project-effective-budget-v467.json');proposal=read(G/'retry/next447_design.json')
    assert read(root/'stage447/result.json')['status']=='SAME_LIVE_STUDY_COMPLETED'
    assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(27516,84000,0)
    assert proposal['model_planned_upper_ticks']==5624 and proposal['actual_wrapper_cap']==96
    deadline=read(root/'research-deadline-current.json')['deadline_utc'];assert deadline==v['authorization_end_utc']=='2026-10-20T10:01:55Z'
    files={Path(f):h for f,h in old['sources'].items()}
    for f in list(G.glob('retry/*448*.py'))+[G/'retry/next447_design.json',G/'retry/continuation447_result.json',root/'project-effective-budget-v467.json',root/'research-deadline-current.json',root/'stage447/result.json',root/'stage447/publication-private.json',root/'stage442/actual_C0/initial-private.json',root/'stage442/actual_C0/trace-private.jsonl',root/'stage442/actual_C0/C0_step23-before-native-private.json',root/'stage417/source-prefix-private.json']:
        files[f]=sha(f)
    # Resolve all reused native/model code into the same immutable manifest.
    for f in G.glob('retry/*442*.py'):files[f]=sha(f)
    for f in [G/'retry/authority439.py',G/'retry/ledger439.py',G/'retry/query445.py',G/'retry/fixture438.py',G/'retry/actual437_boundary.py',G/'retry/paired417_common.py',G/'env_wrapper.py',G/'damage.py']:
        files[f]=sha(f)
    for f in (G/'core').rglob('*.py'):files[f]=sha(f)
    semantic=dict(old['semantic_sources']);semantic.update({str(f):h for f,h in files.items() if str(f).startswith(str(G)) and f.suffix=='.py'})
    p=dict(stage=448,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=deadline,authorization='Explicit delegated448 native known DEV +60m comparison once; fixed two arms,22prefix each,26postroot cap, native96/reset2. No retries, no pulse/root/boundary/tolerance adjustment.',case=read(root/'stage442/plan.json')['case'],fixed_plan=old['fixed_plan'],root_step=23,horizon=13,original_inputs=old['original_inputs'],archives=old['archives'],sources={str(f):h for f,h in files.items()},semantic_sources=semantic,protected=old['protected'],original408_preserve=old['original408_preserve'],model_caps=dict(planned_ticks=5624,hard_ticks=6144,worlds=128,CPU_s=180,wall_s=300,max_parallel_workers=1),actual_caps=dict(actions=96,resets=2,arm_actions=48,prefix_each=22,postroot_each=26,CPU_s=90,wall_s=180,exclusive_of_model=True),worst_native_raw_ticks_including_reset=486,model_arithmetic='216source +52decisions*2copies*13actions*4ticks=5624;6sourceworlds+104currentworlds=110<=128',source_g1='Before native reset rerun both historicalH13 branches independently2 and held first perbranch; nominal factual442/439 gate and copied-current first gate.216ticks6worlds. Counterfactual remains model-only until own native observation.',native_prefix='22 fixed stored native actions each: own charged native ticket, native facts first, exact442pre/post/memory/nominal/command/raw and frozen417source physical fidelity. No new prefix policy choices.',current_guard='Postroot each action: copy current actual physics/memory/ledger/RNG, independently2 model copies; fixed first pre23 gas for candidate only, otherwise own nominal. Same H13 guard or stop earlier at fixed original-root+60m; safety/progress,exact repeat,first nominal memory; native parent unchanged. No finish ranking, no native DONE capability, no fallback.',native_binding='Existing Native442/Authority439 and suffix_step: charge before own step; complete native facts and ledger commit before model comparison, fresh current first source439 and exact goal-side/clock/age/DONE plus geometry-derived intervals. Existing fidelity thresholds unchanged. Prefix/root must exactly reproduce original before candidate.',qualification='Source216/6 before any reset; static constructors blocked and production native/query negative fixtures must pass. Frozen source hashes,protected files,main dfb7a2de2178825ca5c5ce20bab01ba67052ba31,ledger/budget/explicit448permission verified before execution.',stop='First source/fidelity/ledger/memory/RNG/safety/progress/technical/repeat/resource/deadline error stops BOTH arms, retains native facts/cost/failure, no retry/retune.26postroot absent exit=>censor; no gain if either arm censored/stopped. Candidate starts only after baseline native success and own prefix/root exact. Both valid crossings required for local contrast; overlap/small/nonpositive gain remains reported.',research_before=27516,research_after_worst=27420,reserve=84000,reserve_used=0,new_seed_learning_HOLDOUT_SEALED_paid=0,wholelap_pixel_promotion=False)
    for f,h in files.items():assert sha(f)==h,f
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n')
    save(d/'authorization-private.json',dict(source_thread='01a1200d-ecd4-715b-a81e-9f19ca0d10ef',explicit_stage=448,confirmed_native96_reset2_model5624_hard6144_world128=True,deadline_utc=deadline,received_instruction='448 known DEV native +60m transfer compare; first error stop both, no retry; ordinary commit/push allowed.'))
    save(d/'progress-private.json',dict(stage=448,phase='PLAN_FROZEN',at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actual_actions=0,model_ticks=0,worlds=0))
    print(json.dumps(dict(stage=448,plan_sha256=sha(d/'plan.json'),model_planned=5624,model_hard=6144,native_cap=96,resets=2)))


def run(root):
    d=root/'stage448';p=read(d/'plan.json');assert not(d/'opening.json').exists()
    assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()==read(d/'static-result.json')['plan_sha256']
    assert read(d/'static-result.json')['passed'] and read(d/'authorization-private.json')['explicit_stage']==448
    for group in [p['sources'],p['protected'],p['original408_preserve']]:
        for f,h in group.items():assert sha(f)==h,f
    import subprocess
    assert subprocess.check_output(['git','rev-parse','main'],text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31'
    save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),static_sha256=sha(d/'static-result.json'),native_cap=96,model_hard_cap=6144))
    meter=Meter448(d);ex=None;actual=[];status='STARTED';error=None;stage='source_qualification'
    def timeout(*args):raise ResourceStop('448_exclusive_time_cap')
    handlers={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]}
    try:
        meter.checkpoint('SOURCE_G1_STARTED',native_dispatch_allowed=False)
        with meter.model('448_source_g1_before_any_native'):
            ex=Qualify448(root,d,meter);ex.qualify448()
        meter.checkpoint('SOURCE_G1_PASSED',native_dispatch_allowed=True)
        print('448 source216ticks/6worlds passed; opening one native pair.',flush=True)
        stage='native_pair';actual=actual448(root,meter,ex.fixed,ex.pace)
        status='NATIVE_EXIT60_PAIR_COMPLETED' if len(actual)==2 and all(x['status']=='NATIVE_EXIT60_VERIFIED' for x in actual) else 'NATIVE_PAIR_CENSORED_STOP'
    except BaseException as e:
        status='TECHNICAL_STOP';error=type(e).__name__+': '+str(e)
        save(d/'stop-private.json',dict(stage=stage,error=error,traceback=traceback.format_exc()))
    finally:
        meter.end_actual()
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        # Cleanup has no integration or dispatch. It must retain a first cap/error
        # even when the normal model-region entry gate is already closed.
        cc,cw=time.process_time(),time.perf_counter()
        try:
            if ex:
                for c in ex.children:
                    if not c.closed:ex.close(c)
            meter.closeall()
        except BaseException as e:
            save(d/'cleanup-stop-private.json',dict(error=type(e).__name__+': '+str(e),original_error=error))
            if error is None:status='TECHNICAL_STOP';error=type(e).__name__+': '+str(e)
        finally:
            dc,dw=time.process_time()-cc,time.perf_counter()-cw
            meter.mc+=dc;meter.mw+=dw;meter.regions.append(dict(label='448_no_integration_final_cleanup',CPU_s=dc,wall_s=dw))
        for s,h in handlers.items():signal.signal(s,h)
        meter.persist()
    if not actual and(d/'actual-results.json').exists():actual=read(d/'actual-results.json')
    gain=None
    if status=='NATIVE_EXIT60_PAIR_COMPLETED':
        a,b=[x['crossing_from_original_root']['elapsed_bracket_s'] for x in actual];gain=[a[0]-b[1],a[1]-b[0]]
    q=dict(stage=448,status=status,error=error,actual=actual,gain60_bracket_s=gain,budget=read(d/'budget.json'),plan_sha256=sha(d/'plan.json'),wholelap_pixel_generalization_qualified=False,new_learning_seed_HOLDOUT_SEALED_reserve_paid=0)
    save(d/'result.json',q);meter.checkpoint('CLOSED',status=status,error=error)
    print(json.dumps(dict(stage=448,status=status,error=error,native_actions=meter.nb['actions'],resets=meter.nb['resets'],ticks=meter.b['ticks'],worlds=meter.b['worlds'],gain=gain)))

if __name__=='__main__':
    root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
