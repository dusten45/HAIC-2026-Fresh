"""Saved-only whole-lap472 time audit. No physical, solver or seed-selection imports."""
import time
START=time.perf_counter()
import ast,hashlib,importlib.abc,json,math,os,resource,signal,sys
from pathlib import Path
class NoPhysics(importlib.abc.MetaPathFinder):
 def find_spec(self,name,path=None,target=None):
  if name.startswith(('Box2D','core.vendor')) or name in ('retry.diagnose','retry.terminal410_model','retry.source_vehicle_transition','retry.racing258_plan','retry.pace268_profile'):raise RuntimeError('499_FORBIDDEN_IMPORT:'+name)
  return None
sys.meta_path.insert(0,NoPhysics())
import numpy as np
from retry.signed417_executor import canonical_projection
from retry.pilot420_json import json_ready
G=Path(__file__).resolve().parents[1];R=Path('/workspace/haic-private-retry-20261009');D=R/'stage499/qualified-analysis-private'
def check(v,s):
 if not v:raise RuntimeError('499_'+s)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def guard(*a):check(time.process_time()+10<120 and time.perf_counter()-START+20<180,'RESOURCE')
def save(name,value):
 p=D/name;check(not p.exists(),'IMMUTABLE_OUTPUT');data=(json.dumps(json_ready(value),ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode();check(len(data)<4*1024**2 and sum(f.stat().st_size for f in D.iterdir() if f.is_file())+len(data)<16*1024**2,'OUTPUT16MIB')
 with p.open('xb') as f:os.chmod(p,0o600);f.write(data);f.flush();os.fsync(f.fileno())
 check(p.read_bytes()==data,'READBACK')
def run():
 check(not D.exists(),'ONCE');D.mkdir(mode=0o700);signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('499_CPU')));signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('499_WALL')));signal.setitimer(signal.ITIMER_PROF,max(.001,110-time.process_time()));signal.setitimer(signal.ITIMER_REAL,max(.001,160-(time.perf_counter()-START)))
 save('plan-private.json',dict(stage=499,mode='SAVED_ONLY',code_sha256=sha(__file__),caps=dict(CPU_s=120,wall_s=180,new_outputs=16*1024**2,physics=0),overhead_allowance=dict(CPU_s=10,wall_s=20),registered_before_numerics=True,metrics='12 equal canonical-arc bins, raw20ms interval allocation with interpolated bin crossings; hold125 prefix/suffix; low speeds10/20/40; exact gas/brake/coast; curvature bins defined before reading full metrics.',zones=dict(corner_abs_curvature_ge=.02,straight_abs_curvature_le=.005,long_straight_run_m=40,entry_exit_geometry_window_m=20),estimates='Analytical fixed-profile clocks and uniform10/20percent zone speed compression are descriptive what-if time scales, not feasible controller/optimal lower bounds. No other entrant/tracks/state equivalence.',no_new_seed_HOLDOUT_SEALED=True,no_followup=True))
 accessed={};pinned={}
 def read(p,expected=None,lines=False):
  p=Path(p);h=sha(p)
  if expected is not None:check(h==expected,'SOURCE_PIN:'+p.name)
  if str(p) in accessed:check(accessed[str(p)]==h,'INPUT_CHANGED')
  accessed[str(p)]=h;data=p.read_text()
  return [json.loads(s) for s in data.splitlines() if s] if lines else json.loads(data)
 plan=read(R/'stage472/plan.json');manifest=read(R/'stage472-retention-manifest-private.json');budget=R/'project-effective-budget-v495.json';budgethash=sha(budget)
 fixed=read(plan['fixed_plan'],plan['sources'][plan['fixed_plan']]);pace=np.asarray(read(plan['pace_path'],plan['sources'][plan['pace_path']])['frozen268']);profiles=read(plan['projection_path'],plan['projection_sha256']);line=np.asarray(fixed['line']);ds=np.asarray(fixed['free_profile']['ds']);sarc=np.r_[0,np.cumsum(ds)];L=float(sarc[-1]);curve=np.abs(np.asarray(fixed['free_profile']['curvature']));original=np.asarray(fixed['free_profile']['speed'])*pace;p4=np.asarray(profiles['projected_nodes']);check(original.shape==p4.shape==(len(line)+1,),'NODES');check(np.all(ds>0) and np.all(original[1:]>0) and np.all(p4[1:]>0),'PROFILE');check(np.max(abs(ds-np.linalg.norm(np.roll(line,-1,axis=0)-line,axis=1)))<1e-10,'DS_OWNER')
 def clock(nodes,a=0.,b=None):
  b=L if b is None else b;value=0.
  for j in range(len(ds)):
   lo=max(a,sarc[j]);hi=min(b,sarc[j+1])
   if hi<=lo:continue
   v0=math.sqrt((1-(lo-sarc[j])/ds[j])*nodes[j]**2+((lo-sarc[j])/ds[j])*nodes[j+1]**2);v1=math.sqrt((1-(hi-sarc[j])/ds[j])*nodes[j]**2+((hi-sarc[j])/ds[j])*nodes[j+1]**2);check(v0+v1>0,'CLOCK_ZERO');value+=2*(hi-lo)/(v0+v1)
  return float(value)
 def geometry(j):
  def ahead(direction,window):
   out=[];k=j;distance=0.
   while 0<=k<len(ds) and distance<=window:out.append(k);distance+=ds[k];k+=direction
   return out
  if curve[j]>=.02:return 'corner'
  if any(curve[k]>=.02 for k in ahead(1,20)):return 'corner_entry'
  if any(curve[k]>=.02 for k in ahead(-1,20)):return 'corner_exit'
  if curve[j]<=.005:
   low=set()
   for direction in (-1,1):
    k=j
    while 0<=k<len(ds) and curve[k]<=.005:low.add(k);k+=direction
   if sum(ds[k] for k in low)>=40:return 'long_straight'
  return 'transition'
 zones=[geometry(j) for j in range(len(ds))]
 def material(label,path):
  path=Path(path);expected=plan['sources'].get(str(path));actual=path.resolve()
  if label=='472':
   rel=actual.relative_to(Path(manifest['roots']['native']));expected=manifest['entries']['native/'+str(rel)]['sha256']
  rows=read(path,expected,True);check(rows and all(r['step']==i+1 for i,r in enumerate(rows)),'HOLD_INDEX');start=rows[0]['pre']['time'];event=rows[-1]['finish_time_s'];check(rows[-1]['completed'] and event is not None,'OFFICIAL_FINISH');end=event;raw=[];progress=rows[0]['progress_before'];last_arc=canonical_projection(line,rows[0]['pre']['pos'],rows[0]['pre']['vel'],rows[0]['memory_before']['C']['phase'])['arc'];modecounts={}
  for row in rows:
   guard();n=row['raw_ticks'];hulls=row['raw_hull'];tires=row['raw_tire_samples'];check(len(hulls)==n and len(tires)==4*n,'RAW_COVERAGE');command=row['command'];mode='gas' if command[1]>0 else 'brake' if command[2]>0 else 'coast';check(not(command[1]>0 and command[2]>0),'SIMULTANEOUS_PEDALS');phase=row['nominal_memory_after']['C']['phase']
   for k,h in enumerate(hulls):
    t0=h['time'];t1=t0+.02
    dt=max(0.,min(t1,end)-t0);pos=h['origin_position'];vel=h['COM_linear_velocity'];next_h=hulls[k+1] if k+1<n else None;post=row['post'] if next_h is None else None;pos1=post['pos'] if post else next_h['origin_position'];vel1=post['vel'] if post else next_h['COM_linear_velocity'];q=canonical_projection(line,pos,vel,phase);q1=canonical_projection(line,pos1,vel1,phase);increment=(q1['arc']-last_arc+L/2)%L-L/2;before=progress;progress+=increment;last_arc=q1['arc'];j=q['index'];u=q['u'];nodes=p4 if label=='472' and row['step']>=126 else original;ref=math.sqrt((1-u)*nodes[j]**2+u*nodes[j+1]**2);future=[nodes[z] for z in range(j+1,len(nodes)) if sarc[z]-q['arc']<=40];futuremin=min([ref]+future);speed=float(np.linalg.norm(vel));speed1=float(np.linalg.norm(vel1));z=tires[4*k:4*k+4];tangent=(line[(j+1)%len(line)]-line[j])/ds[j];normal=np.asarray([-tangent[1],tangent[0]]);forward=np.asarray([-math.sin(h['angle']),math.cos(h['angle'])]);right=np.asarray([math.cos(h['angle']),math.sin(h['angle'])]);error=max(q['path_error_m'],q1['path_error_m']);foot=line[j]+u*(line[(j+1)%len(line)]-line[j]);zone=zones[j]
    if dt<=0:continue # Validate the confirmation-only ledger tick above, but exclude it from official-event lap time.
    raw.append(dict(hold=row['step'],raw=k+1,t=t0-start,dt=dt,progress0=before,progress1=progress,distance_m=float(np.linalg.norm(np.asarray(pos1)-pos))*dt/.02,speed=speed,speed_post=speed1,accel=(speed1-speed)/.02,ref=ref,ref_gap=ref-speed,future40_ref_min=futuremin,mode=mode,gas=command[1],brake=command[2],zone=zone,curvature=float(curve[j]),error=error,signed_error=float((np.asarray(pos)-foot)@normal),heading_deg=math.degrees(math.atan2(tangent[0]*forward[1]-tangent[1]*forward[0],tangent@forward)),body_lateral=float(np.asarray(vel)@right),normal_velocity=float(np.asarray(vel)@normal),force_ratio=max(x['force_ratio'] for x in z),clipped=sum(x['clipped'] for x in z),tires=len(z),front_lat=max(abs(x['raw_lat_N']) for x in z if x['wheel']<2),rear_lat=max(abs(x['raw_lat_N']) for x in z if x['wheel']>=2)))
   check(abs(progress-row['progress_after'])<1e-8,'ACTUAL_PROGRESS_OWNER:'+label+':'+str(row['step']));check(abs(row['post_projection']['path_error_m']-q1['path_error_m'])<1e-8,'POST_ERROR_OWNER')
  check(abs(sum(x['dt'] for x in raw)-(end-start))<1e-8,'EPISODE_RAW_CLOCK');return dict(label=label,rows=rows,raw=raw,start=start,end=end,lap=end-start,source_sha256=accessed[str(path)])
 def aggregate(samples,weights=None):
  if not samples:return dict(time_s=0.,raw_count=0)
  weights=[x['dt'] for x in samples] if weights is None else weights;T=sum(weights)
  def mean(key):return sum(x[key]*w for x,w in zip(samples,weights))/T
  time_modes={mode:sum(w for x,w in zip(samples,weights) if x['mode']==mode) for mode in ('gas','brake','coast')}
  return dict(time_s=T,raw_count=len(samples),progress_m=sum((x['progress1']-x['progress0'])*w/x['dt'] for x,w in zip(samples,weights)),physical_distance_m=sum(x['distance_m']*w/x['dt'] for x,w in zip(samples,weights)),mean_speed_m_s=mean('speed'),min_speed_m_s=min(x['speed'] for x in samples),max_speed_m_s=max(x['speed_post'] for x in samples),mean_accel_m_s2=mean('accel'),mode_time_s=time_modes,mode_fraction={k:v/T for k,v in time_modes.items()},mean_abs_lateral_error_m=sum(abs(x['signed_error'])*w for x,w in zip(samples,weights))/T,max_raw_guard_error_m=max(x['error'] for x in samples),max_abs_heading_deg=max(abs(x['heading_deg']) for x in samples),max_abs_body_lateral_m_s=max(abs(x['body_lateral']) for x in samples),clipped_wheel_samples=sum(x['clipped'] for x in samples),wheel_samples=sum(x['tires'] for x in samples),clipping_time_s=sum(w for x,w in zip(samples,weights) if x['clipped']),max_force_ratio=max(x['force_ratio'] for x in samples),mean_ref_minus_speed_m_s=mean('ref_gap'),time_speed_below_ref_by5_s=sum(w for x,w in zip(samples,weights) if x['ref_gap']>5),time_braking_below_ref_by5_s=sum(w for x,w in zip(samples,weights) if x['mode']=='brake' and x['ref_gap']>5),time_braking_below_current_and_future40_by5_s=sum(w for x,w in zip(samples,weights) if x['mode']=='brake' and x['speed']<min(x['ref'],x['future40_ref_min'])-5),time_low40_s=sum(w for x,w in zip(samples,weights) if x['speed']<40),time_near_rest_point1_s=sum(w for x,w in zip(samples,weights) if x['speed']<.1),time_weak_pedal_s=sum(w for x,w in zip(samples,weights) if x['gas']<=.05 and x['brake']<=.01))
 paths={'472':R/'stage472-native/actual_Projected4ReferenceCommonPulse/trace-private.jsonl','458C0':R/'stage458/actual_C0/trace-private.jsonl','458P':R/'stage458/actual_P/trace-private.jsonl','463Original':R/'stage463-native/actual_Original/trace-private.jsonl','463Secant':R/'stage463-native/actual_SecantOnce/trace-private.jsonl'}
 laps={label:material(label,path) for label,path in paths.items()};best=laps['472'];raw=best['raw'];N=12;bins=[]
 for i in range(N):
  lo=i*L/N;hi=(i+1)*L/N;samples=[];weights=[]
  for x in raw:
   a=x['progress0'];b=x['progress1']
   if b>a:
    lower=-math.inf if i==0 else lo;upper=math.inf if i==N-1 else hi;span=max(0.,min(b,upper)-max(a,lower));w=x['dt']*span/(b-a)
   else:w=x['dt'] if min(N-1,max(0,int(a/L*N)))==i else 0.
   if w>0:samples.append(x);weights.append(w)
  item=aggregate(samples,weights);item.update(bin=i+1,arc_fraction=[i/N,(i+1)/N],original_profile_clock_s=clock(original,lo,hi),P4_profile_clock_s=clock(p4,lo,hi));item['observed_minus_P4_clock_s']=item['time_s']-item['P4_profile_clock_s'];bins.append(item)
 check(abs(sum(x['time_s'] for x in bins)-best['lap'])<1e-8,'BIN_TIME_SUM')
 zone_summary={zone:aggregate([x for x in raw if x['zone']==zone]) for zone in ('long_straight','corner_entry','corner','corner_exit','transition')};phase_summary={name:aggregate([x for x in raw if (x['hold']<=125)==prefix]) for name,prefix in [('prefix1_125',True),('P4suffix126_171',False)]}
 launches={}
 for speed in (10,20,40):
  hit=next((x for x in raw if x['speed_post']>=speed),None);launches['first_'+str(speed)+'m_s']=None if hit is None else [hit['t'],hit['t']+hit['dt']]
 for distance in (10,25,50):
  hit=next((x for x in raw if x['progress1']>=distance),None);launches['first_'+str(distance)+'m']=None if hit is None else [hit['t'],hit['t']+hit['dt']]
 pair_summary={}
 for a,b,prefix in [('458C0','458P',112),('463Original','463Secant',125)]:
  A=laps[a];B=laps[b];check(A['rows'][:prefix]==B['rows'][:prefix],'PAIR_PREFIX');pair_summary[a+'_'+b]=dict(common_exact_prefix_holds=prefix,lap_A_s=A['lap'],lap_B_s=B['lap'],measured_saving_s=A['lap']-B['lap'],new_pair=False,scope='Historical conditional actual pair; postprefix endogenous paths/states/commands differ.',zones_A={z:aggregate([x for x in A['raw'] if x['zone']==z])['time_s'] for z in zone_summary},zones_B={z:aggregate([x for x in B['raw'] if x['zone']==z])['time_s'] for z in zone_summary})
 check(laps['458P']['rows']==laps['463Original']['rows'],'BASELINE_BRIDGE');check(best['rows'][:125]==laps['458P']['rows'][:125],'BEST_PREFIX_BRIDGE')
 # Locate historical time differences at common *spatial* bins. They describe
 # where whole-pair effects accumulate; they do not isolate each local action.
 def crossing(lap,target):
  if target<=0:return [0.,0.]
  for x in lap['raw']:
   if x['progress0']<=target<=x['progress1']:return [x['t'],x['t']+x['dt']]
  return None
 crossings=[]
 for i in range(1,N+1):
  target=i*L/N;entry={'fraction':i/N,'time_brackets_s':{label:crossing(lap,target) for label,lap in laps.items()}}
  crossings.append(entry)
 # Integrate only the supplied profile, no feasibility solver or rerun.
 rootprogress=best['rows'][124]['progress_after'];refclocks=dict(original_full_s=clock(original),P4_full_s=clock(p4),switched_at_actual_pre126_clock_s=clock(original,0,rootprogress)+clock(p4,rootprogress,L),P4_suffix_clock_s=clock(p4,rootprogress,L),switch_arc_fraction=rootprogress/L)
 whatif={z:dict(observed_zone_time_s=v['time_s'],saving_if10percent_faster_s=v['time_s']*(1-1/1.1),saving_if20percent_faster_s=v['time_s']*(1-1/1.2),needed_speed_increase_fraction_to_save1_65=None if v['time_s']<=1.65 else v['time_s']/(v['time_s']-1.65)-1) for z,v in zone_summary.items()}
 comparepublic={}
 for n in ('compare473_result.json','compare477_result.json','compare470_result.json','diagnostic482_summary.json','transfer472_result.json'):comparepublic[n]=read(G/'retry'/n)
 save('raw-derived-private.json',dict(stage=499,reference='Original472 owner417 canonical, not491 reinterpretation.',raw=raw,best_holds=len(best['rows']),new_world_reset_tick_seed=0))
 result=dict(stage=499,mode='SAVED_ONLY',lap_s=best['lap'],target_s=11.99,gap_s=best['lap']-11.99,time_reduction_fraction=(best['lap']-11.99)/best['lap'],uniform_speed_increase_fraction=best['lap']/11.99-1,canonical_line_length_m=L,canonical_progress_m=raw[-1]['progress1'],official_track_length_claimed=False,global_metrics=aggregate(raw),bins=bins,zones=zone_summary,phases=phase_summary,launch=launches,reference_clocks=refclocks,zone_speed_whatif=whatif,paired_actual=pair_summary,historical_laps={label:lap['lap'] for label,lap in laps.items()},spatial_crossings=crossings,causal_limits=['472 is a single lateP4 actual run, not a new pair against463.','profile clocks are fixed-line scalar estimates, not feasible/optimal lower bounds.','20ms raw bin crossings interpolated; per-boundary bracket <=20ms; bin time is apportioned estimate.','Other entrants track/state/length equivalence unverified.','EarlierP4 model failures differ in prefix/root/control/mode and cannot reject all path/preview/planning families.'],available_raw=dict(best_holds=171,best_raw_ticks=len(raw),tire_samples=sum(x['tires'] for x in raw),all_five_full_actual_traces=True,missing_direct494_post_damage_phase_in_472=True,no_new_evidence_fabricated=True),research_remaining=26027,reserve=84000,reserve_used=0,CPU_s=time.process_time(),wall_s=time.perf_counter()-START,overhead_allowance_CPU_s=10,overhead_allowance_wall_s=20,RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,new_reset_world_integration_seed_HOLDOUT_SEALED=0,no_followup=True)
 for p,h in accessed.items():check(sha(p)==h,'FINAL_READ_PIN')
 check(sha(budget)==budgethash,'BUDGET_UNCHANGED');guard();save('result-private.json',result);save('read-inputs-private.json',accessed);guard();signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
 print(json.dumps({k:result[k] for k in ('stage','lap_s','gap_s','canonical_line_length_m','reference_clocks','launch','CPU_s','wall_s')}),flush=True)
if __name__=='__main__':run()
