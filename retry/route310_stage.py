"""Six single-coefficient pixel route-cost screens, one frozen12-road extension."""
import argparse,datetime,hashlib,json,time,zipfile
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.completion297_search import metrics,diagnose

COEFFICIENTS=[('length',1.),('clearance',2.),('connection',1.)]
def package(p,F,coordinate,factor):
 G=Path(__file__).resolve().parent.parent
 with zipfile.ZipFile(p['baseline296']['config']['archive_path']) as z:members={n:z.read(n) for n in z.namelist()}
 original=members['retry/connected_agent.py'];s=original.decode();needle='next_cost = cost + length * (1 + 2 / max(float(distance[ny, nx]), 1.5))';assert s.count(needle)==1
 if coordinate=='length':s=s.replace(needle,f'next_cost = cost + length * ({factor!r} + 2 / max(float(distance[ny, nx]), 1.5))')
 elif coordinate=='clearance':s=s.replace(needle,f'next_cost = cost + length * (1 + {2*factor!r} / max(float(distance[ny, nx]), 1.5))')
 elif coordinate=='connection':
  needle='def choose_route(candidates, speed, previous_steer, connection_weight=1.0):';assert s.count(needle)==1;s=s.replace(needle,f'def choose_route(candidates, speed, previous_steer, connection_weight={factor!r}):')
 else:assert coordinate=='identity'
 members['retry/connected_agent.py']=s.encode();members['retry/route310_original.py']=original;archive=F/'policy.zip'
 with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
  for n,b in sorted(members.items()):item=zipfile.ZipInfo(n,date_time=(2026,10,9,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,b)
 archive.chmod(0o600);cfg=dict(p['baseline296']['config'],archive_path=str(archive),archive_sha256=sha(archive),members_sha256={n:hashlib.sha256(b).hexdigest() for n,b in members.items()},worker_path=str(G/'retry/route310_worker.py'),worker_sha256=sha(G/'retry/route310_worker.py'));save(F/'candidate-config.json',cfg);return cfg

def prepare(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage310';assert not D.exists(),'Existing310:no duplicate';D.mkdir(mode=0o700);v=read(R/'project-effective-budget-v318.json');assert v['research_remaining']==19541 and v['B_operating_cap']==1330000;old=read(R/'stage299/plan.json');screen=['T2950','T2953','T2956','T2959','O0','O2'];baseline=old['baseline296'];p=dict(stage=310,deadline_utc='2026-10-16T10:01:55+00:00',baseline296=baseline,base_controller_theta=baseline['theta'],screen=screen,extension=[r for r in old['roads'] if r not in screen],roads=old['roads'],cases=old['cases'],initial_observations=old['initial_observations'],sandbox_path=old['sandbox_path'],phase_caps=dict(screen=16000,extension=16000),native_cap=16000,coefficients=COEFFICIENTS,rule='One existing routecostcoefficient only x.8/x1.2: edge length1, softclearance2, connectionweight1. No feasibility/detection/tracking/head/controller/pedal/steering/lookahead changes.',rank='Screencomplete6 only: -completioncount, owncompletedmeanlap,296priority,ordinal. Freezeonewinner; if296 stop else remaining12 once; no runnerup or DEV/adoption.',prior_difference='134/135 compares connection0/1,171 holds near-score passing-side tie,123 changes hardmargin,304 changes cost anchor toHUDwheel,305 recoversemptyroute,294/297 changescontrollerparams,309 finalpedals. No same.8/1.2 coefficient experiment found:189 archivedconnected implementations hadunchangededge1+2/d, examinedchoose defaults1.0; controller gain and steeringconnection cost are different.',cost_relationship='length/clearance partially coupled inedge ratio, butlength changes overallbasegap scale too; differentexisting occurrences, notsixindependentdirections.',cached_geometry_or_GT_used=False)
 candidates=[]
 for name,value in COEFFICIENTS:
  for factor in [.8,1.2]:
   label=name+('080' if factor==.8 else '120');F=D/'candidates'/label;F.mkdir(parents=True,mode=0o700);cfg=package(p,F,name,factor);candidates.append(dict(label=label,ordinal=len(candidates)+1,coordinate=name,original_value=value,new_value=value*factor,factor=factor,config=cfg))
 p['candidates']=candidates;names=['route310_stage.py','route310_worker.py','route310_episode.py','route310_jobs.py'];sources=[G/'retry'/n for n in names]+[Path(baseline['config']['archive_path']),R/'project-effective-budget-v318.json']+[Path(c['config']['archive_path']) for c in candidates];p['hashes']={str(q):sha(q) for q in sources};save(D/'previous-current-champion.json',read(R/'current-champion.json'));save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'budget.json',dict(actions=0,screen=0,extension=0));print('310registered sixcoefficientsinglechanges, screen6each, oneconditional12extension, cap16000',flush=True)
def verify(D):
 p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
 for q,h in p['hashes'].items():
  if Path(q).name=='route310_stage.py' and (D/'source-repair.json').exists():
   repair=read(D/'source-repair.json');assert repair['initial_sha256']==h and repair['repaired_sha256']==sha(q)
  else:assert sha(q)==h,q
 return p

def identity(R):
 from retry.frozen_composite_runtime import prepare as worker
 D=R/'stage310';p=verify(D);F=D/'identity';assert not F.exists();F.mkdir(mode=0o700);cfg=package(p,F,'identity',1.);z=np.load(R/'stage306/collection/O0/observations-actions-private.npz');rows=[json.loads(s) for s in (R/'stage306/collection/O0/trace-private.jsonl').read_text().splitlines()];w=worker(cfg,F/'cpu',p['sandbox_path']);n=0
 try:
  w.call('reset',z['observations'][0])
  for obs,a,r in zip(z['observations'],z['actions'],rows):
   response,_=w.call('act',obs);assert response['action']==a.tolist() and response['features']==r['features'] and not response['route_audit']['path_changed'];ack,_=w.call('commit',a);assert ack['memory']==r['memory'];n+=1
 finally:reaping=w.close()
 assert reaping['process_reaped'] and reaping['actor_pids_absent'];save(D/'identity-receipt.json',dict(actual_cached_actions=n,identity_action_feature_memory_path_exact=True,native=0,extra_route_diagnostic_does_not_change_policy=True));print('310identity exact304 cachedinputs',flush=True)

def evaluate(D,p,c,roads,phase):
 from retry.route310_jobs import jobs
 rr=[];t=p['base_controller_theta']
 for i in range(0,len(roads),2):
  entries=[dict(folder=str(D/'evaluations'/phase/c['label']/r),road=r,case=p['cases'][r],initial_observation_sha256=p['initial_observations'].get(r),config=c['config'],ceiling=float(45*np.exp(t[5])),steering_gain=float(np.exp(t[2]))) for r in roads[i:i+2]];out=jobs(D,p,entries,phase);rr+=out;save(D/(phase+'-'+c['label']+'-partial.json'),rr)
  if len(out)<len(entries) or any(x['censored'] or x['technical_error'] for x in out):break
 return dict(c,results=rr,fully_observed=len(rr)==len(roads) and not any(x['censored'] or x['technical_error'] for x in rr),**metrics(rr))
def rank(c):return(-c['completions'],c['own_complete_mean_ms'] if c['own_complete_mean_ms'] is not None else float('inf'),0 if c['label']=='296' else 1,c['ordinal'])
def run(R):
 D=R/'stage310';p=verify(D);assert read(D/'identity-receipt.json')['identity_action_feature_memory_path_exact'];assert not (D/'opening.json').exists();save(D/'opening.json',dict(epoch=time.time()));base=[x for x in p['baseline296']['results'] if x['road'] in p['screen']];archive=[dict(label='296',ordinal=0,fully_observed=True,results=base,**metrics(base))];rr=[];winner=None;extension=[];error=None
 try:
  for c in p['candidates']:
   e=evaluate(D,p,c,p['screen'],'screen');rr.append(e);save(D/'screen-results-private.json',rr);assert e['fully_observed'],'Incomplete screen, no forcedselection';archive.append(e);print(json.dumps(dict(screen_candidate=e['label'],completions=e['completions'],ownmean_ms=e['own_complete_mean_ms'],native=read(D/'budget.json')['actions'])),flush=True)
  winner=min(archive,key=rank);save(D/'winner-frozen.json',dict(winner=winner,all6screen_complete=True,frozen_epoch=time.time(),no_DEV_or_extension_selection=True));print('310screen winner '+winner['label'],flush=True)
  if winner['label']!='296':
   e=evaluate(D,p,winner,p['extension'],'extension');extension=e['results'];save(D/'extension-results-private.json',e);assert e['fully_observed'],'Incomplete extension, no runnerup or DNFconversion'
 except BaseException as e:error=type(e).__name__+': '+str(e);print(error,flush=True)
 save(D/'outcome-private.json',dict(screen=rr,winner=winner,extension=extension,technical_error=error,wall_s=time.time()-read(D/'opening.json')['epoch']));print('310execution closed',flush=True)

def close(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage310';p=verify(D);o=read(D/'outcome-private.json');assert not (D/'cost.json').exists();rr=[read(q) for q in (D/'evaluations').glob('*/*/*/result.json')];b=read(D/'budget.json');assert sum(x['native_actions'] for x in rr)<=b['actions']<=16000;signals=[]
 for q in (D/'evaluations').glob('*/*/*/result.json'):
  r=read(q);assert r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent'];rows=[json.loads(s) for s in (q.parent/'trace-private.jsonl').read_text().splitlines()];signals.append(dict(phase=q.parent.parent.parent.name,candidate=q.parent.parent.name,road=r['road'],actions=len(rows),path_changed_actions=sum(x['route_audit']['path_changed'] for x in rows),first_path_change=next((x['step'] for x in rows if x['route_audit']['path_changed']),None),multiple_route_candidate_actions=sum(x['route_audit']['candidate_count']>1 for x in rows)))
 v=read(R/'project-effective-budget-v318.json');cost=dict(stage=310,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),new_wrapper_actions=b['actions'],native_cap=16000,screen_native=b['screen'],extension_native=b['extension'],new_official_runs=len(rr),new_source_physics_ticks=0,new_fits=0,new_paid_resources=0,raw_step_ticks=sum(r['raw_step_ticks'] for r in rr),raw_reset_ticks=sum(r['raw_reset_ticks'] for r in rr),runner_CPU_s=sum(r['runner_CPU_s'] for r in rr),actor_CPU_s=sum(r['actor_CPU_s'] for r in rr),sum_episode_wall_s=sum(r['wall_s'] for r in rr),total_wall_s=o['wall_s'],B_operating_cap=1330000,actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions']+b['actions'],research_remaining=v['research_remaining']-b['actions'],final_reserved_actions=84000,final_reserve_used=0);save(D/'cost.json',cost);prior=R/'project-effective-budget-v318.json';v.update(version=319,prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage310_new_wrapper_actions=b['actions']);assert not (R/'project-effective-budget-v319.json').exists();save(R/'project-effective-budget-v319.json',v);ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==310 for s in ledger.read_text().splitlines())
 with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
 assert sha(R/'current-champion.json')==sha(D/'previous-current-champion.json');base=[x for x in p['baseline296']['results'] if x['road'] in p['screen']];screen=[dict(label='296',ordinal=0,completions=sum(x['completed'] for x in base),own_complete_mean_ms=metrics(base)['own_complete_mean_ms'],against296=diagnose(base,base))]+[{k:e[k] for k in ['label','ordinal','coordinate','factor','completions','own_complete_mean_ms','fully_observed']}|dict(against296=diagnose(e['results'],base) if e['fully_observed'] else None) for e in o['screen']];winner=o['winner'];full=winner['results']+o['extension'] if winner and winner['label']!='296' else p['baseline296']['results'];fully=len(full)==18 and all(not x['censored'] and not x['technical_error'] for x in full);safe=lambda x:{k:x.get(k) for k in ['road','completed','actual_DNF','censored','technical_error','lap_ms','damage','native_actions','retire_reason']};pub=dict(stage=310,coefficients=COEFFICIENTS,prior_difference=p['prior_difference'],cost_relationship=p['cost_relationship'],screen=screen,winner=winner['label'] if winner else None,full18=[safe(x) for x in full] if fully else None,full18_summary=dict(**metrics(full),against296=diagnose(full,p['baseline296']['results'])) if fully else None,signals=signals,cost=cost,technical_error=o['technical_error'],champion296_maintained=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,automatic_next_experiment=False);save(G/'retry/route310_result.json',pub);print(json.dumps(dict(screen=screen,winner=pub['winner'],full18_summary=pub['full18_summary'],cost=cost,technical_error=o['technical_error']),indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('phase',choices=['prepare','identity','run','close']);a.add_argument('--private-root',type=Path,required=True);x=a.parse_args();globals()[x.phase](x.private_root.resolve())
