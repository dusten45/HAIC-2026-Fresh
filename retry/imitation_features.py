"""Pixel perception and own history for an offline imitation experiment.

Call observe once per decision, then record_action after executing that action.
No teacher routing, controller, target or action computation enters these features.
"""
import cv2
import numpy as np

from retry.clearance_agent import road_and_obstacles
from retry.temporal_agent import TemporalRouteAgent


ROWS = tuple(range(56, 23, -2))
FEATURE_NAMES = (
    "pixel_speed", "previous_steer", "previous_gas", "previous_brake",
    *(f"road_{row}_{field}" for row in ROWS for field in ("center_x", "width", "present")),
    *(f"hazard_{i}_{field}" for i in range(8)
      for field in ("x", "y", "radius", "age", "present")),
)


class PixelMemoryFeatures:
    feature_names = FEATURE_NAMES

    def __init__(self, speed_gain, speed_bias):
        self.speed_gain, self.speed_bias = float(speed_gain), float(speed_bias)
        self.reset(None)

    def reset(self, observation):
        self.previous_image, self.hazards = None, []
        self.previous_action = np.zeros(3, dtype=np.float32)
        cv2.setRNGSeed(0)

    def record_action(self, actual_action):
        action = np.array(actual_action, dtype=np.float32, copy=True)
        if action.shape != (3,) or not np.isfinite(action).all():
            raise ValueError("one finite executed action required")
        self.previous_action = action

    def observe(self, observation):
        observation = np.asarray(observation)
        if observation.shape != (4, 84, 84):
            raise ValueError("four grayscale 84x84 frames required")
        image = observation[-1]
        speed = max(0., self.speed_gain * float(image[74:83, 9:14].sum()) + self.speed_bias)
        # Only the unbound perception/memory method is reused, once per frame.
        TemporalRouteAgent.tracked_obstacles(self, image, speed)
        path, _ = road_and_obstacles(image)
        centers = {int(round(63 - 1.701 * y)): x for x, y in path}
        road = ((image > .32) & (image < .47)).astype(np.uint8)
        road[61:] = 0
        closed = cv2.morphologyEx(road, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
        features = [speed / 30, *(self.previous_action / np.array([.4, .5, .5]))]
        for row in ROWS:
            center, width = centers.get(row), None
            if center is not None:
                edges = np.diff(np.r_[False, closed[row, 3:81] != 0, False].astype(np.int8))
                starts, ends = np.flatnonzero(edges == 1) + 3, np.flatnonzero(edges == -1) + 3
                pixel = 42 + 1.3608 * center
                for start, end in zip(starts, ends):
                    if start <= pixel < end:
                        width = end - start
                        break
            features.extend((0., 0., 0.) if width is None else (center / 20, width / 30, 1.))
        hazards = sorted(self.hazards, key=lambda p: (np.hypot(p[0], p[1]), p[1], p[0], p[3]))[:8]
        for x, y, radius, age in hazards:
            features.extend((x / 35, y / 35, radius / 3, age / 8, 1.))
        features.extend([0.] * (5 * (8 - len(hazards))))
        return np.asarray(features, dtype=np.float64)
