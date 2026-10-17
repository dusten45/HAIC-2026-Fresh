"""472 one P4 native transfer; new raw only, preserved workspace reproduction inputs."""
import time
WORKER_START=time.perf_counter()
import copy,datetime,json,math,os,pickle,platform,random,shutil,signal,subprocess,sys,traceback
from dataclasses import asdict
from importlib import metadata
from fractions import Fraction
from pathlib import Path
import numpy as np
from retry.meter472 import Meter472
from retry.law468 import root_h13
from retry.native472 import actual472
from retry.compare465 import root_inputs
from retry.qualify453 import qualify,qualify_pending
from retry.qualify_parent453 import qualify as qualify_parent
from retry.pilot420_backend import GoalLedger,H,ResourceStop
from retry.terminal410_model import from_actual_full
from retry.ledger439 import require
from retry.loss389_analyze import read,save,sha
from retry.receipt421_io import save_receipt

G=Path(__file__).resolve().parents[1]
REVISION='472'
RAW=Path('/tmp/haic-retry-stage472-private')
NATIVE=Path('/tmp/haic-retry-stage472-native')
MIB=1024**2

def contract():
    c=copy.deepcopy(read(G/'retry/design471_next.json'))
    prior_storage=c['storage']
    c['baseline471']=dict(path=str(G/'retry/design471_next.json'),sha256=sha(G/'retry/design471_next.json'),status=c['status'])
    c.update(stage=472,runtime_stage=472,revision='472',execution_authorized=True,
             status='AUTHORIZED472_RAW_ONLY_STATIC_AND_SPACE_GATED',
             authorization='EXPLICIT472_RAW_ONLY_SINGLE_P4_TRANSFER_NO_RETRY_NOFOLLOWUP',
             writer='EXISTING_VERIFIED_PLAIN_ONLY',compression_enabled=False,
             storage_mode='NEW_RAW_ONLY_NO_ARCHIVE',new_raw_volume='/tmp',workspace_new_raw_archive_copy=False)
    c['storage']={k:copy.deepcopy(prior_storage[k]) for k in ['model_rate_bytes_per_tick','model_header_parts','model_header_base_bytes','native_rate_bytes_per_action','native_rate_bytes_per_raw_tick','native_source_samples','native_prefix_raw_ticks','native_suffix_raw_ticks','native_reset_raw_ticks','native_total_raw_ticks','native_fixed_allowance_bytes','native_metadata_bytes','native_raw_bytes']}
    c['storage'].update(margin=1.25,archive_bytes=0,archive_created=False,compression_credit=0,
                        temp_bytes=32*MIB,reserve_each_bytes=512*MIB,combined_raw_minimum_bytes=1699733185,
                        raw_only_registered_minimum_tmp_bytes=1699733185+32*MIB+512*MIB,
                        workspace_required_bytes=64*MIB+512*MIB,workspace_new_raw_archive_copies=0,
                        exact_storage_gate='Full new semantic-source manifest growth computed in plan.storage_forecast before any physics',
                        tmp_persistent_or_shared_assumed=False,loss_limit='If/tmp lost exact new raw cannot be reverified; hashes cannot reconstruct raw')
    c['source_gate']['unresolved_before_execution']=['472 production implementation and zero-physics current/terminal/pending startup fixture must pass static-result before any reset']
    c['source_gate']['implementation']='Native472/Query472 own-P4 pair production draft; static gate is mandatory'
    c['conclusion']='472 preregistration only; fresh full storage/static/source/root gates must pass before one native transfer; no retry or followup'
    c['runtime_caps']=dict(ticks=9216,worlds=185,CPU_s=900,wall_s=1200,actual_actions=195,resets=1,max_parallel=1)
    require(c['planned']['total_ticks']==8738 and c['planned']['total_worlds']==181,'472_SCIENCE_SCOPE')
    return c

def create_meter(d):return Meter472(d,worker_start=WORKER_START)

def world_audit():
    return dict(source_replay_restore_worlds=29,source_pending_worlds=3,source_parent_pending_worlds=3,
                root_independent_worlds=4,root_held_first_worlds=2,current_queries_max=70,
                current_independent_worlds_each=2,current_worlds=140,total_worlds=181,
                extra_main_parent_held_guardian_probe_worlds=0,source_ticks_cap=1242,root_ticks_cap=216,
                current_ticks_cap=7280,total_ticks_cap=8738,actual_actions_cap=195,resets_cap=1)

def cost_fixture(c=None):
    return dict(parts=dict(source=dict(ticks=1242,worlds=35),root_H13=dict(ticks=216,worlds=6),
                           current_P4_pairs=dict(ticks=7280,worlds=140)),ticks=8738,worlds=181,
                hard_ticks=9216,hard_worlds=185,actual_actions=195,resets=1,prefix_actions=125,suffix_actions=70)

def storage_forecast(c,semantic,oldsemantic,plan_bytes=2*MIB):
    s=c['storage'];growth=max(0,len(json.dumps(semantic,indent=2).encode())-len(json.dumps(oldsemantic,indent=2).encode()))
    rate=max(Fraction(126087848,1353),Fraction(str(s['model_rate_bytes_per_tick'])))
    header=max(778235,int(s['model_header_base_bytes']))+3*(growth+4096)+16384
    model=math.ceil(9216*rate*Fraction(5,4)+185*header+plan_bytes+16*MIB)
    native=max(457951038,int(s['native_raw_bytes']))
    raw=max(1699733185,model+native);reserve=512*MIB;workspace_metadata=64*MIB;temporary=32*MIB
    return dict(observed_bytes_per_tick=float(rate),observed_ratio_fraction=[rate.numerator,rate.denominator],
                empirical_margin=1.25,source_manifest_growth_bytes=growth,future_manifest_allowance_bytes=4096,
                fixed_header_base_bytes=max(778235,int(s['model_header_base_bytes'])),header_bytes_each=header,
                hard_ticks=9216,hard_worlds=185,scope_ticks=8738,scope_worlds=181,
                full_private_plan_bytes_allowance=plan_bytes,raw_metadata_allowance_bytes=16*MIB,
                model_raw_bytes=model,native_raw_bytes=native,combined_raw_bytes=raw,model_payload_bytes=model,
                temp_bytes=temporary,reserve_each_bytes=reserve,tmp_required_bytes=raw+temporary+reserve,
                workspace_metadata_allowance_bytes=workspace_metadata,workspace_required_bytes=workspace_metadata+reserve,
                model_required_bytes=raw+temporary+reserve,runtime_free_stop_bytes=reserve,
                archive_bytes=0,archive_created=False,workspace_new_raw_archive_copy=False,
                retention_format='NEW_RAW_ONLY_ORIGINAL_PLAIN_FILES_NO_ARCHIVE_NO_COMPRESSION_CREDIT',
                tmp_persistent_or_shared_assumed=False,loss_limit='If/tmp is lost exact new raw cannot be reverified; workspace hashes cannot reconstruct new raw',estimates_not_guaranteed=True)

def storage_status(p,free):
    s=p['storage_forecast'];required={'/tmp':s['tmp_required_bytes'],'/workspace':s['workspace_required_bytes']}
    return {v:dict(free_bytes=free[v],required_bytes=required[v],shortage_bytes=max(0,required[v]-free[v])) for v in required}

def check_storage(p):
    free={v:shutil.disk_usage(v).free for v in ('/tmp','/workspace')};status=storage_status(p,free)
    for v,s in status.items():require(s['shortage_bytes']==0,'472_STORAGE_PREFLIGHT:'+v+':'+json.dumps(s))
    return free

def runtime_environment():
    # Version pins exclude environment variables, credential stores and direct-URL secrets.
    pins=sorted(set((dist.metadata.get('Name') or 'UNKNOWN')+'=='+dist.version for dist in metadata.distributions()))
    git=subprocess.run(['git','rev-parse','HEAD'],cwd=G,check=True,capture_output=True,text=True).stdout.strip()
    return dict(python=sys.version,executable=sys.executable,numpy=np.__version__,platform=platform.platform(),
                byteorder=sys.byteorder,pip_freeze_version_pins=pins,
                pip_freeze_scope='all installed distribution name/version pins; no direct URLs or environment variables',
                git_head=git,argv=list(sys.argv))

def final_limit_error(meter):
    cpu,wall=meter.wholetime();reasons=[]
    if cpu>=900:reasons.append('whole_CPU900')
    if wall>=1200:reasons.append('whole_wall1200')
    if datetime.datetime.now(datetime.timezone.utc)>=meter.deadline():reasons.append('deadline')
    return None if not reasons else '472_FINAL_CLOSURE_RESOURCE_STOP:'+','.join(reasons)

def prepare(root):
    root=Path(root);d=root/('stage'+REVISION)
    require(not d.exists() and not d.is_symlink() and not RAW.exists() and not NATIVE.exists() and not (root/'stage472-native').exists() and not (root/'stage472-native').is_symlink(),'472_ONCE_FRESH_REVISION')
    require(not(root/'project-effective-budget-v476.json').exists(),'472_NO_FOREIGN476')
    c=contract();old=read(root/'stage469-revision1/plan.json');ledger_path=root/'project-effective-budget-v475.json';v=read(ledger_path)
    require(v['stage463_status']=='CLOSED' and (v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(26346,84000,0),'472_LEDGER_UNCHANGED')
    require(read(root/'research-deadline-current.json')['deadline_utc']==c['deadline_utc']=='2026-10-20T10:01:55Z','472_DEADLINE')
    state,memory,ledger,rng,blob,expected=root_inputs(root)
    projection=Path(old['projection_path']);correction=root/'stage441/authorization-correction-private.json'
    require(sha(projection)=='85ac335bf32d11da78e2d76a213b6096a0d357bc4f5d334196695343717d213f','472_FROZEN_PROJECTION')
    require(sha(correction)==c['authorization_extension_sha256']==v['authorization_correction_sha256'],'472_AUTHORIZATION_EXTENSION')
    files={Path(f) for f in old['sources']}
    files.update(G/'retry'/n for n in ['meter472.py','budget472.py','transfer472.py','native472.py','query472.py','static472.py','test_transfer472.py','analyze472.py','retain472.py','design471_result.md','design471_next.json'])
    files.update([projection,correction,ledger_path,root/'stage469-revision1-plan-durable-private.json'])
    files.update(f for f in (root/'stage458/actual_P').glob('*') if f.is_file())
    files.add(root/'stage463-native/actual_SecantOnce/root-before-nominal-private.json')
    semantic=dict(old['semantic_sources']);semantic.update({str(f):sha(f) for f in files if str(f).startswith(str(G)) and f.suffix=='.py'})
    p=dict(stage=472,revision=REVISION,execution=c,execution_allowed=False,static_required_before_physics=True,
           registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=c['deadline_utc'],
           caps=c['runtime_caps'],scope=dict(ticks=8738,worlds=181),case=read(root/'stage463/plan.json')['case'],budget_fixture=cost_fixture(),world_audit=world_audit(),
           fixed_plan=old['fixed_plan'],pace_path=old['pace_path'],projection_path=str(projection),projection_sha256=sha(projection),
           authorization_extension_path=str(correction),authorization_extension_sha256=sha(correction),
           sources={str(f):sha(f) for f in sorted(files)},semantic_sources=semantic,
           protected=old['protected'],original408_preserve=old['original408_preserve'],
           contract_sha256=sha(G/'retry/design471_result.md'),contract_json_sha256=sha(G/'retry/design471_next.json'),
           budget_before_path=str(ledger_path),budget_before_sha256=sha(ledger_path),ledger_path=str(root/'project-effective-budget-v476.json'),storage_free_stop_bytes=512*MIB,
           raw_directory=str(RAW),native_directory=str(root/'stage472-native'),native_raw_directory=str(NATIVE),workspace_new_raw_archive_copy=False,
           runtime_environment=runtime_environment(),
           whole_first_commands={'Projected4ReferenceCommonPulse':expected[0]['command']},
           profile_inputs=dict(fixed_plan_sha256=sha(old['fixed_plan']),pace_sha256=sha(old['pace_path']),projection_sha256=sha(projection)),
           reproducibility_conditions='Existing designated cloud; frozen source/input hashes and RNG receipt; unchanged plain writer; single native P4 transfer with frozen125prefix and everycurrentownP4pair; original raw only remains /tmp; no archive or compressed transformation or workspace raw copy',
           authorization=c['authorization'],new_seed_learning_HOLDOUT_SEALED_reserve_paid=0)
    require(len(p['protected'])+len(p['original408_preserve'])==18,'472_PROTECTED18')
    p['storage_forecast']=storage_forecast(c,semantic,old['semantic_sources']);p['storage_start_free_bytes']=check_storage(p);p['storage_preflight']=storage_status(p,p['storage_start_free_bytes'])
    material=root/('stage'+REVISION+'-input-material-private.json')
    require(not material.exists(),'472_FRESH_INPUT_MATERIAL')
    save_receipt(material,dict(state=state,memory=memory,ledger=asdict(ledger),RNG_blob=blob,RNG_source=rng,
                              expected=expected,fixed=read(old['fixed_plan']),pace=read(old['pace_path']),
                              projected_nodes=read(projection)['projected_nodes']))
    p['input_material_path']=str(material);p['input_material_sha256']=sha(material);p['sources'][str(material)]=sha(material)
    require(len(json.dumps(p,indent=2).encode())<=2*MIB,'472_PLAN_BYTES_ALLOWANCE')
    require(material.stat().st_size+2*MIB<=64*MIB,'472_WORKSPACE_REPRO_METADATA_ALLOWANCE')
    for group in ('protected','original408_preserve'):
        for f,h in p[group].items():require(sha(f)==h,'472_PROTECTED:'+f)
    RAW.mkdir(mode=0o700);NATIVE.mkdir(mode=0o700);(root/'stage472-native').symlink_to(NATIVE,target_is_directory=True);d.symlink_to(RAW,target_is_directory=True);save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n')
    save(root/('stage'+REVISION+'-plan-durable-private.json'),p)
    save(d/'progress-private.json',dict(stage=472,revision=REVISION,phase='PLAN_FROZEN',model_ticks=0,model_worlds=0,actual_actions=0,resets=0))
    print(json.dumps(dict(stage=472,revision=REVISION,plan_sha256=sha(d/'plan.json'),cost=p['budget_fixture'],world_audit=p['world_audit'],storage_forecast=p['storage_forecast'],storage_preflight=p['storage_preflight'])))

def run(root):
    root=Path(root);d=root/('stage'+REVISION);p=read(d/'plan.json');static=read(d/p.get('static_result_name','static-result.json'))
    require(not(d/'opening.json').exists() and static['passed'],'472_ONCE_STATIC')
    require(sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()==static['plan_sha256'],'472_PLAN_STATIC_BINDING')
    require(p['execution']==contract() and p['caps']==contract()['runtime_caps'] and p['scope']==dict(ticks=8738,worlds=181) and p['budget_fixture']==cost_fixture() and p['world_audit']==world_audit(),'472_SINGLE_CONTRACT_SCOPE')
    for group in ('sources','protected','original408_preserve'):
        for f,h in p[group].items():require(sha(f)==h,'472_SOURCE_CHANGED:'+f)
    check_storage(p);state,memory,ledger,rng,blob,expected=root_inputs(root);py,npr=pickle.loads(blob);random.setstate(py);np.random.set_state(npr)
    fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(p['pace_path'])['frozen268']);meter=create_meter(d)
    cohorts=[];cohort_result=None;actual_results=[];status='STARTED';error=None;stage='fresh_source';preflight_counts={}
    save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(d/'plan.json'),static_sha256=sha(d/p.get('static_result_name','static-result.json'))))
    def timeout(*args):raise ResourceStop('472_whole_CPU900_wall1200_or_deadline')
    handlers={s:signal.signal(s,timeout) for s in (signal.SIGPROF,signal.SIGALRM)};meter.timers()
    try:
        with meter.model('472_fresh_source_and_root'):
            meter.checkpoint('FRESH_SOURCE_STARTED')
            fork=read(root/'stage423/actual_C0/fork-private.json');oldstate=from_actual_full(fork);oldmem=fork['controller']['before'];row=json.loads((root/'stage423/actual_C0/trace-private.jsonl').read_text().splitlines()[118]);oldledger=GoalLedger(row['progress_before'],row['goal_before'],H-(row['deadline_before']-118),round(oldstate['physical']['actual_time']*50))
            qualify(root,meter,fixed,pace,oldstate,oldmem,oldledger);qualify_pending(root,meter,fixed,pace);meter.qualification_passed=True;qualify_parent(root,meter,fixed,pace)
            require(meter.b['ticks']<=1242 and meter.b['worlds']==35,'472_SOURCE35')
            preflight_counts['source']=dict(ticks=meter.b['ticks'],worlds=meter.b['worlds'])
            save(d/'preflight-private.json',dict(passed=True,ticks=meter.b['ticks'],worlds=meter.b['worlds'],actual_actions=0,resets=0));meter.checkpoint('OLD_SOURCE_PASSED')
            stage='fresh_root_H13';cohort_result=root_h13(root,meter,fixed,pace,state,memory,ledger,expected);cohorts=cohort_result['cohorts']
            require(meter.b['ticks']<=1458 and meter.b['worlds']<=41,'472_ROOT41_SCOPE')
            preflight_counts['root']=dict(ticks=meter.b['ticks'],worlds=meter.b['worlds'])
        if cohort_result['passed']:
            require(meter.b['worlds']==41,'472_ROOT_EXACT41')
            meter.checkpoint('ROOT_H13_PASSED');stage='single_native_P4_transfer'
            actual_results=actual472(root,meter,fixed,pace)
            require(meter.b['ticks']<=8738 and meter.b['worlds']<=181,'472_ALL_IN_MODEL_SCOPE')
            require(len(actual_results)==1,'472_SINGLE_CANDIDATE_ONLY')
            status='NATIVE_P4_TRANSFER_COMPLETE' if actual_results[0]['completed'] else 'NATIVE_P4_TRANSFER_STOP'
            error=actual_results[0].get('error')
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
        for f,h in p[group].items():require(sha(f)==h,'472_FINAL_PROTECTED:'+f)
    require(sha(p['budget_before_path'])==p['budget_before_sha256'],'472_GLOBAL_LEDGER_CHANGED')
    final_error=final_limit_error(meter)
    if final_error:status='STOP';error=final_error if error is None else error+'; '+final_error
    meter.persist()
    result=dict(stage=472,revision=REVISION,status=status,error=error,last_stage=stage,cohorts=cohorts,cohort_result=cohort_result,root_qualification=cohort_result,preflight_counts=preflight_counts,actual_results=actual_results,budget=read(d/'budget.json'),plan_sha256=sha(d/'plan.json'),live_ledger_sha256=meter.charge_ledger.current_hash,new_actual_actions=meter.nb['actions'],new_resets=meter.nb['resets'],new_seed_learning_HOLDOUT_SEALED_reserve_paid=0,no_followup=True)
    save(d/'result.json',result);meter.checkpoint('CLOSED',status=status,error=error)
    final_error=final_limit_error(meter)
    if final_error and final_error not in (error or ''):
        status='STOP';error=final_error if error is None else error+'; '+final_error
        meter.persist();result.update(status=status,error=error,budget=read(d/'budget.json'));save(d/'result.json',result);meter.checkpoint('CLOSED_RESOURCE_STOP',status=status,error=error)
    print(json.dumps(dict(stage=472,revision=REVISION,status=status,error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds'],actual=meter.nb['actions'],resets=meter.nb['resets'])),flush=True)

if __name__=='__main__':prepare(Path(sys.argv[2])) if sys.argv[1]=='prepare' else run(Path(sys.argv[2]))
