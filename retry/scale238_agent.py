"""Frozen232 final pedals multiplied by two bounded global scales only."""
import numpy as np
from retry.nominal238_base import Agent as FrozenAgent
from retry.scale238_model import SCALES


class Agent(FrozenAgent):
    def act(self, observation):
        before=np.asarray(super().act(observation),np.float32)
        memory=float(self.controller.previous_steer)
        after=before.copy();pre=before[1:].astype(float)*SCALES
        after[1:]=np.clip(pre,0,1).astype(np.float32)
        assert after[0]==before[0] and self.controller.previous_steer==memory
        self.last_audit=dict(before=before.tolist(),after=after.tolist(),
            scales=SCALES.tolist(),pedal_clipped=((pre<0)|(pre>1)).tolist(),
            nominal_memory_preserved=True,steering_unchanged=True)
        return after
