"""Bounded live-parent qualification then once-only O/C GT state-trigger runs."""
import copy,datetime,json,os,random,resource,signal,sys,time,traceback
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.branch401_gate import fingerprint
from retry.cross404_common import G,scope_for,executor,control_code
from retry.loss389_replay import sensor
from retry.pilot398_run import safety_flags,finish_dict,raw_capture_pairs
from retry.fork394_run import ForkTrace,complete_state
from retry.terminal410_run import rollout,compare,ModelFailure
from retry.terminal410_model import TerminalVehicleTransition,from_actual_full
from retry.terminal409_contract import validate
from retry.executor397 import canonical_projection,ExecutorDomainError

class Stop(RuntimeError):pass
class SafetyStop(Stop):pass
class ResourceStop(Stop):pass
class Infeasible(Stop):pass

class Meter:
 def __init__(self,d):self.d=d;self.wall=time.perf_counter();self.cpu=time.process_time();self.queries=[];self.b=dict(native=0,resets=0,ticks=0,reserved=0,worlds=0,CPU_s=0.,wall_s=0.,case_native={})
 def persist(self):self.b.update(CPU_s=time.process_time()-self.cpu,wholeprocess_CPU_s=time.process_time(),wall_s=time.perf_counter()-self.wall);save(self.d/'budget.json',self.b)
 def guard(self):
  self.persist()
  if time.process_time()>=180 or self.b['wall_s']>=300:raise ResourceStop('CPU180_or_wall300')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(read(self.d/'plan.json')['deadline_utc'].replace('Z','+00:00')):raise ResourceStop('deadline')
 def charge(self,kind,name):
  self.guard()
  if kind=='reset':
   if self.b['resets']>=6:raise ResourceStop('reset6')
   self.b['resets']+=1
  else:
   if self.b['native']>=800:raise ResourceStop('native800')
   self.b['native']+=1;self.b['case_native'][name]=self.b['case_native'].get(name,0)+1
  self.persist()
 def world(self,s):
  self.guard()
  if self.b['worlds']>=1200:raise ResourceStop('world1200')
  self.b['worlds']+=1;self.persist();m=TerminalVehicleTransition(s)
  if not(m.initial_bodies_exact and m.initial_tiles_exact and m.initial_progress_exact and m.initial_finish_exact):m.close();raise ModelFailure('restore')
  return m
 def step(self,m,a):
  self.guard()
  if self.b['reserved']+4>60000:raise ResourceStop('model60000')
  self.b['reserved']+=4;self.persist();before=m.native_ticks;success=False
  try:q=m.step(a);success=True;return q
  finally:
   n=m.native_ticks-before;self.b['ticks']+=n
   if success:self.b['reserved']-=4-n
   self.persist()

class ActualController:
 def __init__(self,env,fixed,pace,kind):self.kind=kind;self.scope=scope_for(env,fixed,pace);self.code,_=control_code(G/'retry/pace269_run.py');self.policy=executor(fixed,pace) if kind=='C' else None
 def phase(self):return self.policy.phase if self.policy else 'FIRST_LAP'
 def memory(self):return dict(index=int(self.scope['index']),laststeer=float(self.scope['laststeer']),C=None if not self.policy else {k:getattr(self.policy,k) for k in ['phase','previous_arc','s','last_time','launch_commanded']})
 def act(self,env):
  exec(self.code,dict(np=np),self.scope);a=self.scope['action']
  if self.policy:a,_=self.policy.act(sensor(env),a,finish_dict(env.unwrapped),self.scope['arc'])
  if a is None:raise ModelFailure('Actual_unexpected_DONE')
  return np.asarray(a,np.float32)
 def done(self,env):
  if self.policy:self.policy.mark_done(finish_dict(env.unwrapped),float(env.unwrapped.t))

def _queried_body(meter,env,obs,ctrl,fixed,pace,kind,before,nominal,index,progress,goal,deadline,folder,tag):
 cpu=time.process_time();wall=time.perf_counter();after=ctrl.memory();full=complete_state(env,obs,after);h=fingerprint(full);state=from_actual_full(full);mhash=fingerprint(ctrl.memory());a=rollout(meter,fixed,pace,kind,state,before,index,progress,goal,deadline,False);b=rollout(meter,fixed,pace,kind,state,before,index,progress,goal,deadline,False)
 if fingerprint(a)!=fingerprint(b):raise ModelFailure('nominal_independence')
 if not a['rows']:raise ModelFailure('nominal_no_first_prediction')
 command_delta=max(abs(x-y) for x,y in zip(a['rows'][0]['command'],nominal))
 if command_delta>1e-6:raise ModelFailure('current_nominal_command_mismatch')
 pulse=None;chosen=a;selected=False
 if not a['valid']:
  pulse=rollout(meter,fixed,pace,kind,state,before,index,progress,goal,deadline,True);p2=rollout(meter,fixed,pace,kind,state,before,index,progress,goal,deadline,True)
  if fingerprint(pulse)!=fingerprint(p2):raise ModelFailure('pulse_independence')
  if pulse['valid']:chosen=pulse;selected=True
 if fingerprint(complete_state(env,obs,ctrl.memory()))!=h or fingerprint(ctrl.memory())!=mhash:raise ModelFailure('LIVE_parent_memory_RNG_mutation')
 record=dict(tag=tag,nominal=a,pulse=pulse,selected='pulse' if selected else 'nominal',parent_full_before_sha256=h,parent_full_after_sha256=h,memory_unchanged=True,current_command_max_abs_delta=float(command_delta));save(folder/('forecast-'+tag+'-private.json'),record)
 latency=dict(CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,pulse_queried=pulse is not None,selected_pulse=selected,nominal_valid=a['valid'],pulse_valid=None if pulse is None else pulse['valid'],parent_unchanged=True)
 if not a['valid'] and not selected:raise Infeasible('Both_recipes_infeasible')
 return (np.asarray([0.,0.,.3],np.float32) if selected else nominal.copy()),chosen,a,latency

def queried(meter,env,obs,ctrl,fixed,pace,kind,before,nominal,index,progress,goal,deadline,folder,tag):
 cpu=time.process_time();wall=time.perf_counter();record=dict(folder=folder.name,tag=tag,status='STARTED');meter.queries.append(record)
 try:
  result=_queried_body(meter,env,obs,ctrl,fixed,pace,kind,before,nominal,index,progress,goal,deadline,folder,tag);record.update(result[-1],status='OK');return result
 except BaseException as e:
  record.update(status='FAILED',error=type(e).__name__+': '+str(e),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall);raise
 finally:
  path=meter.d/'query-latency-private.jsonl'
  with path.open('a') as f:f.write(json.dumps(record,allow_nan=False)+'\n')
  path.chmod(0o600)

def actual_step(meter,name,env,obs,ctrl,command,line,initial_damage,initial_pairs,observer,step):
 pre=sensor(env);qp0=canonical_projection(line,pre['pos'],pre['vel'],ctrl.phase());why=safety_flags(pre,qp0,float(env.damage.damage),initial_damage)
 if why:raise SafetyStop('pre:'+','.join(why))
 if not(np.isfinite(command).all() and np.all(command>=np.array([-.4,0,0],np.float32)) and np.all(command<=np.array([.4,1,1],np.float32))):raise ModelFailure('actual_action_domain')
 observer.rows=[];observer.enable();meter.charge('action',name);t=env.unwrapped.t
 try:obs,_,ended,truncated,info=env.step(command)
 finally:observer.disable()
 post=sensor(env);rt=round((env.unwrapped.t-t)*50);damage=float(env.damage.damage);qp=canonical_projection(line,post['pos'],post['vel'],ctrl.phase());why=safety_flags(post,qp,damage,initial_damage,bool(info['collision']),bool(set(tuple(x) for x in raw_capture_pairs(env))-initial_pairs),any(z['grass'] for z in observer.rows));completed=env.unwrapped.finish_time_s is not None
 row=dict(step=step,pre=pre,post=post,command=command.tolist(),raw_ticks=rt,raw_tire_samples=observer.rows.copy(),post_projection=qp,collision=bool(info['collision']),damage=damage,ended=bool(ended),truncated=bool(truncated),completed=completed,finish_time_s=env.unwrapped.finish_time_s,retire_reason=info.get('retire_reason'),safety=why)
 if not validate(row)['passed']:raise ModelFailure('actual_terminal_measurement_contract:'+json.dumps(validate(row)))
 return obs,row

def open_env(root,meter,name,fixed,pace,kind,case):
 from retry.diagnose import make_env
 random.seed(394);np.random.seed(394);env=make_env();meter.charge('reset',name);obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});ctrl=ActualController(env,fixed,pace,kind);initial=complete_state(env,obs,dict(index=0,laststeer=0.));reference=read(root/'stage404/C_268/initial-private.json')
 if initial!=reference:env.close();raise ModelFailure('actual_initial_full_RNG_pixels')
 return env,obs,ctrl,initial

def prepare(root):
 d=root/'stage411';assert not(d/'plan.json').exists();v=read(root/'project-effective-budget-v430.json');assert (v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(30892,84000,0);p410=read(root/'stage410/plan.json');r410=read(root/'stage410/result.json');assert r410['qualification_passed'] and r410['status']=='COMPLETED_STORED_WINDOW_AUDIT'
 for f,h in {**p410['sources'],**p410['protected'],**p410['original408_preserve']}.items():assert sha(f)==h,f
 p404=read(root/'stage404/plan.json');files=[Path(__file__),G/'retry/terminal410_run.py',G/'retry/terminal410_model.py',G/'retry/terminal409_contract.py',G/'retry/source_vehicle_transition.py',G/'retry/cross404_common.py',G/'retry/fork394_run.py',G/'retry/loss389_replay.py',G/'retry/executor397.py',G/'retry/pace269_run.py',G/'env_wrapper.py',G/'damage.py',Path(p404['fixed_plan']),root/'stage404/profiles-private.json',root/'stage404/plan.json',root/'stage404/C_268/initial-private.json',root/'stage404/C_268/trace-private.jsonl',root/'stage404/O_268/trace-private.jsonl',root/'stage404/O_268/result.json',root/'stage408/trace-private.jsonl',root/'stage408/result.json',root/'stage410/result.json',root/'project-effective-budget-v430.json',root/'research-deadline-current.json']+list((G/'core').rglob('*.py'))
 p=dict(stage=411,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],case=p404['case'],fixed_plan=p404['fixed_plan'],native_cap=800,reset_cap=6,model_tick_cap=60000,world_cap=1200,CPU_cap_s=180,execution_wall_cap_s=300,max_parallel=1,per_policy_run_cap=308,gate_native_worst=184,gate_reset_cap=4,final_reserve_use=0,learning_SEALED_actor_paid_cap=0,H=13,goal_distance_m=3.24,goal_deadline_actions=13,recipes=['ownnominal','firstactionfloat32(0,0,.3) thenownnominal'],gate='ResetC target1 thenCpre91 target91, eachqueriedparentfollowedbyfreshunqueriedcontrol; originalprefixcommands/sensors exact404. Fullbeforecurrentstate/RNG/memory equalindependentcontrol. Before/afterqueryparentfullsnapshotandactualnominalmemory/RNGexact. Actualparentnominaloneaction vsfreshunqueriednominalaction/fullpost exact, firstforecast391. Firstfailurestopsallpolicyruns,no retry.',selection='Same410predicate: nominal13 twicefreshworld exactrepeat; ifvalid executecurrentactualnominal, elsepulse13 twicefreshworld andonlyifvalid executefixedfirstpulse. Queryphysicalstatecurrentactualsnapshot,memorybeforecurrentnominal; actualmemorycomputedonceandneveroverwrittenbybranchmemory/override. Aftereachactionquerynewactualstate. Noframe/arc/seedtrigger, no gain/horizon/pulsesearch.',milestone='Persistactualprogressgoal3.24 andintegerdeadline13; updateonlyafteractualgoalreached. Terminalofficialfinish countsgoal success; normal1-4rawtickterminal contract409. Loggoal/deadline andinterventions.',stops='Any liveparent/modelrestore/repeat/RNG/source/391/actionintegrityfailure globalstop. Bothrecipesinvalid/modelbudget/timecap ->censor,no fallbackclaim. Existing3m/collisiondamage/newobstacletouch/roadlossrawgrass/reverse/domain safety ->censor; firstnoncompletedpolicyrun stopsremaining; no retry/tuning. Chargebeforecalls retainunconfirmed.',readout='O/Ceachonceonceaftergate; Ocached40414.78sdamage0 andCfixedpulse40815.08sdamage0 historicalonly (408originalrawtickqualificationfailurepreserved). Perstepfirstpredictionvsactual391, fullparentimmutability, Oactionmemorypreservation, repeatedCinterventions/progress, officialfinish/DONE, queryCPU/wallmaxp95 andwholeCPU. GTknownN1diagnosticnotpixel296promotion/fallback/independentgeneralization.',sources={str(f):sha(f) for f in files},protected=p410['protected'],original408_preserve=p410['original408_preserve']);save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'preparation-result.json',dict(implementation_wall_s=time.time()-read(d/'preparation-opening.json')['epoch'],implementation_CPU_s=None,implementation_CPU_fully_measured=False,includes_reasoning_tool_latency=True,syntax_compiled=True,new_model_native_during_preparation=0));print(json.dumps(dict(registered=True,plan_sha256=sha(d/'plan.json'),caps={k:p[k] for k in ['native_cap','reset_cap','model_tick_cap','world_cap','CPU_cap_s','execution_wall_cap_s']})))
def run(root):
 d=root/'stage411';p=read(d/'plan.json');assert not(d/'opening.json').exists();assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 meter=Meter(d);save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(root/'stage404/profiles-private.json')['frozen268']);line=np.asarray(fixed['line']);L=sum(fixed['free_profile']['ds']);gate_results=[];results=[];failure=None;stage='live_parent_gate';status='RUNNING'
 def timeout(*args):raise ResourceStop('OSCPU180_wall300')
 sig={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM,signal.SIGXCPU]};resource.setrlimit(resource.RLIMIT_CPU,(179,180));signal.setitimer(signal.ITIMER_PROF,max(.01,178-time.process_time()));signal.setitimer(signal.ITIMER_REAL,299)
 oldC=[json.loads(s) for s in (root/'stage404/C_268/trace-private.jsonl').read_text().splitlines()];oldO=[json.loads(s) for s in (root/'stage404/O_268/trace-private.jsonl').read_text().splitlines()]
 try:
  for target,label in [(1,'reset'),(91,'Cpre91')]:
   reference=None
   for arm in ['queried','unqueried']:
    name='gate_'+label+'_'+arm;folder=d/name;folder.mkdir(mode=0o700);env=None;rows=[];observer=None;query_info=None
    try:
     env,obs,ctrl,initial=open_env(root,meter,name,fixed,pace,'C',p['case']);save(folder/'initial-private.json',initial);pairs=set(tuple(x) for x in initial['physical']['touching_obstacle_contacts']);observer=ForkTrace()
     for step in range(1,target+1):
      before=ctrl.memory();nominal=ctrl.act(env);h=oldC[step-1]
      if sensor(env)!=h['pre'] or nominal.tolist()!=h['command'] or before['index']!=h['memory_before']['index'] or before['laststeer']!=h['memory_before']['laststeer']:raise ModelFailure('gate_original_prefix_before')
      if step==target:
       boundary=complete_state(env,obs,dict(before=before,after=ctrl.memory(),nominal=nominal.tolist()));save(folder/'before-private.json',boundary)
       if arm=='queried':
        s=canonical_projection(line,sensor(env)['pos'],sensor(env)['vel'],ctrl.phase())['arc'];_,_,nominal_forecast,query_info=queried(meter,env,obs,ctrl,fixed,pace,'C',before,nominal,step-1,s,s+3.24,step-1+13,folder,str(step));afterquery=complete_state(env,obs,dict(before=before,after=ctrl.memory(),nominal=nominal.tolist()))
        if boundary!=afterquery:raise ModelFailure('gate_live_parent_boundary_changed')
       else:
        if boundary!=read(d/('gate_'+label+'_queried')/'before-private.json'):raise ModelFailure('gate_independent_before_mismatch')
      obs,row=actual_step(meter,name,env,obs,ctrl,nominal,line,0.,pairs,observer,step);rows.append(row);save(folder/'trace-private.json',rows)
      if row['post']!=h['post'] or row['collision']!=h['collision'] or row['damage']!=h['damage']:raise ModelFailure('gate_original_prefix_after')
      if row['safety']:raise SafetyStop(','.join(row['safety']))
     postfull=complete_state(env,obs,ctrl.memory());save(folder/'after-private.json',postfull)
     if arm=='queried':
      z=compare(nominal_forecast['rows'][0]['predicted'],rows[-1],rows[-1]['finish_time_s']);save(folder/'first-model-vs-actual.json',z)
      if not z['passed']:raise ModelFailure('gate_first_prediction_vs_live_actual')
      reference=dict(row=rows[-1],postfull=postfull)
     elif rows[-1]!=reference['row'] or postfull!=reference['postfull']:raise ModelFailure('gate_queried_vs_unqueried_fullpost_mismatch')
     rr=dict(gate=label,arm=arm,target=target,native=len(rows),query=query_info,passed=True,full_parent_unchanged=True if arm=='queried' else None,independent_unqueried_fullpost_exact=arm=='unqueried');gate_results.append(rr);save(folder/'result.json',rr)
    finally:
     if observer:observer.disable()
     if env:env.close()
   print(json.dumps(dict(stage=411,gate=label,passed=True,budget=meter.b)),flush=True)
  save(d/'live-parent-gate.json',dict(passed=True,records=gate_results));stage='policy_runs'
  for kind in ['O','C']:
   name='policy_'+kind;folder=d/name;folder.mkdir(mode=0o700);env=observer=journal=None;rows=[];queries=[];steps=0;runstatus='STARTED';runerror=None;progress=previous=goal=deadline=None;interventions=[];model_checks=[];goal_resets=0;history=[];initial=None;start_t=None;epicpu=time.process_time();epiwall=time.perf_counter();last_before=None
   try:
    env,obs,ctrl,initial=open_env(root,meter,name,fixed,pace,kind,p['case']);save(folder/'initial-private.json',initial);start_t=env.unwrapped.t;pairs=set(tuple(x) for x in initial['physical']['touching_obstacle_contacts']);observer=ForkTrace();journal=(folder/'trace-private.jsonl').open('x');(folder/'trace-private.jsonl').chmod(0o600)
    for step in range(1,309):
     meter.guard();before=ctrl.memory();last_before=before;nominal=ctrl.act(env);pre=sensor(env);qpre=canonical_projection(line,pre['pos'],pre['vel'],ctrl.phase());arc=qpre['arc']
     if progress is None:progress=arc;previous=arc
     if goal is None or progress>=goal:goal=progress+3.24;deadline=step-1+13;goal_resets+=1
     oldgoal=goal;olddeadline=deadline;oldprogress=progress
     command,chosen,nominal_forecast,latency=queried(meter,env,obs,ctrl,fixed,pace,kind,before,nominal,step-1,progress,goal,deadline,folder,str(step));queries.append(latency)
     if latency['selected_pulse']:interventions.append(step)
     nominal_memory=ctrl.memory();obs,row=actual_step(meter,name,env,obs,ctrl,command,line,0.,pairs,observer,step);steps+=1;postarc=row['post_projection']['arc'];progress+=(postarc-previous+L/2)%L-L/2;previous=postarc;reached=progress>=goal or row['completed'];check=compare(chosen['rows'][0]['predicted'],row,row['finish_time_s']);model_checks.append(check)
     if row['completed']:ctrl.done(env)
     hist=None
     if kind=='O' and step<=len(oldO):
      h=oldO[step-1];hist=dict(command=command.tolist()==h['command'],post=row['post']==h['post'],nominal_memory_before=before['index']==h['memory_before']['index'] and before['laststeer']==h['memory_before']['laststeer'],nominal_memory_after=nominal_memory['index']==h['memory_after']['index'] and nominal_memory['laststeer']==h['memory_after']['laststeer']);history.append(hist)
     row.update(nominal=nominal.tolist(),selected_pulse=latency['selected_pulse'],memory_before=before,nominal_memory_after=nominal_memory,actual_memory_after=ctrl.memory(),query_latency=latency,prediction_comparison=check,progress_before=oldprogress,progress_after=progress,goal_before=oldgoal,deadline_before=olddeadline,goal_hit_actual_step=reached,historical_O=hist);rows.append(row);journal.write(json.dumps(row,allow_nan=False)+'\n');journal.flush()
     if not check['passed']:raise ModelFailure('selected_first_transition391')
     if row['safety']:raise SafetyStop(','.join(row['safety']))
     if row['completed']:runstatus='COMPLETED_SAFE';break
     if row['ended']:runstatus='ACTUAL_DNF';break
     if row['truncated']:runstatus='ENV_CENSORED';break
     if len(rows)%30==0:print(json.dumps(dict(stage=411,policy=kind,actions=len(rows),pulses=interventions,budget=meter.b)),flush=True)
    else:runstatus='PER_ARM_CAP_CENSORED'
   except BaseException as e:
    runerror=type(e).__name__+': '+str(e);runstatus='SAFETY_CENSORED' if isinstance(e,SafetyStop) else 'INFEASIBLE_CENSORED' if isinstance(e,Infeasible) else 'RESOURCE_CENSORED' if isinstance(e,ResourceStop) else 'MODEL_OR_TECHNICAL_CENSORED';save(folder/'stop-private.json',dict(error=runerror,status=runstatus,traceback=traceback.format_exc(),memory_before=last_before))
   finally:
    if observer:observer.disable()
    if journal:journal.close()
    lap_ms=None
    if env:
     if env.unwrapped.finish_time_s is not None:lap_ms=round((env.unwrapped.finish_time_s-start_t)*1000)
     save(folder/'final-private.json',complete_state(env,obs,ctrl.memory()));env.close()
   rr=dict(policy=kind,status=runstatus,error=runerror,native_confirmed=len(rows),native_charged=meter.b['case_native'].get(name,0),unconfirmed_native=meter.b['case_native'].get(name,0)-len(rows),completed=runstatus=='COMPLETED_SAFE',lap_ms=lap_ms,damage=rows[-1]['damage'] if rows else None,max_path_error_m=max((z['post_projection']['path_error_m'] for z in rows),default=None),intervention_steps=interventions,intervention_count=len(interventions),query_count=len(queries),query_CPU_max_s=max((z['CPU_s'] for z in queries),default=None),query_CPU_p95_s=float(np.percentile([z['CPU_s'] for z in queries],95)) if queries else None,query_wall_max_s=max((z['wall_s'] for z in queries),default=None),query_wall_p95_s=float(np.percentile([z['wall_s'] for z in queries],95)) if queries else None,goal_resets=goal_resets,goal_step_hits=sum(z['goal_hit_actual_step'] for z in rows),model_check_rows=len(model_checks),model_all_pass=all(z['passed'] for z in model_checks),max_model_errors={k:max((z['errors'][k] for z in model_checks),default=0.) for k in ['speed_m_s','yaw_rate_rad_s','position_m','time_s']},O_historical_exact_rows=sum(all(z.values()) for z in history) if kind=='O' else None,O_historical_checked_rows=len(history) if kind=='O' else None,O_historical_preserved=kind=='O' and len(history)==185 and all(all(z.values()) for z in history) and not interventions,historical_O_lap_ms=14780,historical_C_fixed_pulse_lap_ms=15080,delta_vs_own_historical_ms=lap_ms-(14780 if kind=='O' else 15080) if lap_ms is not None else None,episode_CPU_s=time.process_time()-epicpu,episode_wall_s=time.perf_counter()-epiwall);save(folder/'result.json',rr);results.append(rr);print(json.dumps(rr),flush=True)
   if runstatus!='COMPLETED_SAFE':failure=dict(stage='policy_'+kind,error=runerror or runstatus);break
  status='COMPLETED_ONCE_ONLY_CLOSEDLOOP' if len(results)==2 and all(z['completed'] for z in results) else 'POLICY_CENSORED_STOP'
 except BaseException as e:
  failure=dict(stage=stage,error=type(e).__name__+': '+str(e));status='LIVE_GATE_OR_GLOBAL_STOP';save(d/'failure-private.json',dict(**failure,traceback=traceback.format_exc()))
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in sig.items():signal.signal(s,h)
  meter.persist()
 out=dict(stage=411,status=status,failure=failure,live_parent_gate_passed=(d/'live-parent-gate.json').exists(),gate_records=gate_results,policy_results=results,unexecuted_policies=[k for k in ['O','C'] if k not in [x['policy'] for x in results]],budget=meter.b,query_attempts=meter.queries,wholeworker_CPU_s=time.process_time(),new_actor_learning_SEALED_reserve_paid=0,GT_knownN1_diagnostic=True,pixel296_promotion=False,safe_fallback_validated=False);save(d/'result.json',out);print(json.dumps(dict(stage=411,status=status,failure=failure,budget=meter.b)),flush=True)
if __name__=='__main__':
 root=Path(sys.argv[2]);{'prepare':prepare,'run':run}[sys.argv[1]](root)
