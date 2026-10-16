"""Once-only actual paired pulse, frozen406 candidate; no new model integration."""
import datetime,hashlib,json,os,random,resource,signal,sys,time,traceback
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.cross404_common import G,scope_for,executor,multipliers,control_code
from retry.loss389_replay import sensor
from retry.fork394_run import ForkTrace,complete_state
from retry.executor397 import canonical_projection,ExecutorDomainError
from retry.pilot398_run import safety_flags,finish_dict,raw_capture_pairs

class QualificationFailure(RuntimeError):pass
class SafetyStop(RuntimeError):pass

def cmem(policy):
 return {k:getattr(policy,k) for k in ['phase','previous_arc','s','last_time','launch_commanded']}

def compare(pred,row):
 a=row['post']; errors=dict(speed_m_s=abs(pred['speed_m_s']-a['speed']),yaw_rate_rad_s=abs(pred['angular_velocity']-a['yaw']),position_m=float(np.linalg.norm(np.asarray(pred['position'])-a['pos'])));discrete=dict(collision=pred['collision']==row['collision'],damage=pred['damage']==row['damage'],wheel_road_contacts=pred['wheel_road_contacts']==sum(n>0 for n in a['road_contacts']))
 return dict(errors=errors,discrete=discrete,passed=errors['speed_m_s']<=.5 and errors['yaw_rate_rad_s']<=.05 and errors['position_m']<=.1 and all(discrete.values()))

def prepare(root):
 d=root/'stage407';assert not d.exists();v=read(root/'project-effective-budget-v426.json');assert (v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(31291,84000,0)
 old=read(root/'stage404/plan.json');rp=read(root/'stage406/plan.json')
 for p in [old,rp]:
  for f,h in {**p['sources'],**p['protected']}.items():assert sha(f)==h,f
 forecasts=read(root/'stage406/candidate-forecasts-private.json');q=next(z for z in forecasts if z['state']=='C268_pre91' and z['decision']==0)['forecasts'];assert q['5']['valid'] and not q['0']['valid'];pulse=np.asarray([0,0,.3],np.float32).tolist();assert q['5']['actions'][0]==pulse
 trace=[json.loads(s) for s in (root/'stage404/C_268/trace-private.jsonl').read_text().splitlines()];assert len(trace)==103
 sources=dict(old['sources']);paths=[Path(__file__),root/'stage406/plan.json',root/'stage406/result.json',root/'stage406/candidate-forecasts-private.json',root/'stage406/next-actual-proposal.json',root/'stage404/C_268/trace-private.jsonl',root/'stage404/C_268/result.json',root/'project-effective-budget-v426.json',root/'research-deadline-current.json']
 sources.update({str(f):sha(f) for f in paths});d.mkdir(mode=0o700)
 p=dict(stage=407,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],case=old['case'],initial_pixels=old['initial_pixels'],fixed_plan=old['fixed_plan'],coefficient_source=old['coefficient_source'],arms=['baseline_C268','pulse_C268'],native_cap=228,per_arm_cap=114,prefix=90,suffix_cap=24,reset_cap=2,CPU_cap_s=60,wall_cap_s=120,max_parallel=1,model_actor_learning_SEALED_paid_reserve_cap=0,pulse=pulse,pulse_step=91,reference_slots={'baseline_C268':'0','pulse_C268':'5'},reference_actions=13,original_failure_arc=trace[-1]['post_projection']['arc'],original_failure_time=trace[-1]['post']['time'],cost_basis='404 C103 actions CPU9.475s ->228 about21s; CPU60/wall120 includes two reset/fullfork/rawtire/compare margin; no paid compute.',selection='Already selected406 slot5, no online selector/new candidate/gain/horizon/retry. Prefix original closed-loop C268; step91 onlypulsearm overrides to float32(0,0,.3); all nominal memory updates unchanged includinglaststeer. Step92on unchanged C268 own actual state. Future actual/state/commands never enter controller.',qualification='Both initial full available state/RNG/pixels equal402; prefix90 pre/post sensors/nominal/commands/memory/reference/outcomes exactly404. Atpre91 both new full available fork/RNG/pixels/controller before+after exactlyequal; archive404 has no fullmidfork capture. Base all available103rows replay exact404. Any source/prefix/fork/fidelity/technical/resource/deadline failure stopsremaining globally; no retry.',fidelity='Eachof13suffixrows compare sealed406 chosen firstforecast391: speed<=.5m/s,yaw<=.05rad/s,position<=.1m,collision/damage/roadcontactwheelcount exact. Record command differences, notforceforecastactions. Firstfailglobalstop.',safety='Original398/404 path>3m,newcollision/obstacletouch,damageincrease,roadloss/rawgrass,meaningfulreverse/domain stop arm. Expectedbaseline safety allowed pulsearm, notDNF. Safety violation at targetarc cannotcountrecovery.',endpoint='Record first originalfailurearc crossing separately; safecontinue at least13suffix ifpossible, thenstopatfirstcrossing; suffixmax24/total114. Notreached=>CAP_CENSORED notrescue; reachedsafe=>localcommonarc evidence witharrivaldelay/overshoot, nolap/296promotion.',readout='Modelvsactual localstate/family outcome/rank onlytwofrozenarms. Signedprogress score same406goal; unsafe score noteligible. Pairwise response atmatched steps. No claimamong3brake steering candidates or suffixbenefit.13safe withoutcommonarc notrescue. Posthoc knownDEVcase notgeneralization.',research_before=31291,research_after_worst_case=31063,reserve=84000,reserve_used=0,sources=sources,protected=old['protected'])
 save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');(d/'plan.sha256').chmod(0o600);save(d/'budget.json',dict(actions=0,resets=0,case_actions={},CPU_s=0,wall_s=0));save(d/'qualification.json',dict(passed=True,static_only=True,source_hashes_exact=True,pulse_matches_frozen406=True,no_native_yet=True));print(json.dumps(dict(registered=True,plan_sha256=sha(d/'plan.json'),native_cap=228,reset_cap=2,CPU_cap_s=60,wall_cap_s=120)))

def run(root):
 from retry.diagnose import make_env
 d=root/'stage407';p=read(d/'plan.json');assert not(d/'opening.json').exists() and read(d/'qualification.json')['passed'];assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
 for f,h in {**p['sources'],**p['protected']}.items():assert sha(f)==h,f
 cpu=time.process_time();wall=time.perf_counter();save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));b=read(d/'budget.json');results=[];shared=None
 def persist():b.update(CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall);save(d/'budget.json',b)
 def guard():
  persist()
  if b['CPU_s']>=60 or b['wall_s']>=120:raise TimeoutError('407resourcecap')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')):raise TimeoutError('407deadline')
 def charge(kind,name):
  guard()
  if kind=='reset':assert b['resets']<2;b['resets']+=1
  else:assert b['actions']<228 and b['case_actions'].get(name,0)<114;b['actions']+=1;b['case_actions'][name]=b['case_actions'].get(name,0)+1
  persist()
 def timeout(*args):raise TimeoutError('407OSresourcecap')
 oldsig={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM,signal.SIGXCPU]};resource.setrlimit(resource.RLIMIT_CPU,(int(time.process_time())+61,int(time.process_time())+62));signal.setitimer(signal.ITIMER_PROF,59);signal.setitimer(signal.ITIMER_REAL,119)
 fixed=read(Path(p['fixed_plan']));line=np.asarray(fixed['line']);coef=read(Path(p['coefficient_source']));pace=multipliers(coef['coefficients'],fixed['free_profile']['curvature'],fixed['free_profile']['ds'],fixed['model']);code,_=control_code(G/'retry/pace269_run.py');old=[json.loads(s) for s in (root/'stage404/C_268/trace-private.jsonl').read_text().splitlines()];forecasts=next(z for z in read(root/'stage406/candidate-forecasts-private.json') if z['state']=='C268_pre91' and z['decision']==0)['forecasts']
 try:
  for name in p['arms']:
   f=d/name;assert not f.exists();f.mkdir(mode=0o700);env=observer=journal=None;rows=[];checks=[];steps=ticks=reset=prefixmatched=historical=0;status='STARTED';error=None;safety=[];maxerr=0.;initial_exact=fork_exact=False;firstcross=None;ended=truncated=False;epicpu=time.process_time();epiwall=time.perf_counter()
   try:
    guard();random.seed(394);np.random.seed(394);env=make_env();charge('reset',name);obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});raw=env.unwrapped;reset=round(raw.t*50);scope=scope_for(env,fixed,pace);policy=executor(fixed,pace);initial=complete_state(env,obs,dict(index=0,laststeer=0.));save(f/'initial-private.json',initial)
    if initial!=read(root/'stage402/P10_C/initial-private.json') or hashlib.sha256(obs.tobytes()).hexdigest()!=p['initial_pixels'] or hashlib.sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest()!=p['case']['road_geometry_sha256']:raise QualificationFailure('initial402')
    initial_exact=True;initial_damage=float(env.damage.damage);initial_pairs=set(tuple(x) for x in initial['physical']['touching_obstacle_contacts']);observer=ForkTrace();journal=(f/'trace-private.jsonl').open('x');(f/'trace-private.jsonl').chmod(0o600)
    for step in range(1,115):
     guard();pre=sensor(env);memory_before=dict(index=int(scope['index']),laststeer=float(scope['laststeer']));cb=cmem(policy);exec(code,dict(np=np),scope);nominal=scope['action'];memory_after=dict(index=int(scope['index']),laststeer=float(scope['laststeer']));command,ref=policy.act(pre,nominal,finish_dict(raw),scope['arc']);ca=cmem(policy)
     if command is None:raise QualificationFailure('unexpectedDONE')
     if step<=91:
      h=old[step-1]
      if not(pre==h['pre'] and nominal.tolist()==h['nominal'] and command.tolist()==h['command'] and memory_before==h['memory_before'] and memory_after==h['memory_after'] and all(ref[k]==h['reference'][k] for k in ref)):raise QualificationFailure('prefix_pre_command_memory_reference_'+str(step))
     if step==91:
      fork=complete_state(env,obs,dict(before=memory_before,after=memory_after,Cbefore=cb,Cafter=ca,nominal_command=command.tolist()));save(f/'fork-private.json',fork)
      if name=='pulse_C268' and fork!=read(d/'baseline_C268/fork-private.json'):raise QualificationFailure('twofreshfullfork')
      fork_exact=True
      if name=='pulse_C268':command=np.asarray(p['pulse'],np.float32)
     qpre=ref['projection'];why=safety_flags(pre,qpre,float(env.damage.damage),initial_damage)
     if why:safety=why;raise SafetyStop(','.join(why))
     if not(np.isfinite(command).all() and np.all(command>=np.array([-.4,0,0],np.float32)) and np.all(command<=np.array([.4,1,1],np.float32))):raise QualificationFailure('actiondomain')
     observer.rows=[];observer.enable();charge('action',name);steps+=1;before=raw.t
     try:obs,_,ended,truncated,info=env.step(command)
     finally:observer.disable()
     rt=round((raw.t-before)*50);ticks+=rt;post=sensor(env);damage=float(env.damage.damage);qp=canonical_projection(line,post['pos'],post['vel'],policy.phase);maxerr=max(maxerr,qp['path_error_m']);why=safety_flags(post,qp,damage,initial_damage,bool(info['collision']),bool(set(tuple(x) for x in raw_capture_pairs(env))-initial_pairs),any(z['grass'] for z in observer.rows))
     row=dict(step=step,pre=pre,post=post,command=command.tolist(),nominal=nominal.tolist(),memory_before=memory_before,memory_after=memory_after,Cbefore=cb,Cafter=ca,reference=ref,post_projection=qp,raw_ticks=rt,raw_tire_samples=observer.rows.copy(),collision=bool(info['collision']),damage=damage,ended=bool(ended),truncated=bool(truncated),safety=why);rows.append(row);journal.write(json.dumps(row,allow_nan=False)+'\n');journal.flush()
     if rt!=4 or len(observer.rows)!=16:raise QualificationFailure('rawtickshape')
     if step<=90 or name=='baseline_C268':
      h=old[step-1]
      if not(post==h['post'] and command.tolist()==h['command'] and row['collision']==h['collision'] and damage==h['damage']):raise QualificationFailure('archived_actual_post_'+str(step))
      historical+=1
      if step<=90:prefixmatched+=1
     if 91<=step<=103:
      fc=forecasts[p['reference_slots'][name]];comparison=compare(fc['rows'][step-91]['predicted'],row);comparison.update(step=step,command_abs_delta=[abs(a-c) for a,c in zip(command,fc['actions'][step-91])]);checks.append(comparison);save(f/'fidelity-private.json',checks)
      if not comparison['passed']:raise QualificationFailure('391fidelity_'+str(step))
     if firstcross is None and qp['arc']>=p['original_failure_arc']:firstcross=dict(step=step,time=post['time'],overshoot_m=qp['arc']-p['original_failure_arc'],safe=not why)
     if why:safety=why;raise SafetyStop(','.join(why))
     if ended or truncated:status='ENV_TERMINAL_CENSORED';break
     if step>=103 and firstcross is not None:status='SAFE_COMMON_ARC_REACHED';break
    else:status='SUFFIX_CAP_CENSORED'
   except BaseException as e:
    error=type(e).__name__+': '+str(e)
    if isinstance(e,SafetyStop):status='SAFETY_STOP_CENSORED'
    elif isinstance(e,ExecutorDomainError):status='DOMAIN_STOP_CENSORED'
    else:status='RESOURCE_STOP_CENSORED' if isinstance(e,TimeoutError) else 'QUALIFICATION_OR_TECHNICAL_STOP';shared=error
    if steps<91 or name=='baseline_C268' and (steps!=103 or len(checks)!=13 or status!='SAFETY_STOP_CENSORED' or 'path_error_over3m' not in safety):shared=shared or 'Unexpected_prefix_or_baseline_stop:'+error
    save(f/'stop-private.json',dict(status=status,error=error,traceback=traceback.format_exc()))
   finally:
    if observer:observer.disable()
    if journal:journal.close()
    if env:
     try:save(f/'final-full-private.json',complete_state(env,obs,dict(index=int(scope['index']),laststeer=float(scope['laststeer']),C=cmem(policy))))
     except BaseException as e:save(f/'capture-error.json',dict(error=str(e)));shared=shared or 'final_capture_failure'
     env.close()
   rr=dict(arm=name,status=status,error=error,safety=safety,native=steps,raw_ticks=ticks,reset_ticks=reset,confirmed_rows=len(rows),unconfirmed_charged_native=steps-len(rows),initial_exact=initial_exact,fork_qualified=fork_exact,prefix_exact_rows=prefixmatched,historical_exact_rows=historical,fidelity_rows=len(checks),fidelity_all_pass=all(z['passed'] for z in checks) and len(checks)==13,max_fidelity_errors={k:max((z['errors'][k] for z in checks),default=0.) for k in ['speed_m_s','yaw_rate_rad_s','position_m']},max_command_abs_delta=[max((z['command_abs_delta'][k] for z in checks),default=0.) for k in range(3)],max_path_error_m=maxerr,damage=rows[-1]['damage'] if rows else None,last_arc=rows[-1]['post_projection']['arc'] if rows else None,first_common_arc_crossing=firstcross,actual_DNF=bool(ended),truncated=bool(truncated),episode_CPU_s=time.process_time()-epicpu,episode_wall_s=time.perf_counter()-epiwall);save(f/'result.json',rr);results.append(rr);print(json.dumps(rr),flush=True)
   if shared:break
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in oldsig.items():signal.signal(s,h)
  persist()
 out=dict(stage=407,results=results,shared_stop=shared,unexecuted_arms=[a for a in p['arms'] if a not in [z['arm'] for z in results]],budget=b,wholeworker_CPU_s=time.process_time(),new_model_actor_learning_SEALED_paid_reserve=0);save(d/'result.json',out);print(json.dumps(dict(stage=407,budget=b,shared_stop=shared)),flush=True)

if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
