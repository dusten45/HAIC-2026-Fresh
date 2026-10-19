import math,unittest
import numpy as np
from retry.path569_design import capsule

class Capsule569Tests(unittest.TestCase):
    def test_signed_strip_equivalence_only_interior(self):
        p=np.array([[.5,-2.],[.5,0.],[.5,2.]])
        distance,_,u,_=capsule(p,[0.,0.],[1.,0.]);np.testing.assert_allclose(distance,abs(p[:,1]));self.assertTrue(np.all((u>=0)&(u<=1)))
    def test_endpoint_requires_longitudinal_residual(self):
        distance,_,u,_=capsule([4.1,0.],[0.,0.],[1.,0.]);self.assertAlmostEqual(float(distance),3.1);self.assertGreater(float(u),1.)
    def test_curve_union_is_not_one_frozen_strip(self):
        p=np.array([1.,1.5]);first=capsule(p,[0.,0.],[1.,0.])[0];second=capsule(p,[1.,0.],[1.,1.])[0];self.assertAlmostEqual(float(second),.5);self.assertGreater(float(first),1.);self.assertLess(float(min(first,second)),1.)
    def test_support_cut_is_valid_for_finite_segment(self):
        a=np.array([0.,0.]);b=np.array([1.,0.]);p=np.array([2.,1.]);dist,r,_,_=capsule(p,a,b);n=r/dist;support=max(n@a,n@b);self.assertAlmostEqual(float(n@p-support),float(dist))
        for x in [-2.,0.,.5,1.,3.]:
            for y in [-2.,0.,2.]:self.assertLessEqual(float(n@np.array([x,y])-support),float(capsule([x,y],a,b)[0])+1e-12)
    def test_position_residual_controls_distance_error(self):
        a=np.array([0.,0.]);b=np.array([1.,1.])
        for p,q in [(np.array([0.,1.]),np.array([.1,.8])),(np.array([2.,2.]),np.array([-.1,-.2]))]:
            self.assertLessEqual(abs(float(capsule(p,a,b)[0]-capsule(q,a,b)[0])),float(np.linalg.norm(p-q))+1e-12)

if __name__=='__main__':unittest.main()
