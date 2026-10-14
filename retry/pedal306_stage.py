"""Single fixed221 -> exact296 final-pedal head, six TRAIN collection /18 evaluation."""
import argparse,datetime,gzip,hashlib,json,time,zipfile
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.completion297_search import metrics,diagnose

def verify(D):
 p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(q)==h,q
 return p

def prepare(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage306';assert not D.exists();D.mkdir(mode=0o700);prior=R/'project-effective-budget-v313.json';v=read(prior);assert v['research_remaining']==7081 and v['B_operating_cap']==1230000
 v.update(version=314,prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=10000,B_operating_cap=1240000,research_remaining=17081,budget_reason='User306 grant10000 for one frozen221 final-pedal residual head, cap12000; reserve unchanged');save(R/'project-effective-budget-v314.json',v)
 old=read(R/'stage299/plan.json');base=old['baseline296'];p221=read(R/'stage221/evaluation/plan.json');teacher=p221['arms']['C'];cfg=dict(base['config']);cfg.update(worker_path=str(G/'retry/pedal306_worker.py'),worker_sha256=sha(G/'retry/pedal306_worker.py'))
 selected=['T2950','T2953','T2956','T2959','O0','O2'];m=read(R/'stage295/plan.json');assert [m['new_TRAIN'][i]['public_label'] for i in [0,3,6,9]]==selected[:4] and m['old_TRAIN_roads'][:2]==selected[4:]
 critical=['source_vehicle_transition.py','receding_horizon_oracle.py','track_feedback_candidate.py','transition_ranking_probe.py','short_sequence_probe.py','aggregate229_teacher.py'];sources=[G/'retry'/n for n in critical+['pedal306_agent.py','pedal306_worker.py','pedal306_episode.py','pedal306_jobs.py','pedal306_stage.py']]+[R/'stage221/evaluation/plan.json',R/'stage295/plan.json',Path(cfg['archive_path']),Path(teacher['archive_path']),Path(teacher['worker_path']),R/'project-effective-budget-v314.json']
 for q in sources:
  if str(q) in p221['source_sha256']:assert sha(q)==p221['source_sha256'][str(q)]
 p=dict(stage=306,deadline_utc='2026-10-16T10:01:55+00:00',baseline296=base,collection_config=cfg,teacher=teacher,oracle=p221['oracle'],cases=old['cases'],initial_observations=old['initial_observations'],roads=old['roads'],collection_roads=selected,sandbox_path=old['sandbox_path'],phase_caps=dict(collection=12000,evaluation=12000),native_cap=12000,teacher_query_cap=600,per_road_query_cap=100,teacher_steps='1+3k, k0..99, while actual episode exists; no quota redistribution',fit='Only new306 labels; weighted train mean/std floor1e-6; equal road mass N/6; ridge1 bias unpenalized; teacher finalpedals minus296 finalpedals; clippeddelta.5 applied after296 finalclip; no scale reapplied',selection='All18 once; greater completioncount, or equal count strictlyfastercommoncompletionmean; no alternate,DEV,adoption',capture='Fresh full source capture at every pre-native boundary, including actual touching-obstacle fixture pairs; no300 truth/geometry/history reuse. Source reconstruction omits solver warm-start/manifold/broadphase/island/finish state.',hashes={str(q):sha(q) for q in sources})
 save(D/'previous-current-champion.json',read(R/'current-champion.json'));save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'budget.json',dict(actions=0,collection=0,evaluation=0));print('306 registered: exact296 six TRAIN once, frozen221 max100queries/road, one ridge, all18 once, native12000',flush=True)

def episodes(R,phase):
 from retry.pedal306_jobs import jobs
 D=R/'stage306';p=verify(D);marker=D/(phase+'-opening.json');assert not marker.exists();save(marker,dict(epoch=time.time()));roads=p['collection_roads'] if phase=='collection' else p['roads'];cfg=p['collection_config'] if phase=='collection' else read(D/'candidate-config.json');t=p['baseline296']['theta'];rr=[]
 for i in range(0,len(roads),2):
  entries=[dict(folder=str(D/phase/r),road=r,case=p['cases'][r],config=cfg,initial_observation_sha256=p['initial_observations'].get(r),ceiling=float(45*np.exp(t[5])),steering_gain=float(np.exp(t[2]))) for r in roads[i:i+2]];batch=jobs(D,p,entries,phase);rr+=batch;save(D/(phase+'-results-private.json'),rr)
  print(json.dumps(dict(phase=phase,finished=len(rr),last=[{k:x.get(k) for k in ['road','completed','native_actions','lap_ms','technical_error']} for x in batch])),flush=True)
  if len(batch)!=len(entries) or any(x['technical_error'] or x['censored'] for x in batch):break
 assert len(rr)==len(roads) and not any(x['technical_error'] or x['censored'] for x in rr),'Incomplete phase: no replay or replacement'
 if phase=='collection':
  for r in rr:
   b=next(x for x in p['baseline296']['results'] if x['road']==r['road'])
   for k in ['completed','actual_DNF','native_actions','lap_ms','damage','visited','retire_reason']:assert r[k]==b[k],(r['road'],k)
 save(D/(phase+'-phase-receipt.json'),dict(native=sum(x['native_actions'] for x in rr),wall_s=time.time()-read(marker)['epoch'],complete=True));print(phase+' complete',flush=True)

def model_text(mean,std,w):
 return 'import numpy as np\nMEAN=np.array('+repr(mean.tolist())+',dtype=np.float64)\nSTD=np.array('+repr(std.tolist())+',dtype=np.float64)\nWEIGHTS=np.array('+repr(w.tolist())+',dtype=np.float64)\n'

def archive(D,p,model,name):
 with zipfile.ZipFile(p['baseline296']['config']['archive_path']) as z:members={n:z.read(n) for n in z.namelist()}
 G=Path(__file__).resolve().parent.parent;members['retry/pedal306_base.py']=members['agent.py'];members['agent.py']=(G/'retry/pedal306_agent.py').read_bytes();members['retry/pedal306_model.py']=model.encode();q=D/(name+'.zip')
 with zipfile.ZipFile(q,'x',compression=zipfile.ZIP_DEFLATED) as z:
  for n,b in sorted(members.items()):item=zipfile.ZipInfo(n,date_time=(2026,10,9,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,b)
 q.chmod(0o600);cfg=dict(p['collection_config']);cfg.update(archive_path=str(q),archive_sha256=sha(q),members_sha256={n:hashlib.sha256(b).hexdigest() for n,b in members.items()});return cfg

def teachfit(R):
 from retry.aggregate229_teacher import query
 from retry.frozen_composite_runtime import prepare as actor
 D=R/'stage306';p=verify(D);assert read(D/'collection-phase-receipt.json')['complete'];assert not (D/'teacher-opening.json').exists();save(D/'teacher-opening.json',dict(epoch=time.time()));records=[];xs=[];ys=[];ws=[];allbase=[];allteacher=[];totalq=0;modelticks=0;clones=0;modelcpu=0.;querywall=0.;roadstats=[]
 for road in p['collection_roads']:
  F=D/'collection'/road;track=read(F/'track-private.json');previous=None;labels=[];receipts=[];trace=[json.loads(s) for s in (F/'trace-private.jsonl').read_text().splitlines()]
  with gzip.open(F/'full-source-captures-private.jsonl.gz','rt') as stream:
   for line in stream:
    r=json.loads(line);step=r['step'];s=r['snapshot'];assert len(s['wheels'])==4 and len(s['roads'])==s['road_count'] and 'touching_obstacle_contacts' in s and 'world_flags' in s;assert r['final296']==trace[step-1]['action'] and r['features']==trace[step-1]['features'];assert abs(s['actual_time']-(1.02+(step-1)*.08))<1e-8
    if (step-1)%3 or (step-1)//3>=100:continue
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();target,previous,receipt=query(s,np.array(r['teacher_nominal'],np.float32),p['oracle'],step,previous,track,float(r['previous_action'][0]));receipt.pop('scores');receipts.append(receipt);labels.append(dict(step=step,features=r['features'],base=r['final296'],teacher=target.tolist()));totalq+=1;assert totalq<=600;modelticks+=receipt['model_physics_ticks'];clones+=receipt['model_queries'];modelcpu+=receipt['CPU_s'];querywall+=receipt['wall_s']
    if len(labels)%20==0:print(json.dumps(dict(teacher_road=road,queries=len(labels),total_queries=totalq)),flush=True)
  save(F/'teacher-labels-private.json',labels);save(F/'teacher-receipts-private.json',receipts);assert labels
  x=np.array([r['features'] for r in labels]);base=np.array([r['base'] for r in labels],np.float32);target=np.array([r['teacher'] for r in labels],np.float32);xs.append(x);ys.append(target[:,1:].astype(float)-base[:,1:].astype(float));allbase.append(base);allteacher.append(target);roadstats.append(dict(road=road,queries=len(labels),first_steering_disagreement_fraction=float(np.mean(base[:,0]!=target[:,0])),first_steering_absdelta_mean=float(np.mean(abs(base[:,0]-target[:,0]))),pedal_delta_MAE=np.mean(abs(ys[-1]),axis=0).tolist(),initialization_invalid_queries=sum(not r['initialization_all_exact'] for r in receipts)))
 teacher_cost=dict(queries=totalq,query_cap=600,model_clones=clones,positive_physics_ticks=modelticks,zero_time_world_initializations=clones,query_CPU_s=modelcpu,query_wall_s=querywall,phase_wall_s=time.time()-read(D/'teacher-opening.json')['epoch'],road_stats=roadstats,solver_history_not_restored=True,future_teacher_steering_not_student_steering=True);save(D/'teacher-cost.json',teacher_cost)
 start,cpu=time.perf_counter(),time.process_time();N=sum(len(x) for x in xs);weight=np.concatenate([np.full(len(x),N/(6*len(x))) for x in xs]);x=np.concatenate(xs);y=np.concatenate(ys);mean=np.average(x,axis=0,weights=weight);std=np.maximum(np.sqrt(np.average((x-mean)**2,axis=0,weights=weight)),1e-6);z=np.c_[(x-mean)/std,np.ones(N)];penalty=np.eye(17);penalty[-1,-1]=0;w=np.linalg.solve(z.T@(weight[:,None]*z)+penalty,z.T@(weight[:,None]*y));cfg=archive(D,p,model_text(mean,std,w),'candidate306');save(D/'candidate-config.json',cfg);save(D/'fit-receipt.json',dict(rows=N,features=16,pedal_coefficients=34,lambda_=1,bias_penalty=0,equal_road_mass=N/6,old_labels_used=0,fit_count=1,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu,candidate_sha256=cfg['archive_sha256'],weighted_train_residual_RMSE=np.sqrt(np.average((np.clip(z@w,-.5,.5)-y)**2,axis=0,weights=weight)).tolist()))
 # Exact-zero residual replay uses stored actual pixels and actions, no simulator.
 zero=archive(D,p,model_text(mean,std,np.zeros((17,2))),'zero306');verified=0;zcpu=0.;zwall=time.perf_counter()
 for road in p['collection_roads']:
  cache=np.load(D/'collection'/road/'observations-actions-private.npz');worker=actor(zero,D/'zero-replay'/road,p['sandbox_path']);rows=[json.loads(s) for s in (D/'collection'/road/'trace-private.jsonl').read_text().splitlines()]
  try:
   worker.call('reset',cache['observations'][0])
   for obs,a,row in zip(cache['observations'],cache['actions'],rows):
    response,_=worker.call('act',obs);assert np.array_equal(np.array(response['action'],np.float32),a) and response['features']==row['features'];ack,_=worker.call('commit',a);assert ack['memory']==row['memory'];verified+=1;zcpu=max(zcpu,ack['actor_cumulative_CPU_s'])
  finally:
   reaped=worker.close();assert reaped['process_reaped'] and reaped['actor_pids_absent']
 save(D/'zero-replay-receipt.json',dict(verified_actions=verified,bit_exact_action_features_memory=True,new_native=0,wall_s=time.perf_counter()-zwall,last_actor_CPU_s=zcpu));print('one fit frozen; zero replay verified '+str(verified),flush=True)

def close(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage306';p=verify(D);assert not (D/'cost.json').exists();collection=read(D/'collection-results-private.json');evaluation=read(D/'evaluation-results-private.json');assert len(collection)==6 and len(evaluation)==18 and all(not x['technical_error'] and not x['censored'] for x in collection+evaluation)
 fit=read(D/'fit-receipt.json');teacher=read(D/'teacher-cost.json');assert sha(Path(read(D/'candidate-config.json')['archive_path']))==fit['candidate_sha256'];budget=read(D/'budget.json');rr=collection+evaluation;assert sum(x['native_actions'] for x in rr)==budget['actions']<=12000
 prior=R/'project-effective-budget-v314.json';v=read(prior);cost=dict(stage=306,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),new_wrapper_actions=budget['actions'],native_cap=12000,collection_native=budget['collection'],evaluation_native=budget['evaluation'],raw_step_ticks=sum(x['raw_step_ticks'] for x in rr),raw_reset_ticks=sum(x['raw_reset_ticks'] for x in rr),runner_CPU_s=sum(x['runner_CPU_s'] for x in rr),actor_CPU_s=sum(x['actor_CPU_s'] for x in rr),teacher_pixel_actor_CPU_s=sum(x['teacher_pixel_actor_CPU_s'] for x in collection),source_capture_wall_s=sum(x['capture_wall_s'] for x in collection),collection_wall_s=read(D/'collection-phase-receipt.json')['wall_s'],evaluation_wall_s=read(D/'evaluation-phase-receipt.json')['wall_s'],teacher=teacher,fit_CPU_s=fit['CPU_s'],fit_wall_s=fit['wall_s'],zero_replay=read(D/'zero-replay-receipt.json'),B_operating_cap=1240000,actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions']+budget['actions'],research_remaining=v['research_remaining']-budget['actions'],final_reserved_actions=84000,final_reserve_used=0,new_paid_resources=0)
 for r in rr:assert r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent']
 assert sha(R/'current-champion.json')==sha(D/'previous-current-champion.json');save(D/'cost.json',cost);v.update(version=315,prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage306_new_wrapper_actions=budget['actions']);assert not (R/'project-effective-budget-v315.json').exists();save(R/'project-effective-budget-v315.json',v);ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==306 for s in ledger.read_text().splitlines())
 with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
 safe=lambda r:{k:r.get(k) for k in ['road','completed','actual_DNF','censored','technical_error','lap_ms','damage','native_actions','retire_reason']};base=p['baseline296']['results'];subsets=[]
 for name,roads in [('collection6',p['collection_roads']),('remaining12',[r for r in p['roads'] if r not in p['collection_roads']])]:
  a=[r for r in evaluation if r['road'] in roads];b=[r for r in base if r['road'] in roads];subsets.append(dict(subset=name,candidate_completions=sum(r['completed'] for r in a),baseline_completions=sum(r['completed'] for r in b),paired=diagnose(a,b)))
 d=diagnose(evaluation,base);nc=sum(r['completed'] for r in evaluation);bc=sum(r['completed'] for r in base);passes=nc>bc or(nc==bc and d['common_mean_delta_ms'] is not None and d['common_mean_delta_ms']<0);pub=dict(stage=306,baseline=[safe(r) for r in base],evaluation=[safe(r) for r in evaluation],collection_roads=p['collection_roads'],collection=[safe(r) for r in collection],completion_first_pass=passes,paired=d,subsets=subsets,cost=cost,fit=fit,champion296_maintained=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,automatic_next_experiment=False);save(G/'retry/pedal306_result.json',pub);print(json.dumps(dict(completions=nc,baseline_completions=bc,passes=passes,paired=d,subsets=subsets,native=budget['actions'],remaining=cost['research_remaining']),indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('phase',choices=['prepare','collection','teachfit','evaluation','close']);a.add_argument('--private-root',type=Path,required=True);x=a.parse_args();R=x.private_root.resolve()
 if x.phase in ['collection','evaluation']:episodes(R,x.phase)
 else:globals()[x.phase](R)
