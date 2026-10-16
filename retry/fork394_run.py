"""Five frozen GT prefix forks, one native action each; no actor/model/learning."""
import datetime,fcntl,hashlib,inspect,json,math,os,random,resource,signal,sys,time,traceback
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.loss389_replay import sensor
from retry.probe390_run import control_code
from retry.scalar392_audit import project,pedals
from retry.coherent393_audit import runtime_nodes,rf
G=Path(__file__).resolve().parent.parent

class SafetyStop(RuntimeError):pass

def lock_budget(d,change):
    with (d/'budget.lock').open('a') as h:
        fcntl.flock(h,fcntl.LOCK_EX);b=read(d/'budget.json');result=change(b);save(d/'budget.json',b);return result

def prepare(root):
    d=root/'stage394';assert not d.exists();d.mkdir(mode=0o700);p390=read(root/'stage390/plan.json');v=read(root/'project-effective-budget-v413.json');assert v['research_remaining']==34139 and v['final_reserved_actions']==84000
    data=read(root/'stage393/row-evaluations-private.json');jobs=dict(N1=dict(target=161,arms=['O','C']),O0=dict(target=221,arms=['O','H','C']));expected={}
    for key,job in jobs.items():
        z=next(x for x in data if x['case']==key and x['step']==job['target']);assert z['withheld'] is None and z['sigma']>=0
        tr=read(root/('stage390/A-'+key)/'trace-private.json')[job['target']-1];expected[key]={arm:np.asarray([tr['control']['action'][0],z[arm]['gas'],z[arm]['brake']],np.float32).tolist() for arm in job['arms']}
    sources=[Path(__file__),G/'retry/probe390_run.py',G/'retry/loss389_replay.py',G/'retry/loss389_analyze.py',G/'retry/scalar392_audit.py',G/'retry/coherent393_audit.py',G/'retry/pace265_run.py',G/'retry/pedal331_run.py',G/'retry/source_vehicle_transition.py',G/'retry/diagnose.py',G/'env_wrapper.py',G/'damage.py',root/'stage393/row-evaluations-private.json',root/'stage393/plan.json',root/'stage390/plan.json',root/'project-effective-budget-v413.json',root/'research-deadline-current.json']+list((G/'core').rglob('*.py'))
    for key in jobs:sources += [root/('stage390/A-'+key)/'trace-private.json',Path(p390['A_plans'][key])]
    p=dict(stage=394,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',jobs=jobs,expected_float32_commands=expected,cases={k:p390['cases'][k] for k in jobs},initial_pixels={k:p390['A_initial_pixels'][k] for k in jobs},fixed_plans={k:p390['A_plans'][k] for k in jobs},controller_AST_sha256=p390['controller_AST_sha256'],native_cap=985,reset_cap=5,CPU_cap_s=120,wall_cap_s=300,max_parallel=2,per_worker_CPU_soft_s=59,per_worker_CPU_hard_s=60,actor_cap=0,model_integration_cap=0,learning_cap=0,observer_rng_seed=394,research_before=34139,research_after_worst_case=33154,reserve=84000,reserve_used=0,prefix='Actualreset thenoriginal265 ASTlawatpace1.5; allpre/post sensors,originalfloat32command andoutcomes equal390forprefix; originalarmforkalsoexact390. Independentworlds,notrestoredclones. Oneforkactiononly,originalsteeringandGTcontrollerpersistentindex/laststeer maintained.',fork_qualification='Captureallavailablephysicalsource includingfullbodies/wheels/joints/roads/obstacles/contacts/worldflags anddamage; alsofinishtracker,wrapperelapsedcounter,fullaccessibleRNG,observationhash andcontrollerbefore/aftercalculationmemory. Initialandforkcapture exactOarm percase. Solverinternalwarmstartsnotdirectlyexported; no fullsolverstateclaim.',control_qualification='RecomputeH/C onlyfromactualprestate and frozenoriginalprofile/branch andsameactualuniqueinteriorprojection. Match393float32command exactly; nozero_r,reverse,seamfallback. Holdsameoriginalsteering for4rawticks; nofuturecommandsfeedback.',measurement='Actual4rawtick tire-local ratio,gripclip,grass,laterslip,rawlong/latforces,forward/slipspeed,wheelgas/brake/omega/joint;pre/posthullvel/yaw/position,wheelcontacts/damage/obstaclecontacts. No observermutation.',gates='N1 CminusO prebodyaxisforwardvelocity>=.1m/s; abs yawratedelta<=.05rad/s;no newcollision/damage/roadcontactloss. Local0.08sresponseonly. O0 H/C compareforward/lateral/yaw,slip,rawgas; accelerationnot safety, tiesoractuatorlimitedeffects inconclusive. Newcollision/damage/roadcontactloss orabs yawdifference>.05 ->globalSafetyStop preventsremainingactions/arms. No lap/296promotion.',stops='Firsttechnical/prefix/domain/sourcefailure stops currentarm anddependentremainingarms ofthatcase,otherindependentcase cancontinue ifnotglobalresource/sourceSafetyStop. Safety/resource/deadline marker stopsall furthernativeactions. No retry/replacement/sweep. Chargebeforeeachwrapper/reset; retainunconfirmedcallsifexception.',CPU_accounting='Twoindependentcaseworkers,OSprocessCPUsoft59/hard60eachplus SIGPROF58sabsoluteprocessbudget;sharedguardCPU120 andwall300. RecordwholeworkerCPU andepisodeCPU separately. Preparation/reportnotfullytimed.',source_hashes={str(f):sha(f) for f in sources},protected_hashes={str(f):sha(f) for f in [root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json']},forbidden='Newlap/gainsweep/actor/modelintegration/learning/SEALED/372details/newDEV/HOLDOUT/paidresource/reserveuse')
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');(d/'plan.sha256').chmod(0o600);save(d/'budget.json',dict(actions=0,resets=0,arm_actions={},started_epoch=None,active_cases=[],finished_cases=[],CPU_by_case={}));(d/'budget.lock').touch(mode=0o600);print(json.dumps(dict(registered=True,plan_sha256=sha(d/'plan.json'),native_cap=985,resets=5,commands=expected)),flush=True)

def verify(root,full=False):
    d=root/'stage394';p=read(d/'plan.json');assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
    assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(p['deadline_utc'])
    if full:
        for f,h in {**p['source_hashes'],**p['protected_hashes']}.items():assert sha(f)==h,f
    return p

def guard(root,key):
    d=root/'stage394';verify(root)
    if (d/'SafetyStop.json').exists():raise SafetyStop('RegisteredglobalSafetyStop')
    def update(b):
        if b['started_epoch'] is None:b['started_epoch']=time.time()
        assert time.time()-b['started_epoch']<300,'Globalwall300s';b['CPU_by_case'][key]=time.process_time();assert sum(b['CPU_by_case'].values())<120,'GlobalCPU120s'
    lock_budget(d,update)

def charge(root,key,arm,field):
    d=root/'stage394';guard(root,key)
    def update(b):
        if field=='resets':assert b['resets']<5;b['resets']+=1
        else:
            label=key+'-'+arm;cap=161 if key=='N1' else 221;assert b['actions']<985 and b['arm_actions'].get(label,0)<cap;b['actions']+=1;b['arm_actions'][label]=b['arm_actions'].get(label,0)+1
    lock_budget(d,update)

class ForkTrace:
    def __init__(self):
        from core.vendor.car_dynamics import Car
        self.Car=Car;lines,first=inspect.getsourcelines(Car.step);self.line=first+next(i for i,l in enumerate(lines) if 'if abs(force) > 2.0 * friction_limit:' in l);self.rows=[];self.previous=None
    def trace(self,frame,event,arg):
        if frame.f_code is not self.Car.step.__code__:return None
        if event=='line' and frame.f_lineno==self.line:
            q=frame.f_locals;w=q['w'];idx=next(i for i,x in enumerate(q['self'].wheels) if x==w);limit=float(q['friction_limit']);ratio=float(q['force'])/limit
            self.rows.append(dict(raw_tick=len(self.rows)//4+1,wheel=idx,gas=float(w.gas),brake=float(w.brake),omega=float(w.omega),joint_angle=float(w.joint.angle),force_ratio=ratio,clipped=ratio>1,grass=bool(q['grass']),lateral_slip_m_s=float(q['vs']),forward_speed_m_s=float(q['vf']),longitudinal_slip_m_s=float(q['vr']-q['vf']),raw_long_N=float(q['f_force']),raw_lat_N=float(q['p_force'])))
        return self.trace
    def enable(self):self.previous=sys.gettrace();sys.settrace(self.trace)
    def disable(self):sys.settrace(self.previous)

def complete_state(env,obs,controller):
    from retry.source_vehicle_transition import capture
    from retry.pedal331_run import plain,rng
    raw=env.unwrapped;tracker=raw.finish_line_tracker
    return plain(dict(physical=capture(env),RNG=rng(env),observation_sha256=hashlib.sha256(obs.tobytes()).hexdigest(),controller=controller,wrapper=dict(elapsed_raw_steps=env.env._elapsed_steps,finish_qualified_time_s=raw.finish_qualified_time_s,finish_time_s=raw.finish_time_s,finish_tracker=dict(tracker.__dict__) if tracker else None)))

def changed_command(scope,pre,fixed,arm):
    original=scope['action'].copy()
    if arm=='O':return original
    line=np.array(fixed['line']);q=project(line,pre['pos'],pre['vel']);assert q['valid'] and q['sigma']>=0 and scope['index']<len(line)
    if arm=='H':r=scope['desired'];f=scope['feed']
    else:
        assert arm=='C';nodes=runtime_nodes(fixed,scope['index']);r,f=rf(nodes,np.array(fixed['free_profile']['ds']),q['index'],q['u'])
    assert r>0 and all(math.isfinite(z) for z in [r,f,q['sigma']]);z=pedals(f*(q['sigma']/r)+1.5*(r-pre['speed']),pre['speed'],fixed['model']);original[1:]=[z['gas'],z['brake']];return original

def episode(root,key,arm,p):
    from retry.diagnose import make_env
    d=root/'stage394';f=d/(key+'-'+arm);assert not f.exists();f.mkdir(mode=0o700);save(f/'opening.json',dict(epoch=time.time()));target=p['jobs'][key]['target'];old_damage=read(Path(read(root/'stage390/plan.json')['A_references'][key])/'trajectory-private.json');old=read(root/('stage390/A-'+key)/'trace-private.json');fixed=read(Path(p['fixed_plans'][key]));line=np.array(fixed['line']);prof=fixed['free_profile'];ds=np.array(prof['ds']);sarc=np.r_[0,np.cumsum(ds)];code,digest=control_code(G/'retry/pace265_run.py');assert digest==p['controller_AST_sha256']
    scope=dict(line=line,vprof=np.asarray(prof['speed']),ds=ds,curvature=np.asarray(prof['curvature']),sarc=sarc,L=sarc[-1],model=fixed['model'],index=0,laststeer=0.,pace=1.5)
    env=observer=None;error=None;rows=[];fork=None;charged=ticks=reset=0;matched=0;initial_exact=fork_exact=False;status='STARTED';start,cpu=time.perf_counter(),time.process_time();random.seed(394);np.random.seed(394)
    try:
        verify(root,True);guard(root,key);env=make_env();charge(root,key,arm,'resets');case=p['cases'][key];obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});raw=env.unwrapped;reset=round(raw.t*50);scope['env']=env
        assert hashlib.sha256(obs.tobytes()).hexdigest()==p['initial_pixels'][key] and hashlib.sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest()==case['road_geometry_sha256']
        initial=complete_state(env,obs,dict(index=0,laststeer=0.));save(f/'initial-private.json',initial)
        if arm!='O':assert initial==read(d/(key+'-O')/'initial-private.json')
        initial_exact=True
        for step in range(1,target+1):
            guard(root,key);pre=sensor(env);assert pre==old[step-1]['pre'],('prefixprestate',key,arm,step);memory_before=dict(index=int(scope['index']),laststeer=float(scope['laststeer']));exec(code,dict(np=np),scope);original=scope['action'];memory_after=dict(index=int(scope['index']),laststeer=float(scope['laststeer']));assert original.tolist()==old[step-1]['control']['action']
            command=original.copy()
            if step==target:
                boundary=complete_state(env,obs,dict(before=memory_before,after=memory_after,nominal_command=original.tolist()));save(f/'fork-boundary-private.json',boundary)
                if arm!='O':assert boundary==read(d/(key+'-O')/'fork-boundary-private.json'),('fullfork_physical_memory_RNG_mismatch',key,arm)
                fork_exact=True;command=changed_command(scope,pre,fixed,arm);assert command.tolist()==p['expected_float32_commands'][key][arm];assert command[0]==original[0]
                observer=ForkTrace();observer.enable()
            assert np.isfinite(command).all() and np.all(command>=np.array([-.4,0,0],np.float32)) and np.all(command<=np.array([.4,1,1],np.float32));charge(root,key,arm,'actions');charged+=1;before=raw.t;obs,_,ended,truncated,info=env.step(command);rt=round((raw.t-before)*50);ticks+=rt;post=sensor(env)
            if observer:observer.disable()
            row=dict(step=step,pre=pre,post=post,original_command=original.tolist(),command=command.tolist(),collision=bool(info['collision']),damage=float(env.damage.damage),raw_ticks=rt,memory_before=memory_before,memory_after=memory_after,terminated=bool(ended),truncated=bool(truncated));rows.append(row)
            if step<target or arm=='O':assert post==old[step-1]['post'] and row['collision']==old[step-1]['collision'] and env.damage.damage==old_damage[step-1]['damage'];matched+=1
            assert bool(info['collision'])==old[step-1]['collision'] if step<target or arm=='O' else True
            assert not ended and not truncated,('unexpectedterminal',key,arm,step)
            if step==target:
                assert rt==4 and len(observer.rows)==16;fork=dict(row,raw_tire_samples=observer.rows,post_full=complete_state(env,obs,memory_after));save(f/'fork-private.json',fork)
        status='REGISTERED_ONE_ACTION_DONE'
    except BaseException as e:
        status='SAFETY_STOP' if isinstance(e,SafetyStop) else 'TECHNICAL_STOP';error=type(e).__name__+': '+str(e);save(f/'error-private.json',dict(error=error,traceback=traceback.format_exc()))
    finally:
        if observer:observer.disable()
        if env:env.close()
    save(f/'trace-private.json',rows);r=dict(case=key,arm=arm,status=status,native=charged,raw_ticks=ticks,reset_ticks=reset,matched_original_rows=matched,initial_exact=initial_exact,fork_full_state_exact=fork_exact,technical_error=error if status=='TECHNICAL_STOP' else None,stop_error=error,unconfirmed_charged_native=charged-len(rows),runner_CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,wholeworker_CPU_sofar_s=time.process_time(),diagnostic_prefix_only=True,actual_lap_claim=False,new_actor=0,new_model=0)
    save(f/'result.json',r);print(json.dumps(r),flush=True);return r

def response(root,key,arm):
    d=root/'stage394';base=read(d/(key+'-O')/'fork-private.json');x=read(d/(key+'-'+arm)/'fork-private.json');angle=base['pre']['angle'];fwd=np.array([-np.sin(angle),np.cos(angle)]);lat=np.array([np.cos(angle),np.sin(angle)]);dv=np.array(x['post']['vel'])-base['post']['vel'];dp=np.array(x['post']['pos'])-base['post']['pos'];dy=x['post']['yaw']-base['post']['yaw'];new_pairs=set(tuple(z) for z in x['post_full']['physical']['touching_obstacle_contacts'])-set(tuple(z) for z in base['post_full']['physical']['touching_obstacle_contacts']);safe=not x['collision'] and x['damage']<=base['damage'] and all(n>0 for n in x['post']['road_contacts']) and not new_pairs and abs(dy)<=.05
    z=dict(case=key,arm=arm,delta_forward_velocity_m_s=float(dv@fwd),delta_lateral_velocity_m_s=float(dv@lat),delta_yaw_rate_rad_s=dy,delta_lateral_position_m=float(dp@lat),safe_local_registered_gate=bool(safe),new_touching_obstacle_pairs=len(new_pairs),collision=x['collision'],damage=x['damage'],all_wheels_onroad=all(n>0 for n in x['post']['road_contacts']),N1_local_response_passed=bool(key=='N1' and arm=='C' and safe and dv@fwd>=.1));save(d/(key+'-'+arm)/'response.json',z)
    if arm!='O' and not safe:
        path=d/'SafetyStop.json'
        if not path.exists():save(path,dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),failed_response=z))
    return z

def run_case(root,key):
    p=verify(root,True);d=root/'stage394';assert key in p['jobs'] and not(d/(key+'-case-opening.json')).exists();save(d/(key+'-case-opening.json'),dict(pid=os.getpid(),epoch=time.time()))
    def register(b):
        assert key not in b['active_cases'] and key not in b['finished_cases'] and len(b['active_cases'])<2;b['active_cases'].append(key)
    lock_budget(d,register);resource.setrlimit(resource.RLIMIT_CPU,(59,60))
    def timedout(signum,frame):raise TimeoutError('394 workerCPUbudget')
    sigprof=signal.signal(signal.SIGPROF,timedout);sigxcpu=signal.signal(signal.SIGXCPU,timedout);signal.setitimer(signal.ITIMER_PROF,max(.001,58-time.process_time()));records=[];responses=[];error=None
    try:
        for arm in p['jobs'][key]['arms']:
            if (d/'SafetyStop.json').exists():break
            r=episode(root,key,arm,p);records.append(r)
            if r['status']!='REGISTERED_ONE_ACTION_DONE':break
            z=response(root,key,arm);responses.append(z)
            if arm!='O' and not z['safe_local_registered_gate']:break
    except BaseException as e:error=type(e).__name__+': '+str(e);save(d/(key+'-case-error.json'),dict(error=error,traceback=traceback.format_exc()))
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.signal(signal.SIGPROF,sigprof);signal.signal(signal.SIGXCPU,sigxcpu)
        def finished(b):
            b['active_cases'].remove(key);b['finished_cases'].append(key);b['CPU_by_case'][key]=time.process_time()
        lock_budget(d,finished)
    save(d/(key+'-case-result.json'),dict(records=records,responses=responses,case_error=error,unexecuted=[a for a in p['jobs'][key]['arms'] if a not in [r['arm'] for r in records]],wholeworker_CPU_s=time.process_time()))

if __name__=='__main__':
    root=Path(sys.argv[1]).resolve()
    if sys.argv[2]=='prepare':prepare(root)
    else:run_case(root,sys.argv[2])
