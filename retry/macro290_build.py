"""Package fixed finalcategorical actor and3action macro state, no GT inputs."""
import zipfile,hashlib
from pathlib import Path
import numpy as np

def build(base,parameters,output):
 with zipfile.ZipFile(base) as z:members={n:z.read(n) for n in z.namelist()}
 original=dict(members);members['retry/frozen240_root.py']=original['agent.py'];params=np.load(parameters);mapping={'MEAN':'mean','STD':'std','W0':'actor_0.weight','B0':'actor_0.bias','W2':'actor_2.weight','B2':'actor_2.bias'}
 members['retry/macro290_parameters.py']=('import numpy as np\n'+''.join(name+'=np.array('+repr(params[key].tolist())+',dtype=np.float64)\n' for name,key in mapping.items())).encode()
 members['agent.py']=b'''"""Frozen discrete macro PPO290; pixel features and own executed history only."""
import numpy as np
from retry.frozen240_root import Agent as Frozen
from retry.macro290_parameters import MEAN,STD,W0,B0,W2,B2
class Agent(Frozen):
    def reset(self,observation):
        super().reset(observation)
        self.executed_history=[];self.macro_remaining=0;self.category=0;self.rng=np.random.default_rng(29007)
    def correct_pedals(self,features,nominal):
        self.legal_features=np.asarray(features,np.float64)
        return super().correct_pedals(features,nominal)
    def act(self,observation):
        base=np.asarray(super().act(observation),np.float32)
        decision=self.macro_remaining==0
        if decision:
            padded=np.zeros((3,3),float);mask=np.zeros(3,float)
            if self.executed_history:
                padded[-len(self.executed_history):]=self.executed_history;mask[-len(self.executed_history):]=1
            x=np.r_[(self.legal_features-MEAN)/STD,(padded/np.array([.4,1.,1.])).ravel(),mask]
            logits=np.tanh(x@W0.T+B0)@W2.T+B2
            probabilities=np.exp(logits-logits.max());probabilities/=probabilities.sum()
            self.category=int(self.rng.choice(5,p=probabilities));self.macro_remaining=3
            self.last_probabilities=probabilities.tolist()
        action=base.copy();nominal=self.legal_features[-3:]
        if self.category==1:action[1]=np.float32(np.clip(np.clip(nominal[1]+.5,0,1)*1.412502928638687,0,1))
        elif self.category==2:action[2]=np.float32(np.clip(np.clip(nominal[2]-.5,0,1)*.8138581028883641,0,1))
        elif self.category in [3,4]:action[0]=np.float32(np.clip(float(base[0])+(.015 if self.category==3 else -.015),-.4,.4))
        if action[0]!=base[0]:self.controller.previous_steer=float(action[0])
        self.executed_history.append(action.tolist());self.executed_history=self.executed_history[-3:];self.macro_remaining-=1
        self.macro_audit=dict(category=self.category,decision=decision,remaining=self.macro_remaining,probabilities=self.last_probabilities,base=base.tolist())
        return action
'''
 assert all(members[n]==v for n,v in original.items() if n!='agent.py')
 with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
  for name,data in sorted(members.items()):
   info=zipfile.ZipInfo(name,date_time=(2026,10,9,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,data)
 output.chmod(0o600);return dict(type='champion',archive_path=str(output),archive_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),members_sha256={n:hashlib.sha256(v).hexdigest() for n,v in members.items()},assets={},constants={},all_original_nonroot_files_byte_exact=True,not_champion=True)
