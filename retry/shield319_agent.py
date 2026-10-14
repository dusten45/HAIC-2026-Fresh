"""One first-overlap steering/brake action; then frozen296 with executed memory."""
import numpy as np
from retry.shield319_base import Agent as FrozenAgent
from retry.shield319_constants import ENABLED
from retry.hud248_features import decode
from retry.shield319_geometry import decision


class Agent(FrozenAgent):
    def reset(self,observation):
        super().reset(observation);self.shield_latched=False

    def correct_pedals(self,features,nominal):
        self.shield_features=list(features)
        return super().correct_pedals(features,nominal)

    def act(self,observation):
        base=np.asarray(super().act(observation),np.float32)
        hud=decode(observation[-1]);obstacles=[p[:3] for p in self.hazards]
        action,audit=decision(base,self.shield_features[4],hud[5],hud[4],obstacles,self.shield_latched)
        self.shield_latched=audit['latch_after']
        applied=ENABLED and audit['strict_improvement']
        if not applied:action=base.copy()
        if action[0]!=base[0]:self.controller.previous_steer=float(action[0])
        self.shield_audit=dict(audit,enabled=ENABLED,applied=bool(applied),base=base.tolist(),action=action.tolist(),
            executed_memory=float(self.controller.previous_steer),tracked_obstacles=obstacles,
            HUD_speed=float(self.shield_features[4]),HUD_yaw=float(hud[5]),HUD_joint=float(hud[4]))
        return action
