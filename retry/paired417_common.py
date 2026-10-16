"""Research-only signed C adapters, exclusive model/native accounting and 13-action forecasts."""
import contextlib,copy,datetime,json,math,signal,time
from pathlib import Path
import numpy as np
from retry.signed417_executor import CoherentExecutor
from retry.terminal410_run import Controller,rnghash,ModelFailure
from retry.closed411_run import ActualController
from retry.terminal410_model import TerminalVehicleTransition,snapshot
from retry.branch401_gate import fingerprint
from retry.headroom413_run import Trace,metrics,row_fidelity,wheel_compare,hull_compare
from retry.loss389_analyze import read,save
from retry.executor397 import canonical_projection

class Stop(RuntimeError):pass
class Ineligible(Stop):pass
class SafetyStop(Stop):pass

def policy(fixed,pace):
 c=CoherentExecutor(fixed);c.nodes=np.asarray(fixed['free_profile']['speed'])*pace;return c
class SourceC(Controller):
 def __init__(self,fixed,pace,memory):
  super().__init__(fixed,pace,'C',memory);self.policy=policy(fixed,pace)
  for k,v in memory['C'].items():setattr(self.policy,k,v)
class ActualC(ActualController):
 def __init__(self,env,fixed,pace):super().__init__(env,fixed,pace,'C');self.policy=policy(fixed,pace)
class Meter:
 def __init__(self,d):
  self.d=d;self.p=read(d/'plan.json');self.mb=dict(ticks=0,reserved_ticks=0,worlds=0,CPU_s=0.,wall_s=0.,regions=[]);self.nb=dict(actions=0,resets=0,CPU_s=0.,wall_s=0.,arm_actions={});self.active=None;self.actual_start=None;self.model_base=None;self.queries=[]
 def modeltime(self):
  return (self.mb['CPU_s']+(time.process_time()-self.active[0] if self.active else 0),self.mb['wall_s']+(time.perf_counter()-self.active[1] if self.active else 0))
 def nativetime(self):
  if not self.actual_start:return self.nb['CPU_s'],self.nb['wall_s']
  mc,mw=self.modeltime();return(time.process_time()-self.actual_start[0]-(mc-self.model_base[0]),time.perf_counter()-self.actual_start[1]-(mw-self.model_base[1]))
 def persist(self):
  mc,mw=self.modeltime();nc,nw=self.nativetime();save(self.d/'budget.json',dict(model={**self.mb,'CPU_s':mc,'wall_s':mw},actual={**self.nb,'CPU_s':nc,'wall_s':nw},exclusive_accounting=True))
 def guard(self):
  self.persist();mc,mw=self.modeltime();nc,nw=self.nativetime()
  if mc>=45 or mw>=90:raise Stop('modelCPU45_wall90')
  if nc>=90 or nw>=180:raise Stop('actualCPU90_wall180')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.p['deadline_utc'].replace('Z','+00:00')):raise Stop('deadline')
 def timers(self):
  if self.active:
   c,w=self.modeltime();limits=(45-c,90-w)
  elif self.actual_start:
   c,w=self.nativetime();limits=(90-c,180-w)
  else:limits=None
  signal.setitimer(signal.ITIMER_PROF,max(.001,limits[0]) if limits else 0);signal.setitimer(signal.ITIMER_REAL,max(.001,limits[1]) if limits else 0)
 @contextlib.contextmanager
 def model(self,label):
  assert self.active is None;self.guard();self.active=(time.process_time(),time.perf_counter());self.timers()
  try:yield
  finally:
   c,w=time.process_time()-self.active[0],time.perf_counter()-self.active[1];self.mb['CPU_s']+=c;self.mb['wall_s']+=w;self.mb['regions'].append(dict(label=label,CPU_s=c,wall_s=w));self.active=None;self.timers();self.persist()
 def begin_actual(self):
  assert self.active is None and self.actual_start is None;self.actual_start=(time.process_time(),time.perf_counter());self.model_base=self.modeltime();self.timers();self.persist()
 def end_actual(self):
  if self.actual_start:self.nb['CPU_s'],self.nb['wall_s']=self.nativetime();self.actual_start=None;self.timers();self.persist()
 def world(self,state):
  assert self.active is not None;self.guard()
  if self.mb['worlds']>=160:raise Stop('world160')
  self.mb['worlds']+=1;self.persist();m=TerminalVehicleTransition(state)
  if not(m.initial_bodies_exact and m.initial_tiles_exact and m.initial_progress_exact and m.initial_finish_exact):m.close();raise ModelFailure('restore_body_tiles_progress_finish')
  return m
 def step(self,m,command):
  assert self.active is not None;self.guard()
  if self.mb['reserved_ticks']+4>8192:raise Stop('modeltick8192')
  self.mb['reserved_ticks']+=4;self.persist();start=m.native_ticks;success=False
  try:q=m.step(command);success=True;return q
  finally:
   n=m.native_ticks-start;self.mb['ticks']+=n
   if success:self.mb['reserved_ticks']-=4-n
   self.persist()
 def charge(self,kind,arm):
  assert self.actual_start and not self.active;self.guard();key='resets' if kind=='reset' else 'actions';limit=2 if key=='resets' else 400
  if self.nb[key]>=limit:raise Stop('actualcap_'+key)
  self.nb[key]+=1
  if kind!='reset':self.nb['arm_actions'][arm]=self.nb['arm_actions'].get(arm,0)+1
  self.persist()

def shapecheck(f,row):
 z=row_fidelity(f,row);h=f['raw_hull'][0];pre=row['pre'];e=dict(position_m=math.dist(h['origin_position'],pre['pos']),speed_m_s=abs(math.hypot(*h['COM_linear_velocity'])-pre['speed']),yaw_rad_s=abs(h['yaw']-pre['yaw']),time_s=abs(h['time']-pre['time']));z['raw_first_pre']=e;z['passed']=z['passed'] and e['position_m']<=.1 and e['speed_m_s']<=.5 and e['yaw_rad_s']<=.05 and e['time_s']<1e-8;return z

def modelrow(meter,m,tr,act,k,line,phase):
 tr.reset();tr.enable()
 try:q=meter.step(m,act)
 finally:tr.disable()
 if len(tr.hulls)!=q['raw_ticks'] or len(tr.rows)!=4*q['raw_ticks']:raise ModelFailure('raw_measurement_coverage')
 proj,why=metrics(q,tr.rows,tr.hulls,line,phase);return dict(offset=k,predicted=q,command=act.tolist(),path_error_m=proj['path_error_m'],safety=why,tires=copy.deepcopy(tr.rows),raw_hull=copy.deepcopy(tr.hulls))

def forecast(meter,state,memory,fixed,pace,index,progress,goal,deadline,recipe='nominal'):
 sh=fingerprint(state);mh=fingerprint(memory);rh=rnghash();m=meter.world(state);ctrl=SourceC(fixed,pace,copy.deepcopy(memory));line=np.asarray(fixed['line']);L=sum(fixed['free_profile']['ds']);prev=canonical_projection(line,list(m.car.hull.position),list(m.car.hull.linearVelocity),ctrl.phase())['arc'];s=progress;rows=[];flags=[];hit=False;domain=None;tr=Trace(lambda:m.t)
 try:
  for k in range(13):
   try:act=ctrl.act(m)
   except Exception as e:domain=type(e).__name__+': '+str(e);break
   if k==0 and recipe=='fullgas':act=act.copy();act[1:]=[1.,0.]
   if k==0 and recipe=='neutralbrake':act=np.asarray([0.,0.,.3],np.float32)
   f=modelrow(meter,m,tr,act,k+1,line,ctrl.phase());q=f['predicted'];arc=canonical_projection(line,q['position'],q['velocity'],ctrl.phase())['arc'];s+=(arc-prev+L/2)%L-L/2;prev=arc;hit=hit or index+k+1<=deadline and(s>=goal or q['finished']);f['progress']=s;rows.append(f);flags.extend(f['safety'])
   if f['safety'] or q['terminal']:break
 finally:tr.disable();m.close()
 if fingerprint(state)!=sh or fingerprint(memory)!=mh or rnghash()!=rh:raise ModelFailure('forecast_input_memory_RNG_mutation')
 return dict(rows=rows,valid=len(rows)==13 and not flags and domain is None and hit,goal_reached=hit,safety=sorted(set(flags)),domain=domain,controller_memory=ctrl.memory(),overhead=tr.overhead())

def sig(f):return fingerprint({k:v for k,v in f.items() if k!='overhead'})
def arrival(rows,line,start_arc,exit_arc):
 L=sum(np.linalg.norm(np.roll(line,-1,axis=0)-line,axis=1));last_arc=start_arc;s=start_arc;last_s=start_arc;last_tick=0;tick=0
 for row in rows:
  q=row.get('predicted');samples=[(tick+h['raw_tick']-1,h['origin_position'],h['COM_linear_velocity']) for h in row['raw_hull']]
  samples.append((tick+(q['raw_ticks'] if q else row['raw_ticks']),q['position'] if q else row['post']['pos'],q['velocity'] if q else row['post']['vel']))
  for t,pos,vel in samples:
   arc=canonical_projection(line,pos,vel,'FIRST_LAP')['arc'];s+=(arc-last_arc+L/2)%L-L/2;last_arc=arc
   if last_s<exit_arc<=s:return dict(reached=True,rawtick_bracket=[last_tick,t],elapsed_bracket_s=[last_tick/50,t/50],interpolated=False)
   last_s=s;last_tick=t
  tick+=q['raw_ticks'] if q else row['raw_ticks']
 return dict(reached=False,rawtick_bracket=None,elapsed_bracket_s=None,interpolated=False)
