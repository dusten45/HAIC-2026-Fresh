"""Fixed multioutput ridge gains, TRAIN-road-only normalization and LORO lookup."""
import argparse,time,datetime
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
CLASSES=['baseline','gas_upper','brake_lower','steer_plus','steer_minus'];ROADS=['O0','O2','N0','N1','N2','N3']
def fit(X,Y):
 mean=X.mean(axis=0);std=X.std(axis=0);std=np.where(std<1e-12,1.,std);Z=np.column_stack(((X-mean)/std,np.ones(len(X))));penalty=np.eye(17);penalty[-1,-1]=0.;W=np.linalg.solve(Z.T@Z+penalty,Z.T@Y)
 return dict(mean=mean.tolist(),std=std.tolist(),weights=W.tolist())
def predict(model,X):return np.column_stack(((X-np.array(model['mean']))/np.array(model['std']),np.ones(len(X))))@np.array(model['weights'])
def choose(gains):
 out=[]
 for row in gains:
  value=float(np.max(row));winners=np.flatnonzero(row==value);out.append(int(winners[0])+1 if value>0 and len(winners)==1 else 0)
 return np.array(out,int)
def run(R,recover=False):
 G=Path(__file__).resolve().parent.parent;D=R/'stage283';assert (D/'targets-models-private.json').exists() if recover else not D.exists();
 if not recover:D.mkdir(mode=0o700)
 saved=read(D/'targets-models-private.json') if recover else None
 source=G/'retry/outcome282_result.json';s=read(source);states=s['states'];assert len(states)==24
 plan=dict(stage=283,source_stage=282,source_sha256=sha(source),code_sha256=sha(Path(__file__)),features=16,lambda_ridge=1,normalization='Training fold mean/std population; std<1e-12 becomes1; intercept unpenalized',targets='complete2-T/160; actualDNFp-1 from saved terminal visited/total; delta vs same-state baseline; no imputation',selection='Unique positive maximum macro; nonpositive or exact float64 maximum tie => baseline0; no threshold sweep',folds=ROADS,expected_fits=7,native=0,physics_ticks=0);
 if not recover:save(D/'plan.json',plan)
 start=time.perf_counter();cpu=time.process_time();X=[];returns=[];provenance=[];groups=[];missing=[]
 for state in states:
  road,q=state['road'],state['anchor'];cachepath=R/'stage251/training'/road/'cache-private.npz';X.append(np.load(cachepath)['features'][q-1]);groups.append(road);base_ms=state['outcomes']['baseline']['lap_ms'];row=[2-base_ms/1000/160]
  for macro in CLASSES[1:]:
   outcome=state['outcomes'][macro];path=R/('stage'+str(outcome['source_stage']))/road/(str(q)+'_'+macro)/'result.json';r=read(path);assert r['comparable'] and not r['censored'];assert r['completed']==outcome['completed'] and r['actual_DNF']==outcome['actual_DNF']
   if r['completed']:value=2-r['lap_ms']/1000/160;p=None
   elif r['actual_DNF']:
    if 'visited' not in r or 'total_tiles' not in r or r['total_tiles']<=0:missing.append(dict(road=road,anchor=q,macro=macro));row.append(None);continue
    p=r['visited']/r['total_tiles'];assert 0<=p<=1;value=p-1
   else:missing.append(dict(road=road,anchor=q,macro=macro));row.append(None);continue
   row.append(value);provenance.append(dict(road=road,anchor=q,macro=macro,result_path=str(path),sha256=sha(path),actual_DNF=r['actual_DNF'],visited=r['visited'],total_tiles=r['total_tiles'],progress=p,official_return=value,source='Actual terminal execution receipt, not per-step trace imputation'))
  returns.append(row)
 if missing:
  save(D/'blocked-targets.json',dict(missing=missing,native=0,physics=0));raise ValueError('Terminal progress absent: targets unavailable, no imputation')
 X=np.array(X,float);returns=np.array(returns,float);groups=np.array(groups);assert X.shape==(24,16) and returns.shape==(24,5) and np.isfinite(X).all() and np.isfinite(returns).all();Y=returns[:,1:]-returns[:,0,None];predicted=np.zeros((24,4));folds=[];models={}
 for road in ROADS:
  train=groups!=road;test=~train;model=saved['models_by_fold'][road] if recover else fit(X[train],Y[train]);models[road]=model;predicted[test]=predict(model,X[test]);folds.append(dict(heldout_road=road,training_states=int(train.sum()),test_states=int(test.sum()),training_only_statistics=True))
 choices=choose(predicted);final=saved['final_model'] if recover else fit(X,Y);finalpred=predict(final,X);finalchoices=choose(finalpred)
 tree_rows=s['LORO']['lookup']['rows'];tree_map={(r['road'],r['anchor']):CLASSES.index(r['choice']) for r in tree_rows};tree_choices=np.array([tree_map[(st['road'],st['anchor'])] for st in states])
 def score(ch):
  rows=[]
  for i,(st,c) in enumerate(zip(states,ch)):
   r=st['outcomes'][CLASSES[int(c)]];rows.append(dict(road=st['road'],anchor=st['anchor'],choice=CLASSES[int(c)],completed=r['completed'],actual_DNF=r['actual_DNF'],lap_ms=r['lap_ms'],lap_delta_ms=r['lap_delta_ms'],official_return=float(returns[i,c]),return_delta=float(returns[i,c]-returns[i,0])))
  complete=[r for r in rows if r['completed']];gains=[r['return_delta'] for r in rows]
  return dict(states=24,complete=len(complete),actual_DNF=sum(r['actual_DNF'] for r in rows),censored=0,incomparable=0,abstain=sum(r['choice']=='baseline' for r in rows),choice_distribution={c:sum(r['choice']==c for r in rows) for c in CLASSES},mean_official_return=float(np.mean([r['official_return'] for r in rows])),mean_return_delta=float(np.mean(gains)),sum_return_delta=float(np.sum(gains)),improved_return=sum(v>0 for v in gains),return_ties=sum(v==0 for v in gains),worse_return=sum(v<0 for v in gains),common_completed_mean_time_delta_ms=float(np.mean([r['lap_delta_ms'] for r in complete])) if complete else None,full_cohort_mean_completion_ms=float(np.mean([r['lap_ms'] for r in complete])) if len(complete)==24 else None,rows=rows)
 ridge=score(choices);baseline=score(np.zeros(24,int));tree=score(tree_choices);constants={c:score(np.full(24,i,int)) for i,c in enumerate(CLASSES[1:],1)}
 for f in folds:
  idx=np.flatnonzero(groups==f['heldout_road']);f['selected']=[ridge['rows'][i] for i in idx];f['abstain']=int(sum(choices[i]==0 for i in idx));f['complete']=sum(ridge['rows'][i]['completed'] for i in idx);f['mean_return_delta']=float(np.mean([ridge['rows'][i]['return_delta'] for i in idx]))
 if ridge['actual_DNF'] or ridge['mean_return_delta']<=0:decision='Fixed return-gain ridge did not preserve baseline completion and strict objective improvement; no evidence to expand to repeated policy.'
 else:decision='Road-excluded one-shot lookup preserved completion and improved objective; weak evidence for a separately scoped repeated-policy check, not repeated-policy performance.'
 public=dict(stage=283,target_complete_count=sum(r['completed'] for st in states for c,r in st['outcomes'].items() if c!='baseline'),target_DNF_count=sum(p['actual_DNF'] for p in provenance),missing_targets=0,baseline_gain_exact=0,recipe=plan,return_scale='Complete gains equal negative lap_delta_seconds/160; DNF differences use actual terminal progress and carry full failure cost',LORO_ridge=ridge,baseline=baseline,LORO_282_tree=tree,constant_macro=constants,folds=folds,final_fit=dict(states=24,abstain=int(np.sum(finalchoices==0)),choice_distribution={c:int(np.sum(finalchoices==i)) for i,c in enumerate(CLASSES)},in_sample_gain_RMSE=float(np.sqrt(np.mean((finalpred-Y)**2)))),LORO_gain_prediction_RMSE=float(np.sqrt(np.mean((predicted-Y)**2))),decision=decision,scope='Same24knownTRAIN snapshots, one intervention thenpixel240; lookup of measured outcomes, not repeated policy or independent test',new_native_actions=0,new_model_physics_ticks=0,new_policy_runs=0,no_threshold_sweep=True,champion_changed=False,HOLDOUT_SEALED_used=False)
 if recover:
  assert np.array_equal(Y,np.array(saved['targets'])) and np.array_equal(predicted,np.array(saved['predicted_gains']))
  cost=read(D/'cost.json');save(D/'export-recovery-receipt.json',dict(extra_fits=0,native=0,physics=0,predicted_gains_exact=True,export_wall_s=time.perf_counter()-start,export_CPU_s=time.process_time()-cpu))
 else:
  save(D/'targets-models-private.json',dict(features=X.tolist(),targets=Y.tolist(),returns=returns.tolist(),provenance=provenance,models_by_fold=models,final_model=final,predicted_gains=predicted.tolist(),final_predicted_gains=finalpred.tolist()))
  prior=R/'project-effective-budget-v288.json';v=read(prior);cost=dict(stage=283,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),new_wrapper_actions=0,new_model_physics_ticks=0,new_render_calls=0,new_actor_calls=0,new_policy_runs=0,ridge_fits=7,states=24,macro_gain_targets=96,actual_DNF_targets=10,analysis_wall_s=time.perf_counter()-start,analysis_CPU_s=time.process_time()-cpu,new_paid_resources=0,B_operating_cap=v['B_operating_cap'],actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions'],research_remaining=v['research_remaining'],final_reserved_actions=84000,final_reserve_used=0);save(D/'cost.json',cost)
  v.update(version=289,at_utc=cost['at_utc'],prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),stage283_new_wrapper_actions=0,budget_reason='283fixedreturngainridge LORO onstored24states96macrooutcomes;0native/physics/newpolicy, no imputation.');assert not (R/'project-effective-budget-v289.json').exists();save(R/'project-effective-budget-v289.json',v)
  f=R/'experiment-cost-lines.jsonl';assert not any(__import__('json').loads(x).get('stage')==283 for x in f.read_text().splitlines())
  with f.open('a') as h:h.write(__import__('json').dumps(cost)+'\n')
 public['cost']=cost;public['recipe'].pop('code_sha256');public['recipe'].pop('source_sha256');save(G/'retry/gain283_result.json',public);(G/'retry/gain283_result.json').chmod(0o644)
 print(__import__('json').dumps(dict(ridge={k:v for k,v in ridge.items() if k!='rows'},tree={k:v for k,v in tree.items() if k!='rows'},constant={c:{k:v for k,v in r.items() if k not in ['rows','choice_distribution']} for c,r in constants.items()},decision=decision,cost=cost),indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);a.add_argument('--recover-export',action='store_true');args=a.parse_args();run(args.private_root.resolve(),args.recover_export)
