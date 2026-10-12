"""Read-only target/prediction pedal overlap analysis; no fit or simulation.

--prior names the private research root. Only anonymous counts/means are
emitted. Frozen F1 fold trains on F0/F2/F3 and evaluates F1.
"""
import argparse
import json
from pathlib import Path
import time
import numpy as np


def stats(a):
    return dict(rows=len(a),mean_gas=float(a[:,1].mean()),mean_brake=float(a[:,2].mean()),
                both_positive_count=int(np.sum((a[:,1]>0)&(a[:,2]>0))),
                both_positive_fraction=float(np.mean((a[:,1]>0)&(a[:,2]>0))),
                gas_positive_fraction=float(np.mean(a[:,1]>0)),brake_positive_fraction=float(np.mean(a[:,2]>0)))


def analyze(root):
    start,cpu=time.perf_counter(),time.process_time();model=np.load(root/'stage225/head1.npz',allow_pickle=False)
    targets={};predictions={};training=[];training_raw=[]
    for i in range(4):
        c=np.load(root/'stage224'/('F'+str(i))/'cache.npz',allow_pickle=False)
        x=c['features'];base=c['champion'];y=c['teacher']
        residual=np.c_[(x-model['mean'])/model['std'],np.ones(len(x))]@model['weights']
        raw=base.astype(np.float64)+residual
        pred=np.clip(base.astype(np.float64)+np.clip(residual,-.5,.5),[-1,0,0],[1,1,1]).astype(np.float32)
        targets['F'+str(i)]=stats(y);predictions['F'+str(i)]=stats(pred)
        if i!=1:training.append(y);training_raw.append(raw)
    y=np.concatenate(training);raw=np.concatenate(training_raw)
    plan=json.loads((root/'stage226/plan.json').read_text())
    job=next(j for j in plan['jobs'] if j['road']=='F1' and j['variant']=='pedals')
    case_id=job['case']['id']
    full=np.load(root/'stage225/runs'/(case_id+'__S')/'commands-features.npz',allow_pickle=False)['executed']
    pedals=np.load(root/'stage226/runs'/(case_id+'__P')/'commands-features.npz',allow_pickle=False)['executed']
    return dict(stage=227,fold=1,training_roads=['F0','F2','F3'],held_out_road='F1',
        teacher_targets=targets,F1_frozen_head_predictions_on_teacher_observations=predictions,
        training_teacher=stats(y),training_raw_affine_prediction=stats(raw),
        training_unclipped_predicted_mean_minus_target_mean=(raw.mean(0)-y.astype(np.float64).mean(0)).tolist(),
        F1_all_channels_closed_loop225=stats(full),F1_pedals_only_closed_loop226=stats(pedals),
        explanation='Targets are mutually exclusive per row but both channel means are positive. Separate affine ridge outputs with unpenalized bias match training residual means before clipping; no joint pedal mode constraint. Predicted overlap is introduced by the regressor/independent clipping, not copied from overlapping targets. Means alone do not identify a specific conditional mixture or prove a failure cause.',
        training_updates=0,native_actions=0,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prior',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    with args.output.open('x') as f:json.dump(analyze(args.prior),f,indent=2);f.write('\n')
    args.output.chmod(0o600)
