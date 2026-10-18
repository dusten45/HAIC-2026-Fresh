import math,unittest
import numpy as np
from retry.brake511_control import caps,request,boundary,command,Reference
from retry.test_brake509 import Car


class GoalTests(unittest.TestCase):
    def test_whole_budget_and_braking_allocation(self):
        c=caps();self.assertEqual(c['actions'],80);self.assertEqual(c['prefix_actions'],48);self.assertEqual(c['braking_actions_reserved'],32)
        self.assertEqual(c['total_raw_ticks'],422);self.assertEqual(c['resets'],2)
        self.assertEqual(math.ceil(2./.8),3);self.assertGreaterEqual(40-24,math.ceil(2./.8))
        self.assertEqual(25963-80,25883)
    def test_shared_goal_and_same_requested_end_speed(self):
        car=Car();n=np.array([.001,0.,0.],np.float32)
        a,ra,ia=command(n,car,[car.road],58.,'steady',.02)
        b,rb,ib=command(n,car,[car.road],58.,'response',.02)
        self.assertEqual(ia,ib)
        # The assembly COM norm is itself binary64. The real-valued 60-0.8
        # reference may differ by one ULP after that norm and subtraction.
        # This tolerance belongs only to this pure arithmetic assertion;
        # the physical goal band and prediction/safety gates stay unchanged.
        self.assertLessEqual(abs(ia['requested_end_speed']-59.2),math.ulp(59.2))
        self.assertEqual(ia['requested_end_speed'],max(58.,math.hypot(*ra.planar.linear.velocity)-.08*10.))
        self.assertTrue(np.array_equal(a[:2],b[:2]));self.assertEqual(a.dtype,np.float32)
        self.assertEqual(request(58.3,58.)[0],58.)
    def test_goal_boundary_and_frozen_braking_steer(self):
        self.assertEqual(boundary(58.1,58.),'GOAL_BAND');self.assertEqual(boundary(57.9,58.),'GOAL_BAND')
        self.assertEqual(boundary(57.89,58.),'EXCESS_BRAKING');self.assertEqual(boundary(58.11,58.),'RUN')
        ref=Reference();image=np.zeros((4,84,84),np.float32);ref.reset(image)
        for _ in range(24):last=ref.act(image)
        for _ in range(3):
            x=ref.act(image);self.assertEqual(x[0],last[0]);self.assertEqual(x[1],0.)
        self.assertEqual(ref.calls,27)


if __name__=='__main__':unittest.main()
