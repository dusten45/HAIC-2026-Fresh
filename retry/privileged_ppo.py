"""Small research-only PPO adapter; not a pixel participant or submission.

Learning rewards and terminal annotations are separate from HAIC outcomes.
The underlying simulator, damage, rendering, and retirement rules are intact.
"""
import numpy as np
import gymnasium as gym

from retry.privileged_state import FEATURE_DIM, privileged_features


def control_action(normalized):
    """Clip two policy coordinates and map to legal steer/gas/brake.

    PPO's Gaussian log probability uses its original sample; this fixed map is
    the environment's execution transform. Pedals are mutually exclusive.
    """
    values = np.asarray(normalized, dtype=np.float32)
    if values.shape != (2,) or not np.isfinite(values).all():
        raise ValueError("finite two-coordinate action required")
    steer, pedal = np.clip(values, -1., 1.)
    return np.asarray([.4 * steer, .5 * max(pedal, 0.),
                       .5 * max(-pedal, 0.)], dtype=np.float32)


def progress_reward(before_tiles, after_tiles, total_tiles, completed):
    """Pay only new unique tiles, once-only completion, and a tiny time cost.

    Reset visits are excluded. Same-place motion or repeat visits earn no
    progress reward. The caller stops the episode immediately on completion.
    """
    if not (0 <= before_tiles <= after_tiles <= total_tiles and total_tiles > 0):
        raise ValueError("monotonic bounded unique tile counts required")
    return 100. * (after_tiles - before_tiles) / total_tiles + 10. * bool(completed) - .001


def learning_end_flags(terminated, truncated, completed, at_horizon=False):
    """HAIC completed laps truncate, but their episodic learning value is zero.

    Actual failure also has zero bootstrap. Only an unfinished time limit is a
    timeout for PPO. A collection rollout boundary is not an environment end.
    """
    terminal = bool(terminated or completed)
    timeout = bool((truncated or at_horizon) and not terminal)
    return terminal, timeout


class PrivilegedPilotEnv(gym.Wrapper):
    """Fixed-condition current-state research interface for an unchanged env.

    ``execute`` may meter wrapper actions before delegating to env.step.
    ``observe`` receives audit rows outside the policy; it must not mutate the
    simulator. This adapter performs no teacher/controller/model calls.
    An optional ``action_transform`` maps policy coordinates directly to the
    executed three controls; custom coordinates are logged without clipping.
    """
    def __init__(self, env, reset_seed, reset_options, horizon=2000,
                 execute=None, observe=None, action_transform=None):
        super().__init__(env)
        self.reset_seed = int(reset_seed)
        self.reset_options = dict(reset_options)
        self.horizon = int(horizon)
        self.execute = execute or (lambda env, action: env.step(action))
        self.observe = observe
        self.action_transform = action_transform or control_action
        self.observation_space = gym.spaces.Box(-np.inf, np.inf,
                                                (FEATURE_DIM,), np.float32)
        self.action_space = gym.spaces.Box(-1., 1., (2,), np.float32)
        self.steps = 0
        self.last_features = None
        self.episode = 0
        self.closed_episode = True

    def reset(self, *, seed=None, options=None):
        # Learner RNG seeds never change the preregistered track condition.
        _, info = self.env.reset(seed=self.reset_seed, options=self.reset_options)
        self.steps = 0
        self.episode += 1
        self.closed_episode = False
        self.last_features = privileged_features(self.env)
        return self.last_features.copy(), dict(info)

    def step(self, action):
        if self.closed_episode:
            raise RuntimeError("reset required before another episode action")
        features_before = self.last_features.copy()
        count_before = int(self.env.unwrapped.tile_visited_count)
        actual_action = self.action_transform(action)
        _, official_reward, raw_terminal, raw_truncated, info = self.execute(self.env, actual_action)
        self.steps += 1
        raw = self.env.unwrapped
        completed = raw.finish_time_s is not None
        count_after = int(raw.tile_visited_count)
        reward = progress_reward(count_before, count_after, len(raw.track), completed)
        terminal, timeout = learning_end_flags(raw_terminal, raw_truncated, completed,
                                               self.steps >= self.horizon)
        features_after = privileged_features(self.env)
        self.last_features = features_after
        self.closed_episode = terminal or timeout
        info = dict(info)
        info.update(official_reward=float(official_reward), unique_tiles=count_after,
                    new_unique_tiles=count_after-count_before, total_tiles=len(raw.track),
                    completed=completed, raw_terminated=bool(raw_terminal),
                    raw_truncated=bool(raw_truncated), learning_terminal=terminal,
                    learning_timeout=timeout, pilot_horizon_reached=self.steps >= self.horizon)
        if self.observe is not None:
            self.observe({"episode": self.episode, "step": self.steps,
                "features_before": features_before.tolist(), "features_after": features_after.tolist(),
                "normalized_applied_action": np.clip(np.asarray(action, np.float32), -1., 1.).tolist()
                    if self.action_transform is control_action else None,
                "policy_action_coordinates": np.asarray(action, np.float32).tolist(),
                "custom_action_transform": self.action_transform is not control_action,
                "executed_action": actual_action.tolist(), "unique_tiles_before": count_before,
                "unique_tiles_after": count_after, "learning_reward": reward,
                "official_reward": float(official_reward), "completed": completed,
                "raw_terminated": bool(raw_terminal), "raw_truncated": bool(raw_truncated),
                "learning_terminal": terminal, "learning_timeout": timeout,
                "retire_reason": info.get("retire_reason"), "time_s_after": float(raw.t)})
        return features_after.copy(), float(reward), terminal, timeout, info


def make_small_ppo(env, seed):
    """One fixed small CPU PPO setting. Dependency is optional for other retry code."""
    import torch
    from stable_baselines3 import PPO
    return PPO("MlpPolicy", env, seed=int(seed), device="cpu", verbose=0,
        learning_rate=3e-4, n_steps=256, batch_size=64, n_epochs=5,
        gamma=.99, gae_lambda=.95, clip_range=.2, clip_range_vf=None,
        normalize_advantage=True, ent_coef=.005, vf_coef=.5, max_grad_norm=.5,
        use_sde=False, target_kl=None,
        policy_kwargs={"net_arch": {"pi": [32, 32], "vf": [32, 32]},
                       "activation_fn": torch.nn.Tanh, "log_std_init": -.5})
