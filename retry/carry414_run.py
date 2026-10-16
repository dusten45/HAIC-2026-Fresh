"""Once-only fixed known-time GT pulse carry test, no new source predictions."""
import copy,datetime,json,os,random,resource,signal,sys,time,traceback
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.cross404_common import G
from retry.fork394_run import complete_state
from retry.closed411_run import ActualController
from retry.headroom413_run import Trace,metrics,row_fidelity
from retry.loss389_replay import sensor
from retry.pilot398_run import safety_flags,raw_capture_pairs
from retry.executor397 import canonical_projection
from retry.terminal409_contract import validate

class Stop(RuntimeError):pass
class SafetyStop(Stop):pass
class ReproductionStop(Stop):pass

def prepare(root):
 d=root/'stage414';assert not(d/'plan.json').exists();v=read(root/'project-effective-budget-v433.json');assert (v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(30076,84000,0);r=read(root/'stage413/result.json');assert r['promote_to_next_GT'] and r['status']=='COMPLETED_ACTUAL_PAIRED_DIAGNOSTIC';old=read(root/'stage413/plan.json');p404=read(root/'stage404/plan.json')
 for f,h in {**old['sources'],**old['protected'],**old['original408_preserve']}.items():assert sha(f)==h,f
 files=[Path(__file__),G/'retry/headroom413_run.py',G/'retry/closed411_run.py',G/'retry/terminal409_contract.py',G/'retry/executor397.py',G/'retry/pace269_run.py',G/'retry/cross404_common.py',G/'retry/fork394_run.py',G/'retry/loss389_replay.py',G/'retry/pilot398_run.py',G/'env_wrapper.py',G/'damage.py',root/'stage404/plan.json',root/'stage404/profiles-private.json',Path(p404['fixed_plan']),root/'stage404/O_268/trace-private.jsonl',root/'stage404/O_268/result.json',root/'stage404/O_268/final-full-private.json',root/'stage413/actual_A/trace-private.jsonl',root/'stage413/actual_B/trace-private.jsonl',root/'stage413/actual_B/initial-private.json',root/'stage413/actual_B/fork-private.json',root/'stage413/B1-private.json',root/'stage413/result.json',root/'stage413/source-anchor-private.json',root/'project-effective-budget-v433.json',root/'research-deadline-current.json']+list((G/'core').rglob('*.py'))
 p=dict(stage=414,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],case=p404['case'],fixed_plan=p404['fixed_plan'],native_cap=310,reset_cap=1,CPU_cap_s=60,execution_wall_cap_s=120,max_parallel=1,new_model_actor_learning_SEALED_reserve_paid_cap=0,intervention_step=117,prefix_actions=116,validated_suffix_actions=13,control='Fixed known-time diagnostic: oldO268prefix116, at117onlynominalsteer gas1brake0, then unchanged O268ownactualfeedback toofficialfinish/safetystop/cap. No statebaseddeploymentclaim/newpulse/timing/gain/horizon/search/retry; branchmemorynevercommitted.',qualification='Initialfull/RNG/pixels andpre117fullfork+controllerbeforeafter exactly413B. First116prefix and117-129suffix allsharedrowfields includingrawhull/tires/memory exactly413B; compare existing413B1sourceforecast117-129 body/wheel/hull only,no newforecast. Firstfailurestopwholeepisode. Beyond129 source-longfidelityunvalidated.',safety='Same413 raw/postoriginalpath3m,damageincrease,newcollision/obstaclecontact,roadloss/rawgrass,meaningfulreverse/domain. Actualprogressgoal3.24deadline13persistuntilrealgoalhit; officialfinishcountsgoal. Firstfailure/cap=>censor,no lapimputation. Normalterminal1-4rawtickcontract409.',readout='Officialfinish relative-resetstart, damage/maxpost+rawpatherror/braking/clip/slip. Compare cachedO14.78s viaoriginalreferencearccrossingbrackets, notframepositions. Baseline raw413A through129 verifiedequalO; after129 only404Owrapperboundaries, resolution explicit. Fixed10%-90%L,H1exit+30m,413B13endpoint milestones plusallbaselinepostboundaryarcsafterfork forcarryprofile, originalarc10equalbins; sequentialunwrap, stop/reverse/revisitseparate. Sameprogresscrossing notsamepose/velocity; no interpolatedarrival/virtualreferenceclock.',reference_O_lap_ms=14780,goal_distance_m=3.24,deadline_actions=13,sources={str(f):sha(f) for f in files},protected=old['protected'],original408_preserve=old['original408_preserve']);save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'preparation-result.json',dict(implementation_wall_s=time.time()-read(d/'preparation-opening.json')['epoch'],implementation_CPU_s=None,implementation_CPU_fully_measured=False,reasoning_tools_included=True,syntax_compiled=True,new_native_model_during_preparation=0));print(json.dumps(dict(registered=True,plan_sha256=sha(d/'plan.json'),native_cap=310,resets=1,CPU_cap_s=60,execution_wall_cap_s=120)))

def run(root):
 from retry.diagnose import make_env
 d=root/'stage414';p=read(d/'plan.json');assert not(d/'opening.json').exists() and sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 cpu=time.process_time();wall=time.perf_counter();save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));b=dict(actions=0,resets=0,CPU_s=0.,wall_s=0.)
 def persist():b.update(CPU_s=time.process_time()-cpu,wholeprocess_CPU_s=time.process_time(),wall_s=time.perf_counter()-wall);save(d/'budget.json',b)
 def guard():
  persist()
  if time.process_time()>=60 or b['wall_s']>=120:raise Stop('CPU60_wall120')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')):raise Stop('deadline')
 def charge(kind):
  guard();key='resets' if kind=='reset' else 'actions';cap=1 if key=='resets' else 310
  if b[key]>=cap:raise Stop('callcap')
  b[key]+=1;persist()
 def timeout(*a):raise Stop('OSresourcecap')
 sig={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM,signal.SIGXCPU]};resource.setrlimit(resource.RLIMIT_CPU,(59,60));signal.setitimer(signal.ITIMER_PROF,max(.01,58-time.process_time()));signal.setitimer(signal.ITIMER_REAL,119)
 env=observer=journal=obs=ctrl=None;rows=[];checks=[];status='STARTED';error=None;initial_exact=fork_exact=False;reproduced_prefix=reproduced_suffix=0;reset_ticks=0;completed=ended=truncated=False;info={};start_t=None;progress=previous=goal=deadline=None;goal_resets=0;telemetry=None
 try:
  fixed=read(Path(p['fixed_plan']));line=np.asarray(fixed['line']);L=sum(fixed['free_profile']['ds']);pace=np.asarray(read(root/'stage404/profiles-private.json')['frozen268']);reference=[json.loads(s) for s in (root/'stage413/actual_B/trace-private.jsonl').read_text().splitlines()];sealed=read(root/'stage413/B1-private.json');random.seed(394);np.random.seed(394);env=make_env();charge('reset');obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});ctrl=ActualController(env,fixed,pace,'O');initial=complete_state(env,obs,dict(index=0,laststeer=0.));save(d/'initial-private.json',initial)
  if initial!=read(root/'stage413/actual_B/initial-private.json'):raise ReproductionStop('initial_full_RNG_pixels')
  initial_exact=True;start_t=env.unwrapped.t;reset_ticks=round(start_t*50);pairs=set(tuple(z) for z in initial['physical']['touching_obstacle_contacts']);observer=Trace(lambda:env.unwrapped.t);journal=(d/'trace-private.jsonl').open('x');(d/'trace-private.jsonl').chmod(0o600)
  for step in range(1,311):
   guard();before=ctrl.memory();nominal=ctrl.act(env);pre=sensor(env);qpre=canonical_projection(line,pre['pos'],pre['vel'],'FIRST_LAP');arc=qpre['arc']
   if progress is None:progress=arc;previous=arc
   if goal is None or progress>=goal:goal=progress+3.24;deadline=step-1+13;goal_resets+=1
   oldprogress=progress;oldgoal=goal;olddeadline=deadline;a=nominal.copy()
   if step==117:
    fork=complete_state(env,obs,dict(before=before,after=ctrl.memory(),nominal=nominal.tolist()));save(d/'fork-private.json',fork)
    if fork!=read(root/'stage413/actual_B/fork-private.json'):raise ReproductionStop('fullfork_before_pulse')
    fork_exact=True;a[1:]=[1.,0.]
   why=safety_flags(pre,qpre,float(env.damage.damage),0.)
   if why:raise SafetyStop('pre:'+','.join(why))
   observer.reset();observer.enable();charge('action');t=env.unwrapped.t
   try:obs,_,ended,truncated,info=env.step(a)
   finally:observer.disable()
   post=sensor(env);q=dict(position=post['pos'],velocity=post['vel'],angle=post['angle'],speed_m_s=post['speed'],damage=float(env.damage.damage),collision=bool(info['collision']),wheel_road_contacts=sum(n>0 for n in post['road_contacts']));qp,why=metrics(q,observer.rows,observer.hulls,line,'FIRST_LAP')
   if set(tuple(z) for z in raw_capture_pairs(env))-pairs:why.append('new_obstacle_contact')
   completed=env.unwrapped.finish_time_s is not None;progress+=(qp['arc']-previous+L/2)%L-L/2;previous=qp['arc'];hit=progress>=goal or completed
   row=dict(step=step,pre=pre,post=post,nominal=nominal.tolist(),command=a.tolist(),memory_before=before,nominal_memory_after=ctrl.memory(),raw_ticks=round((env.unwrapped.t-t)*50),raw_tire_samples=copy.deepcopy(observer.rows),raw_hull=copy.deepcopy(observer.hulls),post_projection=qp,collision=bool(info['collision']),damage=float(env.damage.damage),completed=completed,finish_time_s=env.unwrapped.finish_time_s,ended=bool(ended),truncated=bool(truncated),safety=why,cursor=dict(index=int(ctrl.scope['index']),u=float(ctrl.scope['u']),target=float(ctrl.scope['desired']),feed=float(ctrl.scope['feed']),clamped_accel=float(ctrl.scope['acc'])),progress_before=oldprogress,progress_after=progress,goal_before=oldgoal,deadline_before=olddeadline,goal_hit_actual_step=hit)
   rows.append(row);journal.write(json.dumps(row,allow_nan=False)+'\n');journal.flush()
   if not validate(row)['passed']:raise ReproductionStop('normal_partial_measurement:'+json.dumps(validate(row)))
   if step<=129:
    if not all(row[k]==reference[step-1][k] for k in reference[step-1]):raise ReproductionStop('413_exact_record_'+str(step))
    if step<=116:reproduced_prefix+=1
    else:
     reproduced_suffix+=1;z=row_fidelity(sealed['rows'][step-117],row);checks.append(z);save(d/'existing13-model-fidelity.json',checks)
     if not z['passed']:raise ReproductionStop('existing13_body_wheel_hull_'+str(step))
   if why:raise SafetyStop(','.join(why))
   if step>=deadline and not hit:raise SafetyStop('actual_progress_deadline')
   if completed:ctrl.done(env);status='COMPLETED_SAFE';break
   if ended:status='ACTUAL_DNF';break
   if truncated:status='ENV_CENSORED';break
   if step%40==0:print(json.dumps(dict(stage=414,actions=step,budget=b)),flush=True)
  else:status='NATIVE_CAP_CENSORED'
 except BaseException as e:
  error=type(e).__name__+': '+str(e);status='SAFETY_STOP_CENSORED' if isinstance(e,SafetyStop) else 'REPRODUCTION_OR_MODEL_STOP' if isinstance(e,ReproductionStop) else 'RESOURCE_OR_TECHNICAL_STOP';save(d/'stop-private.json',dict(status=status,error=error,traceback=traceback.format_exc()))
 finally:
  if observer:observer.disable();telemetry=observer.overhead()
  if journal:journal.close()
  lap=None
  if env:
   if ctrl is not None and obs is not None:save(d/'final-private.json',complete_state(env,obs,ctrl.memory()))
   if completed:lap=round((env.unwrapped.finish_time_s-start_t)*1000)
   env.close()
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in sig.items():signal.signal(s,h)
  persist()
 out=dict(stage=414,status=status,error=error,completed_safe=status=='COMPLETED_SAFE',official_finish_observed=completed,actual_DNF=bool(ended and not completed),truncated=bool(truncated),lap_ms=lap,reference_historical_O_lap_ms=14780,lap_delta_ms=lap-14780 if status=='COMPLETED_SAFE' else None,damage=rows[-1]['damage'] if rows else None,max_post_path_error_m=max((r['post_projection']['path_error_m'] for r in rows),default=None),raw_step_ticks=sum(r['raw_ticks'] for r in rows),raw_reset_ticks=reset_ticks,initial_full_exact=initial_exact,fork_full_exact=fork_exact,reproduced_prefix_rows=reproduced_prefix,reproduced_suffix_rows=reproduced_suffix,existing13_model_fidelity_pass=len(checks)==13 and all(z['passed'] for z in checks),beyond129_source_fidelity_claim=False,fixed_known_time_diagnostic=True,statebased_deployment_policy=False,confirmed_rows=len(rows),unconfirmed_native=b['actions']-len(rows),goal_resets=goal_resets,actual_goal_hits=sum(r['goal_hit_actual_step'] for r in rows),safety_violations=sum(bool(r['safety']) for r in rows),intervention_steps=[117] if len(rows)>=117 else [],telemetry=telemetry,budget=b,wholeworker_CPU_s=time.process_time(),new_model_actor_learning_SEALED_reserve_paid=0);save(d/'result.json',out);print(json.dumps(out),flush=True)
if __name__=='__main__':
 root=Path(sys.argv[2]);{'prepare':prepare,'run':run}[sys.argv[1]](root)
