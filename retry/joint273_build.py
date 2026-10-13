"""Standalone pixel-only frozen minus/executed probe; parameters remain private."""
import hashlib,zipfile
from pathlib import Path
import numpy as np

def build(base,parameters,output):
    with zipfile.ZipFile(base) as z:members={n:z.read(n) for n in z.namelist()}
    original=dict(members);members['retry/frozen240_root.py']=original['agent.py']
    params=np.load(parameters)
    members['retry/joint273_model.py']=('import numpy as np\n'+''.join(name.upper()+'=np.array('+repr(params[name].tolist())+',dtype=np.float64)\n' for name in ['mean','std','theta'])).encode()
    members['agent.py']=b'''"""Frozen joint273 minus policy; legal pixels, executed steering memory."""
import numpy as np
from retry.frozen240_root import Agent as Frozen
from retry.joint273_model import MEAN,STD,THETA

class Agent(Frozen):
    def correct_pedals(self,features,nominal):
        self.joint_features=np.asarray(features,np.float64)
        return super().correct_pedals(features,nominal)

    def act(self,observation):
        base=np.asarray(super().act(observation),np.float32)
        row=np.r_[(self.joint_features-MEAN)/STD,1.]
        latent=-(row@THETA)
        action=np.clip(base.astype(float)+np.array([.015,.03,.02])*np.tanh(latent),[-.4,0,0],[.4,1,1]).astype(np.float32)
        self.controller.previous_steer=float(action[0])
        return action
'''
    assert all(members[n]==v for n,v in original.items() if n!='agent.py')
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(members.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,10,9,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,data)
    output.chmod(0o600)
    return dict(type='champion',archive_path=str(output),archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),members_sha256={n:hashlib.sha256(data).hexdigest() for n,data in members.items()},assets={},constants={},all_nonroot_original_files_byte_exact=True,original_root_preserved=True)
