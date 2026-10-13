"""Unchangedpolicy4matched TRAIN runs; evaluator-only spatial/actuator truth."""
import argparse,time,datetime,json
from pathlib import Path
import numpy as np
from retry.path271_run import read,sha
from retry.preview286_run import save

def project(line,pos,idx):
 n=len(line);delta=np.roll(line,-1,axis=0)-line;length=np.linalg.norm(delta,axis=1)
 def point(k):
  j=k%n;u=float(np.clip((pos-line[j])@delta[j]/max(length[j]**2,1e-12),0,1));p=line[j]+u*delta[j];return float(np.sum((pos-p)**2)),u,p
 for _ in range(n):
  opts=[(point(k)[0],k) for k in [idx-1,idx,idx+1]];d,k=min(opts,key=lambda z:(z[0],abs(z[1]-idx)));old=point(idx)[0]
  if d>=old-1e-12 or k==idx:break
  idx=k
 d,u,p=point(idx);j=idx%n;arc=float((idx//n)*length.sum()+length[:j].sum()+u*length[j]);t=delta[j]/max(length[j],1e-9);lateral=float((pos-p)@np.array([-t[1],t[0]]));return idx,dict(arc_m=arc,segment=j,projection_fraction=u,lateral_m=lateral,center_distance_m=float(np.sqrt(d)),centerline_point=p.tolist())
def truth(raw):
 h=raw.car.hull;return dict(position=list(h.position),angle=float(h.angle),velocity=list(h.linearVelocity),speed=float(np.linalg.norm(h.linearVelocity)),yaw_rate=float(h.angularVelocity),wheel_velocities=[list(w.linearVelocity) for w in raw.car.wheels],wheel_angles=[float(w.angle) for w in raw.car.wheels],wheel_gas=[float(w.gas) for w in raw.car.wheels],wheel_brake=[float(w.brake) for w in raw.car.wheels],wheel_joint_angles=[float(w.joint.angle) for w in raw.car.wheels[:2]],wheel_targets=[float(w.steer) for w in raw.car.wheels[:2]],wheel_motor_speeds=[float(w.joint.motorSpeed) for w in raw.car.wheels[:2]],wheel_road_contact_counts=[len(w.tiles) for w in raw.car.wheels],wheel_positions=[list(w.position) for w in raw.car.wheels],wheel_omega=[float(w.omega) for w in raw.car.wheels],grip_multiplier=float(raw.car.grip_multiplier),steering_multiplier=float(raw.car.steering_multiplier),time=float(raw.t),visited=raw.tile_visited_count)
def support(points,polygons):
 out=[]
 for point in points:
  x,y=point;inside=False
  for poly in polygons:
   a=np.array(poly);b=np.roll(a,1,axis=0);cross=(a[:,1]>y)!=(b[:,1]>y);den=b[:,1]-a[:,1];den=np.where(abs(den)<1e-15,1,den);hits=cross&(x<(b[:,0]-a[:,0])*(y-a[:,1])/den+a[:,0]);inside|=bool(np.count_nonzero(hits)%2)
   if inside:break
  out.append(inside)
 return out

def run(R):
 from retry.frozen_composite_runtime import prepare
 from retry.diagnose import make_env
 D=R/'stage300';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(q)==h,q
 assert not (D/'opening.json').exists();save(D/'opening.json',dict(epoch=time.time()));results=[];error=None;cpu=time.process_time()
 try:
  for case in p['runs']:
   F=D/case['label'];F.mkdir(mode=0o700);env=worker=None;start=time.perf_counter();ticks=0;steps=0;last={};tickrows=[];trace=[]
   try:
    worker=prepare(case['config'],F/'cpu',p['sandbox_path']);env=make_env();obs,_=env.reset(seed=case['case']['seed'],options={'track_id':case['case']['track_id']});raw=env.unwrapped;t0=raw.t;line=np.array(raw.track)[:,2:4];idx=int(np.argmin(np.linalg.norm(line-np.array(raw.car.hull.position),axis=1)));polygons=[[list(tile.GetWorldPoint(v)) for v in tile.fixtures[0].shape.vertices] for tile in raw.road];save(F/'geometry-private.json',dict(line=line.tolist(),road_polygons=polygons,obstacles=[[float(o.position[0]),float(o.position[1]),float(o.fixtures[0].shape.radius)] for o in raw.obstacles]));worker.call('reset',obs)
    original_step=raw.step
    def measured_step(action):
     before=truth(raw);out=original_step(action);after=truth(raw);tickrows.append(dict(before=before,after=after));return out
    raw.step=measured_step;oldrows=[json.loads(x) for x in Path(case['old_trace']).read_text().splitlines()];j=(F/'trace-private.jsonl').open('x');(F/'trace-private.jsonl').chmod(0o600)
    try:
     remaining=2500-read(D/'budget.json')['actions'];assert remaining>0
     for step in range(1,min(2000,remaining)+1):
      assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();pre=truth(raw);gtobs_pre=[[float(v) for v in raw.car.hull.GetLocalPoint(tuple(ob.position))]+[float(ob.fixtures[0].shape.radius)] for ob in raw.obstacles];idx,coordinate=project(line,np.array(pre['position']),idx);response,ms=worker.call('act',obs);a=np.array(response['action'],np.float32);committed,_=worker.call('commit',a);assert np.float32(committed['memory'])==a[0];expected=oldrows[step-1];assert a.tolist()==expected['action'] and response['features']==expected['features'];assert committed['memory']==expected['memory'];b=read(D/'budget.json');assert b['actions']<2500;b['actions']+=1;save(D/'budget.json',b);steps=step;tickrows=[];obs,_,ended,truncated,info=env.step(a);ticks+=len(tickrows);post=truth(raw);complete=raw.finish_time_s is not None;terminal=bool(ended or truncated or step==2000);assert bool(info['collision'])==expected['collision'] and float(env.damage.damage)==expected['damage'];h=raw.car.hull
      path=np.array(response['pixel_path']).reshape(-1,2);angle=pre['angle'];basis=np.array([[np.cos(angle),np.sin(angle)],[-np.sin(angle),np.cos(angle)]]);world=np.array(pre['position'])+path@basis;targetlocal=response['features'][1:3];targetworld=np.array(pre['position'])+np.array(targetlocal)@basis;gtob=[[float(x) for x in h.GetLocalPoint(tuple(o.position))]+[float(o.fixtures[0].shape.radius)] for o in raw.obstacles];row=dict(step=step,pre=pre,post=post,coordinate=coordinate,action=a.tolist(),features=response['features'],memory=committed['memory'],pixel_path=response['pixel_path'],path_world=world.tolist(),path_road_supported=support(world,polygons),target_road_supported=support([targetworld],polygons)[0] if not response['features'][0] else None,detected_obstacles=response['detected_obstacles'],GT_obstacles_local_PRE=gtobs_pre,GT_obstacles_local_POST=gtob,raw_ticks=tickrows,damage=float(env.damage.damage),collision=bool(info['collision']),terminal=terminal);j.write(json.dumps(row,allow_nan=False)+'\n');j.flush();trace.append(row)
      if terminal:break
    finally:j.close()
    result=dict(label=case['label'],road=case['road'],policy=case['policy'],completed=complete,actual_DNF=terminal and not complete,censored=not terminal,native_actions=steps,lap_ms=round((raw.finish_time_s-t0)*1000) if complete else None,retire_reason=None if complete else info.get('retire_reason') or ('max_steps' if terminal else 'budget_cut'),damage=float(env.damage.damage),visited=raw.tile_visited_count,total_tiles=len(raw.track),raw_step_ticks=ticks,raw_reset_ticks=round(t0*50),actions_features_memory_collision_prefix_exact_to_old=True,wall_s=time.perf_counter()-start,actor_CPU_s=committed['actor_cumulative_CPU_s'],GT_for_diagnosis_only=True,policy_archive_sha256=case['config']['archive_sha256']);save(F/'terminal-receipt.json',result)
   finally:
    if worker:reaping=worker.close()
    if env:env.close()
   result['reaping']=reaping;save(F/'result.json',result);results.append(result);save(D/'collection-results-private.json',results);print(json.dumps({k:result[k] for k in ['label','completed','actual_DNF','censored','lap_ms','native_actions','retire_reason']}),flush=True)
 except BaseException as e:error=type(e).__name__+': '+str(e);save(D/'error-private.json',dict(error=error,traceback=__import__('traceback').format_exc()))
 save(D/'collection-outcome.json',dict(results=results,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(D/'opening.json')['epoch'],runner_CPU_s=time.process_time()-cpu));print('collection closed, error='+str(error),flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
