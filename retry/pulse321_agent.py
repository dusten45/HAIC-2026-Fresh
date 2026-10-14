"""One first-overlap steering/brake action; then frozen296 with executed memory."""
import numpy as np
import hashlib
from retry.shield319_base import Agent as FrozenAgent
from retry.shield319_constants import ENABLED, ARM
from retry.hud248_features import decode
from retry.shield319_geometry import decision


class Agent(FrozenAgent):
    def reset(self,observation):
        super().reset(observation);self.shield_latched=False

    def correct_pedals(self,features,nominal):
        self.shield_features=list(features)
        return super().correct_pedals(features,nominal)

    def act(self,observation):
        pre_state=dict(previous_steer=float(self.controller.previous_steer),lateral_acceleration=float(self.controller.lateral_acceleration),hazards=[list(h) for h in self.hazards],previous_image_sha256=hashlib.sha256(self.previous_image.tobytes()).hexdigest() if self.previous_image is not None else None)
        input_sha=hashlib.sha256(observation.tobytes()).hexdigest()
        base=np.asarray(super().act(observation),np.float32)
        hud=decode(observation[-1]);obstacles=[p[:3] for p in self.hazards]
        action,audit=decision(base,self.shield_features[4],hud[5],hud[4],obstacles,self.shield_latched)
        self.shield_latched=audit['latch_after']
        applied=ENABLED and audit['strict_improvement']
        if not applied:action=base.copy()
        elif ARM=='A':action[1:]=base[1:]
        elif ARM=='B':action[0]=base[0]
        else:raise ValueError('Unexpected ablation arm')
        if action[0]!=base[0]:self.controller.previous_steer=float(action[0])
        self.shield_audit=dict(audit,arm=ARM,policy_state_before=pre_state,observation_sha256=input_sha,enabled=ENABLED,applied=bool(applied),base=base.tolist(),action=action.tolist(),
            executed_memory=float(self.controller.previous_steer),tracked_obstacles=obstacles,
            HUD_speed=float(self.shield_features[4]),HUD_yaw=float(hud[5]),HUD_joint=float(hud[4]))
        return action
