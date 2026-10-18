import unittest
from retry.brake502_response import State,Wheel
from retry.brake504_planar import Planar,choose as nominal
from retry.brake505_uncertainty import histories,choose


def fixture():
    linear=State((0.,80.),tuple(Wheel(80/.54) for _ in range(4)),7.30192)
    return Planar(linear,((-1.1,1.6),(1.1,1.6),(-1.1,-1.64),(1.1,-1.64)),10.,0.,0.,0.,(0.,)*4,(0.,)*4,(.01,)*4,0.)


class ContactTests(unittest.TestCase):
    def test_family_includes_unknown_time_and_every_subset(self):
        h=histories(fixture(),(240.,)*4)
        self.assertEqual(len(h),46)
        self.assertIn((None,()),h)
        self.assertIn((2,(0,2)),h)
        self.assertIn((1,(0,1,2,3)),h)
        self.assertTrue(all(event is None or event>0 for event,_ in h))
    def test_collapsed_uncertainty_matches_nominal_exact_command(self):
        s=fixture();b,info=choose(s,78.4,(400.,)*4)
        self.assertEqual(info['scenarios'],1)
        self.assertEqual(b,nominal(s,78.4)[0])
    def test_robust_bound_contains_nominal_and_respects_target(self):
        s=fixture();b,info=choose(s,78.4,(240.,)*4)
        self.assertGreaterEqual(b,nominal(s,78.4)[0])
        self.assertLessEqual(info['max_end_speed'],78.4)
        self.assertLessEqual(info['min_end_speed'],info['max_end_speed'])


if __name__=='__main__':unittest.main()
