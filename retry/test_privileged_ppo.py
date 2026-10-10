"""Synthetic algorithm-interface sanity; no racing environment is executed."""
import unittest
from types import SimpleNamespace

import numpy as np
import gymnasium as gym
import torch
from stable_baselines3.common.buffers import RolloutBuffer
from stable_baselines3.common.vec_env import DummyVecEnv

from retry.privileged_ppo import (control_action, progress_reward,
    learning_end_flags, make_small_ppo, PrivilegedPilotEnv)


class StaticEnv(gym.Env):
    observation_space = gym.spaces.Box(-1., 1., (23,), np.float32)
    action_space = gym.spaces.Box(-1., 1., (2,), np.float32)
    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.count = 0
        return np.zeros(23, np.float32), {}
    def step(self, action):
        self.count += 1
        return np.ones(23, np.float32) * .1, float(action[1]), self.count >= 8, False, {}


class CurrentStateEnv(gym.Env):
    observation_space = gym.spaces.Box(0.,1.,(4,84,84),np.float32)
    action_space = gym.spaces.Box(-1.,1.,(3,),np.float32)
    def __init__(self, complete=False):
        self.complete=complete
        self.reset_inputs=[]
    def reset(self, *, seed=None, options=None):
        self.reset_inputs.append((seed,options))
        self.track=[(0.,0.,0.,0.),(0.,0.,0.,50.),(0.,0.,50.,50.),(0.,0.,50.,0.)]
        self.car=SimpleNamespace(hull=SimpleNamespace(position=[0.,0.],linearVelocity=[0.,1.],angle=0.,angularVelocity=0.))
        self.obstacles=[]; self.tile_visited_count=1; self.finish_time_s=None; self.t=1.02
        return np.zeros((4,84,84),np.float32),{}
    def step(self,action):
        self.car.hull.position[1]+=1
        self.tile_visited_count+=1; self.t+=.08
        if self.complete: self.finish_time_s=self.t
        return np.zeros((4,84,84),np.float32),-17.,False,self.complete,{}


class PilotSanity(unittest.TestCase):
    def test_bounds_and_signed_pedal(self):
        for u in [[-100,-100], [100,100], [0,0], [.3,-.7]]:
            a = control_action(u)
            self.assertEqual(a.dtype, np.float32)
            self.assertTrue(np.all(a >= np.array([-.4,0,0], np.float32)))
            self.assertTrue(np.all(a <= np.array([.4,.5,.5], np.float32)))
            self.assertEqual(a[1] * a[2], 0)

    def test_unique_reward_no_repeat_or_stationary_gain(self):
        self.assertEqual(progress_reward(7,7,100,False), -.001)
        self.assertEqual(progress_reward(7,9,100,False), 1.999)
        self.assertEqual(progress_reward(99,100,100,True), 10.999)
        with self.assertRaises(ValueError): progress_reward(7,6,100,False)

    def test_completion_and_failures_are_not_timeouts(self):
        self.assertEqual(learning_end_flags(False,True,True), (True,False))
        self.assertEqual(learning_end_flags(True,False,False), (True,False))
        self.assertEqual(learning_end_flags(False,True,False), (False,True))
        self.assertEqual(learning_end_flags(False,False,False,True), (False,True))
        self.assertEqual(learning_end_flags(False,False,False), (False,False))

    def test_rollout_cut_bootstrap_and_terminal_zero(self):
        obs=gym.spaces.Box(-1.,1.,(23,),np.float32)
        act=gym.spaces.Box(-1.,1.,(2,),np.float32)
        for done, want in [(False, 1+.99*4), (True,1.)]:
            b=RolloutBuffer(1,obs,act,device='cpu',gamma=.99,gae_lambda=.95)
            b.add(np.zeros((1,23),np.float32),np.zeros((1,2),np.float32),
                  np.array([1.]),np.array([True]),torch.tensor([2.]),torch.tensor([0.]))
            b.compute_returns_and_advantage(torch.tensor([4.]),np.array([done]))
            self.assertAlmostEqual(float(b.returns[0,0]),want,places=5)

    def test_actual_adapter_alignment_fixed_reset_and_completed_vec_mask(self):
        rows=[]; raw=CurrentStateEnv()
        env=PrivilegedPilotEnv(raw,12,{'track_id':4},horizon=2,observe=rows.append)
        before,_=env.reset(seed=999)
        after,r,term,trunc,info=env.step([.2,.6])
        self.assertTrue(np.array_equal(before,np.asarray(rows[0]['features_before'],np.float32)))
        self.assertTrue(np.array_equal(after,np.asarray(rows[0]['features_after'],np.float32)))
        self.assertEqual(rows[0]['unique_tiles_before'],1)
        self.assertEqual(rows[0]['unique_tiles_after'],2)
        self.assertAlmostEqual(r,24.999)
        self.assertEqual((term,trunc),(False,False))
        _,_,term,trunc,_=env.step([0,0]);self.assertEqual((term,trunc),(False,True))
        env.reset(seed=777);self.assertEqual(raw.reset_inputs,[(12,{'track_id':4}),(12,{'track_id':4})])
        completed=PrivilegedPilotEnv(CurrentStateEnv(True),12,{'track_id':4})
        vec=DummyVecEnv([lambda:completed]);vec.reset()
        _,_,dones,infos=vec.step(np.array([[0.,.2]],np.float32))
        self.assertTrue(dones[0]);self.assertFalse(infos[0]['TimeLimit.truncated'])
        self.assertTrue(infos[0]['raw_truncated']);self.assertTrue(infos[0]['completed'])
        self.assertIn('terminal_observation',infos[0]);vec.close()

    def test_ppo_changes_parameters_with_finite_loss_and_raw_logprob(self):
        torch.set_num_threads(1)
        model=make_small_ppo(StaticEnv(),1901)
        before={k:v.clone() for k,v in model.policy.state_dict().items()}
        model.learn(total_timesteps=256)
        self.assertEqual(model.num_timesteps,256)
        self.assertTrue(any(not torch.equal(before[k],v) for k,v in model.policy.state_dict().items()))
        self.assertTrue(all(torch.isfinite(v).all() for v in model.policy.state_dict().values()))
        obs=torch.zeros((1,23)); actions=torch.tensor([[2.,-2.]])
        _, logp,_=model.policy.evaluate_actions(obs,actions)
        distr=model.policy.get_distribution(obs)
        self.assertTrue(torch.allclose(logp,distr.log_prob(actions)))
        self.assertTrue(any(np.any(np.abs(a)>1) for a in model.rollout_buffer.actions))
        model.get_env().close()


if __name__ == '__main__': unittest.main()
