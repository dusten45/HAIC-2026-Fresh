"""Keep a shadow controller's action memory tied to executed actions."""
import json
import os
import selectors
import time

import numpy as np


class ExecutedHistoryTeacher:
    def __init__(self, policy):
        self.policy = policy
        self.initialized = False
        self.pending = None
        self.last_executed_action = np.zeros(3, dtype=np.float32)
        self.observations = self.commits = self.resets = 0

    def reset(self, observation):
        if self.initialized:
            raise RuntimeError("A warm teacher cannot be reset at takeover")
        self.policy.reset(observation)
        self.initialized = True
        self.resets += 1

    def propose(self, observation):
        if not self.initialized or self.pending is not None:
            raise RuntimeError("Reset once and commit each executed action before proposing again")
        previous = self.policy.controller.previous_steer
        proposal = np.asarray(self.policy.act(observation), dtype=np.float32).copy()
        if proposal.shape != (3,) or not np.isfinite(proposal).all():
            raise ValueError("A finite action is required")
        # The tracker has observed the frame; the provisional controller action
        # must not become executed history before the environment accepts it.
        self.policy.controller.previous_steer = previous
        self.pending = proposal
        self.observations += 1
        return proposal.copy()

    def commit(self, actual_action):
        if self.pending is None:
            raise RuntimeError("No proposal awaits an executed-action receipt")
        action = np.asarray(actual_action, dtype=np.float32).copy()
        if action.shape != (3,) or not np.isfinite(action).all():
            raise ValueError("A finite executed action is required")
        self.policy.controller.previous_steer = float(action[0])
        self.last_executed_action = action
        self.pending = None
        self.commits += 1


def commit_action(participant, action, timeout=5):
    """Acknowledge the actual action separately from the observation protocol."""
    deadline = time.monotonic() + timeout
    action = np.asarray(action, dtype=np.float32)
    if action.shape != (3,) or not np.isfinite(action).all():
        raise ValueError("A finite executed action is required")
    payload = (json.dumps({"op": "commit", "action": action.tolist()}) + "\n").encode()
    writer = selectors.DefaultSelector()
    writer.register(participant.process.stdin, selectors.EVENT_WRITE)
    offset = 0
    try:
        while offset < len(payload):
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not writer.select(remaining):
                participant.close()
                raise TimeoutError("Executed-action receipt deadline")
            try:
                offset += os.write(participant.process.stdin.fileno(), payload[offset:])
            except BlockingIOError:
                continue
        return participant.read_until(deadline)
    finally:
        writer.close()
