"""Static tests of 432 scope and mandatory pre-integration persistence."""
import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from retry.pilot432_run import scope
from retry.pilot432_meter import Meter
from retry.pilot420_backend import TechnicalStop
from retry.planner419 import GoalLedger
from retry.receipt421_io import load_receipt
from retry.proposal429 import bounds

class Scope432(unittest.TestCase):
 def test_frozen_bound(self):
  b=bounds();self.assertEqual((b['total_tick_cap_required'],b['total_world_cap_required']),(519038,882));self.assertLessEqual(b['total_tick_cap_required'],524288);self.assertLessEqual(b['total_world_cap_required'],1024)
 def test_C0_all_guardian(self):
  self.assertEqual(scope('C0',0,'FIRST_LAP'),(80,False))
 def test_P_last_planner_then_guardian(self):
  self.assertEqual(scope('P',63,'FIRST_LAP'),(100,True));self.assertEqual(scope('P',64,'FIRST_LAP'),(100,False));self.assertEqual(scope('P',65,'FIRST_LAP'),(100,False))
 def test_confirmation_never_planner(self):
  self.assertEqual(scope('P',0,'FINISH_CONFIRM'),(100,False))
 def test_world_missing_before_proof_stops_before_constructor(self):
  m=Meter.__new__(Meter);m.inputs=None
  with patch('retry.pilot432_meter.PreviousMeter.world') as call:
   with self.assertRaises(TechnicalStop):m.world({},'test')
   call.assert_not_called()
 def test_step_unregistered_or_concurrent_stops(self):
  m=Meter.__new__(Meter);m.auth={};m.active_step=False
  with self.assertRaises(TechnicalStop):m.step(object(),[0,0,0],'test')
  m.active_step=True
  with self.assertRaises(TechnicalStop):m.step(object(),[0,0,0],'test')
 def test_inputs_durable_and_no_duplicate_overwrite(self):
  m=Meter.__new__(Meter)
  with tempfile.TemporaryDirectory() as td:
   m.d=Path(td);m.qualification_passed=False;state={'finite':[1,2,3]};memory={'x':1};ledger=GoalLedger.start(1.,2)
   proof=m.capture_inputs(state,memory,ledger,'static',gate='TEST_ONLY');saved=load_receipt(proof['path']);self.assertEqual(saved['state'],state);self.assertEqual(saved['memory'],memory);self.assertIn('global_RNG_pickle',saved);self.assertFalse(saved['actual_execution_allowed']);self.assertFalse(saved['qualification_passed'])
   with self.assertRaises(FileExistsError):m.capture_inputs(state,memory,ledger,'static',gate='TEST_ONLY')
 def test_nonfinite_context_stops_before_constructor(self):
  m=Meter.__new__(Meter)
  with tempfile.TemporaryDirectory() as td:
   m.d=Path(td);m.qualification_passed=False
   with self.assertRaises(ValueError):m.capture_inputs({'x':float('nan')},{},GoalLedger.start(1.,2),'bad')
   self.assertFalse(list(m.d.iterdir()))
