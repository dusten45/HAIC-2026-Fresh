import unittest,math,json
from pathlib import Path
from retry.speed516_control import path_for
from retry.corner515_control import nominal
from retry.plan513_model import load_root

class Tests516(unittest.TestCase):
    def test_only_speed_budget_changes(self):
        static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text())
        a,b=path_for(static,80.),path_for(static,100.)
        self.assertEqual({k:v for k,v in a.items() if k!='speeds'},{k:v for k,v in b.items() if k!='speeds'})
        self.assertTrue(all(x<=y for x,y in zip(a['speeds'],b['speeds'])))
        self.assertTrue(any(x<y for x,y in zip(a['speeds'],b['speeds'])))
        for path in (a,b):
            for i,(v,w) in enumerate(zip(path['speeds'],path['speeds'][1:])):
                ds=path['arcs'][i+1]-path['arcs'][i]
                self.assertLessEqual(w*w-v*v,2*25*ds+1e-10)
                self.assertLessEqual(v*v-w*w,2*45*ds+1e-10)
        root=load_root(static['root']);x,_=nominal(root,a);y,_=nominal(root,b);self.assertEqual(x[0],y[0])

if __name__=='__main__':unittest.main()
