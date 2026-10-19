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


def recover_pixel_edge(image,y,index,direction,blocked):
    """Invert a fully visible, monotone two-colour raster edge by area.

    Flat-step area gives a location estimate; resizing still has phase error.
    Plateau and monotonicity checks reject mixed materials, occlusion and
    clipped support. This is not a verified uncertainty bound.
    """
    ids=index+direction*np.arange(-3,5)
    if y>=55 or min(ids)<0 or max(ids)>=84 or np.any(blocked[y,ids]):return None
    values=image[y,ids].astype(np.float64)
    quantum=1./255.
    if np.ptp(values[:2])>2*quantum or np.ptp(values[-2:])>2*quantum:return None
    outside=float(np.mean(values[:2]));inside=float(np.mean(values[-2:]))
    if not .36<inside<.47 or abs(inside-outside)<24*quantum:return None
    fraction=(values-outside)/(inside-outside)
    tolerance=quantum/abs(inside-outside)
    if min(fraction)<-tolerance or max(fraction)>1+tolerance or min(np.diff(fraction))<-tolerance:return None
    edge=4.5-float(np.sum(np.clip(fraction,0.,1.)))
    if not -2.5<=edge<=2.5:return None
    return float(index+direction*edge)


def _raster_halfplane(ids,row,edges,slope):
    """Continuous-area 1000x800->96 filter followed by public84 linear resize."""
    u=(ids+.5)*96./84.-.5;j=np.floor(u);wx=u-j
    v=(row+.5)*96./84.-.5;k=math.floor(v);wy=v-k
    width=84./96.;result=np.zeros((len(edges),len(ids)),np.float64)
    for dx in (0,1):
        right=(j+dx+1)*width-.5
        for dy in (0,1):
            low=(k+dy)*width-.5;high=low+width
            t0=right[None,:]-edges[:,None]-slope*(low-row)
            if abs(slope)<1e-9:area=np.clip(t0,0.,width)/width
            else:
                t1=right[None,:]-edges[:,None]-slope*(high-row)
                primitive=lambda t:.5*(np.maximum(t,0.)**2-np.maximum(t-width,0.)**2)
                area=np.clip((primitive(t1)-primitive(t0))/(-slope*width*width),0.,1.)
            result+=area*((1-wx) if dx==0 else wx)[None,:]*((1-wy) if dy==0 else wy)
    return result


def recover_curb_edge(image,y,index,direction,slope,blocked):
    """Fit visible road/paint/grass layers; mixed-paint junctions stay unknown."""
    ids=index+direction*np.arange(-7,5)
    if y<2 or y>=54 or abs(slope)>1. or min(ids)<0 or max(ids)>=84:return None
    if np.any(blocked[y-1:y+2,ids]):return None
    patch=image[y-1:y+2,ids].astype(np.float64);q=1./255.
    if np.ptp(patch[:,:3])>3*q or np.ptp(patch[:,-2:])>3*q:return None
    grass=float(np.median(patch[:,:3]));road=float(np.median(patch[:,-2:]))
    if not .36<road<.47 or not 156*q<=grass<=184*q:return None
    white=np.max(patch)>grass+8*q;red=np.min(patch)<road-8*q
    if white==red:return None
    paint=1. if white else 76./255.
    edges=index+direction*np.linspace(-2.5,.5,49)
    # Public BORDER=8/6 metres; anisotropic84 projection of a normal offset.
    curb_width=(8./6.)*1.3608*math.sqrt(1.+(slope*1.701/1.3608)**2)
    predictions=[]
    for row in (y-1,y,y+1):
        edge=edges+slope*(row-y)
        inner=_raster_halfplane(ids,row,edge,slope)
        outer=_raster_halfplane(ids,row,edge-direction*curb_width,slope)
        if direction<0:inner=1-inner;outer=1-outer
        predictions.append(grass+(paint-grass)*outer+(road-paint)*inner)
    model=np.stack(predictions,axis=1);residual=model-patch[None,:,:]
    score=np.mean(residual**2,axis=(1,2));best=int(np.argmin(score))
    # One public high-resolution pixel of raster phase plus gray quantization.
    tolerance=2*q+(84./1000.)*max(abs(paint-road),abs(paint-grass))
    if math.sqrt(float(score[best]))>tolerance/2 or np.max(abs(residual[best]))>tolerance:return None
    return float(edges[best])


def visible_road_evidence(image):
    """Interior asphalt pixels actually seen, excluding opaque/HUD support."""
    mask=((image>.36)&(image<.47)).astype(np.uint8)
    mask[70:]=0;mask[55:70,34:51]=0
    return cv2.erode(mask,np.ones((3,3),np.uint8),iterations=1)


def register_road_frames(previous,current):
    """Observed rigid camera motion, with forward/backward pixel checks."""
    a=np.rint(previous*255).astype(np.uint8);b=np.rint(current*255).astype(np.uint8)
    mask=np.zeros((84,84),np.uint8);mask[5:70,2:82]=255;mask[54:70,33:52]=0
    points=cv2.goodFeaturesToTrack(a,128,.01,3,mask=mask)
    if points is None or len(points)<8:return None
    q,status,_=cv2.calcOpticalFlowPyrLK(a,b,points,None,winSize=(15,15),maxLevel=3)
    if q is None:return None
    back,reverse,_=cv2.calcOpticalFlowPyrLK(b,a,q,None,winSize=(15,15),maxLevel=3)
    if back is None:return None
    valid=status.ravel().astype(bool)&reverse.ravel().astype(bool)
    valid&=np.linalg.norm(back[:,0]-points[:,0],axis=1)<=.5
    if np.sum(valid)<8:return None
    p=points[valid,0].astype(np.float64);q=q[valid,0].astype(np.float64)
    for v in (p,q):v[:,0]=(v[:,0]-IMAGE_ORIGIN_X)/1.3608;v[:,1]=(IMAGE_ORIGIN_Y-v[:,1])/1.701
    transform,inliers=cv2.estimateAffinePartial2D(p,q,method=cv2.RANSAC,ransacReprojThreshold=.25,maxIters=200,confidence=.99)
    if transform is None or inliers is None:return None
    keep=inliers.ravel().astype(bool);scale=math.hypot(transform[0,0],transform[1,0])
    if np.mean(keep)<.8 or not .98<=scale<=1.02:return None
    residual=np.linalg.norm(p@transform[:,:2].T+transform[:,2]-q,axis=1)
    if max(residual[keep])>.25:return None
    # Physical rigid transform -> anisotropic pixel transform.
    D=np.diag([1.3608,-1.701]);origin=np.array([IMAGE_ORIGIN_X,IMAGE_ORIGIN_Y])
    linear=D@transform[:,:2]@np.linalg.inv(D)
    translation=origin+D@transform[:,2]-linear@origin
    return np.column_stack((linear,translation))


def vehicle_occluded_pixels(image):
    """Non-asphalt interior of the known opaque hull, not its whole box."""
    mask=np.zeros((84,84),np.uint8)
    for poly in (core.HULL_POLY1,core.HULL_POLY2,core.HULL_POLY3,core.HULL_POLY4):
        points=np.array([(IMAGE_ORIGIN_X+1.3608*x*core.SIZE,
                          IMAGE_ORIGIN_Y-1.701*y*core.SIZE) for x,y in poly])
        cv2.fillPoly(mask,[np.rint(points).astype(np.int32)],1)
    mask=cv2.erode(mask,np.ones((3,3),np.uint8),iterations=1)
    return mask&(((image<=.36)|(image>=.47)).astype(np.uint8))


def vehicle_projection_mask(joint):
    """Public vehicle silhouette plus one output-pixel raster fringe."""
    mask=np.zeros((84,84),np.uint8)
    polys=[[(x*core.SIZE,y*core.SIZE) for x,y in p] for p in
           (core.HULL_POLY1,core.HULL_POLY2,core.HULL_POLY3,core.HULL_POLY4)]
    for i,(x,y) in enumerate(core.WHEELPOS):
        polys.append(core.rectangle((x*core.SIZE,y*core.SIZE),joint if i<2 else 0.))
    for poly in polys:
        pixels=np.array([(IMAGE_ORIGIN_X+1.3608*x,IMAGE_ORIGIN_Y-1.701*y) for x,y in poly])
        cv2.fillPoly(mask,[np.rint(pixels).astype(np.int32)],1)
    return cv2.dilate(mask,np.ones((3,3),np.uint8),iterations=1)


def infer_local_road_support(image,asphalt,obstacle_mask,joint,initializing,speed):
    """Conditioned connected-road hypothesis, never obstacle-clearance proof."""
    cover=vehicle_projection_mask(joint);candidates=[]
    # Output-pixel quantization plus public per-node normal change. This is a
    # conditioning tolerance, not a universal geometric uncertainty bound.
    nominal=2*(40./6.)
    tolerance=2/1.3608+nominal*(1/math.cos(.31)-1)
    for y in np.flatnonzero(np.any(cover,axis=1)):
        row=asphalt[y].astype(bool)&~cover[y].astype(bool)
        d=np.diff(np.pad(row,(1,1)).astype(np.int16));starts=np.flatnonzero(d==1);ends=np.flatnonzero(d==-1)
        good=ends-starts>=3;starts=starts[good];ends=ends[good]
        left=[i for i in range(len(starts)) if ends[i]<=math.ceil(IMAGE_ORIGIN_X)]
        right=[i for i in range(len(starts)) if starts[i]>=math.floor(IMAGE_ORIGIN_X)]
        if not left or not right:continue
        l=max(left,key=lambda i:ends[i]);r=min(right,key=lambda i:starts[i])
        a,b=int(ends[l]),int(starts[r])
        if a>=b or starts[l]==0 or ends[r]>=84:continue
        missing=~asphalt[y,a:b].astype(bool)
        if np.any(missing & ~cover[y,a:b].astype(bool)) or np.any(obstacle_mask[y,a:b]):continue
        if cover[y,starts[l]-1] or cover[y,ends[r]]:continue
        candidates.append((int(y),int(starts[l]),int(ends[r]-1),a,b))
    support=np.zeros((84,84),np.uint8)
    info=dict(road_support_inference_mode='spawn_conditioned' if initializing else 'visible_boundary_continuity',
        road_support_inferred_pixels=0,spawn_prior_used=False,occluded_obstacle_clearance_proved=False,
        local_connected_road_hypothesis=True)
    if len(candidates)<3 or (initializing and speed>3.):return support,info
    y=np.array([r[0] for r in candidates],float);matrix=np.column_stack((y-IMAGE_ORIGIN_Y,np.ones(len(y))))
    left=np.array([r[1] for r in candidates],float);right=np.array([r[2] for r in candidates],float)
    lc=np.linalg.lstsq(matrix,left,rcond=None)[0];rc=np.linalg.lstsq(matrix,right,rcond=None)[0]
    if max(np.max(abs(matrix@lc-left)),np.max(abs(matrix@rc-right)))>1.:return support,info
    if abs(lc[0]-rc[0])*(max(y)-min(y))>2.:return support,info
    slope=(lc[0]+rc[0])*.5
    normal_width=(right-left)/1.3608/math.sqrt(1+(slope*1.701/1.3608)**2)
    if np.max(abs(normal_width-nominal))>tolerance:return support,info
    if initializing:
        # Spawn centering/orientation is never assumed after the first action.
        if abs((lc[1]+rc[1])*.5-IMAGE_ORIGIN_X)>1. or abs(slope*1.701/1.3608)>math.tan(.31):return support,info
        info['spawn_prior_used']=True
    for sy,l,r,a,b in candidates:
        support[sy,a:b]=cover[sy,a:b]&(~asphalt[sy,a:b].astype(bool)).astype(np.uint8)
    support[obstacle_mask]=0
    info['road_support_inferred_pixels']=int(np.sum(support))
    return support,info


def transport_road_evidence(frames):
    """Carry only actual visible road; no registration means no old evidence."""
    unique=[]
    for frame in frames:
        if not unique or not np.array_equal(frame,unique[-1]):unique.append(frame)
    frames=unique
    road=visible_road_evidence(frames[0]);age=np.zeros((84,84),np.uint8)
    accepted=0;rejected=0
    for previous,current in zip(frames,frames[1:]):
        if np.array_equal(previous,current):continue
        transform=register_road_frames(previous,current)
        if transform is None:
            road=np.zeros((84,84),np.uint8);age[:]=0;rejected+=1
        else:
            road=cv2.warpAffine(road,transform,(84,84),flags=cv2.INTER_NEAREST,borderValue=0)
            age=cv2.warpAffine(age,transform,(84,84),flags=cv2.INTER_NEAREST,borderValue=0)+1
            road=cv2.erode(road,np.ones((3,3),np.uint8),iterations=1)
            road[age>7]=0;accepted+=1
        seen=visible_road_evidence(current);age[seen>0]=0;road|=seen
    vehicle=vehicle_occluded_pixels(frames[-1])
    return road&vehicle,dict(registered_pairs=accepted,rejected_pairs=rejected,
        transported_vehicle_pixels=int(np.sum(road&vehicle)),unique_frames=len(frames),
        registration_bounds_universally_validated=False)

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
        self.road_frames=[]
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

    def _map(self,image,transported=None):
        asphalt=((image>.36)&(image<.47)).astype(np.uint8)
        bright=((image>164/255.)&(image<176/255.)).astype(np.uint8);bright[69:]=0
        count,labels,stats,centers=cv2.connectedComponentsWithStats(bright)
        obstacles=[];blocked=np.zeros((84,84),bool);obstacle_blocked=blocked.copy()
        blocked[55:70,34:51]=True
        for i in range(1,count):
            x,y,w,h,area=stats[i];cx,cy=centers[i];ix,iy=int(round(cx)),int(round(cy))
            patch=asphalt[max(0,iy-4):min(69,iy+5),max(0,ix-4):min(84,ix+5)]
            if 3<=area<=30 and min(w,h)>=2 and max(w,h)<=3*min(w,h) and patch.size and np.mean(patch)>.42:
                obstacles.append((((cx-IMAGE_ORIGIN_X)/1.3608,(IMAGE_ORIGIN_Y-cy)/1.701),1.6))
                blocked[max(0,y-2):min(84,y+h+2),max(0,x-2):min(84,x+w+2)]=True
                obstacle_blocked[max(0,y-2):min(84,y+h+2),max(0,x-2):min(84,x+w+2)]=True
        # Never fill opaque pixels. The wider blocked window is only a veto on
        # subpixel recovery, not a reason to erase directly visible asphalt.
        if transported is not None:
            # Provenance is observed earlier pixels, never an inferred hole fill.
            transported=transported.copy();transported[obstacle_blocked]=0
            asphalt|=transported.astype(np.uint8)
        inferred,support_info=infer_local_road_support(image,asphalt,obstacle_blocked,self.joint,
            self.calls==0 and self.last_root is None,self.speed)
        asphalt|=inferred
        self.uncertainty.update(support_info)
        def observed_run(y,anchor):
            edges=np.diff(np.pad(asphalt[y,1:83],(1,1)).astype(np.int16));starts=np.flatnonzero(edges==1)+1;ends=np.flatnonzero(edges==-1)+1
            good=ends-starts>=3;starts=starts[good];ends=ends[good]
            if not len(starts):return None
            center=(starts+ends-1)*.5
            outside=np.maximum(starts-anchor,0)+np.maximum(anchor-ends,0)
            j=int(np.argmin(3*outside+.1*np.abs(center-anchor)))
            if outside[j]>8:return None
            return int(starts[j]),int(ends[j])
        rows=[];pixels=[];anchor=IMAGE_ORIGIN_X
        for y in range(69,4,-2):
            run=observed_run(y,anchor)
            if run is None:
                if len(rows)<3:continue
                break
            start,end=run
            left=(float(start)-IMAGE_ORIGIN_X)/1.3608+.35
            right=(float(end-1)-IMAGE_ORIGIN_X)/1.3608-.35
            if right-left<2.5:break
            anchor=(start+end-1)*.5;rows.append((left,right,(IMAGE_ORIGIN_Y-y)/1.701));pixels.append((y,start,end))
        if len(rows)<8:raise RuntimeError('OBSERVED_ROAD_SUPPORT_INSUFFICIENT')
        # Keep the reference samples unchanged. Geometry uses each actually
        # observed intermediate row, not an assumed diagonal across a missing row.
        dense=[];refined=unresolved=curb_refined=0
        for k,(y,start,end) in enumerate(pixels):
            samples=[(y,start,end)]
            if k+1<len(pixels):
                ny,ns,ne=pixels[k+1]
                if y-ny!=2:raise RuntimeError('OBSERVED_ROAD_ROW_GAP')
                mid=observed_run(y-1,(start+end+ns+ne-2)*.25)
                if mid is None or max(start,ns,mid[0])>=min(end,ne,mid[1]):
                    raise RuntimeError('OBSERVED_ROAD_MIDROW_UNSUPPORTED')
                samples.append((y-1,*mid))
            for sy,ss,se in samples:
                a=recover_pixel_edge(image,sy,ss,1,blocked) if se-ss>=8 else None
                b=recover_pixel_edge(image,sy,se-1,-1,blocked) if se-ss>=8 else None
                if (a is None or b is None) and se-ss>=8 and 2<=sy<54:
                    before=observed_run(sy-1,(ss+se-1)*.5);after=observed_run(sy+1,(ss+se-1)*.5)
                    if before is not None and after is not None:
                        if a is None:
                            a=recover_curb_edge(image,sy,ss,1,(after[0]-before[0])*.5,blocked)
                            curb_refined+=int(a is not None)
                        if b is None:
                            b=recover_curb_edge(image,sy,se-1,-1,(after[1]-before[1])*.5,blocked)
                            curb_refined+=int(b is not None)
                refined+=int(a is not None)+int(b is not None)
                unresolved+=int(a is None)+int(b is None)
                a=float(ss) if a is None else a;b=float(se-1) if b is None else b
                dense.append(((a-IMAGE_ORIGIN_X)/1.3608+.35,(b-IMAGE_ORIGIN_X)/1.3608-.35,(IMAGE_ORIGIN_Y-sy)/1.701))
        left=[(a,y) for a,b,y in dense];right=[(b,y) for a,b,y in dense]
        roads=[((left[i],right[i],right[i+1],left[i+1]),self.grip_prior) for i in range(len(dense)-1)]
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
        self.uncertainty.update(map='finite visible boundaries + explicitly conditioned local road inference',
            observation_support_m=[float(arc[0]),float(arc[-1])],global_map_available=False,
            raster_edges_refined=refined,raster_edges_unresolved=unresolved,
            raster_curb_edges_refined=curb_refined,
            subpixel_bound_universally_validated=False,obstacle_pixels_filled=False,
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
        # The stack is actual history only where consecutive images differ.
        # At reset tiled copies contribute exactly one observation.
        frames=[]
        for frame in obs:
            if not frames or not np.array_equal(frame,frames[-1]):frames.append(frame.copy())
        if self.road_frames:
            matches=[i for i,frame in enumerate(frames) if np.array_equal(frame,self.road_frames[-1])]
            if matches:self.road_frames.extend(frames[matches[-1]+1:])
            else:self.road_frames=frames
        else:self.road_frames=frames
        self.road_frames=self.road_frames[-8:]
        transported,temporal=transport_road_evidence(self.road_frames)
        self.uncertainty.update(temporal)
        scene,high,low,progress=self._map(obs[-1],transported)
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
