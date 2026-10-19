"""Pure policy-domain, clone and gate checks; no force/geometry/source/native."""
import unittest
from types import SimpleNamespace
from retry.carry592_model import action_at,clone,replay_allowed,d
class PureTests(unittest.TestCase):
 def test_absolute_index(self):
  self.assertEqual(action_at({1:[0,0,0],47:[.25,1,0]},47).tolist(),[.25,1.,0.])
 def test_no_extension_or_restart(self):
  for index in [1,46,167]:
   with self.assertRaises(ValueError):action_at({},index)
 def test_gate(self):
  self.assertTrue(replay_allowed(True,14.46));self.assertFalse(replay_allowed(False,13.));self.assertFalse(replay_allowed(True,None));self.assertFalse(replay_allowed(True,14.460001))
 def test_clone_preserves_clock_and_isolates_history(self):
  tracker=d.FinishLineTracker(center=(0,0),forward=(1,0),half_width=1,half_depth=.1,qualification_ratio=.95);s=dict(root=object(),visited={1},tracker=tracker,elapsed=4.699999999999988-1.02,global_raw=184,progress=3.,launch=[2,384],tracking=[0,352]);q=clone(s);q['visited'].add(2);q['tracking'][0]=4;q['tracker'].departed_start_area=True;self.assertEqual(s['tracking'],[0,352]);self.assertEqual(s['visited'],{1});self.assertEqual(q['elapsed'],s['elapsed']);self.assertFalse(s['tracker'].departed_start_area)
