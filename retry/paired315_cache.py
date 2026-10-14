"""Fixed road-held-out paired 1-NN vs ridge and296; saved-motion diagnosis.

No simulator/actor imports, new labels, hyperparameter search or native calls.
Teacher pairs and the full TRAIN index stay private.
"""
import argparse
import json
from pathlib import Path
import time

import numpy as np

from retry.path271_run import read, save, sha
from retry.preview286_control import rollout


def normalize(x,roads):
    weights=np.array([len(x)/(len(set(roads))*roads.count(r)) for r in roads])
    mean=np.average(x,axis=0,weights=weights)
    std=np.maximum(np.sqrt(np.average((x-mean)**2,axis=0,weights=weights)),1e-6)
    return mean,std,weights


def nearest(train, query):
    # Stable first index for exact distance ties. k=1, all16 legal features.
    return np.argmin(np.sum((query[:,None,:]-train[None,:,:])**2,axis=2),axis=1)


def error(pred,y):
    e=np.mean(np.abs(pred-y),axis=0)
    return dict(gas_MAE=float(e[0]),brake_MAE=float(e[1]),joint_L1_MAE=float(e.sum()),
        both_positive_fraction=float(np.mean((pred[:,0]>0)&(pred[:,1]>0))))


def body_diagnosis(path):
    rows=[json.loads(s) for s in path.read_text().splitlines()]
    first=next((r['step'] for r in rows if r['collision']),None)
    errors=[];side=[];joint=[];collision_error=None;count=0
    for r in rows:
        pre,post=r['pre'],r['post']
        dt=post['time']-pre['time']
        if not np.isclose(dt,.08,rtol=0,atol=1e-9):
            continue
        angle=pre['angle'];c,s=np.cos(angle),np.sin(angle)
        delta=np.array(post['position'])-pre['position']
        local=np.array([c*delta[0]+s*delta[1],-s*delta[0]+c*delta[1]])
        predicted=rollout([r['action'][0]],r['features'][4],r['features'][7])[0]
        distance=float(np.linalg.norm(local-predicted));count+=1
        if r['step']==first:
            collision_error=distance
        if first is None or r['step']<first:
            errors.append(distance)
            vx,vy=pre['velocity'];side.append(abs(c*vx+s*vy))
            joint.append(abs(-pre['wheel_joint_angles'][0]-r['features'][7]))
    return dict(role=path.parent.name,first_collision_action=first,
        one_step_kinematic_rollouts=count,kinematic_substeps=4*count,
        pre_first_collision_or_all_rows=len(errors),
        local_position_error_m=dict(mean=float(np.mean(errors)),p95=float(np.percentile(errors,95)),maximum=float(max(errors))),
        actual_body_lateral_speed_m_s=dict(mean=float(np.mean(side)),p95=float(np.percentile(side,95)),maximum=float(max(side))),
        command_memory_vs_actual_joint_rad=dict(p95=float(np.percentile(joint,95)),maximum=float(max(joint))),
        first_collision_endpoint_error_m=collision_error,
        scope='Frozen286 single-step motion, legal speed/action/memory only. GT pose/velocity/joint are labels. Not collision prediction or a continuous hull certificate.')


def run(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage315'
    p=read(D/'plan.json')
    assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for q,h in p['input_sha256'].items():
        assert sha(q)==h,q
    assert not (D/'cache-opening.json').exists()
    save(D/'cache-opening.json',dict(epoch=time.time()))
    start,cpu=time.perf_counter(),time.process_time()
    x=[];y=[];base=[];roads=[]
    for road in p['roads']:
        rows=read(R/'stage306/collection'/road/'teacher-labels-private.json')
        x.extend(r['features'] for r in rows)
        y.extend(r['teacher'][1:] for r in rows)
        base.extend(r['base'][1:] for r in rows)
        roads.extend([road]*len(rows))
    x,y,base=map(np.asarray,[x,y,base]);folds=[]
    for road in p['roads']:
        held=np.array([r==road for r in roads]);keep=~held
        train_roads=[r for r in roads if r!=road]
        mean,std,w=normalize(x[keep],train_roads)
        train=(x[keep]-mean)/std;query=(x[held]-mean)/std
        index=nearest(train,query)
        paired=y[keep][index]
        Z=np.c_[train,np.ones(sum(keep))]
        penalty=np.eye(17);penalty[-1,-1]=0.
        weights=np.linalg.solve(Z.T@(w[:,None]*Z)+penalty,Z.T@(w[:,None]*(y[keep]-base[keep])))
        ridge=np.clip(base[held]+np.clip(np.c_[query,np.ones(sum(held))]@weights,-.5,.5),0,1)
        folds.append(dict(road=road,held_rows=int(sum(held)),train_rows=int(sum(keep)),
            baseline296=error(base[held],y[held]),ridge_same_fold=error(ridge,y[held]),paired_1NN=error(paired,y[held])))
        save(D/(road+'-held-predictions-private.json'),dict(paired=paired.tolist(),ridge=ridge.tolist(),nearest_indices=index.tolist()))
    summary={k:float(np.mean([r[k]['joint_L1_MAE'] for r in folds])) for k in ['baseline296','ridge_same_fold','paired_1NN']}
    passed=summary['paired_1NN']<summary['baseline296'] and summary['paired_1NN']<summary['ridge_same_fold']
    mean,std,w=normalize(x,roads)
    # Store the fixed TRAIN index only; no label generation or optimization.
    np.savez(D/'paired-index-private.npz',mean=mean,std=std,x=(x-mean)/std,y=y)
    (D/'paired-index-private.npz').chmod(0o600)
    body=[body_diagnosis(Path(q)) for q in p['body_traces']]
    pub=dict(stage=315,rule=p['rule'],difference_from_prior=p['difference_from_prior'],
        preregistered_offline_gate=p['offline_gate'],native_gate=p['native_gate'],
        road_leave_one_out=folds,mean_road_joint_L1_MAE=summary,
        offline_gate_passed=bool(passed),body_diagnosis=body,
        teacher_rows=len(x),teacher_both_positive_fraction=float(np.mean((y[:,0]>0)&(y[:,1]>0))),
        cost=dict(new_native=0,new_source_physics_ticks=0,new_teacher_queries=0,
            small_ridge_control_solves=len(folds),new_classifier_or_neural_fits=0,
            nearest_neighbor_indices_built=1,kinematic_rollouts=sum(r['one_step_kinematic_rollouts'] for r in body),
            kinematic_substeps=sum(r['kinematic_substeps'] for r in body),
            new_actor_calls=0,new_paid_resources=0,cache_wall_s=time.perf_counter()-start,cache_CPU_s=time.process_time()-cpu),
        limitations=['Teacher first/future steering mismatch remains; no teacher validity or policy benefit established.',
            'This is predictive road-held-out label error, not causal removal of simultaneous pedals or closed-loop performance.',
            'Frozen286 one-step residual diagnosis does not validate a swept-body model or justify repeating its controller.'],
        champion296_maintained=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,
        automatic_extension=False,promotion=False)
    save(D/'cache-receipt.json',pub)
    save(G/'retry/paired315_result.json',pub)
    print(json.dumps(dict(gate=passed,summary=summary,body=body,cost=pub['cost'])),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True)
    run(a.parse_args().private_root.resolve())
