"""Postselected frozen hybrid: open-loop observed-action HUD rollouts only."""
import argparse
import datetime
import json
import time
from pathlib import Path

import numpy as np

from retry.dynamics325_fit import motor_baseline,plain
from retry.path271_run import read,save,sha


def ridge_step(state,action,models):
    x=np.c_[state,action]
    return np.mean([state+np.c_[(x-m['mean'])/m['scale'],np.ones(len(x))]@m['beta'] for m in models],axis=0)


def step(state,action,models,arm):
    if arm=='persistence':return state.copy()
    if arm=='ridge':return ridge_step(state,action,models)
    motor=motor_baseline(state,action)
    if arm=='motor':return motor
    assert arm=='hybrid'
    ridge=ridge_step(state,action,models);out=ridge.copy();out[:,1:]=motor[:,1:]
    return out


def rollout(initial,actions,models,arm,low,high):
    """No observation, target, fallback, contact or per-model trajectory input."""
    state=initial.copy();n,horizon,_=actions.shape
    diag=dict(windows=n,predicted_step_exposures=n*horizon,negative_speed_pre_steps=0,negative_speed_predicted_steps=0,
              negative_speed_endpoints=0,nonfinite_predicted_steps=0,nonfinite_endpoints=0,
              input_outside_TRAIN_range_steps=0,input_outside_by_channel=np.zeros(6,int),windows_any_input_outside=0,
              motor_initial_joint_clip_steps=0,motor_velocity_saturated_ticks=0,motor_ticks_evaluated=0,
              output_clipping_steps=0,requantization_steps=0,predicted_joint_outside_point4_steps=0)
    outside_windows=np.zeros(n,bool);minimum=np.inf;maximum_joint=0.
    for j in range(horizon):
        action=actions[:,j];x=np.c_[state,action];outside=(x<low)|(x>high)|~np.isfinite(x)
        diag['negative_speed_pre_steps']+=int(sum(state[:,0]<0));diag['input_outside_TRAIN_range_steps']+=int(sum(outside.any(1)))
        diag['input_outside_by_channel']+=outside.sum(0);outside_windows|=outside.any(1)
        if arm in ['motor','hybrid']:
            joint=np.clip(state[:,2],-.4,.4);diag['motor_initial_joint_clip_steps']+=int(sum((state[:,2]<-.4)|(state[:,2]>.4)))
            for _ in range(4):
                request=50*(-action[:,0]-joint);diag['motor_velocity_saturated_ticks']+=int(sum((request<-3)|(request>3)))
                joint+=np.clip(request,-3,3)*.02;diag['motor_ticks_evaluated']+=n
        with np.errstate(over='ignore',invalid='ignore'):state=step(state,action,models,arm)
        finite=np.isfinite(state).all(1);diag['nonfinite_predicted_steps']+=int(sum(~finite));diag['negative_speed_predicted_steps']+=int(sum(state[:,0]<0))
        diag['predicted_joint_outside_point4_steps']+=int(sum(abs(state[:,2])>.4))
        if np.isfinite(state[:,0]).any():minimum=min(minimum,float(state[np.isfinite(state[:,0]),0].min()))
        if np.isfinite(state[:,2]).any():maximum_joint=max(maximum_joint,float(abs(state[np.isfinite(state[:,2]),2]).max()))
    diag['negative_speed_endpoints']=int(sum(state[:,0]<0));diag['nonfinite_endpoints']=int(sum(~np.isfinite(state).all(1)))
    diag['windows_any_input_outside']=int(sum(outside_windows));diag['minimum_finite_predicted_speed']=minimum;diag['maximum_finite_abs_joint']=maximum_joint
    return state,plain(diag)


def metrics(errors,weights):
    w=np.array(weights);w=w/w.sum();e=np.asarray(errors);out=dict(windows=len(e),MAE=[],RMSE=[],bias=[],p95_abs=[],p99_abs=[],max_abs=[],nonfinite_by_channel=[])
    for k in range(3):
        values=e[:,k];finite=np.isfinite(values);absolute=abs(values);bad=int(sum(~finite));out['nonfinite_by_channel'].append(bad)
        out['MAE'].append(float(w@absolute) if not bad else 'INF');out['RMSE'].append(float(np.sqrt(w@(values*values))) if not bad else 'INF')
        out['bias'].append(float(w@values) if not bad else 'undefined');out['max_abs'].append(float(absolute.max()) if not bad else 'INF')
        # Nonfinite predictions stay failures in the full window denominator.
        scored=np.where(finite,absolute,np.inf);order=np.argsort(scored,kind='stable');cdf=np.cumsum(w[order])
        for name,q in [('p95_abs',.95),('p99_abs',.99)]:
            value=scored[order[min(np.searchsorted(cdf,q),len(order)-1)]];out[name].append(float(value) if np.isfinite(value) else 'INF')
    return out


def aggregate(entries):
    roads=set(r['road'] for r in entries);weights=[];errors=[]
    for r in entries:
        trajectories=sum(v['road']==r['road'] for v in entries);weights.extend(np.ones(len(r['error']))/(len(roads)*trajectories*len(r['error'])))
        errors.extend(r['error'])
    return metrics(np.array(errors),weights)


def run(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage328';p=read(D/'plan.json')
    assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for q,h in p['input_hashes'].items():assert sha(q)==h,q
    assert not (D/'opening.json').exists()
    assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00'))
    save(D/'opening.json',dict(epoch=time.time(),code_sha256=sha(Path(__file__))))
    start,cpu=time.perf_counter(),time.process_time();training=np.load(R/'stage325/heldout-predictions-private.npz');all_results=[];h1=[];source_counts=[]
    # Independent old-speed/sign algebra check; the hybrid does not overwrite it.
    test_state=np.array([[20.,.1,.02],[5.,-.3,-.2]]);test_action=np.array([[.2,0.,.5],[-.1,.6,.02]])
    joint=np.clip(test_state[:,2],-.4,.4);old=joint.copy()
    for _ in range(4):joint+=np.clip(50*(-test_action[:,0]-joint),-3,3)*.02
    expected=test_state.copy();expected[:,2]=joint;expected[:,1]+=test_state[:,0]/3.24*(np.tan(joint)-np.tan(old))
    assert np.array_equal(expected,motor_baseline(test_state,test_action))
    for case in p['cases']:
        assert time.perf_counter()-start<p['max_wall_s'];road,trajectory=case['road'],case['arm'];key=road+'_'+trajectory
        z=np.load(R/'stage326'/(key+'-predictions-private.npz'));x=z['x'];states=np.vstack([x[0,:3],z['actual_next']])
        assert np.array_equal(states[:-1],x[:,:3]) and np.isfinite(states).all()
        models=[]
        for path in case['model_paths']:
            m=np.load(path);models.append({name:m[name].copy() for name in m.files})
        fit=training['roads']!=road if road in p['models'] else np.ones(len(training['x']),bool)
        low=training['x'][fit].min(0);high=training['x'][fit].max(0)
        # Every model receives this same state/input at each step, not its own rollout.
        r=step(x[:,:3],x[:,3:],models,'ridge');m=step(x[:,:3],x[:,3:],models,'motor');h=step(x[:,:3],x[:,3:],models,'hybrid')
        assert np.array_equal(r,z['residual_ridge']) and np.array_equal(m,z['motor_kinematic'])
        assert np.array_equal(h[:,0],r[:,0]) and np.array_equal(h[:,1:],m[:,1:])
        h1.append(dict(road=road,trajectory=trajectory,rows=len(x),ridge_motor326_exact=True,hybrid_speed_exact_ridge=True,hybrid_yaw_joint_exact_motor=True))
        source_counts.append(dict(road=road,trajectory=trajectory,available_states=len(states),available_actions=len(x),missing_last_endpoint=1))
        for horizon in p['horizons']:
            count=len(x)-horizon+1;assert count>0
            action_windows=np.stack([x[j:j+count,3:] for j in range(horizon)],axis=1)
            initial=states[:count].copy();target=states[horizon:horizon+count].copy();saved=dict(initial=initial,actions=action_windows,actual_endpoint=target)
            for arm in p['arms']:
                pred,diag=rollout(initial,action_windows,models,arm,low,high);saved[arm]=pred
                if horizon==1:
                    expected_h1={'persistence':x[:,:3],'ridge':r,'motor':m,'hybrid':h}[arm];assert np.array_equal(pred,expected_h1)
                error=pred-target;all_results.append(dict(road=road,trajectory=trajectory,horizon=horizon,arm=arm,error=error,diagnostics=diag))
            q=D/(key+'-H'+str(horizon)+'-rollouts-private.npz');np.savez_compressed(q,**saved);q.chmod(0o600)
        print(json.dumps(dict(road=road,trajectory=trajectory,H1_H3_H12_windows=[len(x)-h+1 for h in p['horizons']],H1_identity=True)),flush=True)
    scores={};byroad={};diagnostics=[]
    for result in all_results:
        diagnostics.append({k:result[k] for k in ['road','trajectory','horizon','arm','diagnostics']})
    for horizon in p['horizons']:
        scores[str(horizon)]={};byroad[str(horizon)]={}
        for group,roads in [('primary_O0_O2',['O0','O2']),('secondary_S1',['S1'])]:
            scores[str(horizon)][group]={arm:aggregate([r for r in all_results if r['horizon']==horizon and r['road'] in roads and r['arm']==arm]) for arm in p['arms']}
        for road in ['O0','O2','S1']:
            byroad[str(horizon)][road]={arm:aggregate([r for r in all_results if r['horizon']==horizon and r['road']==road and r['arm']==arm]) for arm in p['arms']}
    diag_summary={}
    count_fields=['windows','predicted_step_exposures','negative_speed_pre_steps','negative_speed_predicted_steps','negative_speed_endpoints','nonfinite_predicted_steps','nonfinite_endpoints',
                  'input_outside_TRAIN_range_steps','windows_any_input_outside','motor_initial_joint_clip_steps','motor_velocity_saturated_ticks','motor_ticks_evaluated','output_clipping_steps','requantization_steps','predicted_joint_outside_point4_steps']
    for horizon in p['horizons']:
        diag_summary[str(horizon)]={}
        for arm in p['arms']:
            rr=[r['diagnostics'] for r in all_results if r['horizon']==horizon and r['arm']==arm]
            diag_summary[str(horizon)][arm]={field:sum(r[field] for r in rr) for field in count_fields}
            diag_summary[str(horizon)][arm].update(input_outside_by_channel=np.sum([r['input_outside_by_channel'] for r in rr],axis=0),
                                                  minimum_finite_predicted_speed=min(r['minimum_finite_predicted_speed'] for r in rr),maximum_finite_abs_joint=max(r['maximum_finite_abs_joint'] for r in rr))
    for q,h in p['input_hashes'].items():assert sha(q)==h,q
    budget=read(R/'project-effective-budget-v333.json');assert budget['research_remaining']==0
    cost=dict(stage=328,new_wrapper_actions=0,new_native=0,new_source_physics_ticks=0,new_fits=0,new_actor_calls=0,new_PPO=0,new_paid_resources=0,
              predictive_step_exposures=sum(r['diagnostics']['predicted_step_exposures'] for r in all_results),analysis_wall_s=time.perf_counter()-start,analysis_CPU_s=time.process_time()-cpu,
              research_remaining=0,final_reserved_actions=84000,actual_cumulative_wrapper_actions=budget['actual_cumulative_wrapper_actions'],B_operating_cap=budget['B_operating_cap'])
    public=dict(stage=328,post_selection=p['post_selection'],hybrid=p['hybrid'],recursion=p['recursion'],windows=p['windows'],extra327=p['extra327'],
                state_names=read(R/'stage325/plan.json')['state_names'],metrics=scores,per_road=byroad,teacher_forced_one_step=dict(definition='ActualcurrentHUDeveryrow,one-stepactualaction;identicaltoH1open-loop,notH3/12teacherforced.',metrics=scores['1']),
                source_counts=source_counts,H1_verification=h1,diagnostics_summary=diag_summary,per_trajectory_diagnostics=diagnostics,cost=cost,
                support_definition='Training marginal minmax ofstate3+action3 at everypredictedinput; necessarynotjointstatesupport. No support/negative/nonfinite window filtering.',
                quantiles='Weighted empirical CDF inverse,equalroadthenequaltrajectorymass;nonfiniteprediction failures retained withINFfullwindow metrics.',
                decision='Postselected rollout diagnostic only, no controller/MPC or independent confirmation; no parameters, clipping or requantization changed.',
                limitations=['Overlappingwindows andpreviouslyseen326trajectories;notindependentsamples or freshgeneralization.',
                             'Realbehavioractionsequencesaregivenqueries,notactionsequencesgeneratedfrompredictedstatesorlearnedplanner.',
                             'Motorapproximation ignoresdamage,torque,slip;normspeed isnotlongitudinalstate.',
                             'Missingterminalendpointsremainmissing;327unused andnopersistentlargebrakingrolloutclaimed.'],
                champion296_maintained=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False)
    public=plain(public);assert cost['analysis_wall_s']<p['max_wall_s']
    save(D/'summary-private.json',public);save(G/'retry/hybrid328_result.json',public);save(D/'cost.json',cost)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==328 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(dict(metrics=scores,diagnostics=public['diagnostics_summary'],cost=cost)),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--private-root',type=Path,required=True)
    run(parser.parse_args().private_root.resolve())
