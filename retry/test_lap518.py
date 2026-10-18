import json,math,unittest
from pathlib import Path
from retry.lap518_control import path_for,project,point_at,reference
from core.finish_line import FinishLineTracker

class Tests518(unittest.TestCase):
    def test_closed_profiles_and_obstacle_uniqueness(self):
        static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());a,b=path_for(static,80.),path_for(static,100.)
        self.assertEqual({k:v for k,v in a.items() if k not in ('periodic_squared','launch_squared','periodic_pass_rounds')},{k:v for k,v in b.items() if k not in ('periodic_squared','launch_squared','periodic_pass_rounds')})
        self.assertEqual(a['obstacle_association_count'],len(static['obstacles']))
        self.assertNotEqual(a['points'][0],a['points'][-1]);self.assertEqual(len(a['arcs']),len(a['points'])+1)
        for path in (a,b):
            for i,d in enumerate(path['ds']):
                q=path['periodic_squared'];self.assertLessEqual(q[i]-q[(i+1)%len(q)],2*45*d+1e-8);self.assertLessEqual(q[(i+1)%len(q)]-q[i],2*25*d+1e-8)
            self.assertEqual(path['launch_squared'][0],0.);self.assertGreater(path['launch_squared'][-1],0.)
            for i,d in enumerate(path['ds']):
                q=path['launch_squared'];self.assertLessEqual(q[i]-q[i+1],2*45*d+1e-8);self.assertLessEqual(q[i+1]-q[i],2*25*d+1e-8)
            self.assertAlmostEqual(reference(path['length'],path)[0],reference(path['length']+1e-8,path)[0],places=5)
            self.assertLess(math.dist(point_at(-.1,path),point_at(path['length']-.1,path)),1e-10)
    def test_lap_unwrap_and_source_confirmation(self):
        p=dict(points=[(0.,0.),(0.,10.),(10.,10.),(10.,0.)],arcs=[0.,10.,20.,30.,40.],length=40.)
        self.assertEqual(project((1.,0.),p)['s'],-1.);self.assertEqual(project((0.,1.),p,39.)['s'],41.)
        self.assertEqual(project((0.,1.),p,-1.)['s'],1.)
        t=FinishLineTracker((0.,0.),(0.,1.),6.67,.875)
        t.update((0.,0.),(0.,1.),0.,0.);t.update((0.,2.),(0.,1.),.1,.02);t.update((0.,-2.),(0.,1.),.94,.04)
        t.update((0.,-.5),(0.,1.),.95,.06);t.update((0.,.1),(0.,1.),.95,.08);self.assertIsNone(t.finish_time_s)
        self.assertTrue(t.update((0.,1.),(0.,1.),.95,.10));self.assertEqual(t.finish_time_s,.08)

if __name__=='__main__':unittest.main()
