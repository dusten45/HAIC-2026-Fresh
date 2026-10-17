"""Metered source-only adapter for frozen419 protocol; no challenge environment."""
import copy,datetime,json,math,time
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save
from retry.branch401_gate import fingerprint
from retry.terminal410_model import TerminalVehicleTransition,snapshot
from retry.terminal410_run import rnghash
from retry.paired417_common import SourceC
from retry.headroom413_run import Trace,metrics,row_fidelity,hull_compare,wheel_compare
from retry.executor397 import canonical_projection
from retry.planner419 import *
from retry.planner419_model_ledger import ForecastLedger,ModelPrediction

class TechnicalStop(RuntimeError):pass
class PilotStop(RuntimeError):pass
class ResourceStop(PilotStop):pass
class Meter:
 def __init__(self,d):
  self.d=d;self.p=read(d/'plan.json');self.wall=time.perf_counter();self.b=dict(ticks=0,reserved_ticks=0,worlds=0,confirmed_worlds=0,ticks_by_tag={},worlds_by_tag={},CPU_by_tag={},wall_by_tag={},max_live_worlds=0);self.live=[]
 def persist(self):self.b.update(CPU_s=time.process_time(),execution_wall_s=time.perf_counter()-self.wall);save(self.d/'budget.json',self.b)
 def guard(self):
  self.persist()
  if time.process_time()>=150 or time.perf_counter()-self.wall>=240:raise ResourceStop('CPU150_wall240')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.p['deadline_utc'].replace('Z','+00:00')):raise ResourceStop('deadline')
 def timing(self,tag,c,w):
  self.b['CPU_by_tag'][tag]=self.b['CPU_by_tag'].get(tag,0)+time.process_time()-c;self.b['wall_by_tag'][tag]=self.b['wall_by_tag'].get(tag,0)+time.perf_counter()-w
 def world(self,state,tag):
  self.guard()
  if self.b['worlds']>=64:raise ResourceStop('world64')
  self.b['worlds']+=1;self.b['worlds_by_tag'][tag]=self.b['worlds_by_tag'].get(tag,0)+1;self.persist();c=time.process_time();w=time.perf_counter()
  try:m=TerminalVehicleTransition(state)
  finally:self.timing(tag+'_world_setup',c,w)
  self.live.append(m);self.b['confirmed_worlds']+=1;self.b['max_live_worlds']=max(self.b['max_live_worlds'],len(self.live));self.persist()
  if not(m.initial_bodies_exact and m.initial_tiles_exact and m.initial_progress_exact and m.initial_finish_exact):raise TechnicalStop('restore_body_tile_progress_finish')
  return m
 def step(self,m,act,tag):
  self.guard()
  if self.b['reserved_ticks']+4>32768:raise ResourceStop('tick32768')
  self.b['reserved_ticks']+=4;self.persist();before=m.native_ticks;c=time.process_time();w=time.perf_counter();success=False
  try:q=m.step(act);success=True;return q
  finally:
   count=m.native_ticks-before;self.b['ticks']+=count;self.b['ticks_by_tag'][tag]=self.b['ticks_by_tag'].get(tag,0)+count
   if success:self.b['reserved_ticks']-=4-count
   self.timing(tag,c,w);self.persist()
 def close(self,m):
  if m in self.live:self.live.remove(m);m.close()
 def closeall(self):
  for m in list(self.live):self.close(m)
  self.persist()

def model_ledger_view(ledger):
 # A value view for current MODEL context only; actual root object is never advanced.
 return GoalLedger(ledger.progress_m,ledger.goal_m,ledger.age_actions,ledger.last_clock_tick,ledger.deadline_missed,ledger.done)

def capture_context(m,ctrl,before,nominal,ledger,fixed,policy_digest,archive_rng,actual_root_digest):
 line=np.asarray(fixed['line']);h=m.car.hull;q=canonical_projection(line,list(h.position),list(h.linearVelocity),ctrl.phase());r,_=ctrl.policy._reference(q);vel=np.asarray(h.linearVelocity);forward=float(vel@np.asarray([-math.sin(h.angle),math.cos(h.angle)]));value_view=model_ledger_view(ledger);state=dict(terminal_model=snapshot(m),provenance='CURRENT_MODEL_PARENT',immutable_actual_root_digest=actual_root_digest);parent=Parent.current(state,before,dict(archived_actual_rng=archive_rng,model_global_rng_digest=rnghash()),ledger.last_clock_tick)
 ctx=Current(parent,value_view,policy_digest,tuple(float(x) for x in nominal),ctrl.phase(),r,q['sigma'],forward,sum(fixed['free_profile']['ds'])-ledger.progress_m,current_safety_qualified=m.damage.damage==0 and not ledger.deadline_missed)
 return ctx

class Child:
 def __init__(self,meter,state,memory,ledger,fixed,pace,label,recipe='nominal',world_tag='required'):
  self.meter=meter;self.fixed=fixed;self.pace=pace;self.line=np.asarray(fixed['line']);self.L=sum(fixed['free_profile']['ds']);self.label=label;self.recipe=recipe;self.m=meter.world(state,world_tag);self.ctrl=SourceC(fixed,pace,copy.deepcopy(memory));self.ledger=ForecastLedger.fork(ledger);self.root_state_digest=fingerprint(state);self.root_memory_digest=fingerprint(memory);self.root_ledger=ledger;self.rows=[];self.status='ACTIVE';self.error=None;self.first_command=None;self.end13=None;self.initial_count=0;self.tail_count=0;self.checkpoints=[];self.last_checkpoint_count=0;self.finish_ticks=None;self.closed=False;self.trace=Trace(lambda:self.m.t);self.previous_arc=canonical_projection(self.line,list(self.m.car.hull.position),list(self.m.car.hull.linearVelocity),self.ctrl.phase())['arc'];self.start_clock=self.ledger.last_clock_tick;self.clockmap={self.m.t:0}
 def _end_vector(self):
  h=self.m.car.hull;last=self.rows[-1];z=last['tires'][-4:];return TerminalVector(float(math.hypot(*h.linearVelocity)),float(h.angularVelocity),last['path_error_m'],tuple(float(x.omega) for x in self.m.car.wheels),tuple(float(x.joint.angle) for x in self.m.car.wheels[:2]),tuple(x['force_ratio'] for x in z),self.L-self.ledger.progress_m,fingerprint(snapshot(self.m)),fingerprint(self.ctrl.memory()))
 def one(self,tag,first_override=None,prepared_nominal=None,prepared_before=None):
  if self.status!='ACTIVE':raise TechnicalStop('step_nonactive_child')
  self.meter.guard();before=copy.deepcopy(self.ctrl.memory() if prepared_before is None else prepared_before);pos=list(self.m.car.hull.position);vel=list(self.m.car.hull.linearVelocity)
  try:
   pre=canonical_projection(self.line,pos,vel,self.ctrl.phase());forward=float(np.asarray(vel)@np.asarray([-math.sin(self.m.car.hull.angle),math.cos(self.m.car.hull.angle)]))
   if pre['sigma']<-.1 or forward<-.1:self.status='UNSAFE';self.error='pre_meaningful_reverse';return
   act=self.ctrl.act(self.m) if prepared_nominal is None else np.asarray(prepared_nominal,np.float32)
  except Exception as e:
   self.error=type(e).__name__+': '+str(e);self.status='TECHNICAL_STOP';raise TechnicalStop(self.label+':'+self.error) from e
  if first_override is not None:act=np.asarray(first_override,np.float32)
  elif not self.rows:
   if self.recipe=='fullgas':act=act.copy();act[1:]=[1.,0.]
   elif self.recipe=='neutralbrake':act=np.asarray([0.,0.,.3],np.float32)
  if not self.rows:self.first_command=tuple(float(x) for x in act)
  raw_start=self.ledger.last_clock_tick-self.start_clock;self.trace.reset();self.trace.enable()
  try:q=self.meter.step(self.m,act,tag)
  finally:self.trace.disable()
  if not(1<=q['raw_ticks']<=4) or len(self.trace.rows)!=4*q['raw_ticks'] or len(self.trace.hulls)!=q['raw_ticks']:raise TechnicalStop('raw_phase_coverage')
  if q['raw_ticks']<4 and not(q['finished'] or q['terminal']):raise TechnicalStop('nonterminal_partial_raw_step')
  for h in self.trace.hulls:self.clockmap[h['time']]=raw_start+h['raw_tick']-1
  self.clockmap[q['time']]=raw_start+q['raw_ticks']
  try:projected,flags=metrics(q,self.trace.rows,self.trace.hulls,self.line,self.ctrl.phase())
  except Exception as e:self.status='TECHNICAL_STOP';self.error=type(e).__name__+': '+str(e);raise TechnicalStop(self.label+':projection_or_numeric:'+self.error) from e
  progress=self.ledger.progress_m+(projected['arc']-self.previous_arc+self.L/2)%self.L-self.L/2;self.previous_arc=projected['arc'];self.ledger=self.ledger.advance_prediction(ModelPrediction(progress,self.ledger.last_clock_tick+q['raw_ticks'],q['finished']))
  row=dict(offset=len(self.rows)+1,predicted=q,command=act.tolist(),memory_before=before,memory_after=copy.deepcopy(self.ctrl.memory()),tires=copy.deepcopy(self.trace.rows),raw_hull=copy.deepcopy(self.trace.hulls),path_error_m=projected['path_error_m'],safety=flags,model_progress=progress,model_goal=self.ledger.goal_m,model_age=self.ledger.age_actions,actual_root_ledger_digest=self.ledger.actual_root_digest);self.rows.append(row)
  if flags:self.status='UNSAFE';self.error=','.join(flags)
  elif self.ledger.deadline_missed:self.status='INFEASIBLE';self.error='predicted_progress_deadline'
  elif q['finished']:
   tracker=self.m.finish_line_tracker
   if q['finish_time_s'] not in self.clockmap or tracker.qualified_time_s is None:raise TechnicalStop('unregistered_official_finish_clock_or_qualification')
   tick=self.clockmap[q['finish_time_s']]
   if tick<=0:raise TechnicalStop('official_finish_not_after_root')
   self.finish_ticks=TickBracket(tick-1,tick);self.status='FINISHED';self.ctrl.done(self.m)
  elif q['terminal']:self.status='CENSORED';self.error='nonfinish_model_terminal'
 def initial13(self,tag):
  while self.status=='ACTIVE' and len(self.rows)<H:self.one(tag)
  self.initial_count=len(self.rows)
  if not self.rows:raise TechnicalStop('initial_no_row')
  self.end13=self._end_vector();self.initial_ok=len(self.rows)==H or self.status=='FINISHED';self.initial_safe=not any(r['safety'] for r in self.rows);self.initial_progress=self.ledger.progress_qualified()
  return self
 def continue_tail(self,tag):
  if self.end13 is None:raise TechnicalStop('tail_before_initial13')
  while self.status=='ACTIVE' and self.tail_count<TAIL_ACTION_CAP:
   self.one(tag);self.tail_count=len(self.rows)-self.initial_count
   if self.tail_count>self.last_checkpoint_count and (self.tail_count-self.last_checkpoint_count==H or self.status!='ACTIVE'):
    self.checkpoints.append(self.tail_count-self.last_checkpoint_count);self.last_checkpoint_count=self.tail_count
  if self.status=='ACTIVE':self.status='CENSORED';self.error='additional308_action_cap'
  if self.tail_count>self.last_checkpoint_count:self.checkpoints.append(self.tail_count-self.last_checkpoint_count);self.last_checkpoint_count=self.tail_count
  return self
 def signature(self):return fingerprint(dict(rows=self.rows,status=self.status,error=self.error,ledger=asdict(self.ledger),memory=self.ctrl.memory(),physical=snapshot(self.m),finish=None if self.finish_ticks is None else asdict(self.finish_ticks)))
 def evidence(self,ctx):
  if not self.initial_ok:raise TechnicalStop('frozen419_cannot_accept_early_unsafe_partial_initial_receipt_no_padding')
  status=self.status if self.status in ['FINISHED','UNSAFE','INFEASIBLE','CENSORED'] else 'UNQUERIED'
  return Evidence(self.recipe,ctx.parent.stamp(),ctx.ledger.digest(),ctx.policy_digest,self.first_command,self.initial_count,True,True,True,True,self.initial_safe,self.initial_progress,self.end13,tail_status=status,finish_ticks=self.finish_ticks if status=='FINISHED' else None,official_finish_qualified=status=='FINISHED',tail_actions_integrated=self.tail_count,checkpoint_actions=tuple(self.checkpoints),long_tail_physics_qualified=False)
 def dump(self,d):
  save(d/(self.label+'-private.json'),dict(recipe=self.recipe,status=self.status,error=self.error,rows=self.rows,initial_actions=self.initial_count,tail_actions=self.tail_count,checkpoints=self.checkpoints,end13=None if self.end13 is None else asdict(self.end13),finish_ticks=None if self.finish_ticks is None else asdict(self.finish_ticks),model_ledger=asdict(self.ledger),final_state=snapshot(self.m),controller_memory=self.ctrl.memory(),telemetry=self.trace.overhead(),long_tail_physics_qualified=False))
 def close(self):
  self.trace.disable()
  if not self.closed:self.meter.close(self.m);self.closed=True
