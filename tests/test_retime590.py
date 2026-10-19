"""No solver, dynamics, force, profile solve or real-world construction."""
import unittest
from retry.retime590_math import Lineage,backup_profile,plan_for_raw,Gates
class PureTests(unittest.TestCase):
    def test_history_trials_start_same_actual_history(self):
        root=object();a=object();b=object();line=Lineage(root,[3,40]);line.successor(a,[4,44]);line.successor(b,[3,44]);self.assertEqual(line.history(root),[3,40]);self.assertEqual(line.history(a),[4,44]);line.history(root)[0]=90;self.assertEqual(line.history(root),[3,40])
    def test_history_unknown_fails(self):
        line=Lineage(object(),[0,0])
        with self.assertRaises(KeyError):line.history(object())
    def test_backup_same_geometry_and_node_min(self):
        p=dict(points=[[0,0],[2,0]],ds=[2,2],arcs=[0,2,4],length=4,curvature=[0,0]);high=dict(periodic_squared=[8100,100],launch_squared=[0,80,200]);old=dict(periodic_squared=[6400,200],launch_squared=[0,70,300]);low=backup_profile(p,high,old);self.assertEqual(low['points'],p['points']);self.assertEqual(low['periodic_squared'],[6400,100]);self.assertEqual(low['launch_squared'],[0,70,200])
    def test_prefix_plan_boundary(self):
        old=object();new=object();self.assertIs(plan_for_raw(96,old,new),old);self.assertIs(plan_for_raw(97,old,new),new)
    def test_first_ineligible_forward_crossing_is_locked(self):
        gates=Gates([dict(station_m=400,center=[0,0],normal=[1,0])]);root=lambda x:dict(center=[x,0],planar=dict(linear=dict(velocity=[1,0]),yaw=0));row=dict(before_root_without_roads=root(-1),root_without_roads=root(1),global_raw_before=1,global_raw_after=2,episode_before_s=.02,index=1,progress=380,path_error=0);gates.add(row);row['progress']=400;gates.add(row);self.assertFalse(gates.hits['400']['eligible'])
    def test_crossing_needs_whole_hold_safe(self):
        g=Gates([dict(station_m=400,center=[0,0],normal=[1,0])]);root=lambda x:dict(center=[x,0],planar=dict(linear=dict(velocity=[1,0]),yaw=0));r=dict(before_root_without_roads=root(-1),root_without_roads=root(1),global_raw_before=1,global_raw_after=2,episode_before_s=.02,index=1,progress=400,path_error=0);g.add(r);self.assertFalse(g.passed('400'));g.finish_hold([r,r,r,r]);self.assertTrue(g.passed('400'))
