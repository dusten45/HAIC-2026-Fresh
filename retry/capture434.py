"""Prospective immutable capture barrier and official-tracker observation tap.

This module does not create a world, call step, or change tracker mathematics.
No existing model runner is wired to it in434.
"""
from contextlib import AbstractContextManager
from dataclasses import asdict
from pathlib import Path
from core.finish_line import FinishLineTracker
from retry.boundary434 import *
from retry.receipt421_io import save_receipt,load_receipt,receipt_digest

class CaptureBarrier:
 def __init__(self,directory):self.directory=Path(directory);self.pending={};self.started=set()
 def seal(self,boundary,ctx,authority):
  require(Path(boundary.child_id).name==boundary.child_id,'child_file_identity');boundary.validate(ctx,authority,pending_only=False);key=boundary.key();require(boundary.child_id not in self.pending,'child_boundary_already_sealed')
  path=self.directory/(boundary.child_id+'-initial-boundary-private.json');digest=save_receipt(path,boundary.payload());require(receipt_digest(load_receipt(path))==digest,'boundary_readback')
  if decode(boundary.snapshot_bytes)['finish_tracker']['candidate_crossing_time_s'] is not None:boundary.validate(ctx,authority)
  self.pending[boundary.child_id]=(key,str(path),digest);return key
 def begin_continuation(self,child_id,key):
  require(child_id in self.pending and self.pending[child_id][0]==key and child_id not in self.started,'continuation_before_seal_or_wrong_child')
  sealed=load_receipt(self.pending[child_id][1]);snapshot=decode(sealed['snapshot_bytes']);require(not(sealed['vector']['remaining_path_m']<0 and snapshot['finish_tracker']['candidate_crossing_time_s'] is None),'negative_geometry_without_registered_pending')
  self.started.add(child_id);return key
 def complete(self,boundary,tail,ctx,authority):
  require(boundary.child_id in self.started and tail.boundary_key==boundary.key(),'continuation_not_started_with_seal')
  key,path,digest=self.pending[boundary.child_id];require(key==boundary.key(),'boundary_replaced')
  # Preserve the final attempt separately even if its qualification fails.
  save_receipt(self.directory/(boundary.child_id+'-continuation-final-private.json'),asdict(tail))
  result=Completion434(boundary,tail,authority,path,digest);result.authenticate(ctx);return result

class PostTrackerTap(AbstractContextManager):
 """Observe once AFTER original tracker.update; instance __dict__ stays intact.

Future model adapter must supply post-world safety/projection and exact action,
RNG and ledger capture separately. This tap alone is not physical qualification.
"""
 _active=False
 def __init__(self,tracker,callback):self.tracker=tracker;self.callback=callback;self.original=None
 def __enter__(self):
  require(self.original is None and not PostTrackerTap._active,'tap_already_active');PostTrackerTap._active=True;self.original=FinishLineTracker.update;original=self.original;target=self.tracker;callback=self.callback
  def observed(tracker,position,velocity,progress,physics_time_s):
   result=original(tracker,position,velocity,progress,physics_time_s)
   if tracker is target:callback(dict(position=list(position),velocity=list(velocity),progress=progress,time=physics_time_s,tracker_after=asdict(tracker)))
   return result
  self.wrapper=observed;FinishLineTracker.update=observed;return self
 def __exit__(self,*args):
  matched=FinishLineTracker.update is self.wrapper;FinishLineTracker.update=self.original;self.original=None;PostTrackerTap._active=False;require(matched,'tap_connection_changed')


def seal_live_child(barrier,child,ctx,authority,posts,actions,rng,proofs,snapshot_function):
 """Prospective connection point; read the paused child, never call act/step/DONE.

 Call immediately after initial13 (both repeats paused and qualified) and before
 any continuation. snapshot_function is the unchanged Terminal.snapshot reader.
 The callback/post-tick and action record wiring still needs a model gate.
 """
 require(child.initial_count==H and child.tail_count==0 and child.status=='ACTIVE','not_paused_at_initial13')
 state=snapshot_function(child.m);memory=child.ctrl.memory()
 boundary=capture_h13(ctx,authority,child_id=child.label,recipe=child.recipe,snapshot=state,memory=memory,rng=rng,ledger=child.ledger,posts=posts,actions=actions,vector=child.end13,proofs=proofs)
 key=barrier.seal(boundary,ctx,authority);return boundary,key
