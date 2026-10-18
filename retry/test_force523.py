import unittest,json
from pathlib import Path
from retry.force523_control import paths_from_history
from retry.drive519_control import drive

class Tests523(unittest.TestCase):
    def test_geometry_controls_and_closed_force_profile(self):
        s=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());trace=json.loads(Path('/workspace/haic-response522-private/cold-capacity-model-private.json').read_text())['trace'];c=json.loads(Path('retry/force523_calibration.json').read_text());paths,info=paths_from_history(s,trace,c);a,b=paths['capacity'],paths['shield'];excluded=('periodic_squared','launch_squared','periodic_pass_rounds')
        self.assertEqual({k:v for k,v in a.items() if k not in excluded},{k:v for k,v in b.items() if k not in excluded});self.assertTrue(all(x<=y+1e-9 for x,y in zip(b['launch_squared'],a['launch_squared'])));self.assertGreater(info['local_cap_affected_nodes'],0)
        q=b['periodic_squared'];n=len(q)
        for i,d in enumerate(b['ds']):
            self.assertLessEqual(q[(i+1)%n]-q[i],2*drive(q[i])*d+1e-8);self.assertLessEqual(q[i]-q[(i+1)%n],90*d+1e-8)
        self.assertEqual(b['launch_squared'][0],0.);self.assertGreater(b['launch_squared'][-1],0.)

if __name__=='__main__':unittest.main()
