import json,unittest
from dataclasses import asdict,replace
from retry.test_brake509 import Car
from retry.brake509_adapter import context
from retry.plan513_control import steering,steered
from retry.plan513_model import load_root,polygons

class Tests513(unittest.TestCase):
    def test_roundtrip_and_feedback_sign(self):
        car=Car();root=context(car,[car.road],[0,0,0]);root=load_root(json.loads(json.dumps(asdict(root))))
        plan=dict(start=(0.,0.),axis=(0.,1.),gate=100.)
        root=replace(root,center=(0.,50.),planar=replace(root.planar,angle=0.))
        self.assertEqual(steering(root,plan),0.)
        self.assertGreater(steering(replace(root,center=(-1.,50.)),plan),0.)
        self.assertLess(steering(replace(root,center=(1.,50.)),plan),0.)
        self.assertGreater(steering(replace(root,planar=replace(root.planar,angle=.1)),plan),0.)
        a=steering(root,plan);self.assertEqual(steered(root,[a,0,0]).planar.steer,-a)
        self.assertEqual(len(polygons(root)),8)

if __name__=='__main__':unittest.main()
