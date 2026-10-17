"""Native commit boundary. No runner or default authorization to call env.step."""
import copy
from dataclasses import asdict
from retry.actual437_boundary import Dispatch437
from retry.loss389_replay import sensor
from retry.pedal331_run import rng
from retry.canonical438 import compare,canonical
from retry.ledger439 import require,derive_actual,compare_first,typed_ledger
from retry.executor397 import canonical_projection
from retry.headroom413_run import metrics
from retry.pilot398_run import safety_flags,raw_capture_pairs
class NativeAuthority439:
 def __init__(self,env,ctrl,ledger,fixed,*,charge_native=None):
  typed_ledger(ledger);self.env=env;self.ctrl=ctrl;self._ledger=ledger;self.fixed=fixed;self.dispatcher=Dispatch437(env,'NATIVE439');self.charge_native=charge_native;self.prepared=None;self.ticket=None;self.rows=[];self._bound_env=env;self._bound_ctrl=ctrl;self.halted=False;self.failure=None;self.awaiting_verification=False;self._observation_record=None;self.last_verification=None
 @property
 def ledger(self):return self._ledger
 def prepare_before_nominal(self):
  require(not self.halted,'AUTHORITY_HALTED');require(self.env is self._bound_env and self.ctrl is self._bound_ctrl and self.ticket is None and self.prepared is None and not self.awaiting_verification,'NATIVE_OWNER_OR_SEQUENCE');require(not self.ledger.done and not self.ledger.deadline_missed,'PREPARE_AFTER_ACTUAL_STOP');pre=sensor(self.env);canonical(pre);require(not safety_flags(pre,canonical_projection(self.fixed['line'],pre['pos'],pre['vel'],self.ctrl.phase()),float(self.env.damage.damage),0.) and not raw_capture_pairs(self.env),'ACTUAL_PRE_SAFETY');require(round(pre['time']*50)==self.ledger.last_clock_tick,'PREPARE_ACTUAL_CLOCK');self.prepared=copy.deepcopy(dict(pre=pre,memory=self.ctrl.memory(),phase=self.ctrl.phase(),RNG=rng(self.env),ledger=asdict(self.ledger),tracker=dict(self.env.unwrapped.finish_line_tracker.__dict__)));return copy.deepcopy(self.prepared)
 def dispatch(self,command,trace):
  require(not self.halted,'AUTHORITY_HALTED')
  try:return self._dispatch_checked(command,trace)
  except BaseException as e:self.halted=True;self.failure=type(e).__name__+': '+str(e);raise
 def _dispatch_checked(self,command,trace):
  # 439 never supplies this capability. A future explicitly authorized runner
  # must provide its charge-before-dispatch function with its own caps.
  require(callable(self.charge_native),'NO_NATIVE_AUTHORIZATION_IN_STATIC439');require(self.prepared is not None and self.ticket is None,'NATIVE_PREPARE_REQUIRED');root=self.prepared;require(compare(root['pre'],sensor(self.env))['equal'] and compare(root['RNG'],rng(self.env))['equal'] and root['ledger']==asdict(self.ledger),'ACTUAL_ROOT_MUTATED_DURING_FORECAST');memory=copy.deepcopy(self.ctrl.memory());phase=self.ctrl.phase();self.charge_native();out,ticket=self.dispatcher.call(command,trace);self.ticket=ticket;ticket.native_prepared=copy.deepcopy(root);ticket.nominal_memory=memory;ticket.nominal_phase=phase;ticket.native_post=copy.deepcopy(sensor(self.env));ticket.native_out=out;ticket.native_tires=copy.deepcopy(trace.rows);ticket.native_hulls=copy.deepcopy(trace.hulls);return out
 def observed_row(self):
  require(self.env is self._bound_env and self.ctrl is self._bound_ctrl,'NATIVE_OWNER_CHANGED');ticket=self.ticket;require(ticket is self.dispatcher.ticket and ticket is not None and ticket.owner is self.dispatcher and ticket.env is self.env and ticket.success,'OWN_SUCCESSFUL_NATIVE_TICKET_REQUIRED');require(compare(sensor(self.env),ticket.native_post)['equal'] and compare(self.ctrl.memory(),ticket.nominal_memory)['equal'] and self.prepared['ledger']==asdict(self.ledger),'ACTUAL_OBSERVATION_CHANGED_AFTER_DISPATCH');root=ticket.native_prepared;post=ticket.native_post;_,_,ended,truncated,info=ticket.native_out;finished=self.env.unwrapped.finish_time_s is not None;raw=round((post['time']-root['pre']['time'])*50);candidate,proof=derive_actual(self.ledger,root['pre'],post,root['phase'],ticket.nominal_phase,raw,finished,self.fixed['line'],sum(self.fixed['free_profile']['ds']));q=dict(position=post['pos'],velocity=post['vel'],angle=post['angle'],damage=float(self.env.damage.damage),collision=bool(info['collision']),wheel_road_contacts=sum(n>0 for n in post['road_contacts']));projection,flags=metrics(q,ticket.native_tires,ticket.native_hulls,self.fixed['line'],ticket.nominal_phase)
  row=dict(pre=root['pre'],post=post,command=ticket.command,nominal_memory_after=ticket.nominal_memory,memory_before=root['memory'],raw_ticks=raw,completed=finished,finish_time_s=self.env.unwrapped.finish_time_s,ended=bool(ended),truncated=bool(truncated),collision=q['collision'],damage=q['damage'],raw_tire_samples=ticket.native_tires,raw_hull=ticket.native_hulls,post_projection=projection,safety=flags,progress_before=self.ledger.progress_m,goal_before=self.ledger.goal_m,progress_after=candidate.progress_m,goal_hit_actual_step=proof['goal_hit']);self.dispatcher.check(ticket,row)
  # Native raw tracker/corridor/safety and pending event are checked without any
  # guardian certificate granting DONE. All posts came from this own env.step.
  event=root['tracker']['candidate_crossing_time_s'];tracker=self.env.unwrapped.finish_line_tracker
  if event is not None:require((tracker.finish_time_s==event if finished else tracker.candidate_crossing_time_s==event and tracker.finish_time_s is None),'ACTUAL_PENDING_EVENT_CHANGED')
  require(not raw_capture_pairs(self.env),'ACTUAL_NEW_OBSTACLE_CONTACT');require(len(ticket.posts)==raw and all(not p['collision'] and p['wheel_road_contacts']==4 for p in ticket.posts),'ACTUAL_RAW_CONTACT_OR_COLLISION');return row,candidate
 def commit_native_observation(self):
  require(not self.halted and not self.awaiting_verification,'AUTHORITY_HALTED_OR_AWAITING_VERIFICATION')
  try:
   row,observed=self.observed_row();before=self.ledger;record=dict(previous=before,observed=observed,row=copy.deepcopy(row),native_sequence=self.dispatcher.calls)
   # This assignment has no forecast input, model success condition or value.
   self._ledger=observed;self.rows.append(copy.deepcopy(row));self.dispatcher.consume(self.ticket);self.ticket=None;self.prepared=None;self.awaiting_verification=True;self._observation_record=record
   return dict(actual_ledger=asdict(self.ledger),native_fact_committed=True,forecast_verification_pending=True,overall_verification_success=False)
  except BaseException as e:self.halted=True;self.failure=type(e).__name__+': '+str(e);raise
 def verify_forecast(self,model_first):
  require(not self.halted and self.awaiting_verification and self._observation_record is not None,'AUTHORITY_HALTED_OR_NO_NATIVE_OBSERVATION')
  try:
   record=self._observation_record;candidate,comparison=compare_first(record['previous'],model_first,record['row'],self.fixed);require(candidate==record['observed']==self.ledger,'ACTUAL_CANDIDATE_CHANGED_BY_FORECAST');require(not candidate.deadline_missed and not record['row']['safety'],'ACTUAL_SAFETY_OR_PROGRESS');self.last_verification=dict(passed=True,native_sequence=record['native_sequence']);self.awaiting_verification=False;self._observation_record=None
   return dict(actual_ledger=asdict(self.ledger),comparison=comparison,actual_committed_from_native_only=True,model_values_committed=False,overall_verification_success=True)
  except BaseException as e:
   self.halted=True;self.failure=type(e).__name__+': '+str(e);self.last_verification=dict(passed=False,error=self.failure,actual_fact_retained=True);raise
 def commit(self,model_first):
  self.commit_native_observation();return self.verify_forecast(model_first)
