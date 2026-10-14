"""Observed-terminal buffer only: offset control and training-only critic state."""
import argparse
import json
from pathlib import Path
import time

import numpy as np

from retry.path271_run import read, save, sha


def ridge(x,y,w):
    w=w*len(w)/w.sum()
    mean=np.average(x,axis=0,weights=w)
    std=np.maximum(np.sqrt(np.average((x-mean)**2,axis=0,weights=w)),1e-6)
    z=np.c_[(x-mean)/std,np.ones(len(x))]
    penalty=np.eye(z.shape[1]);penalty[-1,-1]=0.
    beta=np.linalg.solve(z.T@(w[:,None]*z)+penalty,z.T@(w*y))
    return mean,std,beta


def metrics(y,pred,w):
    w=w/w.sum();e=pred-y;mean=lambda a:float(w@a)
    variance=lambda a:mean((a-mean(a))**2)
    mse=mean(e*e);var=variance(y)
    return dict(samples=len(y),MSE=mse,RMSE=float(np.sqrt(mse)),bias=mean(e),
        EV=1-variance(e)/var if var>1e-12 else None)


def run(R):
    D=R/'stage316';G=Path(__file__).resolve().parent.parent
    plan=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for q,h in plan['input_sha256'].items():assert sha(q)==h,q
    assert not (D/'opening.json').exists();save(D/'opening.json',dict(epoch=time.time()))
    start,cpu=time.perf_counter(),time.process_time();T=R/'stage276'
    source=read(T/'training-outcome-private.json')['episodes']
    cases=read(T/'training-plan.json')['cases']
    counts=dict(complete=0,DNF=0,collection_cut=0,technical=0)
    X=[];P=[];Y=[];S=[];E=[];ROAD=[];HALF=[];OUT=[];W=[]
    accounting_max=interval_max=0.;nonterminal_checked=first_excluded=0;source_rows=cut_rows=0
    for episode in source:
        if episode['technical_interrupted']:
            counts['technical']+=1;continue
        if not (episode['completed'] or episode['actual_DNF']):
            assert episode['collection_cut'];counts['collection_cut']+=1
            cut_rows+=episode['valid_samples'];continue
        outcome='complete' if episode['completed'] else 'DNF';counts[outcome]+=1
        F=T/f"episode{episode['serial']:03d}_{episode['road']}"
        z=dict(np.load(F/'buffer-private.npz'))
        journal=[json.loads(s) for s in (F/'step-journal-private.jsonl').read_text().splitlines()]
        n=episode['valid_samples'];source_rows+=n
        assert n==len(journal)==len(z['x']) and z['x'].shape==(n,28)
        assert z['done'][-1] and not z['done'][:-1].any() and not z['cut'].any()
        assert all(np.array_equal(np.array(r['buffer']['x']),x) for r,x in zip(journal,z['x']))
        assert np.array_equal(np.array([r['buffer']['reward'] for r in journal]),z['reward'])
        assert all(r['row']['step']==i+1 and r['row']['reward']==z['reward'][i] for i,r in enumerate(journal))
        tiles=cases[episode['road']]['road_point_count']
        assert episode['total_tiles']==tiles
        # All pre-k intervals are nonterminal. Source wrapper has skip4; the
        # stored nonterminal reward algebra independently verifies their time.
        assert 4*(n-1)<episode['raw_step_ticks']<=4*n
        rows=[r['row'] for r in journal]
        visited=np.array([r['visited'] for r in rows],float)
        damage=np.array([r['damage'] for r in rows],float)
        assert np.all(np.diff(visited)>=0) and np.all(np.diff(damage)>=-1e-12)
        assert all(not r['terminal'] for r in rows[:-1]) and rows[-1]['terminal']
        if n>2:
            inferred_dt=(np.diff(visited[:-1])/tiles-z['reward'][1:-1])*160
            err=float(np.max(abs(inferred_dt-.08)))
            interval_max=max(interval_max,err);assert err<1e-9
            nonterminal_checked+=n-2
        returns=np.cumsum(z['reward'][::-1])[::-1]
        assert abs(returns[0]-episode['expected_terminal_return'])<1e-9
        # k>=2: only row k-1, never the current POST-step row or reset guess.
        first_excluded+=1
        progress=visited[:-1]/tiles
        time_fraction=.08*np.arange(1,n)/160
        privileged=np.c_[progress,damage[:-1],time_fraction]
        offset=progress-time_fraction
        final_target=returns[1:]+offset
        err=float(np.max(abs(final_target-episode['expected_terminal_return'])))
        accounting_max=max(accounting_max,err);assert err<1e-9
        X.append(z['x'][1:]);P.append(privileged);Y.append(returns[1:]);S.append(final_target)
        E.extend([episode['serial']]*(n-1));ROAD.extend([episode['road']]*(n-1))
        HALF.extend(['early' if episode['batch']<=33 else 'late']*(n-1));OUT.extend([outcome]*(n-1))
        W.extend([1/(n-1)]*(n-1))
    assert counts==dict(complete=167,DNF=64,collection_cut=62,technical=0),counts
    X=np.vstack(X);P=np.vstack(P);Y=np.concatenate(Y);S=np.concatenate(S)
    E,ROAD,HALF,OUT,W=map(np.asarray,[E,ROAD,HALF,OUT,W])
    assert len(Y)==54147 and source_rows==54378 and first_excluded==231
    testids=[]
    for road in np.unique(ROAD):
        for half in ['early','late']:
            testids.extend(np.unique(E[(ROAD==road)&(HALF==half)])[4::5].tolist())
    old=read(R/'stage277/episode-split-private.json')['test_episode_ids']
    assert sorted(testids)==sorted(old) and len(testids)==43
    test=np.isin(E,testids);train=~test
    assert len(np.unique(E[train]))==188
    predictions={};fit_cost=[]
    for name,x,target in [('A',X,Y),('B',X,S),('C',np.c_[X,P],S)]:
        tick,cp=time.perf_counter(),time.process_time()
        mean,std,beta=ridge(x[train],target[train],W[train])
        pred=np.c_[(x[test]-mean)/std,np.ones(sum(test))]@beta
        if name!='A':pred=pred-P[test,0]+P[test,2]
        predictions[name]=pred
        q=D/(name+'-predictor-private.npz');np.savez(q,mean=mean,std=std,beta=beta);q.chmod(0o600)
        fit_cost.append(dict(arm=name,wall_s=time.perf_counter()-tick,CPU_s=time.process_time()-cp))
    ty=Y[test];te=E[test];tw=W[test]
    overall={name:metrics(ty,pred,tw) for name,pred in predictions.items()}
    strata=[]
    masks=[('complete',OUT[test]=='complete'),('DNF',OUT[test]=='DNF'),('early',HALF[test]=='early'),('late',HALF[test]=='late')]
    masks += [(o+'_'+h,(OUT[test]==o)&(HALF[test]==h)) for o in ['complete','DNF'] for h in ['early','late']]
    for label,mask in masks:
        if mask.any():
            strata.append(dict(stratum=label,episodes=len(np.unique(te[mask])),metrics={name:metrics(ty[mask],pred[mask],tw[mask]) for name,pred in predictions.items()}))
    per=[]
    for eid in np.unique(te):
        m=te==eid
        per.append(dict(episode=int(eid),MSE={name:float(np.mean((pred[m]-ty[m])**2)) for name,pred in predictions.items()}))
    rng=np.random.default_rng(316);draws=rng.integers(0,len(per),size=(500,len(per)));paired=[]
    for left,right in [('C','A'),('C','B'),('B','A')]:
        delta=np.array([r['MSE'][left]-r['MSE'][right] for r in per]);boot=np.mean(delta[draws],axis=1)
        paired.append(dict(comparison=left+'-'+right,episodes=len(per),mean_delta_MSE=float(delta.mean()),
            median_delta_MSE=float(np.median(delta)),p10_p90_delta_MSE=np.percentile(delta,[10,90]).tolist(),
            fraction_left_lower=float(np.mean(delta<0)),paired_bootstrap_resamples=500,
            bootstrap_seed=316,CI95_mean_delta_MSE=np.percentile(boot,[2.5,97.5]).tolist()))
    q=D/'heldout-predictions-private.npz';np.savez(q,episode=te,G=ty,**predictions);q.chmod(0o600)
    save(D/'paired-episode-losses-private.json',per)
    better=overall['C']['MSE']<overall['A']['MSE'] and overall['C']['MSE']<overall['B']['MSE']
    pub=dict(stage=316,arms=plan['arms'],recipe=plan['recipe'],
        provenance=dict(terminal_episodes=231,complete=167,DNF=64,excluded_collection_cut=62,excluded_cut_rows=cut_rows,
            excluded_technical=0,terminal_source_rows=source_rows,excluded_unknown_reset_first_rows=first_excluded,
            usable_rows=len(Y),train_episodes=188,heldout_episodes=43,train_rows=int(sum(train)),heldout_rows=int(sum(test)),
            exact277_split_verified=True,immutable_training_tile_counts=True,all_legal28_buffer_and_journal_rows_exact=True),
        accounting=dict(nonterminal_intervals_checked=nonterminal_checked,maximum_inferred_dt_error_s=interval_max,
            maximum_final_score_identity_error=accounting_max,pre_state_source='journal row k-1 only for k>=2',
            time_source='0.08*(k-1), source skip4 and nonterminal reward-delta verification',first_row_reset_progress_guessed=False),
        heldout_episode_balanced=overall,paired_episode_losses=paired,strata=strata,
        C_lower_than_both=bool(better),no_minimum_improvement_threshold=True,
        cost=dict(new_native=0,new_source_physics_ticks=0,new_PPO_updates=0,new_actor_calls=0,
            scalar_ridge_fits=3,fit_cost=fit_cost,new_paid_resources=0,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu),
        research_remaining=2195,final_reserved_actions=84000,reserve_used=0,
        champion296_maintained=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,
        next_PPO_executed=False,promotion=False,
        limitations=['Realized reward suffix is not a noise-free conditional value.',
            'Same six TRAIN roads and changing historical policies; episode split is not unseen-road generalization.',
            'A training-only asymmetric critic prediction gain is not an actor or policy improvement.',
            'No future outcome, terminal reason, episode length, road or policy identifier enters any predictor.'])
    save(D/'analysis-receipt.json',pub['cost']);save(G/'retry/asymmetric316_result.json',pub)
    print(json.dumps(dict(provenance=pub['provenance'],accounting=pub['accounting'],metrics=overall,paired=paired,C_lower_than_both=bool(better),cost=pub['cost'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',type=Path,required=True)
    run(p.parse_args().private_root.resolve())
