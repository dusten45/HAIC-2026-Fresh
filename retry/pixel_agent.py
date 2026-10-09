"""Small CPU policy using only the supplied grayscale observation."""

import numpy as np


class StraightAgent:
    def reset(self, observation):
        pass

    def act(self, observation):
        return np.array([0.0, 1.0, 0.0], dtype=np.float32)


class PixelAgent:
    def __init__(self, adaptive=False):
        self.adaptive = adaptive
        self.previous_steer = 0.0

    def reset(self, observation):
        self.previous_steer = 0.0

    def road_centers(self, image):
        # Camera follows the car; center is approximately (42, 63).
        # Associate gray road runs upwards from the near road, excluding the HUD.
        gray_road = (image > 0.32) & (image < 0.47)
        centers = []
        anchor = 42.0
        for y in range(56, 23, -2):
            row = gray_road[y, 3:81]
            edges = np.diff(np.concatenate(([False], row, [False])).astype(np.int8))
            starts = np.flatnonzero(edges == 1) + 3
            ends = np.flatnonzero(edges == -1) + 3
            widths = ends - starts
            keep = widths >= 4
            if not np.any(keep):
                continue
            starts, ends = starts[keep], ends[keep]
            xs = (starts + ends - 1) / 2.0
            # Prefer a run containing the previous center over a remote crossing.
            distances = np.maximum(starts - anchor, 0) + np.maximum(anchor - ends, 0)
            choice = int(np.argmin(distances + 0.08 * np.abs(xs - anchor)))
            if distances[choice] > 16:
                break
            anchor = float(xs[choice])
            centers.append((y, anchor))
        return centers

    def act(self, observation):
        image = observation[-1]
        centers = self.road_centers(image)
        if centers:
            rows, xs = np.array(centers).T
            near = float(xs[np.argmin(np.abs(rows - 52))])
            far = float(xs[np.argmin(np.abs(rows - 36))])
            error = (far - 42.0) / 25.0
            steer = float(np.clip(1.1 * error, -1.0, 1.0))
            gas, brake = 0.22, 0.0
            if self.adaptive:
                curvature = abs(far - near) / 25.0
                # Speed bar is public pixels. Its resolution is coarse at 84x84.
                speed_bar = float(np.sum(image[74:82, 10:13] > 0.75)) / 3.0
                target = 1.4 if curvature > 0.35 else 2.3
                steer = float(np.clip(0.85 * error + 0.35 * (near - 42) / 18, -1, 1))
                gas = 0.32 if speed_bar < target else 0.0
                brake = 0.15 if speed_bar > target + 1.2 else 0.0
        else:
            steer, gas, brake = self.previous_steer, 0.08, 0.0
        steer = 0.65 * steer + 0.35 * self.previous_steer
        self.previous_steer = steer
        return np.array([steer, gas, brake], dtype=np.float32)
