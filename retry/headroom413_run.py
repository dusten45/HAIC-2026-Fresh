"""One frozen H1 primitive test, source gates before any conditional native run."""
import copy,datetime,json,math,os,random,resource,signal,sys,time,traceback
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.branch401_gate import fingerprint
from retry.cross404_common import G
from retry.fork394_run import ForkTrace,complete_state
from retry.terminal410_model import TerminalVehicleTransition,from_actual_full,snapshot
from retry.terminal410_run import Controller,compare,rnghash,ModelFailure
from retry.closed411_run import ActualController
from retry.loss389_replay import sensor
from retry.pilot398_run import safety_flags,raw_capture_pairs
from retry.executor397 import canonical_projection,ExecutorDomainError
from retry.terminal409_contract import validate

class Stop(RuntimeError):pass
class BudgetStop(Stop):pass
class ActualSafetyStop(Stop):pass
class Trace(ForkTrace):
 """Identical pre-vector-clamp Car.step line as394; hull read once atwheel0."""
 def __init__(self,clock):super().__init__();self.clock=clock;self.hulls=[];self.payload_CPU_s=0.;self.payload_wall_s=0.;self.dispatch_events=0
 def trace(self,frame,event,arg):
  self.dispatch_events+=1
  if frame.f_code is not self.Car.step.__code__:return None
  target=event=='line' and frame.f_lineno==self.line
  if target:cpu=time.process_time();wall=time.perf_counter()
  result=super().trace(frame,event,arg)
  if target:
   self.rows[-1]['friction_limit']=float(frame.f_locals['friction_limit'])
   if self.rows[-1]['wheel']==0:
    h=frame.f_locals['self'].hull;self.hulls.append(dict(raw_tick=self.rows[-1]['raw_tick'],time=float(self.clock()),origin_position=list(h.position),COM_world=list(h.worldCenter),COM_local=list(h.localCenter),COM_linear_velocity=list(h.linearVelocity),origin_linear_velocity=list(h.GetLinearVelocityFromLocalPoint((0,0))),angle=float(h.angle),yaw=float(h.angularVelocity),mass=float(h.mass),inertia=float(h.inertia)))
   self.payload_CPU_s+=time.process_time()-cpu;self.payload_wall_s+=time.perf_counter()-wall
  return result
 def reset(self):self.rows=[];self.hulls=[]
 def overhead(self):return dict(payload_CPU_s=self.payload_CPU_s,payload_wall_s=self.payload_wall_s,dispatch_events=self.dispatch_events,all_dispatch_overhead_measured=False,uninstrumented_benchmark_executed=False)

class Meter:
 def __init__(self,d):self.d=d;self.phase='source';self.phase_cpu=0.;self.phase_wall=time.perf_counter();self.b=dict(ticks=0,reserved=0,worlds=0,native=0,resets=0,case_native={},phase_cost={})
 def persist(self):self.b['current_phase']=self.phase;self.b['phase_cost'][self.phase]=dict(CPU_s=time.process_time()-self.phase_cpu,wall_s=time.perf_counter()-self.phase_wall);self.b['wholeprocess_CPU_s']=time.process_time();save(self.d/'budget.json',self.b)
 def guard(self):
  self.persist();c=self.b['phase_cost'][self.phase]
  if c['CPU_s']>=(30 if self.phase=='source' else 60) or c['wall_s']>=(60 if self.phase=='source' else 120):raise BudgetStop('phase_resource_cap')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(read(self.d/'plan.json')['deadline_utc'].replace('Z','+00:00')):raise BudgetStop('deadline')
 def switch_actual(self):self.persist();self.phase='actual';self.phase_cpu=time.process_time();self.phase_wall=time.perf_counter();self.persist();signal.setitimer(signal.ITIMER_PROF,59);signal.setitimer(signal.ITIMER_REAL,119)
 def world(self,s):
  self.guard()
  if self.phase!='source' or self.b['worlds']>=64:raise BudgetStop('world64_or_phase')
  self.b['worlds']+=1;self.persist();m=TerminalVehicleTransition(s)
  if not(m.initial_bodies_exact and m.initial_tiles_exact and m.initial_progress_exact and m.initial_finish_exact):m.close();raise ModelFailure('restore')
  return m
 def step(self,m,a):
  self.guard()
  if self.b['reserved']+4>4096:raise BudgetStop('4096ticks')
  self.b['reserved']+=4;self.persist();before=m.native_ticks;success=False
  try:q=m.step(a);success=True;return q
  finally:
   used=m.native_ticks-before;self.b['ticks']+=used
   if success:self.b['reserved']-=4-used
   self.persist()
 def charge(self,kind,name):
  self.guard()
  if self.phase!='actual':raise BudgetStop('native_before_source_gate')
  if kind=='reset':
   if self.b['resets']>=2:raise BudgetStop('reset2')
   self.b['resets']+=1
  else:
   if self.b['native']>=394:raise BudgetStop('native394')
   self.b['native']+=1;self.b['case_native'][name]=self.b['case_native'].get(name,0)+1
  self.persist()

def wheel_compare(pred,actual):
 if len(pred)!=len(actual) or [(z['raw_tick'],z['wheel']) for z in pred]!=[(z['raw_tick'],z['wheel']) for z in actual]:return dict(passed=False,reason='sample_coverage')
 fields={'joint_angle':.01,'omega':1.,'lateral_slip_m_s':.5,'longitudinal_slip_m_s':.5,'force_ratio':.05};errors={k:max((abs(p[k]-a[k]) for p,a in zip(pred,actual)),default=0.) for k in fields};grass=all(p['grass']==a['grass'] for p,a in zip(pred,actual));return dict(passed=grass and all(errors[k]<=v for k,v in fields.items()),max_errors=errors,grass_exact=grass,clipped_flag_mismatches=sum(p['clipped']!=a['clipped'] for p,a in zip(pred,actual)))
def hull_compare(pred,actual):
 if len(pred)!=len(actual):return dict(passed=False,reason='raw_hull_count')
 e=dict(origin_position_m=0.,COM_position_m=0.,COM_speed_m_s=0.,origin_speed_m_s=0.,yaw_rad_s=0.,time_s=0.);meta=True
 for p,a in zip(pred,actual):
  e['origin_position_m']=max(e['origin_position_m'],math.dist(p['origin_position'],a['origin_position']));e['COM_position_m']=max(e['COM_position_m'],math.dist(p['COM_world'],a['COM_world']));e['COM_speed_m_s']=max(e['COM_speed_m_s'],abs(math.hypot(*p['COM_linear_velocity'])-math.hypot(*a['COM_linear_velocity'])));e['origin_speed_m_s']=max(e['origin_speed_m_s'],abs(math.hypot(*p['origin_linear_velocity'])-math.hypot(*a['origin_linear_velocity'])));e['yaw_rad_s']=max(e['yaw_rad_s'],abs(p['yaw']-a['yaw']));e['time_s']=max(e['time_s'],abs(p['time']-a['time']));meta=meta and p['COM_local']==a['COM_local'] and p['mass']==a['mass'] and p['inertia']==a['inertia']
 return dict(passed=meta and e['origin_position_m']<=.1 and e['COM_position_m']<=.1 and e['COM_speed_m_s']<=.5 and e['origin_speed_m_s']<=.5 and e['yaw_rad_s']<=.05 and e['time_s']<1e-8,max_errors=e,COM_mass_metadata_exact=meta)
def metrics(q,tires,hulls,line,phase):
 qp=canonical_projection(line,q['position'],q['velocity'],phase);flags=[]
 if qp['path_error_m']>3 or any(canonical_projection(line,h['origin_position'],h['origin_linear_velocity'],phase)['path_error_m']>3 for h in hulls):flags.append('path_error_over3m')
 if q['damage']>0:flags.append('damage_increase')
 if q['collision'] or q.get('contact_obstacle_ids'):flags.append('collision_or_obstacle')
 if q['wheel_road_contacts']<4 or any(z['grass'] for z in tires):flags.append('road_loss_or_grass')
 if qp['sigma']<-.1 or np.asarray(q['velocity'])@np.asarray([-math.sin(q['angle']),math.cos(q['angle'])])<-.1:flags.append('reverse')
 return qp,flags

def forecast(meter,state,memory,fixed,pace,index,progress,goal,deadline,fullgas=False):
 cpu=time.process_time();wall=time.perf_counter();sh=fingerprint(state);mh=fingerprint(memory);rh=rnghash();m=meter.world(state);ctrl=Controller(fixed,pace,'O',copy.deepcopy(memory));line=np.asarray(fixed['line']);L=sum(fixed['free_profile']['ds']);previous=canonical_projection(line,list(m.car.hull.position),list(m.car.hull.linearVelocity),ctrl.phase())['arc'];s=progress;rows=[];flags=[];hit=False;domain=None;tr=Trace(lambda:m.t)
 try:
  for k in range(13):
   try:a=ctrl.act(m)
   except ExecutorDomainError as e:domain=str(e);break
   if k==0 and fullgas:a=a.copy();a[1:]=[1.,0.]
   tr.reset();tr.enable()
   try:q=meter.step(m,a)
   finally:tr.disable()
   qp,why=metrics(q,tr.rows,tr.hulls,line,ctrl.phase());s+=(qp['arc']-previous+L/2)%L-L/2;previous=qp['arc'];hit=hit or index+k+1<=deadline and (s>=goal or q['finished']);flags.extend(why);rows.append(dict(offset=k+1,predicted=q,command=a.tolist(),progress=s,path_error_m=qp['path_error_m'],safety=why,tires=copy.deepcopy(tr.rows),raw_hull=copy.deepcopy(tr.hulls)))
   if q['terminal']:ctrl.done(m);break
 finally:tr.disable();m.close()
 if fingerprint(state)!=sh or fingerprint(memory)!=mh or rnghash()!=rh:raise ModelFailure('branch_input_memory_RNG_mutation')
 result=dict(rows=rows,safety=sorted(set(flags)),domain=domain,goal_reached=hit,valid=len(rows)==13 and not flags and domain is None and hit,controller_memory=ctrl.memory(),overhead=tr.overhead());return result,dict(CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)

def arrival(rows,start_arc,initial_time,line):
 L=sum(np.linalg.norm(np.roll(line,-1,axis=0)-line,axis=1));target=start_arc+30.;pts=[]
 for row in rows:
  for h in row['raw_hull']:
   a=canonical_projection(line,h['origin_position'],h['origin_linear_velocity'],'FIRST_LAP')['arc'];s=start_arc+(a-start_arc+L/2)%L-L/2;pts.append((h['time'],s))
  q=row.get('predicted');a=row['post_projection']['arc'] if q is None else canonical_projection(line,q['position'],q['velocity'],'FIRST_LAP')['arc'];t=row['post']['time'] if q is None else q['time'];pts.append((t,start_arc+(a-start_arc+L/2)%L-L/2))
 pts=sorted(set(pts))
 for j in range(1,len(pts)):
  if pts[j-1][1]<target<=pts[j][1]:return dict(reached=True,elapsed_bracket_s=[pts[j-1][0]-initial_time,pts[j][0]-initial_time],overshoot_m=pts[j][1]-target,progress_m=pts[-1][1]-start_arc,interpolated_time_used=False)
 return dict(reached=False,elapsed_bracket_s=None,progress_m=pts[-1][1]-start_arc if pts else 0.,interpolated_time_used=False)

def prepare(root):
 d=root/'stage413';assert not(d/'plan.json').exists();v=read(root/'project-effective-budget-v432.json');assert (v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(30334,84000,0);p411=read(root/'stage411/plan.json');p404=read(root/'stage404/plan.json');old=[json.loads(s) for s in (root/'stage404/O_268/trace-private.jsonl').read_text().splitlines()];end=read(root/'stage412/result.json')['datasets']['Oclosed411']['main_last_progress_m'];anchor=next(r for r in old if .6<=r['reference']['projection']['arc']/end<.7 and r['command'][2]>0 and r['reference']['r']-r['pre']['speed']>=5);assert anchor['step']==read(root/'stage412/hypothesis-anchor-private.json')['anchor']['step']==117
 files=[Path(__file__),G/'retry/terminal410_model.py',G/'retry/terminal410_run.py',G/'retry/closed411_run.py',G/'retry/source_vehicle_transition.py',G/'retry/fork394_run.py',G/'retry/pace269_run.py',G/'retry/executor397.py',G/'retry/terminal409_contract.py',G/'env_wrapper.py',G/'damage.py',root/'stage404/plan.json',root/'stage404/profiles-private.json',Path(p404['fixed_plan']),root/'stage404/O_268/trace-private.jsonl',root/'stage404/O_268/initial-private.json',root/'stage404/O_268/final-full-private.json',root/'stage411/policy_O/trace-private.jsonl',root/'stage412/hypothesis-anchor-private.json',root/'stage412/result.json',root/'project-effective-budget-v432.json',root/'research-deadline-current.json']+list((G/'core').rglob('*.py'))
 p=dict(stage=413,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],case=p404['case'],fixed_plan=p404['fixed_plan'],anchor_step=117,prefix_actions=116,anchor_rule='FirstOcurrentprearc incommon60-70percent, nominalbrake>0,target-speed>=5; nofuturetireselection',H=13,goal_distance_m=3.24,deadline_actions=13,common_exit_distance_m=30.,recipes=['originalO268feedback','firstactionnominalsteer gas1brake0 thenownO268feedback'],source_caps=dict(ticks=4096,worlds=64,CPU_s=30,wall_s=60),actual_caps=dict(wrappers=394,resets=2,CPU_s=60,wall_s=120,max_parallel=1),source_order='Prefix116body391+rawtires+firsthullsample boundaryfidelity; nominalA1sealbeforefutureeval/nominalfidelitythenA2; B1 ifvalidB2; postreferenceA3; parentnominalone vsA1+old117. Anyfirstmodel/fidelity/isolationfailurestoprest. Unsafe/infeasibleB=>noactual, notH1wholefalsified.',native_gate='Onlybothrecipesvalidandreachsameexitandallsourcegates. Twofreshactualresets initialfullsame404. Prefixcurrentnominal/sensors/commands exact404 andsourceprefixrawhull/tires. Actualfullfork/memory/RNG/pixels arms identical; predictorbranchmemorynotcommitted. A thenB once13suffixeach, ownactualfeedback. Firstsafety/body/wheel/source/technicalfailurestopsallremainder,no retry.',fidelity=dict(body_position_m=.1,body_speed_m_s=.5,yaw_rad_s=.05,raw_time_s=1e-8,wheel_joint_rad=.01,wheel_omega_rad_s=1.,wheel_lateral_long_slip_m_s=.5,wheel_force_ratio=.05,grass_contact_collision_damage_terminal_exact=True,COM_local_mass_inertia_exact=True),telemetry='SameCar.step line before ifabs(force)>2limit, afteromega/engine/brake update beforeforcevectorclip/world.Step. Newrawhullatwheel0: origin/worldCOM/localCOM/COMvelocity/originpointvelocity/angle/yaw/mass/inertia andpreworldtime. PayloadCPU/wall tracked; tracerdispatchoverheadnotisolated; no extra uninstrumentedrun.',safety='Existing3m pathguard alsoevaluatednewrawhullpoints;roadloss/rawgrass,collision/newobstacle,damageincrease,meaningfulreverse/domain. Sameoriginalreferencearc forprogress/exit. qclipalone notveto. Normalpartial1-4tickterminalcontract409.',promotion='Actualcandidateexitupper<=baselineexitlower-.08; allsafe/goal/deadline/fidelity. Smaller/overlappingintervals reporteffectuncertainty, notH1wholefalsification. Stop13actions, noextraexitextension/otherpedal/anchor/gain/horizon; no11secondvirtualclockgain.',new_actor_learning_SEALED_reserve_paid_cap=0,sources={str(f):sha(f) for f in files},protected=p411['protected'],original408_preserve=p411['original408_preserve']);save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'preparation-result.json',dict(implementation_wall_s=time.time()-read(d/'preparation-opening.json')['epoch'],implementation_CPU_s=None,implementation_CPU_fully_measured=False,includes_reasoning_tools=True,syntax_compiled=True,new_native_model_during_preparation=0));print(json.dumps(dict(registered=True,plan_sha256=sha(d/'plan.json'),anchor=117,source_caps=p['source_caps'],actual_caps=p['actual_caps'])))
def signature(f):return fingerprint({k:v for k,v in f.items() if k!='overhead'})
def row_fidelity(f,r):
 body=compare(f['predicted'],r,r.get('finish_time_s'));wheel=wheel_compare(f['tires'],r['raw_tire_samples']);hull=hull_compare(f['raw_hull'],r['raw_hull']) if 'raw_hull' in r else None
 return dict(passed=body['passed'] and wheel['passed'] and (hull is None or hull['passed']),body=body,wheel=wheel,hull=hull)

def run(root):
 d=root/'stage413';p=read(d/'plan.json');assert not(d/'opening.json').exists() and sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 meter=Meter(d);save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(root/'stage404/profiles-private.json')['frozen268']);line=np.asarray(fixed['line']);L=sum(fixed['free_profile']['ds']);old=[json.loads(s) for s in (root/'stage404/O_268/trace-private.jsonl').read_text().splitlines()];memory_record=old[116]['memory_before'];memory=dict(index=memory_record['index'],laststeer=memory_record['laststeer'],C=None);stage='source_prefix';status='RUNNING';failure=None;parent=None;source_prefix=[];source_branches={};branch_latency=[];actual_results=[];overhead={};source_eligible=False
 def timeout(*a):raise BudgetStop('CPU_or_wall_signal')
 sig={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM,signal.SIGXCPU]};resource.setrlimit(resource.RLIMIT_CPU,(89,90));signal.setitimer(signal.ITIMER_PROF,max(.01,29-time.process_time()));signal.setitimer(signal.ITIMER_REAL,59)
 try:
  initial=from_actual_full(read(root/'stage404/O_268/initial-private.json'));parent=meter.world(initial);tr=Trace(lambda:parent.t);q0=canonical_projection(line,list(parent.car.hull.position),list(parent.car.hull.linearVelocity),'FIRST_LAP');progress=q0['arc'];previous=q0['arc'];goal=progress+3.24;deadline=13;prefix_checks=[]
  for i,r in enumerate(old[:116]):
   if progress>=goal:goal=progress+3.24;deadline=i+13
   tr.reset();tr.enable()
   try:q=meter.step(parent,np.asarray(r['command'],np.float32))
   finally:tr.disable()
   f=dict(step=i+1,predicted=q,tires=copy.deepcopy(tr.rows),raw_hull=copy.deepcopy(tr.hulls));source_prefix.append(f);z=row_fidelity(f,r);h0=f['raw_hull'][0];raw_pre=dict(position_m=math.dist(h0['origin_position'],r['pre']['pos']),speed_m_s=abs(math.hypot(*h0['COM_linear_velocity'])-r['pre']['speed']),yaw_rad_s=abs(h0['yaw']-r['pre']['yaw']));z['raw_first_pre']=raw_pre
   if not z['passed'] or raw_pre['position_m']>.1 or raw_pre['speed_m_s']>.5 or raw_pre['yaw_rad_s']>.05:raise ModelFailure('source_prefix_fidelity:'+str(i+1)+':'+json.dumps(z))
   prefix_checks.append(z);arc=r['post_projection']['arc'];progress+=(arc-previous+L/2)%L-L/2;previous=arc
  overhead['source_prefix']=tr.overhead();save(d/'source-prefix-private.json',source_prefix);save(d/'prefix-qualification.json',dict(passed=True,actions=116,checks=prefix_checks))
  if progress>=goal:goal=progress+3.24;deadline=116+13
  state=snapshot(parent);start_arc=canonical_projection(line,list(parent.car.hull.position),list(parent.car.hull.linearVelocity),'FIRST_LAP')['arc'];start_time=parent.t;parent_h=fingerprint(snapshot(parent));mh=fingerprint(memory);rh=rnghash();save(d/'source-anchor-private.json',dict(state=state,memory=memory,progress=progress,goal=goal,deadline=deadline,start_arc=start_arc,start_time=start_time))
  def branch(label,fullgas):
   f,lat=forecast(meter,state,memory,fixed,pace,116,progress,goal,deadline,fullgas);branch_latency.append(dict(label=label,**lat));overhead[label]=f['overhead']
   if fingerprint(snapshot(parent))!=parent_h or fingerprint(memory)!=mh or rnghash()!=rh:raise ModelFailure('live_source_parent_RNG_memory_changed')
   save(d/(label+'-private.json'),f);return f
  stage='nominal_fidelity';A=branch('A1',False);checks=[row_fidelity(f,r) for f,r in zip(A['rows'],old[116:129])]
  if len(checks)!=13 or not all(z['passed'] for z in checks) or A['domain']:raise ModelFailure('nominal_horizon_body_wheel_fidelity')
  save(d/'nominal-qualification.json',dict(passed=True,checks=checks));A2=branch('A2',False)
  if signature(A)!=signature(A2):raise ModelFailure('nominal_independence')
  stage='candidate';B=branch('B1',True);source_branches=dict(A=A,B=B);source_arrival={k:arrival(f['rows'],start_arc,start_time,line) for k,f in source_branches.items()};save(d/'source-arrival.json',source_arrival)
  if not A['valid'] or not B['valid']:
   status='SOURCE_RECIPE_INELIGIBLE'
  else:
   B2=branch('B2',True)
   if signature(B)!=signature(B2):raise ModelFailure('candidate_independence')
   A3=branch('A3',False)
   if signature(A)!=signature(A3):raise ModelFailure('post_candidate_reference_changed')
   stage='continuous_parent_check';tr.reset();tr.enable()
   try:parentQ=meter.step(parent,np.asarray(A['rows'][0]['command'],np.float32))
   finally:tr.disable()
   parent_ref=dict(predicted=parentQ,tires=tr.rows,raw_hull=tr.hulls);row=copy.deepcopy(old[116]);row['raw_hull']=tr.hulls;z=row_fidelity(A['rows'][0],row)
   parent_body=compare(parentQ,old[116],None)
   if not parent_body['passed'] or not z['passed'] or not wheel_compare(parent_ref['tires'],A['rows'][0]['tires'])['passed'] or not hull_compare(parent_ref['raw_hull'],A['rows'][0]['raw_hull'])['passed']:raise ModelFailure('parent_vs_fresh_nominal')
   save(d/'parent-qualification.json',dict(passed=True,comparison=z,parent_body_vs_actual=parent_body))
   if not all(z['reached'] for z in source_arrival.values()):status='SOURCE_EXIT_CENSORED'
   else:source_eligible=True;status='SOURCE_PASSED'
  parent.close();parent=None
  save(d/'source-result.json',dict(status=status,eligible=source_eligible,branches={k:dict(valid=f['valid'],safety=f['safety'],goal_reached=f['goal_reached'],domain=f['domain'],actions=len(f['rows'])) for k,f in source_branches.items()},latencies=branch_latency,budget=copy.deepcopy(meter.b)))
  if source_eligible:
   meter.switch_actual();stage='actual';from retry.diagnose import make_env
   for name in ['A','B']:
    folder=d/('actual_'+name);folder.mkdir(mode=0o700);env=observer=journal=None;rows=[];checks=[];actual_status='STARTED';err=None;native_start=meter.b['native'];reset_ticks=0;actual_arrival=None;observer_overhead=None;all_prefix_exact=0;fullfork_equal=False
    try:
     random.seed(394);np.random.seed(394);env=make_env();meter.charge('reset',name);obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});ctrl=ActualController(env,fixed,pace,'O');ini=complete_state(env,obs,dict(index=0,laststeer=0.));save(folder/'initial-private.json',ini)
     if ini!=read(root/'stage404/O_268/initial-private.json'):raise ModelFailure('native_initial_full_RNG_pixels')
     reset_ticks=round(env.unwrapped.t*50);initial_pairs=set(tuple(z) for z in ini['physical']['touching_obstacle_contacts']);observer=Trace(lambda:env.unwrapped.t);journal=(folder/'trace-private.jsonl').open('x');(folder/'trace-private.jsonl').chmod(0o600);suffix_start=None
     for step in range(1,130):
      meter.guard();before=ctrl.memory();nominal=ctrl.act(env);pre=sensor(env);a=nominal.copy()
      if step<=117:
       h=old[step-1]
       if pre!=h['pre'] or nominal.tolist()!=h['command'] or before['index']!=h['memory_before']['index'] or before['laststeer']!=h['memory_before']['laststeer']:raise ModelFailure('actual_prefix_pre_command_memory:'+str(step))
      if step==117:
       fork=complete_state(env,obs,dict(before=before,after=ctrl.memory(),nominal=nominal.tolist()));save(folder/'fork-private.json',fork)
       if name=='B' and fork!=read(d/'actual_A/fork-private.json'):raise ModelFailure('actual_fullfork_mismatch')
       fullfork_equal=True;suffix_start=env.unwrapped.t
       if name=='B':a[1:]=[1.,0.]
      qp0=canonical_projection(line,pre['pos'],pre['vel'],'FIRST_LAP');why=safety_flags(pre,qp0,float(env.damage.damage),0.)
      if why:raise ActualSafetyStop('pre:'+','.join(why))
      observer.reset();observer.enable();meter.charge('action',name);before_t=env.unwrapped.t
      try:obs,_,ended,truncated,info=env.step(a)
      finally:observer.disable()
      post=sensor(env);q=dict(position=post['pos'],velocity=post['vel'],angle=post['angle'],angular_velocity=post['yaw'],speed_m_s=post['speed'],damage=float(env.damage.damage),collision=bool(info['collision']),wheel_road_contacts=sum(n>0 for n in post['road_contacts']));qp,why=metrics(q,observer.rows,observer.hulls,line,'FIRST_LAP')
      if set(tuple(z) for z in raw_capture_pairs(env))-initial_pairs:why.append('new_obstacle_contact')
      row=dict(step=step,pre=pre,post=post,nominal=nominal.tolist(),command=a.tolist(),memory_before=before,nominal_memory_after=ctrl.memory(),raw_ticks=round((env.unwrapped.t-before_t)*50),raw_tire_samples=copy.deepcopy(observer.rows),raw_hull=copy.deepcopy(observer.hulls),post_projection=qp,collision=bool(info['collision']),damage=float(env.damage.damage),completed=env.unwrapped.finish_time_s is not None,finish_time_s=env.unwrapped.finish_time_s,ended=bool(ended),truncated=bool(truncated),safety=why)
      rows.append(row);journal.write(json.dumps(row,allow_nan=False)+'\n');journal.flush()
      if not validate(row)['passed']:raise ModelFailure('actual_raw_measurement_contract')
      f=source_prefix[step-1] if step<117 else source_branches[name]['rows'][step-117];z=row_fidelity(f,row);checks.append(z);save(folder/'fidelity-private.json',checks)
      if step<117:
       if post!=old[step-1]['post'] or row['collision']!=old[step-1]['collision'] or row['damage']!=old[step-1]['damage']:raise ModelFailure('actual_prefix_post:'+str(step))
       all_prefix_exact+=1
      if not z['passed']:raise ModelFailure('actual_body_wheel_rawhull_fidelity:'+str(step)+':'+json.dumps(z))
      if why:raise ActualSafetyStop(','.join(why))
      if ended or truncated:actual_status='UNEXPECTED_ENV_TERMINAL_CENSORED';break
     else:actual_status='COMPLETED_13_ACTION_DIAGNOSTIC'
     actual_arrival=arrival(rows[116:],start_arc,suffix_start,line) if len(rows)>116 else None
    except BaseException as e:
     err=type(e).__name__+': '+str(e);actual_status='ACTUAL_SAFETY_STOP' if isinstance(e,ActualSafetyStop) else 'ACTUAL_RESOURCE_STOP' if isinstance(e,BudgetStop) else 'ACTUAL_MODEL_TECHNICAL_STOP';save(folder/'stop-private.json',dict(status=actual_status,error=err,traceback=traceback.format_exc()))
    finally:
     if observer:observer.disable();observer_overhead=observer.overhead()
     if journal:journal.close()
     if env:
      save(folder/'final-private.json',complete_state(env,obs,ctrl.memory()));env.close()
    overhead['actual_'+name]=observer_overhead;rr=dict(arm=name,status=actual_status,error=err,native_charged=meter.b['native']-native_start,confirmed_rows=len(rows),unconfirmed_native=meter.b['native']-native_start-len(rows),reset_ticks=reset_ticks,prefix_exact_rows=all_prefix_exact,fullfork_equal=fullfork_equal,suffix_actions=max(0,len(rows)-116),arrival=actual_arrival,all_fidelity_pass=all(z['passed'] for z in checks),fidelity_comparisons=len(checks),max_path_error_m=max((r['post_projection']['path_error_m'] for r in rows),default=None),damage=rows[-1]['damage'] if rows else None,safety_violations=sum(bool(r['safety']) for r in rows),instrumentation=observer_overhead);save(folder/'result.json',rr);actual_results.append(rr);print(json.dumps(rr),flush=True)
    if actual_status!='COMPLETED_13_ACTION_DIAGNOSTIC':failure=dict(stage='actual_'+name,error=err or actual_status);break
   status='COMPLETED_ACTUAL_PAIRED_DIAGNOSTIC' if len(actual_results)==2 and all(r['status']=='COMPLETED_13_ACTION_DIAGNOSTIC' for r in actual_results) else 'ACTUAL_CENSORED_STOP'
 except BaseException as e:
  failure=dict(stage=stage,error=type(e).__name__+': '+str(e));status='RESOURCE_STOP' if isinstance(e,BudgetStop) else 'SOURCE_MODEL_TECHNICAL_STOP';save(d/'failure-private.json',dict(**failure,traceback=traceback.format_exc()))
 finally:
  if parent:parent.close()
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in sig.items():signal.signal(s,h)
  meter.persist()
 gain=None;promote=False
 if len(actual_results)==2 and all(r['arrival'] and r['arrival']['reached'] for r in actual_results):
  A0,A1=actual_results[0]['arrival']['elapsed_bracket_s'];B0,B1=actual_results[1]['arrival']['elapsed_bracket_s'];gain=[A0-B1,A1-B0];promote=status=='COMPLETED_ACTUAL_PAIRED_DIAGNOSTIC' and gain[0]>=.08-1e-8 and all(r['all_fidelity_pass'] and r['damage']==0 and not r['safety_violations'] for r in actual_results)
 out=dict(stage=413,status=status,failure=failure,source_eligible=source_eligible,source_branch_summary={k:dict(valid=f['valid'],safety=f['safety'],goal_reached=f['goal_reached'],domain=f['domain'],actions=len(f['rows'])) for k,f in source_branches.items()},branch_latencies=branch_latency,actual_results=actual_results,actual_unexecuted=[n for n in ['A','B'] if n not in [r['arm'] for r in actual_results]],gain_bracket_s=gain,promote_to_next_GT=promote,H1_whole_hypothesis_falsified=False,virtual_reference_clock_used=False,overhead=overhead,budget=meter.b,wholeworker_CPU_s=time.process_time(),new_actor_learning_SEALED_reserve_paid=0);save(d/'result.json',out);print(json.dumps(dict(stage=413,status=status,failure=failure,gain_bracket_s=gain,promote=promote,budget=meter.b)),flush=True)
if __name__=='__main__':
 root=Path(sys.argv[2]);{'prepare':prepare,'run':run}[sys.argv[1]](root)
