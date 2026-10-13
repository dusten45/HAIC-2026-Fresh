"""Fixed legal joint PPO recipe, latent likelihood, completed-time objective."""
import numpy as np
from retry.ppo244_math import reward

STD=.2
BOUNDS=np.array([.015,.03,.02])
RECIPE=dict(input_dim=28,hidden=32,actor_output_dim=3,dtype='float64',rollout=1024,
    epochs=4,minibatch=128,actor_lr=3e-4,critic_lr=3e-4,clip=.1,target_KL=.01,
    gamma=1.,GAE_lambda=.95,max_gradient_norm=.5,std=STD,residual_bounds=BOUNDS.tolist(),
    pilot_batches=3,pilot_native=3072,road_order=['O0','N0','O2','N1','N2','N3'])

def create():
    import torch
    from torch import nn
    torch.set_num_threads(1);torch.manual_seed(275)
    actor=nn.Sequential(nn.Linear(28,32,dtype=torch.float64),nn.Tanh(),nn.Linear(32,3,dtype=torch.float64))
    critic=nn.Sequential(nn.Linear(28,32,dtype=torch.float64),nn.Tanh(),nn.Linear(32,1,dtype=torch.float64))
    for net in [actor,critic]:
        nn.init.orthogonal_(net[0].weight,.5);nn.init.zeros_(net[0].bias)
        nn.init.zeros_(net[2].weight);nn.init.zeros_(net[2].bias)
    return actor,critic

def vector(response,mean,std):
    result=np.r_[(np.array(response['features'])-mean)/std,response['history_features']]
    assert result.shape==(28,) and np.isfinite(result).all()
    return result

def logp(z,mu):
    return -.5*np.sum(((np.asarray(z)-mu)/STD)**2,axis=-1)-3*np.log(STD)-1.5*np.log(2*np.pi)

def apply(base,z):
    return np.clip(np.asarray(base,np.float32).astype(float)+BOUNDS*np.tanh(z),[-.4,0,0],[.4,1,1]).astype(np.float32)
