"""One-road actual-simulator CEM of three road-common coefficients; one frozen transfer."""
import argparse,json,time,hashlib,datetime
from pathlib import Path
import numpy as np
from retry.pace268_profile import multipliers


def save(q,x):
 t=q.with_name(q.name+'.tmp');t.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');t.chmod(0o600);t.replace(q)
def read(q):return json.loads(q.read_text())
def sha(q):return hashlib.sha256(Path(q).read_bytes()).hexdigest()


def episode(D,label,road,coefficients,phase,p):
 from retry.diagnose import make_env
 b=read(D/'budget.json');remaining=(3000-b['training']) if phase=='training' else (2000-b['transfer'])
 if remaining<=0:return dict(label=label,road=road,phase=phase,coefficients=list(map(float,coefficients)),completed=False,actual_DNF=False,censored=False,unexecuted=True,reason='phase_budget',native_actions=0,lap_ms=None)
 folder=D/label;assert not folder.exists();folder.mkdir(mode=0o700);plan=read(Path(p['frozen_plans'][road]));line=np.asarray(plan['line']);prof=plan['free_profile'];vprof=np.asarray(prof['speed']);ds=np.asarray(prof['ds']);curve=np.asarray(prof['curvature']);sarc=np.r_[0,np.cumsum(ds)];L=sarc[-1];pace=multipliers(coefficients,curve,ds,plan['model']);model=plan['model'];index=0;laststeer=0.;env=None;rows=[];compute=[];ticks=0;start=time.perf_counter()
 try:
  env=make_env();case=p['cases'][road];obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});assert hashlib.sha256(obs.tobytes()).hexdigest()==p['initial_observations'][road];start_t=env.unwrapped.t;reset=round(start_t*50)
  for step in range(1,min(2000,remaining)+1):
   assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();tic=time.perf_counter();raw=env.unwrapped;pos=np.asarray(raw.car.hull.position);vel=np.asarray(raw.car.hull.linearVelocity);speed=float(np.linalg.norm(vel));N=len(line);cand=np.arange(max(0,index-2),index+18);dots=np.linalg.norm(line[cand%N]-pos,axis=1);closest=int(cand[np.argmin(dots)]);index=max(index,closest);i=index%N;a=line[i];v=line[(i+1)%N]-a;u=float(np.clip((pos-a)@v/max(v@v,1e-9),0,1));projection=a+u*v;err=float(np.linalg.norm(pos-projection));arc=sarc[i]+u*ds[i];look=max(6.,min(25.,3.24+.22*speed));goal=(arc+look)%L;j=min(N-1,int(np.searchsorted(sarc,goal,side='right')-1));alpha=(goal-sarc[j])/max(ds[j],1e-9);target=line[j]+alpha*(line[(j+1)%N]-line[j]);bodyright=np.array([np.cos(raw.car.hull.angle),np.sin(raw.car.hull.angle)]);delta=target-pos;x=float(delta@bodyright);steer=float(np.clip(np.arctan(2*3.24*x/max(delta@delta,1e-6)),-.4,.4));steer=.8*steer+.2*laststeer;laststeer=steer
   runtime_v=vprof.copy()
   if index>=N:runtime_v[:]=np.minimum(100.,np.sqrt(model['lateral_accel']/np.maximum(abs(np.r_[curve,curve[0]]),1e-6)))
   runtime_v*=pace
   desired=float(np.sqrt(max(0,(1-u)*runtime_v[i]**2+u*runtime_v[i+1]**2)));feed=float((runtime_v[i+1]**2-runtime_v[i]**2)/(2*max(ds[i],1e-9)));acc=float(np.clip(feed+1.5*(desired-speed),-model['brake_accel'],model['rear_traction_accel']));gas=float(np.clip(model['effective_mass']*max(acc,0)*(speed+2.7)/80000,0,1));brake=float(np.clip(model['effective_mass']*max(-acc,0)/(4*1.6*15/(.02*.54)),0,1));action=np.asarray([steer,gas,brake],np.float32);compute.append((time.perf_counter()-tic)*1000);b=read(D/'budget.json');assert b['actions']<5000 and b[phase]< (3000 if phase=='training' else 2000);b['actions']+=1;b[phase]+=1;save(D/'budget.json',b);before=raw.t;obs,_,ended,truncated,info=env.step(action);ticks+=round((raw.t-before)*50);complete=raw.finish_time_s is not None;terminal=bool(ended or truncated or step>=2000);rows.append(dict(step=step,path_error_m=err,speed_m_s=speed,target_speed_m_s=desired,pace_near_cursor=float((1-u)*pace[i]+u*pace[i+1]),action=action.tolist(),damage=env.damage.damage,collision=bool(info['collision']),visited=raw.tile_visited_count,terminal=terminal))
   if terminal or step==min(2000,remaining):break
  r=dict(label=label,road=road,phase=phase,coefficients=list(map(float,coefficients)),completed=complete,actual_DNF=terminal and not complete,censored=not terminal,unexecuted=False,lap_ms=round((raw.finish_time_s-start_t)*1000) if complete else None,native_actions=step,retire_reason=info.get('retire_reason') or ('max_steps' if step>=2000 else 'budget_cut' if not terminal else None),damage=env.damage.damage,visited=raw.tile_visited_count,total_tiles=len(raw.track),first_collision=next((x['step'] for x in rows if x['collision']),None),first_large_error=next((x['step'] for x in rows if x['path_error_m']>3),None),tracking_error_m=dict(mean=float(np.mean([x['path_error_m'] for x in rows])),p95=float(np.percentile([x['path_error_m'] for x in rows],95)),max=float(max(x['path_error_m'] for x in rows))),actual_speed_m_s=dict(median=float(np.median([x['speed_m_s'] for x in rows])),max=float(max(x['speed_m_s'] for x in rows))),target_speed_m_s=dict(median=float(np.median([x['target_speed_m_s'] for x in rows])),max=float(max(x['target_speed_m_s'] for x in rows))),pace_on_path=dict(min=float(pace.min()),max=float(pace.max())),raw_step_ticks=ticks,raw_reset_ticks=reset,wall_s=time.perf_counter()-start,oracle_compute_ms=dict(median=float(np.median(compute)),max=float(max(compute))),GT_only=True,controller_positive_clamp_preserved=True)
 finally:
  if env:env.close()
 save(folder/'trajectory-private.json',rows);save(folder/'result.json',r);print(json.dumps({k:r[k] for k in ['label','completed','actual_DNF','censored','lap_ms','native_actions','damage']}),flush=True);return r


def run(path):
 p=read(path);D=path.parent;assert sha(path)==path.with_suffix('.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(q)==h
 assert not (D/'opening.json').exists(),'No replay of started study'
 save(D/'opening.json',dict(epoch=time.time()));rng=np.random.default_rng(268);mu=np.zeros(3);sigma=np.full(3,.10);records=[];generations=[];updates=0;error=None;transfer=None;selected=None;cpu=time.process_time()
 try:
  base=read(Path(p['O0_constant_reference']));assert base['completed'] and base['pace']==1.5 and base['lap_ms']==19700
  incumbent=dict(label='cached265_O0_1.5',road='O0',phase='training',coefficients=[0.]*3,completed=True,actual_DNF=False,censored=False,unexecuted=False,lap_ms=base['lap_ms'],native_actions=0,damage=base['damage'],reference_native_actions=base['native_actions'],reused=True)
  cache={tuple(incumbent['coefficients']):incumbent};all_candidates=[incumbent]
  for gen in range(2):
   points=[np.array(incumbent['coefficients'])]+[np.clip(mu+sigma*rng.standard_normal(3),-.2,.2) for _ in range(3)];save(D/(f'g{gen}-registered-private.json'),dict(generation=gen,mean_coefficients=mu.tolist(),std_coefficients=sigma.tolist(),coefficients=[x.tolist() for x in points]))
   population=[]
   for j,coefficients in enumerate(points):
    key=tuple(map(float,coefficients))
    if key in cache:
     r=dict(cache[key]);r['population_label']=f'g{gen}_p{j}';r['reused']=True
    else:
     r=episode(D,f'g{gen}_p{j}','O0',coefficients,'training',p);r['reused']=False;cache[key]=r;all_candidates.append(r);records.append(r);save(D/'training-records-private.json',records)
    population.append(r)
   completed=[x for x in population if x['completed']];elite=sorted(completed,key=lambda x:x['lap_ms'])[:2]
   if elite:
    latent=np.array([x['coefficients'] for x in elite]);mu=latent.mean(0);sigma=np.maximum(latent.std(0),.03);updates+=1
   incumbent=min((x for x in all_candidates if x['completed']),key=lambda x:x['lap_ms'])
   report=dict(generation=gen,population=population,actual_new_completed=sum(x['completed'] for x in population if not x['reused']),actual_new_DNF=sum(x['actual_DNF'] for x in population if not x['reused']),actual_new_censored=sum(x['censored'] for x in population if not x['reused']),completed_population_including_reuse=len(completed),elite_labels=[x['label'] for x in elite],mean_coefficients_after=mu.tolist(),std_coefficients_after=sigma.tolist(),incumbent=incumbent['label'],incumbent_lap_ms=incumbent['lap_ms']);generations.append(report);save(D/'generations-private.json',generations);print(json.dumps({k:report[k] for k in ['generation','actual_new_completed','actual_new_DNF','actual_new_censored','incumbent','incumbent_lap_ms']}),flush=True)
  selected=dict(stage=268,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),label=incumbent['label'],coefficients=incumbent['coefficients'],O0_lap_ms=incumbent['lap_ms'],O0_damage=incumbent['damage'],selected_on='O0 official completion/time only; stable earliest tie; no N0performance read',profile_rule_sha256=sha(Path(p['profile_source'])),generations_completed=2);save(D/'selected-private.json',selected);frozen_hash=sha(D/'selected-private.json');(D/'selected.sha256').write_text(frozen_hash+'\n');(D/'selected.sha256').chmod(0o600)
  frozen=read(D/'selected-private.json');assert sha(D/'selected-private.json')==frozen_hash;save(D/'transfer-opening.json',dict(selected_sha256=frozen_hash,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));
  if np.array_equal(np.array(frozen['coefficients']),np.zeros(3)):
   existing=read(Path(p['N0_constant_reference']));assert existing['completed'] and existing['pace']==1.5
   transfer=dict(existing,label='transfer_cached265_N0_1.5',phase='transfer',coefficients=frozen['coefficients'],reference_native_actions=existing['native_actions'],native_actions=0,reused=True,unexecuted=False)
  else:transfer=episode(D,'transfer_N0','N0',np.array(frozen['coefficients']),'transfer',p)
  assert sha(D/'selected-private.json')==frozen_hash;save(D/'transfer-private.json',transfer)
 except Exception as e:error=type(e).__name__+': '+str(e)
 save(D/'outcome-private.json',dict(stage=268,training=records,generations=generations,selected=selected,transfer=transfer,technical_error=error,budget=read(D/'budget.json'),CEM_updates=updates,wall_s=time.time()-read(D/'opening.json')['epoch'],CPU_s=time.process_time()-cpu,automatic_next_experiment=False))

if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
