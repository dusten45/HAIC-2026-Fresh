"""Preserve orientation of previously traversed local observed geometry only."""
import numpy as np
from retry.visible260_plan import open_curvature

def edge_key(a,b):
    return tuple(sorted((tuple(np.round(a,4)),tuple(np.round(b,4)))))

def directed_center(data,memory):
    segments=data['segments'];pos=data['pose'];forward=data['forward']
    if not segments:return None
    candidates=[]
    for i,(a,b) in enumerate(segments):
        v=b-a;u=np.clip((pos-a)@v/max(v@v,1e-9),0,1);projection=a+u*v;candidates.append((np.linalg.norm(pos-projection),i,projection))
    _,i,projection=min(candidates,key=lambda x:x[0]);a,b=segments[i]
    direction=memory.get(edge_key(a,b),forward)
    if (b-a)@direction<0:a,b=b,a
    memory.setdefault(edge_key(a,b),(b-a)/np.linalg.norm(b-a))
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
        j,nxt=options[0];key=edge_key(endpoint,nxt);direction=memory.get(key)
        if direction is not None and (nxt-endpoint)@direction<0:break
        memory.setdefault(key,(nxt-endpoint)/np.linalg.norm(nxt-endpoint));used.add(j);path.append(nxt);endpoint=nxt
    return np.asarray(path) if len(path)>=4 else None


def local_plan(data,model,memory):
    center=directed_center(data,memory)
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
