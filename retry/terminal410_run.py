"""One bounded source-only qualification then chronological stored-window audit."""
import copy,datetime,json,math,os,pickle,random,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.branch401_gate import fingerprint
from retry.cross404_common import G,scope_for,executor,control_code
from retry.progress406_run import memory_at
from retry.factorial401_run import sensor
from retry.fork394_run import ForkTrace
from retry.executor397 import canonical_projection,ExecutorDomainError
from retry.terminal410_model import TerminalVehicleTransition,snapshot,from_actual_full

class ModelFailure(RuntimeError):pass
class BudgetStop(RuntimeError):pass

def rnghash():
 import hashlib
 return hashlib.sha256(pickle.dumps((random.getstate(),np.random.get_state()))).hexdigest()
class Meter:
 def __init__(self,d,static):self.d=d;self.cpu=time.process_time();self.wall=time.perf_counter();self.static=static;self.b=dict(ticks=0,reserved=0,worlds=0,CPU_s=0.,wall_s=0.)
 def persist(self):self.b.update(CPU_s=time.process_time()-self.cpu,wall_s=time.perf_counter()-self.wall);save(self.d/'budget.json',self.b)
 def guard(self):
  self.persist()
  if time.process_time()+self.static['wholeprocess_CPU_s']>=180 or self.b['wall_s']+self.static['wall_s']>=300:raise BudgetStop('resourcecap')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(read(self.d/'plan.json')['deadline_utc'].replace('Z','+00:00')):raise BudgetStop('deadline')
 def world(self,s):
  self.guard()
  if self.b['worlds']>=1200:raise BudgetStop('world1200')
  self.b['worlds']+=1;self.persist();m=TerminalVehicleTransition(s)
  if not(m.initial_bodies_exact and m.initial_tiles_exact and m.initial_progress_exact and m.initial_finish_exact):m.close();raise ModelFailure('restore_body_tile_progress_finish')
  return m
 def step(self,m,a):
  self.guard()
  if self.b['reserved']+4>60000:raise BudgetStop('tick60000')
  self.b['reserved']+=4;self.persist();before=m.native_ticks;success=False
  try:q=m.step(a);success=True;return q
  finally:
   used=m.native_ticks-before;self.b['ticks']+=used
   if success:self.b['reserved']-=4-used
   self.persist()
class Controller:
 def __init__(self,fixed,pace,kind,memory):
  self.kind=kind;self.code,_=control_code(G/'retry/pace269_run.py');self.scope=scope_for(None,fixed,pace);self.scope['index']=memory['index'];self.scope['laststeer']=memory['laststeer'];self.policy=executor(fixed,pace) if kind=='C' else None
  if self.policy:
   for k,v in memory['C'].items():setattr(self.policy,k,v)
 def phase(self):return self.policy.phase if self.policy else 'FIRST_LAP'
 def act(self,m):
  self.scope['env']=SimpleNamespace(unwrapped=m);exec(self.code,dict(np=np),self.scope);a=self.scope['action']
  if self.policy:a,_=self.policy.act(sensor(m,m.t),a,copy.deepcopy(m.finish_line_tracker.__dict__),self.scope['arc'])
  if a is None:raise ExecutorDomainError('Unexpected_action_query_after_finish')
  return np.asarray(a,np.float32)
 def done(self,m):
  if self.policy and m.finished:self.policy.mark_done(copy.deepcopy(m.finish_line_tracker.__dict__),m.t)
 def memory(self):return dict(index=int(self.scope['index']),laststeer=float(self.scope['laststeer']),C=None if not self.policy else {k:getattr(self.policy,k) for k in ['phase','previous_arc','s','last_time','launch_commanded']})
def compare(q,row,final_finish):
 a=row['post'];e=dict(speed_m_s=abs(q['speed_m_s']-a['speed']),yaw_rate_rad_s=abs(q['angular_velocity']-a['yaw']),position_m=float(np.linalg.norm(np.asarray(q['position'])-a['pos'])),time_s=abs(q['time']-a['time']));completed=bool(row['completed']);expected_ft=row.get('finish_time_s') if row.get('finish_time_s') is not None else final_finish if completed else None
 dis=dict(collision=q['collision']==row['collision'],damage=q['damage']==row['damage'],wheel_road_contacts=q['wheel_road_contacts']==sum(n>0 for n in a['road_contacts']),raw_ticks=q['raw_ticks']==row['raw_ticks'],terminated=q['terminated']==row['ended'],truncated=q['truncated']==row['truncated'],finished=q['finished']==completed,finish_timestamp=(q['finish_time_s'] is None and expected_ft is None) or (q['finish_time_s'] is not None and expected_ft is not None and abs(q['finish_time_s']-expected_ft)<1e-8))
 return dict(errors=e,discrete=dis,passed=e['speed_m_s']<=.5 and e['yaw_rate_rad_s']<=.05 and e['position_m']<=.1 and e['time_s']<1e-8 and all(dis.values()))
def rollout(meter,fixed,pace,kind,state,memory,start_index,progress,goal,deadline,pulse=False):
 """Causal inputs only; no evaluator truth, future actions, or trajectory argument."""
 before=fingerprint(state);mh=fingerprint(memory);rh=rnghash();m=meter.world(state);ctrl=Controller(fixed,pace,kind,copy.deepcopy(memory));line=np.asarray(fixed['line']);L=sum(fixed['free_profile']['ds']);prev=canonical_projection(line,list(m.car.hull.position),list(m.car.hull.linearVelocity),ctrl.phase())['arc'];s=progress;out=[];flags=[];domain=None;hit=False;observer=ForkTrace();initial_damage=m.damage.damage
 try:
  for k in range(13):
   try:a=ctrl.act(m)
   except ExecutorDomainError as e:domain=str(e);break
   if pulse and k==0:a=np.asarray([0.,0.,.3],np.float32)
   observer.rows=[];observer.enable()
   try:q=meter.step(m,a)
   finally:observer.disable()
   if len(observer.rows)!=4*q['raw_ticks'] or [(z['raw_tick'],z['wheel']) for z in observer.rows]!=[(t,w) for t in range(1,q['raw_ticks']+1) for w in range(4)]:raise ModelFailure('tire_coverage')
   qp=canonical_projection(line,q['position'],q['velocity'],ctrl.phase());s+=(qp['arc']-prev+L/2)%L-L/2;prev=qp['arc'];why=[]
   if qp['path_error_m']>3:why.append('path_error_over3m')
   if q['collision'] or q['contact_obstacle_ids']:why.append('collision_or_obstacle_contact')
   if q['damage']>initial_damage:why.append('damage_increase')
   if q['wheel_road_contacts']<4 or any(z['grass'] for z in observer.rows):why.append('road_loss_or_grass')
   if qp['sigma']<-.1 or np.asarray(q['velocity'])@np.asarray([-math.sin(q['angle']),math.cos(q['angle'])])<-.1:why.append('meaningful_reverse')
   hit=hit or (start_index+k+1<=deadline and (s>=goal or q['finished']));flags.extend(why);out.append(dict(offset=k+1,predicted=q,progress=s,path_error=qp['path_error_m'],flags=why,command=a.tolist()))
   if q['terminal']:ctrl.done(m);break
 finally:observer.disable();m.close()
 if fingerprint(state)!=before or fingerprint(memory)!=mh or rnghash()!=rh:raise ModelFailure('input_memory_or_RNG_mutation')
 complete=len(out)==13 or bool(out and out[-1]['predicted']['finished']);return dict(rows=out,safety_flags=sorted(set(flags)),domain=domain,progress_ok=hit,valid=complete and not flags and domain is None and hit,complete=complete,controller_memory=ctrl.memory())
def static(root):
 from core.finish_line import FinishLineTracker
 from retry.executor397 import CoherentExecutor
 from retry.terminal409_contract import validate
 d=root/'stage410';assert not(d/'static-result.json').exists();cpu=time.process_time();wall=time.perf_counter();t=FinishLineTracker((0.,0.),(1.,0.),2.,.875);t.update((-2.,0.),(2.,0.),1.,1.);t.update((-.5,0.),(2.,0.),1.,2.);clone=FinishLineTracker(**copy.deepcopy(t.__dict__));base=copy.deepcopy(t.__dict__);clone.update((0.,0.),(2.,0.),1.,3.);assert clone.finish_time_s is None;clone.update((1.,0.),(2.,0.),1.,4.);assert clone.finish_time_s==3. and t.__dict__==base
 c=object.__new__(CoherentExecutor);c.phase='FIRST_LAP';assert c.mark_done(dict(finish_time_s=3.),4.)['phase']=='DONE';bad=False
 try:c.mark_done(dict(finish_time_s=5.),4.)
 except ExecutorDomainError:bad=True
 assert bad
 row=json.loads((root/'stage408/trace-private.jsonl').read_text().splitlines()[-1]);assert validate(row)['passed'];missing=copy.deepcopy(row);missing['raw_tire_samples'].pop();assert not validate(missing)['passed']
 r=dict(passed=True,no_worlds_or_positive_ticks=True,tracker_candidate_confirmation_and_clone=True,phase_DONE_current_not_future=True,partial_terminal_and_missing_sample_controls=True,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,wholeprocess_CPU_s=time.process_time());save(d/'static-result.json',r);print(json.dumps(r))
def prepare(root):
 d=root/'stage410';assert not(d/'plan.json').exists();v=read(root/'project-effective-budget-v429.json');assert v['research_remaining']==30892 and v['final_reserved_actions']==84000 and v['final_reserve_used']==0;st=read(d/'static-result.json');assert st['passed'];old=read(root/'stage409/plan.json');p404=read(root/'stage404/plan.json');files=[Path(__file__),G/'retry/terminal410_model.py',G/'retry/source_vehicle_transition.py',G/'retry/progress406_run.py',G/'retry/cross404_common.py',G/'retry/factorial401_run.py',G/'retry/branch401_gate.py',G/'retry/fork394_run.py',G/'retry/pace269_run.py',G/'retry/executor397.py',G/'retry/terminal409_contract.py',G/'env_wrapper.py',G/'damage.py',Path(p404['fixed_plan']),root/'stage404/profiles-private.json',root/'stage404/plan.json',root/'research-deadline-current.json',root/'project-effective-budget-v429.json',d/'static-result.json']+list((G/'core').rglob('*.py'))
 for folder in ['stage404/O_268','stage404/C_268']:
  files += [root/folder/n for n in ['trace-private.jsonl','initial-private.json','final-full-private.json']]
 files += [root/'stage408'/n for n in ['trace-private.jsonl','initial-private.json','final-full-private.json']]
 for f,h in {**old['original408_preserve'],**old['protected']}.items():assert sha(f)==h,f
 p=dict(stage=410,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],model_tick_cap=60000,world_cap=1200,CPU_cap_s=180,wall_cap_s=300,max_parallel=1,native_actor_learning_SEALED_reserve_paid_cap=0,H=13,goal_distance_m=3.24,goal_deadline_actions=13,recipes=['ownnominal','firstactionfloat32(0,0,.3) thenownnominal'],order=['O185 chronological','C91 chronological'],qualification='Causalactualcommandprefix parents O185/C103/408pulse188; eachpost391+rawtick/clock/terminal/finishtimestamp exact criteria. Then resetO/Opre92/Cpre91/Oterminalpre185/408partialpre189 independentnominalduplicates vsactual. Cpre91pulse thennominal repeat provesorderindependence. Firstmodel/restore/isolation/fidelityfailure stopsallwindows, no retry.',windows='Nominal13 twocopies perwindow exactrepeat+parent/input/memory/RNG unchanged, sealbeforeactualfuturecomparison. O usesO memory/law,C usesC. Onlyifnominalinvalid computefixedpulse twocopies; nochangesafterfalsepositive. Originalactualhistorycausal milestoneledger resets onlyafteractualgoalhit, integerdeadlinepersists. Validterminalfinish countsgoal; candidate invalidnotunqualified; source/fidelity/isolationfailureglobalstop.',readout='Separate sourceunqualified vsfalsepositive/negative, progressfailure, nominaldomain, terminal/censored. Overlapping276windowsnotindependentepisodes. Noactualpulsepolicy orfallbackqualification. No newfitness/gain/tuning.',qualification_worst_ticks=2334,window_branch_worst_ticks=57408,total_conditional_worst_ticks=59742,world_worst=1119,fixed_plan=p404['fixed_plan'],sources={str(f):sha(f) for f in files},protected=old['protected'],original408_preserve=old['original408_preserve']);save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'preparation-result.json',dict(implementation_wall_s=time.time()-read(d/'preparation-opening.json')['epoch'],implementation_CPU_s=None,implementation_CPU_fully_measured=False,includes_reasoning_tool_latency=True,static=st));print(json.dumps(dict(registered=True,plan_sha256=sha(d/'plan.json'),worst_ticks=59742)))
def run(root):
 d=root/'stage410';p=read(d/'plan.json');assert not(d/'opening.json').exists();assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 static_result=read(d/'static-result.json');meter=Meter(d,static_result);save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));active=[];contexts={};truth={};final_ft={};qualification=[];windows=[];status='RUNNING';failure=None;stage='prefix_qualification';fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(root/'stage404/profiles-private.json')['frozen268']);line=np.asarray(fixed['line']);L=sum(fixed['free_profile']['ds'])
 def timeout(*args):raise BudgetStop('OS_CPU_or_wall')
 old={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};signal.setitimer(signal.ITIMER_PROF,max(.01,179-static_result['wholeprocess_CPU_s']-time.process_time()));signal.setitimer(signal.ITIMER_REAL,max(.01,299-static_result['wall_s']))
 def branch(ctx,kind,pulse=False):
  before=fingerprint(snapshot(ctx['parent'])) if ctx.get('parent') else None
  out=rollout(meter,fixed,pace,kind,ctx['state'],ctx['memory'],ctx['index'],ctx['progress'],ctx['goal'],ctx['deadline'],pulse)
  if before is not None and fingerprint(snapshot(ctx['parent']))!=before:raise ModelFailure('parent_mutation')
  return out
 def fidelity(pred,key,index):
  expected=truth[key][index:index+13]
  if len(pred['rows'])!=len(expected) or pred['domain']:raise ModelFailure('nominal_replay_length_or_domain:'+key+':'+str(index+1)+':'+str(pred['domain']))
  checks=[compare(q['predicted'],a,final_ft[key]) for q,a in zip(pred['rows'],expected)]
  if not all(z['passed'] for z in checks):raise ModelFailure('nominal391_or_terminal:'+key+':'+str(index+1)+':'+json.dumps(next(z for z in checks if not z['passed'])))
  return dict(rows=len(checks),max_errors={k:max(z['errors'][k] for z in checks) for k in ['speed_m_s','yaw_rate_rad_s','position_m','time_s']},all_discrete=True)
 try:
  for key,folder,kind,count in [('O','stage404/O_268','O',185),('C','stage404/C_268','C',103),('partial','stage408','C',188)]:
   truth[key]=[json.loads(s) for s in (root/folder/'trace-private.jsonl').read_text().splitlines()];full=read(root/folder/'final-full-private.json');final_ft[key]=full['wrapper']['finish_time_s'];initial=from_actual_full(read(root/folder/'initial-private.json'));parent=meter.world(initial);active.append(parent);contexts[key]=[];goal=deadline=progress=previous=None;prefix_checks=[]
   for i,row in enumerate(truth[key][:count]):
    mem=memory_at(truth[key],i,kind);phase=mem['C']['phase'] if kind=='C' else 'FIRST_LAP';arc=row['reference']['projection']['arc']
    if progress is None:progress=arc
    else:progress+=(arc-previous+L/2)%L-L/2
    previous=arc
    if goal is None or progress>=goal:goal=progress+3.24;deadline=i+13
    if key!='partial' or i==187:contexts[key].append(dict(state=snapshot(parent),memory=mem,index=i,progress=progress,goal=goal,deadline=deadline))
    q=meter.step(parent,np.asarray(row['command'],np.float32));z=compare(q,row,final_ft[key]);prefix_checks.append(z)
    if not z['passed']:raise ModelFailure('prefix:'+key+':'+str(i+1)+':'+json.dumps(z))
   if key=='partial':
    i=188;row=truth[key][i];arc=row['reference']['projection']['arc'];progress+=(arc-previous+L/2)%L-L/2
    if progress>=goal:goal=progress+3.24;deadline=i+13
    contexts[key]=[dict(state=snapshot(parent),memory=memory_at(truth[key],i,kind),index=i,progress=progress,goal=goal,deadline=deadline)]
   qualification.append(dict(gate='causal_prefix_'+key,actions=count,ticks=sum(z['raw_ticks'] for z in truth[key][:count]),passed=True,max_errors={k:max(z['errors'][k] for z in prefix_checks) for k in ['speed_m_s','yaw_rate_rad_s','position_m','time_s']}));save(d/'qualification-progress.json',qualification);parent.close();active.remove(parent)
  stage='reference_independence_qualification'
  for key,index,label in [('O',0,'resetO'),('O',91,'Opre92'),('C',90,'Cpre91'),('O',184,'Oterminal185'),('partial',0,'partial408pre189')]:
   ctx=contexts[key][index];kind='O' if key=='O' else 'C';a=branch(ctx,kind);check=fidelity(a,key,ctx['index']);pulse_result=None
   if label=='Cpre91':
    pulse_result=branch(ctx,kind,True);pulse_repeat=branch(ctx,kind,True)
    if fingerprint(pulse_result)!=fingerprint(pulse_repeat):raise ModelFailure('pulse_repeat_qualification')
   b=branch(ctx,kind)
   if fingerprint(a)!=fingerprint(b):raise ModelFailure('nominal_order_repeat_qualification:'+label)
   if label=='Oterminal185' and not(a['rows'][-1]['predicted']['finished'] and a['rows'][-1]['predicted']['raw_ticks']==4):raise ModelFailure('O_terminal4')
   if label=='partial408pre189' and not(a['rows'][-1]['predicted']['finished'] and a['rows'][-1]['predicted']['raw_ticks']==3 and a['controller_memory']['C']['phase']=='DONE'):raise ModelFailure('partial3_phaseDONE')
   qualification.append(dict(gate=label,passed=True,fidelity=check,forecast_rows=len(a['rows']),raw_ticks=sum(z['predicted']['raw_ticks'] for z in a['rows']),terminal_finish=a['rows'][-1]['predicted']['finished'],nominal_repeat_exact=True,pulse_repeat_exact=pulse_result is not None,pulse_valid=None if pulse_result is None else pulse_result['valid']));save(d/'qualification-progress.json',qualification)
  save(d/'qualification.json',dict(passed=True,records=qualification));stage='chronological_windows'
  rawfile=(d/'forecasts-private.jsonl').open('x');(d/'forecasts-private.jsonl').chmod(0o600)
  try:
   for key,limit in [('O',185),('C',91)]:
    kind=key
    for index,ctx in enumerate(contexts[key][:limit]):
     nominal=branch(ctx,kind);repeat=branch(ctx,kind)
     if fingerprint(nominal)!=fingerprint(repeat):raise ModelFailure('window_nominal_independence:'+key+':'+str(index+1))
     rawfile.write(json.dumps(dict(arm=key,step=index+1,recipe='nominal',sealed_before_evaluator=True,forecast=nominal),allow_nan=False)+'\n');rawfile.flush();check=fidelity(nominal,key,index);actual=truth[key][index:index+13];safe=True;goalhit=False;s=ctx['progress'];prev=actual[0]['reference']['projection']['arc']
     for k,row in enumerate(actual):
      qp=row['post_projection'];s+=(qp['arc']-prev+L/2)%L-L/2;prev=qp['arc'];bodyforward=np.asarray(row['post']['vel'])@np.asarray([-math.sin(row['post']['angle']),math.cos(row['post']['angle'])]);bad=qp['path_error_m']>3 or row['collision'] or row['damage']>0 or not all(n>0 for n in row['post']['road_contacts']) or any(z['grass'] for z in row['raw_tire_samples']) or bodyforward<-.1 or qp['sigma']<-.1;safe=safe and not bad;goalhit=goalhit or (index+k+1<=ctx['deadline'] and (s>=ctx['goal'] or row['completed']))
     candidate=None
     if not nominal['valid']:
      candidate=branch(ctx,kind,True);repeat_pulse=branch(ctx,kind,True)
      if fingerprint(candidate)!=fingerprint(repeat_pulse):raise ModelFailure('window_pulse_independence:'+key+':'+str(index+1))
      rawfile.write(json.dumps(dict(arm=key,step=index+1,recipe='pulse',forecast=candidate),allow_nan=False)+'\n');rawfile.flush()
     predsafe=not nominal['safety_flags'] and nominal['domain'] is None;rec=dict(arm=key,step=index+1,overlapping_window=True,nominal_prediction_safe=predsafe,actual_nominal_safe=safe,nominal_progress_ok=nominal['progress_ok'],actual_progress_ok=goalhit,safety_false_positive=not predsafe and safe,safety_false_negative=predsafe and not safe,progress_false_positive=not nominal['progress_ok'] and goalhit,progress_false_negative=nominal['progress_ok'] and not goalhit,nominal_domain=nominal['domain'],terminal_partial_window=len(actual)<13,forecast_actions=len(nominal['rows']),fidelity=check,intervene=candidate is not None and candidate['valid'],candidate_queried=candidate is not None,candidate_valid=None if candidate is None else candidate['valid'],candidate_domain=None if candidate is None else candidate['domain'],infeasible=not nominal['valid'] and (candidate is None or not candidate['valid']),goal_remaining_actions=ctx['deadline']-index);windows.append(rec);save(d/'window-progress.json',dict(completed=len(windows),last=rec,budget=meter.b))
     if len(windows)%30==0:print(json.dumps(dict(stage=410,windows=len(windows),arm=key,budget=meter.b)),flush=True)
  finally:rawfile.close()
  status='COMPLETED_STORED_WINDOW_AUDIT'
 except BaseException as e:
  failure=dict(stage=stage,error=type(e).__name__+': '+str(e));status='RESOURCE_STOP' if isinstance(e,BudgetStop) else 'MODEL_OR_INDEPENDENCE_UNQUALIFIED' if isinstance(e,ModelFailure) else 'TECHNICAL_STOP';save(d/'failure-private.json',dict(**failure,traceback=traceback.format_exc()))
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in old.items():signal.signal(s,h)
  for m in active:m.close()
  meter.persist()
 totals={}
 for key in ['O','C']:
  subset=[z for z in windows if z['arm']==key];totals[key]=dict(completed_windows=len(subset),planned_windows=185 if key=='O' else 91,unexamined_windows=(185 if key=='O' else 91)-len(subset),**{f:sum(bool(z[f]) for z in subset) for f in ['safety_false_positive','safety_false_negative','progress_false_positive','progress_false_negative','terminal_partial_window','intervene','candidate_queried','infeasible']},nominal_progress_failures=sum(not z['nominal_progress_ok'] for z in subset),actual_progress_failures=sum(not z['actual_progress_ok'] for z in subset),nominal_domains=sum(z['nominal_domain'] is not None for z in subset))
 out=dict(stage=410,status=status,failure=failure,qualification=qualification,qualification_passed=(d/'qualification.json').exists(),window_totals=totals,windows=windows,budget=meter.b,static_cost=static_result,wholeworker_CPU_s=time.process_time(),overlapping_windows_not_independent_episodes=True,C_tail12_censored_not_examined=True,new_native_actor_learning_SEALED_reserve_paid=0,no_actual_policy_or_fallback_validation=True);save(d/'result.json',out);print(json.dumps(dict(stage=410,status=status,failure=failure,window_totals=totals,budget=meter.b)),flush=True)
if __name__=='__main__':
 root=Path(sys.argv[2]);{'static':static,'prepare':prepare,'run':run}[sys.argv[1]](root)
