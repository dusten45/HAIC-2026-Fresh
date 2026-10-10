"""Frozen linear retention gate using pixels and the agent's own past actions."""

import cv2
import numpy as np

from retry.clearance_agent import road_and_obstacles
from retry.schedule_agent import HazardScheduledAgent

FEATURES = ['current_gray_component_fraction5', 'current_road_fraction7',
            'birth_component_area_over30', 'birth_road_fraction7', 'age_over8',
            'two_hit_confirmation', 'past4_mean_abs_steer', 'past4_mean_brake',
            'estimated_current_pixelrow_over84', 'optical_flow_valid_fraction']


def patch_fraction(image, point, size, low, high):
    cx = int(np.rint(42 + 1.3608 * point[0]))
    cy = int(np.rint(63 - 1.701 * point[1]))
    h = size // 2
    a, b = max(0, cy - h), min(84, cy + h + 1)
    c, d = max(0, cx - h), min(84, cx + h + 1)
    if a >= b or c >= d:
        return -1.
    patch = image[a:b, c:d]
    return float(np.mean((patch > low) & (patch < high)))


def component_area(image, point):
    road = ((image > .32) & (image < .47)).astype(np.uint8)
    road[61:] = 0
    closed = cv2.morphologyEx(road, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    holes = ((closed != 0) & (road == 0) & (image >= .64) & (image <= .71)).astype(np.uint8)
    holes[61:] = 0
    count, _, stats, centers = cv2.connectedComponentsWithStats(holes, connectivity=8)
    observed = np.array([42 + 1.3608 * point[0], 63 - 1.701 * point[1]])
    distance, area = min((float(np.linalg.norm(centers[j] - observed)),
                         int(stats[j, cv2.CC_STAT_AREA])) for j in range(1, count))
    assert distance < 1e-6
    return area / 30.


def memory_features(image, position, age, birth_area, birth_road,
                    confirmed, past_actions, flow_features, flow_valid):
    past = np.asarray(past_actions, dtype=np.float32).reshape(-1, 3)
    return np.asarray([
        patch_fraction(image, position, 5, .64, .71),
        patch_fraction(image, position, 7, .32, .47), birth_area, birth_road,
        age / 8., float(confirmed),
        float(np.mean(np.abs(past[:, 0]))) if len(past) else 0.,
        float(np.mean(past[:, 2])) if len(past) else 0.,
        (63 - 1.701 * position[1]) / 84., flow_valid / max(1, flow_features)
    ], dtype=np.float64)


class LearnedMemoryAgent(HazardScheduledAgent):
    def __init__(self, speed_gain, speed_bias, speed_cap, lateral_fast,
                 lateral_safe, *, mean, scale, beta, threshold):
        super().__init__(speed_gain, speed_bias, speed_cap, lateral_fast, lateral_safe)
        self.feature_mean = np.asarray(mean, dtype=np.float64).copy()
        self.feature_scale = np.asarray(scale, dtype=np.float64).copy()
        self.feature_beta = np.asarray(beta, dtype=np.float64).copy()
        self.memory_threshold = float(threshold)
        assert self.feature_mean.shape == self.feature_scale.shape == (10,)
        assert self.feature_beta.shape == (11,) and np.all(self.feature_scale > 0)
        assert all(np.isfinite(v).all() for v in
                   (self.feature_mean, self.feature_scale, self.feature_beta))
        assert 0 <= self.memory_threshold <= 1

    def reset(self, observation):
        super().reset(observation)
        self.hazard_metadata = []
        self.past_actions = []
        self.memory_decisions = []

    def act(self, observation):
        action = np.asarray(super().act(observation), dtype=np.float32)
        self.past_actions.append(action.copy())
        self.past_actions = self.past_actions[-4:]
        return action

    def tracked_obstacles(self, image, speed):
        current = np.rint(image * 255).astype(np.uint8)
        transform = None
        flow_features = flow_valid = 0
        if self.previous_image is not None and self.hazards:
            mask = np.ones((84, 84), np.uint8) * 255
            mask[61:] = 0
            mask[50:61, 34:51] = 0
            points = cv2.goodFeaturesToTrack(self.previous_image, 100, 0.02, 4, mask=mask)
            if points is not None:
                flow_features = len(points)
            if points is not None and len(points) >= 4:
                following, status, _ = cv2.calcOpticalFlowPyrLK(self.previous_image, current,
                    points, None, winSize=(11, 11), maxLevel=2)
                valid = status[:, 0] != 0
                flow_valid = int(np.sum(valid))
                if np.sum(valid) >= 4:
                    candidate, _ = cv2.estimateAffinePartial2D(points[valid], following[valid], method=cv2.LMEDS)
                    if candidate is not None and np.isfinite(candidate).all() and 0.8 <= np.linalg.det(candidate[:, :2]) <= 1.2:
                        transform = candidate
        predicted, metadata = [], []
        for (x, y, radius, age), birth in zip(self.hazards, self.hazard_metadata):
            if transform is None:
                y -= speed * 0.08
            else:
                pixel = transform @ np.array([42 + 1.3608 * x, 63 - 1.701 * y, 1])
                x, y = (pixel[0] - 42) / 1.3608, (63 - pixel[1]) / 1.701
            if age < 8 and abs(x) <= 35 and -5 <= y <= 35:
                predicted.append((float(x), float(y), radius, age + 1))
                metadata.append(birth)
        for x, y, radius in road_and_obstacles(image)[1]:
            matches = [j for j, p in enumerate(predicted) if np.hypot(p[0] - x, p[1] - y) <= 2]
            confirmed = any(predicted[j][3] > 0 and
                            (metadata[j]['confirmed'] or predicted[j][3] == 1) for j in matches)
            keep = [j for j in range(len(predicted)) if j not in matches]
            predicted = [predicted[j] for j in keep]
            metadata = [metadata[j] for j in keep]
            predicted.append((x, y, radius, 0))
            metadata.append({'area': component_area(image, (x, y)),
                             'road': patch_fraction(image, (x, y), 7, .32, .47),
                             'confirmed': confirmed})
        outputs, births, decisions = [], [], []
        for p, birth in zip(predicted, metadata):
            keep = True
            if p[3] > 0 and p[1] > 0:
                features = memory_features(image, p[:2], p[3], birth['area'], birth['road'],
                    birth['confirmed'], self.past_actions, flow_features, flow_valid)
                logit = self.feature_beta[0] + ((features - self.feature_mean) /
                                               self.feature_scale) @ self.feature_beta[1:]
                score = float(1 / (1 + np.exp(-np.clip(logit, -30, 30))))
                keep = score >= self.memory_threshold
                decisions.append({'estimated_position': list(p[:2]), 'age': p[3],
                                  'score': score, 'keep': bool(keep)})
            if keep:
                outputs.append(p)
                births.append(birth)
        self.previous_image, self.hazards, self.hazard_metadata = current, outputs, births
        self.memory_decisions = decisions
        return [p[:3] for p in outputs]
