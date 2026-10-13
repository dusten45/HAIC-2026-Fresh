"""One fixed parameter-noise pilot on six DEV roads, then fresh paired screens.

Completed episodes and fixed models are private durable transactions. An unfinished
native folder is never replayed. Pixel-derived features alone enter the actor.
"""
import argparse,json,hashlib,time,datetime
from pathlib import Path
import numpy as np


def run(path):
 from retry.frozen_composite_runtime import prepare
 from retry.diagnose import make_env
 from retry.ppo244_math import apply
 from retry.ars247_math import rms,update
 p=json.loads(path.read_text());D=path.parent
 def sha(q):return hashlib.sha256(Path(q).read_bytes()).hexdigest()
 def save(q,x):
  temp=q.with_name(q.name+'.tmp');temp.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');temp.chmod(0o600);temp.replace(q)
 def read(q):return json.loads(q.read_text())
 assert sha(path)==path.with_suffix('.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(q)==h
 fixed=np.load(p['parameters']);mean,std=fixed['mean'],fixed['std'];probes=fixed['probes'];cov=fixed['covariance']
 if not (D/'opening.json').exists():save(D/'opening.json',dict(start_epoch=time.time()))
 records=read(D/'records.json') if (D/'records.json').exists() else []
 def used(phase):return read(D/'budget.json')['phases'].get(phase,0)
 def episode(name,theta,label,case,phase):
  folder=D/'runs'/(name+'_'+label)
  if folder.exists():
   assert (folder/'result.json').exists(),'Unfinished native episode: no automatic replay'
   r=read(folder/'result.json')
   if not any(x['name']==name and x['label']==label and x['phase']==phase for x in records):records.append(r);save(D/'records.json',records)
   return r
  remain=min(p[phase+'_cap']-used(phase),19000-read(D/'budget.json')['actions'])
  if remain<=0:return None
  folder.mkdir(parents=True,mode=0o700);frozen=theta.copy();worker=env=None;rows=[];features=[];commands=[];latents=[];times=[];start=time.perf_counter();raw=0
  try:
   worker=prepare(p['base'],folder/'cpu',p['sandbox_path']);env=make_env();obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});start_t=env.unwrapped.t;reset_ticks=round(start_t*50);initial=hashlib.sha256(obs.tobytes()).hexdigest();geometry=hashlib.sha256(np.asarray(env.unwrapped.track,dtype='<f8').tobytes()).hexdigest();assert geometry==case['road_geometry_sha256'];worker.call('reset',obs)
   for step in range(1,min(2000,remain)+1):
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp()
    response,ms=worker.call('act',obs);tic=time.perf_counter();f=np.asarray(response['legal_feature_audit']['features'],float);x=np.r_[(f-mean)/std,1.];z=x@frozen;base=np.asarray(response['action'],np.float32);action=apply(base,z);costms=ms+(time.perf_counter()-tic)*1000;assert costms<=5000 and action[0]==base[0]
    b=read(D/'budget.json');assert b['actions']<19000;b['actions']+=1;b['phases'][phase]=b['phases'].get(phase,0)+1;save(D/'budget.json',b)
    before=env.unwrapped.t;obs,_,ended,truncated,info=env.step(action);ticks=round((env.unwrapped.t-before)*50);raw+=ticks;completed=env.unwrapped.finish_time_s is not None;official_limit=step>=2000 and not completed;terminal=bool(ended or truncated or official_limit);progress=env.unwrapped.tile_visited_count/len(env.unwrapped.track);speed=float(np.linalg.norm(env.unwrapped.car.hull.linearVelocity))
    rows.append(dict(action=step,speed_m_s=speed,visited=env.unwrapped.tile_visited_count,damage=env.damage.damage,collision=bool(info.get('collision')),off_track_counter=env.off_track_counter,raw_ticks=ticks,terminal=terminal));features.append(f);commands.append(action);latents.append(z);times.append(costms)
    if terminal or step==min(2000,remain):break
   assert np.array_equal(frozen,theta)
   lap=round((env.unwrapped.finish_time_s-start_t)*1000) if completed else None
   ret=2-(env.unwrapped.finish_time_s-start_t)/160 if completed else progress-1 if terminal else None
   r=dict(name=name,label=label,phase=phase,native_actions=len(rows),completed=completed,actual_DNF=terminal and not completed,censored=not terminal,lap_ms=lap,return_value=ret,damage=env.damage.damage,visited=env.unwrapped.tile_visited_count,total_tiles=len(env.unwrapped.track),retire_reason=info.get('retire_reason') or ('max_steps' if official_limit else 'budget_cut' if not terminal else None),raw_step_ticks=raw,raw_reset_ticks=reset_ticks,initial_observation_sha256=initial,geometry_sha256=geometry,base_actor_CPU_s=response['actor_cumulative_CPU_s'],policy_ms=dict(median=float(np.median(times)),p95=float(np.percentile(times,95)),max=float(max(times))),wall_s=time.perf_counter()-start,parameter_SHA256=hashlib.sha256(frozen.tobytes()).hexdigest())
  finally:
   if worker:reaping=worker.close()
   if env:env.close()
  r['reaping']=reaping;save(folder/'diagnostic-private.json',rows);cache=folder/'legal-features-actions-latents-private.npz';np.savez_compressed(cache,features=np.asarray(features),actions=np.asarray(commands),latents=np.asarray(latents));cache.chmod(0o600);save(folder/'result.json',r);records.append(r);save(D/'records.json',records);print(json.dumps({k:r[k] for k in ['name','label','phase','completed','actual_DNF','censored','lap_ms','native_actions','return_value']}),flush=True)
  return r
 def evaluate(name,theta):
  rr=[]
  for label in p['road_order']:
   r=episode(name,theta,label,p['roads'][label],'training')
   if r is None:break
   rr.append(r)
   if r['censored']:break
  return dict(name=name,results=rr,all_roads_observed=len(rr)==6 and all(not r['censored'] for r in rr),completed=sum(r['completed'] for r in rr),actual_DNF=sum(r['actual_DNF'] for r in rr),censored=sum(r['censored'] for r in rr),unexecuted=6-len(rr),mean_lap_ms=float(np.mean([r['lap_ms'] for r in rr])) if len(rr)==6 and all(r['completed'] for r in rr) else None,mean_return=float(np.mean([r['return_value'] for r in rr])) if len(rr)==6 and all(not r['censored'] for r in rr) else None)
 error=None;cpu=time.process_time();candidates=[];screen=[]
 try:
  candidates=[p['baseline']]
  for i,theta in enumerate(probes):
   q=D/('probe'+str(i)+'-summary.json');r=read(q) if q.exists() else evaluate('probe'+str(i),theta)
   if not q.exists():save(q,r)
   candidates.append(r)
  if all(c['all_roads_observed'] for c in candidates[1:]):
   q=D/'update-freeze.json';modelpath=D/'update-actor.npz'
   if q.exists():theta=np.load(modelpath)['theta']
   else:
    theta,details=update(probes,[c['mean_return'] for c in candidates[1:]],cov);np.savez(modelpath,theta=theta,mean=mean,std=std);modelpath.chmod(0o600);save(q,dict(definition=p['update_definition'],details=details,model_sha256=sha(modelpath)))
   q=D/'update-summary.json'
   if q.exists():c=read(q)
   elif np.array_equal(theta,np.zeros((17,2))):c=dict(p['baseline'],name='update',source='exact zero baseline reuse');save(q,c)
   else:c=evaluate('update',theta);save(q,c)
   candidates.append(c)
  else:save(D/'update-unexecuted.json',dict(reason='Incomplete paired returns; no imputation or update'))
  # Current240 six completions protects selection from incomplete candidates.
  eligible=[c for c in candidates if c['all_roads_observed'] and c['completed']==6]
  def theta_for(name):
   return np.zeros((17,2)) if name=='baseline' else np.load(D/'update-actor.npz')['theta'] if name=='update' else probes[int(name.replace('probe',''))]
  def rank(c):return (c['mean_lap_ms'],float(np.linalg.norm(theta_for(c['name']))),next(i for i,x in enumerate(candidates) if x['name']==c['name']))
  winner=min(eligible,key=rank);save(D/'training-selection.json',dict(candidates=candidates,winner=winner['name'],ranking='Officialcompleted count first; all6complete equalroad mean time; parameterL2 thenfixedorder tie. Incomplete candidates excluded, notfailed.'))
  modelpath=D/'winner-actor.npz'
  if not modelpath.exists():np.savez(modelpath,theta=theta_for(winner['name']),mean=mean,std=std);modelpath.chmod(0o600)
  save(D/'winner-freeze.json',dict(name=winner['name'],sha256=sha(modelpath),screen_opened_after_selection=True))
  for i,case in enumerate(p['screen_cases']):
   pair={};same=np.array_equal(theta_for(winner['name']),np.zeros((17,2)))
   for arm in case['arm_order']:
    name='baseline' if arm=='A' else winner['name'];theta=np.zeros((17,2)) if arm=='A' else theta_for(name)
    if same and pair:pair[arm]=dict(next(iter(pair.values())),reused_same_policy=True,new_native_actions=0)
    else:
     r=episode('screen'+str(i)+arm,theta,'S'+str(i),case,'screen')
     if r is None:pair[arm]=dict(unexecuted=True,new_native_actions=0)
     else:pair[arm]=dict(r,new_native_actions=r['native_actions'])
   valid=[r for r in pair.values() if 'initial_observation_sha256' in r]
   if len(valid)==2:assert valid[0]['initial_observation_sha256']==valid[1]['initial_observation_sha256']
   screen.append(dict(road='S'+str(i),arms=pair));save(D/'screen-results-private.json',screen)
 except Exception as e:error=type(e).__name__+': '+str(e)
 save(D/'outcome.json',dict(stage=247,candidates=candidates,screen=screen,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(D/'opening.json')['start_epoch'],CPU_this_process_s=time.process_time()-cpu,champion_changed=False,HOLDOUT_opened=False,SEALED_opened=False,automatic_next_experiment=False))

if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
