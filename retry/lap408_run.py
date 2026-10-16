"""One posthoc GT full-lap diagnostic after the already frozen single pulse."""
import datetime,hashlib,json,os,random,resource,signal,sys,time,traceback
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.cross404_common import G,scope_for,executor,multipliers,control_code
from retry.loss389_replay import sensor
from retry.fork394_run import ForkTrace,complete_state
from retry.executor397 import canonical_projection,ExecutorDomainError
from retry.pilot398_run import safety_flags,finish_dict,raw_capture_pairs
from retry.pulse407_run import cmem,QualificationFailure,SafetyStop

def prepare(root):
 d=root/'stage408';assert not d.exists();old=read(root/'stage407/plan.json');v=read(root/'project-effective-budget-v427.json');r=read(root/'stage407/result.json');assert (v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(31081,84000,0);assert r['shared_stop'] is None and r['results'][1]['status']=='SAFE_COMMON_ARC_REACHED'
 for f,h in {**old['sources'],**old['protected']}.items():assert sha(f)==h,f
 paths=[Path(__file__),G/'retry/pulse407_run.py',root/'stage407/plan.json',root/'stage407/result.json',root/'stage407/pulse_C268/initial-private.json',root/'stage407/pulse_C268/fork-private.json',root/'stage407/pulse_C268/trace-private.jsonl',root/'stage407/pulse_C268/result.json',root/'stage404/O_268/result.json',root/'project-effective-budget-v427.json',root/'research-deadline-current.json'];sources=dict(old['sources']);sources.update({str(f):sha(f) for f in paths});d.mkdir(mode=0o700)
 p=dict(stage=408,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],case=old['case'],initial_pixels=old['initial_pixels'],fixed_plan=old['fixed_plan'],coefficient_source=old['coefficient_source'],pulse=old['pulse'],pulse_step=91,original_prefix_actions=90,reproduce407_actions=107,original_failure_arc=old['original_failure_arc'],native_cap=600,reset_cap=1,CPU_cap_s=90,wall_cap_s=180,max_parallel=1,model_actor_learning_SEALED_paid_reserve_cap=0,cost_basis='407 runner12.439CPU/210wrapper =>35.54CPU/600; wall12.477/210=>35.65s/600. CPU90/wall180 covers one reset/fullcaptures/rawtire/finish checks. 404O268185actions16.766CPU implies54.38CPU/600, also within90.',control='Same known N1 reset, original C268 prefix90. At91 override once float32(0,0,.3), nominal computation/memory staysunchanged; from92 existing C268 ownactual feedback only. No extra pulse, selector, gain/profile/horizon changes. Storedfuture commands/states evaluationonly, neverforced.',qualification='All source/protection hashes exact. Fresh initial fullstate/RNG/pixels equal407pulse; prefix90 pre/post sensors/commands/nominalmemory/reference/outcome exact404; pre91 nominal/state exact404 and fullfork before+after C/nominal memory equal407pulse. First107 executed rows sensors/commands/memory/reference/rawtire/outcomes exactly407pulse, withoutforcing. Any mismatch/technical/domain/resource/deadline stops thisonlyrun,no repair/retry.',safety='Same398/404/407 samplednearestpath>3m,newcollision/obstacletouch,damageincrease,roadloss/rawgrass,meaningfulreverse<-.1; current C FIRST_LAP negative sigma domainstop. Firstviolation stops, retainfirstnewfailedtransition evenifofficialfinishsimultaneous. Clip alone observednotveto.',finish='Only official finish_time_s with qualifiedforwardedge; relative lap=(finish_time_s-resetstart_t), DONE checked via existing C mark_done. Stop first officialfinish, retirement/truncation, safety/domain/technical/resource/deadline, or600cap. ActualDNF vs researchcensor separate; no full-lap rerun/tuning after outcome.',readout='Posthoc GT diagnostic selected using knownfailurelocation, notdeployableframepolicy/pixel296/generalization. Ifsafecomplete comparetime/damage to cached404O26814.78s/damage0 (notconcurrentpair); iffails reportfirstnew segment afterreproduced107, previoussafe/newfailurearc/time/path/yaw/speed andcurrentcommand. No imputedlap forcensoredfailure. Local407recovery doesnotguaranteefulllap.',reference_O268_lap_ms=14780,reference_O268_damage=0,research_before=31081,research_after_worst_case=30481,reserve=84000,reserve_used=0,sources=sources,protected=old['protected'])
 save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');(d/'plan.sha256').chmod(0o600);save(d/'qualification.json',dict(passed=True,static_sources_exact=True,dynamic_initial_prefix_fork_replay_required=True,new_native_yet=0));save(d/'budget.json',dict(actions=0,resets=0,CPU_s=0,wall_s=0));print(json.dumps(dict(registered=True,plan_sha256=sha(d/'plan.json'),native_cap=600,reset_cap=1,CPU_cap_s=90,wall_cap_s=180)))

def run(root):
 from retry.diagnose import make_env
 d=root/'stage408';p=read(d/'plan.json');assert not(d/'opening.json').exists() and read(d/'qualification.json')['passed'];assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
 for f,h in {**p['sources'],**p['protected']}.items():assert sha(f)==h,f
 cpu=time.process_time();wall=time.perf_counter();save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));b=read(d/'budget.json')
 def persist():b.update(CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall);save(d/'budget.json',b)
 def guard():
  persist()
  if b['CPU_s']>=90 or b['wall_s']>=180:raise TimeoutError('408resourcecap')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')):raise TimeoutError('408deadline')
 def charge(kind):
  guard();key='resets' if kind=='reset' else 'actions';assert b[key]<(1 if key=='resets' else 600);b[key]+=1;persist()
 def timeout(*args):raise TimeoutError('408OSresourcecap')
 oldsig={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM,signal.SIGXCPU]};resource.setrlimit(resource.RLIMIT_CPU,(int(time.process_time())+91,int(time.process_time())+92));signal.setitimer(signal.ITIMER_PROF,89);signal.setitimer(signal.ITIMER_REAL,179)
 env=observer=journal=raw=scope=policy=obs=None;rows=[];steps=ticks=reset=prefixmatched=replaymatched=0;status='STARTED';error=None;safety=[];maxerr=0.;initial_exact=fork_exact=completed=ended=truncated=False;start_t=None;info={};attempted_step=None;pre=None;command=None;ref=None;phases=[]
 try:
  fixed=read(Path(p['fixed_plan']));line=np.asarray(fixed['line']);coef=read(Path(p['coefficient_source']));pace=multipliers(coef['coefficients'],fixed['free_profile']['curvature'],fixed['free_profile']['ds'],fixed['model']);code,_=control_code(G/'retry/pace269_run.py');old=[json.loads(s) for s in (root/'stage404/C_268/trace-private.jsonl').read_text().splitlines()];replay=[json.loads(s) for s in (root/'stage407/pulse_C268/trace-private.jsonl').read_text().splitlines()]
  guard();random.seed(394);np.random.seed(394);env=make_env();charge('reset');obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});raw=env.unwrapped;start_t=float(raw.t);reset=round(raw.t*50);scope=scope_for(env,fixed,pace);policy=executor(fixed,pace);initial=complete_state(env,obs,dict(index=0,laststeer=0.));save(d/'initial-private.json',initial)
  if initial!=read(root/'stage407/pulse_C268/initial-private.json') or hashlib.sha256(obs.tobytes()).hexdigest()!=p['initial_pixels'] or hashlib.sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest()!=p['case']['road_geometry_sha256']:raise QualificationFailure('initial407')
  initial_exact=True;initial_damage=float(env.damage.damage);initial_pairs=set(tuple(x) for x in initial['physical']['touching_obstacle_contacts']);observer=ForkTrace();journal=(d/'trace-private.jsonl').open('x');(d/'trace-private.jsonl').chmod(0o600)
  for step in range(1,601):
   guard();attempted_step=step;pre=sensor(env);memory_before=dict(index=int(scope['index']),laststeer=float(scope['laststeer']));cb=cmem(policy);exec(code,dict(np=np),scope);nominal=scope['action'];memory_after=dict(index=int(scope['index']),laststeer=float(scope['laststeer']));previous=policy.phase;command,ref=policy.act(pre,nominal,finish_dict(raw),scope['arc']);ca=cmem(policy)
   if command is None:raise QualificationFailure('unexpectedDONE_beforeofficialfinish')
   if previous!=policy.phase:phases.append(dict(step=step,phase=policy.phase))
   if step<=91:
    h=old[step-1]
    if not(pre==h['pre'] and nominal.tolist()==h['nominal'] and command.tolist()==h['command'] and memory_before==h['memory_before'] and memory_after==h['memory_after'] and all(ref[k]==h['reference'][k] for k in ref)):raise QualificationFailure('originalprefix_pre_'+str(step))
   if step==91:
    fork=complete_state(env,obs,dict(before=memory_before,after=memory_after,Cbefore=cb,Cafter=ca,nominal_command=command.tolist()));save(d/'fork-private.json',fork)
    if fork!=read(root/'stage407/pulse_C268/fork-private.json'):raise QualificationFailure('fullfork407')
    fork_exact=True;command=np.asarray(p['pulse'],np.float32)
   why=safety_flags(pre,ref['projection'],float(env.damage.damage),initial_damage)
   if why:safety=why;raise SafetyStop(','.join(why))
   if not(np.isfinite(command).all() and np.all(command>=np.array([-.4,0,0],np.float32)) and np.all(command<=np.array([.4,1,1],np.float32))):raise QualificationFailure('actiondomain')
   observer.rows=[];observer.enable();charge('action');steps+=1;before=raw.t
   try:obs,_,ended,truncated,info=env.step(command)
   finally:observer.disable()
   rt=round((raw.t-before)*50);ticks+=rt;post=sensor(env);damage=float(env.damage.damage);qp=canonical_projection(line,post['pos'],post['vel'],policy.phase);maxerr=max(maxerr,qp['path_error_m']);why=safety_flags(post,qp,damage,initial_damage,bool(info['collision']),bool(set(tuple(x) for x in raw_capture_pairs(env))-initial_pairs),any(z['grass'] for z in observer.rows));completed=raw.finish_time_s is not None
   row=dict(step=step,pre=pre,post=post,command=command.tolist(),nominal=nominal.tolist(),memory_before=memory_before,memory_after=memory_after,Cbefore=cb,Cafter=ca,reference=ref,post_projection=qp,raw_ticks=rt,raw_tire_samples=observer.rows.copy(),collision=bool(info['collision']),damage=damage,ended=bool(ended),truncated=bool(truncated),safety=why,completed=completed,finish_time_s=raw.finish_time_s,retire_reason=info.get('retire_reason'));rows.append(row);journal.write(json.dumps(row,allow_nan=False)+'\n');journal.flush()
   if rt!=4 or len(observer.rows)!=16:raise QualificationFailure('rawtickshape')
   if step<=90:
    h=old[step-1]
    if not(post==h['post'] and command.tolist()==h['command'] and row['collision']==h['collision'] and damage==h['damage']):raise QualificationFailure('originalprefix_post_'+str(step))
    prefixmatched+=1
   if step<=107:
    h=replay[step-1]
    if not all(row[k]==h[k] for k in h):raise QualificationFailure('exact407replay_'+str(step))
    replaymatched+=1
   if why:safety=why;raise SafetyStop(','.join(why))
   if completed:
    policy.mark_done(finish_dict(raw),raw.t);phases.append(dict(step=step,phase=policy.phase));status='COMPLETED_SAFE';break
   if ended:status='ACTUAL_DNF';break
   if truncated:status='ENV_CENSORED';break
  else:status='NATIVE_CAP_CENSORED'
 except BaseException as e:
  error=type(e).__name__+': '+str(e)
  if isinstance(e,SafetyStop):status='SAFETY_STOP_CENSORED'
  elif isinstance(e,ExecutorDomainError):status='DOMAIN_STOP_CENSORED'
  else:status='RESOURCE_STOP_CENSORED' if isinstance(e,TimeoutError) else 'QUALIFICATION_OR_TECHNICAL_STOP'
  save(d/'stop-private.json',dict(status=status,error=error,traceback=traceback.format_exc(),attempted_step=attempted_step,pre=pre,command=None if command is None else command.tolist(),reference=ref))
 finally:
  if observer:observer.disable()
  if journal:journal.close()
  if env and raw is not None and scope is not None and policy is not None and obs is not None:
   try:save(d/'final-full-private.json',complete_state(env,obs,dict(index=int(scope['index']),laststeer=float(scope['laststeer']),C=cmem(policy))))
   except BaseException as e:save(d/'capture-error.json',dict(error=str(e)));status='QUALIFICATION_OR_TECHNICAL_STOP';error=error or str(e)
   lap_ms=round((raw.finish_time_s-start_t)*1000) if completed else None;env.close()
  else:
   lap_ms=None
   if env:env.close()
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in oldsig.items():signal.signal(s,h)
  persist()
 rr=dict(stage=408,status=status,error=error,safety=safety,completed_official=completed,completed_safe=status=='COMPLETED_SAFE',actual_DNF=bool(ended and not completed),truncated=bool(truncated),censored=status!='COMPLETED_SAFE' and not ended,retire_reason=info.get('retire_reason'),native=steps,raw_ticks=ticks,reset_ticks=reset,confirmed_rows=len(rows),unconfirmed_charged_native=steps-len(rows),initial_exact=initial_exact,fork_qualified=fork_exact,prefix90_exact_rows=prefixmatched,reproduced407_exact_rows=replaymatched,attempted_step=attempted_step,max_path_error_m=maxerr,damage=rows[-1]['damage'] if rows else None,lap_ms=lap_ms,reference_O268_lap_ms=14780,reference_O268_damage=0,lap_delta_vs_O268_ms=lap_ms-14780 if status=='COMPLETED_SAFE' else None,phase_events=phases,budget=b,wholeworker_CPU_s=time.process_time(),new_model_actor_learning_SEALED_paid_reserve=0);save(d/'result.json',rr);print(json.dumps(rr),flush=True)

if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
