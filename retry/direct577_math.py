"""Frozen six-window bases and exact float32 direct-search proposals."""
import numpy as np
from retry.wide574_math import SCALE

def bases(p,linear,g):
    # Actual local derivatives only. Empirical L/t and rounding tubes are unused.
    physical=-linear['J']*SCALE;rank=p['A'][p['ratio_rows'],:264];support=p['A'][6656:8760,:264];A=np.vstack([physical,rank,support]);b=np.r_[g,p['b'][p['ratio_rows']],p['b'][6656:8760]];B=[];details=[]
    for k in range(6):
        ids=np.arange(44*k,44*(k+1));block=A[:,ids];norm=np.linalg.norm(block,axis=1);score=np.divide(np.maximum(b,0.),norm,out=np.full(len(b),np.inf),where=norm>1e-14);selected=[];C=[]
        for i in np.argsort(score,kind='stable'):
            if not np.isfinite(score[i]) or len(C)>=8:break
            row=block[i]/norm[i];res=row.copy()
            for previous in C:res-=np.dot(res,previous)*previous
            size=np.linalg.norm(res)
            if size>1e-8:C.append(res/size);selected.append(int(i))
        raw=-p['objective'][ids];v=raw.copy()
        for row in C:v-=np.dot(v,row)*row
        fallback=None
        if np.linalg.norm(v)<1e-10*max(np.linalg.norm(raw),1e-30):v=raw.copy();fallback='unprojected_time_gradient'
        if max(abs(v))==0:
            v=np.sin(np.linspace(0,np.pi,44));fallback='deterministic_sinusoid'
        v/=max(abs(v));full=np.zeros(264);full[ids]=v
        if p['objective']@full>0:full=-full
        B.append(full);details.append(dict(index=k,holds=[35+22*k,56+22*k],critical_rows=selected,critical_score_min=float(min(score[selected],default=0)),fallback=fallback,predicted_gain_per_unit_s=-float(p['objective']@full),infinity_norm=float(max(abs(full)))))
    return np.asarray(B),details

def propose(seed,anchor,direction,step,sign):
    domain=np.tile([float(np.float32(.4)),1.],132);lo=np.maximum(-domain,seed-.012*SCALE);hi=np.minimum(domain,seed+.012*SCALE)
    lower=lo.astype(np.float32);lower=np.where(lower.astype(float)<lo,np.nextafter(lower,np.float32(np.inf),dtype=np.float32),lower);upper=hi.astype(np.float32);upper=np.where(upper.astype(float)>hi,np.nextafter(upper,np.float32(-np.inf),dtype=np.float32),upper)
    target=anchor+sign*step*SCALE*direction;x=np.clip(target.astype(np.float32),lower,upper).astype(float)
    if np.any(abs((x-seed)/SCALE)>.012) or np.any(abs(x)>domain):raise ValueError('577_PROPOSAL_TRUST_OR_DOMAIN')
    return x,dict(domain_or_global_clipped_coordinates=int(sum((target<lo)|(target>hi))),normalized_seed_displacement=float(max(abs((x-seed)/SCALE))),exact_float32=bool(np.array_equal(x,x.astype(np.float32).astype(float))))

def choose(anchor_time,anchor_raw,cases):
    eligible=[(i,c) for i,c in enumerate(cases) if c.get('safe') and c['raw']<=anchor_raw and anchor_time-c['hull']>=1e-6]
    return min(eligible,key=lambda pair:(pair[1]['hull'],pair[1]['raw'],pair[0]))[0] if eligible else None
