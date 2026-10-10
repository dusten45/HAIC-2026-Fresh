"""Fixed piecewise actions for offline simulator probes, not an online Agent.

The caller supplies a preregistered sequence and the offset after a branch.
No candidate generation, simulator, state estimation or ranking is performed.
Outside the sequence the unmodified baseline action is returned. Controller
feedback, replay validation and evaluation remain the caller's responsibility.
"""

import bisect
import numbers

import numpy as np


class ActionSequence:
    def __init__(self, phases):
        ends, actions, total = [], [], 0
        for phase in phases:
            if set(phase) != {'duration_actions', 'action'}:
                raise ValueError('Each phase needs duration_actions and action')
            duration = phase['duration_actions']
            if isinstance(duration, bool) or not isinstance(duration, numbers.Integral) or duration <= 0:
                raise ValueError('Phase duration must be a positive integer')
            action = np.asarray(phase['action'], dtype=np.float32)
            if action.shape != (3,) or not np.isfinite(action).all():
                raise ValueError('Action must be a finite steering/gas/brake vector')
            if np.any(action < [-1., 0., 0.]) or np.any(action > [1., 1., 1.]):
                raise ValueError('Action outside the environment action domain')
            total += int(duration)
            ends.append(total)
            actions.append(tuple(float(x) for x in action))
        self._ends = tuple(ends)
        self._actions = tuple(actions)
        self.duration_actions = total

    def apply(self, offset, baseline_action):
        if isinstance(offset, bool) or not isinstance(offset, numbers.Integral):
            raise ValueError('Sequence offset must be an integer')
        if offset < 0 or offset >= self.duration_actions:
            return np.asarray(baseline_action, dtype=np.float32).copy(), False
        phase = bisect.bisect_right(self._ends, offset)
        return np.asarray(self._actions[phase], dtype=np.float32), True
