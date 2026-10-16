"""Existing TRAIN-only time-loss decomposition. No Agent/env/world imports."""
import datetime,gzip,hashlib,json,math,os,sys,time
from pathlib import Path
import numpy as np
G=Path(__file__).resolve().parent.parent

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 p=Path(p);t=p.with_suffix(p.suffix+'.tmp')
 with t.open('x') as f:
  os.chmod(t,0o600);json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 t.replace(p)
def lines(p):
 with Path(p).open() as f:return [json.loads(x) for x in f]
def projection(line,points):
 line=np.asarray(line,float);points=np.asarray(points,float).reshape(-1,2);v=np.roll(line,-1,axis=0)-line;ds=np.linalg.norm(v,axis=1);delta=points[:,None,:]-line[None,:,:];u=np.clip(np.sum(delta*v,axis=2)/np.maximum(ds**2,1e-18),0,1);q=line[None,:,:]+u[:,:,None]*v;distance=np.linalg.norm(points[:,None,:]-q,axis=2);idx=distance.argmin(axis=1);n=np.arange(len(points));tangent=v[idx]/ds[idx,None];s=np.r_[0,np.cumsum(ds)];arc=s[idx]+u[n,idx]*ds[idx];lat=np.cross(tangent,points-q[n,idx]);angles=np.arctan2(v[:,1],v[:,0]);turn=np.arctan2(np.sin(angles-np.roll(angles,1)),np.cos(angles-np.roll(angles,1)));curvature=turn/((ds+np.roll(ds,1))/2);curvature=(np.roll(curvature,1)+curvature+np.roll(curvature,-1))/3
 return dict(index=idx,arc=arc,lateral=lat,tangent=tangent,curvature=curvature[idx],length=float(s[-1]),ds=ds)
def support(points,polygons):
 p=np.asarray(points,float).reshape(-1,2);pol=np.asarray(polygons,float);edge=np.roll(pol,-1,axis=1)-pol;delta=p[:,None,None,:]-pol[None,:,:,:];cross=edge[None,:,:,0]*delta[:,:,:,1]-edge[None,:,:,1]*delta[:,:,:,0];return np.any(np.all(cross>=-1e-6,axis=2)|np.all(cross<=1e-6,axis=2),axis=1)
def phases(proj,obstacle_arcs,radius):
 out=[];L=proj['length']
 for arc,lat,k in zip(proj['arc'],proj['lateral'],proj['curvature']):
  diff=(obstacle_arcs-arc+L/2)%L-L/2;j=int(np.argmin(abs(diff)))
  if abs(lat)>2*(40/6):out.append('off_reference')
  elif abs(diff[j])<=radius:out.append('obstacle_approach' if diff[j]>=0 else 'post_obstacle')
  else:out.append('straight' if abs(k)<=.01 else 'corner')
 return out

def dt_for(rows,result):
 t=np.array([x['time'] for x in rows]);assert np.all(np.diff(t)>0);dt=np.r_[np.diff(t),result['raw_step_ticks']/50-(t[-1]-t[0])];assert 0<dt[-1]<=.0800001
 if result['completed']:
  lap=result['lap_ms']/1000;dt=np.minimum(dt,np.maximum(0,t[0]+lap-t));assert abs(dt.sum()-lap)<1e-6
 return dt

def capture306(root,key):
 f=root/'stage306/collection'/key;trace=lines(f/'trace-private.jsonl');off=lines(root/'stage334'/key/'OFF-private.jsonl');rows=[];polygons=None;obs=None
 with gzip.open(f/'full-source-captures-private.jsonl.gz','rt') as h:
  for i,line in enumerate(h):
   x=json.loads(line);s=x['snapshot'];a=trace[i];b=off[i];assert x['step']==a['step']==i+1 and x['final296']==a['action']==b['action'] and x['features']==a['features']==b['features']
   if polygons is None:
    polygons=[z['fixture']['geometry']['vertices'] for z in s['roads']];obs=[dict(center=z['body']['position'],radius=z['fixture']['geometry'].get('radius',z['fixture'].get('radius'))) for z in s['obstacles']]
   rows.append(dict(step=i+1,time=s['actual_time'],pos=s['hull']['position'],vel=s['hull']['velocity'],angle=s['hull']['angle'],yaw=s['hull']['angular_velocity'],joint=[w['joint']['angle'] for w in s['wheels'][:2]],road_contacts=[len(w['tiles']) for w in s['wheels']],visited=s['unique_tiles'],action=a['action'],features=a['features'],path=b['pixel_path'],direct=b['tracker']['direct'],collision=a['collision'],damage=a['damage']))
 assert len(rows)==len(trace)==len(off);return rows,read(f/'result.json'),np.asarray(read(f/'track-private.json'))[:,2:4],polygons,obs

def capture300(root,key):
 f=root/'stage300'/key;rr=lines(f/'trace-private.jsonl');geom=read(f/'geometry-private.json');rows=[]
 for x in rr:
  s=x['pre'];rows.append(dict(step=x['step'],time=s['time'],pos=s['position'],vel=s['velocity'],angle=s['angle'],yaw=s['yaw_rate'],joint=s['wheel_joint_angles'],road_contacts=s['wheel_road_contact_counts'],visited=s['visited'],action=x['action'],features=x['features'],path=x['pixel_path'],direct=x['detected_obstacles'],collision=x['collision'],damage=x['damage']))
 obs=[dict(center=z[:2],radius=z[2]) for z in geom['obstacles']]
 return rows,read(f/'result.json'),np.asarray(geom['line']),geom['road_polygons'],obs

def analyze_case(key,rows,result,line,polygons,obstacles):
 n=len(rows);assert result['native_actions']==n;dt=dt_for(rows,result);pos=np.asarray([x['pos'] for x in rows]);vel=np.asarray([x['vel'] for x in rows]);speed=np.linalg.norm(vel,axis=1);action=np.asarray([x['action'] for x in rows]);features=np.asarray([x['features'] for x in rows]);pr=projection(line,pos);obs=np.asarray([x['center'] for x in obstacles]);oarc=projection(line,obs)['arc'];phase=phases(pr,oarc,45);distance=np.r_[np.linalg.norm(np.diff(pos,axis=0),axis=1),np.nan];accel=np.r_[np.diff(speed)/np.diff([x['time'] for x in rows]),np.nan];steerd=np.r_[0,np.abs(np.diff(action[:,0]))];forward=np.sum(vel*pr['tangent'],axis=1);unwrapped=np.unwrap(pr['arc']/pr['length']*2*np.pi)*pr['length']/(2*np.pi);arc_delta=np.r_[np.diff(unwrapped),np.nan]
 # Pixel route replay is matched to the exact source296 action/features per frame.
 pathlen=[];pathsupport=[];targetsupport=[];nextpath=[];deterror=[];lag=[]
 for i,x in enumerate(rows):
  p=np.asarray(x['path'],float).reshape(-1,2);ang=x['angle'];basis=np.array([[math.cos(ang),math.sin(ang)],[-math.sin(ang),math.cos(ang)]]);world=pos[i]+p@basis
  pathlen.append(float(np.linalg.norm(np.diff(p,axis=0),axis=1).sum()) if len(p)>1 else None)
  pathsupport.append(float(support(world,polygons).mean()) if len(p) else None)
  targetsupport.append(bool(support([pos[i]+features[i,1:3]@basis],polygons)[0]) if not features[i,0] else None)
  if i<n-1 and len(world)>1:
   v=np.diff(world,axis=0);u=np.clip(np.sum((pos[i+1]-world[:-1])*v,axis=1)/np.maximum(np.sum(v*v,axis=1),1e-18),0,1);nextpath.append(float(np.min(np.linalg.norm(pos[i+1]-world[:-1]-u[:,None]*v,axis=1))))
  else:nextpath.append(None)
  direct=np.asarray(x['direct'],float)
  if direct.size:
   centers=pos[i]+direct.reshape(-1,direct.shape[-1])[:,:2]@basis;deterror.append(float(np.max(np.min(np.linalg.norm(centers[:,None,:]-obs[None,:,:],axis=2),axis=1))))
  else:deterror.append(None)
  lag.append(max(abs(a+action[i,0]) for a in rows[i+1]['joint']) if i<n-1 else None)
 def weighted(values,mask):
  vals=np.array([np.nan if v is None else v for v in values],float);m=mask&np.isfinite(vals)&(dt>0);return float(np.sum(vals[m]*dt[m])/np.sum(dt[m])) if m.any() else None
 def part(label):
  m=np.array([x==label for x in phase]) if label!='ALL' else np.ones(n,bool);duration=float(dt[m].sum());valid=m&(features[:,0]==0)
  return dict(time_s=duration,observed_chord_distance_m=float(np.nansum(distance[m])),unknown_distance_intervals=int(np.sum(m&~np.isfinite(distance))),mean_speed_m_s=weighted(speed,m),min_speed_m_s=float(np.min(speed[m])) if m.any() else None,mean_target_m_s=weighted(np.where(features[:,0]==0,features[:,6],np.nan),m),target_missing_s=float(dt[m&(features[:,0]!=0)].sum()),gas_brake_both_positive_s=float(dt[m&(action[:,1]>1e-6)&(action[:,2]>1e-6)].sum()),gas_brake_both_over05_s=float(dt[m&(action[:,1]>.05)&(action[:,2]>.05)].sum()),mean_gas=weighted(action[:,1],m),mean_brake=weighted(action[:,2],m),acceleration_gt1_s=float(dt[m&(accel>1)].sum()),deceleration_ltminus1_s=float(dt[m&(accel<-1)].sum()),below_target_by5_s=float(dt[valid&(speed<features[:,6]-5)].sum()),above_target_by5_s=float(dt[valid&(speed>features[:,6]+5)].sum()),nominal_gas0_but_finalgas_over05_s=float(dt[m&(features[:,14]==0)&(action[:,1]>.05)].sum()),steer_total_variation_rad=float(steerd[m].sum()),steer_corrections_over03=int(np.sum(m&(steerd>.03))),mean_abs_steer=weighted(abs(action[:,0]),m),mean_one_step_endpoint_route_error_m=weighted(nextpath,m),mean_post_joint_command_error_rad=weighted(lag,m),mean_path_point_road_support=weighted(pathsupport,m),target_point_offroad_s=float(dt[m&np.array([x is False for x in targetsupport])].sum()),reverse_centerline_velocity_s=float(dt[m&(forward<0)].sum()),wheel_road_contact_loss_s=float(dt[m&np.array([min(x['road_contacts'])==0 for x in rows])].sum()),mean_max_direct_center_error_m=weighted(deterror,m))
 firstcontact=next((i for i,x in enumerate(rows) if x['collision']),None);lastnew=next((i for i in range(n-1,0,-1) if rows[i]['visited']>rows[i-1]['visited']),None)
 result_fields={k:result.get(k) for k in ['completed','actual_DNF','censored','lap_ms','native_actions','damage','retire_reason','raw_step_ticks']}
 byphase={k:part(k) for k in ['straight','corner','obstacle_approach','post_obstacle','off_reference']};total=part('ALL');assert abs(sum(x['time_s'] for x in byphase.values())-total['time_s'])<1e-8
 summary=dict(case=key,result=result_fields,time_basis='official_lap_window' if result['completed'] else 'observed_DNF_episode_not_lap',centerline_length_m=pr['length'],centerline_mean_speed_required_for11s_m_s=pr['length']/11,total=total,phases=byphase,phase_radius_sensitivity={str(rad):{k:float(sum(dt[i] for i,p in enumerate(phases(pr,oarc,rad)) if p==k)) for k in byphase} for rad in [30,60]},first_contact=None if firstcontact is None else dict(step=firstcontact+1,time_s=rows[firstcontact]['time']-rows[0]['time'],arc_m=float(pr['arc'][firstcontact]),pre_speed_m_s=float(speed[firstcontact])),after_first_contact_s=float(dt[firstcontact+1:].sum()) if firstcontact is not None else 0,last_new_tile_pre_step=None if lastnew is None else lastnew+1,after_last_new_tile_pre_s=float(dt[lastnew:].sum()) if lastnew is not None else None,missing=['Final post-action pose absent for306pre-capture corpus; distance/acceleration/joint error finalinterval not imputed','One-step path deviation combines tracking and replan effects; not uniquely follower error','Ground-truth FOV visibility/occlusion not recorded, so no complete perception recall','No causal time attribution from observational phase averages'])
 normalized=[]
 for i,x in enumerate(rows):normalized.append(dict(step=x['step'],t_from_start=x['time']-rows[0]['time'],duration_s=float(dt[i]),phase=phase[i],segment=int(pr['index'][i]),arc_m=float(pr['arc'][i]),unwrapped_arc_m=float(unwrapped[i]),speed_m_s=float(speed[i]),forward_velocity_m_s=float(forward[i]),chord_distance_m=float(distance[i]) if np.isfinite(distance[i]) else None,accel_m_s2=float(accel[i]) if np.isfinite(accel[i]) else None,steer=x['action'][0],gas=x['action'][1],brake=x['action'][2],target_m_s=float(features[i,6]) if not features[i,0] else None,visited=x['visited'],collision=x['collision'],damage=x['damage'],one_step_route_error_m=nextpath[i],post_joint_error_rad=lag[i]))
 return summary,normalized

def run(root):
 d=root/'stage389';assert not(d/'analysis-plan.json').exists();start,cpu=time.perf_counter(),time.process_time();keys=['T2950','T2953','T2956','T2959','O0','O2'];sources=[Path(__file__),root/'project-effective-budget-v407.json',root/'current-champion.json',root/'research-deadline-current.json']
 for key in keys:
  f=root/'stage306/collection'/key;sources += [f/n for n in ['job.json','result.json','track-private.json','full-source-captures-private.jsonl.gz','trace-private.jsonl']]+[root/'stage334'/key/'OFF-private.jsonl']
 f=root/'stage300/T2954_296';sources += [f/n for n in ['result.json','geometry-private.json','trace-private.jsonl']]
 protected={str(p):sha(p) for p in [root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json']}
 plan=dict(stage=389,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),question='Where20second-lap time is spent and what separates path/speed/follower/perception evidence; target approximately11s',native_action_cap_this_analysis=0,replay_contingency='Only if necessary fields missing; at most3outcome-blind registered knownTRAIN exact296 episodes,total6000 from35943,each2000horizon; no automaticuse',cases=keys+['T2954'],source_hashes={str(p):sha(p) for p in sources},protected_hashes=protected,definitions=dict(phase_priority='offreference>|2*40/6m lateral|,then closest obstacle signed centerline arc +/-45m approach/post,else abs3node curvature<=.01/m straight else corner',sensitivity_radius_m=[30,60],time='Measured preaction source time differences + recorded raw terminalticks, clipped to official lap forcompleted; DNF neverassignedlap',distance='Observed consecutive hull-center chord displacement; finalunknown notfilled; not exact continuous pathlength',corrections='abssteerchange>.03rad; simultaneous pedal positive>1e-6 andsubstantialboth>.05',control='Original296 unchanged; no inference/model/physics/fit/tuning',stops='Source/action/feature/row/time mismatch blocks matched analysis; missingmetric reported unavailable notestimated',forbidden='372failure-specificdata/SEALED/othercompute/newtraining/sweeps',parent_source='Parent completeplan589lines+methodology2326lines reread11:08-11:09UTC; consumerdirectfullreadnotclaimed'))
 save(d/'analysis-plan.json',plan);out=[]
 for key in keys:
  rows,r,line,pol,obs=capture306(root,key);summary,normalized=analyze_case(key,rows,r,line,pol,obs);out.append(summary);save(d/(key+'-normalized-private.json'),normalized);print(json.dumps(dict(case=key,lap_ms=r['lap_ms'],phases={k:round(v['time_s'],3) for k,v in summary['phases'].items()},mean_speed=summary['total']['mean_speed_m_s'],overlap_s=summary['total']['gas_brake_both_over05_s'])),flush=True)
 rows,r,line,pol,obs=capture300(root,'T2954_296');summary,normalized=analyze_case('T2954',rows,r,line,pol,obs);out.append(summary);save(d/'T2954-normalized-private.json',normalized)
 for p,h in plan['source_hashes'].items():assert sha(p)==h,p
 assert all(sha(p)==h for p,h in protected.items());save(d/'baseline-decomposition.json',out);save(d/'baseline-analysis-measurement.json',dict(wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu,new_native=0,new_actor=0,new_physics=0))
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
