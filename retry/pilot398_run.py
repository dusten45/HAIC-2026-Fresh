"""One frozen full-lap GT candidate on two known TRAIN, after397 qualification."""
import datetime,fcntl,hashlib,json,os,random,resource,signal,sys,time,traceback
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.loss389_replay import sensor
from retry.probe390_run import control_code
from retry.fork394_run import ForkTrace,complete_state
from retry.executor397 import CoherentExecutor,ExecutorDomainError,canonical_projection
from retry.scalar392_audit import project as diagnostic_project
G=Path(__file__).resolve().parent.parent

class PilotSafetyStop(RuntimeError):pass

def locked(d,fun):
    with (d/'budget.lock').open('a') as h:
        fcntl.flock(h,fcntl.LOCK_EX);b=read(d/'budget.json');z=fun(b);save(d/'budget.json',b);return z

def prepare(root):
    d=root/'stage398';assert not d.exists();gate=read(root/'stage397/result.json');assert gate['passed'] and gate['technical_error'] is None
    p397=read(root/'stage397/plan.json')
    for f,h in p397['sources'].items():assert sha(f)==h,f
    b=read(root/'project-effective-budget-v417.json');assert b['research_remaining']==32346 and b['final_reserved_actions']==84000 and b['final_reserve_used']==0
    d.mkdir(mode=0o700);p394=read(root/'stage394/plan.json');p390=read(root/'stage390/plan.json')
    sources=[Path(__file__),G/'retry/executor397.py',G/'retry/qualify397.py',G/'retry/probe390_run.py',G/'retry/scalar392_audit.py',G/'retry/loss389_replay.py',G/'retry/loss389_analyze.py',G/'retry/fork394_run.py',G/'retry/diagnose.py',G/'retry/source_vehicle_transition.py',G/'retry/pedal331_run.py',G/'env_wrapper.py',G/'damage.py',root/'stage397/plan.json',root/'stage397/result.json',root/'project-effective-budget-v417.json',root/'research-deadline-current.json',root/'stage390/plan.json',root/'stage394/plan.json']+list((G/'core').rglob('*.py'))
    for key in ['O0','N1']:sources += [Path(p394['fixed_plans'][key]),root/('stage394/'+key+'-O')/'initial-private.json',root/('stage390/A-'+key)/'trace-private.json',Path(p390['A_references'][key])/'result.json']
    p=dict(stage=398,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',cases={k:p394['cases'][k] for k in ['O0','N1']},fixed_plans=p394['fixed_plans'],initial_pixels=p394['initial_pixels'],controller_AST_sha256=p394['controller_AST_sha256'],observer_rng_seed=394,arms='C397onefreshcandidateeachO0/N1; cachedO390baselines only, no freshO needed',case_order=['O0','N1'],native_cap=1600,per_case_cap=800,reset_cap=2,CPU_cap_s=180,wall_cap_s=300,parallel_cap=2,per_worker_CPU_soft_s=89,per_worker_CPU_hard_s=90,cost_basis='395wholeworker51.4CPU/808wrapper;1600linear~101.8CPU,180capallowsfullrawtiretracing/qualificationmargin;wall300vs395receiptspan29.6s/808. No paidresources.',actor_cap=0,model_integration_cap=0,learning_cap=0,reserve_use=0,research_before=32346,research_after_worst_case=30746,candidate='Unchanged397source/gain1.5/path/profilepace1.5/clamps/pedalmap; explicitLAUNCH/FIRST_LAP/FINISH_CONFIRM/DONE; ownactualstateGTsteeringandcurrentfinishmetadata. No futureobservations,casepatches,retuning orrestarts.',baselines=dict(O0=dict(completed=True,lap_ms=19700,damage=0.),N1=dict(completed=False,episode_s=20.72,damage=0.,reason='off_track')),research_gate='Bothofficialcomplete,damage0,maxactualnearestpatherror<=3m,no roadcontactloss/meaningfulreverse/collision,andO0lap<19.70. Candidate-specificresearchgate,not296/SEALED/generalizationclaim.',finish='Onlyrawofficialfinish_time_s indicatescompletion. Qualification/centercandidatealone insufficient; sourcewaitsforwardedge. Lapfinish_time_s -recordedresetstart_t,notlastactiontime orarcL. Terminalpostcanhavert<4.',stops='800caporCPU/wall ->CENSOREDnotDNF. Nativeendedwithoutfinish ->actualDNF;truncatedwithoutfinish ->envcensor. Domain/safetycurrentcasestops,no fallback/retuning/rerun;otherindependentcasecontinues. Sharedtechnical/source/resource/deadlinefail stopsallnewactions. All outcomes preserved.',safety='Pre/postnearestpathdist>3m,damageincrease,newcollision/touchingobstaclepair,wheelroadlossorrawtiregrass,meaningfulbody/pathsigma<-.1 ->caseSafetyStop. Negative sigma inFIRST_LAPisstrictdomainstopwithoutmask. Rawclip aloneobservednotnewgate. Officialcompletedwithlaststepsafetyviolation recordedboth butfailsresearchgate.',record='Eachactionpre/postactualsensors,nominal+executedcontrols,memory,phase/reference/arc/patherror,rawtire16or4*rtsamples. Initialfullstateequal394O;firstlaunchcommand/postexact390. No actor/source-modelclones/learning.',sources={str(f):sha(f) for f in sources},protected={str(f):sha(f) for f in [root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json']},forbidden='SEALED/372details/newDEV/HOLDOUT/paidresource/reserveuse/newgainorprofilefits/conditionreselections')
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');(d/'plan.sha256').chmod(0o600);save(d/'budget.json',dict(actions=0,resets=0,case_actions={},started_epoch=None,active_cases=[],finished_cases=[],CPU_by_case={}));(d/'budget.lock').touch(mode=0o600);print(json.dumps(dict(registered=True,plan_sha256=sha(d/'plan.json'),native_cap=1600,CPU_cap=180,wall_cap=300)),flush=True)

def verify(root,full=False):
    d=root/'stage398';p=read(d/'plan.json');assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip();assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(p['deadline_utc'])
    if (d/'SharedStop.json').exists():raise RuntimeError('Sharedtechnicalstop')
    if full:
        for f,h in {**p['sources'],**p['protected']}.items():assert sha(f)==h,f
    return p

def guard(root,key):
    d=root/'stage398';verify(root)
    def f(b):
        if b['started_epoch'] is None:b['started_epoch']=time.time()
        b['CPU_by_case'][key]=time.process_time();assert sum(b['CPU_by_case'].values())<180,'CPU180cap';assert time.time()-b['started_epoch']<300,'wall300cap'
    locked(d,f)

def charge(root,key,kind):
    d=root/'stage398';guard(root,key)
    def f(b):
        if kind=='reset':assert b['resets']<2;b['resets']+=1
        else:assert b['actions']<1600 and b['case_actions'].get(key,0)<800;b['actions']+=1;b['case_actions'][key]=b['case_actions'].get(key,0)+1
    locked(d,f)

def finish_dict(raw):return dict(raw.finish_line_tracker.__dict__)

def safety_flags(state,q,damage,initial_damage,collision=False,new_pairs=False,grass=False):
    angle=state['angle'];forward=float(np.asarray(state['vel'])@np.array([-np.sin(angle),np.cos(angle)]));why=[]
    if q['path_error_m']>3:why.append('path_error_over3m')
    if not all(n>0 for n in state['road_contacts']) or grass:why.append('wheel_road_loss')
    if damage>initial_damage:why.append('damage_increase')
    if collision or new_pairs:why.append('collision_or_new_obstacle_contact')
    if q.get('sigma') is not None and q['sigma']<-.1 or forward<-.1:why.append('meaningful_reverse')
    return why

def run_case(root,key):
    from retry.diagnose import make_env
    d=root/'stage398';p=verify(root,True);folder=d/key;assert key in p['cases'] and not folder.exists();folder.mkdir(mode=0o700);save(folder/'opening.json',dict(pid=os.getpid(),epoch=time.time()))
    def active(b):assert key not in b['active_cases']+b['finished_cases'] and len(b['active_cases'])<2;b['active_cases'].append(key)
    locked(d,active);resource.setrlimit(resource.RLIMIT_CPU,(89,90))
    def timeout(signum,frame):raise TimeoutError('398workerCPUcap')
    priorprof=signal.signal(signal.SIGPROF,timeout);priorcpu=signal.signal(signal.SIGXCPU,timeout);signal.setitimer(signal.ITIMER_PROF,max(.001,88-time.process_time()))
    env=observer=None;rows=[];steps=ticks=reset=0;status='STARTED';error=None;completed=ended=truncated=False;info={};start_t=None;damage=0.;phase_events=[];maxerr=0.;initial_exact=False;first_launch_exact=False;safety=[];start,cpu=time.perf_counter(),time.process_time();random.seed(394);np.random.seed(394)
    try:
        fixed=read(Path(p['fixed_plans'][key]));policy=CoherentExecutor(fixed,'lap');line=np.asarray(fixed['line']);prof=fixed['free_profile'];ds=np.asarray(prof['ds']);sarc=np.r_[0,np.cumsum(ds)];scope=dict(line=line,vprof=np.asarray(prof['speed']),ds=ds,curvature=np.asarray(prof['curvature']),sarc=sarc,L=sarc[-1],model=fixed['model'],index=0,laststeer=0.,pace=1.5);code,astsha=control_code(G/'retry/pace265_run.py');assert astsha==p['controller_AST_sha256'];env=make_env();charge(root,key,'reset');case=p['cases'][key];obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});raw=env.unwrapped;start_t=float(raw.t);reset=round(raw.t*50);scope['env']=env
        assert hashlib.sha256(obs.tobytes()).hexdigest()==p['initial_pixels'][key] and hashlib.sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest()==case['road_geometry_sha256']
        initial=complete_state(env,obs,dict(index=0,laststeer=0.));assert initial==read(root/('stage394/'+key+'-O')/'initial-private.json');save(folder/'initial-private.json',initial);initial_exact=True;initial_damage=float(env.damage.damage);initial_pairs=set(tuple(x) for x in initial['physical']['touching_obstacle_contacts']);old_first=read(root/('stage390/A-'+key)/'trace-private.json')[0];observer=ForkTrace()
        journal=(folder/'trace-private.jsonl').open('x');(folder/'trace-private.jsonl').chmod(0o600)
        try:
            for step in range(1,801):
                guard(root,key);pre=sensor(env);memory_before=dict(index=int(scope['index']),laststeer=float(scope['laststeer']));exec(code,dict(np=np),scope);nominal=scope['action'];memory_after=dict(index=int(scope['index']),laststeer=float(scope['laststeer']));phase_before=policy.phase;command,ref=policy.act(pre,nominal,finish_dict(raw),scope['arc']);assert command is not None and command[0]==nominal[0]
                if policy.phase!=phase_before:phase_events.append(dict(step=step,phase=policy.phase,time=pre['time']))
                q=ref['projection'];maxerr=max(maxerr,q['path_error_m']);why=safety_flags(pre,q,float(env.damage.damage),initial_damage)
                if why:safety=why;raise PilotSafetyStop(','.join(why))
                if step==1:assert command.tolist()==old_first['control']['action']
                observer.rows=[];observer.enable();charge(root,key,'action');steps+=1;before=raw.t;obs,_,ended,truncated,info=env.step(command);rt=round((raw.t-before)*50);ticks+=rt;observer.disable();post=sensor(env);damage=float(env.damage.damage);assert len(observer.rows)==4*rt
                post_domain_error=None
                try:qp=canonical_projection(line,post['pos'],post['vel'],policy.phase)
                except ExecutorDomainError as e:
                    post_domain_error=str(e);dq=diagnostic_project(line,post['pos'],post['vel']);j=dq['index'];foot=line[j]+dq['u']*(line[(j+1)%len(line)]-line[j]);qp=dict(path_error_m=float(np.linalg.norm(np.asarray(post['pos'])-foot)),sigma=None,measurement_only_unqualified=post_domain_error)
                maxerr=max(maxerr,qp['path_error_m']);newpairs=set(tuple(x) for x in raw_capture_pairs(env))-initial_pairs;why=safety_flags(post,qp,damage,initial_damage,bool(info['collision']),bool(newpairs),any(s['grass'] for s in observer.rows));completed=raw.finish_time_s is not None
                row=dict(step=step,pre=pre,post=post,nominal=nominal.tolist(),command=command.tolist(),memory_before=memory_before,memory_after=memory_after,reference=ref,post_projection=qp,raw_ticks=rt,raw_tire_samples=observer.rows.copy(),collision=bool(info['collision']),damage=damage,completed=completed,terminated=bool(ended),truncated=bool(truncated),retire_reason=info.get('retire_reason'));rows.append(row);journal.write(json.dumps(row,allow_nan=False)+'\n');journal.flush()
                if step==1:assert post==old_first['post'];first_launch_exact=True
                if completed:
                    policy.mark_done(finish_dict(raw),raw.t);phase_events.append(dict(step=step,phase='DONE',time=raw.t));safety=why;status='COMPLETED' if not why else 'COMPLETED_WITH_SAFETY_VIOLATION';break
                if ended:status='ACTUAL_DNF';safety=why;break
                if truncated:status='ENV_CENSORED';safety=why;break
                if why:safety=why;raise PilotSafetyStop(','.join(why))
                if post_domain_error:raise ExecutorDomainError('Poststate_'+post_domain_error)
            else:status='NATIVE_CAP_CENSORED'
        finally:journal.close()
        save(folder/'final-full-private.json',complete_state(env,obs,dict(index=int(scope['index']),laststeer=float(scope['laststeer']))))
    except BaseException as e:
        error=type(e).__name__+': '+str(e)
        if isinstance(e,ExecutorDomainError):status='DOMAIN_STOP_CENSORED'
        elif isinstance(e,PilotSafetyStop):status='SAFETY_STOP_CENSORED'
        elif isinstance(e,TimeoutError) or 'CPU' in error or 'wall300cap' in error:status='RESOURCE_CENSORED'
        else:
            status='TECHNICAL_STOP_CENSORED'
            if not(d/'SharedStop.json').exists():save(d/'SharedStop.json',dict(case=key,error=error))
        save(folder/'stop-private.json',dict(status=status,error=error,traceback=traceback.format_exc()))
    finally:
        if observer:observer.disable()
        if env:env.close()
        signal.setitimer(signal.ITIMER_PROF,0);signal.signal(signal.SIGPROF,priorprof);signal.signal(signal.SIGXCPU,priorcpu)
        def finished(b):b['active_cases'].remove(key);b['finished_cases'].append(key);b['CPU_by_case'][key]=time.process_time()
        locked(d,finished)
    lap=round((raw.finish_time_s-start_t)*1000) if completed else None
    result=dict(case=key,status=status,completed=completed,actual_DNF=bool(ended and not completed),censored=bool(not completed and not ended),lap_ms=lap,retire_reason=info.get('retire_reason'),stop_reason=error,technical_error=error if status=='TECHNICAL_STOP_CENSORED' else None,safety_reasons=safety,native=steps,raw_ticks=ticks,reset_ticks=reset,damage=damage,max_path_error_m=maxerr,phase_events=phase_events,initial_exact=initial_exact,first_launch_exact=first_launch_exact,unconfirmed_charged_native=steps-len(rows),runner_CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,wholeworker_CPU_s=time.process_time(),new_actor=0,new_model_integration=0,new_learning=0)
    save(folder/'result.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)

def raw_capture_pairs(env):
    from retry.source_vehicle_transition import obstacle_contact_pair
    raw=env.unwrapped;return [pair for c in raw.world.contacts if c.touching and (pair:=obstacle_contact_pair(c,raw.car,raw.obstacles)) is not None]

if __name__=='__main__':
    root=Path(sys.argv[1]).resolve()
    if sys.argv[2]=='prepare':prepare(root)
    else:run_case(root,sys.argv[2])
