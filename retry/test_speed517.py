import json,unittest
from pathlib import Path
from retry.speed517_control import path_for,markers
from retry.speed516_control import path_for as old_path

class Tests517(unittest.TestCase):
    def test_append_and_single_budget_change(self):
        x=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());a,b=path_for(x,80.),path_for(x,100.)
        self.assertEqual({k:v for k,v in a.items() if k!='speeds'},{k:v for k,v in b.items() if k!='speeds'})
        self.assertEqual(a['points'][:100],old_path(x,80.)['points']);self.assertGreater(a['measurement_end'],a['next_corner_end']);self.assertGreater(a['next_approach'],a['prior_window_end']);self.assertEqual(len(markers(a)),7)
        self.assertTrue(all(u<=v for u,v in zip(a['speeds'],b['speeds'])))

if __name__=='__main__':unittest.main()
