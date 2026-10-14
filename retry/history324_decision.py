"""Causal history ablation for cached real intervention gains; no policy execution."""
import argparse
import datetime
import hashlib
import time
from pathlib import Path

import numpy as np

from retry.gain283_ridge import CLASSES, choose, predict
from retry.path271_run import read, save, sha


def fit_history(x, y):
    mean=x.mean(0);std=x.std(0);std=np.where(std<1e-12,1.,std)
    z=np.c_[(x-mean)/std,np.ones(len(x))];penalty=np.eye(z.shape[1]);penalty[-1,-1]=0.
    weights=np.linalg.solve(z.T@z+penalty,z.T@y)
    residual=np.max(abs((z.T@z+penalty)@weights-z.T@y))
    assert residual<1e-9
    return dict(mean=mean.tolist(),std=std.tolist(),weights=weights.tolist()),float(residual)


def run(R,recover=False):
    G=Path(__file__).resolve().parent.parent;D=R/'stage324';p=read(D/'plan.json')
    assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for q,h in p['input_hashes'].items():assert sha(q)==h,q
    if recover:
        assert (D/'before-fit-recovery.json').exists()
        assert not (D/'models-predictions-private.json').exists() and not (D/'cost.json').exists()
    else:
        assert not (D/'opening.json').exists()
    assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00'))
    save(D/('recovery-code-receipt.json' if recover else 'code-receipt.json'),dict(script_sha256=sha(Path(__file__))))
    save(D/('recovery-opening.json' if recover else 'opening.json'),dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    start,cpu=time.perf_counter(),time.process_time()
    source=read(G/'retry/outcome282_result.json');states=source['states'];old=read(R/'stage283/targets-models-private.json')
    returns=np.array(old['returns']);y=np.array(old['targets']);assert np.array_equal(y,returns[:,1:]-returns[:,0,None])
    data={};materialized={}
    for road in p['roads']:
        F=R/'stage251/training'/road;z=np.load(F/'cache-private.npz')
        data[road]={k:z[k].copy() for k in z.files};materialized[road]=read(F/'materialized.json')
        obs=data[road]['observations'];assert np.array_equal(obs[1:,:3],obs[:-1,1:])
        print('324 immutable cache aligned: '+road,flush=True)
    X=[];H=[];provenance=[];groups=[];actual_target_count=0
    for i,state in enumerate(states):
        road,q=state['road'],state['anchor'];assert p['states'][i]==dict(road=road,anchor=q)
        z=data[road];current=z['features'][q-1];assert np.array_equal(current,np.array(old['features'][i]))
        out=state['outcomes']['gas_upper'];F=R/f"stage{out['source_stage']}"/road/f'{q}_gas_upper'
        rows=read(F/'trace-private.json');assert rows[q-1]['step']==q
        time_errors=[];past=[];commands=[];mask=[]
        m=materialized[road]
        # actual[k] is POST action k+1, hence PRE row k+2. Sparse
        # snapshots are PRE their named query. Use complete measured times.
        times=np.r_[m['snapshots']['1']['actual_time'],[r['time'] for r in m['actual']]]
        for step,snapshot in m['snapshots'].items():
            assert abs(times[int(step)-1]-snapshot['actual_time'])<1e-12
        for lag in [1,2,3]:
            j=q-1-lag;assert j>=0
            a,b=times[j],times[j+1]
            time_errors.append(abs(b-a-.08));assert abs(b-a-.08)<1e-9
            r=rows[j];assert r['step']==j+1 and r['phase']=='prefix'
            assert np.array_equal(z['features'][j],np.array(r['features']))
            assert np.array_equal(z['commands'][j],np.array(r['action'],np.float32))
            # Outcome282 stores the post-step frame hash, unlike its pre-step features.
            assert hashlib.sha256(z['observations'][j+1].tobytes()).hexdigest()==r['obs_sha256']
            past.extend(z['features'][j]);commands.extend(z['commands'][j]);mask.append(1.)
        assert rows[q-1]['features']==current.tolist()
        assert rows[q-1]['base']==z['commands'][q-1].tolist()
        assert hashlib.sha256(z['observations'][q-1].tobytes()).hexdigest()==rows[q-2]['obs_sha256']
        X.append(current);H.append(np.r_[current,past,commands,mask]);groups.append(road)
        base=state['outcomes']['baseline'];assert returns[i,0]==2-base['lap_ms']/1000/160
        for index,macro in enumerate(CLASSES[1:],1):
            outcome=state['outcomes'][macro];F=R/f"stage{outcome['source_stage']}"/road/f'{q}_{macro}'
            r=read(F/'result.json');assert r['comparable'] and not r['censored']
            assert r['completed']==outcome['completed'] and r['actual_DNF']==outcome['actual_DNF']
            value=2-r['lap_ms']/1000/160 if r['completed'] else r['visited']/r['total_tiles']-1
            assert r['completed'] or r['actual_DNF'];assert value==returns[i,index];actual_target_count+=1
        provenance.append(dict(road=road,anchor=q,causal_lags_verified=3,current_macro_action_excluded=True,
                               maximum_interval_error_s=max(time_errors),prefix_feature_action_pixel_hash_exact=True))
    X=np.array(X);H=np.array(H);groups=np.array(groups);assert H.shape==(24,76)
    current=np.array(old['predicted_gains']);history=np.zeros_like(current);models={};folds=[]
    for road in p['roads']:
        assert time.perf_counter()-start<p['max_analysis_wall_s']
        train=groups!=road;test=~train;assert train.sum()==20 and test.sum()==4
        reproduced=predict(old['models_by_fold'][road],X[test]);assert np.array_equal(reproduced,current[test])
        model,residual=fit_history(H[train],y[train]);models[road]=model;history[test]=predict(model,H[test])
        folds.append(dict(heldout_road=road,train_states=20,test_states=4,normal_equation_max_residual=residual,
                          current_saved_prediction_exact=True,training_road_ids_disjoint_test=True))
    choices=dict(current16=choose(current),history76=choose(history),baseline=np.zeros(24,int))
    def score(ch):
        details=[]
        for i,c in enumerate(ch):
            st=states[i];r=st['outcomes'][CLASSES[int(c)]]
            details.append(dict(road=st['road'],anchor=st['anchor'],choice=CLASSES[int(c)],completed=r['completed'],
                                actual_DNF=r['actual_DNF'],lap_delta_ms=r['lap_delta_ms'],return_delta=float(returns[i,c]-returns[i,0])))
        complete=[r for r in details if r['completed']]
        return dict(completions=len(complete),actual_DNF=sum(r['actual_DNF'] for r in details),
                    mean_official_return_gain=float(np.mean([r['return_delta'] for r in details])),
                    common_completed_mean_time_delta_ms=float(np.mean([r['lap_delta_ms'] for r in complete])),
                    abstain=int(sum(c==0 for c in ch)),choice_distribution={label:int(sum(ch==j)) for j,label in enumerate(CLASSES)},
                    improved=sum(r['return_delta']>0 for r in details),tied=sum(r['return_delta']==0 for r in details),
                    worsened=sum(r['return_delta']<0 for r in details),rows=details)
    scores={arm:score(ch) for arm,ch in choices.items()}
    assert scores['current16']['completions']==21 and scores['baseline']['completions']==24
    differences=int(sum(choices['current16']!=choices['history76']))
    eligible=bool(scores['history76']['completions']==24 and scores['history76']['mean_official_return_gain']>0 and
                  scores['history76']['mean_official_return_gain']>scores['current16']['mean_official_return_gain'] and differences>0)
    for fold in folds:
        mask=groups==fold['heldout_road'];fold['choices_differ']=int(sum(choices['current16'][mask]!=choices['history76'][mask]))
        fold['gain_prediction_RMSE']={a:float(np.sqrt(np.mean((v[mask]-y[mask])**2))) for a,v in [('current16',current),('history76',history)]}
        fold['selected_outcomes']={a:dict(completions=sum(scores[a]['rows'][i]['completed'] for i in np.flatnonzero(mask)),
                                        mean_return_gain=float(np.mean([scores[a]['rows'][i]['return_delta'] for i in np.flatnonzero(mask)]))) for a in ['current16','history76']}
    save(D/'models-predictions-private.json',dict(current_features=X.tolist(),history_features=H.tolist(),targets=y.tolist(),
                                                 returns=returns.tolist(),models=models,predicted_current=current.tolist(),predicted_history=history.tolist()))
    for q,h in p['input_hashes'].items():assert sha(q)==h,q
    budget=read(R/'project-effective-budget-v331.json');assert budget['research_remaining']==395
    cost=dict(stage=324,new_wrapper_actions=0,new_native=0,new_source_physics_ticks=0,new_actor_calls=0,new_PPO=0,
              history_ridge_fits=6,current_ridge_fits=0,full_final_fits=0,teacher_queries=0,new_paid_resources=0,
              analysis_wall_s=time.perf_counter()-start,analysis_CPU_s=time.process_time()-cpu,research_remaining=395,
              before_fit_field_recovery=2 if recover else 0,failed_attempt_native=0,failed_attempt_fits=0,
              failed_attempt_CPU_unrecorded=bool(recover),
              final_reserved_actions=84000,actual_cumulative_wrapper_actions=budget['actual_cumulative_wrapper_actions'],B_operating_cap=budget['B_operating_cap'])
    assert cost['analysis_wall_s']<p['max_analysis_wall_s'];save(D/'cost.json',cost)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(read_row.get('stage')==324 for read_row in map(__import__('json').loads,ledger.read_text().splitlines()))
    with ledger.open('a') as f:f.write(__import__('json').dumps(cost)+'\n')
    public=dict(stage=324,hypothesis=p['hypothesis'],candidates=p['candidates'],inputs=dict(A=p['input_A'],B=p['input_B']),
                target=p['targets'],recipe=p['recipe'],gate=p['gate'],gate_passed=eligible,
                actual_targets_verified=actual_target_count,states=24,roads=6,provenance=provenance,folds=folds,
                scores=scores,action_selection_differences=differences,
                gain_prediction_RMSE={a:float(np.sqrt(np.mean((v-y)**2))) for a,v in [('current16',current),('history76',history)]},
                decision='Gate passed only for known240 one-shot lookup; no automatic native authorization.' if eligible else 'Reject this fixed history extension for decision selection; no native expansion.',
                cost=cost,champion296_maintained=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,
                limitations=['24 dependent snapshots on six known240 TRAIN roads, four per road; no new296 or repeated-policy performance.',
                             'Current16 already includes tracker and controller memory; this ablates additional three-step summaries, not memory versus no memory.',
                             'No teacher action regression or state reconstruction; actual terminal gains include failure cost, but this is finite data and fixed linear prediction.',
                             'Three-step feature/action history added jointly; no attribution to individual history component or longer recurrent architecture.'])
    save(G/'retry/history324_result.json',public)
    print(__import__('json').dumps(dict(scores={a:{k:v for k,v in s.items() if k!='rows'} for a,s in scores.items()},differences=differences,gate_passed=eligible,cost=cost)),flush=True)


def recover_export(R):
    """Recalculate metrics from the six stored fits without solving or charging again."""
    G=Path(__file__).resolve().parent.parent;D=R/'stage324';start,cpu=time.perf_counter(),time.process_time()
    assert not (G/'retry/history324_result.json').exists()
    p=read(D/'plan.json');saved=read(D/'models-predictions-private.json');states=read(G/'retry/outcome282_result.json')['states']
    for q,h in p['input_hashes'].items():assert sha(q)==h,q
    X=np.array(saved['current_features']);H=np.array(saved['history_features']);y=np.array(saved['targets']);returns=np.array(saved['returns'])
    groups=np.array([r['road'] for r in states]);current=np.array(saved['predicted_current']);history=np.array(saved['predicted_history'])
    old=read(R/'stage283/targets-models-private.json');assert np.array_equal(current,np.array(old['predicted_gains']))
    assert np.array_equal(y,returns[:,1:]-returns[:,0,None])
    # Independently recreate all76 causal columns from immutable legal caches.
    cache={road:np.load(R/'stage251/training'/road/'cache-private.npz') for road in p['roads']}
    for i,st in enumerate(states):
        z=cache[st['road']];j=st['anchor']-1
        expected=np.r_[z['features'][j],np.concatenate([z['features'][j-k] for k in [1,2,3]]),
                       np.concatenate([z['commands'][j-k] for k in [1,2,3]]),np.ones(3)]
        assert np.array_equal(expected,H[i]) and np.array_equal(X[i],H[i,:16])
    folds=[]
    for road in p['roads']:
        train=groups!=road;test=~train;model=saved['models'][road]
        assert np.array_equal(predict(model,H[test]),history[test])
        mean=H[train].mean(0);std=H[train].std(0);std=np.where(std<1e-12,1.,std)
        assert np.array_equal(mean,np.array(model['mean'])) and np.array_equal(std,np.array(model['std']))
        z=np.c_[(H[train]-mean)/std,np.ones(sum(train))];penalty=np.eye(77);penalty[-1,-1]=0.
        residual=float(np.max(abs((z.T@z+penalty)@np.array(model['weights'])-z.T@y[train])));assert residual<1e-9
        folds.append(dict(heldout_road=road,train_states=20,test_states=4,normal_equation_max_residual=residual,training_road_ids_disjoint_test=True))
    choices=dict(current16=choose(current),history76=choose(history),baseline=np.zeros(24,int));scores={}
    for arm,ch in choices.items():
        rows=[]
        for i,c in enumerate(ch):
            st=states[i];r=st['outcomes'][CLASSES[int(c)]]
            rows.append(dict(road=st['road'],anchor=st['anchor'],choice=CLASSES[int(c)],completed=r['completed'],actual_DNF=r['actual_DNF'],
                             lap_delta_ms=r['lap_delta_ms'],return_delta=float(returns[i,c]-returns[i,0])))
        completed=[r for r in rows if r['completed']]
        scores[arm]=dict(completions=len(completed),actual_DNF=sum(r['actual_DNF'] for r in rows),
                         mean_official_return_gain=float(np.mean([r['return_delta'] for r in rows])),
                         common_completed_mean_time_delta_ms=float(np.mean([r['lap_delta_ms'] for r in completed])),
                         abstain=int(sum(ch==0)),choice_distribution={c:int(sum(ch==j)) for j,c in enumerate(CLASSES)},
                         improved=sum(r['return_delta']>0 for r in rows),tied=sum(r['return_delta']==0 for r in rows),worsened=sum(r['return_delta']<0 for r in rows),rows=rows)
    differences=int(sum(choices['current16']!=choices['history76']))
    eligible=bool(scores['history76']['completions']==24 and scores['history76']['mean_official_return_gain']>0 and scores['history76']['mean_official_return_gain']>scores['current16']['mean_official_return_gain'] and differences>0)
    for fold in folds:
        mask=groups==fold['heldout_road'];fold['choices_differ']=int(sum(choices['current16'][mask]!=choices['history76'][mask]))
        fold['gain_prediction_RMSE']={a:float(np.sqrt(np.mean((v[mask]-y[mask])**2))) for a,v in [('current16',current),('history76',history)]}
        fold['selected_outcomes']={a:dict(completions=sum(scores[a]['rows'][i]['completed'] for i in np.flatnonzero(mask)),mean_return_gain=float(np.mean([scores[a]['rows'][i]['return_delta'] for i in np.flatnonzero(mask)]))) for a in ['current16','history76']}
    cost=read(D/'cost.json');assert cost['history_ridge_fits']==6 and cost['new_native']==0
    receipt=dict(export_recovery=True,new_fits=0,new_native=0,all76_input_columns_recreated_exact=True,stored_model_predictions_exact=True,
                 normal_equations_verified=True,all_input_hashes_preserved=True,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu)
    public=dict(stage=324,hypothesis=p['hypothesis'],candidates=p['candidates'],inputs=dict(A=p['input_A'],B=p['input_B']),target=p['targets'],recipe=p['recipe'],gate=p['gate'],gate_passed=eligible,
                actual_targets_verified=96,states=24,roads=6,folds=folds,scores=scores,action_selection_differences=differences,
                gain_prediction_RMSE={a:float(np.sqrt(np.mean((v-y)**2))) for a,v in [('current16',current),('history76',history)]},
                validation=dict(causal_lags_per_state=3,prefix_feature_action_post_pixel_hash_exact=True,current_pre_pixel_is_prior_post_pixel=True,complete_post_action_times_aligned_with_sparse_pre_snapshots=True,original_current_predictions_reproduced_exact=True),
                decision='Gate passed only for known240 one-shot lookup; no automatic native authorization.' if eligible else 'Reject this fixed history extension for decision selection; no native expansion.',cost=cost,export_recovery=receipt,
                champion296_maintained=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False,
                limitations=['24 snapshots on six known240 TRAIN roads, not296 or repeated-policy performance.',
                             'Current16 already has tracker/controller memory; additional3step feature/action history added jointly.',
                             'Fixed lambda1 linear action-gain predictor, not teacher regression/state reconstruction or a general memory impossibility result.'])
    save(D/'export-recovery-receipt.json',receipt);save(G/'retry/history324_result.json',public)
    print(__import__('json').dumps(dict(scores={a:{k:v for k,v in s.items() if k!='rows'} for a,s in scores.items()},differences=differences,gate_passed=eligible,export=receipt)),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--private-root',type=Path,required=True);parser.add_argument('--recover-before-fit',action='store_true')
    parser.add_argument('--recover-export',action='store_true')
    args=parser.parse_args()
    if args.recover_export:recover_export(args.private_root.resolve())
    else:run(args.private_root.resolve(),args.recover_before_fit)
