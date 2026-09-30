"""Small observation-only behavior cloning policy for CPU inference."""

from collections import deque

import numpy as np
import torch
from torch import nn
from bc.contracts import OBSERVATION_SHAPE


class BCPolicy(nn.Module):
    """Maps four or eight normalized grayscale frames to [steer, gas, brake]."""

    def __init__(self, motion=False, history_frames=4):
        super().__init__()
        if history_frames not in (4, 8):
            raise ValueError("history_frames must be 4 or 8")
        if history_frames == 8 and motion:
            raise ValueError("history8 cannot be combined with motion features")
        self.motion = motion
        self.history_frames = history_frames
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

    def forward(self, observations):
        features = self.features(observations)
        if self.motion:
            last = observations[:, 3]
            differences = torch.stack(((last - observations[:, 2]).abs().mean(dim=(1, 2)),
                                       (last - observations[:, 0]).abs().mean(dim=(1, 2))), dim=1)
            features = torch.cat((features, differences * 50), dim=1)
        raw = self.head(features)
        return torch.cat((torch.tanh(raw[:, :1]), torch.sigmoid(raw[:, 1:])), dim=1)

    @classmethod
    def from_checkpoint(cls, path):
        """Load a trainer checkpoint onto CPU without importing training code."""
        checkpoint = torch.load(path, map_location="cpu", weights_only=True)
        version = checkpoint.get("model")
        if version not in ("BCPolicy-v1", "BCPolicy-motion-v2", "BCPolicy-history8-v3"):
            raise ValueError("Unsupported BC checkpoint format")
        history_frames = checkpoint.get("history_frames", 4)
        if history_frames != (8 if version == "BCPolicy-history8-v3" else 4):
            raise ValueError("Checkpoint history length does not match its model format")
        policy = cls(motion=version == "BCPolicy-motion-v2", history_frames=history_frames)
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
