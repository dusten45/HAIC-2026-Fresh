"""Retain recently visible hazards through short near-car image occlusions."""

import cv2
import numpy as np

from retry.clearance_agent import road_and_obstacles
from retry.route_agent import RouteAgent, route_target, safe_route


class TemporalRouteAgent(RouteAgent):
    def reset(self, observation):
        super().reset(observation)
        self.previous_image = None
        self.hazards = []
        cv2.setRNGSeed(0)

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
        for x, y, radius, age in self.hazards:
            if transform is None:
                y -= speed * 0.08
            else:
                pixel = transform @ np.array([42 + 1.3608 * x, 63 - 1.701 * y, 1])
                x, y = (pixel[0] - 42) / 1.3608, (63 - pixel[1]) / 1.701
            if age < 8 and abs(x) <= 35 and -5 <= y <= 35:
                predicted.append((float(x), float(y), radius, age + 1))
        for x, y, radius in road_and_obstacles(image)[1]:
            predicted = [p for p in predicted if np.hypot(p[0] - x, p[1] - y) > 2]
            predicted.append((x, y, radius, 0))
        self.previous_image, self.hazards = current, predicted
        return [p[:3] for p in predicted]

    def act(self, observation):
        image = observation[-1]
        speed = max(0.0, self.speed_gain * float(image[74:83, 9:14].sum()) + self.speed_bias)
        obstacles = self.tracked_obstacles(image, speed)
        target = route_target(safe_route(image, obstacles_override=obstacles), speed)
        if target is None:
            return self.controller.action(None, speed)
        return self.controller.action_target(float(target[0]), float(target[1]), speed)
