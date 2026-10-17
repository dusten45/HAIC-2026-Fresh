"""Saved423/427 actual traces are calibration targets only, never planner inputs."""
import copy,json
from dataclasses import asdict
import numpy as np
from retry.pilot420_backend import *
from retry.paired417_common import shapecheck
from retry.pilot421_run import compare_frames
from retry.receipt421_io import load_receipt
from retry.preflight421 import restore_typed
from retry.calibrate422_analyze import maxima

def qualify(root,meter,fixed,pace,state,memory,ledger):
 d=root/'stage428';ld=ledger.digest();sh=fingerprint(state);mh=fingerprint(memory);rh=rnghash();held=Child(meter,state,memory,ledger,fixed,pace,'qualification_held_parent',world_tag='qualification_parent');nominal=held.ctrl.act(held.m);ph=fingerprint(snapshot(held.m));cm=fingerprint(held.ctrl.memory());closed=[];records={};first_C0=None
 def unchanged():
  if fingerprint(snapshot(held.m))!=ph or fingerprint(held.ctrl.memory())!=cm or fingerprint(state)!=sh or fingerprint(memory)!=mh or ledger.digest()!=ld or rnghash()!=rh:raise TechnicalStop('qualification_live_parent_RNG_memory_ledger_mutation')
 try:
  for arm in ['C0','P']:
   actual=[json.loads(t) for t in (root/'stage423/actual_C0/trace-private.jsonl' if arm=='C0' else root/'stage427/actual_P/trace-private.jsonl').read_text().splitlines()][118:];signatures=[];stats=[]
   if arm=='C0' and nominal.tolist()!=actual[0]['nominal']:raise TechnicalStop('actual423_current_nominal_not_exact')
   for rep in range(2):
    tag='qualification_replay_required' if rep==0 else 'qualification_replay_repeat';child=Child(meter,state,memory,ledger,fixed,pace,'qualification_'+arm+'_'+str(rep+1),world_tag=tag);checks=[];phase=True;delta=[]
    try:
     for index,row in enumerate(actual):
      if child.status!='ACTIVE':raise TechnicalStop('qualification_model_ended_before_actual')
      before=copy.deepcopy(child.ctrl.memory());computed=child.ctrl.act(child.m);delta.append(float(max(abs(computed-np.asarray(row['nominal'])))));child.one(tag+('_first13' if index<13 else '_continuation'),first_override=row['command'],prepared_nominal=computed,prepared_before=before);frame=child.rows[-1];z=shapecheck(frame,row);phase=phase and frame['memory_before']['C']['phase']==row['memory_before']['C']['phase'] and frame['memory_after']['C']['phase']==row['nominal_memory_after']['C']['phase'];checks.append(z)
      if not z['passed'] or z['wheel']['clipped_flag_mismatches']!=0 or not phase:raise TechnicalStop('actual423_replay_bodywheelrawhull_phase_clip:'+arm+':'+str(index+1))
      unchanged()
     if child.status!='FINISHED':raise TechnicalStop('actual423_replay_official_finish_mismatch')
     if arm=='C0' and rep==0:first_C0=copy.deepcopy(child.rows[0])
     signatures.append(child.signature());stats.append(dict(first13=maxima(checks[:13]),continuation=maxima(checks[13:]),rows=len(checks),phase_exact=phase,max_recomputed_nominal_difference=max(delta),official_finish_ticks=asdict(child.finish_ticks),command_source='STORED_ACTUAL423_C0_427P_CALIBRATION_ONLY; notusedinpilotselection',actual_root_ledger_unchanged=True))
    finally:
     try:child.dump(d)
     finally:child.close()
   if signatures[0]!=signatures[1]:raise TechnicalStop('actual423_full_replay_independent_repeat:'+arm)
   records[arm]=dict(independent_repeat_exact=True,replays=stats)
  # Freshly restore the twelve actually observed427 P query states. These are
  # calibration targets; subsequent scope64 parents start from the root.
  restores=[]
  actual=[json.loads(t) for t in (root/'stage427/actual_P/trace-private.jsonl').read_text().splitlines()]
  for n in range(12):
   payload=load_receipt(root/('stage427/actual_P/actual_P_'+str(119+n)+'-receipt-private.json'));ctx,ev=restore_typed(copy.deepcopy(payload));src,mem,rng=ctx.parent.fork_inputs();actual_state=src['terminal_model'];expected=actual[118+n];signatures=[]
   for rep in range(2):
    tag='qualification_restore_required' if rep==0 else 'qualification_restore_repeat';child=Child(meter,actual_state,mem,ctx.ledger,fixed,pace,'qualification_restore'+str(n+1)+'_'+str(rep+1),world_tag=tag)
    try:
     child.one(tag,first_override=expected['command']);z=shapecheck(child.rows[0],expected)
     if not z['passed'] or z['wheel']['clipped_flag_mismatches']!=0 or child.rows[0]['memory_after']['C']['phase']!=expected['nominal_memory_after']['C']['phase']:raise TechnicalStop('actual423_current_state_restore_first_transition')
     signatures.append(child.signature());unchanged()
    finally:
     try:child.dump(d)
     finally:child.close()
   if signatures[0]!=signatures[1]:raise TechnicalStop('actual423_current_restore_repeat')
   restores.append(dict(relative_actual_decision=n+1,passed=True,independent_repeat_exact=True,first_transition=z))
  held.one('qualification_parent_step',prepared_nominal=nominal,prepared_before=memory);check=compare_frames(held.rows[0],first_C0)
  if not check['passed'] or check['wheel']['clipped_flag_mismatches']!=0:raise TechnicalStop('qualification_held_parent_first_transition')
  if ledger.digest()!=ld or rnghash()!=rh:raise TechnicalStop('qualification_actual_root_ledger_RNG_mutation')
  held.dump(d);q=dict(passed=True,actual423_replays=records,current_actual_state_restores=restores,held_parent_first_transition=check,immutable_actual_root_ledger_unchanged=True,RNG_unchanged=True,scope='Qualificationonlyofsaved423C0and427Pactualstatesandcommands/first13/continuation. Noqualificationofnew428modelstatesorwiderclipping. Noactualfuturetraceusedbyselector.')
  save(d/'qualification.json',q);return q
 finally:held.close()
