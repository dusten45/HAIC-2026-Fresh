"""The predetermined575 zero-excluded40 face; no endpoint-combination search."""
import numpy as np
from retry.causal575_rounding import effective_uncertainty,check

def active_face(problem,expected=40):
    x=problem['x0'];domain=np.tile([float(np.float32(.4)),1.],len(x)//2);_,original_inward,_=effective_uncertainty(problem);fixed=(original_inward[:len(x),0]>0)|(original_inward[:len(x),1]<0)
    endpoint=abs(x)==domain;neighbor=abs(x)==np.nextafter(domain.astype(np.float32),np.float32(0),dtype=np.float32).astype(float)
    if int(sum(fixed))!=expected or np.any(fixed&~(endpoint|neighbor)):raise ValueError('UNEXPECTED_PREDETERMINED_575_FACE')
    p=dict(problem,bounds=problem['bounds'].copy());p['bounds'][:len(x)][fixed]=0.
    q,inward,mag=effective_uncertainty(p)
    if np.any(q[fixed]!=0) or np.any(inward[:len(x)][fixed]!=0):raise ValueError('FIXED_ROUNDING_NOT_ZERO')
    if not check(p,x)['pass_all']:raise ValueError('ACTIVE_FACE_SEED_FAILED')
    if np.any(inward[:,0]>inward[:,1]):raise ValueError('ACTIVE_FACE_EMPTY_BOX')
    return p,fixed,q,inward

def enclosures(p,fixed,q,inward):
    x=p['x0'];scale=p['scale'];worst=0.;count=0;free=np.flatnonzero(~fixed)
    # Endpoints,zero,interior samples,and representable neighbors/ties in every
    # free coordinate. The analytic q theorem is inherited unchanged from573.
    for j in free:
        lo,hi=inward[j];values=list(np.linspace(lo,hi,17))+[0.]
        for v in [x[j]+scale[j]*lo,x[j],x[j]+scale[j]*hi]:
            a=np.float32(v);neighbors=[np.nextafter(a,np.float32(-np.inf),dtype=np.float32),a,np.nextafter(a,np.float32(np.inf),dtype=np.float32)]
            for u,w in zip(neighbors,neighbors[1:]):
                z=((float(u)+float(w))/2-x[j])/scale[j]
                if lo<=z<=hi:values.extend([z,np.nextafter(z,-np.inf),np.nextafter(z,np.inf)])
        z=np.asarray([v for v in values if lo<=v<=hi]);rounded=(x[j]+scale[j]*z).astype(np.float32).astype(float);actual=(rounded-x[j])/scale[j];error=abs(actual-z)
        if np.any(error>q[j]):raise ValueError('FREE_ENCLOSURE_FAILED:'+str(j))
        if np.any(actual<p['bounds'][j,0]-1e-8) or np.any(actual>p['bounds'][j,1]+1e-8):raise ValueError('ROUNDED_BOUND_FAILED')
        worst=max(worst,float(max(error/q[j])));count+=len(z)
    domain=np.tile([float(np.float32(.4)),1.],len(x)//2)
    return dict(fixed_count=int(sum(fixed)),exact_domain_endpoint_count=int(sum(fixed&(abs(x)==domain))),adjacent_float32_count=int(sum(fixed&(abs(x)!=domain))),free_count=len(free),fixed_actual_rounding_error=0.,free_coordinate_checks=len(free),scalar_boundary_tie_checks=count,maximum_error_over_enclosure=worst,all_pass=True,analytic_enclosure='Unchanged573 uniform halfULP+binary64 arithmetic theorem over originalfreebox;fixedexactseedq0.',seed_separate_disjunct=True,seed_original_verdict=check(p,x),zero_in_every_free_inward_interval=bool(np.all(inward[:len(x)][~fixed,0]<=0)&np.all(inward[:len(x)][~fixed,1]>=0)))
