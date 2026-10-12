"""One output-only magnitude comparison, frozen232 policy unchanged beneath it."""
import numpy as np
from retry.nominal236_base import Agent as FrozenAgent


class Agent(FrozenAgent):
    def act(self, observation):
        before = np.asarray(super().act(observation), np.float32)
        memory = float(self.controller.previous_steer)
        after = before.copy()
        if before[1] > before[2]:
            after[2] = 0.0
        elif before[2] > before[1]:
            after[1] = 0.0
        else:
            after[1:] = 0.0
        assert after[0] == before[0] and self.controller.previous_steer == memory
        self.last_audit = dict(before=before.tolist(), after=after.tolist(),
            nominal_memory_after=memory, steering_unchanged=True, nominal_memory_preserved=True)
        return after
