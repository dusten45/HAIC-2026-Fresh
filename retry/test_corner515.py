import math,unittest
from dataclasses import replace
import numpy as np
from retry.test_brake509 import Car
from retry.brake509_adapter import context
from retry.corner515_control import project,point_at,reference,future_floor,nominal,command

class Tests515(unittest.TestCase):
    def test_projection_and_profile(self):
        path=dict(points=[(0.,0.),(0.,100.),(10.,120.)],arcs=[0.,100.,100.+math.sqrt(500)],speeds=[80.,30.,40.])
        q=project((1.,50.),path);self.assertEqual(q['s'],50.);self.assertEqual(q['distance'],1.)
        self.assertEqual(point_at(50.,path),(0.,50.));self.assertEqual(reference(100.,path)[0],30.)
        self.assertEqual(future_floor(90.,path),30.)
    def test_release_changes_only_brake_when_undershoot_is_predicted(self):
        car=Car()
        for body in [car.hull,*car.wheels]:body.linearVelocity=(0.,30.1)
        for w in car.wheels:w.omega=30.1/.54
        root=context(car,[car.road],[0,0,0]);root=replace(root,center=(0.,96.))
        path=dict(points=[(0.,0.),(0.,100.),(10.,120.)],arcs=[0.,100.,100.+math.sqrt(500)],speeds=[80.,30.,40.])
        a,_=command(root,path,'reference',[0]);counter=[0];b,details=command(root,path,'release',counter)
        self.assertTrue(details['brake_changed']);self.assertTrue(np.array_equal(a[:2],b[:2]));self.assertLess(b[2],a[2]);self.assertGreater(counter[0],0)

if __name__=='__main__':unittest.main()
