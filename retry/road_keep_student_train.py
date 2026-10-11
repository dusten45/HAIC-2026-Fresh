"""Fit one fixed-capacity student from two already saved trajectory caches."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import time

import cv2
import numpy as np

from retry.road_keep_student import FEATURE_NAMES, KeepStudent, features


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ah(value): return hashlib.sha256(value.tobytes()).hexdigest()
def write(path,value):
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');path.chmod(0o600)


def metrics(student,observations,labels):
    confusion=np.zeros((2,2),dtype=np.int64); rows=[]; times=[]; feature_means=[]
    for obs,label in zip(observations,labels):
        pred,detail=student.mask(obs);P=((obs[-1]>.32)&(obs[-1]<.47))
        truth=label[P].astype(np.uint8);guess=pred[P]
        confusion += np.bincount(truth*2+guess,minlength=4).reshape(2,2)
        rows.append({'teacher_deleted':int((P&~label.astype(bool)).sum()),
                     'student_deleted':detail['deleted_cells'],'P_cells':detail['original_P_cells'],
                     'teacher_keep_lost':int((label.astype(bool)&~pred.astype(bool)).sum())})
        times.append(detail['inference_ms'])
        feature_means.append(detail['feature_mean_on_P'])
    delete_tp,missed=map(int,confusion[0]);false_delete,kept=map(int,confusion[1])
    return {'confusion_true_delete_keep_by_pred_delete_keep':confusion.tolist(),
            'delete_precision':delete_tp/max(1,delete_tp+false_delete),
            'delete_recall':delete_tp/max(1,delete_tp+missed),
            'keep_recall':kept/max(1,kept+false_delete),
            'balanced_accuracy':.5*(delete_tp/max(1,delete_tp+missed)+kept/max(1,kept+false_delete)),
            'student_delete_fraction_on_P':(delete_tp+false_delete)/max(1,int(confusion.sum())),
            'teacher_delete_fraction_on_P':(delete_tp+missed)/max(1,int(confusion.sum())),
            'unchanged_frame_count':sum(r['student_deleted']==0 for r in rows),
            'empty_output_frame_count':sum(r['student_deleted']==r['P_cells'] for r in rows),
            'feature_mean_across_frames':np.mean(feature_means,axis=0).tolist(),
            'feature_std_across_frames':np.std(feature_means,axis=0).tolist(),
            'inference_ms_median':float(np.median(times)),'inference_ms_max':max(times),'rows':rows}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plan',type=Path,required=True)
    path=parser.parse_args().plan.resolve();D=path.parent;p=json.loads(path.read_text())
    assert sha(path)==(D/'learning-plan.sha256').read_text().split()[0]
    for name,expected in p['source_sha256'].items():assert sha(name)==expected,name
    for name,expected in p['cache_sha256'].items():assert sha(name)==expected,name
    cv2.setNumThreads(1);cv2.setRNGSeed(p['training_rng_seed'])
    resource.setrlimit(resource.RLIMIT_CPU,(p['offline_CPU_limit_s'],)*2)
    wall=time.perf_counter();cpu=time.process_time()
    with np.load(p['training_pixels_actions'],allow_pickle=False) as z:frames=z['frames'].copy()
    with np.load(p['training_masks'],allow_pickle=False) as z:m={k:z[k].copy() for k in z.files}
    receipts=[json.loads(line) for line in Path(p['training_mask_receipts']).read_text().splitlines()]
    trace=[json.loads(line) for line in Path(p['training_trace']).read_text().splitlines()]
    assert len(frames)==834 and len(trace)==833 and len(m['intersection'])==834
    assert m['operation'].tolist()==[0]+[1]*833
    observations=[];labels=[];X=[];Y=[];full_hashes=set();last_hashes=set()
    for step in range(1,834):
        obs=frames[np.maximum(0,np.arange(step-4,step))].astype(np.float32)/255
        feat,P=features(obs);label=m['intersection'][step]
        assert ah(obs)==receipts[step]['observation_sha256']==trace[step-1]['observation_sha256_before']
        assert np.array_equal(P,m['original_raw'][step])
        assert np.array_equal(label,P&m['visible_GT'][step])
        assert ah(label)==receipts[step]['intersection_sha256']
        indices=np.flatnonzero(P.reshape(-1))
        take=indices[np.linspace(0,len(indices)-1,min(len(indices),p['samples_per_frame']),dtype=np.int64)]
        X.append(feat.reshape(-1,len(FEATURE_NAMES))[take]);Y.append(label.reshape(-1)[take])
        observations.append(obs);labels.append(label);full_hashes.add(ah(obs));last_hashes.add(ah(obs[-1]))
    valid_obs=[];valid_labels=[];excluded=[];retained=[]
    for name in p['validation_captures']:
        with np.load(name,allow_pickle=False) as z:
            obs=z['observation'].astype(np.float32)/255;P=((obs[-1]>.32)&(obs[-1]<.47)).astype(np.uint8)
            assert np.array_equal(P,z['pixel_raw_road']);label=P&z['visible_GT']
        if ah(obs) in full_hashes or ah(obs[-1]) in last_hashes:
            excluded.append(name);continue
        valid_obs.append(obs);valid_labels.append(label);retained.append(name)
    assert len(valid_obs)==p['expected_validation_frames'] and len(excluded)==2
    x=np.ascontiguousarray(np.concatenate(X),dtype=np.float32);y=np.concatenate(Y).astype(np.int32)
    assert len(np.unique(y))==2
    weights=np.where(y==0,p['delete_weight'],1.).astype(np.float32)
    data=cv2.ml.TrainData_create(x,cv2.ml.ROW_SAMPLE,y,sampleWeights=weights)
    model=cv2.ml.DTrees_create();model.setMaxDepth(5);model.setMinSampleCount(64)
    model.setCVFolds(0);model.setUseSurrogates(False);model.setUse1SERule(False);model.setTruncatePrunedTree(False)
    fit_wall=time.perf_counter();fit_cpu=time.process_time()
    assert model.train(data)
    fit_wall=time.perf_counter()-fit_wall;fit_cpu=time.process_time()-fit_cpu
    model_path=D/'student.xml';model.save(str(model_path));model_path.chmod(0o600)
    student=KeepStudent(model_path)
    train_metrics=metrics(student,observations,labels)
    validation=metrics(student,valid_obs,valid_labels)
    gate={'alignment':True,'official_float32_input_only':True,'finite_two_class_fit':True,
          'fixed_depth_and_features':model.getMaxDepth()==5 and model.getVarCount()==len(FEATURE_NAMES),
          'not_noop_or_collapse':0<validation['student_delete_fraction_on_P']<.5 and validation['empty_output_frame_count']==0,
          'learned_teacher_signal':validation['balanced_accuracy']>.5,
          'execution_cost':validation['inference_ms_max']<1000}
    report={'status':'PASS_FROZEN_STUDENT_FOR_ONE_NATIVE_PROBE' if all(gate.values()) else 'STOP_OFFLINE_GATE',
            'plan_sha256':sha(path),'model_sha256':sha(model_path),'training_frames':833,
            'validation_frames':len(valid_obs),'excluded_duplicate_paths':excluded,'validation_retained_paths':retained,
            'same_geometry_different_trajectories':True,'independent_geometry_generalization':False,
            'sample_count':len(y),'sample_class_counts_delete_keep':np.bincount(y,minlength=2).tolist(),
            'features':FEATURE_NAMES,'max_depth':5,'max_leaves_bound':32,'max_nodes_bound':63,
            'min_sample_count':64,'delete_weight':p['delete_weight'],'model_variants':1,
            'fit_wall_s':fit_wall,'fit_CPU_s':fit_cpu,'total_offline_wall_s':time.perf_counter()-wall,
            'total_offline_CPU_s':time.process_time()-cpu,'peak_RSS_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
            'train':train_metrics,'validation':validation,'gate':gate,
            'teacher_semantics':'useful keep/delete convention, not physical absolute road truth',
            'competition_training_eligibility_verified':False,'new_environment_actions':0,'new_rollouts_collected':0}
    write(D/'learning-result.json',report)
    print(json.dumps({k:report[k] for k in ['status','training_frames','validation_frames','sample_count','fit_wall_s','total_offline_wall_s','gate']}),flush=True)
    return int(not all(gate.values()))


if __name__=='__main__':raise SystemExit(main())
