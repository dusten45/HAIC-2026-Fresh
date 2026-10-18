import json,math,unittest
from pathlib import Path
from retry.capacity522_control import path_for,lateral_budget
from retry.drive519_control import drive

class Tests522(unittest.TestCase):
    def test_only_corner_budget_and_closed_constraints(self):
        static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());a,b=path_for(static,'baseline'),path_for(static,'capacity');excluded=('periodic_squared','launch_squared','periodic_pass_rounds')
        self.assertEqual({k:v for k,v in a.items() if k not in excluded},{k:v for k,v in b.items() if k not in excluded})
        self.assertAlmostEqual(lateral_budget(static),153.38431605269326)
        self.assertTrue(all(x<=y+1e-9 for x,y in zip(a['launch_squared'],b['launch_squared'])))
        q=b['periodic_squared'];n=len(q)
        for i,d in enumerate(b['ds']):
            self.assertLessEqual(q[(i+1)%n]-q[i],2*drive(q[i])*d+1e-8);self.assertLessEqual(q[i]-q[(i+1)%n],90*d+1e-8)
            self.assertLessEqual(q[i],min(80.**2,lateral_budget(static)/max(abs(b['curvature'][i]),1e-8))+1e-8)
        self.assertEqual(b['launch_squared'][0],0.);self.assertGreater(b['launch_squared'][-1],0.)

if __name__=='__main__':unittest.main()
