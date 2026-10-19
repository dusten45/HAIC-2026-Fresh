"""Pure payload, horizon, phase-boundary, history and official-clock tests."""
import unittest
import numpy as np
from retry.cold593_certificate import future_commands,phase_failure,finish_raw
class PureTests(unittest.TestCase):
 def test_nonconstant_future_payload(self):
  commands={h:np.asarray([h/256.,h/512.,0],np.float32) for h in range(1,167)};before={h:a.tobytes() for h,a in commands.items()};future=future_commands(commands,23);self.assertEqual([h for h,a in future],list(range(23,35)));self.assertTrue(all(a.tobytes()==before[h] for h,a in future));future[0][1][0]=0;self.assertEqual(commands[23].tobytes(),before[23])
 def test_no_extension(self):
  self.assertEqual([h for h,a in future_commands({166:np.zeros(3,np.float32)},166)],[166])
  for h in [0,167]:
   with self.assertRaises(ValueError):future_commands({},h)
 def test_launch_tracking_boundary(self):
  self.assertIsNone(phase_failure(24,3,2.4,[58,380],20));self.assertEqual(phase_failure(24,4,2.4,[58,384],20),'LAUNCH_CLIP');self.assertIsNone(phase_failure(24,4,2.4,[55,384],20));self.assertEqual(phase_failure(25,1,1.060,[0,4],0),'TRACK_FORCE');self.assertEqual(phase_failure(25,1,1.01,[1,4],0),'TRACK_CLIP');self.assertEqual(phase_failure(25,1,1.,[0,4],4.85001),'REFERENCE')
 def test_official_integer_gain(self):
  self.assertEqual(finish_raw(14.67999999999977,1.02),683);self.assertEqual(finish_raw(14.68+1e-12,1.02),683);self.assertLess(finish_raw(14.66,1.02),683)
