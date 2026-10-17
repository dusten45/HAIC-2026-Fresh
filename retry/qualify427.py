"""Limited independent model confirmation at saved425 pending root; no actual DONE."""
import copy,json
from retry.carry427_model import *
from retry.guardian426_confirmed import GuardianChild
from retry.pilot421_run import compare_frames

def qualify(root,meter,fixed,pace):
 d=root/'stage427';full=read(root/'stage425/actual_P/final-private.json');last=json.loads((root/'stage425/actual_P/trace-private.jsonl').read_text().splitlines()[-1]);memory=last['nominal_memory_after'];ledger=GoalLedger(**read(root/'stage425/actual_P/result.json')['actual_ledger']);state=from_actual_full(full);failed=read(root/'stage425/actual_P/actual_P_177_nominal_1-private.json')['rows'][0];rh=rnghash();sh=fingerprint(state);mh=fingerprint(memory);ld=ledger.digest();children=[];held=None
 meter.phase_tag='qualification_'
 with meter.model('saved425_pending_root_qualification'):
  try:
   held=GuardianChild(meter,state,memory,ledger,fixed,pace,'held_pending_root',world_tag='parent');nominal=held.ctrl.act(held.m);ph=fingerprint(snapshot(held.m));ch=fingerprint(held.ctrl.memory());signatures=[];certificates=[];checks=[]
   for rep in range(2):
    tag='required' if rep==0 else 'repeat';c=GuardianChild(meter,state,memory,ledger,fixed,pace,'pending_nominal_'+str(rep+1),world_tag=tag,confirmation_phase=held.ctrl.phase());children.append(c);c.initial13(tag);c.dump(d);z=compare_frames(c.rows[0],failed)
    if not z['passed'] or z['wheel']['clipped_flag_mismatches']!=0 or c.status!='FINISHED' or len(c.rows)!=1 or c.guardian_certificate['kind']!='AT_ROOT_CONFIRMED_IN_MODEL' or c.guardian_certificate['actual_done_allowed']:raise TechnicalStop('pending_guardian_model_qualification')
    if c.first_command!=tuple(nominal):raise TechnicalStop('pending_guardian_nominal_action_changed')
    if fingerprint(snapshot(held.m))!=ph or fingerprint(held.ctrl.memory())!=ch or rnghash()!=rh or fingerprint(state)!=sh or fingerprint(memory)!=mh or ledger.digest()!=ld:raise TechnicalStop('pending_held_parent_RNG_memory_ledger_changed')
    signatures.append(c.signature());certificates.append(c.guardian_certificate);checks.append(z);c.close()
   if signatures[0]!=signatures[1] or certificates[0]!=certificates[1]:raise TechnicalStop('pending_guardian_independent_repeat')
   if full['wrapper']['finish_time_s'] is not None:raise TechnicalStop('saved425_actual_finish_relabelled')
   result=dict(passed=True,model_repeats=2,model_raw_ticks=2,worlds=3,certificates=certificates,old_failed_model_transition_comparisons=checks,held_parent_memory_RNG_ledger_unchanged=True,saved425_actual_finish_still_unobserved=True,nominal_action_unchanged=True);save(d/'qualification.json',result);return result
  finally:
   for c in children:
    if not c.closed:
     try:c.dump(d)
     finally:c.close()
   if held:
    try:held.dump(d)
    finally:held.close()
