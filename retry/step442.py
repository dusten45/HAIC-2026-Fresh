"""The same suffix-dispatch function is used by fixtures and the actual runner."""
import numpy as np
from retry.receipt421_io import save_receipt
from retry.ledger439 import require
from retry.parent436 import encoded

def _suffix_checked(native,history,frame,trace,pending=None):
 # No forecast is supplied to dispatch or to native fact construction/commit.
 native.dispatch(np.asarray(frame['command'],np.float32),trace);fact=native.commit_native_observation();row=native.rows[-1];history.append_native_fact(row,native.last_bundle)
 if pending is not None:
  require(pending.actual_token==history.token and pending.dispatch_count+1==native.dispatcher.calls,'PENDING_NEXT_OWN_NATIVE_STEP');require(pending.actual_ledger_bytes==encoded(native.last_bundle['ledger_before']),'PENDING_ACTUAL_LEDGER_BEFORE');save_receipt(native.directory/(native.label()+'-pending-native-confirmation-private.json'),dict(model_guardian_cannot_commit=True,actual_fact_committed=True,official_native_finish=row['completed'],native_event_time_s=row['finish_time_s'],native_confirmation_time_s=row['post']['time'] if row['completed'] else None,raw_ticks=row['raw_ticks'],actual_ledger_done=native.ledger.done))
 report=native.verify_forecast(frame);history.mark_verified();return row,fact,report

def suffix_step(native,history,frame,trace,pending=None):
 try:return _suffix_checked(native,history,frame,trace,pending)
 except BaseException as e:
  native.halted=True;native.failure=type(e).__name__+': '+str(e);save_receipt(native.directory/(native.label()+'-step-stop-private.json'),dict(error=native.failure,actual_ledger_retained=dict(native.ledger.__dict__),native_facts=len(native.rows),dispatch_calls=native.dispatcher.calls,awaiting_verification=native.awaiting_verification,next_dispatch_forbidden=True));raise
