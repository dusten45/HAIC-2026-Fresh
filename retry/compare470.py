"""469 revision1: one plain-writer whole-window pair, all raw retention in /tmp."""
import time
WORKER_START=time.perf_counter()
import copy,datetime,json,math,os,pickle,platform,random,shutil,signal,subprocess,sys,traceback
from dataclasses import asdict
from importlib import metadata
from fractions import Fraction
from pathlib import Path
import numpy as np
from retry.meter470 import Meter470
from retry.law468 import root_h13
from retry.law470 import whole_parents
from retry.compare465 import root_inputs
from retry.qualify453 import qualify,qualify_pending
from retry.qualify_parent453 import qualify as qualify_parent
from retry.pilot420_backend import GoalLedger,H,ResourceStop
from retry.terminal410_model import from_actual_full
from retry.ledger439 import require
from retry.loss389_analyze import read,save,sha
from retry.receipt421_io import save_receipt

G=Path(__file__).resolve().parents[1]
REVISION='469-revision1'
RAW=Path('/tmp/haic-retry-stage469-revision1-private')
ARCHIVE=Path('/tmp/haic-retry-stage469-revision1-retained')
MIB=1024**2

def contract():
    c=copy.deepcopy(read(G/'retry/design469_next.json'))
    c.update(runtime_stage=470,revision=REVISION,execution_authorized=True,
             authorization='EXPLICIT469_REVISION1_ONE_PAIR_TMP_FULL_RAW_RETENTION_NOFOLLOWUP',
             writer='EXISTING_VERIFIED_PLAIN_ONLY',compression_enabled=False,
             new_raw_and_retained_archive_volume='/tmp',workspace_new_raw_archive_copy=False)
    require(c['hard']==dict(ticks=2048,worlds=43,CPU_s=180,wall_s=300,actual_actions=0,resets=0),'470_SCIENCE_HARD')
    require(c['planned']['total_ticks']==2018 and c['planned']['total_worlds']==43,'470_SCIENCE_SCOPE')
    return c

def create_meter(d):return Meter470(d,worker_start=WORKER_START)

def world_audit():
    return dict(source_replay_restore_worlds=29,source_pending_worlds=3,source_parent_pending_worlds=3,
                root_independent_worlds=4,root_held_first_worlds=2,whole_parent_worlds=2,
                total_worlds=43,extra_main_or_capture_or_held_or_probe_worlds=0,
                source_ticks_cap=1242,root_ticks_cap=216,whole_ticks_cap=560,total_ticks_cap=2018,
                independent_whole_repetitions=0,actual_actions=0,resets=0)

def cost_fixture(c=None):
    return dict(parts=dict(source=dict(ticks=1242,worlds=35),root_H13=dict(ticks=216,worlds=6),
                           whole_parents=dict(ticks=560,worlds=2)),ticks=2018,worlds=43,
                hard_ticks=2048,hard_worlds=43,actual_actions=0,resets=0,whole_parent_actions_each=70)

def storage_forecast(c,semantic,oldsemantic,plan_bytes=2*MIB):
    s=c['storage'];growth=max(0,len(json.dumps(semantic,indent=2).encode())-len(json.dumps(oldsemantic,indent=2).encode()))
    rate=max(Fraction(126087848,1353),Fraction(str(s['observed_bytes_per_tick'])))
    header=max(777215,int(s['header_base_bytes']))+3*(growth+4096)+16384
    raw=math.ceil(2048*rate*Fraction(5,4)+43*header+plan_bytes+16*MIB)
    archive=math.ceil(raw*Fraction(11,10)+32*MIB)
    temporary=32*MIB;reserve=512*MIB;workspace_metadata=64*MIB
    return dict(observed_bytes_per_tick=float(rate),observed_ratio_fraction=[rate.numerator,rate.denominator],
                empirical_margin=1.25,source_manifest_growth_bytes=growth,future_manifest_allowance_bytes=4096,
                fixed_header_base_bytes=max(777215,int(s['header_base_bytes'])),header_bytes_each=header,
                hard_ticks=2048,hard_worlds=43,scope_ticks=2018,scope_worlds=43,
                full_private_plan_bytes_allowance=plan_bytes,raw_metadata_allowance_bytes=16*MIB,
                raw_payload_forecast_bytes=raw,model_payload_bytes=raw,archive_forecast_bytes=archive,
                archive_temporary_allowance_bytes=temporary,reserve_bytes_each_volume=reserve,
                tmp_required_bytes=raw+archive+temporary+reserve,
                workspace_metadata_allowance_bytes=workspace_metadata,workspace_required_bytes=workspace_metadata+reserve,
                model_required_bytes=raw+archive+temporary+reserve,runtime_free_stop_bytes=reserve,
                simultaneous_raw_archive_temp=True,workspace_new_raw_archive_copy=False,
                retention_format='FULL_PRIVATE_RAW_PLAIN_ARCHIVE_NO_COMPRESSION_CREDIT',estimates_not_guaranteed=True)

def storage_status(p,free):
    s=p['storage_forecast'];required={'/tmp':s['tmp_required_bytes'],'/workspace':s['workspace_required_bytes']}
    return {v:dict(free_bytes=free[v],required_bytes=required[v],shortage_bytes=max(0,required[v]-free[v])) for v in required}

def check_storage(p):
    free={v:shutil.disk_usage(v).free for v in ('/tmp','/workspace')};status=storage_status(p,free)
    for v,s in status.items():require(s['shortage_bytes']==0,'470_STORAGE_PREFLIGHT:'+v+':'+json.dumps(s))
    return free

def runtime_environment():
    # Version pins exclude environment variables, credential stores and direct-URL secrets.
    pins=sorted(set((dist.metadata.get('Name') or 'UNKNOWN')+'=='+dist.version for dist in metadata.distributions()))
    git=subprocess.run(['git','rev-parse','HEAD'],cwd=G,check=True,capture_output=True,text=True).stdout.strip()
    return dict(python=sys.version,executable=sys.executable,numpy=np.__version__,platform=platform.platform(),
                byteorder=sys.byteorder,pip_freeze_version_pins=pins,
                pip_freeze_scope='all installed distribution name/version pins; no direct URLs or environment variables',
                git_head=git,argv=list(sys.argv))

def prepare(root):
    root=Path(root);d=root/('stage'+REVISION)
    require(not d.exists() and not d.is_symlink() and not RAW.exists() and not ARCHIVE.exists(),'470_ONCE_FRESH_REVISION')
    c=contract();old=read(root/'stage468/plan.json');ledger_path=root/'project-effective-budget-v475.json';v=read(ledger_path)
    require(sha(root/'stage468/plan.json')==c['prior_plan_sha256'],'470_PRIOR468_PLAN')
    require(v['stage463_status']=='CLOSED' and (v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(26346,84000,0),'470_LEDGER_UNCHANGED')
    require(read(root/'research-deadline-current.json')['deadline_utc']==c['deadline_utc']=='2026-10-20T10:01:55Z','470_DEADLINE')
    state,memory,ledger,rng,blob,expected=root_inputs(root)
    projection=Path(old['projection_path']);correction=root/'stage441/authorization-correction-private.json'
    require(sha(projection)==c['frozen_profile_sha256']=='85ac335bf32d11da78e2d76a213b6096a0d357bc4f5d334196695343717d213f','470_FROZEN_PROJECTION')
    require(sha(correction)==c['authorization_extension_evidence_sha256']==v['authorization_correction_sha256'],'470_AUTHORIZATION_EXTENSION')
    files={Path(f) for f in old['sources']}
    files.update(G/'retry'/n for n in ['meter470.py','compare470.py','law470.py','static470.py','test_compare470.py','analyze470.py','retain470.py','design469_result.md','design469_next.json'])
    files.update([projection,correction,ledger_path,root/'stage468-plan-durable-private.json'])
    semantic=dict(old['semantic_sources']);semantic.update({str(f):sha(f) for f in files if str(f).startswith(str(G)) and f.suffix=='.py'})
    p=dict(stage=470,revision=REVISION,execution=c,execution_allowed=False,static_required_before_physics=True,
           registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=c['deadline_utc'],
           caps=c['hard'],scope=dict(ticks=2018,worlds=43),budget_fixture=cost_fixture(),world_audit=world_audit(),
           fixed_plan=old['fixed_plan'],pace_path=old['pace_path'],projection_path=str(projection),projection_sha256=sha(projection),
           authorization_extension_path=str(correction),authorization_extension_sha256=sha(correction),
           sources={str(f):sha(f) for f in sorted(files)},semantic_sources=semantic,
           protected=old['protected'],original408_preserve=old['original408_preserve'],
           contract_sha256=sha(G/'retry/design469_result.md'),contract_json_sha256=sha(G/'retry/design469_next.json'),
           ledger_path=str(ledger_path),ledger_sha256=sha(ledger_path),storage_free_stop_bytes=512*MIB,
           raw_directory=str(RAW),archive_directory=str(ARCHIVE),workspace_new_raw_archive_copy=False,
           runtime_environment=runtime_environment(),
           whole_first_commands={arm:expected[0]['command'] for arm in c['policy']['arms']},
           profile_inputs=dict(fixed_plan_sha256=sha(old['fixed_plan']),pace_sha256=sha(old['pace_path']),projection_sha256=sha(projection)),
           reproducibility_conditions='Existing designated cloud; frozen source/input hashes and RNG receipt; unchanged plain writer; whole arms once; original raw remains /tmp; no compressed transformation or workspace raw copy',
           authorization=c['authorization'],new_seed_learning_HOLDOUT_SEALED_reserve_paid=0)
    require(len(p['protected'])+len(p['original408_preserve'])==18,'470_PROTECTED18')
    p['storage_forecast']=storage_forecast(c,semantic,old['semantic_sources']);p['storage_start_free_bytes']=check_storage(p);p['storage_preflight']=storage_status(p,p['storage_start_free_bytes'])
    material=root/('stage'+REVISION+'-input-material-private.json')
    require(not material.exists(),'470_FRESH_INPUT_MATERIAL')
    save_receipt(material,dict(state=state,memory=memory,ledger=asdict(ledger),RNG_blob=blob,RNG_source=rng,
                              expected=expected,fixed=read(old['fixed_plan']),pace=read(old['pace_path']),
                              projected_nodes=read(projection)['projected_nodes']))
    p['input_material_path']=str(material);p['input_material_sha256']=sha(material);p['sources'][str(material)]=sha(material)
    require(len(json.dumps(p,indent=2).encode())<=2*MIB,'470_PLAN_BYTES_ALLOWANCE')
    require(material.stat().st_size+2*MIB<=64*MIB,'470_WORKSPACE_REPRO_METADATA_ALLOWANCE')
    for group in ('protected','original408_preserve'):
        for f,h in p[group].items():require(sha(f)==h,'470_PROTECTED:'+f)
    RAW.mkdir(mode=0o700);d.symlink_to(RAW,target_is_directory=True);save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n')
    save(root/('stage'+REVISION+'-plan-durable-private.json'),p)
    save(d/'progress-private.json',dict(stage=470,revision=REVISION,phase='PLAN_FROZEN',model_ticks=0,model_worlds=0,actual_actions=0,resets=0))
    print(json.dumps(dict(stage=470,revision=REVISION,plan_sha256=sha(d/'plan.json'),cost=p['budget_fixture'],world_audit=p['world_audit'],storage_forecast=p['storage_forecast'],storage_preflight=p['storage_preflight'])))

def run(root):
    root=Path(root);d=root/('stage'+REVISION);p=read(d/'plan.json');static=read(d/p.get('static_result_name','static-result.json'))
    require(not(d/'opening.json').exists() and static['passed'],'470_ONCE_STATIC')
    require(sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()==static['plan_sha256'],'470_PLAN_STATIC_BINDING')
    require(p['execution']==contract() and p['caps']==contract()['hard'] and p['scope']==dict(ticks=2018,worlds=43) and p['budget_fixture']==cost_fixture() and p['world_audit']==world_audit(),'470_SINGLE_CONTRACT_SCOPE')
    for group in ('sources','protected','original408_preserve'):
        for f,h in p[group].items():require(sha(f)==h,'470_SOURCE_CHANGED:'+f)
    check_storage(p);state,memory,ledger,rng,blob,expected=root_inputs(root);py,npr=pickle.loads(blob);random.setstate(py);np.random.set_state(npr)
    fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(p['pace_path'])['frozen268']);meter=create_meter(d)
    cohorts=[];cohort_result=None;whole_result=None;status='STARTED';error=None;stage='fresh_source';preflight_counts={}
    save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(d/'plan.json'),static_sha256=sha(d/p.get('static_result_name','static-result.json'))))
    def timeout(*args):raise ResourceStop('470_whole_CPU180_wall300_or_deadline')
    handlers={s:signal.signal(s,timeout) for s in (signal.SIGPROF,signal.SIGALRM)};meter.timers()
    try:
        with meter.model('470_source_root_and_two_once_whole_parents'):
            meter.checkpoint('FRESH_SOURCE_STARTED')
            fork=read(root/'stage423/actual_C0/fork-private.json');oldstate=from_actual_full(fork);oldmem=fork['controller']['before'];row=json.loads((root/'stage423/actual_C0/trace-private.jsonl').read_text().splitlines()[118]);oldledger=GoalLedger(row['progress_before'],row['goal_before'],H-(row['deadline_before']-118),round(oldstate['physical']['actual_time']*50))
            qualify(root,meter,fixed,pace,oldstate,oldmem,oldledger);qualify_pending(root,meter,fixed,pace);meter.qualification_passed=True;qualify_parent(root,meter,fixed,pace)
            require(meter.b['ticks']<=1242 and meter.b['worlds']==35,'470_SOURCE35')
            preflight_counts['source']=dict(ticks=meter.b['ticks'],worlds=meter.b['worlds'])
            save(d/'preflight-private.json',dict(passed=True,ticks=meter.b['ticks'],worlds=meter.b['worlds'],actual_actions=0,resets=0));meter.checkpoint('OLD_SOURCE_PASSED')
            stage='fresh_root_H13';cohort_result=root_h13(root,meter,fixed,pace,state,memory,ledger,expected);cohorts=cohort_result['cohorts']
            require(meter.b['ticks']<=1458 and meter.b['worlds']<=41,'470_ROOT41_SCOPE')
            preflight_counts['root']=dict(ticks=meter.b['ticks'],worlds=meter.b['worlds'])
            if cohort_result['passed']:
                require(meter.b['worlds']==41,'470_ROOT_EXACT41')
                meter.checkpoint('ROOT_H13_PASSED');stage='two_once_whole_parents'
                whole_result=whole_parents(root,meter,fixed,pace,state,memory,ledger,expected)
                require(meter.b['ticks']<=2018 and meter.b['worlds']<=43,'470_WHOLE_SCOPE')
                require(meter.b['worlds']==43 and whole_result['model_worlds']==2 and len(whole_result['policies'])==2,'470_BOTH_FIXED_WHOLE_ARMS_ATTEMPTED')
                status='WHOLE_COMPARISON_COMPLETE'
            else:status='ROOT_QUALIFICATION_STOP'
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
    for group in ('protected','original408_preserve'):
        for f,h in p[group].items():require(sha(f)==h,'470_FINAL_PROTECTED:'+f)
    require(sha(p['ledger_path'])==p['ledger_sha256'],'470_GLOBAL_LEDGER_CHANGED')
    result=dict(stage=470,revision=REVISION,status=status,error=error,last_stage=stage,cohorts=cohorts,cohort_result=cohort_result,root_qualification=cohort_result,preflight_counts=preflight_counts,whole_result=whole_result,whole_arms=whole_result.get('policies',[]) if whole_result else [],budget=read(d/'budget.json'),plan_sha256=sha(d/'plan.json'),new_actual_actions=0,new_resets=0,new_seed_learning_HOLDOUT_SEALED_reserve_paid=0,no_followup=True)
    save(d/'result.json',result);meter.checkpoint('CLOSED',status=status,error=error)
    print(json.dumps(dict(stage=470,revision=REVISION,status=status,error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds'],actual=0,resets=0)),flush=True)

if __name__=='__main__':prepare(Path(sys.argv[2])) if sys.argv[1]=='prepare' else run(Path(sys.argv[2]))
