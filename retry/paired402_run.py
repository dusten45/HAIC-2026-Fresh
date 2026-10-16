"""Once-only actual N1 paired profile test with a frozen401 model shadow."""
import datetime,hashlib,json,math,os,random,resource,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.loss389_replay import sensor
from retry.fork394_run import ForkTrace,complete_state
from retry.probe390_run import control_code
from retry.executor397 import CoherentExecutor,ExecutorDomainError,canonical_projection
from retry.pilot398_run import safety_flags,finish_dict,raw_capture_pairs
from retry.factorial401_run import sensor as model_sensor,metrics
G=Path(__file__).resolve().parent.parent
class SafetyStop(RuntimeError):pass
class FidelityStop(RuntimeError):pass
class SharedStop(RuntimeError):pass

def prepare(root):
 d=root/'stage402';assert not d.exists();d.mkdir(mode=0o700);b=read(root/'project-effective-budget-v421.json');assert b['research_remaining']==32072 and b['final_reserved_actions']==84000 and b['final_reserve_used']==0
 p398=read(root/'stage398/plan.json');fp=read(root/'stage401/factorial-plan.json');assert read(root/'stage401/factorial-result.json')['status']=='COMPLETED_MODEL_DIAGNOSTIC'
 files=[Path(__file__),G/'retry/executor397.py',G/'retry/pace265_run.py',G/'retry/factorial401_run.py',G/'retry/pilot398_run.py',G/'retry/probe390_run.py',G/'retry/fork394_run.py',G/'retry/source_vehicle_transition.py',G/'retry/loss389_replay.py',G/'retry/diagnose.py',G/'env_wrapper.py',G/'damage.py',root/'stage398/plan.json',root/'stage398/N1/initial-private.json',root/'stage398/N1/trace-private.jsonl',root/'stage401/factorial-plan.json',root/'stage401/factorial-result.json',root/'stage401/P15_C-rows-private.json',root/'stage401/P10_C-rows-private.json',Path(p398['fixed_plans']['N1']),root/'project-effective-budget-v421.json',root/'research-deadline-current.json']+list((G/'core').rglob('*.py'))
 p=dict(stage=402,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],arms=[dict(name='P15_C',pace=1.5,cap=160,model_actions=99,continue_full=False),dict(name='P10_C',pace=1.,cap=1040,model_actions=106,continue_full=True)],case=p398['cases']['N1'],initial_pixels=p398['initial_pixels']['N1'],fixed_plan=p398['fixed_plans']['N1'],controller_AST_sha256=p398['controller_AST_sha256'],target_arc=fp['target_arc'],native_cap=1200,reset_cap=2,model_tick_cap=820,model_world_cap=2,CPU_cap_s=180,wall_cap_s=300,max_parallel=1,actor_cap=0,learning_cap=0,SEALED_cap=0,reserve_use=0,research_before=32072,research_after_worst_case=30872,cost_basis='398N1wholeworker8.05285CPU/99wrapper=>97.61CPU/1200;180totalincludesrawtires/shadow820ticks/fullcapturemargin. 398CPU23.47/274 andwallreceipt14.92. 300wallhardcap,serialphysicsworkers1; no paidcompute.',policy='Exactly401C profile1.5/1.0 nodes, same CoherentExecutor source/intents/launch/gain/clamps/pedalmap andsame ownstatepursuit AST+memory. No J arms. Groundtruthfinishcurrentmetadata allowedonlyactual, no future. No commandreplayforcingactual, no retuning/retry/reselection.',model_shadow='Twofreshsourceworlds fromfrozen398initialsnapshot, no actualstatecorrection. Ownstate same401C law. Up to99/106actions,820ticks total. Beforeeachactualaction check independentlygeneratedmodelarc/patherror/absyaw/speed equal401storedvalues EXACT, then compareactualpost speed<=.5,yaw<=.05,posL2<=.1, collision/damage/contactedwheelcount exact391. Thisreconstructsmissingfullposition/signedyaw metadata only,notnewpolicyexperiment.',local_gate='Eachstep no safety/domain/technical/fidelityfailure. P10reachesfixed401failurearcwithdamage0,no collision/roadcontactloss/meaningfulreverse and all available106modelboundariesqualified; onlythenenablewholelapcontinuation IN SAME actualenv/controller/noreset. Ifarc reachedbefore106 waituntil106forqualification;no forcedtrajectory. Ifmodelmismatch stopallfutureactualcalls.',baseline_stop='P15stopatfirsttargetarc or160, withsafetyfailuretakingprecedence. No fullbaseline lap; modelhasno safecompletionclaim. Safetycase-local, otherfrozenarmcontinues; technical/source/fidelity/resource/deadline stopsall.',continuation='P10afterlocalgate continueunchangedtoofficialfinishorpredeclaredsafetydomain/native1040cap/actualtermination/truncation/resource/deadline. No modelclaimsafter106. Onlyfinish_time_s withforwardedgeclearanceofficialcompletion; lap=sourcecenterfinish_time_s-resetstart_t,notlaststep. Bothstatusanddamage/safetyreported.',safety='Same398 pre/postnearestpatherror>3m,damageincrease,newcollision/obstaclecontact,wheelroadloss/rawgrass,meaningfulbody/pathsigma<-.1. NegativeFIRST_LAPsigma strictdomainstop. Rawclippingobservednotnewveto. Nosafetythresholdrelaxation.',classification='Completion,actualenvDNF,environmentcensor,safetycensor,domaincensor,fidelitycensor,technical/resourcecensor separately. Targetarcnotfinish. Safe106localpassnotfull-lap/11simprovement/296promotion. No averagingcensoredtimeaslap.',record='Fullavailableinitialsnapshot+RNG+pixels/sourcehash exact398; firstlaunchaction/postmatch398 ifsamecommand. Everyactualpre/post+commands/memory/refs/rawtires and shadowfullpost/errors savedprivate. Finalcaptureonallnormal/safetystopswhenavailable.',sources={str(f):sha(f) for f in files},protected={str(f):sha(f) for f in [root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json']})
 save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');(d/'plan.sha256').chmod(0o600);save(d/'budget.json',dict(actions=0,resets=0,model_ticks=0,model_reserved=0,model_worlds=0,started_epoch=None,CPU_s=0.,case_actions={},finished=[]));print(json.dumps(dict(registered=True,plan_sha256=sha(d/'plan.json'),native_cap=1200,reset_cap=2,model_cap=820,CPU_cap=180,wall_cap=300)))

def run(root):
 from retry.diagnose import make_env
 from retry.source_vehicle_transition import SourceVehicleTransition
 d=root/'stage402';p=read(d/'plan.json');assert not(d/'opening.json').exists();assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
 for f,h in {**p['sources'],**p['protected']}.items():assert sha(f)==h,f
 save(d/'opening.json',dict(epoch=time.time(),pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));b=read(d/'budget.json');b['started_epoch']=time.time();save(d/'budget.json',b);cpu=time.process_time();results=[];shared=None;resource.setrlimit(resource.RLIMIT_CPU,(179,180))
 def timeout(*args):raise TimeoutError('402CPU180')
 oldsig=signal.signal(signal.SIGPROF,timeout);oldcpu=signal.signal(signal.SIGXCPU,timeout);signal.setitimer(signal.ITIMER_PROF,max(.01,178-time.process_time()))
 def guard():
  b['CPU_s']=time.process_time()-cpu;save(d/'budget.json',b)
  if b['CPU_s']>=180 or time.time()-b['started_epoch']>=300:raise TimeoutError('402resourcecap')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(p['deadline_utc']):raise TimeoutError('402deadline')
 def charge(kind,name):
  guard()
  if kind=='reset':assert b['resets']<2;b['resets']+=1
  else:assert b['actions']<1200;b['actions']+=1;b['case_actions'][name]=b['case_actions'].get(name,0)+1
  save(d/'budget.json',b)
 fixed=read(Path(p['fixed_plan']));line=np.asarray(fixed['line']);prof=fixed['free_profile'];ds=np.asarray(prof['ds']);sarc=np.r_[0,np.cumsum(ds)];code,astsha=control_code(G/'retry/pace265_run.py');assert astsha==p['controller_AST_sha256'];initial_stored=read(root/'stage398/N1/initial-private.json');oldfirst=__import__('json').loads((root/'stage398/N1/trace-private.jsonl').read_text().splitlines()[0])
 def scope_for(env,pace):return dict(line=line,vprof=np.asarray(prof['speed']),ds=ds,curvature=np.asarray(prof['curvature']),sarc=sarc,L=sarc[-1],model=fixed['model'],index=0,laststeer=0.,pace=pace,env=env)
 try:
  for arm in p['arms']:
   guard();name=arm['name'];folder=d/name;assert not folder.exists();folder.mkdir(mode=0o700);env=shadow=observer=None;journal=None;rows=[];steps=rawticks=resetticks=0;damage=maxerr=0.;status='STARTED';error=None;safety=[];completed=ended=truncated=False;info={};initial_exact=first_exact=False;local_pass=False;local_event=None;phase_events=[];predictions=[];epi_cpu=time.process_time();epi_wall=time.perf_counter();start_t=None
   try:
    random.seed(394);np.random.seed(394);policy=CoherentExecutor(fixed);policy.nodes=np.asarray(prof['speed'])*arm['pace'];env=make_env();charge('reset',name);obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});raw=env.unwrapped;start_t=float(raw.t);resetticks=round(raw.t*50);scope=scope_for(env,arm['pace']);initial=complete_state(env,obs,dict(index=0,laststeer=0.));save(folder/'initial-private.json',initial)
    assert initial==initial_stored and hashlib.sha256(obs.tobytes()).hexdigest()==p['initial_pixels'] and hashlib.sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest()==p['case']['road_geometry_sha256'];initial_exact=True;initial_damage=float(env.damage.damage);pairs=set(tuple(x) for x in initial['physical']['touching_obstacle_contacts'])
    guard();assert b['model_worlds']<2;b['model_worlds']+=1;save(d/'budget.json',b);shadow=SourceVehicleTransition(initial_stored['physical']);assert shadow.initial_bodies_exact and shadow.initial_tiles_exact and shadow.initial_progress_exact;spolicy=CoherentExecutor(fixed);spolicy.nodes=np.asarray(prof['speed'])*arm['pace'];sscope=scope_for(SimpleNamespace(unwrapped=shadow),arm['pace']);expected=read(root/f'stage401/{name}-rows-private.json');observer=ForkTrace();journal=(folder/'trace-private.jsonl').open('x');(folder/'trace-private.jsonl').chmod(0o600)
    for step in range(1,arm['cap']+1):
     guard();pre=sensor(env);memory_before=dict(index=int(scope['index']),laststeer=float(scope['laststeer']));exec(code,dict(np=np),scope);nominal=scope['action'];phase_before=policy.phase;command,ref=policy.act(pre,nominal,finish_dict(raw),scope['arc']);assert command is not None;memory_after=dict(index=int(scope['index']),laststeer=float(scope['laststeer']))
     if phase_before!=policy.phase:phase_events.append(dict(step=step,phase=policy.phase))
     qpre=ref['projection'];maxerr=max(maxerr,qpre['path_error_m']);why=safety_flags(pre,qpre,float(env.damage.damage),initial_damage)
     if why:safety=why;raise SafetyStop(','.join(why))
     pred=None;match=None;scommand=None
     if step<=arm['model_actions']:
      guard();sp=model_sensor(shadow,initial_stored['physical']['actual_time']+(step-1)*.08);exec(code,dict(np=np),sscope);scommand,sref=spolicy.act(sp,sscope['action'],{},sscope['arc']);assert b['model_reserved']+4<=820;b['model_reserved']+=4;save(d/'budget.json',b);before_shadow=shadow.native_ticks
      try:pred=shadow.step(scommand)
      finally:b['model_ticks']+=shadow.native_ticks-before_shadow;save(d/'budget.json',b)
      met=metrics(shadow,pred,line,spolicy.phase,0.,False);truth=expected[step-1];same=all(met[k]==truth[k] for k in ['arc','path_error','speed']) and met['abs_yaw']==truth['yaw_abs']
      if not same:raise SharedStop('Frozen401model_reconstruction_mismatch')
     observer.rows=[];observer.enable();charge('action',name);steps+=1;before=raw.t
     try:obs,_,ended,truncated,info=env.step(command)
     finally:observer.disable()
     rt=round((raw.t-before)*50);rawticks+=rt;post=sensor(env);damage=float(env.damage.damage);assert len(observer.rows)==4*rt;qp=canonical_projection(line,post['pos'],post['vel'],policy.phase);maxerr=max(maxerr,qp['path_error_m']);why=safety_flags(post,qp,damage,initial_damage,bool(info['collision']),bool(set(tuple(x) for x in raw_capture_pairs(env))-pairs),any(s['grass'] for s in observer.rows));completed=raw.finish_time_s is not None
     if pred is not None:
      errs=dict(speed_m_s=abs(pred['speed_m_s']-post['speed']),yaw_rate_rad_s=abs(pred['angular_velocity']-post['yaw']),position_m=float(np.linalg.norm(np.asarray(pred['position'])-post['pos'])));discrete=dict(collision=pred['collision']==bool(info['collision']),damage=pred['damage']==damage,wheel_road_contacts=pred['wheel_road_contacts']==sum(n>0 for n in post['road_contacts']));match=dict(errors=errs,discrete=discrete,passed=errs['speed_m_s']<=.5 and errs['yaw_rate_rad_s']<=.05 and errs['position_m']<=.1 and all(discrete.values()),command_equal=command.tolist()==scommand.tolist());predictions.append(match)
     row=dict(step=step,pre=pre,post=post,command=command.tolist(),nominal=nominal.tolist(),memory_before=memory_before,memory_after=memory_after,reference=ref,post_projection=qp,raw_ticks=rt,raw_tire_samples=observer.rows.copy(),collision=bool(info['collision']),damage=damage,completed=completed,ended=bool(ended),truncated=bool(truncated),retire_reason=info.get('retire_reason'),model_post=pred,model_match=match);rows.append(row);journal.write(json.dumps(row,allow_nan=False)+'\n');journal.flush()
     if step==1:first_exact=command.tolist()==oldfirst['command'] and post==oldfirst['post'];assert first_exact
     if match is not None and not match['passed']:raise FidelityStop('Model_actual_boundary_mismatch')
     if why:safety=why;raise SafetyStop(','.join(why))
     if completed:
      policy.mark_done(finish_dict(raw),raw.t);status='COMPLETED';phase_events.append(dict(step=step,phase='DONE'));break
     if ended:status='ACTUAL_DNF';break
     if truncated:status='ENV_CENSORED';break
     if qp['arc']>=p['target_arc'] and step>=arm['model_actions'] and not local_pass:
      local_pass=True;local_event=dict(step=step,elapsed_interval_s=[pre['time']-start_t,post['time']-start_t],max_path_error_m=maxerr,shadow_boundaries_qualified=len(predictions));save(folder/'local-gate.json',local_event)
      if not arm['continue_full']:status='LOCAL_TARGET_REACHED';break
    else:status='NATIVE_CAP_CENSORED'
   except BaseException as e:
    error=type(e).__name__+': '+str(e)
    if isinstance(e,SafetyStop):status='SAFETY_STOP_CENSORED'
    elif isinstance(e,ExecutorDomainError):status='DOMAIN_STOP_CENSORED'
    elif isinstance(e,FidelityStop):status='FIDELITY_STOP_CENSORED';shared=error
    elif isinstance(e,TimeoutError):status='RESOURCE_CENSORED';shared=error
    else:status='TECHNICAL_STOP_CENSORED';shared=error
    save(folder/'stop-private.json',dict(status=status,error=error,traceback=traceback.format_exc()))
   finally:
    if observer:observer.disable()
    if journal:journal.close()
    if env:
     try:save(folder/'final-full-private.json',complete_state(env,obs,dict(index=int(scope['index']),laststeer=float(scope['laststeer']))))
     except BaseException as capture_error:save(folder/'final-capture-error.json',dict(error=str(capture_error)))
     lap=round((raw.finish_time_s-start_t)*1000) if completed else None;env.close()
    else:lap=None
    if shadow:shadow.close()
   result=dict(arm=name,pace=arm['pace'],status=status,completed=completed,actual_DNF=bool(ended and not completed),censored=bool(not completed and not ended),lap_ms=lap,retire_reason=info.get('retire_reason'),stop_reason=error,safety=safety,local_gate_passed=local_pass,local_event=local_event,native=steps,raw_ticks=rawticks,reset_ticks=resetticks,damage=damage,max_path_error_m=maxerr,initial_exact=initial_exact,first_launch_exact=first_exact,phase_events=phase_events,model_compared_actions=len(predictions),all_model_boundaries_qualified=all(z['passed'] for z in predictions),max_model_errors={k:max([z['errors'][k] for z in predictions] or [0.]) for k in ['speed_m_s','yaw_rate_rad_s','position_m']},model_command_difference_count=sum(not z['command_equal'] for z in predictions),unconfirmed_charged_native=steps-len(rows),episode_CPU_s=time.process_time()-epi_cpu,episode_wall_s=time.perf_counter()-epi_wall)
   save(folder/'result.json',result);results.append(result);b['finished'].append(name);save(d/'budget.json',b);print(json.dumps(result,ensure_ascii=False),flush=True)
   if shared:break
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.signal(signal.SIGPROF,oldsig);signal.signal(signal.SIGXCPU,oldcpu);b['CPU_s']=time.process_time()-cpu;b['wall_s']=time.time()-b['started_epoch'];save(d/'budget.json',b)
 result=dict(stage=402,results=results,shared_stop=shared,unexecuted_arms=[a['name'] for a in p['arms'] if a['name'] not in [r['arm'] for r in results]],budget=b,new_actor_calls=0,new_learning_fits=0,new_SEALED_queries=0,new_paid_resources=0,wholeworker_CPU_s=time.process_time(),actual_environment=True);save(d/'result.json',result);print(json.dumps(dict(stage=402,budget=b,shared_stop=shared),ensure_ascii=False))
if __name__=='__main__':
 root=Path(sys.argv[2]);(prepare if sys.argv[1]=='prepare' else run)(root)
