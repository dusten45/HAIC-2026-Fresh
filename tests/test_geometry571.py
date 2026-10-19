import unittest
import numpy as np
from retry.geometry571 import road_support,obstacle_support
from retry.geometry571_design import constraints

class Primitive571Tests(unittest.TestCase):
    def test_road_support_keeps_both_tied_corners(self):
        poly=[(.501,-.5),(1.061,-.5),(1.061,.5),(.501,.5)];n,h,d=road_support(poly,(0.,-2.),(0.,2.));slacks=np.asarray(poly)@n-h-.5
        self.assertAlmostEqual(d,.501);self.assertEqual(sum(abs(slacks-.001)<1e-12),2);self.assertTrue(np.all(slacks>=0))
    def test_finite_endpoint_support_is_sufficient(self):
        poly=[(2.,1.),(3.,1.),(3.,2.),(2.,2.)];n,h,d=road_support(poly,(0.,0.),(1.,0.));self.assertAlmostEqual(d,2**.5);self.assertAlmostEqual(float(min(np.asarray(poly)@n)-h),d)
    def test_circle_support_preserves_radius(self):
        poly=[(1.,-.2),(2.,-.2),(2.,.2),(1.,.2)];n,h,d=obstacle_support(poly,(0.,0.),.5);self.assertAlmostEqual(d,.5);self.assertAlmostEqual(float(min(np.asarray(poly)@n)-h),.5)
    def test_observed_error_rule_includes_seed_without_buffer_grid(self):
        V=np.array([[[.6,0.]]]);JV=np.zeros((1,1,2,68));x=np.zeros(68);changed=x.copy();changed[0]=.05*.003;obs=[dict(x=changed,V=np.array([[[.59,0.]]]))];f=[dict(raw=0,normal=[1.,0.],offset=0.,polygon=0,kind='road',feature=1)]
        q,J,L,keys=constraints(V,JV,x,f,[[0]],obs);self.assertGreaterEqual(q[0],0);self.assertAlmostEqual(float(L[0]*.05),.02,places=10);self.assertEqual(float(L[0]*0),0.)

if __name__=='__main__':unittest.main()
