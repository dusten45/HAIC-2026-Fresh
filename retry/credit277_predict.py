"""Single episode-heldout state/history contrast, conditional on latecritic error."""
import argparse,time,datetime
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.credit277_analyze import ridge,weighted_metrics

def run(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage277';T=R/'stage276';summary=read(D/'analysis.json');assert not summary['history_predictor_contrast']['executed'] and not (D/'predictor-plan.json').exists()
    late=summary['critic_calibration']['late']['episode_balanced'];assert late['RMSE']>.5 and abs(late['bias_value_minus_return'])>.25
    save(D/'analysis-before-scope-review.json',summary)
    plan=dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),criterion_scope='Userrequestedearly/late: same prespecifiedRMSE/bias criterion applies to latecritic; pooledbias doesnot erase lateerror. Initialimplementationcheckedpooledonly.',
        thresholds_unchanged=True,models_and_split_unchanged=True,trigger_late=late,predictor=read(D/'plan.json')['predictor'],split=read(D/'plan.json')['episode_split'],history_support=read(D/'plan.json')['history_support'],predictor_pairs=1,native=0,policy_updates=0,
        hashes={str(q):sha(q) for q in [G/'retry/credit277_predict.py',G/'retry/credit277_analyze.py',D/'analysis-before-scope-review.json',T/'training-outcome-private.json']})
    save(D/'predictor-plan.json',plan);(D/'predictor-plan.sha256').write_text(sha(D/'predictor-plan.json')+'\n');(D/'predictor-plan.sha256').chmod(0o600)
    start=time.perf_counter();cpu=time.process_time();X=[];H=[];Y=[];V=[];E=[];ROAD=[];HALF=[];OUTCOME=[]
    for e in read(T/'training-outcome-private.json')['episodes']:
        if not (e['completed'] or e['actual_DNF']):continue
        z=np.load(T/f"episode{e['serial']:03d}_{e['road']}"/'buffer-private.npz');x=z['x'];n=len(x);hist=np.zeros((n,51))
        for lag in [1,2,3]:
            if n>lag:hist[lag:,(lag-1)*16:lag*16]=x[:-lag,:16];hist[lag:,48+lag-1]=1
        X.append(x);H.append(np.c_[x,hist]);Y.append(np.cumsum(z['reward'][::-1])[::-1]);V.append(z['value']);E.extend([e['serial']]*n);ROAD.extend([e['road']]*n);HALF.extend(['early' if e['batch']<=33 else 'late']*n);OUTCOME.extend(['complete' if e['completed'] else 'DNF']*n)
    X=np.vstack(X);H=np.vstack(H);Y=np.concatenate(Y);V=np.concatenate(V);E=np.array(E);ROAD=np.array(ROAD);HALF=np.array(HALF);OUTCOME=np.array(OUTCOME);weights=np.zeros(len(E));testids=[]
    for eid in np.unique(E):weights[E==eid]=1/np.sum(E==eid)
    for road in np.unique(ROAD):
        for half in ['early','late']:testids.extend(np.unique(E[(ROAD==road)&(HALF==half)])[4::5].tolist())
    test=np.isin(E,testids);train=~test;predictions=[];metrics=[];fitwall=[]
    for name,features in [('current28',X),('history79',H)]:
        tick=time.perf_counter();mean,std,coef=ridge(features[train],Y[train],weights[train]);fitwall.append(time.perf_counter()-tick)
        q=D/(name+'-predictor-private.npz');np.savez(q,mean=mean,std=std,coefficients=coef);q.chmod(0o600)
        predicted=np.c_[(features[test]-mean)/std,np.ones(test.sum())]@coef;predictions.append(predicted);metrics.append(weighted_metrics(Y[test],predicted,weights[test]))
    testE=E[test];testY=Y[test];per=[]
    for eid in np.unique(testE):
        m=testE==eid;per.append(dict(episode=int(eid),current_MSE=float(np.mean((predictions[0][m]-testY[m])**2)),history_MSE=float(np.mean((predictions[1][m]-testY[m])**2))))
    delta=np.array([r['history_MSE']-r['current_MSE'] for r in per]);rng=np.random.default_rng(277);boot=np.mean(rng.choice(delta,size=(500,len(delta)),replace=True),axis=1);ci=np.percentile(boot,[2.5,97.5]).tolist();improvement=1-metrics[1]['RMSE']/metrics[0]['RMSE']
    strata=[]
    for road in np.unique(ROAD):
        for half in ['early','late']:
            m=(ROAD[test]==road)&(HALF[test]==half)
            if m.any():strata.append(dict(road=road,half=half,episodes=len(np.unique(testE[m])),current=weighted_metrics(testY[m],predictions[0][m],weights[test][m]),history=weighted_metrics(testY[m],predictions[1][m],weights[test][m])))
    contrast=dict(executed=True,trigger_scope='late half meets unchangedcriterion',input_dimensions=[28,79],predictor='scalar affine ridge lambda1',train_episodes=len(np.unique(E[train])),test_episodes=len(testids),test_samples=int(test.sum()),test_metrics=metrics,
        contemporaneous_critic_on_same_heldout=weighted_metrics(testY,V[test],weights[test]),history_relative_RMSE_improvement=float(improvement),paired_episode_delta_MSE_CI95=ci,history_support_passed=improvement>=.05 and ci[1]<0,fit_wall_s=fitwall,strata=strata,
        scope='Episodeheldout within same6TRAIN and changinghistoricalpolicies, no novelroad/policy performance validation',policy_updates=0,cut_samples_excluded=True,
        availability_masks_note='Newhistoryavailabilitymasks duplicate existingactionavailability information; fixedlambda1 sensitivity is not separately tested.')
    save(D/'episode-split-private.json',dict(test_episode_ids=testids,paired_episode_losses=per));q=D/'heldout-predictions-private.npz';np.savez_compressed(q,episode=testE,observed_return=testY,current=predictions[0],history=predictions[1]);q.chmod(0o600)
    summary['history_predictor_contrast']=contrast;summary['predictor_scope_review']=plan['criterion_scope'];summary['additional_prediction_wall_s']=time.perf_counter()-start;summary['additional_prediction_CPU_s']=time.process_time()-cpu
    save(D/'analysis.json',summary);save(G/'retry/credit277_result.json',summary);(G/'retry/credit277_result.json').chmod(0o644)
    print('277pairedcontrast',dict(metrics=metrics,critic=contrast['contemporaneous_critic_on_same_heldout'],relative_RMSE_improvement=improvement,CI=ci,support=contrast['history_support_passed'],native=0),flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
