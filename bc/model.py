"""Small observation-only behavior cloning policy for CPU inference."""

from collections import deque

import numpy as np
import torch
from torch import nn
from bc.contracts import OBSERVATION_SHAPE


class BCPolicy(nn.Module):
    """Maps four or eight normalized grayscale frames to [steer, gas, brake]."""

    def __init__(self, motion=False, history_frames=4, signed_longitudinal=False,
                 mode_longitudinal=False):
        super().__init__()
        if history_frames not in (4, 8):
            raise ValueError("history_frames must be 4 or 8")
        if history_frames == 8 and motion:
            raise ValueError("history8 cannot be combined with motion features")
        if signed_longitudinal and history_frames != 8:
            raise ValueError("signed-longitudinal trial requires history8")
        if mode_longitudinal and (history_frames != 8 or signed_longitudinal):
            raise ValueError("mode-longitudinal requires history8 and cannot be combined with signed")
        self.motion = motion
        self.history_frames = history_frames
        self.signed_longitudinal = signed_longitudinal
        self.mode_longitudinal = mode_longitudinal
        self._history = None
        self.features = nn.Sequential(
            nn.Conv2d(4, 8, kernel_size=8, stride=4), nn.ReLU(),
            nn.Conv2d(8, 16, kernel_size=4, stride=2), nn.ReLU(),
            nn.Conv2d(16, 16, kernel_size=3), nn.ReLU(),
            nn.Flatten(),
        )
        self.head = nn.Sequential(nn.Linear(16 * 7 * 7 + (2 if motion else 0), 32),
                                  nn.ReLU(), nn.Linear(32, 3))
        if history_frames == 8:
            # Build the entire original CNN first; widening must not shift its RNG.
            original = self.features[0]
            with torch.random.fork_rng(devices=[]):
                extended = nn.Conv2d(8, 8, kernel_size=8, stride=4)
            extended.load_state_dict({
                "weight": torch.cat((torch.zeros_like(original.weight), original.weight), dim=1),
                "bias": original.bias,
            })
            self.features[0] = extended
        if signed_longitudinal:
            # Preserve the shared and steering initialization, including RNG state.
            original = self.head[-1]
            with torch.random.fork_rng(devices=[]):
                controls = nn.Linear(32, 2)
            controls.load_state_dict({"weight": original.weight[:2], "bias": original.bias[:2]})
            self.head[-1] = controls
        if mode_longitudinal:
            original = self.head[-1]
            with torch.random.fork_rng(devices=[]):
                controls = nn.Linear(32, 5)
            with torch.no_grad():
                controls.weight[0].copy_(original.weight[0])
                controls.bias[0].copy_(original.bias[0])
            self.head[-1] = controls

    @staticmethod
    def longitudinal_targets(actions):
        gas, brake = actions[:, 1], actions[:, 2]
        if torch.any((gas > 0) & (brake > 0)):
            raise ValueError("Mode targets require no simultaneous positive gas/brake")
        mode = torch.where(gas > 0, 0, torch.where(brake > 0, 2, 1))
        return mode, torch.maximum(gas, brake)

    @staticmethod
    def decode_mode(controls):
        mode = controls[:, 1:4].argmax(dim=1)
        magnitude = controls[:, 4]
        return torch.stack((controls[:, 0], magnitude * (mode == 0),
                            magnitude * (mode == 2)), dim=1)

    @staticmethod
    def decode_signed(controls):
        longitudinal = controls[:, 1:2]
        return torch.cat((controls[:, :1], longitudinal.clamp_min(0),
                          (-longitudinal).clamp_min(0)), dim=1)

    def forward(self, observations, decode=True):
        features = self.features(observations)
        if self.motion:
            last = observations[:, 3]
            differences = torch.stack(((last - observations[:, 2]).abs().mean(dim=(1, 2)),
                                       (last - observations[:, 0]).abs().mean(dim=(1, 2))), dim=1)
            features = torch.cat((features, differences * 50), dim=1)
        raw = self.head(features)
        if self.mode_longitudinal:
            controls = torch.cat((torch.tanh(raw[:, :1]), raw[:, 1:4],
                                  torch.sigmoid(raw[:, 4:])), dim=1)
            return self.decode_mode(controls) if decode else controls
        if self.signed_longitudinal:
            controls = torch.tanh(raw)
            return self.decode_signed(controls) if decode else controls
        return torch.cat((torch.tanh(raw[:, :1]), torch.sigmoid(raw[:, 1:])), dim=1)

    @classmethod
    def from_checkpoint(cls, path):
        """Load a trainer checkpoint onto CPU without importing training code."""
        checkpoint = torch.load(path, map_location="cpu", weights_only=True)
        version = checkpoint.get("model")
        if version not in ("BCPolicy-v1", "BCPolicy-motion-v2", "BCPolicy-history8-v3",
                           "BCPolicy-signed-history8-v4", "BCPolicy-mode-history8-v5"):
            raise ValueError("Unsupported BC checkpoint format")
        history_frames = checkpoint.get("history_frames", 4)
        if history_frames != (8 if version in ("BCPolicy-history8-v3", "BCPolicy-signed-history8-v4",
                                               "BCPolicy-mode-history8-v5") else 4):
            raise ValueError("Checkpoint history length does not match its model format")
        policy = cls(motion=version == "BCPolicy-motion-v2", history_frames=history_frames,
                     signed_longitudinal=version == "BCPolicy-signed-history8-v4",
                     mode_longitudinal=version == "BCPolicy-mode-history8-v5")
        policy.load_state_dict(checkpoint["state_dict"])
        return policy.cpu().eval()

    def reset(self, observation):
        """Discard prior episode history and pad with the reset image."""
        if self.history_frames == 8:
            image = np.asarray(observation, dtype=np.float32)
            if image.shape != OBSERVATION_SHAPE or not np.isfinite(image).all():
                raise ValueError("Expected finite observation shaped (4, 84, 84)")
            self._history = deque((image[-1].copy() for _ in range(7)), maxlen=8)

    @torch.inference_mode()
    def act(self, observation):
        """Return a finite, legal float32 action for one official observation."""
        image = np.asarray(observation, dtype=np.float32)
        if image.shape != OBSERVATION_SHAPE or not np.isfinite(image).all():
            raise ValueError("Expected finite observation shaped (4, 84, 84)")
        if self.history_frames == 8:
            if self._history is None:
                self.reset(image)
            assert self._history is not None
            self._history.append(image[-1].copy())
            image = np.stack(tuple(self._history))
        action = self(torch.from_numpy(image).unsqueeze(0)).squeeze(0).cpu().numpy()
        return np.clip(action, [-1.0, 0.0, 0.0], [1.0, 1.0, 1.0]).astype(np.float32)
