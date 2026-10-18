import math,unittest
import numpy as np
from retry.test_brake509 import Car
from retry.brake509_adapter import context
from retry.gas520_control import request,action

class Tests520(unittest.TestCase):
    def test_shared_request_and_gas_only_change(self):
        car=Car();root=context(car,[car.road],[.001,.5,0]);nom=np.array([.001,.5,0],np.float32);count=[0]
        a,ia,da=action(root,nom,'steady',count);b,ib,db=action(root,nom,'response',count)
        self.assertEqual(ia,ib);self.assertEqual(ia['target'],math.hypot(*root.planar.linear.velocity)+.08*ia['steady_acceleration'])
        self.assertTrue(np.array_equal(a[[0,2]],b[[0,2]]));self.assertTrue(0<=b[1]<=1)
    def test_passthrough_brake_and_low_target(self):
        car=Car();root=context(car,[car.road],[0,0,.1]);n=np.array([.01,0.,.1],np.float32);a,intent,d=action(root,n,'response',[0]);self.assertTrue(np.array_equal(a,n));self.assertFalse(intent['active'])
        with self.assertRaises(ValueError):request(root,[0,.1,.1])

if __name__=='__main__':unittest.main()
