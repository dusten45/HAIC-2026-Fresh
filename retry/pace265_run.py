"""Fixed258 GT free-line pace stress; four episodes once, no solve or pixel promotion."""
import argparse,json,hashlib,time,datetime
from pathlib import Path
import numpy as np

def run(path):
 from retry.diagnose import make_env
 from retry.pace265_force import TireTrace
 D=path.parent;p=json.loads(path.read_text())
 def read(q):return json.loads(q.read_text())
 def sha(q):return hashlib.sha256(Path(q).read_bytes()).hexdigest()
 def save(q,x):
  t=q.with_name(q.name+'.tmp');t.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');t.chmod(0o600);t.replace(q)
 assert sha(path)==path.with_suffix('.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(q)==h
 assert not (D/'opening.json').exists(),'Started native: no replay'
 save(D/'opening.json',dict(epoch=time.time()));results=[];error=None;cpu=time.process_time()
 try:
  for road,pace in p['order']:
   remain=2500-read(D/'budget.json')['actions']
   if remain<=0:break
   folder=D/(road+'_'+str(pace));assert not folder.exists();folder.mkdir(mode=0o700);plan=read(Path(p['frozen_plans'][road]));line=np.asarray(plan['line']);prof=plan['free_profile'];vprof=np.asarray(prof['speed']);ds=np.asarray(prof['ds']);curvature=np.asarray(prof['curvature']);sarc=np.r_[0,np.cumsum(ds)];L=sarc[-1];model=plan['model'];index=0;laststeer=0.;env=None;tire=TireTrace();rows=[];compute=[];ticks=0;start=time.perf_counter()
   try:
    env=make_env();case=p['cases'][road];obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});assert hashlib.sha256(obs.tobytes()).hexdigest()==p['initial_observations'][road];start_t=env.unwrapped.t;resetticks=round(start_t*50);tire.enable()
    for step in range(1,min(2000,remain)+1):
     assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();tic=time.perf_counter();raw=env.unwrapped;pos=np.asarray(raw.car.hull.position);vel=np.asarray(raw.car.hull.linearVelocity);speed=float(np.linalg.norm(vel));N=len(line);cand=np.arange(max(0,index-2),index+18);dots=np.linalg.norm(line[cand%N]-pos,axis=1);closest=int(cand[np.argmin(dots)]);index=max(index,closest);i=index%N;a=line[i];v=line[(i+1)%N]-a;u=float(np.clip((pos-a)@v/max(v@v,1e-9),0,1));projection=a+u*v;err=float(np.linalg.norm(pos-projection));arc=sarc[i]+u*ds[i];look=max(6.,min(25.,3.24+.22*speed));goal=(arc+look)%L;j=min(N-1,int(np.searchsorted(sarc,goal,side='right')-1));alpha=(goal-sarc[j])/max(ds[j],1e-9);target=line[j]+alpha*(line[(j+1)%N]-line[j]);bodyright=np.array([np.cos(raw.car.hull.angle),np.sin(raw.car.hull.angle)]);delta=target-pos;x=float(delta@bodyright);steer=float(np.clip(np.arctan(2*3.24*x/max(delta@delta,1e-6)),-.4,.4));steer=.8*steer+.2*laststeer;laststeer=steer
     runtime_v=vprof.copy()
     if index>=N:runtime_v[:]=np.minimum(100.,np.sqrt(model['lateral_accel']/np.maximum(abs(np.r_[curvature,curvature[0]]),1e-6)))
     runtime_v*=pace
     desired=float(np.sqrt(max(0,(1-u)*runtime_v[i]**2+u*runtime_v[i+1]**2)));feed=float((runtime_v[i+1]**2-runtime_v[i]**2)/(2*max(ds[i],1e-9)));feedback=1.5*(desired-speed);acc=float(np.clip(feed+feedback,-model['brake_accel'],model['rear_traction_accel']));gas=float(np.clip(model['effective_mass']*max(acc,0)*(speed+2.7)/80000,0,1));brake=float(np.clip(model['effective_mass']*max(-acc,0)/(4*1.6*15/(.02*.54)),0,1));action=np.asarray([steer,gas,brake],np.float32);compute.append((time.perf_counter()-tic)*1000);b=read(D/'budget.json');assert b['actions']<2500;b['actions']+=1;save(D/'budget.json',b);tire.begin_action();before=raw.t;obs,_,ended,truncated,info=env.step(action);rawstep=round((raw.t-before)*50);ticks+=rawstep;assert len(tire.current)==rawstep*4;complete=raw.finish_time_s is not None;terminal=bool(ended or truncated or step>=2000);rows.append(dict(step=step,path_error_m=err,speed_m_s=speed,target_speed_m_s=desired,speed_error_m_s=speed-desired,feedforward_accel=feed,feedback_accel=feedback,clipped_command_accel=acc,action=action.tolist(),damage=env.damage.damage,collision=bool(info['collision']),visited=raw.tile_visited_count,terminal=terminal,tire=tire.summarize()))
     if terminal or step==min(2000,remain):break
    ratios=[x['speed_m_s']/x['target_speed_m_s'] for x in rows if x['target_speed_m_s']>1e-8];spe=[x['speed_error_m_s'] for x in rows];errors=[x['path_error_m'] for x in rows];firstlarge=next((x for x in rows if x['path_error_m']>3),None);firstcontact=next((x for x in rows if x['collision']),None);r=dict(road=road,pace=pace,completed=complete,actual_DNF=terminal and not complete,censored=not terminal,lap_ms=round((raw.finish_time_s-start_t)*1000) if complete else None,native_actions=step,retire_reason=info.get('retire_reason') or ('max_steps' if step>=2000 else 'budget_cut' if not terminal else None),damage=env.damage.damage,visited=raw.tile_visited_count,total_tiles=len(raw.track),first_large_error_action=firstlarge['step'] if firstlarge else None,first_large_error_m=firstlarge['path_error_m'] if firstlarge else None,first_collision_action=firstcontact['step'] if firstcontact else None,tracking_error_m=dict(mean=float(np.mean(errors)),p95=float(np.percentile(errors,95)),max=float(max(errors))),actual_speed_m_s=dict(median=float(np.median([x['speed_m_s'] for x in rows])),max=float(max(x['speed_m_s'] for x in rows))),target_speed_m_s=dict(median=float(np.median([x['target_speed_m_s'] for x in rows])),max=float(max(x['target_speed_m_s'] for x in rows))),speed_tracking=dict(mean_error=float(np.mean(spe)),mean_absolute_error=float(np.mean(np.abs(spe))),median_actual_target_ratio=float(np.median(ratios))),tire=tire.summarize(tire.total),raw_step_ticks=ticks,raw_reset_ticks=resetticks,wall_s=time.perf_counter()-start,oracle_compute_ms=dict(median=float(np.median(compute)),max=float(max(compute))),privileged_GT=True,pixel_only=False,geometric_path_unchanged=True,stress_profile_physical_feasibility_claim=False)
   finally:
    tire.disable()
    if env:env.close()
   save(folder/'trajectory-private.json',rows);save(folder/'result.json',r);results.append(r);save(D/'results-private.json',results);print(json.dumps(r),flush=True)
 except Exception as e:error=type(e).__name__+': '+str(e)
 save(D/'outcome-private.json',dict(stage=265,results=results,technical_error=error,budget=read(D/'budget.json'),unexecuted=[dict(road=a,pace=b) for a,b in p['order'] if not any(r['road']==a and r['pace']==b for r in results)],wall_s=time.time()-read(D/'opening.json')['epoch'],CPU_s=time.process_time()-cpu))

if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
