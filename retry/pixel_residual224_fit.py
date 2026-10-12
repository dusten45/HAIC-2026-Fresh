"""Fixed affine ridge residual pilot on four qualified whole DEV roads.

No simulator or GT features are imported. Input caches stay private. Each fold
fits normalization and residual weights on the other three roads only.
"""
import argparse
import json
from pathlib import Path
import time
import numpy as np

FEATURES = ['target_missing','target_x','target_forward','HUD_speed',
            'pedal_feedback_speed','curvature','target_speed','previous_shadow_steer',
            'near_hazard','route_length','path_point_count','obstacle_count',
            'nearest_pixel_hazard_range','champion_steer','champion_gas','champion_brake']
SETTINGS = dict(head='affine_ridge_16_to_3',parameters=51,L2_lambda=1.0,
                intercept_penalty=0.0,solver='float64_closed_form',
                residual_clip=[0.5,0.5,0.5],action_min=[-1.,0.,0.],
                action_max=[1.,1.,1.],sweep=False,
                normalization='train_roads_only_mean_std; std_floor1e-6',
                gate='four_exact_observation_sequence_reproductions_and_shadow_checks',
                judgment='Report each road and macro MAE/RMSE against zero residual; no promotion')


def predict(x, base, mean, std, weights):
    z = np.concatenate(((x-mean)/std,np.ones((len(x),1))),axis=1)
    residual = np.clip(z@weights,-0.5,0.5)
    return np.clip(base+residual,SETTINGS['action_min'],SETTINGS['action_max']).astype(np.float32)


def errors(pred, teacher, mask):
    delta = pred[mask].astype(np.float64)-teacher[mask]
    return dict(count=int(mask.sum()),MAE=np.abs(delta).mean(0).tolist() if len(delta) else None,
                RMSE=np.sqrt((delta*delta).mean(0)).tolist() if len(delta) else None)


def fit(directory, output):
    start,cpu=time.perf_counter(),time.process_time()
    contract=json.loads((directory/'contract.json').read_text())
    assert contract['head_settings']==SETTINGS and contract['features']==FEATURES
    outcome=json.loads((directory/'outcome.json').read_text())
    assert len(outcome['roads'])==4 and all(r['qualified'] for r in outcome['roads'])
    caches=[np.load(directory/('F'+str(i))/'cache.npz') for i in range(4)]
    folds=[]
    for held in range(4):
        t=time.perf_counter();tcpu=time.process_time()
        train=[c for i,c in enumerate(caches) if i!=held]
        x=np.concatenate([c['features'] for c in train]);base=np.concatenate([c['champion'] for c in train])
        teacher=np.concatenate([c['teacher'] for c in train])
        mean=x.mean(0);std=np.maximum(x.std(0),1e-6)
        z=np.concatenate(((x-mean)/std,np.ones((len(x),1))),axis=1)
        penalty=np.eye(17);penalty[-1,-1]=0
        w=np.linalg.solve(z.T@z+penalty,z.T@(teacher-base))
        trainwall=time.perf_counter()-t;traincpu=time.process_time()-tcpu
        c=caches[held];xx=c['features'];bb=c['champion'];yy=c['teacher']
        pred=predict(xx,bb,mean,std,w)
        # Diagnostic masks use teacher targets/past controls only, never inputs.
        different=np.any(yy!=bb,axis=1)
        state_different=c['previous_control_different'].astype(bool)
        masks=dict(all=np.ones(len(xx),bool),teacher_command_different=different,
                   previous_steering_state_different=state_different,
                   teacher_command_equal=~different)
        metrics={k:dict(zero_residual=errors(bb,yy,m),residual=errors(pred,yy,m)) for k,m in masks.items()}
        # Incremental head inference only; pixel feature extraction is timed separately.
        lat=[]
        for row,b in zip(xx,bb):
            ti=time.perf_counter_ns();predict(row[None],b[None],mean,std,w);lat.append((time.perf_counter_ns()-ti)/1e6)
        path=directory/('fold'+str(held)+'.npz')
        np.savez(path,mean=mean,std=std,weights=w,predictions=pred);path.chmod(0o600)
        folds.append(dict(held_out='F'+str(held),train_roads=['F'+str(i) for i in range(4) if i!=held],
                          train_rows=len(x),held_rows=len(xx),train_wall_s=trainwall,train_CPU_s=traincpu,
                          metrics=metrics,head_inference_ms=dict(count=len(lat),median=float(np.median(lat)),
                          p95=float(np.percentile(lat,95)),max=float(max(lat))),model_bytes=mean.nbytes+std.nbytes+w.nbytes))
    macro={metric:{arm:np.mean([f['metrics']['all'][arm][metric] for f in folds],axis=0).tolist()
                   for arm in ['zero_residual','residual']} for metric in ['MAE','RMSE']}
    result=dict(stage=224,settings=SETTINGS,features=FEATURES,folds=folds,macro_road_errors=macro,
                channel_order=['steering','gas','brake'],fit_wall_s=time.perf_counter()-start,
                fit_CPU_s=time.process_time()-cpu,closed_loop_student_runs=0,champion_changed=False,
                native_actions=0,scope='Offline teacher imitation on known DEV trajectories only; not driving performance')
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--data',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();fit(args.data,args.output)
