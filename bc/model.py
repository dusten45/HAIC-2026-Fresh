"""Small observation-only behavior cloning policy for CPU inference."""

from pathlib import Path

import numpy as np
import torch
from torch import nn


class BCPolicy(nn.Module):
    """Maps four normalized grayscale frames to [steer, gas, brake]."""

    def __init__(self, motion=False):
        super().__init__()
        self.motion = motion
        self.features = nn.Sequential(
            nn.Conv2d(4, 8, kernel_size=8, stride=4), nn.ReLU(),
            nn.Conv2d(8, 16, kernel_size=4, stride=2), nn.ReLU(),
            nn.Conv2d(16, 16, kernel_size=3), nn.ReLU(),
            nn.Flatten(),
        )
        self.head = nn.Sequential(nn.Linear(16 * 7 * 7 + (2 if motion else 0), 32),
                                  nn.ReLU(), nn.Linear(32, 3))

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
        checkpoint = torch.load(Path(path), map_location="cpu", weights_only=True)
        version = checkpoint.get("model")
        if version not in ("BCPolicy-v1", "BCPolicy-motion-v2"):
            raise ValueError("Unsupported BC checkpoint format")
        policy = cls(motion=version == "BCPolicy-motion-v2")
        policy.load_state_dict(checkpoint["state_dict"])
        return policy.cpu().eval()

    @torch.inference_mode()
    def act(self, observation):
        """Return a finite, legal float32 action for one official observation."""
        image = np.asarray(observation, dtype=np.float32)
        if image.shape != (4, 84, 84) or not np.isfinite(image).all():
            raise ValueError("Expected finite observation shaped (4, 84, 84)")
        action = self(torch.from_numpy(image).unsqueeze(0)).squeeze(0).cpu().numpy()
        return np.clip(action, [-1.0, 0.0, 0.0], [1.0, 1.0, 1.0]).astype(np.float32)
