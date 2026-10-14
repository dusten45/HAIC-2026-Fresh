"""Road-held-out legal-state identifiability; immutable cached GT labels only."""
import argparse,gzip,json,time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.hud248_features import decode

NAMES=['ego_longitudinal_m_s','ego_right_lateral_m_s','yaw_CCW_rad_s','front0_joint_angle_rad']


def targets(snapshot):
    h=snapshot['hull'];angle=h['angle'];vx,vy=h['velocity'];c,s=np.cos(angle),np.sin(angle)
    return np.array([-s*vx+c*vy,c*vx+s*vy,h['angular_velocity'],snapshot['wheels'][0]['joint']['angle']],float)


def ridge(x,y,roads):
    n=len(x);w=np.array([n/(len(set(roads))*roads.count(r)) for r in roads])
    mean=np.average(x,axis=0,weights=w)
    std=np.maximum(np.sqrt(np.average((x-mean)**2,axis=0,weights=w)),1e-6)
    z=np.c_[(x-mean)/std,np.ones(n)];penalty=np.eye(z.shape[1]);penalty[-1,-1]=0
    beta=np.linalg.solve(z.T@(w[:,None]*z)+penalty,z.T@(w[:,None]*y))
    return mean,std,beta


def metrics(y,pred,roads):
    w=np.array([1/(len(set(roads))*roads.count(r)) for r in roads])
    e=pred-y;mse=w@(e*e)
    return {name:dict(RMSE=float(np.sqrt(mse[i])),MAE=float(w@abs(e[:,i])),bias=float(w@e[:,i])) for i,name in enumerate(NAMES)}


def run(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage318';p=read(D/'plan.json')
    assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for q,h in p['input_sha256'].items():assert sha(q)==h,q
    assert not (D/'opening.json').exists();save(D/'opening.json',dict(epoch=time.time()))
    start,cpu=time.perf_counter(),time.process_time();data={};provenance=[];exclusions=[];fullrows={}
    for road in p['roads']:
        F=R/'stage306/collection'/road
        trace=[json.loads(s) for s in (F/'trace-private.jsonl').read_text().splitlines()]
        cache=np.load(F/'observations-actions-private.npz');obs=cache['observations'];actions=cache['actions']
        assert len(obs)==len(actions)==len(trace)
        assert np.array_equal(obs[1:,:3],obs[:-1,1:])
        snapshots={}
        with gzip.open(F/'full-source-captures-private.jsonl.gz','rt') as f:
            for line in f:
                r=json.loads(line);step=r['step'];assert step not in snapshots
                try:
                    y=targets(r['snapshot'])
                    if not np.isfinite(y).all():raise ValueError('nonfinite target')
                    snapshots[step]=dict(features=r['features'],action=r['final296'],previous_action=r['previous_action'],
                        y=y,time=r['snapshot']['actual_time'],damage=r['snapshot']['damage'])
                except (KeyError,ValueError,TypeError) as error:
                    exclusions.append(dict(road=road,step=step,reason='target_not_recoverable:'+type(error).__name__))
        first_collision=next((r['step'] for r in trace if r['collision']),None)
        result=read(F/'result.json');assert not result['technical_error'] and not result['censored']
        eligible=[];time_errors=[];history=[0,0,0];X=[];H=[];Y=[];PROXY=[];SPEED=[];POST=[];OUT=[]
        for i,row in enumerate(trace):
            step=i+1;assert row['step']==step
            if step not in snapshots:
                exclusions.append(dict(road=road,step=step,reason='missing_snapshot'));continue
            r=snapshots[step]
            if r['features']!=row['features'] or r['action']!=row['action'] or not np.array_equal(actions[i],np.array(row['action'],np.float32)):
                exclusions.append(dict(road=road,step=step,reason='preaction_source_mismatch'));continue
            if i and (step-1 not in snapshots or abs(r['time']-snapshots[step-1]['time']-.08)>1e-9):
                exclusions.append(dict(road=road,step=step,reason='unknown_or_non80ms_interval'));continue
            if i:
                assert r['previous_action']==actions[i-1].tolist()
                assert abs(r['damage']-trace[i-1]['damage'])<1e-12
                time_errors.append(abs(r['time']-snapshots[step-1]['time']-.08))
            x=np.array(row['features'],float);past=np.zeros((3,16));act=np.zeros((3,3));mask=np.zeros(3)
            for lag in [1,2,3]:
                j=i-lag
                if j<0:continue
                if all(k+1 in snapshots and abs(snapshots[k+1]['time']-snapshots[k]['time']-.08)<=1e-9 for k in range(j+1,i+1)):
                    past[lag-1]=trace[j]['features'];act[lag-1]=actions[j];mask[lag-1]=1;history[lag-1]+=1
            hud=decode(obs[i,-1]);proxy=np.array([x[4],0.,hud[5],hud[4]])
            X.append(x);H.append(np.r_[x,past.ravel(),act.ravel(),mask]);Y.append(r['y']);PROXY.append(proxy)
            SPEED.append([x[3],x[4],np.hypot(r['y'][0],r['y'][1]),-x[7]])
            POST.append(first_collision is not None and step>first_collision);OUT.append(result['completed']);eligible.append(step)
        data[road]=dict(x=np.array(X),h=np.array(H),y=np.array(Y),proxy=np.array(PROXY),speed=np.array(SPEED),post=np.array(POST),complete=np.array(OUT),steps=np.array(eligible))
        fullrows[road]=snapshots
        provenance.append(dict(road=road,cached_pixels=len(obs),snapshot_rows=len(snapshots),eligible_rows=len(eligible),
            previous_lag_valid_rows=history,maximum_interval_error_s=max(time_errors,default=0.),
            cached_stack_shift_exact=True,features_actions_previous_action_and_pre_damage_exact=True,
            completed=result['completed'],first_collision_post_action=first_collision))
        print(json.dumps(provenance[-1]),flush=True)
    assert all(len(data[r]['x'])>0 for r in p['roads'])
    # Duplicate300 T2950 is a cross-check, never another fitted episode.
    cross=[json.loads(s) for s in (R/'stage300/T2950_296/trace-private.jsonl').read_text().splitlines()];cross_error=0.
    for row in cross:
        if row['step'] not in fullrows['T2950']:continue
        old=row['pre'];snapshot=dict(hull=dict(angle=old['angle'],velocity=old['velocity'],angular_velocity=old['yaw_rate']),wheels=[dict(joint=dict(angle=old['wheel_joint_angles'][0]))])
        cross_error=max(cross_error,float(np.max(abs(targets(snapshot)-fullrows['T2950'][row['step']]['y']))))
        assert row['features']==fullrows['T2950'][row['step']]['features']
    held={};folds=[]
    for road in p['roads']:
        train_roads=[r for r in p['roads'] if r!=road]
        yy=np.vstack([data[r]['y'] for r in train_roads]);rr=[r for r in train_roads for _ in data[r]['y']]
        predictions={}
        for arm,key in [('A','x'),('B','h')]:
            xx=np.vstack([data[r][key] for r in train_roads]);mean,std,beta=ridge(xx,yy,rr)
            query=data[road][key];pred=np.c_[(query-mean)/std,np.ones(len(query))]@beta;predictions[arm]=pred
            q=D/(road+'-'+arm+'-ridge-private.npz');np.savez(q,mean=mean,std=std,beta=beta);q.chmod(0o600)
        held[road]=predictions
        folds.append(dict(road=road,train_rows=len(yy),test_rows=len(data[road]['y']),metrics={a:metrics(data[road]['y'],pred,[road]*len(pred)) for a,pred in predictions.items()}))
    y=np.vstack([data[r]['y'] for r in p['roads']]);roads=[r for r in p['roads'] for _ in data[r]['y']]
    pred={a:np.vstack([held[r][a] for r in p['roads']]) for a in ['A','B']}
    pred['direct_proxy']=np.vstack([data[r]['proxy'] for r in p['roads']])
    speed=np.vstack([data[r]['speed'] for r in p['roads']]);post=np.concatenate([data[r]['post'] for r in p['roads']]);complete=np.concatenate([data[r]['complete'] for r in p['roads']])
    overall={a:metrics(y,v,roads) for a,v in pred.items()};strata=[]
    for name,mask in [('completed_trajectory',complete),('DNF_trajectory',~complete),('before_first_collision_or_no_collision',~post),('after_first_collision',post)]:
        if mask.any():
            rr=[r for r,m in zip(roads,mask) if m]
            strata.append(dict(stratum=name,roads=len(set(rr)),rows=int(sum(mask)),metrics={a:metrics(y[mask],v[mask],rr) for a,v in pred.items()}))
    weights=np.array([1/(len(set(roads))*roads.count(r)) for r in roads]);proxyextra={}
    for name,estimate,target in [('legacy_norm_speed_vs_physical_norm',speed[:,0],speed[:,2]),('HUD_norm_speed_vs_physical_norm',speed[:,1],speed[:,2]),('negative_previous_command_vs_front_joint',speed[:,3],y[:,3])]:
        e=estimate-target;proxyextra[name]=dict(RMSE=float(np.sqrt(weights@(e*e))),MAE=float(weights@abs(e)),bias=float(weights@e))
    q=D/'heldout-predictions-private.npz';np.savez(q,GT=y,A=pred['A'],B=pred['B'],proxy=pred['direct_proxy'],post_collision=post,complete=complete);q.chmod(0o600)
    pub=dict(stage=318,targets=p['targets'],input_recipe=p['input_recipe'],ridge_recipe=p['ridge_recipe'],
        provenance=provenance,total_eligible_rows=len(y),six_road_LOO=True,folds=folds,road_balanced=overall,strata=strata,
        proxy_definitions=dict(longitudinal='Current legal HUD scalar norm speed treated as forward speed; not an exact longitudinal observation.',lateral='Zero null prediction, not a measured lateral proxy.',yaw='Unchanged248 current-pixel HUD yaw decoder',joint='Unchanged248 current-pixel front0 joint-angle decoder'),
        extra_proxy_metrics=proxyextra,excluded_rows_by_reason={reason:sum(e['reason']==reason for e in exclusions) for reason in set(e['reason'] for e in exclusions)},
        additional_source_scope=dict(stage300_T2950_duplicate_target_max_abs_difference=cross_error,stage300_duplicate_used_for_fitting=False,
            stage300_T2954_outside_fixed_six_not_added=True,stage315_actual_rows_without_preGT_excluded=1685,stage315_foreign_trajectory_GT_transferred=False),
        cost=dict(new_native=0,new_source_physics_ticks=0,new_actor_calls=0,new_PPO_updates=0,scalar_target_columns=4,
            ridge_multioutput_solves=12,extra_full_fit_or_input_search=0,new_paid_resources=0,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu),
        research_remaining=2969,final_reserved_actions=84000,champion296_maintained=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,
        promotion=False,automatic_extension=False,
        limitations=['Linear state prediction, not a certified sufficient observation or control-performance gain.',
            'Six known296 TRAIN trajectories; one DNF trajectory, correlated adjacent observations.',
            'B adds past features, executed actions and masks jointly; no component attribution or longer history tested.',
            'No GT angle or velocity enters legal predictors or proxy decoder.'])
    save(D/'exclusions-private.json',exclusions);save(D/'analysis-receipt.json',pub['cost']);save(G/'retry/state318_result.json',pub)
    print(json.dumps(dict(total_rows=len(y),metrics=overall,proxy=proxyextra,cross_error=cross_error,cost=pub['cost'])),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
