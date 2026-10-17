"""No-integration lifetime and archived-H13 gates."""
import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
from retry.live447 import LiveH13447,LiveGateError,check_historical_h13
from retry.loss389_analyze import read


class Live447Tests(unittest.TestCase):
    def make(self):
        archive=read(Path('/workspace/haic-private-retry-20261009/stage444/H1/nominal1-private.json'))
        c=SimpleNamespace(rows=copy.deepcopy(archive['rows']),initial_ok=True,initial_safe=True,initial_progress=True,
                          m=object(),ctrl=SimpleNamespace(memory=lambda:copy.deepcopy(archive['controller_memory'])),
                          stream=SimpleNamespace(key='sealed',boundary=SimpleNamespace(key=lambda:'sealed')))
        return c,archive

    def test_H13_archive_exact_gate(self):
        c,a=self.make()
        with patch('retry.live447.snapshot',return_value=copy.deepcopy(a['final_state'])):
            check_historical_h13(c,a)

    def test_H13_difference_or_unsafe_not_waived(self):
        c,a=self.make();c.rows[0]['model_progress']+=.001
        with self.assertRaises(LiveGateError):check_historical_h13(c,a)
        c,a=self.make();c.initial_safe=False
        with self.assertRaises(LiveGateError):check_historical_h13(c,a)

    def test_same_live_identity_survives_append(self):
        c,a=self.make();token=LiveH13447.seal(c);c.rows.append({'diagnostic':'one new model transition'})
        self.assertTrue(token.validate(c))

    def test_recreated_child_or_world_is_rejected(self):
        c,a=self.make();token=LiveH13447.seal(c)
        with self.assertRaises(LiveGateError):token.validate(SimpleNamespace(**c.__dict__))
        c.m=object()
        with self.assertRaises(LiveGateError):token.validate(c)

    def test_changed_stream_or_old_prefix_is_rejected(self):
        c,a=self.make();token=LiveH13447.seal(c);c.stream=copy.copy(c.stream)
        with self.assertRaises(LiveGateError):token.validate(c)
        c,a=self.make();token=LiveH13447.seal(c);c.rows[0]['model_age']+=1
        with self.assertRaises(LiveGateError):token.validate(c)

    def test_changed_boundary_key_is_rejected(self):
        c,a=self.make();token=LiveH13447.seal(c);c.stream.key='changed'
        with self.assertRaises(LiveGateError):token.validate(c)
