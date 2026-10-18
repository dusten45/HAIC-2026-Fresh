import unittest
from retry.path521_control import rebuild,obstacle_clearances,scalar_clock

class Tests521(unittest.TestCase):
    def test_closed_profile_geometry_and_finish(self):
        p=rebuild([(0.,0.),(50.,0.),(50.,50.),(0.,50.)],[])
        self.assertEqual(p['length'],200.);self.assertEqual(p['launch_squared'][0],0.)
        self.assertGreater(p['launch_squared'][-1],0.);self.assertGreater(scalar_clock(p),0.)
        for i,d in enumerate(p['ds']):
            j=(i+1)%4;self.assertLessEqual(p['periodic_squared'][i],p['periodic_squared'][j]+90*d+1e-10)
        self.assertAlmostEqual(obstacle_clearances(p['points'],[((25.,5.),1.)])[0],4.)
    def test_bad_segment_rejected(self):
        with self.assertRaises(ValueError):rebuild([(0.,0.),(0.,0.),(1.,1.)],[])

if __name__=='__main__':unittest.main()
