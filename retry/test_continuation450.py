"""Same-live cap/stop controls plus observed-root current-context fixtures."""
import copy,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from retry.continuation450 import continue450
from retry.root449 import load_root449
from retry.loss389_analyze import read
from retry.fixture438 import stored_env
from retry.actual437_boundary import live_proxy
from retry.paired417_common import SourceC
from retry.pilot420_backend import capture_context
R=Path('/workspace/haic-private-retry-20261009')

class Continuation450Tests(unittest.TestCase):
    def child(self):
        archive=read(R/'stage444/H1/nominal1-private.json')
        c=SimpleNamespace(rows=copy.deepcopy(archive['rows']),status='ACTIVE',initial_count=13,initial_ok=True,initial_safe=True,initial_progress=True,m=object(),recipe='nominal',root_ledger=SimpleNamespace(progress_m=1.),ledger=SimpleNamespace(deadline_missed=False),tail_count=0)
        c.stream=SimpleNamespace(key='sealed',boundary=SimpleNamespace(key=lambda:'sealed'),prepare_boundary=lambda ctx:None,start_tail=lambda:None)
        c.one=lambda tag:c.rows.append(dict(safety=[]))
        return c
    def test_observed_roots_satisfy_current_context_without_native_authority(self):
        p=read(R/'stage449/plan.json');fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(p['pace_path'])['frozen268'])
        for arm in ['nominal','fullgas']:
            data=load_root449(R,arm);proxy=live_proxy(stored_env(data['full']));ctrl=SourceC(fixed,pace,copy.deepcopy(data['memory']));before=ctrl.memory();nominal=ctrl.act(proxy)
            ctx=capture_context(proxy,ctrl,before,nominal,data['ledger'],fixed,'fixture450',{},data['ledger'].digest());ctx.validate()
            self.assertEqual(ctx.gate(),'QUERY_CURRENT');self.assertEqual(ctx.ledger,data['ledger'])
    def test_same_child_can_exit_after_two_tail_actions(self):
        c=self.child()
        with patch('retry.continuation450.arrival',side_effect=[dict(reached=False),dict(reached=True)]) as arrival:
            hit,token=continue450(c,object(),[],271.)
        self.assertTrue(hit['reached']);self.assertEqual(c.tail_count,2);self.assertEqual(arrival.call_count,2);self.assertTrue(token.validate(c))
    def test_total64_means_only51_additional_actions(self):
        c=self.child()
        with patch('retry.continuation450.arrival',return_value=dict(reached=False)) as arrival:
            hit,token=continue450(c,object(),[],271.)
        self.assertFalse(hit['reached']);self.assertEqual(len(c.rows),64);self.assertEqual(c.tail_count,51);self.assertEqual(arrival.call_count,51)
    def test_changed_world_stops_before_any_next_action(self):
        c=self.child()
        def replaced(tag):c.rows.append(dict(safety=[]));c.m=object()
        c.one=replaced
        with patch('retry.continuation450.arrival') as arrival:
            with self.assertRaises(Exception):continue450(c,object(),[],271.)
        self.assertEqual(len(c.rows),14);self.assertEqual(arrival.call_count,0)
    def test_changed_H13_prefix_is_not_waived(self):
        c=self.child()
        def changed(tag):c.rows.append(dict(safety=[]));c.rows[0]['model_progress']+=.001
        c.one=changed
        with self.assertRaises(Exception):continue450(c,object(),[],271.)
        self.assertEqual(len(c.rows),14)
    def test_first_unsafe_tail_stops_with_recorded_row(self):
        c=self.child()
        def unsafe(tag):c.rows.append(dict(safety=['path_error_over3m']));c.status='UNSAFE'
        c.one=unsafe
        with self.assertRaises(Exception):continue450(c,object(),[],271.)
        self.assertEqual(len(c.rows),14)
