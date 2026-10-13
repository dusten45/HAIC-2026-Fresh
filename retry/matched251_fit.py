"""One road-uniform ridge correction with frozen originalTRAIN normalization."""
import argparse,json,time,hashlib
from pathlib import Path
import numpy as np


def fit(directory,normalization):
    start,cpu=time.perf_counter(),time.process_time();xs=[];ys=[];weights=[];mass=[]
    caches=[np.load(directory/'training'/road/'targets-private.npz') for road in ['O0','O2','N0','N1','N2','N3']];N=sum(len(c['delta']) for c in caches)
    for road,c in zip(['O0','O2','N0','N1','N2','N3'],caches):
        n=len(c['delta']);xs.append(c['features']);ys.append(c['delta']);weights.append(np.full(n,N/(6*n)));mass.append(dict(road=road,rows=n,weight=N/6))
    source=np.load(normalization);x=np.concatenate(xs);y=np.concatenate(ys);weight=np.concatenate(weights);z=np.c_[(x-source['mean'])/source['std'],np.ones(N)];penalty=np.eye(17);penalty[-1,-1]=0
    w=np.linalg.solve(z.T@(weight[:,None]*z)+penalty,z.T@(weight[:,None]*y));q=directory/'correction251.npz';assert not q.exists();np.savez(q,weights=w,mean=source['mean'],std=source['std']);q.chmod(0o600)
    receipt=dict(stage=251,rows=N,road_mass=mass,L2_lambda=1.,bias_penalty=0.,normalization='Fixedoriginal231TRAINmean/std; no onpolicy/evaluation refit',correction_parameters=34,zero_target_rows=int(np.sum(np.all(y==0,axis=1))),target_delta_min=y.min(0).tolist(),target_delta_max=y.max(0).tolist(),target_delta_mean=y.mean(0).tolist(),target_delta_nonzero_rows=int(np.sum(np.any(y!=0,axis=1))),wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu,model_sha256=hashlib.sha256(q.read_bytes()).hexdigest(),native_actions=0)
    with (directory/'fit-private.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
    (directory/'fit-private.json').chmod(0o600);return receipt

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--directory',type=Path,required=True);a.add_argument('--normalization',type=Path,required=True);p=a.parse_args();print(json.dumps(fit(p.directory,p.normalization)))
