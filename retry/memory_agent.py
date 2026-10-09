"""Pixel-only memory contrasts with the frozen routing and speed law."""

import cv2
import numpy as np

from retry.clearance_agent import road_and_obstacles
from retry.schedule_agent import HazardScheduledAgent


class FreshDetectionAgent(HazardScheduledAgent):
    def tracked_obstacles(self, image, speed):
        self.hazards = []
        return road_and_obstacles(image)[1]


class MinimalMemoryAgent(HazardScheduledAgent):
    """Use fresh detections immediately; persist only a twice-seen track.

    Association radius, motion estimation, lifetime, routing and control stay
    inherited. Confirmation is a Boolean, not a fitted confidence threshold.
    """

    def reset(self, observation):
        super().reset(observation)
        self.hazard_confirmed = []

    def tracked_obstacles(self, image, speed):
        current = np.rint(image * 255).astype(np.uint8)
        transform = None
        if self.previous_image is not None and self.hazards:
            mask = np.ones((84, 84), np.uint8) * 255
            mask[61:] = 0
            mask[50:61, 34:51] = 0
            points = cv2.goodFeaturesToTrack(self.previous_image, 100, 0.02, 4, mask=mask)
            if points is not None and len(points) >= 4:
                following, status, _ = cv2.calcOpticalFlowPyrLK(self.previous_image, current, points,
                    None, winSize=(11, 11), maxLevel=2)
                valid = status[:, 0] != 0
                if np.sum(valid) >= 4:
                    candidate, _ = cv2.estimateAffinePartial2D(points[valid], following[valid], method=cv2.LMEDS)
                    if candidate is not None and np.isfinite(candidate).all() and 0.8 <= np.linalg.det(candidate[:, :2]) <= 1.2:
                        transform = candidate
        predicted = []
        for (x, y, radius, age), confirmed in zip(self.hazards, self.hazard_confirmed):
            if transform is None:
                y -= speed * 0.08
            else:
                pixel = transform @ np.array([42 + 1.3608 * x, 63 - 1.701 * y, 1])
                x, y = (pixel[0] - 42) / 1.3608, (63 - pixel[1]) / 1.701
            if age < 8 and abs(x) <= 35 and -5 <= y <= 35:
                # Tentative previous-frame detections participate in confirmation
                # but do not survive a missing fresh observation.
                predicted.append((float(x), float(y), radius, age + 1, confirmed, age == 0))
        outputs = [p for p in predicted if p[4]]
        for x, y, radius in road_and_obstacles(image)[1]:
            matches = [p for p in predicted if np.hypot(p[0] - x, p[1] - y) <= 2]
            confirmed = any(p[4] or p[5] for p in matches)
            outputs = [p for p in outputs if np.hypot(p[0] - x, p[1] - y) > 2]
            predicted = [p for p in predicted if np.hypot(p[0] - x, p[1] - y) > 2]
            outputs.append((x, y, radius, 0, confirmed, False))
        self.previous_image = current
        self.hazards = [p[:4] for p in outputs]
        self.hazard_confirmed = [p[4] for p in outputs]
        return [p[:3] for p in outputs]
