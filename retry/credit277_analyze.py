"""TRAIN-only observed-terminal credit audit; no policy update or physics."""
import argparse,time,datetime
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha

def weighted_metrics(target,value,weight=None):
    target,value=np.asarray(target),np.asarray(value)
    w=np.ones(len(target)) if weight is None else np.asarray(weight);w=w/w.sum();error=value-target
    avg=lambda a:float(w@a)
    var=lambda a:avg((a-avg(a))**2)
    return dict(samples=len(target),RMSE=float(np.sqrt(avg(error**2))),MAE=avg(abs(error)),bias_value_minus_return=avg(error),
        mean_observed_return=avg(target),mean_value=avg(value),explained_variance=1-var(target-value)/var(target) if var(target)>1e-12 else None)

def signs(a,b):
    valid=(abs(a)>1e-8)&(abs(b)>1e-8)
    return dict(samples=len(a),nonzero=int(valid.sum()),opposite_fraction=float(np.mean(np.sign(a[valid])!=np.sign(b[valid]))) if valid.any() else None,
        mean_GAE=float(np.mean(a)),mean_MC=float(np.mean(b)))

def ridge(X,y,w):
    w=w*len(w)/w.sum();mean=np.average(X,axis=0,weights=w);std=np.maximum(np.sqrt(np.average((X-mean)**2,axis=0,weights=w)),1e-6)
    Z=np.c_[(X-mean)/std,np.ones(len(X))];penalty=np.eye(Z.shape[1]);penalty[-1,-1]=0
    coef=np.linalg.solve(Z.T@(w[:,None]*Z)+penalty,Z.T@(w*y))
    return mean,std,coef

def run(R):
    D=R/'stage277';D.mkdir(mode=0o700);assert not (D/'plan.json').exists()
    G=Path(__file__).resolve().parent.parent;T=R/'stage276';out=read(T/'training-outcome-private.json');episodes=out['episodes']
    sources=[G/'retry/credit277_analyze.py',G/'retry/ppo275_model.py',T/'training-outcome-private.json',R/'project-effective-budget-v279.json']
    plan=dict(stage=277,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),native=0,model_physics=0,rollouts=list(range(3,65)),halves={'early':[3,33],'late':[34,64]},DNF_preterminal_k=[20,100],sign_zero_epsilon=1e-8,
        gradient='Initialoldpolicy score surrogate only, actorparameter gradients on matched DNF20..100subset. Actualbatch GAE normalization also applied unchanged to observed MC reference; no fabricated cut returns. Not finalPPO/Adam update.',
        critic_predictor_trigger='Episodebalanced observedterminal RMSE>0.5 and absmeanbias>0.25; minimum10complete and10DNFepisodes.',
        predictor='One pairedlambda1 scalar ridge,biasunpenalized,TRAINepisode-onlymean/std, equalepisodeweights. Current28 vs current28+3past16pixelderivedfeatures+3availabilitymasks=79. No road/GT/future/eval inputs.',
        episode_split='Perroad/half sorted terminalepisodes, every5th(index4)heldout; identical splitforbothmodels. History confined to own episode.',
        history_support='Heldoutepisodeweighted RMSE improves>=5% and 500episodepairedbootstrap95%deltaMSEinterval strictlybelow0; otherwise inconclusive/unsupported.',
        hashes={str(q):sha(q) for q in sources},policy_updates=0,no_intermediate_policy_evaluation=True,no_screen_or_HOLDOUT_or_SEALED_reads=True)
    save(D/'plan.json',plan);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600)
    started=time.perf_counter();cpu=time.process_time();batchdata={};chunks=[];cut_records=[];allX=[];allH=[];allY=[];allV=[];allE=[];allRoad=[];allHalf=[];allOutcome=[]
    for batch in range(3,65):
        z=dict(np.load(T/f'rollout{batch}-private.npz'));n=len(z['reward']);assert n==1024
        adv=np.zeros(n);carry=0.
        for i in range(n-1,-1,-1):
            delta=z['reward'][i]+(1-float(z['done'][i]))*z['next_value'][i]-z['value'][i]
            carry=delta+.95*(0. if z['cut'][i] else 1-float(z['done'][i]))*carry;adv[i]=carry
        normalized=(adv-adv.mean())/(adv.std()+1e-8)
        records=sorted([e for e in episodes if e['batch']==batch],key=lambda e:e['serial']);offset=0
        mc=np.full(n,np.nan);remaining=np.full(n,np.nan);roads=np.empty(n,object);outcomes=np.empty(n,object);distances=np.full(n,-1);epids=np.empty(n,int)
        for e in records:
            length=e['valid_samples'];sl=slice(offset,offset+length);folder=T/f"episode{e['serial']:03d}_{e['road']}";ez=dict(np.load(folder/'buffer-private.npz'))
            assert np.array_equal(ez['x'],z['x'][sl]) and np.array_equal(ez['reward'],z['reward'][sl]);assert not e['technical_interrupted']
            roads[sl]=e['road'];epids[sl]=e['serial'];outcomes[sl]='complete' if e['completed'] else 'DNF' if e['actual_DNF'] else 'cut'
            half='early' if batch<=33 else 'late'
            if e['completed'] or e['actual_DNF']:
                assert ez['done'][-1] and not ez['cut'][-1]
                returns=np.cumsum(ez['reward'][::-1])[::-1].copy();assert abs(returns[0]-e['expected_terminal_return'])<1e-9
                remaining[sl]=returns;mc[sl]=returns-ez['value'];distances[sl]=np.arange(length-1,-1,-1)
                # Only past legal16 feature values, reset/pad at episode start.
                hist=np.zeros((length,51))
                for lag in [1,2,3]:
                    if length>lag:hist[lag:,(lag-1)*16:lag*16]=ez['x'][:-lag,:16];hist[lag:,48+lag-1]=1
                allX.append(ez['x']);allH.append(np.c_[ez['x'],hist]);allY.append(returns);allV.append(ez['value']);allE.extend([e['serial']]*length);allRoad.extend([e['road']]*length);allHalf.extend([half]*length);allOutcome.extend([outcomes[offset]]*length)
            else:
                assert e['collection_cut'] and ez['cut'][-1] and not ez['done'][-1]
                k=np.arange(length-1,-1,-1);contribution=.95**k*ez['next_value'][-1]
                cut_records.append(dict(road=e['road'],half=half,serial=e['serial'],prefix_actions=length,observed_prefix_reward_sum=float(ez['reward'].sum()),bootstrap_value=float(ez['next_value'][-1]),
                    GAE_bootstrap_contribution_mean=float(contribution.mean()),GAE_bootstrap_last20_mean=float(contribution[-20:].mean()),terminal_unobserved=True))
            offset+=length
        assert offset==1024
        mcn=(mc-adv.mean())/(adv.std()+1e-8)
        batchdata[batch]=dict(z=z,adv=adv,normalized=normalized,mc=mc,mcn=mcn,remaining=remaining,roads=roads,outcomes=outcomes,distances=distances,epids=epids)
        chunks.append(dict(batch=batch,half='early' if batch<=33 else 'late',normalizer_mean=float(adv.mean()),normalizer_std=float(adv.std()+1e-8)))
    X=np.vstack(allX);H=np.vstack(allH);Y=np.concatenate(allY);V=np.concatenate(allV);E=np.array(allE);ROAD=np.array(allRoad);HALF=np.array(allHalf);OUTCOME=np.array(allOutcome)
    ids=np.unique(E);weights=np.zeros(len(E))
    for eid in ids:weights[E==eid]=1/np.sum(E==eid)
    calibration={}
    for key,mask in [('all',np.ones(len(E),bool)),('complete',OUTCOME=='complete'),('DNF',OUTCOME=='DNF'),('early',HALF=='early'),('late',HALF=='late')]:
        calibration[key]=dict(episodes=len(np.unique(E[mask])),sample_weighted=weighted_metrics(Y[mask],V[mask]),episode_balanced=weighted_metrics(Y[mask],V[mask],weights[mask]))
    for road in np.unique(ROAD):
        for half in ['early','late']:
            mask=(ROAD==road)&(HALF==half)
            calibration[road+'_'+half]=dict(episodes=len(np.unique(E[mask])),episode_balanced=weighted_metrics(Y[mask],V[mask],weights[mask]))
    windowstats=[]
    for road in list(np.unique(ROAD))+['all']:
        for half in ['early','late','all']:
            a=[];b=[];an=[];bn=[];ep=[]
            for batch,data in batchdata.items():
                if half!='all' and half!=('early' if batch<=33 else 'late'):continue
                mask=(data['outcomes']=='DNF')&(data['distances']>=20)&(data['distances']<=100)
                if road!='all':mask&=data['roads']==road
                a.extend(data['adv'][mask]);b.extend(data['mc'][mask]);an.extend(data['normalized'][mask]);bn.extend(data['mcn'][mask]);ep.extend(data['epids'][mask])
            if a:
                windowstats.append(dict(road=road,half=half,DNF_episodes=len(set(ep)),raw=signs(np.array(a),np.array(b)),actual_centered=signs(np.array(an),np.array(bn)),inconclusive_small_episode_count=len(set(ep))<3))
    # Samecontemporaneous actor/Jacobian, no optimizer, no policy evaluation.
    import torch
    from retry.ppo275_model import create,STD
    actor,_=create();gradient_records=[]
    for batch,data in batchdata.items():
        mask=(data['outcomes']=='DNF')&(data['distances']>=20)&(data['distances']<=100)
        if not mask.any():continue
        checkpoint=R/'stage275/checkpoint2.pt' if batch==3 else T/f'checkpoint{batch-1}.pt'
        actor.load_state_dict(torch.load(checkpoint)['actor']);tx=torch.as_tensor(data['z']['x'],dtype=torch.float64);z=torch.as_tensor(data['z']['latent'],dtype=torch.float64);mu=actor(tx)
        assert torch.max(abs(mu-torch.tensor(data['z']['old_mu']))).item()<1e-12
        lp=-.5*((z-mu)/STD).pow(2).sum(1)-3*np.log(STD)-1.5*np.log(2*np.pi)
        for road in list(set(data['roads'][mask]))+['all']:
            m=mask.copy()
            if road!='all':m&=data['roads']==road
            idx=np.flatnonzero(m);a=torch.tensor(data['normalized'][idx]);b=torch.tensor(data['mcn'][idx]);sel=torch.tensor(idx)
            ga=torch.autograd.grad((lp[sel]*a).mean(),actor.parameters(),retain_graph=True)
            gb=torch.autograd.grad((lp[sel]*b).mean(),actor.parameters(),retain_graph=True)
            va=torch.cat([g.ravel() for g in ga]).detach().numpy();vb=torch.cat([g.ravel() for g in gb]).detach().numpy();norma=np.linalg.norm(va);normb=np.linalg.norm(vb)
            gradient_records.append(dict(batch=batch,road=road,half='early' if batch<=33 else 'late',samples=len(idx),
                parameter_gradient_cosine=float(va@vb/(norma*normb)) if norma*normb>1e-16 else None,MC_to_GAE_gradient_norm_ratio=float(normb/norma) if norma>1e-12 else None))
    gradient_summary=[]
    for road in list(np.unique(ROAD))+['all']:
        for half in ['early','late','all']:
            rows=[r for r in gradient_records if r['road']==road and (half=='all' or r['half']==half) and r['parameter_gradient_cosine'] is not None]
            if rows:gradient_summary.append(dict(road=road,half=half,rollouts=len(rows),cosine_median=float(np.median([r['parameter_gradient_cosine'] for r in rows])),cosine_negative_fraction=float(np.mean([r['parameter_gradient_cosine']<0 for r in rows])),norm_ratio_median=float(np.median([r['MC_to_GAE_gradient_norm_ratio'] for r in rows]))))
    global_metric=calibration['all']['episode_balanced'];trigger=global_metric['RMSE']>.5 and abs(global_metric['bias_value_minus_return'])>.25 and calibration['complete']['episodes']>=10 and calibration['DNF']['episodes']>=10
    contrast=dict(executed=False,trigger_passed=trigger)
    if trigger:
        testids=[]
        for road in np.unique(ROAD):
            for half in ['early','late']:
                subset=np.unique(E[(ROAD==road)&(HALF==half)]);testids.extend(subset[4::5].tolist())
        test=np.isin(E,testids);train=~test;predictions=[];metrics=[];fitwall=[]
        for features in [X,H]:
            tick=time.perf_counter();mean,std,coef=ridge(features[train],Y[train],weights[train]);fitwall.append(time.perf_counter()-tick)
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
        contrast=dict(executed=True,trigger_passed=True,input_dimensions=[28,79],predictor='scalar affine ridge lambda1',train_episodes=len(np.unique(E[train])),test_episodes=len(testids),test_samples=int(test.sum()),test_metrics=metrics,
            history_relative_RMSE_improvement=float(improvement),paired_episode_delta_MSE_CI95=ci,history_support_passed=improvement>=.05 and ci[1]<0,fit_wall_s=fitwall,strata=strata,
            scope='Episodeheldout within same6TRAIN and changinghistoricalpolicies; not unseenroad or policy performance',new_policy_updates=0)
        q=D/'heldout-predictions-private.npz';np.savez_compressed(q,episode=testE,observed_return=testY,current=predictions[0],history=predictions[1]);q.chmod(0o600);save(D/'episode-split-private.json',dict(test_episode_ids=testids,paired_episode_losses=per))
    cutsummary=[]
    for road in list(np.unique(ROAD))+['all']:
        rows=[r for r in cut_records if road=='all' or r['road']==road]
        if rows:cutsummary.append(dict(road=road,cut_episodes=len(rows),cut_samples=sum(r['prefix_actions'] for r in rows),prefix_length_min=int(min(r['prefix_actions'] for r in rows)),prefix_length_median=float(np.median([r['prefix_actions'] for r in rows])),prefix_length_max=int(max(r['prefix_actions'] for r in rows)),bootstrap_value_mean=float(np.mean([r['bootstrap_value'] for r in rows])),GAE_bootstrap_contribution_prefix_mean=float(np.mean([r['GAE_bootstrap_contribution_mean'] for r in rows])),GAE_bootstrap_last20_mean=float(np.mean([r['GAE_bootstrap_last20_mean'] for r in rows])),terminal_unobserved=True))
    summary=dict(stage=277,source='62TRAINrollouts3..64 only',terminal_episodes=len(ids),terminal_samples=len(Y),critic_calibration=calibration,DNF_window_signs=windowstats,DNF_window_initial_surrogate_parameter_gradients=gradient_summary,
        cut_summary=cutsummary,history_predictor_contrast=contrast,lambda_terminal_decay_reference={str(k):.95**k for k in [20,50,100]},native_actions=0,model_physics=0,policy_updates=0,wall_s=time.perf_counter()-started,CPU_s=time.process_time()-cpu,
        research_remaining=5069,reserve_used=0,champion_changed=False,screen_HOLDOUT_SEALED_used=False,
        limitations=['ObservedMC is realized return,not noisefreeconditionalexpectedvalue. Complete/DNF conditionalbias alone doesnot prove criticwrong.','Gradient comparison is matchedoldpolicy initialsurrogate with sameGAEnormalizer,not actualmulti-epochPPO/Adam step or performance causality.','No futureterminal forcuts; samplecorrelation accounted at episode split/bootstrap; sparse road/halfDNF cells inconclusive.'])
    save(D/'analysis.json',summary);save(D/'cut-records-private.json',cut_records);save(D/'gradient-records-private.json',gradient_records);save(D/'GAE-normalizers-private.json',chunks)
    save(G/'retry/credit277_result.json',summary);(G/'retry/credit277_result.json').chmod(0o644)
    print('277done:',dict(terminal_episodes=len(ids),terminal_samples=len(Y),critic=global_metric,contrast=contrast,native=0),flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
