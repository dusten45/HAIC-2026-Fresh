"""Frozen405 three-state source-model falsification, never a native env or actor."""
import copy,datetime,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.cross404_common import G,scope_for,executor,control_code
from retry.branch401_gate import snapshot,fingerprint
from retry.source_vehicle_transition import SourceVehicleTransition
from retry.factorial401_run import sensor as source_sensor
from retry.executor397 import canonical_projection,ExecutorDomainError
from retry.fork394_run import ForkTrace

class QualificationFailure(RuntimeError):pass
class BudgetStop(RuntimeError):pass
class RecipeStop(RuntimeError):pass

class Meter:
 def __init__(self,d):
  self.d=d;self.cpu=time.process_time();self.wall=time.perf_counter();self.b=dict(ticks=0,reserved=0,worlds=0,CPU_s=0.,wall_s=0.)
 def persist(self):
  self.b.update(CPU_s=time.process_time()-self.cpu,wall_s=time.perf_counter()-self.wall);save(self.d/'budget.json',self.b)
 def guard(self):
  self.persist()
  if self.b['CPU_s']>=60 or self.b['wall_s']>=120:raise BudgetStop('CPU60_or_wall120')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(read(self.d/'plan.json')['deadline_utc']):raise BudgetStop('deadline')
 def world(self,ss):
  self.guard()
  if self.b['worlds']>=66:raise BudgetStop('world66cap')
  self.b['worlds']+=1;self.persist();m=SourceVehicleTransition(ss)
  if not(m.initial_bodies_exact and m.initial_tiles_exact and m.initial_progress_exact):m.close();raise QualificationFailure('snapshot_body_tile_progress')
  return m
 def step(self,m,a):
  self.guard()
  if self.b['reserved']+4>4096:raise BudgetStop('4096tickcap')
  self.b['reserved']+=4;self.persist();before=m.native_ticks
  try:return m.step(np.asarray(a,np.float32))
  finally:self.b['ticks']+=m.native_ticks-before;self.persist()

class Controller:
 """Input contract: fixed path/profile + current source state and own memory only."""
 def __init__(self,fixed,pace,kind,memory=None):
  self.fixed=fixed;self.pace=pace;self.kind=kind;self.code,_=control_code(G/'retry/pace269_run.py');self.scope=scope_for(None,fixed,pace);self.policy=executor(fixed,pace) if kind=='C' else None
  if memory:
   self.scope['index']=memory['index'];self.scope['laststeer']=memory['laststeer']
   if self.policy:
    for k,v in memory['C'].items():setattr(self.policy,k,v)
 def memory(self):
  c=None if self.policy is None else {k:getattr(self.policy,k) for k in ['phase','previous_arc','s','last_time','launch_commanded']}
  return dict(index=int(self.scope['index']),laststeer=float(self.scope['laststeer']),C=c)
 def phase(self):return self.policy.phase if self.policy else 'FIRST_LAP'
 def act(self,m,t):
  self.scope['env']=SimpleNamespace(unwrapped=m);exec(self.code,dict(np=np),self.scope);a=self.scope['action']
  if self.policy:a,_=self.policy.act(source_sensor(m,t),a,{},self.scope['arc'])
  if a is None:raise ExecutorDomainError('UnexpectedDONEinlocalwindow')
  return np.asarray(a,np.float32)


def actual_compare(q,row):
 a=row['post'];errors=dict(speed_m_s=abs(q['speed_m_s']-a['speed']),yaw_rate_rad_s=abs(q['angular_velocity']-a['yaw']),position_m=float(np.linalg.norm(np.asarray(q['position'])-a['pos'])));dis=dict(collision=q['collision']==row['collision'],damage=q['damage']==row['damage'],wheel_road_contacts=q['wheel_road_contacts']==sum(n>0 for n in a['road_contacts']))
 return dict(errors=errors,discrete=dis,passed=errors['speed_m_s']<=.5 and errors['yaw_rate_rad_s']<=.05 and errors['position_m']<=.1 and all(dis.values()))
def model_compare(q,r):
 errors=dict(speed_m_s=abs(q['speed_m_s']-r['speed_m_s']),yaw_rate_rad_s=abs(q['angular_velocity']-r['angular_velocity']),position_m=float(np.linalg.norm(np.asarray(q['position'])-r['position'])));dis={k:q[k]==r[k] for k in ['collision','damage','wheel_road_contacts']}
 return dict(errors=errors,discrete=dis,passed=errors['speed_m_s']<=.5 and errors['yaw_rate_rad_s']<=.05 and errors['position_m']<=.1 and all(dis.values()))
def memory_at(rows,index,kind):
 r=rows[index];memory=dict(index=r['memory_before']['index'],laststeer=r['memory_before']['laststeer'],C=None)
 if kind=='C':
  if index==0:memory['C']=dict(phase='LAUNCH',previous_arc=None,s=None,last_time=None,launch_commanded=False)
  else:
   prev=rows[index-1];memory['C']=dict(phase=prev['reference']['phase'],previous_arc=prev['reference']['projection']['arc'],s=prev['reference']['actual_arc'],last_time=prev['pre']['time'],launch_commanded=True)
 return memory

def projection(m,line,phase):return canonical_projection(line,list(m.car.hull.position),list(m.car.hull.linearVelocity),phase)
def advance(s,oldarc,newarc,L):return s+(newarc-oldarc+L/2)%L-L/2

def rollout(meter,fixed,pace,kind,ss,memory,clock,progress,start_index,goal,deadline_index,first_action=None,retained=None,reference=False):
 """No actual reference states/actions argument; this function cannot read future truth."""
 m=meter.world(ss);ctrl=Controller(fixed,pace,kind,copy.deepcopy(memory));line=np.asarray(fixed['line']);L=sum(fixed['free_profile']['ds']);rows=[];actions=[];s=progress;prev=projection(m,line,ctrl.phase())['arc'];observer=ForkTrace();flags=[];domain=None;reached=False;score=0.;maxerr=0.;maxyaw=0.;initial_damage=ss['damage']
 try:
  for k in range(13):
   try:
    nominal=ctrl.act(m,clock+k*.08);command=np.asarray(retained[k],np.float32) if retained is not None and k<len(retained) else np.asarray(first_action,np.float32) if k==0 and first_action is not None else nominal
    observer.rows=[];observer.enable()
    try:q=meter.step(m,command)
    finally:observer.disable()
    qp=projection(m,line,ctrl.phase());s=advance(s,prev,qp['arc'],L);prev=qp['arc'];yaw=abs(q['angular_velocity']);current=[]
    if qp['path_error_m']>3:current.append('path_error_over3m')
    if q['collision']:current.append('collision')
    if q['damage']>initial_damage:current.append('damage')
    if q['wheel_road_contacts']<4 or any(z['grass'] for z in observer.rows):current.append('wheel_road_loss')
    bodyforward=float(np.asarray(q['velocity'])@np.array([-math.sin(q['angle']),math.cos(q['angle'])]))
    if qp['sigma']<-.1 or bodyforward<-.1:current.append('meaningful_reverse')
    maxerr=max(maxerr,qp['path_error_m']);maxyaw=max(maxyaw,yaw);score+=(goal-s)*.08
    if start_index+k+1<=deadline_index and s>=goal:reached=True
    rear=[z for z in observer.rows if z['wheel']>=2];rows.append(dict(offset=k+1,predicted=q,arc=s,path_error=qp['path_error_m'],abs_yaw=yaw,flags=current,rear_max_force_ratio=max(z['force_ratio'] for z in rear),rear_max_abs_lateral_slip=max(abs(z['lateral_slip_m_s']) for z in rear)));actions.append(command.tolist())
    if current:
     flags.extend(current)
     if not reference:break
   except ExecutorDomainError as e:
    domain=str(e);break
 finally:observer.disable();m.close()
 valid=len(rows)==13 and not flags and domain is None and reached
 return dict(rows=rows,actions=actions,controller_memory=ctrl.memory(),domain_failure=domain,safety_flags=flags,goal_reached_by_deadline=reached,valid=valid,score=score,max_path_error=maxerr,max_abs_yaw=maxyaw)

def prepare(root):
 d=root/'stage406';assert not d.exists();d.mkdir(mode=0o700);bp=read(G/'retry/progress405_design.json');v=read(root/'project-effective-budget-v425.json');assert v['research_remaining']==31291 and v['final_reserved_actions']==84000 and v['final_reserve_used']==0
 p404=read(root/'stage404/plan.json');fixed=Path(p404['fixed_plan']);files=[Path(__file__),G/'retry/progress405_design.json',G/'retry/cross404_common.py',G/'retry/pace269_run.py',G/'retry/executor397.py',G/'retry/probe390_run.py',G/'retry/fork394_run.py',G/'retry/factorial401_run.py',G/'retry/branch401_gate.py',G/'retry/source_vehicle_transition.py',G/'damage.py',root/'stage404/profiles-private.json',root/'stage404/plan.json',root/'project-effective-budget-v425.json',root/'research-deadline-current.json',fixed]+list((G/'core').rglob('*.py'))
 for f in ['stage402/P10_C/trace-private.jsonl','stage402/P10_C/initial-private.json','stage404/O_268/trace-private.jsonl','stage404/O_268/initial-private.json','stage404/C_268/trace-private.jsonl','stage404/C_268/initial-private.json']:files.append(root/f)
 p=dict(stage=406,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],fixed_plan=str(fixed),blueprint_sha256=sha(G/'retry/progress405_design.json'),states=[dict(name='reset_Cbase',kind='C',profile='base',folder='stage402/P10_C',index=0),dict(name='O268_pre92',kind='O',profile='268',folder='stage404/O_268',index=91),dict(name='C268_pre91',kind='C',profile='268',folder='stage404/C_268',index=90)],model_tick_cap=4096,CPU_cap_s=60,wall_cap_s=120,world_cap=66,new_native_actor_fit_SEALED_reserve_cap=0,max_parallel=1,K=6,H=13,decisions=2,goal_distance_m=3.24,goal_deadline_actions=13,selection='Safety/domain+goalbyintegerdeadlineindex, then signed sum(goal-s_post)*.08, maxpatherror, maxabsyaw,index. Fixedsteer nominal/holdcurrentjoint/0 x nominalpedals/brake0.3;slot5retainedsuffixonlydecision2. No actualfuture inrollout/selector.',memory='Initializecontrollerfromanchorcurrentnominalmemory+pastpreviousrowphase/arc/time only. Candidatefirstcalculationadvancesnominalmemoryevenwithfirstactionoverride; subsequenttailownpredictedstates; parentupdatesnominalmemoryfromcurrentparentstate. Retainedsuffixcontrolsareownpreviousforecast,neveractualfuture.',deadline='Useintegerdecisionindices;setgoalcurrentarc+3.24deadlineindex+13;resetonlyafterparentcurrentarc>=goal;H13alwaysincludingseconddecision,safetyall13,goalbyremainingdeadline.',qualification='Prefixactualcommandreplayeachpost391limits/discrete. All3freshnominal13 forecasts sealbeforeactualfuturecomparison. Twoindependentnominalrefs BEFORE anycandidate establish snapshot/controller/input/parentisolation; exactrepeat andactual391limits. KnownunsafeC referencefidelitycanpass. Firstfailureglobalstop.',candidate_independence='Afterallreferencespass, first6 forward/reverse13forecasts,exactrepeat andimmutableparent/input required;beforeselection repeatnominal13 compareprequalifiedreference. Then2decisionsmax, chosenfirstpredictionvscontinuoussourceparent391. CandidatepredictedExecutorDomainError/safetyviolation=infeasiblecandidate,notmodelrestorefailure. Allinvalid=>recipeINFEASIBLEstopallno newqueries.',budget_change_within405margin='Extra3x13 pre-candidate nominalduplicate uses156ticks/3worlds from228margin. Worst4024ticks,66worlds,leaves72ticks. No candidate/horizon enlargement.',classification='Qualificationfailure/technical/resource/infeasible recipe distinct. Branchinternalagreement notactualcounterfactualranking, no nativeperformance/296promotion.',sources={str(f):sha(f) for f in files},protected={str(f):sha(f) for f in [root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json']})
 save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');(d/'plan.sha256').chmod(0o600);print(json.dumps(dict(stage=406,registered=True,model_cap=4096,CPU_cap=60,wall_cap=120,worst_ticks=4024,plan_sha256=sha(d/'plan.json'))))

def run(root):
 d=root/'stage406';p=read(d/'plan.json');assert not(d/'opening.json').exists();assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
 for f,h in {**p['sources'],**p['protected']}.items():assert sha(f)==h,f
 save(d/'opening.json',dict(pid=os.getpid(),epoch=time.time(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));meter=Meter(d);fixed=read(Path(p['fixed_plan']));line=np.asarray(fixed['line']);L=sum(fixed['free_profile']['ds']);profiles=read(root/'stage404/profiles-private.json');contexts=[];references=[];results=[];active=[];failure=None;error=None;status='RUNNING';stage='prefix_reference';raw_records=[]
 def timeout(*args):raise BudgetStop('CPU60_signal')
 oldsig=signal.signal(signal.SIGPROF,timeout);signal.setitimer(signal.ITIMER_PROF,59)
 try:
  # Evaluator-owned actual rows never passed into Controller or rollout.
  for case in p['states']:
   meter.guard();truth=[json.loads(s) for s in (root/case['folder']/'trace-private.jsonl').read_text().splitlines()];initial=read(root/case['folder']/'initial-private.json')['physical'];pace=np.asarray(profiles['frozen268']) if case['profile']=='268' else np.asarray(profiles['base']);parent=meter.world(initial);active.append(parent);prefix=[]
   for row in truth[:case['index']]:
    q=meter.step(parent,row['command']);check=actual_compare(q,row);prefix.append(dict(step=row['step'],**check))
    if not check['passed']:raise QualificationFailure(f'{case["name"]}:prefix:{row["step"]}:{check}')
   row=truth[case['index']];clock=row['pre']['time'];memory=memory_at(truth,case['index'],case['kind']);ctrl=Controller(fixed,pace,case['kind'],memory);ss=snapshot(parent,clock);q0=projection(parent,line,ctrl.phase());progress=q0['arc'];goal=progress+3.24;baseline=None;comparisons=[];inputhash=fingerprint(ss);parenthash=fingerprint(snapshot(parent,clock));memhash=fingerprint(memory)
   for repeat in range(2):
    forecast=rollout(meter,fixed,pace,case['kind'],ss,memory,clock,progress,0,goal,13,reference=True)
    if forecast['domain_failure'] or len(forecast['rows'])!=13:raise QualificationFailure(f'{case["name"]}:nominal_reference_domain')
    signature=fingerprint(forecast)
    if repeat==0:
     baseline=forecast
     # Predictions are sealed before looking up the actual future reference rows.
     save(d/(case['name']+'-nominal-sealed-private.json'),forecast)
     for j,pred in enumerate(forecast['rows']):
      check=actual_compare(pred['predicted'],truth[case['index']+j]);comparisons.append(dict(actual_step=case['index']+j+1,**check))
      if not check['passed']:raise QualificationFailure(f'{case["name"]}:reference:{j+1}:{check}')
    elif signature!=fingerprint(baseline):raise QualificationFailure(f'{case["name"]}:nominal_repeat')
    if fingerprint(ss)!=inputhash or fingerprint(snapshot(parent,clock))!=parenthash or fingerprint(memory)!=memhash:raise QualificationFailure(f'{case["name"]}:reference_mutation')
   rec=dict(state=case['name'],prefix_actions=len(prefix),prefix_pass=True,reference_actions=13,reference_comparisons=comparisons,reference_safe=baseline['valid'],reference_flags=baseline['safety_flags'],reference_max_error=baseline['max_path_error'],initial_fresh_bodies_tiles_progress=True,pre_candidate_independence_pass=True)
   references.append(rec);save(d/'qualification-progress.json',dict(references=references,budget=meter.b));contexts.append(dict(case=case,parent=parent,pace=pace,controller=ctrl,clock=clock,progress=progress,prev_arc=q0['arc'],goal=goal,deadline=13,index=0,retained=None,initial_snapshot=ss,initial_memory=memory,baseline=baseline))
  save(d/'qualification.json',dict(passed=True,states=references,budget=meter.b));stage='candidates'
  for ctx in contexts:
   case=ctx['case'];case_results=[]
   for decision in range(2):
    meter.guard();parent=ctx['parent'];ctrl=ctx['controller'];ss=snapshot(parent,ctx['clock']);memory=ctrl.memory();inputhash=fingerprint(ss);parenthash=fingerprint(snapshot(parent,ctx['clock']));memhash=fingerprint(memory);preview=Controller(fixed,ctx['pace'],case['kind'],copy.deepcopy(memory));nominal=preview.act(parent,ctx['clock']);joint=float(np.mean([w.joint.angle for w in parent.car.wheels[:2]]));actions=[np.asarray([a,*b],np.float32).tolist() for a in [nominal[0],float(np.clip(-joint,-.4,.4)),0.] for b in [nominal[1:].tolist(),[0.,.3]]];forecasts={}
    for slot in list(range(6))+(list(range(5,-1,-1)) if decision==0 else []):
     retained=ctx['retained'] if decision==1 and slot==5 else None
     forecast=rollout(meter,fixed,ctx['pace'],case['kind'],ss,memory,ctx['clock'],ctx['progress'],ctx['index'],ctx['goal'],ctx['deadline'],first_action=None if retained is not None else actions[slot],retained=retained)
     if fingerprint(ss)!=inputhash or fingerprint(snapshot(parent,ctx['clock']))!=parenthash or fingerprint(memory)!=memhash:raise QualificationFailure(f'{case["name"]}:candidate_mutation')
     if slot in forecasts and fingerprint(forecast)!=fingerprint(forecasts[slot]):raise QualificationFailure(f'{case["name"]}:candidate_order:{slot}')
     forecasts[slot]=forecast
    if decision==0:
     repeated=rollout(meter,fixed,ctx['pace'],case['kind'],ss,memory,ctx['clock'],ctx['progress'],0,ctx['goal'],13,reference=True)
     if fingerprint(repeated)!=fingerprint(ctx['baseline']):raise QualificationFailure(f'{case["name"]}:postcandidate_nominal_repeat')
    records=[dict(slot=i,retained_suffix=decision==1 and i==5,valid=f['valid'],goal_reached=f['goal_reached_by_deadline'],steps=len(f['rows']),domain=f['domain_failure'],safety=f['safety_flags'],score=f['score'],max_error=f['max_path_error'],max_yaw=f['max_abs_yaw']) for i,f in sorted(forecasts.items())];valid=[i for i,f in forecasts.items() if f['valid']];unique=len({fingerprint(forecasts[i]['actions']) for i in valid});raw_records.append(dict(state=case['name'],decision=decision,forecasts=forecasts));save(d/'candidate-forecasts-private.json',raw_records)
    if not valid:
     case_results.append(dict(decision=decision,goal=ctx['goal'],deadline_index=ctx['deadline'],candidates=records,valid_count=0,valid_unique_count=0,selected=None));results.append(dict(state=case['name'],decisions=case_results,status='INFEASIBLE_RECIPE'));raise RecipeStop(f'{case["name"]}:no_feasible_candidate')
    chosen=min(valid,key=lambda i:(forecasts[i]['score'],forecasts[i]['max_path_error'],forecasts[i]['max_abs_yaw'],i));f=forecasts[chosen];expected=f['rows'][0]['predicted'];parent_nominal=ctrl.act(parent,ctx['clock']);assert parent_nominal.tolist()==nominal.tolist();q=meter.step(parent,f['actions'][0]);check=model_compare(q,expected)
    if not check['passed']:raise QualificationFailure(f'{case["name"]}:chosen_parent_mismatch:{check}')
    qp=projection(parent,line,ctrl.phase());oldprogress=ctx['progress'];ctx['progress']=advance(ctx['progress'],ctx['prev_arc'],qp['arc'],L);ctx['prev_arc']=qp['arc'];ctx['clock']+=.08;ctx['index']+=1;oldgoal=ctx['goal'];olddeadline=ctx['deadline'];reached=ctx['progress']>=ctx['goal']
    if reached:ctx['goal']=ctx['progress']+3.24;ctx['deadline']=ctx['index']+13
    ctx['retained']=f['actions'][1:]
    case_results.append(dict(decision=decision,goal_before=oldgoal,deadline_before=olddeadline,goal_after=ctx['goal'],deadline_after=ctx['deadline'],actual_parent_model_progress=ctx['progress']-oldprogress,milestone_reached_after_parent_step=reached,candidates=records,valid_count=len(valid),valid_unique_count=unique,selected=chosen,selected_first_command=f['actions'][0],selected_score=f['score'],selected_branch_parent_check=check,retained_slot_revalidated=decision==1,retained_slot_valid=forecasts[5]['valid'] if decision==1 else None))
    save(d/'candidate-progress.json',dict(completed_states=results,active_state=case['name'],active_decisions=case_results,budget=meter.b))
   if case['name']=='reset_Cbase' and not(any(z['selected_first_command'][1]>0 for z in case_results) and sum(z['actual_parent_model_progress'] for z in case_results)>0):results.append(dict(state=case['name'],decisions=case_results,status='RESET_STATIONARY_RECIPE'));raise RecipeStop('reset_stationary_no_gasfloor_repair')
   results.append(dict(state=case['name'],decisions=case_results,status='TWO_MODEL_DECISIONS_COMPLETED'))
  status='COMPLETED_MODEL_PROBE'
 except QualificationFailure as e:failure=str(e);status='QUALIFICATION_FAILED'
 except RecipeStop as e:failure=str(e);status='INFEASIBLE_OR_STATIONARY_RECIPE'
 except BudgetStop as e:failure=str(e);status='RESOURCE_OR_DEADLINE_CENSORED'
 except BaseException as e:error=type(e).__name__+': '+str(e);status='TECHNICAL_STOP';save(d/'error-private.json',dict(error=error,traceback=traceback.format_exc()))
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.signal(signal.SIGPROF,oldsig)
  for m in active:m.close()
  meter.persist()
 if stage=='prefix_reference' and not(d/'qualification.json').exists():save(d/'qualification.json',dict(passed=False,states=references,failure=failure,technical_error=error,budget=meter.b))
 x=dict(stage=406,status=status,stopped_stage=stage,failure=failure,technical_error=error,reference_states=references,results=results,candidates_started=stage=='candidates',uncompleted_states=[s['name'] for s in p['states'] if s['name'] not in [r['state'] for r in results]],budget=meter.b,new_wrapper_actions=0,new_actor_calls=0,new_learning_fits=0,new_SEALED_queries=0,new_paid_resources=0,actual_counterfactual_performance=False,source_hashes_rechecked=all(sha(f)==h for f,h in p['sources'].items()),protected_hashes_rechecked=all(sha(f)==h for f,h in p['protected'].items()))
 save(d/'result.json',x);print(json.dumps(dict(stage=406,status=status,stopped_stage=stage,failure=failure,error=error,budget=meter.b,results=[dict(state=r['state'],status=r['status'],selected=[d['selected'] for d in r['decisions']],valid=[d['valid_unique_count'] for d in r['decisions']]) for r in results]),ensure_ascii=False))
if __name__=='__main__':
 root=Path(sys.argv[2]);(prepare if sys.argv[1]=='prepare' else run)(root)
