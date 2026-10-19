"""Fixed local normal graph, linear corridor guide and geometry-only objective."""
import bisect,math
import numpy as np
from retry.smoother588_math import signed_curvature
R=3.24
EPS=1e-5


def frames(points):
    p=np.asarray(points,float);t=np.roll(p,-1,axis=0)-np.roll(p,1,axis=0);n=np.linalg.norm(t,axis=1)
    if np.any(n<=0):raise ValueError('FRAME_DEGENERACY')
    t=t/n[:,None];return t,np.c_[-t[:,1],t[:,0]]


def basis(path):
    seed=np.asarray(path['points'],float);sigma=np.asarray(path['arcs'][:-1],float);inside=np.flatnonzero((sigma>90)&(sigma<220))
    if len(inside)<3:raise ValueError('INSUFFICIENT_INTERIOR_NODES')
    free=inside[1:-1];t,normal=frames(seed);n=len(seed);weights=np.zeros(n)
    for i in range(n):weights[i]=max(0.,min(220.,path['arcs'][i+1])-max(90.,path['arcs'][i]))/path['ds'][i]
    segments=np.flatnonzero(weights>0);nodes=np.unique(np.r_[segments,(segments+1)%n]);affected=np.unique(np.r_[free,(free-1)%n])
    return dict(seed=seed,normal=normal,free=free,sigma=sigma,weights=weights,segments=segments,nodes=nodes,affected=affected)


def points(x,b):
    p=b['seed'].copy();p[b['free']]+=np.asarray(x)[:,None]*b['normal'][b['free']];return p


def components(p,b):
    ds,k=signed_curvature(p);ids=b['segments'];nodes=b['nodes'];dual=(np.roll(ds,1)+ds)/2
    length=float(ds@b['weights']);bend=float(R**2*np.sum(k[nodes]**2*dual[nodes]));transition=float(R**4*np.sum((np.roll(k,-1)[ids]-k[ids])**2/ds[ids]));burden=bend+transition
    if not all(math.isfinite(q) and q>=0 for q in [length,bend,transition,burden]) or length<=0:raise ValueError('OBJECTIVE_DOMAIN')
    return dict(length_m=length,bending_m=bend,transition_m=transition,burden_m=burden,total_length_m=float(ds.sum()),peak_abs_curvature=float(max(abs(k))))


def objective(q,seed):
    if seed['burden_m']<=0:raise ValueError('ZERO_SEED_BURDEN')
    return .5*(q['length_m']/seed['length_m']+q['burden_m']/seed['burden_m'])


def projection_order(p,b):
    edge=np.roll(p,-1,axis=0)-p;oldedge=np.roll(b['seed'],-1,axis=0)-b['seed'];return np.sum(edge*oldedge,axis=1)/np.linalg.norm(oldedge,axis=1)


def endpoint_metrics(p,old,b):
    out=[]
    for s in [90.,220.]:
        i=min(len(old['ds'])-1,bisect.bisect_left(old['arcs'][1:],s));f=(s-old['arcs'][i])/old['ds'][i];j=(i+1)%len(p);a=(1-f)*p[i]+f*p[j];ref=(1-f)*b['seed'][i]+f*b['seed'][j];v=p[j]-p[i];w=b['seed'][j]-b['seed'][i]
        out.append(dict(oldstation_m=s,position_error_m=float(np.linalg.norm(a-ref)),tangent_error_rad=float(math.atan2(v[0]*w[1]-v[1]*w[0],float(v@w)))))
    return out


def sample_count(p,ids):
    ds=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
    if np.any(ds<=0):raise ValueError('ZERO_GEOMETRY_SEGMENT')
    return sum(int(math.ceil(ds[i]/.5))+1 for i in ids)


def polyline(p):
    ds,k=signed_curvature(p);arcs=np.r_[0.,np.cumsum(ds)]
    return dict(points=np.asarray(p).tolist(),ds=ds.tolist(),arcs=arcs.tolist(),length=float(arcs[-1]),curvature=k.tolist())


def guides(b,static,fixture_polys,count):
    # Cheap fixed support planes are guides, not finite-body safety certificates.
    p=b['seed'];n=len(p);center=np.asarray([(v[2],v[3]) for v in static['track']]);_,roadnormal=frames(center)
    if len(center)!=n or len(static['boundary'])!=2*n:raise ValueError('ROAD_NODE_ASSOCIATION')
    k=len(b['free']);col={int(j):i for i,j in enumerate(b['free'])};rows=[];base=[];categories=[]
    for j in b['free']:
        count('proxy_support_packs',1);count('geometry_checks',1);polys=fixture_polys(int(j));v=np.concatenate(polys)-p[j];rn=roadnormal[j];sides=[float((np.asarray(static['boundary'][i][0])-center[j])@rn) for i in [j,n+j]];lo,hi=min(sides),max(sides);lat=float((p[j]-center[j])@rn);a=float(b['normal'][j]@rn)
        for coeff,c,name in [(a,lat+float(np.min(v@rn))-lo-.5,'ROAD_LOWER'),(-a,hi-.5-lat-float(np.max(v@rn)),'ROAD_UPPER')]:
            row=np.zeros(k);row[col[int(j)]]=coeff;rows.append(row);base.append(c);categories.append(name)
        for obstacle,radius in static['obstacles']:
            outward=p[j]-obstacle;d=float(np.linalg.norm(outward))
            if d<=0:raise ValueError('OBSTACLE_SUPPORT_DIRECTION')
            outward/=d;row=np.zeros(k);row[col[int(j)]]=float(b['normal'][j]@outward);rows.append(row);base.append(d+float(np.min(v@outward))-radius-.5);categories.append('OBSTACLE_SUPPORT')
    oldedge=np.roll(p,-1,axis=0)-p;oldds=np.linalg.norm(oldedge,axis=1)
    for j in b['affected']:
        row=np.zeros(k);t=oldedge[j]/oldds[j]
        for idx,sign in [(int(j),-1),((int(j)+1)%n,1)]:
            if idx in col:row[col[idx]]+=sign*float(b['normal'][idx]@t)
        rows.append(row);base.append(float(oldds[j]));categories.append('LOCAL_ROAD_ORDER')
    return np.asarray(rows),np.asarray(base),categories
