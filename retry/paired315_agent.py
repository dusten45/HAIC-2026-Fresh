"""Retrieve one intact teacher pedal pair; preserve296 steering and memory."""
import numpy as np
from retry.paired315_base import Agent as FrozenAgent
from retry.paired315_model import MEAN, STD, X, Y, ENABLED


class Agent(FrozenAgent):
    def correct_pedals(self,features,nominal):
        self.query_features=list(features)
        return super().correct_pedals(features,nominal)

    def act(self,observation):
        before=np.asarray(super().act(observation),np.float32)
        memory=float(self.controller.previous_steer)
        query=(np.asarray(self.query_features,np.float64)-MEAN)/STD
        distances=np.sum((X-query)**2,axis=1)
        index=int(np.argmin(distances))
        after=before.copy()
        if ENABLED:
            after[1:]=Y[index].astype(np.float32)
        assert after[0]==before[0] and memory==float(self.controller.previous_steer)
        assert np.isfinite(after).all() and np.all(after[1:]>=0) and np.all(after[1:]<=1)
        self.delta_audit=dict(before=before.tolist(),after=after.tolist(),nearest_index=index,
            squared_distance=float(distances[index]),teacher_pair=Y[index].tolist(),
            enabled=ENABLED,memory_preserved=True)
        return after
