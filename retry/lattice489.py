"""Fixed489 producer. Geometry only; no profile, simulator, optimizer or RNG."""
from fractions import Fraction as F
import numpy as np

B=40/6-1.4-.35
TARGET=np.tan(.4)/3.24
K=21

def source_geometry(snapshot):
    # Frozen original functions, AST-selected by the registered runner.
    from retry.racing258_plan import geometry
    center,normal,obs,radii=geometry(snapshot)
    ds=np.linalg.norm(np.roll(center,-1,axis=0)-center,axis=1)
    s=np.r_[0,np.cumsum(ds[:-1])];L=ds.sum()
    t=np.minimum(np.minimum(s,L-s)/10,1);t=t*t*(3-2*t)
    return center,normal,s,L,obs,radii,t

def taper(s,L):
    x=min(s,L-s,F(10))/10
    return x*x*(3-2*x)

def tube(center,points,s,L,bound=B):
    arcs=[F.from_float(float(x)) for x in s]+[F.from_float(float(L))]
    vals=[taper(x,arcs[-1]) for x in arcs]
    limits=[(F.from_float(float(bound))*min(vals[i-1] if i else vals[-2],vals[i],vals[i+1]))**2 for i in range(len(s))]
    # root incident end label is L with zero taper, not s_last's taper.
    limits[0]=F(0)
    out=np.zeros(points.shape[:2],dtype=bool)
    for i in range(len(s)):
        c=[F.from_float(float(x)) for x in center[i]]
        for j,p in enumerate(points[i]):
            out[i,j]=sum((F.from_float(float(p[k]))-c[k])**2 for k in range(2))<=limits[i]
    return out

def points(center,normal,s,L,t):
    qs=np.array([0.]+[v for x in np.arange(.5,5.,.5) for v in (x,-x)]+[B,-B],dtype=np.float64)
    p=center[:,None,:]+normal[:,None,:]*(t[:,None]*qs[None,:])[:,:,None]
    p[[0,1,len(center)-1],:,:]=center[[0,1,len(center)-1],None,:]
    unique=np.zeros(p.shape[:2],dtype=bool)
    for i,row in enumerate(p):
        seen=set()
        for j,v in enumerate(row):
            key=v.tobytes()
            if key not in seen:unique[i,j]=True;seen.add(key)
    return qs,p,unique

def edge(P,Q,obs,radii):
    a=P[:,None,None,:];b=Q[None,:,None,:];v=b-a
    t=np.clip(np.sum((obs[None,None,:,:]-a)*v,axis=3)/np.maximum(np.sum(v*v,axis=3),1e-9),0,1)
    near=a+t[:,:,:,None]*v
    margins=np.linalg.norm(near-obs[None,None,:,:],axis=3)-(radii+2.9+.25)
    margin=np.min(margins,axis=2)
    lengths=np.linalg.norm(Q[None,:,:]-P[:,None,:],axis=2)
    valid=(margin>=0)&np.isfinite(lengths)&(lengths>0)&np.all(np.isfinite(margins),axis=2)
    return valid,margin

def triple(P,Q,R,target=TARGET):
    a=Q[None,:,None,:]-P[:,None,None,:]
    b=R[None,None,:,:]-Q[None,:,None,:];c=a+b
    cross=a[:,:,:,0]*b[:,:,:,1]-a[:,:,:,1]*b[:,:,:,0]
    k=2*cross/np.maximum(np.linalg.norm(a,axis=3)*np.linalg.norm(b,axis=3)*np.linalg.norm(c,axis=3),1e-9)
    return np.isfinite(k)&(abs(k)<=target)&(np.sum(a*b,axis=3)>0)

def advance(reachable,triples,edges):
    options=reachable[:,:,None]&triples&edges[None,:,:]
    reached=options.any(axis=0)
    parent=np.where(reached,options.argmax(axis=0),255).astype(np.uint8)
    return reached,parent

def choose(reach,edge_last,triple_last,triple_root):
    goals=reach&edge_last[:,0][None,:]&triple_last[:,:,0]&triple_root[:,0,0][None,:]
    found=np.argwhere(goals)
    return None if len(found)==0 else tuple(int(x) for x in found[0])

def reconstruct(parents,goal):
    n=len(parents);ranks=np.zeros(n,dtype=np.uint8)
    ranks[-2:]=goal
    for i in range(n-1,1,-1):
        a=int(parents[i,int(ranks[i-1]),int(ranks[i])]);assert a!=255
        ranks[i-2]=a
    assert ranks[0]==ranks[1]==ranks[-1]==0
    return ranks

def compatibility(line):
    # Conservative on-reference ambiguity test; no off-reference guarantee.
    n=len(line);ds=np.linalg.norm(np.roll(line,-1,axis=0)-line,axis=1)
    duplicate=len({p.tobytes() for p in line})!=n
    backtracking=bool(np.any(np.sum((line-np.roll(line,1,axis=0))*(np.roll(line,-1,axis=0)-line),axis=1)<=0))
    def cross(a,b):return float(a[0]*b[1]-a[1]*b[0])
    collisions=[]
    for i in range(n):
        a,b=line[i],line[(i+1)%n]
        for j in range(i+1,n):
            if j==i+1 or (i==0 and j==n-1):continue
            c,d=line[j],line[(j+1)%n]
            if np.any(np.maximum(np.minimum(a,b),np.minimum(c,d))>np.minimum(np.maximum(a,b),np.maximum(c,d))):continue
            x=[cross(b-a,c-a),cross(b-a,d-a),cross(d-c,a-c),cross(d-c,b-c)]
            if x[0]*x[1]<=0 and x[2]*x[3]<=0:collisions.append([i,j])
    schema=bool(np.isfinite(line).all() and np.all(ds>0) and not duplicate)
    ok=schema and not backtracking and not collisions
    return dict(status='ON_REFERENCE_COMPATIBLE_ONLY' if ok else 'EXECUTOR_COMPATIBILITY_UNQUALIFIED',schema=schema,duplicate=duplicate,adjacent_backtracking=backtracking,nonadjacent_intersections=collisions,canonical_on_reference_projection_unambiguous=ok,off_reference_cursor_tracking_qualified=False,complete_executor_input=False)
