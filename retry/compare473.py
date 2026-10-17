"""473 fixed pre23 natural own-reference model pair; raw only, no native capability."""
import time
WORKER_START=time.perf_counter()
import ast,copy,datetime,json,math,os,pickle,platform,random,shutil,signal,subprocess,sys,traceback
from dataclasses import asdict
from importlib import metadata
from fractions import Fraction
from pathlib import Path
import numpy as np
from retry.meter473 import Meter473
from retry.law473 import root_h13,root_inputs473 as root_inputs,root_source_paths
from retry.law473 import whole_parents
from retry.qualify453 import qualify,qualify_pending
from retry.qualify_parent453 import qualify as qualify_parent
from retry.pilot420_backend import GoalLedger,H,ResourceStop
from retry.terminal410_model import from_actual_full
from retry.ledger439 import require
from retry.loss389_analyze import read,save,sha
from retry.receipt421_io import save_receipt

G=Path(__file__).resolve().parents[1]
REVISION='473'
RAW=Path('/tmp/haic-retry-stage473-private')

MIB=1024**2

def contract():
    return dict(stage=473,status='PRE_REGISTERED_STATIC_SPACE_AND_SOURCE_GATED',execution_authorized=True,
                deadline_utc='2026-10-20T10:01:55Z',authorization_extension_sha256='3b0dc9c16c5356e107e73dbd8a8f88e75a2434f9e24f046358783fbde8307078',
                authorization='EXPLICIT473_FIXED_PRE23_TWO_NATURAL_MODEL_LAWS_ONCE_NOFOLLOWUP',
                question='Does frozen P4 advantage persist from the fixed post-launch FIRST_LAP pre23 root through own model finish?',
                root=dict(source='453 actual_baseline pre23',native_pre_step=23,new_root_search=False,after_observed_launch=True,required_phase='FIRST_LAP'),
                policy=dict(arms=['OriginalReference','Projected4Reference'],point_derivative_FF=True,feedback=1.5,hold_s=.08,forced_first_fullgas=False,own_terminal_target=True,guardian_rescue_ranking=0),
                whole_parent=dict(max_actions_each=250,independent_repetitions=0,once_each=True),
                planned=dict(source_ticks=1242,source_worlds=35,root_ticks=216,root_worlds=6,whole_ticks=2000,whole_worlds=2,total_ticks=3458,total_worlds=43),
                hard=dict(ticks=4096,worlds=43,CPU_s=300,wall_s=600,actual_actions=0,resets=0,max_parallel=1),
                projection_sha256='85ac335bf32d11da78e2d76a213b6096a0d357bc4f5d334196695343717d213f',
                goal=dict(native_target_s=11.99,profile_clock12_260_is_diagnostic_only=True,no_native_or_generalization_claim=True),
                storage=dict(model_ratio_samples=[[503172296,5461],[126087848,1353],[138331916,1671]],header_base_bytes=779344,
                             margin=1.25,reserve_bytes=512*MIB,raw_metadata_bytes=16*MIB,plan_bytes=2*MIB,temp_bytes=32*MIB,workspace_metadata_bytes=64*MIB,
                             new_raw_volume='/tmp',archive_bytes=0,compression_credit=0,workspace_new_raw_archive_copy=False),
                new_seed_learning_HOLDOUT_SEALED_reserve_paid=0,no_followup=True)

def create_meter(d):return Meter473(d,worker_start=WORKER_START)

def world_audit():
    return dict(source_replay_restore_worlds=29,source_pending_worlds=3,source_parent_pending_worlds=3,
                root_independent_worlds=4,root_held_first_worlds=2,whole_parent_worlds=2,total_worlds=43,
                extra_main_capture_held_probe_worlds=0,source_ticks_cap=1242,root_ticks_cap=216,whole_ticks_cap=2000,total_ticks_cap=3458,
                independent_whole_repetitions=0,actual_actions=0,resets=0)

def cost_fixture(c=None):
    return dict(parts=dict(source=dict(ticks=1242,worlds=35),root_H13=dict(ticks=216,worlds=6),whole_parents=dict(ticks=2000,worlds=2)),
                ticks=3458,worlds=43,hard_ticks=4096,hard_worlds=43,actual_actions=0,resets=0,whole_parent_actions_each=250)

def storage_forecast(c,semantic,oldsemantic,plan_bytes=2*MIB):
    s=c['storage'];growth=max(0,len(json.dumps(semantic,indent=2).encode())-len(json.dumps(oldsemantic,indent=2).encode()))
    rate=max(Fraction(*sample) for sample in s['model_ratio_samples']);header=s['header_base_bytes']+3*(growth+4096)+16384
    raw=math.ceil(4096*rate*Fraction(5,4)+43*header+plan_bytes+16*MIB)
    return dict(observed_bytes_per_tick=float(rate),model_ratio_samples=s['model_ratio_samples'],source_manifest_growth_bytes=growth,
                header_bytes_each=header,empirical_margin=1.25,hard_ticks=4096,hard_worlds=43,scope_ticks=3458,scope_worlds=43,
                full_private_plan_bytes_allowance=plan_bytes,raw_metadata_allowance_bytes=16*MIB,raw_payload_forecast_bytes=raw,model_payload_bytes=raw,
                temp_bytes=32*MIB,reserve_bytes_each_volume=512*MIB,tmp_required_bytes=raw+32*MIB+512*MIB,model_required_bytes=raw+32*MIB+512*MIB,
                workspace_metadata_allowance_bytes=64*MIB,workspace_required_bytes=64*MIB+512*MIB,runtime_free_stop_bytes=512*MIB,
                archive_bytes=0,archive_created=False,retention_format='ORIGINAL_RAW_ONLY_NO_ARCHIVE',workspace_new_raw_archive_copy=False,
                tmp_persistent_or_shared_assumed=False,loss_limit='Loss of/tmp prevents exact new raw verification; hashes cannot reconstruct raw',estimates_not_guaranteed=True)

def source_closure(seeds):
    pending=list(seeds);found=set()
    while pending:
        path=Path(pending.pop()).resolve()
        if path in found:continue
        require(path.is_file(),'473_LOCAL_SOURCE_MISSING:'+str(path));found.add(path)
        if path.suffix!='.py':continue
        for node in ast.walk(ast.parse(path.read_text())):
            modules=[]
            if isinstance(node,ast.Import):modules=[alias.name for alias in node.names]
            elif isinstance(node,ast.ImportFrom):
                if node.level:
                    base=path.parent
                    for _ in range(node.level-1):base=base.parent
                    if node.module:base=base.joinpath(*node.module.split('.'))
                    local=base.with_suffix('.py')
                    if local.is_file():pending.append(local)
                    elif (base/'__init__.py').is_file():pending.append(base/'__init__.py')
                    for alias in node.names:
                        if alias.name=='*':continue
                        child=base/alias.name
                        if child.with_suffix('.py').is_file():pending.append(child.with_suffix('.py'))
                        elif (child/'__init__.py').is_file():pending.append(child/'__init__.py')
                elif node.module:modules=[node.module]+[node.module+'.'+alias.name for alias in node.names if alias.name!='*']
            for module in modules:
                base=G.joinpath(*module.split('.'));local=base.with_suffix('.py')
                if local.is_file():pending.append(local)
                elif (base/'__init__.py').is_file():pending.append(base/'__init__.py')
                for length in range(1,len(module.split('.'))):
                    init=G.joinpath(*module.split('.')[:length])/'__init__.py'
                    if init.is_file():pending.append(init)
    return found

def qualification_source_paths(root):
    paths=[root/p for p in ['stage423/actual_C0/fork-private.json','stage423/actual_C0/trace-private.jsonl','stage427/actual_P/trace-private.jsonl',
            'stage425/actual_P/final-private.json','stage425/actual_P/trace-private.jsonl','stage425/actual_P/result.json','stage425/actual_P/actual_P_177_nominal_1-private.json',
            'stage435/P_decision55-context-stop-private.json','stage435/parent_P-observer-private.json','stage435/parent_P-private.json']]
    paths += [root/('stage427/actual_P/actual_P_'+str(n)+'-receipt-private.json') for n in range(119,131)]
    names=['qualification_'+arm+'_'+str(rep) for arm in ['C0','P'] for rep in [1,2]]
    names += ['qualification_restore'+str(n)+'_'+str(rep) for n in range(1,13) for rep in [1,2]]
    names += ['pending_nominal_1','pending_nominal_2']
    paths += [root/('stage433/'+name+'-private.json') for name in names]
    number=read(root/'stage435/parent_P-observer-private.json')['link']['world_number']
    paths.append(root/('stage435/world'+str(number)+'-before-constructor-private.json'))
    return paths

def storage_status(p,free):
    s=p['storage_forecast'];required={'/tmp':s['tmp_required_bytes'],'/workspace':s['workspace_required_bytes']}
    return {v:dict(free_bytes=free[v],required_bytes=required[v],shortage_bytes=max(0,required[v]-free[v])) for v in required}

def check_storage(p):
    free={v:shutil.disk_usage(v).free for v in ('/tmp','/workspace')};status=storage_status(p,free)
    for v,s in status.items():require(s['shortage_bytes']==0,'473_STORAGE_PREFLIGHT:'+v+':'+json.dumps(s))
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
    if cpu>=300:reasons.append('whole_CPU300')
    if wall>=600:reasons.append('whole_wall600')
    if datetime.datetime.now(datetime.timezone.utc)>=meter.deadline():reasons.append('deadline')
    return None if not reasons else '473_FINAL_CLOSURE_RESOURCE_STOP:'+','.join(reasons)

def prepare(root):
    root=Path(root);d=root/('stage'+REVISION)
    require(not d.exists() and not d.is_symlink() and not RAW.exists() ,'473_ONCE_FRESH_REVISION')
    c=contract();old=read(root/'stage472/plan.json');ledger_path=root/'project-effective-budget-v476.json';v=read(ledger_path)
    require(v['stage472_status']=='CLOSED' and (v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(26175,84000,0),'473_LEDGER_UNCHANGED')
    require(read(root/'research-deadline-current.json')['deadline_utc']==c['deadline_utc']=='2026-10-20T10:01:55Z','473_DEADLINE')
    state,memory,ledger,rng,blob,expected=root_inputs(root)
    projection=Path(old['projection_path']);correction=root/'stage441/authorization-correction-private.json'
    require(sha(projection)==c['projection_sha256']=='85ac335bf32d11da78e2d76a213b6096a0d357bc4f5d334196695343717d213f','473_FROZEN_PROJECTION')
    require(sha(correction)==c['authorization_extension_sha256']==v['authorization_correction_sha256'],'473_AUTHORIZATION_EXTENSION')
    files={Path(f) for f in old['semantic_sources'] if Path(f).is_absolute()}
    files.update(source_closure([G/'retry'/n for n in ['compare473.py','meter473.py','law473.py','static473.py','test_compare473.py','analyze473.py','retain473.py']]))
    files.update(qualification_source_paths(root));files.update(root_source_paths(root));files.update([Path(old['fixed_plan']),Path(old['pace_path'])])
    files.update(G/'retry'/n for n in ['meter473.py','compare473.py','law473.py','static473.py','test_compare473.py','analyze473.py','retain473.py','design471_result.md','design471_next.json'])
    files.update([projection,correction,ledger_path,root/'stage472-plan-durable-private.json',G/'retry/transfer472_retention.json',root/'stage472-retention-manifest-private.json',G/'retry/compare470_retention.json',root/'stage469-revision1-retention-manifest-private.json'])
    for f,h in old['semantic_sources'].items():
        if Path(f).is_absolute():require(sha(f)==h,'473_OLD_SEMANTIC_SOURCE_CHANGED:'+f)
    from retry.pilot436_run import fingerprint_line
    fixed_geometry=read(old['fixed_plan'])
    require(old['semantic_sources']['geometry_line_json']==fingerprint_line(fixed_geometry['line']) and old['semantic_sources']['geometry_total_length_json']==fingerprint_line(sum(fixed_geometry['free_profile']['ds'])),'473_LOGICAL_GEOMETRY_DIGESTS')
    semantic=dict(old['semantic_sources']);semantic.update({str(f):sha(f) for f in files if str(f).startswith(str(G)) and f.suffix=='.py'})
    p=dict(stage=473,revision=REVISION,execution=c,execution_allowed=False,static_required_before_physics=True,
           registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=c['deadline_utc'],
           caps=c['hard'],scope=dict(ticks=3458,worlds=43),budget_fixture=cost_fixture(),world_audit=world_audit(),
           fixed_plan=old['fixed_plan'],pace_path=old['pace_path'],projection_path=str(projection),projection_sha256=sha(projection),
           authorization_extension_path=str(correction),authorization_extension_sha256=sha(correction),
           sources={str(f):sha(f) for f in sorted(files)},semantic_sources=semantic,
           protected=old['protected'],original408_preserve=old['original408_preserve'],
           contract_sha256=sha(G/'retry/compare473.py'),contract_json_sha256=None,
           ledger_path=str(ledger_path),ledger_sha256=sha(ledger_path),storage_free_stop_bytes=512*MIB,
           raw_directory=str(RAW),archive_created=False,archive_bytes=0,workspace_new_raw_archive_copy=False,
           runtime_environment=runtime_environment(),
           forced_first_fullgas=False,
           profile_inputs=dict(fixed_plan_sha256=sha(old['fixed_plan']),pace_sha256=sha(old['pace_path']),projection_sha256=sha(projection)),
           reproducibility_conditions='Existing designated cloud; frozen source/input hashes and RNG receipt; unchanged plain writer; pre23 fixed FIRST_LAP root after observed launch; two natural own-reference whole laws once; no forced first pulse; original raw only remains/tmp; no archive/transformation/workspace raw copy',
           authorization=c['authorization'],new_seed_learning_HOLDOUT_SEALED_reserve_paid=0)
    require(len(p['protected'])+len(p['original408_preserve'])==18,'473_PROTECTED18')
    p['storage_forecast']=storage_forecast(c,semantic,old['semantic_sources']);p['storage_start_free_bytes']=check_storage(p);p['storage_preflight']=storage_status(p,p['storage_start_free_bytes'])
    material=root/('stage'+REVISION+'-input-material-private.json')
    require(not material.exists(),'473_FRESH_INPUT_MATERIAL')
    save_receipt(material,dict(state=state,memory=memory,ledger=asdict(ledger),RNG_blob=blob,RNG_source=rng,
                              expected=expected,fixed=read(old['fixed_plan']),pace=read(old['pace_path']),
                              projected_nodes=read(projection)['projected_nodes']))
    p['input_material_path']=str(material);p['input_material_sha256']=sha(material);p['sources'][str(material)]=sha(material)
    require(len(json.dumps(p,indent=2).encode())<=2*MIB,'473_PLAN_BYTES_ALLOWANCE')
    require(material.stat().st_size+2*MIB<=64*MIB,'473_WORKSPACE_REPRO_METADATA_ALLOWANCE')
    for group in ('protected','original408_preserve'):
        for f,h in p[group].items():require(sha(f)==h,'473_PROTECTED:'+f)
    RAW.mkdir(mode=0o700);d.symlink_to(RAW,target_is_directory=True);save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n')
    save(root/('stage'+REVISION+'-plan-durable-private.json'),p)
    save(d/'progress-private.json',dict(stage=473,revision=REVISION,phase='PLAN_FROZEN',model_ticks=0,model_worlds=0,actual_actions=0,resets=0))
    print(json.dumps(dict(stage=473,revision=REVISION,plan_sha256=sha(d/'plan.json'),cost=p['budget_fixture'],world_audit=p['world_audit'],storage_forecast=p['storage_forecast'],storage_preflight=p['storage_preflight'])))

def run(root):
    root=Path(root);d=root/('stage'+REVISION);p=read(d/'plan.json');static=read(d/p.get('static_result_name','static-result.json'))
    require(not(d/'opening.json').exists() and static['passed'],'473_ONCE_STATIC')
    require(sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()==static['plan_sha256'],'473_PLAN_STATIC_BINDING')
    require(p['execution']==contract() and p['caps']==contract()['hard'] and p['scope']==dict(ticks=3458,worlds=43) and p['budget_fixture']==cost_fixture() and p['world_audit']==world_audit(),'473_SINGLE_CONTRACT_SCOPE')
    for group in ('sources','protected','original408_preserve'):
        for f,h in p[group].items():require(sha(f)==h,'473_SOURCE_CHANGED:'+f)
    check_storage(p);state,memory,ledger,rng,blob,expected=root_inputs(root);py,npr=pickle.loads(blob);random.setstate(py);np.random.set_state(npr)
    fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(p['pace_path'])['frozen268']);meter=create_meter(d)
    cohorts=[];cohort_result=None;whole_result=None;status='STARTED';error=None;stage='fresh_source';preflight_counts={}
    save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),plan_sha256=sha(d/'plan.json'),static_sha256=sha(d/p.get('static_result_name','static-result.json'))))
    def timeout(*args):raise ResourceStop('473_whole_CPU300_wall600_or_deadline')
    handlers={s:signal.signal(s,timeout) for s in (signal.SIGPROF,signal.SIGALRM)};meter.timers()
    try:
        with meter.model('473_pre23_source_root_and_two_once_whole_parents'):
            meter.checkpoint('FRESH_SOURCE_STARTED')
            fork=read(root/'stage423/actual_C0/fork-private.json');oldstate=from_actual_full(fork);oldmem=fork['controller']['before'];row=json.loads((root/'stage423/actual_C0/trace-private.jsonl').read_text().splitlines()[118]);oldledger=GoalLedger(row['progress_before'],row['goal_before'],H-(row['deadline_before']-118),round(oldstate['physical']['actual_time']*50))
            qualify(root,meter,fixed,pace,oldstate,oldmem,oldledger);qualify_pending(root,meter,fixed,pace);meter.qualification_passed=True;qualify_parent(root,meter,fixed,pace)
            require(meter.b['ticks']<=1242 and meter.b['worlds']==35,'473_SOURCE35')
            preflight_counts['source']=dict(ticks=meter.b['ticks'],worlds=meter.b['worlds'])
            save(d/'preflight-private.json',dict(passed=True,ticks=meter.b['ticks'],worlds=meter.b['worlds'],actual_actions=0,resets=0));meter.checkpoint('OLD_SOURCE_PASSED')
            stage='fresh_root_H13';cohort_result=root_h13(root,meter,fixed,pace,state,memory,ledger,expected);cohorts=cohort_result['cohorts']
            require(meter.b['ticks']<=1458 and meter.b['worlds']<=41,'473_ROOT41_SCOPE')
            preflight_counts['root']=dict(ticks=meter.b['ticks'],worlds=meter.b['worlds'])
            if cohort_result['passed']:
                require(meter.b['worlds']==41,'473_ROOT_EXACT41')
                meter.checkpoint('ROOT_H13_PASSED');stage='two_once_whole_parents'
                whole_result=whole_parents(root,meter,fixed,pace,state,memory,ledger,expected)
                require(meter.b['ticks']<=3458 and meter.b['worlds']<=43,'473_WHOLE_SCOPE')
                require(meter.b['worlds']==43 and whole_result['model_worlds']==2 and len(whole_result['policies'])==2,'473_BOTH_FIXED_WHOLE_ARMS_ATTEMPTED')
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
        for f,h in p[group].items():require(sha(f)==h,'473_FINAL_PROTECTED:'+f)
    require(sha(p['ledger_path'])==p['ledger_sha256'],'473_GLOBAL_LEDGER_CHANGED')
    final_error=final_limit_error(meter)
    if final_error:status='STOP';error=final_error if error is None else error+'; '+final_error
    meter.persist()
    result=dict(stage=473,revision=REVISION,status=status,error=error,last_stage=stage,cohorts=cohorts,cohort_result=cohort_result,root_qualification=cohort_result,preflight_counts=preflight_counts,whole_result=whole_result,whole_arms=whole_result.get('policies',[]) if whole_result else [],budget=read(d/'budget.json'),plan_sha256=sha(d/'plan.json'),new_actual_actions=0,new_resets=0,new_seed_learning_HOLDOUT_SEALED_reserve_paid=0,no_followup=True)
    save(d/'result.json',result);meter.checkpoint('CLOSED',status=status,error=error)
    final_error=final_limit_error(meter)
    if final_error and final_error not in (error or ''):
        status='STOP';error=final_error if error is None else error+'; '+final_error
        meter.persist();result.update(status=status,error=error,budget=read(d/'budget.json'));save(d/'result.json',result);meter.checkpoint('CLOSED_RESOURCE_STOP',status=status,error=error)
    print(json.dumps(dict(stage=473,revision=REVISION,status=status,error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds'],actual=0,resets=0)),flush=True)

if __name__=='__main__':prepare(Path(sys.argv[2])) if sys.argv[1]=='prepare' else run(Path(sys.argv[2]))
