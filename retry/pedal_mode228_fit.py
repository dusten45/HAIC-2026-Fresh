"""Fixed whole-road LOO multinomial mode + mode-specific ridge strength heads.

No simulator is imported. Private caches contain actual legal 16-feature
shadow inputs separately from teacher targets. No class weighting or sweeps.
"""
import argparse
import json
from pathlib import Path
import time
import numpy as np

SETTINGS=dict(features=16,mode_order=['gas','brake','coast'],L2_lambda=1.,bias_penalty=0.,
    objective='sum cross entropy + .5 squared nonbias weights',optimizer='deterministic inverse BFGS',
    init='all zeros',max_iterations=400,gradient_infinity_tolerance=1e-6,
    line_search='Armijo1e-4, initial1, half steps at most40',
    normalization='train roads only mean/std floor1e-6',
    strength='ridge sum squared loss+lambda1, same normalization, mode rows only',
    output='argmax gas/brake/coast; one strength clipped0..1, coast0/0; nominal steering',
    absent_class='Keep3logits, no pseudo counts; finite optimizer approximation reported',sweep=False)


def modes(y):
    g=y[:,1]>np.float32(0);b=y[:,2]>np.float32(0)
    assert not (g&b).any()
    return np.where(g,0,np.where(b,1,2))


def loss_grad(v,z,labels):
    w=v.reshape(z.shape[1],3);s=z@w;s-=s.max(1,keepdims=True)
    ex=np.exp(s);prob=ex/ex.sum(1,keepdims=True)
    loss=float(np.sum(np.log(ex.sum(1))-s[np.arange(len(z)),labels])+.5*np.sum(w[:-1]**2))
    prob[np.arange(len(z)),labels]-=1
    grad=z.T@prob;grad[:-1]+=w[:-1]
    return loss,grad.ravel()


def classifier(z,labels):
    v=np.zeros(z.shape[1]*3);H=np.eye(len(v));value,grad=loss_grad(v,z,labels);history=[]
    for i in range(SETTINGS['max_iterations']):
        if np.max(np.abs(grad))<=SETTINGS['gradient_infinity_tolerance']:break
        direction=-H@grad
        if float(direction@grad)>=0:direction=-grad;H=np.eye(len(v))
        rate=1.;slope=float(grad@direction)
        for j in range(40):
            trial=v+rate*direction;newval,newgrad=loss_grad(trial,z,labels)
            if np.isfinite(newval) and newval<=value+1e-4*rate*slope:break
            rate*=.5
        else:raise RuntimeError('Fixed BFGS line search failed')
        step=trial-v;delta=newgrad-grad;sy=float(step@delta)
        if sy>1e-10:
            rho=1./sy;V=np.eye(len(v))-rho*np.outer(step,delta)
            H=V@H@V.T+rho*np.outer(step,step)
        v,value,grad=trial,newval,newgrad;history.append(value)
    return v.reshape(z.shape[1],3),dict(iterations=len(history),objective=value,
        gradient_inf=float(np.max(abs(grad))),converged=bool(np.max(abs(grad))<=1e-6),
        coast_training_rows=int((labels==2).sum()),absent_coast_bias_limit='No finite exact unpenalized-bias MLE when class absent')


def predict(x,base,mean,std,w,gas,brake):
    z=np.c_[(x-mean)/std,np.ones(len(x))];mode=np.argmax(z@w,axis=1)
    out=base.copy();out[:,1:]=0
    out[mode==0,1]=np.clip(z[mode==0]@gas,0,1)
    out[mode==1,2]=np.clip(z[mode==1]@brake,0,1)
    return out.astype(np.float32),mode


def score(pred,y,labels,decisions=None):
    g=pred[:,1]>0;b=pred[:,2]>0;actual=np.where(g&b,3,np.where(g,0,np.where(b,1,2)))
    confusion=np.zeros((3,4),int)
    for t,a in zip(labels,actual):confusion[t,a]+=1
    d=pred[:,1:].astype(float)-y[:,1:]
    return dict(rows=len(y),pedal_MAE=np.abs(d).mean(0).tolist(),pedal_RMSE=np.sqrt((d*d).mean(0)).tolist(),
        actual_mode_error=float(np.mean(actual!=labels)),argmax_mode_error=None if decisions is None else float(np.mean(decisions!=labels)),
        confusion_teacher3_actual4=confusion.tolist(),simultaneous_positive_fraction=float(np.mean(g&b)))


def fit(root,outdir):
    start,cpu=time.perf_counter(),time.process_time();contract=json.loads((outdir/'contract.json').read_text())
    assert contract['fit_settings']==SETTINGS
    caches=[np.load(root/'stage224'/('F'+str(i))/'cache.npz',allow_pickle=False) for i in range(4)];folds=[]
    for i in range(4):
        t,c=time.perf_counter(),time.process_time();train=[j for j in range(4) if j!=i]
        x=np.concatenate([caches[j]['features'] for j in train]);y=np.concatenate([caches[j]['teacher'] for j in train]);labels=modes(y)
        mean=x.mean(0);std=np.maximum(x.std(0),1e-6);z=np.c_[(x-mean)/std,np.ones(len(x))]
        w,opt=classifier(z,labels);penalty=np.eye(17);penalty[-1,-1]=0;strength=[]
        for k in [0,1]:
            zz=z[labels==k];target=y[labels==k,k+1]
            assert len(zz)>0
            strength.append(np.linalg.solve(zz.T@zz+penalty,zz.T@target))
        f=caches[i];pred,decisions=predict(f['features'],f['champion'],mean,std,w,*strength)
        old=np.load(root/'stage224'/('fold'+str(i)+'.npz'),allow_pickle=False)['predictions'];truth=modes(f['teacher'])
        model=outdir/('head'+str(i)+'.npz');np.savez(model,mean=mean,std=std,classifier=w,gas=strength[0],brake=strength[1]);model.chmod(0o600)
        cache=outdir/('offline'+str(i)+'.npz');np.savez(cache,predictions=pred,modes=decisions);cache.chmod(0o600)
        folds.append(dict(held_out='F'+str(i),train_roads=['F'+str(j) for j in train],train_rows=len(x),
            train_mode_counts=np.bincount(labels,minlength=3).tolist(),held_mode_counts=np.bincount(truth,minlength=3).tolist(),
            old_affine=score(old,f['teacher'],truth),mode_strength=score(pred,f['teacher'],truth,decisions),optimizer=opt,
            fit_wall_s=time.perf_counter()-t,fit_CPU_s=time.process_time()-c,model_bytes=mean.nbytes+std.nbytes+w.nbytes+sum(v.nbytes for v in strength)))
    result=dict(stage=228,settings=SETTINGS,folds=folds,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu,
        native_actions=0,scope='Offline known DEV teacher observations; coast absent, not evaluated; no driving claim')
    with (outdir/'fit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    (outdir/'fit.json').chmod(0o600)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prior',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();fit(a.prior,a.out)
