"""Fixed4x8 CEM, whole6TRAIN archive, exactcache, frozenwinner4DEV."""
import argparse,json,time,datetime,subprocess,sys,os
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.cem294_build import build,LOW,HIGH
ROADS=['O0','O2','N0','N1','N2','N3']

def config(p,theta,F):
 q=F/'config.json'
 if q.exists():return read(q)
 c=dict(p['base']);c.update({k:v for k,v in build(p['base']['archive_path'],theta,F/'policy.zip').items() if k in ['archive_path','archive_sha256','members_sha256']});save(q,c);return c

def episode_jobs(D,p,entries,phase):
 # Max2separate simulation processes; budget capacities allocated in fixedorder.
 phasecap=p['training_cap'] if phase=='training' else p['evaluation_cap'];remaining=phasecap-read(D/'budget.json')[phase];pending=[];records=[]
 for e in entries:
  F=Path(e['folder']);q=F/'result.json'
  if q.exists():records.append(read(q));continue
  if F.exists():raise RuntimeError('Unfinished episode preserved; no automatic native replay: '+str(F))
  cap=min(2000,remaining);remaining-=cap
  if cap<=0:break
  F.mkdir(parents=True,mode=0o700);job=dict(private_stage=str(D),phase=phase,native_cap=cap,**{k:v for k,v in e.items() if k!='folder'});save(F/'job.json',job);log=(F/'driver-private.log').open('x');(F/'driver-private.log').chmod(0o600);env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1');proc=subprocess.Popen([sys.executable,'-m','retry.cem294_episode','--job',str(F/'job.json')],stdout=log,stderr=subprocess.STDOUT,env=env);pending.append((F,proc,log))
 for F,proc,log in pending:
  rc=proc.wait();log.close();assert (F/'result.json').exists(),f'Technical child exit{rc}: {F}';records.append(read(F/'result.json'))
 return records

def evaluate(D,p,label,theta,cfg):
 F=D/'policies'/label;F.mkdir(parents=True,exist_ok=True,mode=0o700);q=F/'evaluation.json'
 if q.exists():return read(q)
 results=[]
 for i in range(0,6,2):
  entries=[dict(folder=str(F/r),road=r,case=p['cases'][r],config=cfg,initial_observation_sha256=p['initial_observations'][r],ceiling=float(45*np.exp(theta[5])),steering_gain=float(np.exp(theta[2]))) for r in ROADS[i:i+2]];results+=episode_jobs(D,p,entries,'training')
  save(F/'partial.json',results)
 result=dict(label=label,theta=list(theta),results=results,fully_observed=len(results)==6 and not any(x['technical_error'] or x['censored'] for x in results),complete6=len(results)==6 and all(x['completed'] and not x['technical_error'] and not x['censored'] for x in results),unexecuted=[r for r in ROADS if not any(x['road']==r for x in results)],native_actions=sum(x['native_actions'] for x in results),config=cfg)
 result['mean_lap_ms']=float(np.mean([x['lap_ms'] for x in results])) if result['complete6'] else None;save(q,result);return result

def rank(a):return (a['mean_lap_ms'],float(np.linalg.norm(a['theta'])),a['ordinal'])
def preflight(D,p):
 from retry.frozen_composite_runtime import prepare
 if (D/'zero-receipt.json').exists():return
 z=np.load(D.parent/'stage291/O0_baseline240/observations-private.npz');workers=[];n=0
 try:
  for label,c in [('base',p['base']),('zero',read(D/'zero-config.json'))]:workers.append(prepare(c,D/('preflight-'+label),p['sandbox_path']))
  obs=z['pixels'][0].astype(np.float32)/255
  for w in workers:w.call('reset',obs)
  for i in range(12):
   obs=z['pixels'][i].astype(np.float32)/255;r=[w.call('act',obs)[0] for w in workers];assert r[0]['action']==r[1]['action'] and r[0]['features']==r[1]['features'] and r[0]['nominal']==r[1]['nominal'] and r[0]['state']==r[1]['state']
   for w,x in zip(workers,r):c,_=w.call('commit',np.array(x['action'],np.float32));assert np.float32(c['memory'])==np.float32(x['action'][0])
   n+=1
 finally:
  reaping=[w.close() for w in workers]
 save(D/'zero-receipt.json',dict(passed=True,cached_actual_observations=n,zero_actions_features_nominal_state_exact=True,actual_steering_memory_exact=True,new_native=0,source_physics=0,reaping=reaping))

def run(R):
 D=R/'stage294';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(q)==h
 preflight(D,p);cp=D/'checkpoint.json';rng=np.random.default_rng(p['recipe']['seed'])
 if cp.exists():state=read(cp);rng.bit_generator.state=state['rng']
 else:
  baseline=dict(label='240',ordinal=0,theta=[0.]*6,mean_lap_ms=float(np.mean([p['baseline'][r]['lap_ms'] for r in ROADS])),complete6=True,fully_observed=True,cached=True,config=p['base']);state=dict(completed_generations=0,completed_policies=[],archive=[baseline],mean=[0.]*6,variance=(np.array(p['recipe']['initial_sigma'])**2).tolist(),rng=rng.bit_generator.state,active_draws=None,technical_error=None,started_epoch=time.time());save(cp,state)
 try:
  for gen in range(state['completed_generations'],4):
   assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp()
   if state['active_draws'] is None:
    draws=np.clip(rng.normal(np.array(state['mean']),np.sqrt(state['variance']),size=(8,6)),LOW,HIGH).tolist();state['active_draws']=draws;state['rng']=rng.bit_generator.state;save(cp,state)
   for j,theta in enumerate(state['active_draws']):
    ordinal=gen*8+j+1;label=f'g{gen+1}p{j+1}'
    existing=next((x for x in state['completed_policies'] if x['ordinal']==ordinal),None)
    if existing:continue
    if read(D/'budget.json')['training']>=p['training_cap']:raise RuntimeError('TRAINbudget exhausted; unfinished generation preserved')
    F=D/'policies'/label;F.mkdir(parents=True,exist_ok=True,mode=0o700);key=np.asarray(theta,np.float64).tobytes().hex();same=next((x for x in state['completed_policies'] if x['cache_key']==key),None)
    if same:result=dict(read(D/'policies'/same['label']/'evaluation.json'),label=label,cached_from=same['label']);save(F/'evaluation.json',result)
    elif all(x==0 for x in theta):result=dict(state['archive'][0],label=label,cached_from='240');save(F/'evaluation.json',result)
    else:result=evaluate(D,p,label,theta,config(p,theta,F))
    item=dict(ordinal=ordinal,label=label,theta=theta,cache_key=key,complete6=result['complete6'],fully_observed=result['fully_observed'],mean_lap_ms=result['mean_lap_ms'],native_actions=result.get('native_actions',0),cached_from=result.get('cached_from'));state['completed_policies'].append(item)
    if result['complete6']:state['archive'].append(dict(item,config=result['config']))
    save(cp,state);print(json.dumps(dict(generation=gen+1,policy=j+1,complete6=item['complete6'],mean_lap_ms=item['mean_lap_ms'],native=read(D/'budget.json')['training'],archive_best=min(state['archive'],key=rank)['mean_lap_ms'])),flush=True)
    if not result['fully_observed'] and not any(x.get('technical_error') for x in result.get('results',[])):raise RuntimeError('Budgetcensored/unexecuted policy excluded; remaining work preserved')
   elite=sorted(state['archive'],key=rank)[:3];E=np.array([a['theta'] for a in elite]);state['mean']=(.5*np.array(state['mean'])+.5*E.mean(0)).tolist();state['variance']=np.maximum(.5*np.array(state['variance'])+.5*E.var(0),.015**2).tolist();state['completed_generations']=gen+1;state['active_draws']=None;save(cp,state);save(D/f'generation{gen+1}-receipt.json',dict(elite=[x['label'] for x in elite],mean=state['mean'],sigma=np.sqrt(state['variance']).tolist(),archive_count=len(state['archive'])));print('Generation'+str(gen+1)+' complete',flush=True)
  winner=min(state['archive'],key=rank);gate=winner['mean_lap_ms']<state['archive'][0]['mean_lap_ms'];winnerpath=D/'winner-frozen.json'
  if not winnerpath.exists():save(winnerpath,dict(winner=winner,strict_TRAIN_improvement=gate,baseline_mean_lap_ms=state['archive'][0]['mean_lap_ms'],registration_sha256=p['registration_sha256'],frozen_epoch=time.time(),all32policies_finished=True))
  assert read(winnerpath)['winner']==winner
  dev=[]
  if gate:
   meta=read(p['registration']);save(D/'screen-opening.json',dict(winner_sha256=sha(winnerpath),no_retune=True)) if not (D/'screen-opening.json').exists() else None
   for index,case in enumerate(meta['cases']):
    road=f'S294{index}';pairs=[]
    # Paired arms run in registered AB/BA order, sequential within eachroad.
    for arm in case['arm_order']:
     cfg=p['base'] if arm=='A' else winner['config'];t=[0.]*6 if arm=='A' else winner['theta'];pairs+=episode_jobs(D,p,[dict(folder=str(D/'DEV'/road/arm),road=road,case=case,config=cfg,ceiling=float(45*np.exp(t[5])),steering_gain=float(np.exp(t[2])))],'evaluation')
    dev.append(dict(road=road,arm_order=case['arm_order'],results=pairs));save(D/'DEV-results-private.json',dev)
    if len(pairs)<2 or any(x['technical_error'] or x['censored'] for x in pairs):raise RuntimeError('DEVtechnical/budgetcensor; no replacement')
  save(D/'search-outcome.json',dict(completed=True,technical_error=None,completed_generations=state['completed_generations'],evaluated_new_policies=len(state['completed_policies']),winner=winner,strict_TRAIN_improvement=gate,DEV=dev,budget=read(D/'budget.json'),wall_s=time.time()-state['started_epoch']))
 except BaseException as e:
  state['technical_error']=type(e).__name__+': '+str(e);save(cp,state);save(D/'search-outcome.json',dict(completed=False,technical_error=state['technical_error'],completed_generations=state['completed_generations'],evaluated_new_policies=len(state['completed_policies']),budget=read(D/'budget.json'),wall_s=time.time()-state['started_epoch']));print(state['technical_error'],flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
