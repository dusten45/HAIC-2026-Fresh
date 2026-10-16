"""Frozen 12-action own-state GT control windows; no actor/model/learning."""
import datetime,fcntl,json,math,os,random,resource,signal,sys,time,traceback
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.loss389_replay import sensor
from retry.probe390_run import control_code
from retry.scalar392_audit import project,pedals
from retry.coherent393_audit import runtime_nodes,rf
from retry.fork394_run import ForkTrace,complete_state
G=Path(__file__).resolve().parent.parent
class DomainStop(RuntimeError):pass
class SafetyStop(RuntimeError):pass

def budget_update(d,fun):
    with (d/'budget.lock').open('a') as h:
        fcntl.flock(h,fcntl.LOCK_EX);b=read(d/'budget.json');z=fun(b);save(d/'budget.json',b);return z

def prepare(root):
    d=root/'stage395';assert not d.exists();d.mkdir(mode=0o700);p394=read(root/'stage394/plan.json');p390=read(root/'stage390/plan.json');v=read(root/'project-effective-budget-v414.json');assert v['research_remaining']==33154 and v['final_reserved_actions']==84000 and v['final_reserve_used']==0
    jobs=dict(N1=dict(first=161,last=172,arms=['O','C']),O0=dict(first=221,last=232,arms=['O','C']));sources=[Path(__file__),G/'retry/fork394_run.py',G/'retry/probe390_run.py',G/'retry/loss389_replay.py',G/'retry/loss389_analyze.py',G/'retry/scalar392_audit.py',G/'retry/coherent393_audit.py',G/'retry/pace265_run.py',G/'retry/source_vehicle_transition.py',G/'retry/pedal331_run.py',G/'retry/diagnose.py',G/'env_wrapper.py',G/'damage.py',root/'stage394/plan.json',root/'stage390/plan.json',root/'project-effective-budget-v414.json',root/'research-deadline-current.json']+list((G/'core').rglob('*.py'))
    for key in jobs:sources += [Path(p394['fixed_plans'][key]),root/('stage390/A-'+key)/'trace-private.json',Path(p390['A_references'][key])/'trajectory-private.json']+[root/('stage394/'+key+'-O')/name for name in ['initial-private.json','fork-boundary-private.json']]
    p=dict(stage=395,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',jobs=jobs,cases=p394['cases'],initial_pixels=p394['initial_pixels'],fixed_plans=p394['fixed_plans'],old_damage_references={k:str(Path(p390['A_references'][k])/'trajectory-private.json') for k in jobs},controller_AST_sha256=p394['controller_AST_sha256'],observer_rng_seed=394,native_cap=808,reset_cap=4,CPU_cap_s=120,wall_cap_s=300,parallel_cap=2,actor_cap=0,model_integration_cap=0,learning_cap=0,final_reserve_use=0,research_before=33154,research_after_worst_case=32346,window_actions=12,window_s=.96,information_gate='BothO/Cfull12completed; finalsignedactualprojectedarc progressCminusO>=1m; maxactualnearestpathEuclideandistance<=3m;no newcollision/damage/roadcontactloss/meaningfulreverse. Notlap/generalization/296promotion.',projection='Same392uniqueinteriorclosedpolyline actualpositionprojection; sigma=velocity dotunitsegmenttangent. Arc unwrap bysignedshortestperiodicdifference,initialgauge nearestoriginalcursorarc. No poststate usedfornextcommandexceptnormalownenvironmentfeedback; storedfuturestates/actions only O/prefixvalidation,notCinput.',domain='Duringwindowbotharms requireuniqueinteriorprojection,ownoriginalcursor index<N andactualunwrappedarc in[0,L];referenceonactualsegment mustr>0. C requires signedsigma>=0 withnoepsilon. Profilebranch/lapcross/zero_r/multipleorendpoint ->DOMAIN_STOPwithoutfallback. Prefixonlyusesoriginal265,includingitsoriginalstandingstart. No domainruleoverwrittenafteroutcomes.',controls='Reset+original265 AST atpace1.5 tofirst-1. Thereafter everyarm recalculates originalGTsteeringandpersistentindex/laststeer fromownactualstate. Ooriginalpedals; Csameactualfootr/f/sigma onfrozenoriginalprofilewithsameclamps. Noforcingfuturestoredsteer/state. No gain/path/profilechanges.',qualification='Initialandfirst-windowfullavailablephysical/RNG/observation/finish/wrapper/controllerbefore/aftercaps equal394OandpairedO. No directexportedhiddenBox2Dwarmstartclaim. Allnominalprefixpre/post/actions/damage exact390/reusedoldreference;Owholewindowalsoexact390.',safety='Checkbothpre/postduringwindow:actualhulltonearestpathdistance<=3m,all4wheelsroadcontacts,damage<=forkdamage,no collisionornewtouchingobstaclepair; sigmaprogress orbodyforwardv<-.1m/s ->meaningfulreverse. Yaw/laterslip/steer recorded but394samepositionyawdiff.05notreusedasgateaftertrajectoriesdiverge. GlobalSafetyStop onviolation.',stops='DOMAIN_STOPcurrentcasewithoutfallback;technical/prefixfailurecurrentcaseandremainingdependentarmsstop. Safety/resource/deadline ->stopallnewnative. No retry/substitution/horizonextension. Unexpectedfinish/terminal endswindowwithoutlapperformanceclaim.',measure='All12pre/postphysicalsource/ownstatecontroller/refdata;rawtire16samplesperaction andrequested/actualgas/brake,slip,clip,yaw/lateral/arc/pathdistance,contacts/damage. Baselineendpointcomparison onlyafterwindows,notruntimecontrol.',sources={str(f):sha(f) for f in sources},protected={str(f):sha(f) for f in [root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json']},forbidden='Newlap/gainsweep/actor/modelintegration/learning/372details/DEV/HOLDOUT/SEALED/paidresource/reserveuse')
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');(d/'plan.sha256').chmod(0o600);save(d/'budget.json',dict(actions=0,resets=0,arm_actions={},started_epoch=None,active_cases=[],finished_cases=[],CPU_by_case={}));(d/'budget.lock').touch(mode=0o600);print(json.dumps(dict(registered=True,plan_sha256=sha(d/'plan.json'),jobs=jobs,native_cap=808)),flush=True)

def verify(root,full=False):
    d=root/'stage395';p=read(d/'plan.json');assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip();assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(p['deadline_utc'])
    if full:
        for f,h in {**p['sources'],**p['protected']}.items():assert sha(f)==h,f
    return p

def guard(root,key):
    d=root/'stage395';verify(root)
    if (d/'SafetyStop.json').exists():raise SafetyStop('GlobalSafetyStop')
    def update(b):
        if b['started_epoch'] is None:b['started_epoch']=time.time()
        b['CPU_by_case'][key]=time.process_time();assert sum(b['CPU_by_case'].values())<120;assert time.time()-b['started_epoch']<300
    budget_update(d,update)

def charge(root,key,arm,kind,last):
    d=root/'stage395';guard(root,key)
    def update(b):
        if kind=='reset':assert b['resets']<4;b['resets']+=1
        else:
            lab=key+'-'+arm;assert b['actions']<808 and b['arm_actions'].get(lab,0)<last;b['actions']+=1;b['arm_actions'][lab]=b['arm_actions'].get(lab,0)+1
    budget_update(d,update)

class ArcTracker:
    def __init__(self,L):self.L=L;self.previous=None;self.s=None
    def update(self,arc,initial_cursor):
        if self.previous is None:self.s=arc+round((initial_cursor-arc)/self.L)*self.L
        else:
            delta=(arc-self.previous+self.L/2)%self.L-self.L/2
            if abs(delta)==self.L/2:raise DomainStop('Halfperiodambiguousarc')
            self.s+=delta
        self.previous=arc;return float(self.s)

def spatial(line,state):
    q=project(line,state['pos'],state['vel']);edge=line[(q['index']+1)%len(line)]-line[q['index']];foot=line[q['index']]+q['u']*edge;q['path_error_m']=float(np.linalg.norm(np.asarray(state['pos'])-foot));angle=state['angle'];q['body_forward_v']=float(np.asarray(state['vel'])@np.array([-np.sin(angle),np.cos(angle)]));q['body_lateral_v']=float(np.asarray(state['vel'])@np.array([np.cos(angle),np.sin(angle)]));return q

def domain(q,s,scope,fixed,arm):
    if not q['valid']:raise DomainStop(q['reason'])
    if scope['index']>=len(fixed['line']) or not 0<=s<=scope['L']:raise DomainStop('Unqualifiedlap/profilebranch')
    nodes=runtime_nodes(fixed,scope['index']);r,f=rf(nodes,np.asarray(fixed['free_profile']['ds']),q['index'],q['u'])
    if r<=0:raise DomainStop('Zeroornonpositivetarget')
    if arm=='C' and q['sigma']<0:raise DomainStop('Cnegativeprogressdomain')
    if not all(math.isfinite(z) for z in [r,f,q['sigma']]):raise DomainStop('Nonfinitereference')
    return r,f

def safety(d,key,arm,step,state,q,damage,initial_damage,collision=False,new_pairs=False):
    why=[]
    if q['path_error_m']>3:why.append('path_error_over3m')
    if not all(n>0 for n in state['road_contacts']):why.append('wheel_road_loss')
    if damage>initial_damage:why.append('new_damage')
    if collision or new_pairs:why.append('collision_ornew_obstaclecontact')
    if q['sigma'] is not None and q['sigma']<-.1 or q['body_forward_v']<-.1:why.append('meaningful_reverse')
    if why:
        path=d/'SafetyStop.json'
        if not path.exists():save(path,dict(case=key,arm=arm,step=step,reasons=why))
        raise SafetyStop(','.join(why))

def episode(root,key,arm,p):
    from retry.diagnose import make_env
    d=root/'stage395';folder=d/(key+'-'+arm);assert not folder.exists();folder.mkdir(mode=0o700);save(folder/'opening.json',dict(epoch=time.time()));job=p['jobs'][key];first,last=job['first'],job['last'];old=read(root/('stage390/A-'+key)/'trace-private.json');damageold=read(Path(p['old_damage_references'][key]));fixed=read(Path(p['fixed_plans'][key]));line=np.asarray(fixed['line']);prof=fixed['free_profile'];ds=np.asarray(prof['ds']);sarc=np.r_[0,np.cumsum(ds)];scope=dict(line=line,vprof=np.asarray(prof['speed']),ds=ds,curvature=np.asarray(prof['curvature']),sarc=sarc,L=sarc[-1],model=fixed['model'],index=0,laststeer=0.,pace=1.5);tracker=ArcTracker(float(sarc[-1]));code,digest=control_code(G/'retry/pace265_run.py');assert digest==p['controller_AST_sha256']
    env=observer=None;rows=[];window=[];charged=ticks=reset=matched=0;initial_exact=fork_exact=False;fork_s=fork_damage=None;fork_pairs=set();error=None;status='STARTED';start,cpu=time.perf_counter(),time.process_time();random.seed(394);np.random.seed(394)
    try:
        verify(root,True);guard(root,key);env=make_env();charge(root,key,arm,'reset',last);case=p['cases'][key];obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});raw=env.unwrapped;reset=round(raw.t*50);scope['env']=env
        assert __import__('hashlib').sha256(obs.tobytes()).hexdigest()==p['initial_pixels'][key] and __import__('hashlib').sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest()==case['road_geometry_sha256']
        init=complete_state(env,obs,dict(index=0,laststeer=0.));save(folder/'initial-private.json',init);assert init==read(root/('stage394/'+key+'-O')/'initial-private.json')
        if arm=='C':assert init==read(d/(key+'-O')/'initial-private.json')
        initial_exact=True
        for step in range(1,last+1):
            guard(root,key);pre=sensor(env)
            if step<=first or arm=='O':assert pre==old[step-1]['pre']
            mem_before=dict(index=int(scope['index']),laststeer=float(scope['laststeer']));exec(code,dict(np=np),scope);nominal=scope['action'];mem_after=dict(index=int(scope['index']),laststeer=float(scope['laststeer']));command=nominal.copy();q=spatial(line,pre);s=tracker.update(q['arc_m'],scope['arc']);reference=None
            if step<=first or arm=='O':assert nominal.tolist()==old[step-1]['control']['action']
            if step==first:
                boundary=complete_state(env,obs,dict(before=mem_before,after=mem_after,nominal_command=nominal.tolist()));save(folder/'fork-boundary-private.json',boundary);assert boundary==read(root/('stage394/'+key+'-O')/'fork-boundary-private.json')
                if arm=='C':assert boundary==read(d/(key+'-O')/'fork-boundary-private.json')
                fork_exact=True;fork_s=s;fork_damage=float(env.damage.damage);fork_pairs=set(tuple(x) for x in boundary['physical']['touching_obstacle_contacts'])
            if step>=first:
                r,f=domain(q,s,scope,fixed,arm);reference=dict(r=r,f=f,sigma=q['sigma'],raw_accel=f*(q['sigma']/r)+1.5*(r-pre['speed']))
                safety(d,key,arm,step,pre,q,float(env.damage.damage),fork_damage)
                if arm=='C':z=pedals(reference['raw_accel'],pre['speed'],fixed['model']);command[1:]=[z['gas'],z['brake']]
                observer=ForkTrace();observer.enable()
            assert np.isfinite(command).all() and np.all(command>=np.array([-.4,0,0],np.float32)) and np.all(command<=np.array([.4,1,1],np.float32));charge(root,key,arm,'action',last);charged+=1;before=raw.t;obs,_,ended,truncated,info=env.step(command);rt=round((raw.t-before)*50);ticks+=rt;post=sensor(env)
            if observer:observer.disable()
            row=dict(step=step,pre=pre,post=post,nominal_command=nominal.tolist(),command=command.tolist(),collision=bool(info['collision']),damage=float(env.damage.damage),raw_ticks=rt,memory_before=mem_before,memory_after=mem_after,terminated=bool(ended),truncated=bool(truncated));rows.append(row)
            if step<first or arm=='O':assert post==old[step-1]['post'] and row['collision']==old[step-1]['collision'] and row['damage']==damageold[step-1]['damage'];matched+=1
            if step>=first:
                assert rt==4 and len(observer.rows)==16;qp=spatial(line,post);sp=tracker.update(qp['arc_m'],scope['arc']);full=complete_state(env,obs,mem_after);new_pairs=set(tuple(x) for x in full['physical']['touching_obstacle_contacts'])-fork_pairs
                record=dict(row,pre_spatial=q,post_spatial=qp,pre_arc_unwrapped_m=s,post_arc_unwrapped_m=sp,progress_since_fork_m=sp-fork_s,original_cursor_path_error_m=scope['err'],coherent_reference=reference,raw_tire_samples=observer.rows,post_full=full);window.append(record);save(folder/'window-private.json',window)
                if not qp['valid']:raise DomainStop('Poststate_'+str(qp['reason']))
                if not 0<=sp<=scope['L']:raise DomainStop('Poststate_lapbranch')
                safety(d,key,arm,step,post,qp,row['damage'],fork_damage,row['collision'],bool(new_pairs))
                if arm=='C' and qp['sigma']<0:raise DomainStop('Poststate_Cnegativeprogress')
            if ended or truncated:raise DomainStop('Unexpectedterminal_orfinish_no_lapclaim')
        status='REGISTERED_12_ACTION_WINDOW_DONE'
    except BaseException as e:
        status='DOMAIN_STOP' if isinstance(e,DomainStop) else 'SAFETY_STOP' if isinstance(e,SafetyStop) else 'TECHNICAL_STOP';error=type(e).__name__+': '+str(e);save(folder/'stop-private.json',dict(status=status,error=error,traceback=traceback.format_exc()))
    finally:
        if observer:observer.disable()
        if env:env.close()
    save(folder/'trace-private.json',rows)
    if not(folder/'window-private.json').exists():save(folder/'window-private.json',window)
    result=dict(case=key,arm=arm,status=status,stop_reason=error,technical_error=error if status=='TECHNICAL_STOP' else None,native=charged,raw_ticks=ticks,reset_ticks=reset,window_actions=len(window),matched_original_rows=matched,initial_exact=initial_exact,fork_exact=fork_exact,final_progress_m=window[-1]['progress_since_fork_m'] if window else None,max_actual_path_error_m=max((max(z['pre_spatial']['path_error_m'],z['post_spatial']['path_error_m']) for z in window),default=None),unconfirmed_charged_native=charged-len(rows),runner_CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,actor=0,model_integration=0,learning=0,whole_lap_claim=False)
    save(folder/'result.json',result);print(json.dumps(result),flush=True);return result

def run_case(root,key):
    d=root/'stage395';p=verify(root,True);assert key in p['jobs'] and not(d/(key+'-case-opening.json')).exists();save(d/(key+'-case-opening.json'),dict(pid=os.getpid(),epoch=time.time()))
    def active(b):assert key not in b['active_cases']+b['finished_cases'] and len(b['active_cases'])<2;b['active_cases'].append(key)
    budget_update(d,active);resource.setrlimit(resource.RLIMIT_CPU,(59,60))
    def timeout(signum,frame):raise TimeoutError('395processCPUcap')
    oldprof=signal.signal(signal.SIGPROF,timeout);oldcpu=signal.signal(signal.SIGXCPU,timeout);signal.setitimer(signal.ITIMER_PROF,max(.001,58-time.process_time()));records=[];error=None
    try:
        for arm in ['O','C']:
            if (d/'SafetyStop.json').exists():break
            r=episode(root,key,arm,p);records.append(r)
            if r['status']!='REGISTERED_12_ACTION_WINDOW_DONE':break
    except BaseException as e:error=type(e).__name__+': '+str(e);save(d/(key+'-case-error.json'),dict(error=error,traceback=traceback.format_exc()))
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.signal(signal.SIGPROF,oldprof);signal.signal(signal.SIGXCPU,oldcpu)
        def finished(b):b['active_cases'].remove(key);b['finished_cases'].append(key);b['CPU_by_case'][key]=time.process_time()
        budget_update(d,finished)
    save(d/(key+'-case-result.json'),dict(case=key,records=records,case_error=error,unexecuted=[a for a in ['O','C'] if a not in [r['arm'] for r in records]],wholeworker_CPU_s=time.process_time()))
if __name__=='__main__':
    root=Path(sys.argv[1]).resolve()
    if sys.argv[2]=='prepare':prepare(root)
    else:run_case(root,sys.argv[2])
