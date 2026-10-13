"""Fixed label selection and road-excluded CART lookup on one-shot recorded outcomes."""
import argparse,time,datetime
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.outcome282_tree import CLASSES,fit,predict
ROADS=['O0','O2','N0','N1','N2','N3']
def run(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage282';assert not (D/'analysis-private.json').exists();start=time.perf_counter();cpu=time.process_time();p=read(D/'plan.json');records=[];new=[];outs={}
 for road in ROADS:
  o=read(D/road/'outcome-private.json');outs[road]=o;assert o['technical_error'] is None and len(o['results'])==len(read(D/road/'plan.json')['jobs']);new.extend(o['results'])
 records.extend(new)
 for r in p['reused_runs']:
  q=Path(r['result_path']);assert sha(q)==r['sha256'];records.append(read(q))
 assert len(records)==96;states=[];X=[];y=[];groups=[]
 for road in ROADS:
  roadplan=read(D/road/'plan.json');cache=np.load(roadplan['cache'])
  for anchor in p['anchors'][road]:
   rs=[r for r in records if r['road']==road and r['anchor']==anchor];assert len(rs)==4 and {r['macro'] for r in rs}==set(CLASSES[1:])
   base=dict(completed=True,actual_DNF=False,censored=False,comparable=True,lap_ms=roadplan['baseline_lap_ms'],lap_delta_ms=0,macro='baseline',new_native=0)
   outcomes={r['macro']:dict(completed=r['completed'],actual_DNF=r['actual_DNF'],censored=r['censored'],comparable=r['comparable'],lap_ms=r['lap_ms'],lap_delta_ms=r['lap_delta_ms'],retire_reason=r['retire_reason'],native_actions=r['native_actions'],source_stage=281 if (road in ['N0','N2'] and anchor in p['anchors'][road][1:3]) else 282) for r in rs};outcomes['baseline']=base
   valid=all(r['comparable'] and not r['censored'] for r in rs)
   best='baseline';bestms=base['lap_ms']
   for macro in CLASSES[1:]:
    r=outcomes[macro]
    if r['comparable'] and r['completed'] and not r['censored'] and r['lap_ms']<bestms:best=macro;bestms=r['lap_ms']
   state=dict(road=road,anchor=anchor,label=best,eligible_for_tree=valid,best_gain_ms=base['lap_ms']-bestms,outcomes=outcomes)
   states.append(state)
   if valid:X.append(cache['features'][anchor-1]);y.append(CLASSES.index(best));groups.append(road)
 X=np.asarray(X,float);y=np.array(y,int);groups=np.array(groups);assert X.shape[1]==16 and np.isfinite(X).all()
 validstates=[s for s in states if s['eligible_for_tree']];trees={};predictions=np.zeros(len(y),int);folds=[]
 def score(choices,subset=validstates):
  evaluated=[]
  for s,ch in zip(subset,choices):
   r=s['outcomes'][CLASSES[int(ch)]];evaluated.append(dict(road=s['road'],anchor=s['anchor'],choice=CLASSES[int(ch)],completed=r['completed'],actual_DNF=r['actual_DNF'],censored=r['censored'],comparable=r['comparable'],lap_ms=r['lap_ms'],delta_ms=r['lap_delta_ms'],baseline_lap_ms=s['outcomes']['baseline']['lap_ms']))
  completed=[r for r in evaluated if r['completed'] and r['comparable'] and not r['censored']]
  return dict(states=len(evaluated),complete=len(completed),actual_DNF=sum(r['actual_DNF'] for r in evaluated),censored=sum(r['censored'] for r in evaluated),incomparable=sum(not r['comparable'] for r in evaluated),abstain=sum(r['choice']=='baseline' for r in evaluated),choice_distribution={c:sum(r['choice']==c for r in evaluated) for c in CLASSES},improved=sum(r['delta_ms'] is not None and r['delta_ms']<0 for r in completed),ties=sum(r['delta_ms']==0 for r in completed),slower=sum(r['delta_ms'] is not None and r['delta_ms']>0 for r in completed),mean_delta_ms_on_common_completed=float(np.mean([r['delta_ms'] for r in completed])) if completed else None,total_time_all_states_ms=sum(r['lap_ms'] for r in completed) if len(completed)==len(evaluated) else None,rows=evaluated)
 for road in ROADS:
  train=groups!=road;test=~train;tree=fit(X[train],y[train]);trees[road]=tree;pr=predict(tree,X[test]);predictions[test]=pr;subset=[s for s in validstates if s['road']==road];folds.append(dict(heldout_road=road,training_states=int(train.sum()),test_states=int(test.sum()),classification_correct=int(np.sum(pr==y[test])),lookup=score(pr,subset)))
 final=fit(X,y);in_sample=predict(final,X);loro=score(predictions);baseline=score(np.zeros(len(y),int));constant={c:score(np.full(len(y),i,int)) for i,c in enumerate(CLASSES[1:],1)};oracle=score(y)
 confusion=np.zeros((5,5),int)
 for truth,pred in zip(y,predictions):confusion[truth,pred]+=1
 private=dict(states=states,legal_features=X.tolist(),labels=y.tolist(),groups=groups.tolist(),trees_by_fold=trees,final_tree=final,LORO_predictions=predictions.tolist());save(D/'analysis-private.json',private)
 public=dict(stage=282,recipe=dict(max_depth=2,min_samples_leaf=3,criterion='Gini',legal_features=16,split_ties='feature order then ascending midpoint',class_ties=CLASSES),registered_states=24,eligible_tree_states=len(y),ineligible_states=24-len(y),label_distribution={c:int(np.sum(y==i)) for i,c in enumerate(CLASSES)},labels_by_road={r:{c:sum(s['road']==r and s['label']==c for s in validstates) for c in CLASSES} for r in ROADS},states=states,collection=dict(new_runs=80,reused_runs=16,new_complete=sum(r['completed'] for r in new),new_actual_DNF=sum(r['actual_DNF'] for r in new),new_censored=sum(r['censored'] for r in new),new_incomparable=sum(not r['comparable'] for r in new),total_macro_complete=sum(r['completed'] for r in records),total_macro_actual_DNF=sum(r['actual_DNF'] for r in records)),LORO=dict(classification_accuracy=float(np.mean(predictions==y)),confusion_truth_rows_prediction_columns=confusion.tolist(),folds=folds,lookup=loro),baseline=baseline,always_same_macro=constant,oracle_recorded_best=oracle,final_fit=dict(training_states=len(y),in_sample_accuracy=float(np.mean(in_sample==y)),in_sample_abstain=int(np.sum(in_sample==0)),prediction_distribution={c:int(np.sum(in_sample==i)) for i,c in enumerate(CLASSES)}),limitations=['One3-action intervention thenpixel240 at recorded TRAIN snapshots, not repeated policy performance','6road-excluded fits of one fixed recipe; one final24-state fit; no hyperparameter tuning','Baseline abstain is classchoice, no confidence threshold','DNF/censored/incomparable never assigned fictional completion times; common-completion means conditional','Oracle selection uses observed outcomes and is optimistic; no independent DEV/HOLDOUT/SEALED'],analysis_wall_s=time.perf_counter()-start,analysis_CPU_s=time.process_time()-cpu)
 if loro['actual_DNF'] or loro['censored'] or loro['incomparable']:
  decision='LORO chosen outcomes contain failure/unknown; no current evidence to test repeated policy. Outcome-label collection is feasible but fixed tree selection gate failed.'
 elif loro['mean_delta_ms_on_common_completed'] is not None and loro['mean_delta_ms_on_common_completed']<0:
  decision='LORO one-shot lookup preserves completion and improves mean time; limited reason for separately scoped repeated-policy diagnostic, not proof of repeated performance.'
 else:decision='No strict LORO mean-time improvement with completion preserved; no current reason to test repeated policy.'
 public['time_resolution_ms']=20;public['decision']=decision;save(D/'analysis-summary.json',public)
 prior=R/'project-effective-budget-v287.json';v=read(prior);native=sum(o['budget']['actions'] for o in outs.values());assert native==sum(r['native_actions'] for r in new)<=52000
 opening={r:read(D/r/'opening.json')['epoch'] for r in ROADS};end=max(opening[r]+outs[r]['wall_s'] for r in ROADS);cost=dict(stage=282,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),explicit_research_grant=46000,new_wrapper_actions=native,new_runs=80,reused_runs=16,new_baseline_native=0,new_training_native=0,prefix_actions=sum(r['phase_actions'].get('prefix',0) for r in new),macro_actions=sum(r['phase_actions'].get('macro',0) for r in new),continuation_actions=sum(r['phase_actions'].get('continuation',0) for r in new),native_technical_errors=0,lost_native_actions=0,new_actual_DNF=sum(r['actual_DNF'] for r in new),new_censored=sum(r['censored'] for r in new),new_incomparable=sum(not r['comparable'] for r in new),raw_step_ticks=sum(r['raw_step_ticks'] for r in new),raw_reset_ticks=sum(r['raw_reset_ticks'] for r in new),parallel_elapsed_s=end-min(opening.values()),runner_CPU_s=sum(o['CPU_s'] for o in outs.values()),actor_CPU_s=sum(r['actor_CPU_s'] for r in new),env_step_wall_s_sum=sum(r['env_step_wall_s'] for r in new),tree_fits=7,analysis_wall_s=public['analysis_wall_s'],analysis_CPU_s=public['analysis_CPU_s'],model_physics_ticks=0,new_paid_resources=0,B_operating_cap=1064000,actual_cumulative_wrapper_actions=927800+native,research_remaining=52200-native,final_reserved_actions=84000,final_reserve_used=0)
 assert cost['actual_cumulative_wrapper_actions']+cost['research_remaining']+84000==1064000;save(D/'cost.json',cost);v.update(version=288,at_utc=cost['at_utc'],prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),stage282_new_wrapper_actions=native,budget_reason='282closed80new+16reused outcomes and fixedtree7fits includingLORO; no policy run/promotion/reserve.');assert not (R/'project-effective-budget-v288.json').exists();save(R/'project-effective-budget-v288.json',v)
 f=R/'experiment-cost-lines.jsonl';assert not any(__import__('json').loads(x).get('stage')==282 for x in f.read_text().splitlines())
 with f.open('a') as h:h.write(__import__('json').dumps(cost)+'\n')
 public['cost']=cost;save(G/'retry/outcome282_result.json',public)
 # Public result permissions; raw parameters and pixels remain private.
 (G/'retry/outcome282_result.json').chmod(0o644)
 print(__import__('json').dumps(dict(labels=public['label_distribution'],collection=public['collection'],LORO={k:v for k,v in loro.items() if k!='rows'},constant={c:{k:v for k,v in s.items() if k not in ['rows','choice_distribution']} for c,s in constant.items()},decision=decision,cost=cost),indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
