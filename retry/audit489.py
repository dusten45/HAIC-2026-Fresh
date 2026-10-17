"""Independent489 geometry predicates; no search, file reads or profile calls.

All functions operate only on caller-provided arrays/snapshots. The producer
owns deduplication, eligibility masking, work charging, DP and retention. This
module independently recomputes the registered numeric predicates.
"""
import math
from fractions import Fraction
import numpy as np

class Audit489Error(ValueError):pass

def _require(value,reason):
    if not value:raise Audit489Error('489_AUDIT:'+reason)

def _array(value,shape=None):
    a=np.asarray(value,dtype=np.float64)
    _require(np.isfinite(a).all() and (shape is None or a.shape==shape),'finite_array_schema')
    return a

def _points(value):
    p=_array(value)
    _require(p.ndim==2 and p.shape[1]==2 and 1<=len(p)<=21,'point_rank_schema')
    return p

def reconstruct(snapshot):
    """Reproduce original geometry/basis label operations without any solver.

    Returns center, normal, source_arc, source_L, obstacles, radii, sampled_taper.
    The source's sampled floating taper is deliberately separate from the exact
    rational reference taper used by tube_eligible.
    """
    if 'physical' in snapshot:snapshot=snapshot['physical']
    roads=sorted(snapshot['roads'],key=lambda r:r['idx'])
    _require(3<=len(roads)<=512,'station_cap_or_schema')
    _require(len({r['idx'] for r in roads})==len(roads),'duplicate_road_index')
    quads=[_array(r['fixture']['geometry']['vertices'],(4,2)) for r in roads]
    centers=[]
    for i,q in enumerate(quads):
        lengths=np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1)
        endpoints=[(q[j]+q[(j+1)%4])/2 for j in np.argsort(lengths)[-2:]]
        next_center=quads[(i+1)%len(quads)].mean(0)
        centers.append(min(endpoints,key=lambda p:np.linalg.norm(p-next_center)))
    center=np.asarray(centers,dtype=np.float64)
    tangent=np.roll(center,-1,axis=0)-np.roll(center,1,axis=0)
    norm=np.linalg.norm(tangent,axis=1)
    _require(np.isfinite(norm).all() and np.all(norm>0),'normal_frame_degenerate')
    tangent/=norm[:,None]
    normal=np.c_[tangent[:,1],-tangent[:,0]]
    ds=np.linalg.norm(np.roll(center,-1,axis=0)-center,axis=1)
    _require(np.isfinite(ds).all() and np.all(ds>0),'source_edge_degenerate')
    s=np.r_[0,np.cumsum(ds[:-1])];L=ds.sum()
    _require(np.isfinite(L) and L>0 and s[0]==0 and np.all(np.diff(s)>0) and s[-1]<L,'source_arc_order')
    distance=np.minimum(s,L-s);taper=np.minimum(distance/10,1)
    taper=taper*taper*(3-2*taper)
    obstacles=_array([o['body']['position'] for o in snapshot['obstacles']])
    radii=_array([o['fixture']['radius'] for o in snapshot['obstacles']])
    _require(obstacles.shape==(6,2) and radii.shape==(6,) and np.all(radii>0),'six_obstacle_schema')
    return center,normal,s,L,obstacles,radii,taper

def _fraction(value):
    # Convert the serialized binary64 VALUE first, never a rounded difference.
    v=float(value);_require(math.isfinite(v),'nonfinite_rational_input')
    return Fraction.from_float(v)

def _reference_taper(s,L):
    _require(Fraction(0)<=s<=L and L>0,'rational_arc_domain')
    t=min(min(s,L-s)/10,Fraction(1))
    return t*t*(3-2*t)

def tube_eligible(center,points,s,L,B):
    """Exact sufficient smoothstep tube test for all supplied node ranks.

    This returns ONLY tube eligibility. In particular it does not remove point
    aliases, force boundary bytes, or silently mask producer-ineligible ranks.
    Last edge uses labels [s_last,L], not a backwards interval to zero.
    """
    center=_array(center);points=_array(points);s=_array(s)
    _require(center.ndim==2 and center.shape[1]==2 and 3<=len(center)<=512,'tube_center_schema')
    n=len(center)
    _require(points.ndim==3 and points.shape[0]==n and points.shape[2]==2 and 1<=points.shape[1]<=21 and s.shape==(n,),'tube_node_schema')
    _require(math.isfinite(float(L)) and L>0 and s[0]==0 and np.all(np.diff(s)>0) and s[-1]<L and math.isfinite(float(B)) and B>0,'tube_arc_or_bound_schema')
    source_L=_fraction(L);bound=_fraction(B)
    labels=[_fraction(v) for v in s]
    tau=[_reference_taper(v,source_L) for v in labels]+[Fraction(0)]
    edge_min=[min(tau[i],tau[i+1]) for i in range(n)]
    squared_limits=[(bound*min(edge_min[(i-1)%n],edge_min[i]))**2 for i in range(n)]
    origins=[(_fraction(c[0]),_fraction(c[1])) for c in center]
    valid=np.zeros(points.shape[:2],dtype=bool)
    for i in range(n):
        cx,cy=origins[i];limit=squared_limits[i]
        for j,p in enumerate(points[i]):
            ux=_fraction(p[0])-cx;uy=_fraction(p[1])-cy
            valid[i,j]=ux*ux+uy*uy<=limit
    return valid

def edges(P,Q,obs,radii):
    """All directed P→Q edges: source-order complete segment distance.

    margin[i,j] is the minimum over ALL obstacles. Source radius addition is
    intentionally (radii+2.9)+0.25, never radii+3.15. A zero-length edge is
    invalid even though the source's distance denominator has a numeric floor.
    """
    P=_points(P);Q=_points(Q);obs=_array(obs);radii=_array(radii)
    _require(obs.ndim==2 and obs.shape[1]==2 and len(obs)>=1 and radii.shape==(len(obs),) and np.all(radii>0),'edge_obstacle_schema')
    start=P[:,None,None,:]
    delta=Q[None,:,None,:]-start
    numerator=np.sum((obs[None,None]-start)*delta,axis=-1)
    denominator=np.maximum(np.sum(delta*delta,axis=-1),1e-9)
    t=np.clip(numerator/denominator,0,1)
    nearest=start+t[:,:,:,None]*delta
    clear=np.linalg.norm(nearest-obs[None,None],axis=-1)-(radii+2.9+.25)
    margin=np.min(clear,axis=-1)
    lengths=np.linalg.norm(Q[None,:,:]-P[:,None,:],axis=-1)
    _require(np.isfinite(margin).all() and np.isfinite(lengths).all(),'edge_numeric_result')
    return (lengths>0)&(margin>=0),margin

def triples(A,B,C,target):
    """All ordered triples, original curvature arithmetic and positive dot.

    No node masks or cached producer decisions are consumed. Axes are incoming
    rank, current rank, outgoing rank; callers apply their independent masks.
    """
    A=_points(A);B=_points(B);C=_points(C)
    _require(math.isfinite(float(target)) and target>0,'curvature_target')
    incoming=B[None,:,None,:]-A[:,None,None,:]
    outgoing=C[None,None,:,:]-B[None,:,None,:]
    chord=incoming+outgoing
    cross=incoming[:,:,:,0]*outgoing[:,:,:,1]-incoming[:,:,:,1]*outgoing[:,:,:,0]
    n_in=np.linalg.norm(incoming,axis=-1);n_out=np.linalg.norm(outgoing,axis=-1)
    denominator=np.maximum(n_in*n_out*np.linalg.norm(chord,axis=-1),1e-9)
    curvature=2*cross/denominator
    heading_dot=np.sum(incoming*outgoing,axis=-1)
    _require(np.isfinite(curvature).all() and np.isfinite(heading_dot).all() and np.isfinite(n_in).all() and np.isfinite(n_out).all(),'triple_numeric_result')
    return (n_in>0)&(n_out>0)&(np.abs(curvature)<=target)&(heading_dot>0)
