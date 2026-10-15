"""Unchanged296 perception/goal/steering/memory, then frozen H1 pedal selection."""
import numpy as np
from retry.h1_330_base import Agent as Frozen296
from retry.h1_330_select import choose
from retry.h1_330_model import MODELS,ENABLED
from retry.hud248_features import decode
from retry.hud_feedback import decode_feedback_speed


class Agent(Frozen296):
    def correct_pedals(self,features,nominal):
        self.selector_features=list(features)
        return super().correct_pedals(features,nominal)

    def act(self,observation):
        base=np.asarray(super().act(observation),np.float32);memory=float(self.controller.previous_steer)
        f=self.selector_features;state=None
        if ENABLED and not f[0]:
            image=observation[-1];hud=decode(image)
            state=np.array([decode_feedback_speed(image,f[3]),hud[5],hud[4]])
        action,audit=choose(base,f,state,MODELS,ENABLED)
        assert action[0]==base[0] and memory==float(self.controller.previous_steer)
        audit['nominal_memory_preserved']=True;self.delta_audit=audit
        return action
