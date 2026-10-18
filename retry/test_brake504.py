import math
import unittest
from dataclasses import replace
from retry.brake502_response import State,Wheel,forecast as old_forecast
from retry.brake504_planar import Planar,forecast


class PlanarTests(unittest.TestCase):
    def state(self):
        lin=State((0.,80.),tuple(Wheel(80/.54) for _ in range(4)),7.30192)
        return Planar(lin,((-1.1,1.6),(1.1,1.6),(-1.1,-1.64),(1.1,-1.64)),10.,0.,0.,0.,(0.,)*4,(0.,)*4,(.01,)*4,0.)
    def test_straight_symmetric_reduces_to_frozen(self):
        state=self.state();result=forecast(state,.2)
        expected=old_forecast(state.linear,.2)[0]
        self.assertEqual(result.linear.velocity,expected.velocity)
        self.assertEqual([w.omega for w in result.linear.wheels],[w.omega for w in expected.wheels])
        self.assertEqual(result.yaw,0.)
    def test_free_steering_conserves_global_angular_momentum(self):
        state=self.state();lin=replace(state.linear,wheels=tuple(replace(w,friction=0.) for w in state.linear.wheels))
        result=forecast(replace(state,linear=lin,steer=.3),0.)
        self.assertEqual(result.linear.velocity,lin.velocity)
        self.assertAlmostEqual(result.inertia*result.yaw+sum(i*r for i,r in zip(result.wheel_inertias,result.rates)),0.,places=14)
        self.assertNotEqual(result.yaw,0.)


if __name__=='__main__':unittest.main()
