"""Privileged whole-map planning/following diagnostic; never a legalparticipant."""
import argparse,json,time,datetime,hashlib
from pathlib import Path
import numpy as np


def run(path):
    from retry.diagnose import make_env
    from retry.source_vehicle_transition import SourceVehicleTransition
    from retry.racing258_plan import solve,geometry
    p=json.loads(path.read_text());D=path.parent
    def read(q):return json.loads(q.read_text())
    def save(q,x):
        t=q.with_name(q.name+'.tmp');t.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');t.chmod(0o600);t.replace(q)
    def sha(q):return hashlib.sha256(Path(q).read_bytes()).hexdigest()
    assert sha(path)==path.with_suffix('.sha256').read_text().strip()
    for q,h in p['hashes'].items():assert sha(q)==h
    if not (D/'opening.json').exists():save(D/'opening.json',dict(start_epoch=time.time()))
    results=[];plans=[];error=None;cpu=time.process_time()
    try:
        for road in ['O0','N0']:
            m=read(Path(p['materializations'][road]));snapshot=m['snapshots']['1'];q=D/(road+'-plan-private.json')
            if q.exists():plan=read(q)
            else:
                source=SourceVehicleTransition(snapshot);mass=float(source.car.hull.mass+sum(w.mass for w in source.car.wheels));source.close();model=dict(mass=mass,effective_mass=mass+4*1.6/.54**2,rear_traction_accel=.8*800/(mass+2*1.6/.54**2),brake_accel=.3*(4*1.6*15/(.02*.54))/(mass+4*1.6/.54**2),lateral_accel=.4*1600/mass);s=solve(snapshot,model)
                plan={k:(v.tolist() if isinstance(v,np.ndarray) else {kk:vv.tolist() if isinstance(vv,np.ndarray) else vv for kk,vv in v.items()} if isinstance(v,dict) else v) for k,v in s.items()};plan['model']=model;plan['whole_map_GT']=True;save(q,plan)
            plans.append(dict(road=road,**{k:plan[k] for k in ['free_feasible','center_blocked','model_calls','first_model_wall_s','model_wall_s','dimension','violation','solver_converged']}));print(json.dumps(plans[-1]),flush=True)
            for arm in ['free']:
                folder=D/(road+'_'+arm)
                if folder.exists():
                    assert (folder/'result.json').exists(),'Unfinishednativeoracle: no replay';results.append(read(folder/'result.json'));continue
                if arm=='free' and not plan['free_feasible']:results.append(dict(road=road,arm=arm,unexecuted=True,reason='solver_geometry_infeasible',native_actions=0));continue
                remain=5058-read(D/'budget.json')['actions']
                if remain<=0:results.append(dict(road=road,arm=arm,unexecuted=True,reason='budget',native_actions=0));continue
                folder.mkdir(mode=0o700);env=None;trace=[];raw=0;start=time.perf_counter();line=np.asarray(plan['center' if arm=='center' else 'line']);prof=plan['center_profile' if arm=='center' else 'free_profile'];vprof=np.asarray(prof['speed']);ds=np.asarray(prof['ds']);sarc=np.r_[0,np.cumsum(ds)];L=sarc[-1];curvature=np.asarray(prof['curvature']);index=0;laststeer=0.;oraclems=[];model=plan['model']
                try:
                    env=make_env();case=p['cases'][road];obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});assert hashlib.sha256(obs.tobytes()).hexdigest()==p['initial_observations'][road];start_t=env.unwrapped.t;reset_ticks=round(start_t*50)
                    for step in range(1,min(2000,remain)+1):
                        assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();tic=time.perf_counter();rawenv=env.unwrapped;pos=np.asarray(rawenv.car.hull.position);vel=np.asarray(rawenv.car.hull.linearVelocity);speed=float(np.linalg.norm(vel));N=len(line);cand=np.arange(max(0,index-2),index+18);dots=np.linalg.norm(line[cand%N]-pos,axis=1);closest=int(cand[np.argmin(dots)]);index=max(index,closest);i=index%N;a=line[i];v=line[(i+1)%N]-a;u=float(np.clip((pos-a)@v/max(v@v,1e-9),0,1));projection=a+u*v;err=float(np.linalg.norm(pos-projection));arc=sarc[i]+u*ds[i];look=max(6.,min(25.,3.24+.22*speed));goal=(arc+look)%L;j=min(N-1,int(np.searchsorted(sarc,goal,side='right')-1));alpha=(goal-sarc[j])/max(ds[j],1e-9);target=line[j]+alpha*(line[(j+1)%N]-line[j]);bodyright=np.array([np.cos(rawenv.car.hull.angle),np.sin(rawenv.car.hull.angle)]);bodyforward=np.array([-np.sin(rawenv.car.hull.angle),np.cos(rawenv.car.hull.angle)]);delta=target-pos;x=float(delta@bodyright);steer=float(np.clip(np.arctan(2*3.24*x/max(delta@delta,1e-6)),-.4,.4));steer=.8*steer+.2*laststeer;laststeer=steer
                        # Squared-speed interpolation andsource rolling-wheel feedforward.
                        runtime_v=vprof.copy()
                        if index>=N:runtime_v[:]=np.minimum(100.,np.sqrt(model['lateral_accel']/np.maximum(abs(np.r_[curvature,curvature[0]]),1e-6)))
                        desired=float(np.sqrt(max(0,(1-u)*runtime_v[i]**2+u*runtime_v[i+1]**2)));feed=float((runtime_v[i+1]**2-runtime_v[i]**2)/(2*max(ds[i],1e-9)));acc=float(np.clip(feed+1.5*(desired-speed),-model['brake_accel'],model['rear_traction_accel']));gas=float(np.clip(model['effective_mass']*max(acc,0)*(speed+2.7)/80000,0,1));brake=float(np.clip(model['effective_mass']*max(-acc,0)/(4*1.6*15/(.02*.54)),0,1));action=np.asarray([steer,gas,brake],np.float32);oraclems.append((time.perf_counter()-tic)*1000);b=read(D/'budget.json');assert b['actions']<5058;b['actions']+=1;save(D/'budget.json',b);old_t=rawenv.t;obs,_,ended,truncated,info=env.step(action);ticks=round((rawenv.t-old_t)*50);raw+=ticks;complete=rawenv.finish_time_s is not None;terminal=bool(ended or truncated or step>=2000 and not complete);trace.append(dict(step=step,path_error_m=err,speed_m_s=speed,target_speed_m_s=desired,road_progress_index=index,damage=env.damage.damage,collision=bool(info['collision']),action=action.tolist(),visited=rawenv.tile_visited_count,terminal=terminal))
                        if terminal or step==min(2000,remain):break
                    r=dict(road=road,arm=arm,native_actions=step,completed=complete,actual_DNF=terminal and not complete,censored=not terminal,lap_ms=round((rawenv.finish_time_s-start_t)*1000) if complete else None,retire_reason=info.get('retire_reason') or ('max_steps' if step>=2000 else 'budget_cut' if not terminal else None),damage=env.damage.damage,visited=rawenv.tile_visited_count,total_tiles=len(rawenv.track),predicted_model_time_s=prof['estimated_time_s'],path_feasible=arm=='free' and plan['free_feasible'] or arm=='center' and plan['center_blocked'] is None,tracking_error_m=dict(mean=float(np.mean([t['path_error_m'] for t in trace])),p95=float(np.percentile([t['path_error_m'] for t in trace],95)),max=float(max(t['path_error_m'] for t in trace))),speed_m_s=dict(median=float(np.median([t['speed_m_s'] for t in trace])),max=float(max(t['speed_m_s'] for t in trace))),oracle_compute_ms=dict(median=float(np.median(oraclems)),max=float(max(oraclems))),raw_step_ticks=raw,raw_reset_ticks=reset_ticks,wall_s=time.perf_counter()-start,privileged_GT=True,legal_submission_candidate=False)
                finally:
                    if env:env.close()
                save(folder/'trajectory-private.json',trace);save(folder/'result.json',r);results.append(r);save(D/'results-private.json',results);print(json.dumps({k:r[k] for k in ['road','arm','completed','actual_DNF','censored','lap_ms','native_actions','predicted_model_time_s','path_feasible']}),flush=True)
    except Exception as e:error=type(e).__name__+': '+str(e)
    save(D/'outcome-private.json',dict(stage=259,results=results,plans=plans,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(D/'opening.json')['start_epoch'],CPU_s=time.process_time()-cpu))

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
