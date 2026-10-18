import json,math,unittest
from pathlib import Path
from retry.drive519_control import path_for,drive
from retry.envelope500 import REAR

class Tests519(unittest.TestCase):
    def test_single_forward_rule_and_closed_constraints(self):
        x=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());a,b=path_for(x,'baseline'),path_for(x,'source_drive')
        excluded=('periodic_squared','launch_squared','periodic_pass_rounds')
        self.assertEqual({k:v for k,v in a.items() if k not in excluded},{k:v for k,v in b.items() if k not in excluded})
        self.assertTrue(all(v<=w+1e-10 for v,w in zip(a['launch_squared'],b['launch_squared'])))
        self.assertEqual(drive(0.),REAR);self.assertLess(drive(80.**2),REAR)
        for i,d in enumerate(b['ds']):
            q=b['periodic_squared'];self.assertLessEqual(q[(i+1)%len(q)]-q[i],2*drive(q[i])*d+1e-8);self.assertLessEqual(q[i]-q[(i+1)%len(q)],2*45*d+1e-8)
        self.assertEqual(b['launch_squared'][0],0.);self.assertGreater(b['launch_squared'][-1],0.)

if __name__=='__main__':unittest.main()
