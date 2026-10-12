"""Frozen affine base +78parameter16->4->2 identity/tanh corrections.

Weighted sum SSE (no row/channel averaging), lambda1 on theta-theta_initial.
Clipping is used for command metrics/inference, not for the fitting objective.
Exact1000 fullbatch Adam steps, same seed/initialization, no earlystop/sweep.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np

SETTINGS=dict(input_features=16,hidden_units=4,outputs=2,trainable_parameters=78,fixed_base_parameters=34,
    hidden_activations=['identity','tanh'],seed=237,hidden_normal_std=.25,hidden_bias_initial=0.,
    output_weight_and_bias_initial=0.,loss='sum(weight*(fixed_raw_residual+network-target_residual)^2) +sum((theta-theta0)^2)',
    L2_lambda=1.,Adam_learning_rate=.01,Adam_betas=[.9,.999],Adam_epsilon=1e-8,steps=1000,
    residual_clip=.5,pedal_clip=[0.,1.],early_stop=False,sweep=False)


def unpack(t):return t[:64].reshape(16,4),t[64:68],t[68:76].reshape(4,2),t[76:78]


def initial():
    t=np.zeros(78);t[:64]=np.random.default_rng(237).normal(0,.25,64);return t


def network(z,theta,activation):
    w1,b1,w2,b2=unpack(theta);h=z@w1+b1
    if activation=='tanh':h=np.tanh(h)
    else:assert activation=='identity'
    return h@w2+b2,h


def commands(x,nominal,model,theta,activation):
    z=(x-model['mean'])/model['std'];raw=np.c_[z,np.ones(len(z))]@model['weights']
    correction,_=network(z,theta,activation);combined=raw+correction
    out=nominal.copy();pre=nominal[:,1:].astype(float)+np.clip(combined,-.5,.5);out[:,1:]=np.clip(pre,0,1)
    return out.astype(np.float32),combined,pre


def train(x,target,weight,model,activation):
    z=(x-model['mean'])/model['std'];base=np.c_[z,np.ones(len(z))]@model['weights']
    theta0=initial();theta=theta0.copy();m=np.zeros(78);v=np.zeros(78)
    initial_SSE=float(np.sum(weight[:,None]*(base-target)**2))
    for step in range(1,1001):
        pred,h=network(z,theta,activation);w1,b1,w2,b2=unpack(theta)
        d=2*weight[:,None]*(base+pred-target);dw2=h.T@d;db2=d.sum(0);dh=d@w2.T
        if activation=='tanh':dh*=1-h*h
        grad=np.r_[(z.T@dh).ravel(),dh.sum(0),dw2.ravel(),db2]+2*(theta-theta0)
        m=.9*m+.1*grad;v=.999*v+.001*grad*grad
        theta-=.01*(m/(1-.9**step))/(np.sqrt(v/(1-.999**step))+1e-8)
    pred,_=network(z,theta,activation);sse=float(np.sum(weight[:,None]*(base+pred-target)**2));pen=float(np.sum((theta-theta0)**2))
    assert np.isfinite(theta).all()
    return theta,dict(steps=1000,initial_weighted_SSE=initial_SSE,final_weighted_SSE=sse,initial_delta_L2=0.,final_delta_L2=pen,final_objective=sse+pen,parameter_changes_exact_nonzero=int(np.count_nonzero(theta-theta0)),parameter_changes_abs_gt1e12=int(np.sum(np.abs(theta-theta0)>1e-12)),max_abs_change=float(np.max(np.abs(theta-theta0))),fixed_base_unchanged=True)


def fit(root,out):
    start,cpu=time.perf_counter(),time.process_time()
    old=[np.load(root/'stage224'/('F'+str(i))/'cache.npz') for i in range(4)]
    new=[np.load(root/'stage229'/('F'+str(i))/'cache.npz') for i in range(4)]
    def data(roads):
        N=sum(len(old[i]['features']) for i in roads);xs=[];ys=[];ws=[];mass=[]
        for pop,caches in [('old',old),('new',new)]:
            for i in roads:
                c=caches[i];nom=c['champion'] if pop=='old' else c['nominal'];n=len(c['features']);xs.append(c['features']);ys.append(c['teacher'][:,1:]-nom[:,1:]);ws.append(np.full(n,N/(2*len(roads)*n)));mass.append(dict(population=pop,road='F'+str(i),rows=n,weight=N/(2*len(roads))))
        return np.concatenate(xs),np.concatenate(ys).astype(float),np.concatenate(ws),mass
    def metric(held,model,theta,activation):
        groups=[]
        for pop,caches in [('old',old),('new',new)]:
            c=caches[held];nom=c['champion'] if pop=='old' else c['nominal'];pred,raw,pre=commands(c['features'],nom,model,theta,activation);e=pred[:,1:].astype(float)-c['teacher'][:,1:]
            groups.append(dict(population=pop,rows=len(pred),MAE=np.abs(e).mean(0).tolist(),MSE=(e*e).mean(0).tolist(),residual_clip_fraction=(np.abs(raw)>.5).mean(0).tolist(),pedal_clip_fraction=((pre<0)|(pre>1)).mean(0).tolist()))
        return dict(groups=groups,group_equal_MAE=np.mean([g['MAE'] for g in groups],axis=0).tolist(),group_equal_RMSE=np.sqrt(np.mean([g['MSE'] for g in groups],axis=0)).tolist(),group_equal_residual_clip_fraction=np.mean([g['residual_clip_fraction'] for g in groups],axis=0).tolist(),group_equal_pedal_clip_fraction=np.mean([g['pedal_clip_fraction'] for g in groups],axis=0).tolist())
    folds=[];full=[]
    for held in [0,1,2,3,None]:
        roads=[i for i in range(4) if i!=held];x,y,weight,mass=data(roads)
        basepath=root/'stage231/single-head.npz' if held is None else root/'stage229'/('aggregate-head'+str(held)+'.npz')
        model=np.load(basepath);base_sha=hashlib.sha256(basepath.read_bytes()).hexdigest();mean=np.average(x,axis=0,weights=weight);std=np.maximum(np.sqrt(np.average((x-mean)**2,axis=0,weights=weight)),1e-6)
        assert np.array_equal(mean,model['mean']) and np.array_equal(std,model['std'])
        rec=dict(held_out=None if held is None else 'F'+str(held),train_roads=['F'+str(i) for i in roads],weight_mass=mass,fixed_base_sha256=base_sha,train_only_normalization_exact=True,arms={})
        if held is not None:rec['baseline']=metric(held,model,initial(),'identity')
        for activation in ['identity','tanh']:
            t0=initial();check,_=network((x-model['mean'])/model['std'],t0,activation);assert np.array_equal(check,np.zeros((len(x),2)))
            theta,receipt=train(x,y,weight,model,activation)
            name=('full' if held is None else 'fold'+str(held))+'-'+activation+'.npz';p=out/name
            assert not p.exists();np.savez(p,mean=model['mean'],std=model['std'],weights=model['weights'],theta=theta,theta0=t0);p.chmod(0o600)
            receipt['model_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();receipt['zero_initial_correction_exact']=True
            if held is not None:receipt['held_command_error']=metric(held,model,theta,activation)
            rec['arms'][activation]=receipt
        assert hashlib.sha256(basepath.read_bytes()).hexdigest()==base_sha
        (full if held is None else folds).append(rec)
    result=dict(stage=237,settings=SETTINGS,folds=folds,full_DEV=full[0],wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu,native_actions=0,model_queries=0,scope='LOO excludesentireheldroad old/new fromadditionaltraining/base/norm. Fullheads trainallDEV; subsequentDEVnative is notindependentvalidation.')
    with (out/'fit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    (out/'fit.json').chmod(0o600);print(json.dumps(dict(folds=4,full_arms=2,parameters=78,fixed_base=34,steps_per_fit=1000,wall_s=result['wall_s'])))


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--private-root',type=Path,required=True);a.add_argument('--output',type=Path,required=True);p=a.parse_args();fit(p.private_root,p.output)
