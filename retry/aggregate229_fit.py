"""Four weighted whole-road LOO affine pedal residual fits, no driving.

Old/new each get 50% of training weight, each training road equal within each
population. Weight sum equals old training row count to retain ridge lambda1
scale. Labels of the held-out road never enter fit or normalization.
"""
import argparse
import json
from pathlib import Path
import time
import numpy as np

SETTINGS=dict(features=16,pedal_coefficients=34,L2_lambda=1.,bias_penalty=0.,
    old_group_fraction=.5,new_group_fraction=.5,road_fraction_within_group=1/3,
    total_weight='old training row count',normalization='weighted train populations/roads only',
    residual_clip=.5,action_clip=[0.,1.],steering='nominal unchanged',sweep=False)


def predict(x,base,mean,std,w):
    z=np.c_[(x-mean)/std,np.ones(len(x))];out=base.copy()
    out[:,1:]=np.clip(base[:,1:].astype(float)+np.clip(z@w,-.5,.5),0,1)
    return out.astype(np.float32)


def score(pred,teacher,mask):
    d=pred[mask,1:].astype(float)-teacher[mask,1:]
    return dict(rows=int(mask.sum()),MAE=np.abs(d).mean(0).tolist() if len(d) else None,
        RMSE=np.sqrt((d*d).mean(0)).tolist() if len(d) else None,
        exact_pedal_disagreement_fraction=float(np.mean(np.any(d!=0,axis=1))) if len(d) else None,
        both_positive_fraction=float(np.mean((pred[mask,1]>0)&(pred[mask,2]>0))) if len(d) else None)


def fit(root,out):
    start,cpu=time.perf_counter(),time.process_time();contract=json.loads((out/'contract.json').read_text());assert contract['fit_settings']==SETTINGS
    outcome=json.loads((out/'outcome.json').read_text());assert len(outcome['records'])==4 and all(r['qualified'] for r in outcome['records'])
    old=[np.load(root/'stage224'/('F'+str(i))/'cache.npz') for i in range(4)]
    new=[np.load(out/('F'+str(i))/'cache.npz') for i in range(4)]
    folds=[]
    for held in range(4):
        t,c=time.perf_counter(),time.process_time();roads=[i for i in range(4) if i!=held];N=sum(len(old[i]['features']) for i in roads);xs=[];ys=[];bases=[];weights=[];mass=[]
        for population,caches in [('old',old),('new',new)]:
            for i in roads:
                cc=caches[i];base=cc['champion'] if population=='old' else cc['nominal'];n=len(cc['features']);assert n>0
                xs.append(cc['features']);ys.append(cc['teacher'][:,1:]-base[:,1:]);bases.append(base)
                weights.append(np.full(n,N/(6*n)));mass.append(dict(population=population,road='F'+str(i),rows=n,weight=N/6))
        x=np.concatenate(xs);target=np.concatenate(ys);weight=np.concatenate(weights);assert np.isclose(weight.sum(),N)
        mean=np.average(x,axis=0,weights=weight);std=np.maximum(np.sqrt(np.average((x-mean)**2,axis=0,weights=weight)),1e-6)
        z=np.c_[(x-mean)/std,np.ones(len(x))];penalty=np.eye(17);penalty[-1,-1]=0
        w=np.linalg.solve(z.T@(weight[:,None]*z)+penalty,z.T@(weight[:,None]*target))
        model=out/('aggregate-head'+str(held)+'.npz');np.savez(model,mean=mean,std=std,weights=w);model.chmod(0o600)
        cc=new[held];xx=cc['features'];base=cc['nominal'];teacher=cc['teacher'];executed=cc['executed'];pred=predict(xx,base,mean,std,w)
        prior=np.load(root/'stage224'/('fold'+str(held)+'.npz'));oldpred=base.copy();oldpred[:,1:]=np.clip(base[:,1:].astype(float)+np.clip(np.c_[(xx-prior['mean'])/prior['std'],np.ones(len(xx))]@prior['weights'][:,1:],-.5,.5),0,1)
        disagreement=np.any(executed[:,1:]!=teacher[:,1:],axis=1)
        masks=dict(all=np.ones(len(xx),bool),teacher_disagrees_with_collection=disagreement,teacher_agrees_with_collection=~disagreement)
        metrics={k:dict(old224=score(oldpred,teacher,m),aggregated=score(pred,teacher,m),collection=score(executed,teacher,m)) for k,m in masks.items()}
        cache=out/('held-predictions'+str(held)+'.npz');np.savez(cache,old=oldpred,aggregated=pred);cache.chmod(0o600)
        folds.append(dict(held_out='F'+str(held),train_roads=['F'+str(i) for i in roads],weight_mass=mass,metrics=metrics,
            fit_wall_s=time.perf_counter()-t,fit_CPU_s=time.process_time()-c))
    result=dict(stage=229,settings=SETTINGS,folds=folds,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu,
        aggregated_head_closed_loop_runs=0,scope='Held-out student states, privileged teacher labels, offline only')
    with (out/'fit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    (out/'fit.json').chmod(0o600)


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--prior',type=Path,required=True);a.add_argument('--out',type=Path,required=True);p=a.parse_args();fit(p.prior,p.out)
