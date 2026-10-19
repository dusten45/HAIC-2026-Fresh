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
        self.obstacles = []
        self.steer_estimate = 0.0
        self.stall = 0
        self.road_distance = None
        self.diagnostics = {}

    def reset(self, observation):
        self.speed = 0.0
        self.yaw = 0.0
        self.previous_action[:] = 0.0
        self.obstacles = []
        self.steer_estimate = 0.0
        self.stall = 0
        self.road_distance = None
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
        left_steer = float(np.sum(image[76:80, 32:42]))
        right_steer = float(np.sum(image[76:80, 42:52]))
        measured = min(.4,max(-.4,(right_steer-left_steer)/51.7734))
        self.steer_estimate = .6*measured+.4*self.steer_estimate

    def _local_path(self, image):
        road = ((image > .36) & (image < .47)).astype(np.uint8)
        road[70:] = 0
        # Orange obstacles have a public grayscale luminance near173/255.
        # Accept compact components surrounded by observed asphalt, rather
        # than interpreting grass or the unobserved part of a track as objects.
        bright = ((image > 164/255.) & (image < 176/255.)).astype(np.uint8)
        bright[68:] = 0
        count, labels, stats, centers = cv2.connectedComponentsWithStats(bright)
        detections = []
        for i in range(1, count):
            sx, sy, width, height, area = stats[i]
            if not (3 <= area <= 30 and min(width, height) >= 2 and max(width,height) <= 3*min(width,height)):
                continue
            cx, cy = centers[i]
            ix, iy = int(round(cx)), int(round(cy))
            patch = road[max(0,iy-4):min(68,iy+5), max(0,ix-4):min(84,ix+5)]
            if patch.size==0 or float(np.mean(patch)) < .42:
                continue
            detections.append(((cx-42.)/1.3608, (63.-cy)/1.701))
            # Recover only the asphalt centerline behind this *detected*
            # occlusion; its obstacle footprint is handled separately below.
            road[labels==i] = 1
        theta = .08*self.yaw
        c, sn = math.cos(theta), math.sin(theta)
        tracks = [[c*x+sn*y, -sn*x+c*y-.08*self.speed, age+1, side] for x,y,age,side in self.obstacles]
        for x,y in detections:
            distances = [(q[0]-x)**2+(q[1]-y)**2 for q in tracks]
            j = int(np.argmin(distances)) if distances else -1
            if j>=0 and distances[j] < 9.:
                tracks[j] = [x,y,0,tracks[j][3]]
            else:
                tracks.append([x,y,0,0])
        self.obstacles = [q for q in tracks if q[2]<=15 and -6.<q[1]<45. and abs(q[0])<40.][-8:]
        # The vehicle occludes the near road. This masks only its public,
        # camera-fixed footprint, not an inferred hidden road or obstacle.
        road[58:65, 39:45] = 1
        distance = cv2.distanceTransform(road, cv2.DIST_L2, 3)
        self.road_distance = distance
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

    def _shield(self, desired, path, arc, target_speed):
        """Bounded local estimated-state rollout, not a true-state certificate."""
        commands = np.unique(np.r_[np.linspace(-.4,.4,17),desired])
        n = len(commands)
        x=np.zeros(n);y=np.zeros(n);heading=np.zeros(n)
        yaw=np.full(n,-self.yaw);joint=np.full(n,self.steer_estimate)
        clearance=np.full(n,10.);tracking=np.zeros(n)
        speed=self.speed
        for tick in range(28):
            distance=(x[:,None]-path[None,:,0])**2+(y[:,None]-path[None,:,1])**2
            nearest=np.argmin(distance,axis=1)
            tracking += np.min(distance,axis=1)
            if tick<4:
                use=commands
            else:
                station=arc[nearest]+max(7.,.3*speed)
                tx=np.interp(station,arc,path[:,0])-x
                ty=np.interp(station,arc,path[:,1])-y
                lateral=np.cos(heading)*tx-np.sin(heading)*ty
                use=np.clip(np.arctan(3.24*2*lateral/np.maximum(tx*tx+ty*ty,1.)),-.4,.4)
            joint += np.clip(50*(use-joint),-3.,3.)*.02
            desired_yaw=np.clip(speed*np.tan(joint)/3.24,-60/max(speed,1.),60/max(speed,1.))
            yaw += (desired_yaw-yaw)/.12*.02
            heading += yaw*.02
            speed=max(0.,speed+.02*min(35.,max(-30.,2*(target_speed-speed))))
            x += speed*np.sin(heading)*.02;y += speed*np.cos(heading)*.02
            for ox,oy,age,side in self.obstacles:
                dx=ox-x;dy=oy-y
                u=dx*np.cos(heading)-dy*np.sin(heading)
                v=dx*np.sin(heading)+dy*np.cos(heading)
                gap=np.hypot(np.maximum(np.abs(u)-1.3,0.),np.maximum(np.abs(v)-2.5,0.))-1.6
                clearance=np.minimum(clearance,gap)
            # Current vehicle pixels occlude the near road. Apply the raster
            # road check once a predicted center enters visible forward support.
            ix=np.rint(42+x*1.3608).astype(np.int32)
            iy=np.rint(63-y*1.701).astype(np.int32)
            visible=(y>3.)&(iy>=1)&(iy<68)&(ix>=1)&(ix<83)
            road=np.full(n,2.)
            road[visible]=self.road_distance[iy[visible],ix[visible]]/1.701-1.6
            road[(y>3.)&~visible]=-2.
            clearance=np.minimum(clearance,road)
        cost=tracking/28+3*(commands-desired)**2+.5*(commands-float(self.previous_action[0]))**2
        safe=clearance>=0.
        score=np.where(safe,cost,1e4+1e3*np.maximum(-clearance,0.)+cost)
        j=int(np.argmin(score))
        return float(commands[j]),bool(safe[j]),float(clearance[j])

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
            base_path = path.copy()
            delta = np.diff(base_path, axis=0)
            ds = np.linalg.norm(delta, axis=1)
            base_arc = np.r_[0., np.cumsum(ds)]
            tangent = np.gradient(base_path, base_arc, axis=0)
            tangent /= np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-6)
            normal = np.column_stack((tangent[:,1],-tangent[:,0]))
            # Observation-derived version of 598's smooth obstacle offset.
            # The support is local; no future map or episode-specific tape.
            for obstacle in self.obstacles:
                ox, oy, age, side = obstacle
                obj = np.asarray([ox,oy])
                fraction = np.clip(np.sum((obj-base_path[:-1])*delta,axis=1)/np.maximum(ds*ds,1e-6),0.,1.)
                projected = base_path[:-1]+fraction[:,None]*delta
                j = int(np.argmin(np.linalg.norm(projected-obj,axis=1)))
                n = np.asarray([delta[j,1],-delta[j,0]])/max(ds[j],1e-6)
                lateral = float(np.dot(obj-projected[j],n))
                if side==0:
                    side = -1 if lateral>=-.7 else 1
                    obstacle[3] = side
                amplitude = side*max(0.,3.8-abs(lateral))
                station = base_arc[j]+fraction[j]*ds[j]
                path += (amplitude*np.exp(-.5*((base_arc-station)/16.)**2))[:,None]*normal
            arc = np.r_[0.,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))]
            arc = np.maximum.accumulate(arc + np.arange(len(arc))*1e-7)
            tangent = np.gradient(path,arc,axis=0)
            second = np.gradient(tangent,arc,axis=0)
            curvature = (tangent[:,0]*second[:,1]-tangent[:,1]*second[:,0])/np.maximum(np.linalg.norm(tangent,axis=1)**3,1e-6)
            support = np.maximum(np.abs(curvature), .001)
            support = np.maximum(support, cv2.dilate(support.reshape(1, -1), np.ones((1, 5), np.uint8)).ravel())
            cap = np.minimum(55., np.sqrt(40./support))
            # Stop within visible support. This replaces the unavailable global
            # backward envelope; the original 598 full-map claim is not reused.
            cap[-1] = min(cap[-1], 15.)
            squared = cap*cap
            for i in range(len(squared)-2, -1, -1):
                squared[i] = min(squared[i], squared[i+1]+2*45.*(arc[i+1]-arc[i]))
            target_speed = float(math.sqrt(max(0., squared[0])))
            lookahead = max(7., .3*self.speed)
            target_station = max(0.,lookahead-float(np.linalg.norm(path[0])))
            tx = float(np.interp(target_station,arc,path[:,0]))
            ty = float(np.interp(target_station,arc,path[:,1]))
            kappa = 2*tx/max(tx*tx+ty*ty, 1.)
            steer = math.atan(3.24*kappa)
            steer = min(.4, max(-.4, steer))
            steer, admitted, predicted_margin = self._shield(steer,path,arc,target_speed)
            # Same generic source-pedal map used by 598 nominal. State/target
            # inputs here are observation estimates, not privileged truth.
            accel = min(35.0188778925416, max(-91.16873397261595, 2*(target_speed-self.speed)))
            gas = min(1., max(0., 29.249793766661764*max(accel,0.)*(self.speed+2.7)/80000.))
            brake = min(1., max(0., 29.249793766661764*max(-accel,0.)/(4*1.6*15/(.02*.54))))
            if not admitted:
                gas=0.;brake=max(brake,.25)
            self.stall = self.stall+1 if self.speed<4. and self.previous_action[1]>.025 else 0
            if self.stall>15:
                near=[q for q in self.obstacles if -3.<q[1]<8.]
                if near:
                    closest=min(near,key=lambda q:q[0]*q[0]+q[1]*q[1])
                    steer=-math.copysign(.4,closest[0] if abs(closest[0])>.2 else 1.)
                gas=.7;brake=0.
            action = np.asarray([steer, gas, brake], dtype=np.float32)
            self.diagnostics = dict(speed=self.speed, yaw=self.yaw, path_points=len(path),
                target_speed=target_speed, lookahead=lookahead, visible_m=float(y[-1]),
                obstacle_tracks=len(self.obstacles), local_model_admitted=admitted,
                estimated_margin=predicted_margin, stall_count=self.stall, lost=False)
        self.previous_action = action.copy()
        return action
