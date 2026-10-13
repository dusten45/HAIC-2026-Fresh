"""Reproduce fixed231 ridge, then add exactly six source-derived HUD proxies.

Same224/229 pixels/labels, population half and road-uniform weights. No GT,
new decoder training, parameter sweep or simulator calls.
"""
import argparse,json,time,hashlib
from pathlib import Path
import numpy as np
from retry.hud248_features import decode,NAMES


def fit(root,out):
    start,cpu=time.perf_counter(),time.process_time();xs=[];hs=[];ys=[];weights=[];mass=[];hashes={};samples=[]
    groups={stage:[np.load(root/f'stage{stage}'/f'F{i}'/'cache.npz') for i in range(4)] for stage in [224,229]}
    N=sum(len(c['features']) for c in groups[224])
    for stage,caches in groups.items():
        for i,c in enumerate(caches):
            n=len(c['features']);obs=c['observations'];indices=np.arange(n) if stage==224 else c['actions']-1
            assert len(indices)==n and indices.min()>=0 and indices.max()<len(obs)-1
            h=np.asarray([decode(obs[index,-1]) for index in indices]);x=c['features'];base=c['champion'] if stage==224 else c['nominal']
            assert h.shape==(n,6) and np.isfinite(h).all();xs.append(x);hs.append(h);ys.append(c['teacher'][:,1:]-base[:,1:]);weights.append(np.full(n,N/(8*n)))
            q=root/f'stage{stage}'/f'F{i}'/'cache.npz';hashes[str(q)]=hashlib.sha256(q.read_bytes()).hexdigest();mass.append(dict(group=stage,road='F'+str(i),rows=n,weight=N/8))
            if stage==224 and i==0:
                for j in [0,100,200]:samples.append(dict(stored_row=j,proxy=h[j].tolist()))
    x=np.concatenate(xs);h=np.concatenate(hs);y=np.concatenate(ys);weight=np.concatenate(weights)
    mean=np.average(x,axis=0,weights=weight);std=np.maximum(np.sqrt(np.average((x-mean)**2,axis=0,weights=weight)),1e-6)
    def solve(xx,mu,sd):
        z=np.c_[(xx-mu)/sd,np.ones(len(xx))];penalty=np.eye(z.shape[1]);penalty[-1,-1]=0
        return np.linalg.solve(z.T@(weight[:,None]*z)+penalty,z.T@(weight[:,None]*y))
    original=solve(x,mean,std);fixed=np.load(root/'stage231/single-head.npz');errors={k:float(np.max(np.abs(value-fixed[k]))) for k,value in [('mean',mean),('std',std),('weights',original)]}
    assert errors['mean']<1e-10 and errors['std']<1e-10 and errors['weights']<1e-10,'Original231fit reproduction failed'
    newmean=np.average(h,axis=0,weights=weight);newstd=np.maximum(np.sqrt(np.average((h-newmean)**2,axis=0,weights=weight)),1e-6)
    m22=np.r_[mean,newmean];s22=np.r_[std,newstd];w22=solve(np.c_[x,h],m22,s22)
    q=out/'head22.npz';assert not q.exists();np.savez(q,mean=m22,std=s22,weights=w22);q.chmod(0o600)
    result=dict(stage=248,old_rows=N,new_rows=sum(len(c['features']) for c in groups[229]),weight_mass=mass,original231_reproduction_max_abs=errors,added_features=NAMES,signal=dict(samples=samples,min=h.min(0).tolist(),max=h.max(0).tolist(),std=h.std(0).tolist(),nonzero_rows=np.count_nonzero(h,axis=0).tolist()),settings=dict(inputs=22,coefficients=46,L2_lambda=1.,bias_penalty=0.,residual_clip=.5,action_clip=[0,1],group_fraction=.5,road_uniform=True,normalization='TRAINweighted only; stdfloor1e-6',lateral_acceleration=[24.,8.],sweep=False,decoder_fits=0),source_cache_sha256=hashes,model_sha256=hashlib.sha256(q.read_bytes()).hexdigest(),fit_wall_s=time.perf_counter()-start,fit_CPU_s=time.process_time()-cpu,native_actions=0,new_GT_queries=0)
    with (out/'fit-private.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    (out/'fit-private.json').chmod(0o600);return result

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--prior',type=Path,required=True);a.add_argument('--out',type=Path,required=True);p=a.parse_args();print(json.dumps(fit(p.prior,p.out)))
