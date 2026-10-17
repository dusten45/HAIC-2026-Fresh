"""Fresh candidate P4 allocation pending fixture,3 worlds maximum. No actual DONE."""
import copy
from dataclasses import asdict
from retry.observer435 import GuardianChild
from retry.qualify_parent453 import saved_history,RestoredParent
from retry.pilot420_backend import GoalLedger,ForecastLedger,fingerprint,snapshot,rnghash,TechnicalStop
from retry.pilot421_run import compare_frames
from retry.loss389_analyze import read,save
from retry.law477 import ReferencePolicy477,ALLOCATED,one477
from retry.law468 import profile_inputs468,PROJECTED_SHA

def qualify_pending477(root,meter,fixed,pace):
 stop,history=saved_history(root);state=stop['live_parent'];memory=stop['memory_before_nominal'];full=read(root/'stage435/parent_P-private.json')['model_ledger'];view=GoalLedger(full['progress_m'],full['goal_m'],full['age_actions'],full['last_clock_tick'],full['deadline_missed'],full['done']);_,projected,path=profile_inputs468(root,fixed,pace);binding=ReferencePolicy477(ALLOCATED,projected,PROJECTED_SHA);rootstamp=(fingerprint(state),fingerprint(memory),fingerprint(full),rnghash());children=[];t0,w0=meter.b['ticks'],meter.b['worlds'];signatures=[];first=None;held=None;packets=[]
 def make(label):
  meter.capture_inputs(state,memory,view,label+'_inputs',gate='477_CANDIDATE_PENDING_NO_HISTORICAL_RECIPE_AUTHORITY')
  child=RestoredParent(meter,copy.deepcopy(state),copy.deepcopy(memory),view,fixed,pace,label,world_tag='477_candidate_pending',confirmation_phase='FINISH_CONFIRM',full_ledger=full);binding.inject(child);children.append(child);return child
 def immutable():
  if (fingerprint(state),fingerprint(memory),fingerprint(full),rnghash())!=rootstamp:raise TechnicalStop('477_pending_root_mutation')
 try:
  held=make('AllocationP4_pending_held');heldstamp=(fingerprint(snapshot(held.m)),fingerprint(held.ctrl.memory()),fingerprint(asdict(held.ledger)),held.m.native_ticks)
  event=state['finish_tracker']['candidate_crossing_time_s']
  if event is None or state['finish_tracker']['finish_time_s'] is not None:raise TechnicalStop('477_pending_fixture_domain')
  for rep in [1,2]:
   c=make('AllocationP4_pending_'+str(rep))
   for k in range(13):
    if c.status!='ACTIVE':break
    one477(c,ALLOCATED,k,'477_candidate_pending_H13')
   if c.status!='FINISHED' or not c.rows or any(r['safety'] for r in c.rows) or not c.guardian_certificate or c.guardian_certificate['event_time_s']!=event or c.guardian_certificate['actual_done_allowed']:raise TechnicalStop('477_candidate_pending_not_same_official_event')
   if (fingerprint(snapshot(held.m)),fingerprint(held.ctrl.memory()),fingerprint(asdict(held.ledger)),held.m.native_ticks)!=heldstamp:raise TechnicalStop('477_pending_prediction_committed_held')
   signatures.append(c.signature());packets.append(dict(label=c.label,rows=len(c.rows),certificate=c.guardian_certificate,phase='FINISH_CONFIRM',actual_DONE_allowed=False));first=copy.deepcopy(c.rows[0]) if first is None else first;c.dump(meter.d);c.close();immutable()
  if signatures[0]!=signatures[1]:raise TechnicalStop('477_candidate_pending_repeat')
  one477(held,ALLOCATED,0,'477_candidate_pending_held_own')
  z=compare_frames(held.rows[0],first)
  if not z['passed'] or z['wheel']['clipped_flag_mismatches'] or held.rows[0]['command']!=first['command'] or held.rows[0]['memory_before']!=first['memory_before'] or held.rows[0]['memory_after']!=first['memory_after'] or held.status!='FINISHED' or not held.ledger.done or held.guardian_certificate['event_time_s']!=event:raise TechnicalStop('477_candidate_pending_held_first')
  immutable();held.dump(meter.d)
  if meter.b['worlds']-w0!=3 or meter.b['ticks']-t0>108:raise TechnicalStop('477_candidate_pending_cost')
  out=dict(passed=True,worlds=3,ticks=meter.b['ticks']-t0,independent_repeat_exact=True,held_first_passed=True,full_ForecastLedger_preserved=True,certificate=held.guardian_certificate,cohorts=packets,actual_DONE_allowed=False,historical_recipe_authority_claimed=False);save(meter.d/'candidate-pending-qualification.json',out);return out
 finally:
  for c in children:
   if not c.closed:
    try:c.dump(meter.d)
    finally:c.close()
