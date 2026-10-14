"""Frozen learned275 mean actor, pixels and own action history only."""
import hashlib,zipfile
from pathlib import Path
import numpy as np

def build(base,parameters,output):
    with zipfile.ZipFile(base) as z:members={n:z.read(n) for n in z.namelist()}
    original=dict(members);members['retry/frozen296_root.py']=original['agent.py'];params=np.load(parameters)
    mapping={'MEAN':'mean','STD':'std','W0':'actor_0.weight','B0':'actor_0.bias','W2':'actor_2.weight','B2':'actor_2.bias'}
    members['retry/ppo275_model.py']=('import numpy as np\n'+''.join(name+'=np.array('+repr(params[key].tolist())+',dtype=np.float64)\n' for name,key in mapping.items())).encode()
    members['agent.py']=b'''"""317 learned deterministic mean policy; no GT, teacher or screen metadata."""
import numpy as np
from retry.frozen296_root import Agent as Frozen
from retry.ppo275_model import MEAN,STD,W0,B0,W2,B2

class Agent(Frozen):
    def reset(self,observation):
        super().reset(observation)
        self.executed_history=[]

    def correct_pedals(self,features,nominal):
        self.legal_features=np.asarray(features,np.float64)
        return super().correct_pedals(features,nominal)

    def act(self,observation):
        base=np.asarray(super().act(observation),np.float32)
        padded=np.zeros((3,3),np.float64);mask=np.zeros(3,np.float64)
        if self.executed_history:
            padded[-len(self.executed_history):]=self.executed_history
            mask[-len(self.executed_history):]=1
        x=np.r_[(self.legal_features-MEAN)/STD,(padded/np.array([.4,1.,1.])).ravel(),mask]
        latent=np.tanh(x@W0.T+B0)@W2.T+B2
        action=np.clip(base.astype(float)+np.array([.015,.03,.02])*np.tanh(latent),[-.4,0,0],[.4,1,1]).astype(np.float32)
        if action[0]!=base[0]:self.controller.previous_steer=float(action[0])
        self.executed_history.append(action.tolist());self.executed_history=self.executed_history[-3:]
        return action
'''
    assert all(members[n]==v for n,v in original.items() if n!='agent.py')
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(members.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,10,9,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,data)
    output.chmod(0o600)
    return dict(type='champion',archive_path=str(output),archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),members_sha256={n:hashlib.sha256(v).hexdigest() for n,v in members.items()},assets={},constants={},all_original_nonroot_files_byte_exact=True,not_champion=True)
