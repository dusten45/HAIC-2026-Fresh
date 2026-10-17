"""Limited fresh independent confirmation of stored435 pending; not435 recovery."""
import copy,json
from dataclasses import asdict
from retry.pilot420_backend import *
from retry.observer435 import ObserveMixin,Stream,GuardianChild,current_rng
from retry.guardian426_confirmed import GuardianChild as BaseGuardian
from retry.parent436 import capture_pending,guardian_proof,verify_parent_step
from retry.receipt421_io import load_receipt,save_receipt
from retry.loss389_analyze import read,save
from retry.pilot421_run import compare_frames

class RestoredParent(ObserveMixin,BaseGuardian):
 def __init__(self,*args,full_ledger,**kwargs):
  BaseGuardian.__init__(self,*args,**kwargs);self.ledger=ForecastLedger(**copy.deepcopy(full_ledger));self.stream=Stream(self)

def saved_history(root):
 stop=load_receipt(root/'stage435/P_decision55-context-stop-private.json');obs=read(root/'stage435/parent_P-observer-private.json');n=obs['link']['world_number'];start=load_receipt(root/('stage435/world'+str(n)+'-before-constructor-private.json'))['state'];return stop,dict(root=start,ledger=obs['link']['model_ledger'],posts=obs['posts'],actions=obs['actions'])

def qualify(root,meter,fixed,pace):
 d=root/'stage436';stop,history=saved_history(root);state=stop['live_parent'];memory=stop['memory_before_nominal'];full=read(root/'stage435/parent_P-private.json')['model_ledger'];view=GoalLedger(full['progress_m'],full['goal_m'],full['age_actions'],full['last_clock_tick'],full['deadline_missed'],full['done']);rh=rnghash();ld=fingerprint(full);children=[];parent=None;t0=meter.b['ticks'];w0=meter.b['worlds']
 try:
  meter.capture_inputs(state,memory,view,'qualification435_parent_inputs',gate='RESTORE_SAVED435_PENDING_NO_OLD_LAP_RECERTIFICATION');parent=RestoredParent(meter,copy.deepcopy(state),copy.deepcopy(memory),view,fixed,pace,'qualification435_parent',world_tag='qualification435_parent',confirmation_phase='FINISH_CONFIRM',full_ledger=full);before=copy.deepcopy(parent.ctrl.memory());nominal=parent.ctrl.act(parent.m);ctx=capture_context(parent.m,parent.ctrl,before,nominal,parent.ledger,fixed,stop['context']['policy_digest'],{},full['actual_root_digest']);pending=capture_pending(parent,ctx,before,meter.p['semantic_sources'],'RESTORED435_PENDING_QUALIFICATION_ONLY',history);info=pending.validate(parent.stream.child_id,ctx);save_receipt(d/'qualification435-pending-before-private.json',asdict(pending));ph=fingerprint(snapshot(parent.m));mh=fingerprint(parent.ctrl.memory());native=parent.m.native_ticks;signatures=[];proofs=[];first=None
  for rep in range(2):
   tag='qualification435_guardian_required' if rep==0 else 'qualification435_guardian_repeat';label='qualification435_nominal_'+str(rep+1);meter.capture_inputs(snapshot(parent.m),before,ctx.ledger,label+'_inputs',context=ctx,gate='REGISTERED_PENDING_GUARDIAN_ONLY');c=GuardianChild(meter,snapshot(parent.m),copy.deepcopy(before),ctx.ledger,fixed,pace,label,world_tag=tag,confirmation_phase='FINISH_CONFIRM');children.append(c);c.initial13(tag);c.dump(d);valid=c.initial_ok and c.initial_safe and c.initial_progress and c.status=='FINISHED';proof=guardian_proof(pending,c,valid)
   if c.guardian_certificate['event_time_s']!=info['event_time_s'] or c.guardian_certificate['kind']!='AT_ROOT_CONFIRMED_IN_MODEL':raise TechnicalStop('stored435_pending_not_same_AT_ROOT_confirmation')
   if fingerprint(snapshot(parent.m))!=ph or fingerprint(parent.ctrl.memory())!=mh or parent.m.native_ticks!=native or parent.ledger.done or rnghash()!=rh or fingerprint(full)!=ld:raise TechnicalStop('guardian_prediction_committed_parent_or_RNG_ledger')
   if first is None:first=copy.deepcopy(c.rows[0])
   signatures.append(c.signature());proofs.append(dict(child_id=c.stream.child_id,certificate=c.guardian_certificate,parent_done_after_prediction=parent.ledger.done));save_receipt(d/(label+'-proof-private.json'),asdict(proof));c.close()
  if signatures[0]!=signatures[1]:raise TechnicalStop('stored435_pending_guardian_repeat')
  parent.one('qualification435_parent_own_step',first_override=first['command'],prepared_nominal=nominal,prepared_before=before);own=verify_parent_step(pending,parent,native,episode_bracket=False);comparison=compare_frames(parent.rows[-1],first)
  if not comparison['passed'] or comparison['wheel']['clipped_flag_mismatches'] or not own['official_finished'] or not parent.ledger.done or rnghash()!=rh:raise TechnicalStop('stored435_own_parent_confirmation_or_first_transition')
  if meter.b['ticks']-t0>108 or meter.b['worlds']-w0!=3:raise ResourceStop('pending_qualification108ticks3worlds')
  result=dict(passed=True,restored435_historical_still_stop=True,old435_recertified=False,new_restored_model_confirmation_only=True,parent_done_before_own_step=False,guardian_repeats=proofs,parent_own_confirmation=own,first_transition=comparison,new_ticks=meter.b['ticks']-t0,new_worlds=meter.b['worlds']-w0,actual_DONE_allowed=False);save(d/'parent-pending-qualification.json',result);return result
 finally:
  for c in children:
   if not c.closed:
    try:c.dump(d)
    finally:c.close()
  if parent:
   try:parent.dump(d)
   finally:parent.close()
