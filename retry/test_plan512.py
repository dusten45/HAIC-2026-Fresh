import math,unittest
from dataclasses import replace
import numpy as np
from retry.brake509_adapter import context
from retry.test_brake509 import Car
from retry.brake508_corridor import bounds,forecast
from retry.brake502_response import wheel_response
from retry.plan512_control import tick,hold,pedal,axis_plan,station,BRAKE,TARGET,GOAL,scalar_action,response_action

class Pure512(unittest.TestCase):
    def test_zero_gas_is_existing_brake_predictor(self):
        car=Car();root=context(car,[car.road],[0.,0.,0.]);counter=[0]
        for b in (0.,.03,BRAKE):
            a,rows=hold(root,np.array([0,0,b]),bounds(root.roads),counter)
            z,_=forecast(root,b,bounds(root.roads))
            self.assertEqual(a,z)
        self.assertEqual(counter[0],12)
    def test_engine_is_source_order_with_rear_ramp(self):
        car=Car();root=context(car,[car.road],[0.,0.,0.]);counter=[0]
        after=tick(root,1.,0.,bounds(root.roads),counter)
        expected=[wheel_response(w,root.planar.linear.velocity,.1 if i>=2 else 0.,0.,root.planar.linear.engine_multiplier) for i,w in enumerate(root.planar.linear.wheels)]
        v=tuple(root.planar.linear.velocity[j]+.02*sum(x[1][j] for x in expected)/root.planar.linear.mass for j in range(2))
        np.testing.assert_allclose(after.planar.linear.velocity,v,rtol=0,atol=1e-12)
        self.assertEqual([w.gas for w in after.planar.linear.wheels],[0.,0.,.1,.1])
        for x,y in zip(after.planar.linear.wheels,expected):self.assertEqual(x.omega,y[0].omega)
    def test_both_plans_accept_unconstrained_straight(self):
        car=Car();root=context(car,[car.road],[0.,0.,0.]);counter=[0]
        plan=dict(start=(0.,-50.),axis=(0.,1.),gate=120.)
        a,detail=scalar_action(root,0.,plan)
        b,detail=response_action(root,0.,plan,counter)
        self.assertEqual(a[2],0.);self.assertEqual(b[2],0.)
        self.assertGreater(a[1],0.);self.assertEqual(b[1],1.)
        self.assertLess(counter[0],1000)
    def test_gate_plan_and_caps(self):
        p=[(0.,0.,0.,float(i)*3.5) for i in range(40)]+[(0.,0.,3.5,140.)]+[(0.,0.,7.,140.-i*3.5) for i in range(40)]
        plan=axis_plan(p,(0.,0.));self.assertEqual(plan['gate'],133.)
        self.assertEqual(station((0.,70.),plan),70.)
        self.assertEqual(TARGET,29.85);self.assertEqual(GOAL,30.)
        self.assertEqual(2*51+400*4,1702);self.assertEqual(25909-400,25509)
        for u in (-1.,0.,1.):
            a=pedal(u,.001);self.assertEqual(a.dtype,np.float32);self.assertFalse(a[1]>0 and a[2]>0)

if __name__=='__main__':unittest.main()
