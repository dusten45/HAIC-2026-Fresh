"""Geometry fixtures only: no solver, dynamic FD, profile or force evaluation."""
import math,unittest
from collections import Counter
import numpy as np
from retry import corridor589_math as m
TEST_OBJECTIVES=0
TESTCOUNTS=Counter()

def fixture():
    a=np.arange(32)*2*math.pi/32;p=np.c_[50*np.cos(a),50*np.sin(a)];return m.polyline(p)
def objective(p,b,seed):
    global TEST_OBJECTIVES
    TEST_OBJECTIVES+=1;return m.objective(m.components(p,b),seed)
class PureTests(unittest.TestCase):
    def test_exact_seed_and_endpoint_guard(self):
        path=fixture();b=m.basis(path);p=m.points(np.zeros(len(b['free'])),b);self.assertTrue(np.array_equal(p,b['seed']));x=np.ones(len(b['free']))*.3;changed=m.points(x,b)
        self.assertTrue(np.array_equal(changed[np.setdiff1d(np.arange(len(p)),b['free'])],p[np.setdiff1d(np.arange(len(p)),b['free'])]));self.assertTrue(all(q['position_error_m']==q['tangent_error_rad']==0 for q in m.endpoint_metrics(changed,path,b)));self.assertGreater(len(b['free']),0)
    def test_dimensionally_normalized_seed_objective(self):
        path=fixture();b=m.basis(path);seed=m.components(b['seed'],b);self.assertGreater(seed['burden_m'],0);self.assertAlmostEqual(seed['length_m'],130.,places=10);self.assertEqual(objective(b['seed'],b,seed),1.)
        q=m.components(m.points(np.ones(len(b['free']))*.1,b),b);self.assertGreater(q['bending_m'],0);self.assertGreaterEqual(q['transition_m'],0);TESTCOUNTS.update(test_geometric_component_evaluations=2)
    def test_local_order_and_true_arc_not_global_chord(self):
        path=fixture();b=m.basis(path);p=m.points(np.ones(len(b['free']))*.1,b);self.assertTrue(np.all(m.projection_order(p,b)>0));new=m.polyline(p);self.assertNotEqual(new['length'],path['length']);self.assertTrue(np.array_equal(b['sigma'],np.asarray(path['arcs'][:-1])));self.assertTrue(np.all(np.diff(new['arcs'])>0))
    def test_fixed_corridor_support_seed_and_jacobian(self):
        path=fixture();b=m.basis(path);p=b['seed'];_,normal=m.frames(p);n=len(p);sides=[p-5*normal,p+5*normal];boundary=[(v[i].tolist(),v[(i+1)%n].tolist()) for v in sides for i in range(n)];static=dict(track=[[0,0,*v] for v in p],boundary=boundary,obstacles=[([1000.,1000.],1.)])
        def polys(j):return [p[j]+np.asarray([[-.2,-.2],[.2,-.2],[.2,.2],[-.2,.2]])]*8
        A,c,k=m.guides(b,static,polys,lambda key,z:TESTCOUNTS.update({key:z}));self.assertGreater(c.min(),0);TESTCOUNTS.update(constraint_evaluations=4);x=np.arange(len(b['free']))*.01;np.testing.assert_allclose((A@(x+m.EPS)-A@x)/m.EPS,A@np.ones(len(x)),atol=1e-10)
    def test_dense_samples_include_both_segment_headings(self):
        p=np.asarray([[0.,0.],[1.1,0.],[1.1,1.],[0.,1.]]);self.assertEqual(m.sample_count(p,[0]),4);self.assertEqual(m.sample_count(p,[1]),3);self.assertGreater(m.sample_count(p,range(4)),len(p))
    def test_invalid_geometry_stops_without_solver(self):
        with self.assertRaises(ValueError):m.signed_curvature([[0,0],[0,0],[1,0]])
        with self.assertRaises(ValueError):m.objective(dict(length_m=1,burden_m=0),dict(length_m=1,burden_m=0))
