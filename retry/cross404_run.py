"""Three once-only actual cells; cached402 C-base remains explicitly historical."""
import datetime,json,hashlib,os,random,resource,signal,sys,time,traceback
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.cross404_common import G,scope_for,executor,multipliers,control_code
from retry.loss389_replay import sensor
from retry.fork394_run import ForkTrace,complete_state
from retry.executor397 import canonical_projection,ExecutorDomainError
from retry.pilot398_run import safety_flags,finish_dict,raw_capture_pairs
class SafetyStop(RuntimeError):pass

def run(root):
 from retry.diagnose import make_env
 d=root/'stage404';p=read(d/'plan.json');gate=read(d/'qualification.json');assert gate['passed'] and not(d/'opening.json').exists();assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
 for f,h in {**p['sources'],**p['protected']}.items():assert sha(f)==h,f
 save(d/'opening.json',dict(epoch=time.time(),pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));b=read(d/'budget.json');b['started_epoch']=time.time();save(d/'budget.json',b);cpu=time.process_time();results=[];shared=None;resource.setrlimit(resource.RLIMIT_CPU,(179,180))
 def timeout(*args):raise TimeoutError('404CPU180')
 oldsig=signal.signal(signal.SIGPROF,timeout);oldcpu=signal.signal(signal.SIGXCPU,timeout);signal.setitimer(signal.ITIMER_PROF,max(.01,178-time.process_time()))
 def guard():
  b['CPU_s']=time.process_time()-cpu;save(d/'budget.json',b)
  if b['CPU_s']>=180 or time.time()-b['started_epoch']>=300:raise TimeoutError('404resourcecap')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(p['deadline_utc']):raise TimeoutError('404deadline')
 def charge(kind,name):
  guard()
  if kind=='reset':assert b['resets']<3;b['resets']+=1
  else:assert b['actions']<1600;b['actions']+=1;b['case_actions'][name]=b['case_actions'].get(name,0)+1
  save(d/'budget.json',b)
 fixed=read(Path(p['fixed_plan']));line=np.asarray(fixed['line']);coef=read(Path(p['coefficient_source']));frozen=multipliers(coef['coefficients'],fixed['free_profile']['curvature'],fixed['free_profile']['ds'],fixed['model']);assert frozen.tolist()==read(d/'profiles-private.json')['frozen268'];code,digest=control_code(G/'retry/pace269_run.py');assert digest==read(d/'controller-AST-sha256.json')['source269_AST_sha256'];initial_stored=read(root/'stage402/P10_C/initial-private.json');historic=read(root/'stage269/N1_candidate/trajectory-private.json');histres=read(root/'stage269/N1_candidate/result.json');basefirst=json.loads((root/'stage402/P10_C/trace-private.jsonl').read_text().splitlines()[0])
 try:
  for arm in p['arms']:
   guard();name=arm['name'];folder=d/name;assert not folder.exists();folder.mkdir(mode=0o700);env=observer=journal=None;rows=[];steps=ticks=reset=0;damage=maxerr=0.;completed=ended=truncated=False;info={};status='STARTED';error=None;safety=[];initial_exact=first_exact=False;phases=[];history_checks=[];last_arc=unwrapped=None;epicpu=time.process_time();epiwall=time.perf_counter();start_t=None
   try:
    random.seed(394);np.random.seed(394);pace=frozen if arm['profile']=='268' else np.ones(len(frozen));policy=executor(fixed,pace) if arm['executor']=='C' else None;env=make_env();charge('reset',name);obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});raw=env.unwrapped;start_t=float(raw.t);reset=round(raw.t*50);scope=scope_for(env,fixed,pace);initial=complete_state(env,obs,dict(index=0,laststeer=0.));save(folder/'initial-private.json',initial);assert initial==initial_stored and hashlib.sha256(obs.tobytes()).hexdigest()==p['initial_pixels'] and hashlib.sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest()==p['case']['road_geometry_sha256'];initial_exact=True;initial_damage=float(env.damage.damage);initial_pairs=set(tuple(x) for x in initial['physical']['touching_obstacle_contacts']);observer=ForkTrace();journal=(folder/'trace-private.jsonl').open('x');(folder/'trace-private.jsonl').chmod(0o600)
    for step in range(1,arm['cap']+1):
     guard();pre=sensor(env);memory_before=dict(index=int(scope['index']),laststeer=float(scope['laststeer']));exec(code,dict(np=np),scope);nominal=scope['action'];memory_after=dict(index=int(scope['index']),laststeer=float(scope['laststeer']))
     if policy:
      previous=policy.phase;command,ref=policy.act(pre,nominal,finish_dict(raw),scope['arc']);assert command is not None;qpre=ref['projection']
      if previous!=policy.phase:phases.append(dict(step=step,phase=policy.phase))
     else:
      command=nominal;qpre=canonical_projection(line,pre['pos'],pre['vel'],'FIRST_LAP');ref=dict(phase='ORIGINAL_CURSOR',r=scope['desired'],f=scope['feed'],raw_accel=scope['feed']+1.5*(scope['desired']-scope['speed']),command_accel=scope['acc'],projection=qpre,profile_wrapped=bool(scope['index']>=len(line)))
     if last_arc is None:unwrapped=qpre['arc']
     else:unwrapped+=(qpre['arc']-last_arc+sum(fixed['free_profile']['ds'])/2)%sum(fixed['free_profile']['ds'])-sum(fixed['free_profile']['ds'])/2
     last_arc=qpre['arc'];ref['measured_unwrapped_arc']=unwrapped;maxerr=max(maxerr,qpre['path_error_m']);why=safety_flags(pre,qpre,float(env.damage.damage),initial_damage)
     if why:safety=why;raise SafetyStop(','.join(why))
     observer.rows=[];observer.enable();charge('action',name);steps+=1;before=raw.t
     try:obs,_,ended,truncated,info=env.step(command)
     finally:observer.disable()
     rt=round((raw.t-before)*50);ticks+=rt;post=sensor(env);damage=float(env.damage.damage);assert len(observer.rows)==4*rt;qp=canonical_projection(line,post['pos'],post['vel'],'FIRST_LAP' if not policy else policy.phase);maxerr=max(maxerr,qp['path_error_m']);why=safety_flags(post,qp,damage,initial_damage,bool(info['collision']),bool(set(tuple(x) for x in raw_capture_pairs(env))-initial_pairs),any(s['grass'] for s in observer.rows));completed=raw.finish_time_s is not None
     history=None
     if name=='O_268':
      if step<=len(historic):
       h=historic[step-1];history=dict(action=command.tolist()==h['action'],speed=float(scope['speed'])==h['speed_m_s'],target=float(scope['desired'])==h['target_speed_m_s'],cursor_path_error=float(scope['err'])==h['path_error_m'],visited=post['visited']==h['visited'],damage=damage==h['damage'],collision=bool(info['collision'])==h['collision'])
      else:history=dict(extra_action_beyond_history=False)
      history_checks.append(history)
     row=dict(step=step,pre=pre,post=post,command=command.tolist(),nominal=nominal.tolist(),memory_before=memory_before,memory_after=memory_after,reference=ref,post_projection=qp,cursor=dict(index=int(scope['index']),u=float(scope['u']),arc=float(scope['arc']),path_error=float(scope['err']),target=float(scope['desired']),feed=float(scope['feed'])),raw_ticks=rt,raw_tire_samples=observer.rows.copy(),collision=bool(info['collision']),damage=damage,completed=completed,ended=bool(ended),truncated=bool(truncated),retire_reason=info.get('retire_reason'),historical_check=history);rows.append(row);journal.write(json.dumps(row,allow_nan=False)+'\n');journal.flush()
     if step==1:first_exact=command.tolist()==basefirst['command'] and post==basefirst['post'];assert first_exact
     if why:safety=why;raise SafetyStop(','.join(why))
     if completed:
      if policy:policy.mark_done(finish_dict(raw),raw.t)
      phases.append(dict(step=step,phase='DONE_OFFICIAL'));status='COMPLETED';break
     if ended:status='ACTUAL_DNF';break
     if truncated:status='ENV_CENSORED';break
    else:status='NATIVE_CAP_CENSORED'
   except BaseException as e:
    error=type(e).__name__+': '+str(e)
    if isinstance(e,SafetyStop):status='SAFETY_STOP_CENSORED'
    elif isinstance(e,ExecutorDomainError):status='DOMAIN_STOP_CENSORED'
    elif isinstance(e,TimeoutError):status='RESOURCE_CENSORED';shared=error
    else:status='TECHNICAL_STOP_CENSORED';shared=error
    save(folder/'stop-private.json',dict(status=status,error=error,traceback=traceback.format_exc()))
   finally:
    if observer:observer.disable()
    if journal:journal.close()
    if env:
     try:save(folder/'final-full-private.json',complete_state(env,obs,dict(index=int(scope['index']),laststeer=float(scope['laststeer']))))
     except BaseException as ce:save(folder/'final-capture-error.json',dict(error=str(ce)))
     lap=round((raw.finish_time_s-start_t)*1000) if completed else None;env.close()
    else:lap=None
   hist_final=bool(name=='O_268' and completed and steps==histres['native_actions'] and lap==histres['lap_ms'] and damage==histres['damage'] and len(history_checks)==len(historic) and all(all(z.values()) for z in history_checks))
   result=dict(arm=name,executor=arm['executor'],profile=arm['profile'],fresh_actual=True,status=status,completed=completed,actual_DNF=bool(ended and not completed),censored=bool(not completed and not ended),lap_ms=lap,retire_reason=info.get('retire_reason'),stop_reason=error,safety=safety,native=steps,raw_ticks=ticks,reset_ticks=reset,damage=damage,max_path_error_m=maxerr,initial_exact=initial_exact,first_launch_exact=first_exact,phase_events=phases,historical269_reproduced=hist_final if name=='O_268' else None,historical269_exact_rows=sum(all(z.values()) for z in history_checks) if name=='O_268' else None,historical269_checked_rows=len(history_checks) if name=='O_268' else None,unconfirmed_charged_native=steps-len(rows),episode_CPU_s=time.process_time()-epicpu,episode_wall_s=time.perf_counter()-epiwall)
   save(folder/'result.json',result);results.append(result);b['finished'].append(name);save(d/'budget.json',b);print(json.dumps(result,ensure_ascii=False),flush=True)
   if shared:break
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.signal(signal.SIGPROF,oldsig);signal.signal(signal.SIGXCPU,oldcpu);b['CPU_s']=time.process_time()-cpu;b['wall_s']=time.time()-b['started_epoch'];save(d/'budget.json',b)
 x=dict(stage=404,results=results,shared_stop=shared,unexecuted_arms=[a['name'] for a in p['arms'] if a['name'] not in [r['arm'] for r in results]],cached_C_base=read(root/'stage402/P10_C/result.json'),budget=b,wholeworker_CPU_s=time.process_time(),new_actor_calls=0,new_model_integration_ticks=0,new_learning_fits=0,new_SEALED_queries=0,new_paid_resources=0);save(d/'result.json',x);print(json.dumps(dict(stage=404,budget=b,shared_stop=shared),ensure_ascii=False))
if __name__=='__main__':run(Path(sys.argv[1]))
