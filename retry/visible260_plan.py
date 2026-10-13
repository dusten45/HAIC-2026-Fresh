"""Current-renderer-FOV localGT provider and minimum-displacement local planner.

No globaltile IDs, finishindex, optimizedglobalpath or globalspeedprofile inputs.
Visible roadcentres inferred from visibleboundary edges; notpixel-only.
"""
import numpy as np
import cv2
from retry.current_view_road_oracle import camera


def observed_geometry(raw):
    from core.vendor.car_racing import WINDOW_W,WINDOW_H
    zoom,translation,angle=camera(raw);R=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]]);carpolys=[np.array([obj.GetWorldPoint(v) for v in f.shape.vertices]) for obj in raw.car.drawlist for f in obj.fixtures];obstacles=[(np.asarray(o.position),float(o.fixtures[0].shape.radius)) for o in raw.obstacles]
    def screen(world):
        q=np.asarray(world)@R.T*zoom+np.asarray(translation);q[:,1]=WINDOW_H-1-q[:,1];return q
    def inside(q):return bool(np.all((q[:,0]>=0)&(q[:,0]<WINDOW_W)&(q[:,1]>=0)&(q[:,1]<WINDOW_H*35/40)))
    def occluded(point):
        if any(np.linalg.norm(point-o)<r for o,r in obstacles):return True
        return any(cv2.pointPolygonTest(p.astype(np.float32),tuple(map(float,point)),False)>=0 for p in carpolys)
    segments=[]
    for tile in raw.road:
        q=np.array([tile.GetWorldPoint(v) for v in tile.fixtures[0].shape.vertices]);pix=screen(q)
        boundary=np.concatenate([q[j]+np.linspace(0,1,17)[:,None]*(q[(j+1)%4]-q[j]) for j in range(4)])
        if not inside(pix) or any(occluded(p) for p in boundary):continue
        lengths=np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1);ends=[(q[j]+q[(j+1)%4])/2 for j in np.argsort(lengths)[-2:]];segments.append(np.asarray(ends))
    # Remove sourceiteration/index ordering; geometry sorting only.
    segments.sort(key=lambda p:tuple(p.mean(0)));visible=[]
    for o,r in obstacles:
        circle=o+np.c_[np.cos(np.arange(32)*2*np.pi/32),np.sin(np.arange(32)*2*np.pi/32)]*r
        if inside(screen(circle)) and not any(cv2.pointPolygonTest(p.astype(np.float32),tuple(map(float,v)),False)>=0 for p in carpolys for v in np.vstack([circle,o])):visible.append((o,r))
    return dict(segments=segments,obstacles=np.asarray([o for o,r in visible]).reshape(-1,2),radii=np.asarray([r for o,r in visible]),pose=np.asarray(raw.car.hull.position),forward=np.asarray(raw.car.hull.GetWorldVector((0,1))),speed=float(np.linalg.norm(raw.car.hull.linearVelocity)),global_ids_provided=False)


def local_center(data):
    segments=data['segments'];pos=data['pose'];forward=data['forward']
    if not segments:return None
    candidates=[]
    for i,(a,b) in enumerate(segments):
        v=b-a;u=np.clip((pos-a)@v/max(v@v,1e-9),0,1);projection=a+u*v;candidates.append((np.linalg.norm(pos-projection),i,projection))
    _,i,projection=min(candidates,key=lambda x:x[0]);a,b=segments[i]
    if (b-a)@forward<0:a,b=b,a
    path=[projection]
    if np.linalg.norm(b-projection)>.05:path.append(b)
    endpoint=b;used={i}
    while len(path)<30:
        options=[]
        for j,(a,b) in enumerate(segments):
            if j in used:continue
            if np.linalg.norm(a-endpoint)<.01:options.append((j,b))
            elif np.linalg.norm(b-endpoint)<.01:options.append((j,a))
        if not options:break
        j,nxt=options[0];used.add(j);path.append(nxt);endpoint=nxt
    return np.asarray(path) if len(path)>=4 else None


def open_curvature(line):
    a=line[1:-1]-line[:-2];b=line[2:]-line[1:-1];c=a+b;k=2*(a[:,0]*b[:,1]-a[:,1]*b[:,0])/np.maximum(np.linalg.norm(a,axis=1)*np.linalg.norm(b,axis=1)*np.linalg.norm(c,axis=1),1e-9);return np.r_[k[0],k,k[-1]]


def local_plan(data,model):
    center=local_center(data)
    if center is None:return None
    ds=np.linalg.norm(np.diff(center,axis=0),axis=1);s=np.r_[0,np.cumsum(ds)];L=s[-1];K=6;u=s/L*(K-1);B=np.zeros((len(center),K))
    for j in range(K):
        d=abs(u-j);B[:,j]=np.where(d<1,(4-6*d*d+3*d**3)/6,np.where(d<2,(2-d)**3/6,0))
    B/=B.sum(1)[:,None];t=np.gradient(center,axis=0);t/=np.maximum(np.linalg.norm(t,axis=1)[:,None],1e-9);normal=np.c_[t[:,1],-t[:,0]];start_offset=float((data['pose']-center[0])@normal[0]);bound=40/6-1.4-.35;desired=np.zeros(len(center));weights=np.ones(len(center))*.01
    for o,r in zip(data['obstacles'],data['radii']):
        i=int(np.argmin(np.linalg.norm(center-o,axis=1)));l=float((o-center[i])@normal[i]);desired[i]=(-1 if l>=0 else 1)*min(bound,r+2.9+.45-abs(l));weights[i]=50
    theta=np.linalg.solve(B.T@(weights[:,None]*B)+.02*np.eye(K),B.T@(weights*desired));theta=np.clip(theta,-bound,bound);calls=0
    def evaluate(q):
        nonlocal calls;calls+=1;off=B@q;off+=np.exp(-s/10)*(np.clip(start_offset,-bound,bound)-off[0]);line=center+normal*off[:,None];v=np.diff(line,axis=0);k=open_curvature(line);bad=np.sum(np.maximum(abs(k)-np.tan(.4)/3.24,0)**2)*100+np.sum(np.maximum(abs(off)-bound,0)**2)
        if len(data['obstacles']):
            delta=data['obstacles'][None]-line[:-1,None];fraction=np.clip(np.sum(delta*v[:,None],axis=2)/np.maximum(np.sum(v*v,axis=1)[:,None],1e-9),0,1);near=line[:-1,None]+fraction[:,:,None]*v[:,None];clear=np.min(np.linalg.norm(near-data['obstacles'][None],axis=2),axis=0)-(data['radii']+2.9+.25);bad+=np.sum(np.maximum(-clear,0)**2)
        return float(np.sum(off*off*np.r_[ds,ds[-1]])/np.sum(np.r_[ds,ds[-1]])+1000*bad),line,float(bad)
    best=evaluate(theta)
    for step in [1.,.4]:
        for j in range(K):
            chosen=theta.copy();value=best
            for sign in [-1,1]:
                trial=theta.copy();trial[j]=np.clip(trial[j]+sign*step,-bound,bound);r=evaluate(trial)
                if r[0]<value[0]:chosen,value=trial,r
            theta,best=chosen,value
    _,line,bad=best;k=open_curvature(line);ds=np.linalg.norm(np.diff(line,axis=0),axis=1);speed=np.minimum(100.,np.sqrt(model['lateral_accel']/np.maximum(abs(k),1e-6)));speed[0]=min(speed[0],data['speed'])
    # Publicunknown-tail boundary: holdlastobservedcurvature, notstop.
    for _ in range(4):
        for i in range(len(line)-2,-1,-1):speed[i]=min(speed[i],np.sqrt(speed[i+1]**2+2*model['brake_accel']*ds[i]))
        for i in range(len(line)-1):
            acc=min(model['rear_traction_accel'],80000/(speed[i]+2.7)/model['effective_mass']);speed[i+1]=min(speed[i+1],np.sqrt(speed[i]**2+2*acc*ds[i]))
    return dict(line=line,speed=speed,curvature=k,ds=ds,visible_length_m=float(ds.sum()),objective_calls=calls,geometry_violation=bad,geometrically_feasible=bad<=1e-8,assumed_tail_curvature=float(k[-1]))
