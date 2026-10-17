"""Targeted non-confirmation controls using valid tracker algebra, no physics."""
import copy,tempfile,unittest
from pathlib import Path
from dataclasses import asdict,replace
from core.finish_line import FinishLineTracker
from retry.test_boundary434 import fixture
from retry.boundary434 import *
from retry.capture434 import CaptureBarrier,PostTrackerTap

class More434(unittest.TestCase):
 def test_signed_negative_with_genuinely_no_crossing(self):
  # Same signed geometry/goal progress, but source tracker has not reached x=0.
  ctx,a,b,t=fixture(100)
  with self.assertRaisesRegex(ProtocolStop,'no_registered_pending_event'):b.validate(ctx,a)
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);store=CaptureBarrier(td.name);key=store.seal(b,ctx,a)
  self.assertTrue((Path(td.name)/(b.child_id+'-initial-boundary-private.json')).exists())
  with self.assertRaisesRegex(ProtocolStop,'negative_geometry_without_registered_pending'):store.begin_continuation(b.child_id,key)
 def test_genuine_candidate_cancellation_cannot_be_replaced_later(self):
  ctx,a,b,t=fixture();tracker=FinishLineTracker(**decode(b.snapshot_bytes)['finish_tracker']);posts=decode(t.posts_bytes);posts[0]['position']=[-2.,0.];tracker.update((-2.,0.),(2.,0.),.96,posts[0]['time']);posts[0]['tracker_after']=asdict(tracker)
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);store=CaptureBarrier(td.name);key=store.seal(b,ctx,a);store.begin_continuation(b.child_id,key)
  with self.assertRaisesRegex(ProtocolStop,'pending_cancelled_or_replaced'):store.complete(b,replace(t,posts_bytes=encoded(posts)),ctx,a)
  self.assertIsNone(b.finish_ticks)
 def test_future_official_finish_cannot_repair_failed_initial_goal(self):
  ctx,a,b,t=fixture();actions=decode(b.actions_bytes);ledger=ForecastLedger.fork(ctx.ledger)
  for row in actions:
   ledger=ledger.advance_prediction(ModelPrediction(0.,row['raw_end_clock'],False));row['model_progress_m']=0.;row['ledger_after']=asdict(ledger)
  bad=replace(b,actions_bytes=encoded(actions),ledger_bytes=encoded(asdict(ledger)),vector=replace(b.vector,remaining_path_m=a.geometry_total_length_m))
  with self.assertRaisesRegex(ProtocolStop,'initial_progress_not_retrospective'):bad.validate(ctx,a)
  self.assertIsNone(bad.finish_ticks)
 def test_tap_restores_source_after_callback_failure_and_rejects_nesting(self):
  tracker=FinishLineTracker((0.,0.),(1.,0.),4.,1.);original=FinishLineTracker.update
  def fail(row):raise RuntimeError('STATIC_CALLBACK_FAILURE')
  with self.assertRaisesRegex(RuntimeError,'STATIC_CALLBACK_FAILURE'):
   with PostTrackerTap(tracker,fail):tracker.update((-2.,0.),(2.,0.),.96,.02)
  self.assertIs(FinishLineTracker.update,original)
  with PostTrackerTap(tracker,lambda row:None):
   with self.assertRaises(ProtocolStop):
    with PostTrackerTap(tracker,lambda row:None):pass
  self.assertIs(FinishLineTracker.update,original)

 def test_nonpending_positive_H13_is_sealed_before_ordinary_continuation(self):
  ctx,a,b,t=fixture(100);b=replace(b,vector=replace(b.vector,remaining_path_m=4.));a=replace(a,geometry_total_length_m=30.);ctx=replace(ctx,remaining_path_m=30.);b=replace(b,context_bytes=encoded(__import__('retry.pilot420_json',fromlist=['json_ready']).json_ready(asdict(ctx))))
  b.validate(ctx,a,pending_only=False);td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);store=CaptureBarrier(td.name);key=store.seal(b,ctx,a);store.begin_continuation(b.child_id,key);self.assertTrue((Path(td.name)/(b.child_id+'-initial-boundary-private.json')).exists());self.assertIsNone(b.finish_ticks)
  with self.assertRaisesRegex(ProtocolStop,'no_registered_pending_event'):b.validate(ctx,a)
