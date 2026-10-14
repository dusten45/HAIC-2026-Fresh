"""Observed-action HUD transition identification; cached six-road LORO only."""
import argparse
import datetime
import gzip
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

from retry.hud248_features import decode
from retry.path271_run import read, save, sha


def plain(x):
    if isinstance(x, dict):return {k:plain(v) for k,v in x.items()}
    if isinstance(x, (list,tuple)):return [plain(v) for v in x]
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    return x


def motor_baseline(state,actions):
    initial=np.clip(state[:,2],-.4,.4);joint=initial.copy()
    for _ in range(4):joint+=np.clip(50*(-actions[:,0]-joint),-3,3)*.02
    out=state.copy();out[:,2]=joint
    out[:,1]+=state[:,0]/3.24*(np.tan(joint)-np.tan(initial))
    return out


def metrics(error,roads,mask):
    rr=np.asarray(roads)[mask];e=error[mask]
    if not len(e):return dict(rows=0,roads=0)
    w=np.array([1/(len(set(rr))*sum(rr==r)) for r in rr])
    result=dict(rows=len(e),roads=len(set(rr)),RMSE=np.sqrt(w@(e*e)),MAE=w@abs(e),bias=w@e,max_abs=abs(e).max(0))
    for name,p in [('p95_abs',.95),('p99_abs',.99)]:
        values=[]
        for k in range(3):
            order=np.argsort(abs(e[:,k]),kind='stable');index=min(np.searchsorted(np.cumsum(w[order]),p),len(order)-1)
            values.append(float(abs(e[order[index],k])))
        result[name]=values
    return plain(result)


def fit(x,y,roads):
    weights=np.array([len(x)/(len(set(roads))*sum(roads==r)) for r in roads])
    mean=np.average(x,axis=0,weights=weights)
    scale=np.maximum(np.sqrt(np.average((x-mean)**2,axis=0,weights=weights)),1e-6)
    z=np.c_[(x-mean)/scale,np.ones(len(x))];penalty=np.eye(7);penalty[-1,-1]=0
    matrix=z.T@(weights[:,None]*z)+penalty;rhs=z.T@(weights[:,None]*y)
    beta=np.linalg.solve(matrix,rhs);residual=float(np.max(abs(matrix@beta-rhs)));assert residual<1e-8
    return dict(mean=mean,scale=scale,beta=beta),residual


def run(R,recover=False):
    G=Path(__file__).resolve().parent.parent;D=R/'stage325';p=read(D/'plan.json')
    assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for q,h in p['input_hashes'].items():assert sha(q)==h,q
    assert not (D/'cost.json').exists()
    assert not list(D.glob('*-ridge-private.npz'))
    if recover:assert (D/'prefit-input-contract-correction.json').exists()
    else:assert not (D/'opening.json').exists()
    assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00'))
    save(D/('corrected-code-receipt.json' if recover else 'code-receipt.json'),dict(script_sha256=sha(Path(__file__))))
    save(D/('corrected-opening.json' if recover else 'opening.json'),dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    start,cpu=time.perf_counter(),time.process_time()
    decoder_path=R/'stage306/zero-replay/O0/package/retry/hud_feedback.py'
    spec=importlib.util.spec_from_file_location('frozen_speed_decoder325',decoder_path);speed_decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(speed_decoder)
    inputs=[];state0=[];state1=[];truth0=[];truth1=[];roads=[];before=[];contact=[];after=[];provenance=[]
    for road in p['roads']:
        F=R/'stage306/collection'/road;z=np.load(F/'observations-actions-private.npz');obs=z['observations'];commands=z['actions']
        rows=[json.loads(s) for s in (F/'trace-private.jsonl').read_text().splitlines()]
        with gzip.open(F/'full-source-captures-private.jsonl.gz','rt') as f:snapshots={r['step']:r for r in map(json.loads,f)}
        assert len(obs)==len(commands)==len(rows)==len(snapshots)
        assert np.array_equal(obs[1:,:3],obs[:-1,1:])
        first=next((r['step'] for r in rows if r['collision']),None);states=[];gt=[];times=[];fallback_count=0;cached_speed_different=0
        for i,row in enumerate(rows):
            r=snapshots[i+1];assert row['step']==i+1 and r['features']==row['features'] and r['final296']==row['action']
            assert np.array_equal(commands[i],np.array(row['action'],np.float32))
            if i:assert r['previous_action']==commands[i-1].tolist()
            image=obs[i,-1];speed=speed_decoder.decode_feedback_speed(image,row['features'][3])
            cached_speed_different+=speed!=row['features'][4]
            if speed!=row['features'][4]:assert row['features'][0]==1 and row['features'][4]==row['features'][3]
            signature=np.rint(image[74:83,11:13]*255).astype(np.uint8).tobytes();fallback_count+=signature not in speed_decoder.TEMPLATES
            hud=decode(image);states.append([speed,hud[5],hud[4]])
            hull=r['snapshot']['hull'];gt.append([np.linalg.norm(hull['velocity']),hull['angular_velocity'],r['snapshot']['wheels'][0]['joint']['angle']]);times.append(r['snapshot']['actual_time'])
        states=np.array(states);gt=np.array(gt);times=np.array(times)
        assert np.isfinite(states).all() and np.isfinite(gt).all();assert np.max(abs(np.diff(times)-.08))<1e-9
        n=len(states)-1;inputs.extend(np.c_[states[:-1],commands[:-1]]);state0.extend(states[:-1]);state1.extend(states[1:]);truth0.extend(gt[:-1]);truth1.extend(gt[1:]);roads.extend([road]*n)
        steps=np.arange(1,n+1);before.extend(steps<first if first is not None else np.ones(n,bool));contact.extend(steps==first if first is not None else np.zeros(n,bool));after.extend(steps>first if first is not None else np.zeros(n,bool))
        provenance.append(dict(road=road,preaction_rows=len(states),eligible_transitions=n,terminal_endpoint_unavailable=1,first_contact_action=first,
                               maximum_interval_error_s=float(np.max(abs(np.diff(times)-.08))),stack_shift_exact=True,features_commands_previous_action_exact=True,
                               speed_decode_direct_each_frame=True,cached_feature4_different_rows=int(cached_speed_different),speed_fallback_rows=int(fallback_count)))
        print(json.dumps(provenance[-1]),flush=True)
    x=np.array(inputs);s0=np.array(state0);s1=np.array(state1);g0=np.array(truth0);g1=np.array(truth1);roads=np.array(roads)
    assert x.shape==(1748,6);delta=s1-s0;held=np.zeros_like(delta);folds=[];support=[]
    for road in p['roads']:
        assert time.perf_counter()-start<p['max_analysis_wall_s'];train=roads!=road;test=~train
        model,residual=fit(x[train],delta[train],roads[train]);held[test]=np.c_[(x[test]-model['mean'])/model['scale'],np.ones(sum(test))]@model['beta']
        q=D/(road+'-ridge-private.npz');np.savez(q,**model);q.chmod(0o600)
        low=x[train,3:].min(0);high=x[train,3:].max(0);outside=(x[test,3:]<low)|(x[test,3:]>high)
        support.append(dict(road=road,rows=int(test.sum()),action_min=x[test,3:].min(0),action_max=x[test,3:].max(0),action_p05=np.quantile(x[test,3:],.05,axis=0),
                            action_p95=np.quantile(x[test,3:],.95,axis=0),action_std=x[test,3:].std(0),both_pedals_positive=int(sum((x[test,4]>0)&(x[test,5]>0))),
                            heldout_actions_outside_TRAIN_marginal_range=int(sum(outside.any(1))),outside_by_channel=outside.sum(0),TRAIN_action_min=low,TRAIN_action_max=high))
        folds.append(dict(road=road,train_rows=int(train.sum()),test_rows=int(test.sum()),normal_equation_max_residual=residual))
    predictions=dict(persistence=s0,residual_ridge=s0+held,motor_kinematic=motor_baseline(s0,x[:,3:]))
    masks=dict(all=np.ones(len(x),bool),before_first_contact_or_no_contact=np.array(before),first_contact_interval=np.array(contact),after_first_contact=np.array(after))
    scores={label:{arm:metrics(pred-s1,roads,mask) for arm,pred in predictions.items()} for label,mask in masks.items()}
    physical={label:{arm:metrics((pred-s0)-(g1-g0),roads,mask) for arm,pred in predictions.items()} for label,mask in masks.items()}
    decoder={label:dict(next_state_error=metrics(s1-g1,roads,mask),transition_noise=metrics((s1-s0)-(g1-g0),roads,mask)) for label,mask in masks.items()}
    perroad={road:{label:{arm:metrics(pred-s1,roads,mask&(roads==road)) for arm,pred in predictions.items()} for label,mask in masks.items()} for road in p['roads']}
    decomposition_max=0.
    for pred in predictions.values():
        decomposition_max=max(decomposition_max,float(abs(((pred-s0)-(g1-g0))-((pred-s1)+((s1-s0)-(g1-g0)))).max()))
    assert decomposition_max<1e-12
    supported=bool(np.all(np.array(scores['all']['residual_ridge']['RMSE'])<np.array(scores['all']['persistence']['RMSE'])))
    q=D/'heldout-predictions-private.npz';np.savez(q,x=x,observed_next=s1,GT_now=g0,GT_next=g1,roads=roads,**predictions);q.chmod(0o600)
    for q,h in p['input_hashes'].items():assert sha(q)==h,q
    budget=read(R/'project-effective-budget-v331.json');assert budget['research_remaining']==395
    assert not any(n.startswith(('core','env_wrapper','Box2D')) for n in sys.modules)
    cost=dict(stage=325,new_wrapper_actions=0,new_native=0,new_source_physics_ticks=0,new_actor_calls=0,new_PPO=0,new_paid_resources=0,
              ridge_fits=6,full_final_fits=0,model_coefficients_per_fold=21,normalization_values_per_fold=12,
              prefit_input_contract_corrections=int(recover),failed_attempt_native=0,failed_attempt_fits=0,failed_attempt_CPU_unrecorded=bool(recover),
              analysis_wall_s=time.perf_counter()-start,analysis_CPU_s=time.process_time()-cpu,research_remaining=395,final_reserved_actions=84000,
              actual_cumulative_wrapper_actions=budget['actual_cumulative_wrapper_actions'],B_operating_cap=budget['B_operating_cap'])
    public=dict(stage=325,duplicate_found=False,prior_scope=p['novelty'],state_names=p['state_names'],action_names=p['action_names'],inputs=p['inputs'],target=p['targets'],
                recipe=p['primary_baseline'],secondary_baseline=p['secondary_baseline'],gate=p['gate'],gate_supported=supported,
                transitions=len(x),provenance=provenance,folds=folds,action_support=support,road_balanced_HUD_next_errors=scores,
                per_road_HUD_next_errors=perroad,GT_posthoc_physical_delta_errors=physical,GT_posthoc_decoder_errors=decoder,
                validation=dict(error_decomposition_max_abs=decomposition_max,GT_never_fit_input_or_target=True,all_input_hashes_unchanged=True,motor_target_sign_minus_steer=True,
                                terminal_future_endpoints_not_synthesized=True,road_separation=True),cost=cost,
                decision='One-step observed-action HUD premise supported; no off-policy planning/controller/native authorization.' if supported else 'Fixed residual dynamics did not improve all three HUD targets over persistence; no controller/native expansion.',
                limitations=['Six known296TRAIN on-policy trajectories, adjacent transitions correlated, no action interventions or independent generalization.',
                             'Marginal action ranges are not joint state-action support, causal action sensitivity or counterfactual calibration.',
                             'Norm speed is not longitudinal velocity; motor/kinematic comparator ignores slip, damage and wheel forces.',
                             'HUD target prediction includes quantization/decoder errors; GT diagnostics are posthoc only. No recursive rollout, translation or collision accuracy claimed.'],
                champion296_maintained=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False)
    public=plain(public);assert cost['analysis_wall_s']<p['max_analysis_wall_s']
    save(D/'analysis-summary-private.json',public);save(G/'retry/dynamics325_result.json',public);save(D/'cost.json',cost)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==325 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(dict(gate_supported=supported,all=scores['all'],physical_all=physical['all'],cost=cost)),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--private-root',type=Path,required=True);parser.add_argument('--recover-prefit',action='store_true')
    args=parser.parse_args();run(args.private_root.resolve(),args.recover_prefit)
