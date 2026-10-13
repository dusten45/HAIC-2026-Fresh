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
 b=read(D/'budget.json');remaining=4500-b['actions']
 if remaining<=0:return dict(label=label,road=road,phase=phase,coefficients=list(map(float,coefficients)),completed=False,actual_DNF=False,censored=False,unexecuted=True,reason='phase_budget',native_actions=0,lap_ms=None)
 folder=D/label;assert not folder.exists();folder.mkdir(mode=0o700);plan=read(Path(p['frozen_plans'][road]));line=np.asarray(plan['line']);prof=plan['free_profile'];vprof=np.asarray(prof['speed']);ds=np.asarray(prof['ds']);curve=np.asarray(prof['curvature']);sarc=np.r_[0,np.cumsum(ds)];L=sarc[-1];pace=multipliers(coefficients,curve,ds,plan['model']);model=plan['model'];index=0;laststeer=0.;env=None;rows=[];compute=[];ticks=0;start=time.perf_counter()
 try:
  env=make_env();case=p['cases'][road];obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});assert hashlib.sha256(obs.tobytes()).hexdigest()==p['initial_observations'][road];assert hashlib.sha256(np.asarray(env.unwrapped.track,dtype='<f8').tobytes()).hexdigest()==case['road_geometry_sha256'];start_t=env.unwrapped.t;reset=round(start_t*50)
  for step in range(1,min(2000,remaining)+1):
   assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();tic=time.perf_counter();raw=env.unwrapped;pos=np.asarray(raw.car.hull.position);vel=np.asarray(raw.car.hull.linearVelocity);speed=float(np.linalg.norm(vel));N=len(line);cand=np.arange(max(0,index-2),index+18);dots=np.linalg.norm(line[cand%N]-pos,axis=1);closest=int(cand[np.argmin(dots)]);index=max(index,closest);i=index%N;a=line[i];v=line[(i+1)%N]-a;u=float(np.clip((pos-a)@v/max(v@v,1e-9),0,1));projection=a+u*v;err=float(np.linalg.norm(pos-projection));arc=sarc[i]+u*ds[i];look=max(6.,min(25.,3.24+.22*speed));goal=(arc+look)%L;j=min(N-1,int(np.searchsorted(sarc,goal,side='right')-1));alpha=(goal-sarc[j])/max(ds[j],1e-9);target=line[j]+alpha*(line[(j+1)%N]-line[j]);bodyright=np.array([np.cos(raw.car.hull.angle),np.sin(raw.car.hull.angle)]);delta=target-pos;x=float(delta@bodyright);steer=float(np.clip(np.arctan(2*3.24*x/max(delta@delta,1e-6)),-.4,.4));steer=.8*steer+.2*laststeer;laststeer=steer
   runtime_v=vprof.copy()
   if index>=N:runtime_v[:]=np.minimum(100.,np.sqrt(model['lateral_accel']/np.maximum(abs(np.r_[curve,curve[0]]),1e-6)))
   runtime_v*=pace
   desired=float(np.sqrt(max(0,(1-u)*runtime_v[i]**2+u*runtime_v[i+1]**2)));feed=float((runtime_v[i+1]**2-runtime_v[i]**2)/(2*max(ds[i],1e-9)));acc=float(np.clip(feed+1.5*(desired-speed),-model['brake_accel'],model['rear_traction_accel']));gas=float(np.clip(model['effective_mass']*max(acc,0)*(speed+2.7)/80000,0,1));brake=float(np.clip(model['effective_mass']*max(-acc,0)/(4*1.6*15/(.02*.54)),0,1));action=np.asarray([steer,gas,brake],np.float32);compute.append((time.perf_counter()-tic)*1000);b=read(D/'budget.json');assert b['actions']<4500;b['actions']+=1;b[phase]+=1;save(D/'budget.json',b);before=raw.t;obs,_,ended,truncated,info=env.step(action);ticks+=round((raw.t-before)*50);complete=raw.finish_time_s is not None;terminal=bool(ended or truncated or step>=2000);rows.append(dict(step=step,path_error_m=err,speed_m_s=speed,target_speed_m_s=desired,pace_near_cursor=float((1-u)*pace[i]+u*pace[i+1]),action=action.tolist(),damage=env.damage.damage,collision=bool(info['collision']),visited=raw.tile_visited_count,terminal=terminal))
   if terminal or step==min(2000,remaining):break
  r=dict(label=label,road=road,phase=phase,coefficients=list(map(float,coefficients)),completed=complete,actual_DNF=terminal and not complete,censored=not terminal,unexecuted=False,lap_ms=round((raw.finish_time_s-start_t)*1000) if complete else None,native_actions=step,retire_reason=info.get('retire_reason') or ('max_steps' if step>=2000 else 'budget_cut' if not terminal else None),damage=env.damage.damage,visited=raw.tile_visited_count,total_tiles=len(raw.track),first_collision=next((x['step'] for x in rows if x['collision']),None),first_large_error=next((x['step'] for x in rows if x['path_error_m']>3),None),tracking_error_m=dict(mean=float(np.mean([x['path_error_m'] for x in rows])),p95=float(np.percentile([x['path_error_m'] for x in rows],95)),max=float(max(x['path_error_m'] for x in rows))),actual_speed_m_s=dict(median=float(np.median([x['speed_m_s'] for x in rows])),max=float(max(x['speed_m_s'] for x in rows))),target_speed_m_s=dict(median=float(np.median([x['target_speed_m_s'] for x in rows])),max=float(max(x['target_speed_m_s'] for x in rows))),pace_on_path=dict(min=float(pace.min()),max=float(pace.max())),raw_step_ticks=ticks,raw_reset_ticks=reset,wall_s=time.perf_counter()-start,oracle_compute_ms=dict(median=float(np.median(compute)),max=float(max(compute))),GT_only=True,controller_positive_clamp_preserved=True)
 finally:
  if env:env.close()
 save(folder/'trajectory-private.json',rows);save(folder/'result.json',r);print(json.dumps({k:r[k] for k in ['label','completed','actual_DNF','censored','lap_ms','native_actions','damage']}),flush=True);return r



def run(path):
 p=read(path);D=path.parent;assert sha(path)==path.with_suffix('.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(q)==h
 assert not (D/'opening.json').exists(),'No repeat of started native pairs'
 save(D/'opening.json',dict(epoch=time.time()));records=[];error=None;cpu=time.process_time();frozen=read(Path(p['coefficient_source']));assert frozen['coefficients']==p['coefficients']
 try:
  for road,arm in p['order']:
   plan=read(Path(p['frozen_plans'][road]))
   if not plan['free_feasible']:
    r=dict(label=road+'_'+arm,road=road,arm=arm,completed=False,actual_DNF=False,censored=False,unexecuted=True,reason='fixed_solver_geometry_infeasible',native_actions=0,lap_ms=None)
   else:
    beta=np.zeros(3) if arm=='baseline' else np.array(p['coefficients']);r=episode(D,road+'_'+arm,road,beta,'evaluation',p);r['arm']=arm;r['paired_geometry_sha256']=sha(Path(p['frozen_plans'][road]))
   records.append(r);save(D/'records-private.json',records)
  assert sha(Path(p['coefficient_source']))==p['coefficient_source_sha256']
 except Exception as e:error=type(e).__name__+': '+str(e)
 save(D/'outcome-private.json',dict(stage=269,records=records,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(D/'opening.json')['epoch'],CPU_s=time.process_time()-cpu,coefficients_changed=False))

if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
