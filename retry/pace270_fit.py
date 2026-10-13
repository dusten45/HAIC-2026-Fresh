"""One scalar affine ridge on240 on-policy features; GT used for labels only."""
import argparse,json,time,hashlib
from pathlib import Path
import numpy as np
from retry.pace268_profile import multipliers

def run(D):
 p=json.loads((D/'fit-plan.json').read_text());R=D.parent
 def sha(q):return hashlib.sha256(Path(q).read_bytes()).hexdigest()
 def save(q,x):q.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');q.chmod(0o600)
 for q,h in p['hashes'].items():assert sha(q)==h
 assert not (D/'fit-opening.json').exists(),'Singlefit, no refit'
 save(D/'fit-opening.json',dict(epoch=time.time()));F=[];Y=[];counts=[];samples=[];mapping=[];errors=[];labelstart=time.perf_counter()
 for road in p['roads']:
  m=json.loads(Path(p['materializations'][road]).read_text());z=np.load(Path(p['materializations'][road]).parent/'cache-private.npz');features=z['features'];actual=m['actual'];assert len(features)==len(actual) and len(z['observations'])==len(features)+1
  plan=json.loads(Path(p['oracle_plans'][road]).read_text());line=np.array(plan['line']);prof=plan['free_profile'];vbase=np.array(prof['speed']);ds=np.array(prof['ds']);k=np.array(prof['curvature']);pace=multipliers(p['teacher_coefficients'],k,ds,plan['model']);index=0;N=len(line);valid=[];labels=[];rows=[];excluded={'absent_or_zero_student_target':0,'nonpositive_teacher_target':0,'standing_start':0}
  for i,f in enumerate(features):
   state=m['snapshots']['1']['hull'] if i==0 else actual[i-1];pos=np.array(state['position']);gt_speed=float(np.linalg.norm(state['velocity']));assert i==0 or abs(gt_speed-actual[i-1]['speed_m_s'])<1e-8
   candidates=np.arange(max(0,index-2),index+18);j=int(candidates[np.argmin(np.linalg.norm(line[candidates%N]-pos,axis=1))]);index=max(index,j);j=index%N;v=line[(j+1)%N]-line[j];u=float(np.clip((pos-line[j])@v/max(v@v,1e-9),0,1));projection=line[j]+u*v;distance=float(np.linalg.norm(pos-projection));runtime=vbase.copy()
   if index>=N:runtime=np.minimum(100.,np.sqrt(plan['model']['lateral_accel']/np.maximum(abs(np.r_[k,k[0]]),1e-6)))
   runtime*=pace;target=float(np.sqrt(max(0,(1-u)*runtime[j]**2+u*runtime[j+1]**2)));denominator=float(f[6]);teacher_curvature=-float((1-u)*k[j]+u*k[(j+1)%N]);reason=None
   if i==0:reason='standing_start'
   elif bool(f[0]) or denominator<=0:reason='absent_or_zero_student_target'
   elif target<=0:reason='nonpositive_teacher_target'
   if reason:excluded[reason]+=1
   else:valid.append(f);labels.append(float(np.log(target/denominator)));mapping.append(distance);errors.append(abs(abs(teacher_curvature)-abs(float(f[5]))))
   row=dict(action=i+1,student_nominal_target=denominator,teacher_target=target,student_pursuit_curvature=float(f[5]),teacher_path_right_curvature=teacher_curvature,projection_distance_m=distance,excluded=reason);rows.append(row)
   if i in [12,64,116] and reason is None:samples.append(dict(road=road,**row))
  count=len(valid);counts.append(dict(road=road,original_actions=len(features),valid=count,excluded=excluded));F.extend(valid);Y.extend(labels);save(D/(road+'-labels-private.json'),rows)
 labelwall=time.perf_counter()-labelstart;F=np.array(F);Y=np.array(Y);params=np.load(Path(p['normalization']));mean=params['mean'];std=params['std'];X=np.c_[(F-mean)/std,np.ones(len(F))];weights=np.concatenate([np.full(c['valid'],len(F)/(len(counts)*c['valid'])) for c in counts]);penalty=np.eye(17);penalty[-1,-1]=0;tic=time.perf_counter();coef=np.linalg.solve(X.T@(weights[:,None]*X)+penalty,X.T@(weights*Y));fitwall=time.perf_counter()-tic;prediction=X@coef
 q=D/'scalar-model.npz';np.savez(q,weights=coef,mean=mean,std=std,log_min=Y.min(),log_max=Y.max());q.chmod(0o600);np.savez_compressed(D/'training-features-labels-private.npz',features=F,labels=Y,road_weights=weights);(D/'training-features-labels-private.npz').chmod(0o600)
 save(D/'fit-result.json',dict(roads=counts,label_count=len(Y),excluded_N2=True,standing_start_excluded='Teacherstanding-start entry speed0 doesnotencode its accelerationfeedforward; exclude initialpreaction for everyroad, do not fabricate pace floor.',label_log_min=float(Y.min()),label_log_max=float(Y.max()),pace_bounds=np.exp([Y.min(),Y.max()]).tolist(),lambda_L2=1,bias_unpenalized=True,road_equal_total_weight=True,normalization_sha256=sha(Path(p['normalization'])),weighted_RMSE_log=float(np.sqrt(np.average((prediction-Y)**2,weights=weights))),prediction_min=float(prediction.min()),prediction_max=float(prediction.max()),projection_distance_m=dict(median=float(np.median(mapping)),p95=float(np.percentile(mapping,95)),max=float(max(mapping))),absolute_curvature_mismatch=dict(median=float(np.median(errors)),p95=float(np.percentile(errors,95))),samples=samples,label_wall_s=labelwall,fit_wall_s=fitwall,model_sha256=sha(q),new_native=0,model_physics_ticks=0,fit_count=1,feature_GT_inputs=False))
 print('Onefit completed, labels',len(Y),'logbounds',float(Y.min()),float(Y.max()),'native0',flush=True)

if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--stage-dir',type=Path,required=True);run(a.parse_args().stage_dir.resolve())
