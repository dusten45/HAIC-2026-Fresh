from types import SimpleNamespace
import unittest

import numpy as np
from retry.executed_history import ExecutedHistoryTeacher


class FakePolicy:
    def __init__(self):
        self.controller = SimpleNamespace(previous_steer=0.)
        self.seen_previous = []

    def reset(self, observation):
        self.controller.previous_steer = 0.

    def act(self, observation):
        self.seen_previous.append(self.controller.previous_steer)
        self.controller.previous_steer = .3
        return np.array([.3, .5, 0], np.float32)


class ExecutedHistoryTests(unittest.TestCase):
    def test_unexecuted_proposal_never_enters_next_controller_history(self):
        policy = FakePolicy(); teacher = ExecutedHistoryTeacher(policy)
        teacher.reset(None); teacher.propose(None)
        self.assertEqual(policy.controller.previous_steer, 0.)
        actual = np.array([-.1, 0., .2], np.float32)
        teacher.commit(actual); teacher.propose(None)
        self.assertEqual(policy.seen_previous, [0., float(actual[0])])
        np.testing.assert_array_equal(teacher.last_executed_action, actual)

    def test_takeover_reset_and_double_observation_are_rejected(self):
        teacher = ExecutedHistoryTeacher(FakePolicy()); teacher.reset(None)
        teacher.propose(None)
        with self.assertRaises(RuntimeError): teacher.propose(None)
        with self.assertRaises(RuntimeError): teacher.reset(None)
        teacher.commit([.3, .5, 0])
        self.assertEqual((teacher.resets, teacher.observations, teacher.commits), (1, 1, 1))


if __name__ == '__main__': unittest.main()
