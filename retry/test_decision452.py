"""Recorded-model replay labeling and single-new-decision controls, no physics."""
import copy,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from retry.decision452 import Parent452
from retry.segment451 import Parent451
from retry.root449 import load_root449
from retry.loss389_analyze import read
from retry.planner419_model_ledger import ForecastLedger
R=Path('/workspace/haic-private-retry-20261009')

class Decision452Tests(unittest.TestCase):
    def parent(self,count=0):
        c=Parent452.__new__(Parent452);c.segment451=None;c._selected451=False;c._replay452=False;c.rows=[];c.status='ACTIVE';c.label='fixture452'
        source=read(R/'stage451/fullgas1-private.json');c.rows=copy.deepcopy(source['rows'][:count])
        return c,source
    def test_unplanned_prefix_step_is_forbidden(self):
        c,source=self.parent()
        with self.assertRaises(Exception):c.one('unplanned')
    def test_recorded_source_one_is_exact_and_bounded(self):
        c,source=self.parent();frame=source['rows'][0]
        with patch.object(Parent451,'one',side_effect=lambda *a,**kw:c.rows.append(copy.deepcopy(frame))):c.replay_source_one(frame)
        self.assertEqual(c.rows,[frame]);self.assertFalse(c._replay452)
        c.rows=copy.deepcopy(source['rows'])
        with self.assertRaises(Exception):c.replay_source_one(frame)
    def test_recorded_source_mismatch_stops_without_next_step(self):
        c,source=self.parent();frame=source['rows'][0];bad=copy.deepcopy(frame);bad['model_progress']+=.001
        with patch.object(Parent451,'one',side_effect=lambda *a,**kw:c.rows.append(bad)) as step:
            with self.assertRaises(Exception):c.replay_source_one(frame)
        self.assertEqual(step.call_count,1);self.assertEqual(len(c.rows),1)
    def test_new_scope_begins_after_exact48_with_native_root_separate(self):
        c,source=self.parent(48);actual=load_root449(R,'fullgas')['ledger'];c.ledger=ForecastLedger(**source['model_ledger']);c.m=SimpleNamespace(t=source['final_state']['physical']['actual_time'],native_ticks=192);c.ctrl=SimpleNamespace(memory=lambda:copy.deepcopy(source['controller_memory']));c.stream=SimpleNamespace(require_owner=lambda owner:self.assertIs(owner,c))
        with tempfile.TemporaryDirectory() as td,patch('retry.decision452.snapshot',return_value=source['final_state']):c.begin_current_one(actual,Path(td))
        self.assertEqual(c.segment451.prefix_actions,48);self.assertIs(c.segment451.actual,actual);c.segment451.validate(c,actual)
        for call in [lambda:c.evidence(None),lambda:c.continue_tail('not_nominal')]:
            with self.assertRaises(Exception):call()
    def test_second_new_decision_is_blocked_before_parent_call(self):
        c,source=self.parent(48);c.segment451=object()
        with patch.object(Parent451,'guarded_one',side_effect=lambda *a,**kw:c.rows.append(dict(new_current=True))) as selected:
            c.guarded_one(None,None,None,None,None,'one')
            with self.assertRaises(Exception):c.guarded_one(None,None,None,None,None,'two')
        self.assertEqual(selected.call_count,1);self.assertEqual(len(c.rows),49)
