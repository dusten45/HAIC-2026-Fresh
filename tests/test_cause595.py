"""Pure equivalence of the original OR guard and split predicate telemetry."""
import itertools,math,unittest
from retry.split595_certificate import geometry_branches
class PureTests(unittest.TestCase):
 def test_equivalence_boundaries(self):
  minimum=[math.nextafter(.5,-math.inf),.5,math.nextafter(.5,math.inf),2.]
  distance=[math.nextafter(3.,-math.inf),3.,math.nextafter(3.,math.inf),4.]
  delta=[math.nextafter(-.5,-math.inf),-.5,0.,5.,math.nextafter(5.,math.inf),7.,math.nextafter(7.,math.inf)]
  for m,d,s,limit in itertools.product(minimum,distance,delta,[5.,7.]):
   original=m<.5 or d>3 or s<-.5 or s>limit;flags,first=geometry_branches(m,d,s,limit);self.assertEqual(original,bool(first));self.assertEqual(original,any(flags.values()))
 def test_original_shortcircuit_priority(self):
  self.assertEqual(geometry_branches(.49,4,-1,5)[1],'FOOTPRINT');self.assertEqual(geometry_branches(.5,4,-1,5)[1],'PATH');self.assertEqual(geometry_branches(.5,3,-1,5)[1],'PROJECTION_BACKWARD');self.assertEqual(geometry_branches(.5,3,6,5)[1],'PROJECTION_FORWARD')
 def test_equalities_are_safe(self):
  self.assertIsNone(geometry_branches(.5,3,-.5,5)[1]);self.assertIsNone(geometry_branches(.5,3,5,5)[1])
 def test_all_active_flags_retained(self):
  flags,first=geometry_branches(.49,4,6,5);self.assertEqual([k for k,v in flags.items() if v],['FOOTPRINT','PATH','PROJECTION_FORWARD'])
