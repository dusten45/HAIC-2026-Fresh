"""Completionfirst18TRAIN CEM, wholeofficialcache, frozenwinner12DEV only."""
import argparse,time,json,datetime
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.cem294_search import config,episode_jobs
from retry.cem294_build import LOW,HIGH
from retry.reliability296_run import judge

def key(theta):return np.asarray(theta,np.float64).tobytes().hex()
def metrics(results):
 complete=[r for r in results if r['completed']];return dict(completions=len(complete),own_complete_mean_ms=float(np.mean([r['lap_ms'] for r in complete])) if complete else None)
def rank(a):return (-a['completions'],a['own_complete_mean_ms'] if a['own_complete_mean_ms'] is not None else float('inf'),float(np.linalg.norm(a['theta'])),a['ordinal'])
def diagnose(results,baseline):
 rr={r['road']:r for r in results};bb={r['road']:r for r in baseline};common=[r for r in rr if rr[r]['completed'] and bb[r]['completed']];return dict(paired_additional_completions=sum(rr[r]['completed'] and not bb[r]['completed'] for r in rr),paired_lost_completions=sum(not rr[r]['completed'] and bb[r]['completed'] for r in rr),common_completions=len(common),common_mean_delta_ms=float(np.mean([rr[r]['lap_ms']-bb[r]['lap_ms'] for r in common])) if common else None,completion_sets_equal={r for r in rr if rr[r]['completed']}=={r for r in bb if bb[r]['completed']})

def evaluate(D,p,label,theta,cfg,cache):
 F=D/'policies'/label;F.mkdir(parents=True,exist_ok=True,mode=0o700);q=F/'evaluation.json'
 if q.exists():return read(q)
 prior={}
 for c in cache:
  if key(c['theta'])==key(theta):
   for r in c['results']:prior[r['road']]=r
 results=[];new=0;reused=0
 for i in range(0,18,2):
  roads=p['roads'][i:i+2];jobs=[]
  for road in roads:
   if road in prior:continue
   jobs.append(dict(folder=str(F/road),road=road,case=p['cases'][road],config=cfg,initial_observation_sha256=p['initial_observations'].get(road),ceiling=float(45*np.exp(theta[5])),steering_gain=float(np.exp(theta[2]))))
  fresh=episode_jobs(D,p,jobs,'training') if jobs else [];new+=sum(r['native_actions'] for r in fresh);mapping={r['road']:r for r in fresh}
  for road in roads:
   if road in prior:results.append(prior[road]);reused+=1
   elif road in mapping:results.append(mapping[road])
  save(F/'partial.json',dict(results=results,reused_roads=reused,new_native=new))
  if len(fresh)<len(jobs) or any(r['censored'] for r in fresh):break
 fully=len(results)==18 and not any(r['technical_error'] or r['censored'] for r in results);m=metrics(results);diag=diagnose(results,p['baseline296']['results']) if fully else None;out=dict(label=label,theta=theta,config=cfg,results=results,fully_observed=fully,new_native=new,reused_TRAIN_roads=reused,unexecuted=[r for r in p['roads'] if not any(x['road']==r for x in results)],**m,against296=diag);save(q,out);return out

def run(R):
 D=R/'stage297';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(q)==h,q
 rng=np.random.default_rng(297);cp=D/'checkpoint.json';cache=read(D/'TRAIN-cache-private.json')
 if cp.exists():s=read(cp);rng.bit_generator.state=s['rng']
 else:
  archive=[dict(a,**metrics(a['results']),fully_observed=True,cached=True) for a in p['initial_archive']];s=dict(completed_generations=0,completed_policies=[],archive=archive,mean=p['recipe']['initial_mean'],variance=(np.array(p['recipe']['initial_sigma'])**2).tolist(),rng=rng.bit_generator.state,active_draws=None,technical_error=None,started_epoch=time.time());save(cp,s)
 for item in s['completed_policies']:
  e=read(D/'policies'/item['label']/'evaluation.json');cache.append(dict(theta=e['theta'],config=e['config'],results=[r for r in e['results'] if not r['technical_error'] and not r['censored']]))
 dev=[];winner=None;error=None
 try:
  for gen in range(s['completed_generations'],2):
   assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp()
   if s['active_draws'] is None:s['active_draws']=np.clip(rng.normal(np.array(s['mean']),np.sqrt(s['variance']),size=(8,6)),LOW,HIGH).tolist();s['rng']=rng.bit_generator.state;save(cp,s)
   for j,theta in enumerate(s['active_draws']):
    ordinal=2+8*gen+j;label=f'g{gen+1}p{j+1}'
    if any(x['ordinal']==ordinal for x in s['completed_policies']):continue
    if read(D/'budget.json')['training']>=85000:raise RuntimeError('TRAINcap reached; preserveunfinishedgeneration, no extension')
    F=D/'policies'/label;F.mkdir(parents=True,exist_ok=True,mode=0o700);same=next((c for c in cache if key(c['theta'])==key(theta) and len(c['results'])==18),None);cfg=same['config'] if same else config(p,theta,F);e=evaluate(D,p,label,theta,cfg,cache);item=dict(label=label,ordinal=ordinal,theta=theta,config=cfg,fully_observed=e['fully_observed'],completions=e['completions'],own_complete_mean_ms=e['own_complete_mean_ms'],against296=e['against296'],new_native=e['new_native'],reused_TRAIN_roads=e['reused_TRAIN_roads']);s['completed_policies'].append(item)
    if e['fully_observed']:s['archive'].append(dict(item,results=e['results']))
    cache.append(dict(theta=theta,config=cfg,results=[r for r in e['results'] if not r['technical_error'] and not r['censored']]));save(cp,s);best=min(s['archive'],key=rank);print(json.dumps(dict(generation=gen+1,policy=j+1,completions=item['completions'],own_complete_mean_ms=item['own_complete_mean_ms'],fully_observed=item['fully_observed'],new_native=read(D/'budget.json')['training'],best_label=best['label'],best_completions=best['completions'],best_mean_ms=best['own_complete_mean_ms'])),flush=True)
    if not e['fully_observed'] and (e['unexecuted'] or any(r['censored'] for r in e['results'])):raise RuntimeError('TRAINbudget/unfinished policy excluded; no forcedselection')
   elite=sorted(s['archive'],key=rank)[:3];E=np.array([a['theta'] for a in elite]);s['mean']=(.5*np.array(s['mean'])+.5*E.mean(0)).tolist();s['variance']=np.maximum(.5*np.array(s['variance'])+.5*E.var(0),.015**2).tolist();s['completed_generations']=gen+1;s['active_draws']=None;save(cp,s);save(D/f'generation{gen+1}-receipt.json',dict(elite=[a['label'] for a in elite],mean=s['mean'],sigma=np.sqrt(s['variance']).tolist(),archive_count=len(s['archive'])));print('Generation'+str(gen+1)+' complete',flush=True)
  winner=min(s['archive'],key=rank);frozen=D/'winner-frozen.json'
  if not frozen.exists():save(frozen,dict(winner=winner,all16draws_processed=True,frozen_epoch=time.time(),freshDEV_used_for_selection=False,baseline296_archive_hash=p['baseline296']['config']['archive_sha256']))
  assert read(frozen)['winner']==winner
  if winner['label']!='296':
   if not (D/'screen-opening.json').exists():save(D/'screen-opening.json',dict(winner_sha256=sha(frozen),epoch=time.time(),single_candidate_only=True))
   for case in p['fresh_DEV']:
    pair={}
    for arm in case['arm_order']:
     c=p['baseline296'] if arm=='A' else winner;t=c['theta'];jobs=[dict(folder=str(D/'DEV'/case['public_label']/arm),road=case['public_label'],case=case,config=c['config'],ceiling=float(45*np.exp(t[5])),steering_gain=float(np.exp(t[2])))];rr=episode_jobs(D,p,jobs,'evaluation')
     if rr:pair[arm]=rr[0]
    dev.append(dict(road=case['public_label'],arm_order=case['arm_order'],results=pair));save(D/'DEV-records-private.json',dev);print(json.dumps(dict(DEVroad=case['public_label'],results={a:{k:r.get(k) for k in ['completed','actual_DNF','censored','technical_error','lap_ms']} for a,r in pair.items()},native=read(D/'budget.json')['evaluation'])),flush=True)
    if set(pair)!={'A','B'} or any(r['censored'] or r['technical_error'] for r in pair.values()):raise RuntimeError('DEVcap/technicalunknown; preserve296, no alternatecandidate')
  judgment=judge([x['results'] for x in dev]) if len(dev)==12 else None
  if judgment:judgment.update(winner=winner['label'] if judgment['candidate_outranks'] else '296')
  save(D/'search-outcome.json',dict(completed=True,technical_error=None,completed_generations=s['completed_generations'],sampled_policies=len(s['completed_policies']),winner=winner,DEV=dev,judgment=judgment,budget=read(D/'budget.json'),wall_s=time.time()-s['started_epoch']))
 except BaseException as e:
  error=type(e).__name__+': '+str(e);s['technical_error']=error;save(cp,s);save(D/'search-outcome.json',dict(completed=False,technical_error=error,completed_generations=s['completed_generations'],sampled_policies=len(s['completed_policies']),winner=winner,DEV=dev,judgment=None,budget=read(D/'budget.json'),wall_s=time.time()-s['started_epoch']));print(error,flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
