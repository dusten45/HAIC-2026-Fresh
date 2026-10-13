"""One categorical semi-Markov PPO recipe, legal28inputs, five3action options."""
import numpy as np
from retry.ppo275_model import vector
from retry.ppo244_math import reward
CLASSES=['baseline','gas_upper','brake_lower','steer_plus','steer_minus']
PROBS=np.array([.6,.1,.1,.1,.1]);SCALES=np.array([1.412502928638687,.8138581028883641])
RECIPE=dict(input_dim=28,hidden=32,actor_output_dim=5,dtype='float64',initial_probabilities=PROBS.tolist(),native_per_rollout=1024,updates=16,total_training_native=16384,macro_max_native=3,epochs=4,minibatch_decisions_max=64,actor_lr=3e-4,critic_lr=3e-4,clip=.1,target_KL=.01,max_gradient_norm=.5,gamma_per_decision=1.,GAE_lambda_per_decision=.95,entropy_coefficient=0.,actor_seed=290,sample_seed=29001,shuffle_seed=29002,final_policy_mode='stochasticcategorical fixedlegal internalRNG resetseed29007',final_reset_seed=29007,cut_rule='Onlycompletedmacro boundary;1/2remainingnativeunused;actualterminalshortens',road_order=['O0','N0','O2','N1','N2','N3'])
def create():
 import torch
 from torch import nn
 torch.set_num_threads(1);torch.manual_seed(290)
 actor=nn.Sequential(nn.Linear(28,32,dtype=torch.float64),nn.Tanh(),nn.Linear(32,5,dtype=torch.float64));critic=nn.Sequential(nn.Linear(28,32,dtype=torch.float64),nn.Tanh(),nn.Linear(32,1,dtype=torch.float64))
 for net in [actor,critic]:
  nn.init.orthogonal_(net[0].weight,.5);nn.init.zeros_(net[0].bias);nn.init.zeros_(net[2].weight);nn.init.zeros_(net[2].bias)
 with torch.no_grad():actor[2].bias.copy_(torch.tensor(np.log(PROBS),dtype=torch.float64))
 return actor,critic
def apply(base,features,category):
 out=np.asarray(base,np.float32).copy();nominal=np.asarray(features[-3:],float)
 if category==1:out[1]=np.float32(np.clip(np.clip(nominal[1]+.5,0,1)*SCALES[0],0,1))
 elif category==2:out[2]=np.float32(np.clip(np.clip(nominal[2]-.5,0,1)*SCALES[1],0,1))
 elif category in [3,4]:out[0]=np.float32(np.clip(float(out[0])+(.015 if category==3 else -.015),-.4,.4))
 else:assert category==0
 return out
