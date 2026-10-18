import unittest,math
from dataclasses import replace
import numpy as np
from retry.test_brake509 import Car
from retry.brake509_adapter import context
from retry.plan514_control import perturb,guarded_arrival,POSITION_ALLOWANCE,SPEED_ALLOWANCE,PLANNING_NODE,PHYSICAL_LOW,PHYSICAL_HIGH
from retry.brake508_corridor import bounds
from retry.plan512_control import BRAKE

class Tests514(unittest.TestCase):
    def test_physical_node_and_residual_transform(self):
        car=Car();root=context(car,[car.road],[0,0,0]);p=dict(start=(0.,0.),axis=(0.,1.),gate=100.)
        self.assertLess(PHYSICAL_LOW,PLANNING_NODE);self.assertLess(PLANNING_NODE,PHYSICAL_HIGH)
        q=perturb(root,p,1)
        self.assertAlmostEqual(q.center[1]-root.center[1],POSITION_ALLOWANCE,places=12)
        self.assertAlmostEqual(q.planar.linear.velocity[1]-root.planar.linear.velocity[1],SPEED_ALLOWANCE,places=12)
        self.assertAlmostEqual(q.planar.linear.wheels[0].omega-root.planar.linear.wheels[0].omega,SPEED_ALLOWANCE/.54,places=12)
        self.assertEqual(perturb(root,p,0),root)
        z=perturb(q,p,-1);np.testing.assert_allclose(z.planar.linear.velocity,root.planar.linear.velocity,rtol=0,atol=1e-12)
    def test_guard_injects_future_hold_uncertainty(self):
        car=Car();root=context(car,[car.road],[0,0,0]);p=dict(start=(0.,0.),axis=(0.,1.),gate=50.)
        count=[0];result=guarded_arrival(root,np.array([0,0,BRAKE],np.float32),p,bounds(root.roads),count)
        self.assertIsNone(result);self.assertGreater(count[0],4);self.assertLessEqual(count[0],104)

if __name__=='__main__':unittest.main()
