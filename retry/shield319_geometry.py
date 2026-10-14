"""80ms oriented-fixture screen. Constant speed; no braking or safety model."""
import numpy as np

DT=.02;SUB=8;L=3.24;SKIN=.009999999776482582
HULL=[np.array(p,float)*.02 for p in [
    [(-60,130),(60,130),(60,110),(-60,110)],
    [(-15,120),(15,120),(20,20),(-20,20)],
    [(25,20),(50,-10),(50,-40),(20,-90),(-20,-90),(-50,-40),(-50,-10),(-25,20)],
    [(-50,-120),(50,-120),(50,-90),(-50,-90)]]]
ANCHORS=np.array([(-55,80),(55,80),(-55,-82),(55,-82)],float)*.02
WHEEL=np.array([(-14,27),(14,27),(14,-27),(-14,-27)],float)*.02
R=float(np.hypot(1.2,2.6))+SKIN;WR=float(np.linalg.norm(WHEEL,axis=1).max())


def rotate(poly,angle):
    c,s=np.cos(angle),np.sin(angle)
    return np.c_[c*poly[:,0]-s*poly[:,1],s*poly[:,0]+c*poly[:,1]]


def fixtures(position,heading_cw,joint):
    polys=HULL+[anchor+rotate(WHEEL,joint if i<2 else 0.) for i,anchor in enumerate(ANCHORS)]
    result=[]
    for p in polys:
        p=rotate(p,-heading_cw)+position
        result.append(np.vstack([p,np.repeat(p[-1:],8-len(p),axis=0)]))
    return np.array(result)


def sweep(speed,yaw_ccw,joint,command):
    v=max(0.,float(speed));joint=float(np.clip(joint,-.4,.4));initial=joint
    heading=0.;position=np.zeros(2);polys=[fixtures(position,heading,joint)]
    max_point_speed=v+R*abs(yaw_ccw)
    for tick in range(4):
        previous=joint
        end=joint+float(np.clip(50*(-float(command)-joint),-3,3))*DT
        for j in range(1,SUB+1):
            joint=previous+(end-previous)*j/SUB
            # Measured present yaw + incremental bicycle response to steering.
            # This does not identify tire dynamics, slip, damage or braking.
            rate_cw=-float(yaw_ccw)+v/L*(np.tan(-joint)-np.tan(-initial))
            mid=heading+.5*rate_cw*DT/SUB
            position+=v*np.array([np.sin(mid),np.cos(mid)])*DT/SUB
            heading+=rate_cw*DT/SUB
            polys.append(fixtures(position,heading,joint))
            max_point_speed=max(max_point_speed,v+R*abs(rate_cw)+WR*abs(end-previous)/DT)
    return np.array(polys),max_point_speed*(DT/SUB)/2


def clearance(polys,obstacles):
    obs=np.asarray(obstacles,float).reshape(-1,3)
    a=polys[:,:,:,None,:];edges=(np.roll(polys,-1,axis=2)-polys)[:,:,:,None,:]
    d=obs[None,None,None,:,:2]-a
    frac=np.clip(np.sum(d*edges,axis=-1)/np.maximum(np.sum(edges*edges,axis=-1),1e-20),0,1)
    distances=np.linalg.norm(d-frac[...,None]*edges,axis=-1).min(axis=2)
    cross=edges[...,0]*d[...,1]-edges[...,1]*d[...,0]
    inside=(np.all(cross>=-1e-12,axis=2)|np.all(cross<=1e-12,axis=2))
    signed=np.where(inside,-distances,distances)-obs[None,None,:,2]-SKIN
    return float(signed.min())


def decision(base,speed,yaw_ccw,joint,obstacles,latched):
    audit=dict(predicted_overlap=False,first_overlap=False,strict_improvement=False,
        original_margin_m=None,choices=[],sampling_half_gap_bound_m=0.,pose_samples=33,
        source_physics_ticks=0,speed_constant=True,braking_effect_predicted=False,latch_after=latched)
    if not len(obstacles):return np.asarray(base,np.float32).copy(),audit
    polygons,error=sweep(speed,yaw_ccw,joint,float(base[0]));original=clearance(polygons,obstacles)
    audit.update(original_margin_m=original,predicted_overlap=original<0,sampling_half_gap_bound_m=error)
    if latched or original>=0:return np.asarray(base,np.float32).copy(),audit
    audit.update(first_overlap=True,latch_after=True)
    choices=[(float(base[0]),original)]
    # Compare actual float32 commands; clipping at.4 must not create a
    # numerically different alternative that executes the same steering.
    for u in [float(np.float32(np.clip(float(base[0])-.08,-.4,.4))),float(np.float32(np.clip(float(base[0])+.08,-.4,.4)))]:
        if any(u==c[0] for c in choices):continue
        poly,bound=sweep(speed,yaw_ccw,joint,u);choices.append((u,clearance(poly,obstacles)))
        audit['sampling_half_gap_bound_m']=max(audit['sampling_half_gap_bound_m'],bound)
    selected=max(range(len(choices)),key=lambda i:choices[i][1])
    audit['choices']=[dict(steering=u,margin_m=m) for u,m in choices]
    audit['selected_index']=selected
    improved=choices[selected][1]>original and choices[selected][0]!=float(base[0])
    audit['strict_improvement']=bool(improved)
    action=np.asarray(base,np.float32).copy()
    if improved:action[0]=choices[selected][0];action[1]=0.;action[2]=max(float(action[2]),.5)
    return action,audit
