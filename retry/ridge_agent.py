"""Road center from a two-dimensional distance ridge; control stays frozen."""

import cv2
import numpy as np

from retry.arc_agent import ArcAgent, arc_target
from retry.clearance_agent import road_and_obstacles


def ridge_path(image):
    road = ((image > 0.32) & (image < 0.47)).astype(np.uint8)
    road[61:] = 0
    road = cv2.morphologyEx(road, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    distance = cv2.distanceTransform(road, cv2.DIST_L2, 5)
    anchor, path = 42.0, []
    for row in range(56, 23, -2):
        d = distance[row]
        xs = np.flatnonzero((d[3:81] >= d[2:80]) & (d[3:81] >= d[4:82]) & (d[3:81] >= 2)) + 3
        if not len(xs):
            continue
        choice = int(np.argmin(0.25 * np.abs(xs - anchor) - d[xs]))
        x = float(xs[choice])
        if abs(x - anchor) > 16:
            break
        anchor = x
        path.append(((x - 42) / 1.3608, (63 - row) / 1.701))
    return path


class RidgeAgent(ArcAgent):
    def act(self, observation):
        path = ridge_path(observation[-1])
        _, obstacles = road_and_obstacles(observation[-1])
        integral = float(observation[-1, 74:83, 9:14].sum())
        speed = max(0.0, self.speed_gain * integral + self.speed_bias)
        target = arc_target(path, speed, obstacles)
        if target is None:
            return self.controller.action(None, speed)
        return self.controller.action_target(float(target[0]), float(target[1]), speed)
