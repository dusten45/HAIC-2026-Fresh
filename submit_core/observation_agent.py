"""Observation-only experimental input adapter for the actual runtime598 core.

All physical states/history below are estimates or explicit mechanical priors.
The returned runtime admission is NOT a true-state safety certificate. No global
map, seed, stored prefix command, tracker or evaluation data is loaded here.
"""
import math
import numpy as np
import cv2
import runtime598 as core

# Pixel centres after public 1000x800 -> 96x96 -> 84x84 rendering,
# including the vertical flip about WINDOW_H-1. No fitted camera offset.
IMAGE_ORIGIN_X=(500.+.5)*84./1000.-.5
IMAGE_ORIGIN_Y=(799.-200.+.5)*84./800.-.5

class _TickCounter(list):
    def __init__(self):super().__init__([0]);self.limit=50000
    def __setitem__(self,index,value):
        if value>self.limit:raise RuntimeError('ADAPTER_MODEL_TICK_BUDGET')
        super().__setitem__(index,value)


def _mass_properties(poly,density):
    p=np.asarray(poly,np.float64);q=np.roll(p,-1,axis=0)
    cross=p[:,0]*q[:,1]-q[:,0]*p[:,1]
    area=float(np.sum(cross)/2.)
    center=np.sum((p+q)*cross[:,None],axis=0)/(6*area)
    inertia=abs(float(np.sum(cross*(np.sum(p*p,axis=1)+np.sum(p*q,axis=1)+np.sum(q*q,axis=1)))/12.))*density
    return abs(area)*density,center,inertia


class Agent:
    def __init__(self):
        # Generic analytic public vehicle dimensions/densities, not a snapshot.
        hull=[_mass_properties(np.asarray(p)*core.SIZE,1.) for p in (core.HULL_POLY1,core.HULL_POLY2,core.HULL_POLY3,core.HULL_POLY4)]
        self.hull_mass=sum(m for m,c,i in hull)
        self.hull_com=sum(m*c for m,c,i in hull)/self.hull_mass
        wheel_poly=[(-.28,-.54),(.28,-.54),(.28,.54),(-.28,.54)]
        wm,wc,wi=_mass_properties(wheel_poly,.1)
        self.wheel_inertia=wi
        wheel_positions=np.asarray(core.WHEELPOS)*core.SIZE
        self.mass=self.hull_mass+4*wm
        self.com=(self.hull_mass*self.hull_com+wm*np.sum(wheel_positions,axis=0))/self.mass
        self.levers=wheel_positions-self.com
        self.inertia=sum(i for m,c,i in hull)+sum(wi+wm*float(p@p) for p in wheel_positions)-self.mass*float(self.com@self.com)
        self.counter=_TickCounter()
        self.calls=0
        self.diagnostics={}
        self.reset(None)

    def reset(self,observation):
        # Resource counter intentionally survives reset; episode state does not.
        self.speed=0.;self.yaw=0.;self.joint=0.;self.previous_joint=0.
        self.distance=0.;self.previous_action=np.zeros(3,np.float32)
        self.predicted_wheels=None;self.predicted_hull_speed=None;self.calls=0
        self.predicted_hull_velocity_body=None
        self.history=[0,0];self.last_root=None;self.last_path=None
        self.grip_prior=1.;self.engine_prior=1.;self.steering_prior=1.
        self.uncertainty={};self.diagnostics={}

    def _state_estimates(self,obs):
        image=obs[-1]
        area=float(np.sum(image[76:83,10:14]))
        speed=max(0.,area/.091728-2.5) if area>.02 else 0.
        yaw=(float(np.sum(image[75:81,54:63]))-float(np.sum(image[75:81,63:72])))/2.109744
        # Include the full raster support of the public green indicator.
        joint=(float(np.sum(image[75:81,32:42]))-float(np.sum(image[75:81,42:52])))/51.7734
        self.previous_joint=self.joint;self.joint=float(np.clip(joint,-.4,.4))
        # Missing optical flow is not evidence of zero side slip in a turn.
        lateral_speed=(0. if self.predicted_hull_velocity_body is None else
                       float(np.clip(self.predicted_hull_velocity_body[0],-10.,10.)))
        flow_confidence=0.
        a=np.rint(obs[-2]*255).astype(np.uint8);b=np.rint(image*255).astype(np.uint8)
        mask=np.zeros((84,84),np.uint8);mask[8:69,2:82]=255;mask[54:69,35:49]=0
        points=cv2.goodFeaturesToTrack(a,64,.02,4,mask=mask)
        if points is not None and len(points)>=8:
            next_points,status,errors=cv2.calcOpticalFlowPyrLK(a,b,points,None,winSize=(15,15),maxLevel=2)
            if next_points is not None:
                valid=status.ravel().astype(bool)&(errors.ravel()<20.)
                if np.sum(valid)>=8:
                    p=points[valid,0,:].astype(np.float64);q=next_points[valid,0,:].astype(np.float64)
                    for z in (p,q):z[:,0]=(z[:,0]-IMAGE_ORIGIN_X)/1.3608;z[:,1]=(IMAGE_ORIGIN_Y-z[:,1])/1.701
                    affine,inliers=cv2.estimateAffinePartial2D(p,q,method=cv2.RANSAC,ransacReprojThreshold=.4,maxIters=100,confidence=.95)
                    if affine is not None and inliers is not None:
                        scale=math.hypot(affine[0,0],affine[1,0]);flow_confidence=float(np.mean(inliers))
                        if .97<scale<1.03 and flow_confidence>.6:
                            visual_speed=math.hypot(float(affine[0,2]),float(affine[1,2]))/.08
                            visual_yaw=math.atan2(affine[0,1],affine[0,0])/.08
                            lateral_speed=float(np.clip(-affine[0,2]/.08,-10.,10.))
                            if abs(visual_speed-speed)<8.:speed=.7*speed+.3*max(0.,visual_speed)
                            if abs(visual_yaw-yaw)<1.:yaw=.7*yaw+.3*visual_yaw
        if self.predicted_hull_speed is not None and self.predicted_hull_speed-speed>8.:
            # A possible impact or loss of traction, not observed damage truth.
            self.grip_prior=.6;self.engine_prior=.8;self.steering_prior=.8
        self.speed=float(np.clip(speed,0.,100.));self.yaw=float(np.clip(yaw,-5.,5.))
        self.distance+=self.speed*.08 if self.last_root is not None else 0.
        self.uncertainty=dict(speed_interval_m_s=[max(0.,self.speed-3.),self.speed+3.],
            intervals_are_unvalidated_engineering_priors=True,
            visual_motion_confidence=flow_confidence,lateral_speed_assumption='visual estimate or own-action prediction; initial zero prior',
            wheel_contact_frictions_and_clip_history='model-estimated, NOT observed',
            damage='not observed; multiplier priors may reduce after motion residual',
            wheel_omega=('rolling-speed initial prior' if self.predicted_wheels is None else
                         'own-action model propagation; wheel slip error unresolved'))
        return lateral_speed

    def _map(self,image):
        asphalt=((image>.36)&(image<.47)).astype(np.uint8)
        bright=((image>164/255.)&(image<176/255.)).astype(np.uint8);bright[69:]=0
        count,labels,stats,centers=cv2.connectedComponentsWithStats(bright)
        obstacles=[]
        for i in range(1,count):
            x,y,w,h,area=stats[i];cx,cy=centers[i];ix,iy=int(round(cx)),int(round(cy))
            patch=asphalt[max(0,iy-4):min(69,iy+5),max(0,ix-4):min(84,ix+5)]
            if 3<=area<=30 and min(w,h)>=2 and max(w,h)<=3*min(w,h) and patch.size and np.mean(patch)>.42:
                obstacles.append((((cx-IMAGE_ORIGIN_X)/1.3608,(IMAGE_ORIGIN_Y-cy)/1.701),1.6))
                asphalt[labels==i]=1
        rows=[];anchor=IMAGE_ORIGIN_X
        for y in range(69,4,-2):
            edges=np.diff(np.pad(asphalt[y,1:83],(1,1)).astype(np.int16));starts=np.flatnonzero(edges==1)+1;ends=np.flatnonzero(edges==-1)+1
            good=ends-starts>=3;starts=starts[good];ends=ends[good]
            if not len(starts):
                if len(rows)<3:continue
                break
            # Bridge the known vehicle occlusion between visible flanking road
            # runs. This is an interpolation assumption, not seen hidden asphalt.
            if 55<=y<=69:
                near=(starts<50)&(ends>34)
                if np.sum(near)>1:
                    starts=np.asarray([starts[near].min()]);ends=np.asarray([ends[near].max()])
            center=(starts+ends-1)*.5
            outside=np.maximum(starts-anchor,0)+np.maximum(anchor-ends,0)
            j=int(np.argmin(3*outside+.1*np.abs(center-anchor)))
            if outside[j]>8:
                if len(rows)<3:continue
                break
            left=(float(starts[j])-IMAGE_ORIGIN_X)/1.3608+.35
            right=(float(ends[j]-1)-IMAGE_ORIGIN_X)/1.3608-.35
            if right-left<2.5:break
            anchor=float(center[j]);rows.append((left,right,(IMAGE_ORIGIN_Y-y)/1.701))
        if len(rows)<8:raise RuntimeError('OBSERVED_ROAD_SUPPORT_INSUFFICIENT')
        left=[(a,y) for a,b,y in rows];right=[(b,y) for a,b,y in rows]
        roads=[((left[i],right[i],right[i+1],left[i+1]),self.grip_prior) for i in range(len(rows)-1)]
        boundary=list(zip(left,left[1:]))+list(zip(right,right[1:]))+[(left[0],right[0]),(left[-1],right[-1])]
        points=np.asarray([((a+b)*.5,y) for a,b,y in rows],np.float64)
        points[:,0]=cv2.GaussianBlur(points[:,0].reshape(1,-1),(5,1),1.).ravel()
        arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
        tangent=np.gradient(points,arc,axis=0);normal=np.column_stack((tangent[:,1],-tangent[:,0]));normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-6)
        for center,radius in obstacles:
            j=int(np.argmin(np.linalg.norm(points-np.asarray(center),axis=1)))
            signed=float(np.dot(np.asarray(center)-points[j],normal[j]))
            amplitude=-math.copysign(max(0.,3.8-abs(signed)),signed if signed else 1.)
            points+=(amplitude*np.exp(-.5*((arc-arc[j])/16.)**2))[:,None]*normal
        arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
        tangent=np.gradient(points,arc,axis=0);second=np.gradient(tangent,arc,axis=0)
        curvature=np.abs(tangent[:,0]*second[:,1]-tangent[:,1]*second[:,0])/np.maximum(np.linalg.norm(tangent,axis=1)**3,1e-6)
        current=float(arc[np.argmin(np.linalg.norm(points-self.com,axis=1))])
        def reference(budget,max_speed):
            q=np.minimum(max_speed**2,budget/np.maximum(curvature,1e-6));q[-1]=0.
            for i in range(len(q)-2,-1,-1):q[i]=min(q[i],q[i+1]+2*45.*(arc[i+1]-arc[i]))
            q=np.minimum(q,2*core.REAR*np.maximum(0.,self.distance+arc-current))
            return dict(points=points.tolist(),arcs=arc.tolist(),ds=np.diff(arc).tolist(),length=float(arc[-1]),
                launch_squared=q.tolist(),periodic_squared=q[:-1].tolist(),observed_open=True)
        self.uncertainty.update(map='finite observed corridor + explicit vehicle occlusion interpolation',
            observation_support_m=[float(arc[0]),float(arc[-1])],global_map_available=False,
            obstacles='visible grayscale detections with0.4m radius inflation; unseen obstacles unknown')
        return core.Scene(roads,boundary,obstacles),reference(153.,90.),reference(100.,80.),current

    def _root(self,scene,lateral_speed):
        yaw=self.yaw;rate=float(np.clip((self.joint-self.previous_joint)/.08,-3.,3.))
        center=tuple(float(x) for x in self.com)
        delta=self.com-self.hull_com
        lateral_speed=float(np.clip(lateral_speed,-self.speed,self.speed))
        # HUD speed is hull velocity magnitude, not its forward component.
        forward_speed=math.sqrt(max(0.,self.speed**2-lateral_speed**2))
        velocity=(lateral_speed-yaw*float(delta[1]),forward_speed+yaw*float(delta[0]))
        joints=(self.joint,self.joint,0.,0.);rates=(rate,rate,0.,0.)
        contacts=tuple(core.indexed_contacts(core.rectangle((center[0]+r[0],center[1]+r[1]),q),scene.roads,scene.index,.02) for r,q in zip(self.levers,joints))
        wheels=[]
        for i,(r,q) in enumerate(zip(self.levers,joints)):
            friction=max([240.*self.grip_prior,*[400.*scene.roads[j][1] for j in contacts[i]]])
            # Only the first observation uses a rolling prior. Later observations
            # retain wheel spin/throttle integrated from our own previous action;
            # camera-frame geometry and observable body estimates are rebuilt.
            omega,gas=((self.speed/.54,0.) if self.predicted_wheels is None else self.predicted_wheels[i])
            wheels.append(core.Wheel(omega,gas,q,friction,(-yaw*float(r[1]),yaw*float(r[0]))))
        linear=core.State(velocity,tuple(wheels),self.mass,self.engine_prior)
        momentum=self.inertia*yaw+sum(self.wheel_inertia*r for r in rates)
        planar=core.Planar(linear,tuple(tuple(float(v) for v in r) for r in self.levers),self.inertia,momentum,yaw,0.,joints,rates,(self.wheel_inertia,)*4,-float(self.previous_action[0]),self.steering_prior)
        return core.Geometry(planar,center,scene.roads,contacts,240.*self.grip_prior,.02)

    def act(self,observation):
        obs=np.asarray(observation,np.float32)
        if obs.shape!=(4,84,84) or not np.isfinite(obs).all():raise ValueError('OBSERVATION_CONTRACT')
        lateral=self._state_estimates(obs)
        scene,high,low,progress=self._map(obs[-1])
        root=self._root(scene,lateral)
        controller=core.Controller(high,low,scene)
        controller.model=self.counter
        self.calls+=1;before=self.counter[0]
        self.diagnostics=dict(runtime598_calls=self.calls,model_ticks_total=self.counter[0],
            input_kind='estimated_observation_only',true_state_certificate=False,
            prefix39_replacement='original feedback chooser from first decision; no saved commands',
            finite_path_change='no modulo/closing chord on observed_open path',
            uncertainty=dict(self.uncertainty),estimated_speed=self.speed,
            estimated_wheel_omega=[w.omega for w in root.planar.linear.wheels],
            wheel_state_propagated=self.predicted_wheels is not None)
        action,report=controller.select(root,progress,40,self.history,self.history)
        self.diagnostics.update(model_ticks_total=self.counter[0],decision_model_ticks=self.counter[0]-before,
            original_chooser_reason=report['mode'],estimated_admission=action is not None)
        trial_reports=report.get('trials',report.get('reports',[]))
        reasons=[q['reason'] for q in trial_reports]
        self.diagnostics['estimated_report_reasons']={reason:reasons.count(reason) for reason in set(reasons)}
        if action is None:raise RuntimeError('NO_ESTIMATED_INPUT_ADMISSIBLE_ACTION')
        self.previous_action=action.copy();self.last_root=root
        # History is explicitly model-predicted, not actual clipped-wheel truth.
        r=root
        for i in range(4):
            r=core.replace(r,planar=core.replace(r.planar,steer=-float(action[0])))
            forces=core.force_rows(r,action)
            self.history[0]+=sum(f['clipped'] for f in forces);self.history[1]+=4
            r=core.tick(r,float(action[1]),float(action[2]),scene.index,self.counter)
        self.predicted_wheels=tuple((w.omega,w.gas) for w in r.planar.linear.wheels)
        velocity=core.hull_pose(r)[1];angle=r.planar.angle
        self.predicted_hull_speed=math.hypot(*velocity)
        self.predicted_hull_velocity_body=(math.cos(angle)*velocity[0]+math.sin(angle)*velocity[1],
            -math.sin(angle)*velocity[0]+math.cos(angle)*velocity[1])
        self.diagnostics['model_ticks_total']=self.counter[0]
        return action
