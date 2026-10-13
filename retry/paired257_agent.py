"""Current240 plus exactly256paired reduction aftereveryaction; legalpixels only."""
from retry.reference257 import Agent as Frozen240
from retry.paired257_math import paired


class Agent(Frozen240):
    def correct_pedals(self,features,nominal):
        self.legal_speed257=float(features[4])
        return super().correct_pedals(features,nominal)

    def act(self,observation):
        before=super().act(observation);memory=float(self.controller.previous_steer)
        after,K,d=paired(before,self.legal_speed257)
        assert after[0]==before[0] and self.controller.previous_steer==memory
        self.paired257_audit=dict(before=before.tolist(),after=after.tolist(),K=K,d=d)
        return after
