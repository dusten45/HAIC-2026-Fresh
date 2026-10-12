"""Two fixed-basis conditional brake coefficients, unchanged240 underneath."""
import numpy as np
from retry.nominal242_base import Agent as FrozenAgent
from retry.conditional242_model import THETA


def bases(features):
    f=np.asarray(features,float)
    curve=1.0 if f[0] else float(np.clip(abs(f[5])*f[4]**2/24.,0,1))
    proximity=1./(1.+f[12]/5.) if f[11]>0 else 0.
    hazard=max(float(f[8]),proximity)
    return np.asarray([curve,hazard],np.float64)


class Agent(FrozenAgent):
    def correct_pedals(self, features, nominal):
        result=super().correct_pedals(features,nominal)
        self.current_legal_features=list(map(float,features))
        return result

    def act(self, observation):
        before=np.asarray(super().act(observation),np.float32)
        memory=float(self.controller.previous_steer)
        basis=bases(self.current_legal_features)
        multiplier=float(np.exp(THETA@basis))
        after=before.copy();after[2]=np.float32(np.clip(float(before[2])*multiplier,0,1))
        assert np.array_equal(before[:2],after[:2]) and self.controller.previous_steer==memory
        self.last_audit=dict(before=before.tolist(),after=after.tolist(),basis=basis.tolist(),
            features=self.current_legal_features,theta=THETA.tolist(),composed_multiplier=multiplier,
            brake_clipped=bool(float(before[2])*multiplier>1),gas_steering_unchanged=True,nominal_memory_preserved=True)
        return after
