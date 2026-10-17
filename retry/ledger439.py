"""Actual observation is authority; model ledger is a branch-bounded comparison."""
import copy,math
from dataclasses import asdict
from retry.geometry439 import Projection439,Interval,GeometryStop439
from retry.planner419 import GoalLedger,ActualObservation,PROGRESS_GOAL_M,H
from retry.planner419_model_ledger import ForecastLedger,ModelPrediction
from retry.executor397 import canonical_projection
from retry.paired417_common import shapecheck
from retry.headroom413_run import metrics
from retry.canonical438 import compare,canonical
class LedgerStop439(ValueError):pass

def require(value,reason):
 if not value:raise LedgerStop439(reason)
def equal(a,b):return compare(a,b)['equal']
def typed_ledger(ledger):
 require(type(ledger) is GoalLedger,'ACTUAL_LEDGER_TYPE_REQUIRED');canonical(asdict(ledger));require(type(ledger.deadline_missed) is bool and type(ledger.done) is bool,'LEDGER_DISCRETE_TYPE');require(not ledger.done and not ledger.deadline_missed and ledger.age_actions<H,'ACTUAL_PREVIOUS_LEDGER_STOPPED')
def advance_source(progress,post,pre,L):return progress+(post-pre+L/2)%L-L/2

def derive_actual(old,pre,post,phase_before,phase_after,raw_ticks,completed,line,L):
 """No forecast argument or forecast read exists in this calculation."""
 typed_ledger(old);canonical(dict(pre=pre,post=post,phase_before=phase_before,phase_after=phase_after,completed=completed));require(type(completed) is bool and type(raw_ticks) is int and 1<=raw_ticks<=4,'NATIVE_DISCRETE_TYPE_OR_TICKS');require(round(pre['time']*50)==old.last_clock_tick and round(post['time']*50)==old.last_clock_tick+raw_ticks and abs((post['time']-pre['time'])-raw_ticks/50)<1e-8,'NATIVE_CLOCK')
 a=canonical_projection(line,pre['pos'],pre['vel'],phase_before);b=canonical_projection(line,post['pos'],post['vel'],phase_after);progress=advance_source(old.progress_m,b['arc'],a['arc'],L);candidate=old.advance_actual(ActualObservation(progress,old.last_clock_tick+raw_ticks,completed));hit=bool(progress>=old.goal_m or completed)
 return candidate,dict(pre_projection=a,post_projection=b,goal_hit=hit,actual_only=True)

def row_candidate(old,row,line,L):
 phase_before=row['memory_before']['C']['phase'];phase_after=row['nominal_memory_after']['C']['phase'];candidate,proof=derive_actual(old,row['pre'],row['post'],phase_before,phase_after,row['raw_ticks'],row['completed'],line,L)
 require(equal(row['progress_before'],old.progress_m) and equal(row['goal_before'],old.goal_m) and equal(row['progress_after'],candidate.progress_m),'CLAIMED_ACTUAL_PROGRESS_OR_GOAL_TAMPER');require(row['goal_hit_actual_step']==proof['goal_hit'],'CLAIMED_GOAL_HIT_TAMPER');return candidate,proof

def geometry_transition(projection,frame,row):
 h=frame['raw_hull'][0];return projection.transition(row['pre'],row['post'],dict(pos=h['origin_position'],vel=h['COM_linear_velocity']),dict(pos=frame['predicted']['position'],vel=frame['predicted']['velocity']),row['memory_before']['C']['phase'],row['nominal_memory_after']['C']['phase'])

def compare_ledgers(actual_old,actual_candidate,model_old,model_candidate,actual_hit,model_hit,model_progress_interval,old_goal_interval):
 require(actual_hit==model_hit,'GOAL_BOUNDARY_REVERSAL');require((actual_candidate.progress_m>=actual_old.goal_m)==(model_candidate.progress_m>=model_old.goal_m),'NUMERIC_GOAL_BOUNDARY_REVERSAL_EVEN_IF_DONE')
 for field in ['age_actions','last_clock_tick','deadline_missed','done']:require(type(getattr(actual_candidate,field)) is type(getattr(model_candidate,field)) and getattr(actual_candidate,field)==getattr(model_candidate,field),'DISCRETE_'+field.upper()+'_MISMATCH')
 require(not actual_candidate.deadline_missed,'ACTUAL_PROGRESS_DEADLINE')
 require(model_progress_interval.contains(model_candidate.progress_m) and model_progress_interval.contains(actual_candidate.progress_m),'CONTINUOUS_PROGRESS_OUTSIDE_GEOMETRY_BOUND')
 if actual_candidate.done:goal_interval=old_goal_interval
 elif actual_hit:goal_interval=model_progress_interval+Interval.point(PROGRESS_GOAL_M)
 else:goal_interval=old_goal_interval
 require(goal_interval.contains(model_candidate.goal_m) and goal_interval.contains(actual_candidate.goal_m),'CONTINUOUS_GOAL_OUTSIDE_ANCHOR_BOUND')
 return dict(progress_interval=model_progress_interval.values(),goal_interval=goal_interval.values(),progress_difference_m=model_candidate.progress_m-actual_candidate.progress_m,goal_difference_m=model_candidate.goal_m-actual_candidate.goal_m,goal_hit_exact=True,clock_age_deadline_DONE_exact=True,actual_authority='NATIVE_OBSERVATION_ONLY'),goal_interval

def compare_first(old,frame,row,fixed,position_tolerance=.1,require_current_root=True):
 canonical(frame);canonical(row);line=fixed['line'];L=sum(fixed['free_profile']['ds']);projection=Projection439(line,L,position_tolerance);actual,observed=row_candidate(old,row,line,L)
 require(equal(frame['command'],row['command']),'DISPATCH_COMMAND_MISMATCH');fidelity=shapecheck(frame,row);require(fidelity['passed'] and fidelity['wheel']['clipped_flag_mismatches']==0,'UNCHANGED_PHYSICAL_FIDELITY')
 require(compare(frame['memory_before'],row['memory_before'])['equal'],'CURRENT_MEMORY_BEFORE_MISMATCH');require(compare(frame['memory_after'],row['nominal_memory_after'])['equal'],'NOMINAL_MEMORY_AFTER_MISMATCH')
 # act()/nominal memory is computed BEFORE physics. It stays exact at copied
 # current inputs; future replay memory drift is not a first-transition proof.
 if require_current_root:
  h=frame['raw_hull'][0];pre=row['pre'];require(h['origin_position']==pre['pos'] and h['COM_linear_velocity']==pre['vel'] and h['angle']==pre['angle'] and h['yaw']==pre['yaw'] and h['time']==pre['time'],'CURRENT_RESTORE_INPUT_DRIFT')
  require(frame['actual_root_ledger_digest']==old.digest(),'OTHER_ACTUAL_LEDGER_ROOT')
 transition=geometry_transition(projection,frame,row);expected=projection.progress(old.progress_m,transition,'model');require(equal(frame['model_progress'],expected),'FORECAST_PROGRESS_NOT_FROM_OWN_GEOMETRY')
 model=ForecastLedger.fork(old).advance_prediction(ModelPrediction(expected,old.last_clock_tick+frame['predicted']['raw_ticks'],frame['predicted']['finished']));require(equal(frame['model_goal'],model.goal_m) and equal(frame['model_age'],model.age_actions),'FORECAST_SELF_CONSISTENCY')
 require(type(frame['predicted']['finished']) is bool and type(frame['predicted']['raw_ticks']) is int,'FORECAST_DISCRETE_TYPE');require(model.last_clock_tick==actual.last_clock_tick and frame['predicted']['finished']==row['completed'],'CLOCK_OR_DONE_MISMATCH')
 modelhit=bool(expected>=old.goal_m or frame['predicted']['finished']);bound=projection.progress_interval(Interval.point(old.progress_m),transition);report,_=compare_ledgers(old,actual,ForecastLedger.fork(old),model,observed['goal_hit'],modelhit,bound,Interval.point(old.goal_m))
 _,af=metrics(dict(position=row['post']['pos'],velocity=row['post']['vel'],angle=row['post']['angle'],damage=row['damage'],collision=row['collision'],wheel_road_contacts=sum(n>0 for n in row['post']['road_contacts'])),row['raw_tire_samples'],row['raw_hull'],projection.line,row['nominal_memory_after']['C']['phase']);_,mf=metrics(frame['predicted'],frame['tires'],frame['raw_hull'],projection.line,frame['memory_after']['C']['phase']);require(not af and not mf and not row['safety'] and not frame['safety'],'UNCHANGED_SAFETY')
 report.update(geometry=transition,fidelity=fidelity,memory_exact_at_current_inputs=True,model_replaces_actual=False,actual_candidate=asdict(actual),actual_execution_allowed=False,actual_DONE_authorized=False)
 return actual,report
