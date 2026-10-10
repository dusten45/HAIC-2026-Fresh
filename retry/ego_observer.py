"""Small lawful-pixel features and a fixed supervised body-state observer.

No simulator, pose, speed truth, policy identity, or road identity is accepted by
the feature API. Flow is an image-interval quantity; outputs may be trained on
instantaneous states but do not acquire that meaning from optical flow alone.
"""
import cv2
import numpy as np

from retry.clearance_agent import road_and_obstacles

ROAD_ROWS = tuple(range(56, 23, -2))
PATCH_CENTERS = tuple((x, y) for y in (14, 34, 54) for x in (20, 42, 64))
CURRENT_NAMES = (
    'current_hud_integral',
    *(f'road_{r}_{k}' for r in ROAD_ROWS for k in ('center', 'width', 'present')),
)
HISTORY_NAMES = (
    *(f'interval_{i}_patch_{p}_{k}' for i in range(3) for p in range(9)
      for k in ('dx', 'dy', 'confidence')),
    *(f'interval_{i}_{k}' for i in range(3)
      for k in ('affine_x_bias', 'affine_x_x', 'affine_x_y',
                'affine_y_bias', 'affine_y_x', 'affine_y_y',
                'affine_residual', 'confidence_mean')),
    *(f'interval_{i}_available' for i in range(3)),
    *(f'past_action_{i}_{k}' for i in range(3) for k in ('steer', 'gas', 'brake')),
    *(f'past_action_{i}_available' for i in range(3)),
)
FEATURE_NAMES = CURRENT_NAMES + HISTORY_NAMES
FLOW_PARAMETERS = dict(pyr_scale=.5, levels=3, winsize=15, iterations=3,
                       poly_n=5, poly_sigma=1.1, flags=0)


def current_features(image):
    path, _ = road_and_obstacles(image)
    centers = {int(round(63 - 1.701*y)): x for x, y in path}
    road = ((image > .32) & (image < .47)).astype(np.uint8)
    road[61:] = 0
    closed = cv2.morphologyEx(road, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    values = [float(image[74:83, 9:14].sum()) / 45.]
    for row in ROAD_ROWS:
        center, width = centers.get(row), None
        if center is not None:
            edges = np.diff(np.r_[False, closed[row, 3:81] != 0, False].astype(np.int8))
            starts, ends = np.flatnonzero(edges == 1)+3, np.flatnonzero(edges == -1)+3
            pixel = 42 + 1.3608*center
            for left, right in zip(starts, ends):
                if left <= pixel < right:
                    width = right-left
                    break
        values.extend((0., 0., 0.) if width is None else (center/20., width/30., 1.))
    return np.asarray(values, dtype=np.float64)


def interval_features(first, second):
    """Return fixed pixel-flow summaries, without converting them into truth yaw."""
    first = np.rint(np.asarray(first)*255).astype(np.uint8)
    second = np.rint(np.asarray(second)*255).astype(np.uint8)
    flow = cv2.calcOpticalFlowFarneback(first, second, None, **FLOW_PARAMETERS)
    yy, xx = np.mgrid[:84, :84].astype(np.float32)
    following = cv2.remap(second, xx+flow[..., 0], yy+flow[..., 1],
                          cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
    error = np.abs(first.astype(float)-following.astype(float))
    patches = []
    for x, y in PATCH_CENTERS:
        box = np.s_[y-4:y+4, x-4:x+4]
        dx, dy = np.median(flow[box], axis=(0, 1)) / 20.
        texture = min(1., float(first[box].std()) / 64.)
        confidence = texture * np.exp(-float(error[box].mean()) / 32.)
        patches.append((dx, dy, confidence))
    patches = np.asarray(patches)
    coordinates = np.array([[1., (x-42)/22., (y-34)/20.] for x, y in PATCH_CENTERS])
    weight = np.sqrt(np.maximum(patches[:, 2], .001))
    coefficients = np.linalg.lstsq(coordinates*weight[:, None],
                                   patches[:, :2]*weight[:, None], rcond=None)[0]
    residual = float(np.sqrt(np.mean((coordinates@coefficients-patches[:, :2])**2)))
    summary = np.r_[coefficients.T.ravel(), residual, patches[:, 2].mean()]
    return patches.ravel(), summary


def extract_features(observation, executed_past_actions):
    """Use oldest-to-newest4 pixels and at most3 already executed actions.

    Callers must reset history at episode/gap boundaries. At reset, repeated
    pixels do not represent independent intervals; availability follows the
    number of executed actions supplied by the caller.
    """
    observation = np.asarray(observation)
    actions = np.asarray(executed_past_actions, dtype=np.float64)
    if actions.size == 0:
        actions = np.empty((0, 3), dtype=np.float64)
    if observation.shape != (4, 84, 84) or not np.isfinite(observation).all():
        raise ValueError('four finite grayscale84x84 frames required')
    if observation.min() < 0 or observation.max() > 1:
        raise ValueError('pixel values must be in[0,1]')
    if actions.ndim != 2 or actions.shape[1] != 3 or len(actions) > 3 or not np.isfinite(actions).all():
        raise ValueError('at most3 finite executed3D actions required')
    available = np.array([len(actions) >= 3-i for i in range(3)], dtype=np.float64)
    patches, summaries = [], []
    for i, present in enumerate(available):
        patch, summary = interval_features(observation[i], observation[i+1]) if present else (np.zeros(27), np.zeros(8))
        patches.extend(patch); summaries.extend(summary)
    padded = np.zeros((3, 3), dtype=np.float64)
    if len(actions):
        padded[-len(actions):] = actions / np.array([.4, .5, .5])
    result = np.r_[current_features(observation[-1]), patches, summaries,
                   available, padded.ravel(), available]
    assert len(result) == len(FEATURE_NAMES) == 172
    return result


class FixedRidgeObserver:
    """One alpha1 weighted ridge fit with TRAIN-only centering/scaling."""
    def fit(self, inputs, labels, sample_weight, shared_scaling=None):
        x, y, w = map(lambda a: np.asarray(a, dtype=np.float64), (inputs, labels, sample_weight))
        if y.shape != (len(x), 3) or w.shape != (len(x),) or not np.isfinite(x).all() or not np.isfinite(y).all():
            raise ValueError('finite inputs and three same-row targets required')
        if np.any(w <= 0) or not np.isclose(w.sum(), len(x)):
            raise ValueError('positive road-balanced weights must have mean1')
        if shared_scaling is None:
            self.mean = np.average(x, axis=0, weights=w)
            self.scale = np.maximum(np.sqrt(np.average((x-self.mean)**2, axis=0, weights=w)), 1e-6)
        else:
            self.mean, self.scale = [np.asarray(a, dtype=np.float64).copy() for a in shared_scaling]
        self.target_mean = np.average(y, axis=0, weights=w)
        z = (x-self.mean)/self.scale
        self.coefficients = np.linalg.solve(z.T@(w[:, None]*z)+np.eye(x.shape[1]),
                                            z.T@(w[:, None]*(y-self.target_mean)))
        return self

    def predict(self, inputs):
        return (np.asarray(inputs)-self.mean)/self.scale@self.coefficients + self.target_mean

    def save(self, path):
        np.savez_compressed(path, mean=self.mean, scale=self.scale,
                            target_mean=self.target_mean, coefficients=self.coefficients)
