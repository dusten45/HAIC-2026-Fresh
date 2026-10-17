"""Guardian completion certificate has no planner ranking time or actual DONE right."""
import copy,math
from dataclasses import asdict
from retry.pilot420_backend import Child,TechnicalStop,snapshot,ModelPrediction,TickBracket,TerminalVector,metrics,canonical_projection,np,fingerprint,save
from retry.signed417_executor import CoherentExecutor
from retry.terminal409_contract import validate

def guardian_finish(root,phase,pred,tracker,clockmap):
 t=float(root['physical']['actual_time']);event=pred['finish_time_s'];post=pred['time'];old=root['finish_tracker'];h=root['physical']['hull']
 if event is None or not all(math.isfinite(x) for x in [t,event,post]) or not(pred['finished'] and pred['terminal']) or post<=t or event>post:raise TechnicalStop('guardian_finish_temporal_metadata')
 if old['finish_time_s'] is not None:raise TechnicalStop('guardian_query_after_current_official_finish')
 if phase not in ['FIRST_LAP','FINISH_CONFIRM']:raise TechnicalStop('guardian_finish_phase')
 if tracker['finish_time_s']!=event or tracker['candidate_crossing_time_s']!=event or not tracker['crossing_from_back'] or tracker['qualified_time_s'] is None or tracker['qualified_time_s']>event:raise TechnicalStop('guardian_finish_confirmation_metadata')
 if event<=t:
  if phase!='FINISH_CONFIRM' or old['candidate_crossing_time_s']!=event or old['qualified_time_s'] is None or old['qualified_time_s']>event:raise TechnicalStop('guardian_unregistered_past_or_root_event')
  sensor=dict(time=t,pos=h['position'],vel=h['velocity'])
  CoherentExecutor._confirm_valid(None,sensor,old)
  kind='AT_ROOT_CONFIRMED_IN_MODEL' if event==t else 'BEFORE_ROOT_CONFIRMED_IN_MODEL'
 else:
  if event not in clockmap or clockmap[event]<=0:raise TechnicalStop('guardian_unregistered_future_event')
  if old['candidate_crossing_time_s'] is not None and old['candidate_crossing_time_s']!=event:raise TechnicalStop('guardian_changed_pending_event')
  kind='AFTER_ROOT_CONFIRMED_IN_MODEL'
 return dict(kind=kind,model_confirmation_qualified=True,event_time_s=event,confirmation_time_s=post,planner_ranking_eligible=False,actual_done_allowed=False)

def actual_done_eligible(row,dispatched):return bool(dispatched and row['completed'] and validate(row)['passed'])

class GuardianChild(Child):
 def __init__(self,*args,confirmation_phase=None,**kwargs):
  super().__init__(*args,**kwargs);self.guardian_root=copy.deepcopy(args[1]);self.confirmation_phase=confirmation_phase;self.guardian_certificate=None
 def evidence(self,ctx):raise TechnicalStop('guardian_certificate_cannot_enter_planner_time_ranking')
 def dump(self,d):
  save(d/(self.label+'-private.json'),dict(recipe=self.recipe,status=self.status,error=self.error,rows=self.rows,initial_actions=self.initial_count,tail_actions=self.tail_count,checkpoints=self.checkpoints,end13=None if self.end13 is None else asdict(self.end13),finish_ticks=None,guardian_certificate=self.guardian_certificate,planner_ranking_eligible=False,model_ledger=asdict(self.ledger),final_state=snapshot(self.m),controller_memory=self.ctrl.memory(),telemetry=self.trace.overhead(),long_tail_actual_physics_qualified=False))
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
   rootphase=self.confirmation_phase or self.rows[0]['memory_after']['C']['phase']
   self.guardian_certificate=guardian_finish(self.guardian_root,rootphase,q,dict(self.m.finish_line_tracker.__dict__),self.clockmap)
   self.finish_ticks=None;self.status='FINISHED';self.ctrl.done(self.m)
  elif q['terminal']:self.status='CENSORED';self.error='nonfinish_model_terminal'
