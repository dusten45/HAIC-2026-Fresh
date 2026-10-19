"""Pure numerical/geometry invariants; no integration or force kernels."""
import copy,json,math,unittest
from pathlib import Path
from collections import Counter
import numpy as np
from retry import smoother588_math as m
from retry.smoother588_design import static_pose
from retry.plan513_model import load_root,polygons
from retry.corner515_model import margin
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
TESTCOUNTS=Counter()
STATIC=Path('/workspace/haic-response515-private/collected-map-state-private.json')

class PureTests(unittest.TestCase):
    def test_hermite_endpoint_position_derivatives_and_signed_curvature(self):
        p0=np.array([0.,0.]);p1=np.array([1.,1.]);L=math.sqrt(2.);d0=np.array([L,0.]);d1=np.array([0.,L]);a0=np.array([0.,L*L]);a1=np.array([-L*L,0.]);c=m.coefficients(p0,p1,d0,d1,a0,a1)
        for u,p,d,a in [(0,p0,d0,a0),(1,p1,d1,a1)]:
            np.testing.assert_allclose(m.evaluate(c,u),p,rtol=0,atol=1e-13);np.testing.assert_allclose(m.evaluate(c,u,1),d,rtol=0,atol=1e-13);np.testing.assert_allclose(m.evaluate(c,u,2),a,rtol=0,atol=1e-13)
            self.assertAlmostEqual(float(np.cross(d,a)/np.linalg.norm(d)**3),1.)
    def test_left_endpoint_tie_and_squared_profile_branches(self):
        path=dict(points=[[0.,0.],[10.,0.],[10.,10.],[0.,10.]],ds=[10.]*4,arcs=[0.,10.,20.,30.,40.],length=40.,curvature=[0.,1.,2.,3.],periodic_squared=[100.,200.,300.,400.],launch_squared=[0.,10.,20.,30.,40.])
        p,t,k,i,f=m.endpoint(path,10);self.assertEqual(i,0);self.assertEqual(f,1.);np.testing.assert_equal(t,[1.,0.]);self.assertEqual(k,1.)
        self.assertEqual(m.interpolate_squared(path,40,True),40);self.assertEqual(m.interpolate_squared(path,40,False),100);self.assertEqual(m.interpolate_squared(path,5,True),5)
        self.assertEqual(m.project([10,0],path,10)['i'],0);self.assertEqual(m.project([0,0],path,39)['s'],40)
    def test_signed_curvature_and_nonadjacent_intersection(self):
        ds,k=m.signed_curvature([[0,0],[1,0],[1,1],[0,1]]);self.assertTrue(np.all(k>0));self.assertFalse(m.intersections([[0,0],[1,0],[1,1],[0,1]],lambda k,n:TESTCOUNTS.update({k:n}),lambda:None))
        hits=m.intersections([[0,0],[1,1],[0,1],[1,0]],lambda k,n:TESTCOUNTS.update({k:n}),lambda:None);self.assertIn([0,2],hits);self.assertTrue(m.segment_intersects([0,0],[2,0],[1,0],[3,0]))
    def test_true_arc_and_sigma_construction(self):
        points=[[x,0.] for x in range(0,301,25)]+[[300.,100.],[0.,100.]];ds,k=m.signed_curvature(points);path=dict(points=points,ds=ds.tolist(),arcs=np.r_[0,np.cumsum(ds)].tolist(),length=float(sum(ds)),curvature=k.tolist());z=m.construct(path)
        self.assertEqual(len(z['curve']),513);self.assertTrue(all(a<b for a,b in zip(z['oldstation'],z['oldstation'][1:])));np.testing.assert_allclose(np.array(z['curve'])[:,1],0,atol=1e-13);self.assertAlmostEqual(z['diagnostics']['new_replaced_arc_m'],130)
    def test_static_com_frame_full_vehicle_and_obstacle(self):
        template=load_root(json.loads(STATIC.read_text())['root']);r=static_pose(template,[0.,0.],[0.,1.]);r2=static_pose(template,[0.,0.],[1.,0.]);self.assertAlmostEqual(r.planar.angle,0);self.assertAlmostEqual(r2.planar.angle,-math.pi/2)
        p=np.array(polygons(r)[0]);q=np.array(polygons(r2)[0]);np.testing.assert_allclose(q,np.c_[p[:,1],-p[:,0]],atol=1e-12)
        roads=[([[-10.,-10.],[10.,-10.],[10.,10.],[-10.,10.]],1.)];boundary=list(zip(roads[0][0],roads[0][0][1:]+roads[0][0][:1]));idx=bounds(roads);edge=boundary_index(boundary)
        TESTCOUNTS.update(geometry_checks=2,test_fullbody_geometry_checks=2)
        self.assertGreater(margin(r,roads,idx,boundary,edge,[]),7.);self.assertLess(margin(r,roads,idx,boundary,edge,[([0.,0.],.5)]),0)
    def test_retime_and_backup_minimum_are_preplanned_not_measured(self):
        static=json.loads(STATIC.read_text());path=dict(points=[[0.,0.],[1.,0.]],ds=[1.,1.],arcs=[0.,1.,2.],length=2.,curvature=[0.,0.]);old=dict(path,periodic_squared=[6400.,6400.],launch_squared=[0.,50.,100.]);high,low,info=m.retime(path,old,[0.,1.],static,lambda k,n:TESTCOUNTS.update({k:n}),lambda:None)
        self.assertEqual(high['periodic_squared'],[8100.,8100.]);self.assertEqual(low['periodic_squared'],[6400.,6400.]);self.assertEqual(low['launch_squared'],[0.,50.,100.]);self.assertFalse(info['old_observed_curvature_used']);self.assertLessEqual(info['nominal_peak_wheel_force_ratio'],.9990000001)
