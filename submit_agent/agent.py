"""Observation-only local form of the 598 steering/speed-control architecture.

No global map, simulator state, stored episode commands or custom native code.
The local references and latent estimates are uncertain, not 598 certificates.
"""
import math
import numpy as np
import cv2


class Agent:
    def __init__(self):
        self.speed = 0.0
        self.yaw = 0.0
        self.previous_action = np.zeros(3, dtype=np.float32)
        self.diagnostics = {}

    def reset(self, observation):
        self.speed = 0.0
        self.yaw = 0.0
        self.previous_action[:] = 0.0
        self.diagnostics = {}

    def _estimate(self, image):
        # Public renderer: 1000x800 -> 84x84. White speed bar has width
        # Polygon rasterization includes its end pixel (26px width); the
        # road/HUD boundary at rows73..75 must not enter the speed integral.
        area = float(np.sum(image[76:83, 10:14]))
        observed_speed = max(0., area/.091728-2.5) if area>.02 else 0.
        # Red yaw bar: place30, width -20*yaw, height40, luminance .299.
        left = float(np.sum(image[75:81, 54:63]))
        right = float(np.sum(image[75:81, 63:72]))
        observed_yaw = (left - right) / 2.109744
        self.speed = .65 * min(110., max(0., observed_speed)) + .35 * self.speed
        self.yaw = .55 * min(5., max(-5., observed_yaw)) + .45 * self.yaw

    def _local_path(self, image):
        road = ((image > .36) & (image < .47)).astype(np.uint8)
        road[70:] = 0
        # The vehicle occludes the near road. This masks only its public,
        # camera-fixed footprint, not an inferred hidden road or obstacle.
        road[58:65, 39:45] = 1
        distance = cv2.distanceTransform(road, cv2.DIST_L2, 3)
        anchor = 42.0
        points = []
        widths = []
        for y in range(59, 5, -2):
            edges = np.diff(np.pad(road[y, 2:82], (1, 1)).astype(np.int16))
            starts = np.flatnonzero(edges == 1) + 2
            ends = np.flatnonzero(edges == -1) + 2
            valid = ends - starts >= 4
            starts, ends = starts[valid], ends[valid]
            if len(starts) == 0:
                break
            centers = (starts + ends - 1) * .5
            outside = np.maximum(starts - anchor, 0) + np.maximum(anchor - ends + 1, 0)
            cost = 3.0 * outside + .18 * np.abs(centers - anchor) - .05 * (ends-starts)
            choice = int(np.argmin(cost))
            if outside[choice] > 8:
                break
            x = float(centers[choice])
            # Prefer clearance within the associated road run; obstacle holes
            # split runs instead of being treated as traversable asphalt.
            lo, hi = int(starts[choice]), int(ends[choice])
            candidates = np.arange(lo, hi)
            c = distance[y, lo:hi] - .08*np.abs(candidates-x)
            x = .5*x + .5*float(candidates[int(np.argmax(c))])
            points.append(((x-42.)/1.3608, (63.-y)/1.701))
            widths.append((hi-lo)/1.3608)
            anchor = x
        return np.asarray(points, dtype=np.float64), widths

    def act(self, observation):
        obs = np.asarray(observation, dtype=np.float32)
        if obs.shape != (4, 84, 84) or not np.isfinite(obs).all():
            return np.array([0., 0., .3], dtype=np.float32)
        image = obs[-1]
        self._estimate(image)
        path, widths = self._local_path(image)
        if len(path) < 4:
            action = np.array([self.previous_action[0], 0., .3], dtype=np.float32)
            self.diagnostics = dict(speed=self.speed, yaw=self.yaw, path_points=len(path), lost=True)
        else:
            # Smooth sensor quantization; all geometry remains local and comes
            # from the current observation rather than a stored track.
            x = cv2.GaussianBlur(path[:, 0].reshape(1, -1), (5, 1), 1.0).ravel()
            path[:, 0] = x
            y = path[:, 1]
            dx = np.gradient(x, y)
            curvature = np.gradient(dx, y) / np.maximum((1+dx*dx)**1.5, 1e-6)
            support = np.maximum(np.abs(curvature), .001)
            support = np.maximum(support, cv2.dilate(support.reshape(1, -1), np.ones((1, 5), np.uint8)).ravel())
            cap = np.minimum(55., np.sqrt(40./support))
            arc = np.r_[0., np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
            # Stop within visible support. This replaces the unavailable global
            # backward envelope; the original 598 full-map claim is not reused.
            cap[-1] = min(cap[-1], 15.)
            squared = cap*cap
            for i in range(len(squared)-2, -1, -1):
                squared[i] = min(squared[i], squared[i+1]+2*45.*(arc[i+1]-arc[i]))
            target_speed = float(math.sqrt(max(0., squared[0])))
            lookahead = max(7., .3*self.speed)
            tx = float(np.interp(lookahead, y, x))
            ty = min(lookahead, float(y[-1]))
            kappa = 2*tx/max(tx*tx+ty*ty, 1.)
            steer = math.atan(3.24*kappa) + .025*(self.yaw+self.speed*kappa)
            steer = min(.4, max(-.4, steer))
            # Same generic source-pedal map used by 598 nominal. State/target
            # inputs here are observation estimates, not privileged truth.
            accel = min(35.0188778925416, max(-91.16873397261595, 2*(target_speed-self.speed)))
            gas = min(1., max(0., 29.249793766661764*max(accel,0.)*(self.speed+2.7)/80000.))
            brake = min(1., max(0., 29.249793766661764*max(-accel,0.)/(4*1.6*15/(.02*.54))))
            action = np.asarray([steer, gas, brake], dtype=np.float32)
            self.diagnostics = dict(speed=self.speed, yaw=self.yaw, path_points=len(path),
                target_speed=target_speed, lookahead=lookahead, visible_m=float(y[-1]), lost=False)
        self.previous_action = action.copy()
        return action
