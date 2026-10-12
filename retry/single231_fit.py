"""Fit one affine pedal head on all four known DEV roads, before road draw.

Same weighted objective as229: old/new half each, four roads equal within a
population, weight sum old row count, lambda1, unpenalized bias. No simulator.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from retry.pixel_residual224_fit import FEATURES

SETTINGS=dict(features=16,pedal_coefficients=34,L2_lambda=1.,bias_penalty=0.,
    old_fraction=.5,new_fraction=.5,road_fraction=.25,total_weight='old DEV row count',
    normalization='weighted DEV only',residual_clip=.5,action_clip=[0.,1.],
    steering='originalnormal24',nominal_memory='original',sweep=False)


def fit(root,out,parameters):
    start,cpu=time.perf_counter(),time.process_time();xs=[];ys=[];weights=[];mass=[]
    old=[np.load(root/'stage224'/('F'+str(i))/'cache.npz') for i in range(4)]
    new=[np.load(root/'stage229'/('F'+str(i))/'cache.npz') for i in range(4)]
    N=sum(len(x['features']) for x in old)
    for population,caches in [('old',old),('new',new)]:
        for i,c in enumerate(caches):
            base=c['champion'] if population=='old' else c['nominal'];x=c['features'];n=len(x)
            xs.append(x);ys.append(c['teacher'][:,1:]-base[:,1:]);weights.append(np.full(n,N/(8*n)))
            mass.append(dict(population=population,road='F'+str(i),rows=n,weight=N/8))
    x=np.concatenate(xs);y=np.concatenate(ys);weight=np.concatenate(weights)
    mean=np.average(x,axis=0,weights=weight);std=np.maximum(np.sqrt(np.average((x-mean)**2,axis=0,weights=weight)),1e-6)
    z=np.c_[(x-mean)/std,np.ones(len(x))];penalty=np.eye(17);penalty[-1,-1]=0
    w=np.linalg.solve(z.T@(weight[:,None]*z)+penalty,z.T@(weight[:,None]*y))
    model=out/'single-head.npz';assert not model.exists();np.savez(model,mean=mean,std=std,weights=w);model.chmod(0o600)
    export=dict(schema='normal24-affine-pedal-v1',settings=SETTINGS,features=FEATURES,
                mean=mean.tolist(),std=std.tolist(),weights=w.tolist(),weight_mass=mass,
                source_data='Known DEV224/229 only; no road identities or raw observations/targets included')
    with parameters.open('x') as f:json.dump(export,f,indent=2,allow_nan=False);f.write('\n')
    parameters.chmod(0o644)
    receipt=dict(stage=231,settings=SETTINGS,old_rows=N,new_rows=sum(len(c['features']) for c in new),
        weight_mass=mass,model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),
        public_parameter_sha256=hashlib.sha256(parameters.read_bytes()).hexdigest(),
        wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu,native_actions=0,
        condition_draws_before_fit=0)
    with (out/'fit.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
    (out/'fit.json').chmod(0o600)


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--prior',type=Path,required=True)
    a.add_argument('--out',type=Path,required=True);a.add_argument('--parameters',type=Path,required=True);p=a.parse_args();fit(p.prior,p.out,p.parameters)
