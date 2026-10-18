"""One source-state braking reachability falsification, not a racing candidate."""
import datetime,hashlib,json,math,signal,time,traceback
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
import retry.whole551_model as old
import retry.structure537_control as policy
from retry.drive519_control import steering,project,reference,force_rows
from retry.brake508_corridor import bounds
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response552-private');old.D=D

class Stage(old.Stage):
 def __init__(self):
  self.phase='probe';self.cpu=time.process_time();self.wall=time.perf_counter();self.counter=[0];self.cost=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0,geometry_checks=0,model_body_checks=0,max_all_model_body_speed_m_s=0.);self.c=json.loads((G/'retry/defect552_probe_contract.json').read_text());self.outcomes=[];self.current=None;self.safety_state=None;self.arm='candidate';limits=self.c['caps'];self.tick_cap=limits['model_ticks'];self.force_cap=limits['force'];self.cpu_cap=limits['CPU_s'];self.wall_cap=limits['wall_s']
  for p,h in self.c['source_sha256'].items():assert hashlib.sha256((G/p).read_bytes()).hexdigest()==h
  for p,h in self.c['private_inputs_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
  self.static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());self.paths=json.loads(Path('/workspace/haic-response551-private/frozen-paths-private.json').read_text());self.entry=json.loads((D/'probe-input-private.json').read_text());self.index=bounds(self.static['roads']);self.edge=old.boundary_index(self.static['boundary']);self.geometry=policy.geometry_context(self.static,limits['geometry']);self.save(D/'probe-STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/defect552_probe_contract.json').read_bytes()).hexdigest()))
 def braking_action(self,root,s,history):
  self.guard(6400);cert=policy.certifier(root,self.paths['candidate'],self.paths['backup'],s,self.counter,self.cost,self.geometry,self.tick_cap,history);steer=steering(root,self.paths['candidate'],s);lock=np.float32(.9)
  if lock<.9:lock=np.nextafter(lock,np.float32(1.))
  points=sorted(set([float(np.float32(-1+i/8)) for i in range(9)]+[-float(lock),-float(np.nextafter(lock,np.float32(0.)))]));cache={};trials=[]
  def command(u):return np.array([steer,0.,-float(u)],np.float32)
  def evaluate(u):
   u=float(np.float32(u));assert -1<=u<=0
   if u not in cache:
    self.guard()
    if len(cache)>=31:raise RuntimeError('BRAKING_QUERY_CAP')
    report=cert(command(u));value=dict(u=u,report=report);cache[u]=value;trials.append(value)
   return cache[u]
  coarse=[evaluate(u) for u in points];edges=[];regime=lambda u:'locked' if -u>=.9 else 'brake'
  for a,b in zip(coarse,coarse[1:]):
   if a['report']['ok']!=b['report']['ok'] and regime(a['u'])==regime(b['u']):
    safe=a if a['report']['ok'] else b;unsafe=b if a['report']['ok'] else a;edges.append(dict(safe=safe['u'],unsafe=unsafe['u'],score=safe['report']['first_hold']['speed']))
  edges.sort(key=lambda x:(x['score'],x['safe']))
  for j in range(9):
   if not edges:break
   edge=edges[j%len(edges)];mid=float(np.float32((edge['safe']+edge['unsafe'])/2))
   if not min(edge['safe'],edge['unsafe'])<mid<max(edge['safe'],edge['unsafe']):continue
   trial=evaluate(mid);edge['safe' if trial['report']['ok'] else 'unsafe']=mid
  good=[x for x in cache.values() if x['report']['ok']]
  if not good:return None,dict(mode='NO_CERTIFIED_BRAKING_ACTION',trials=trials)
  best=min(good,key=lambda x:(x['report']['first_hold']['speed'],x['u']));a=command(best['u']);final=cert(a);assert final['ok'] and final['min_footprint_margin_m']>=.5 and final['peak']<=policy.ADMISSION;return a,dict(mode='SOURCE_MIN_FIRST_HOLD_SPEED',trials=trials,reports=[dict(mode='FINAL',**final)],final_recertified=True,source_calls=len(cache)+1)
 def probe(self):
  self.current='stateful-braking';data=self.entry;root=self.root(data['root']);s=s0=data['progress'];v0=math.hypot(*root.planar.linear.velocity);target=data['target_speed'];history=list(data['history']);trace=[];commands=[];cross=None;failure=None;minimum=self.measure_margin(root);peak=over=pathmax=bodymax=0.;maxclip=history[0]/history[1];path=self.paths['candidate'];witness=None
  try:
   for hold in range(self.c['max_holds']):
    self.checkpoint();action,detail=self.braking_action(root,s,tuple(history));commands.append(dict(index=data['completed']+hold+1,action=action.tolist() if action is not None else None,detail=detail))
    if action is None:failure='NO_CERTIFIED_BRAKING_ACTION';break
    root=replace(root,planar=replace(root.planar,steer=-float(action[0])))
    for raw in range(4):
     self.guard(4);before=root;old_s=s;fs=force_rows(root,action);self.cost['force_evaluations']+=4;root=self.checked_tick(root,float(action[1]),float(action[2]),self.index,self.counter);q=project(root.center,path,s);s=q['s'];v=math.hypot(*root.planar.linear.velocity);gap=self.measure_margin(root);ratio=max(z['ratio'] for z in fs);o=v-reference(s,path)[0];body=max(math.hypot(*old.hull_pose(root)[1]),*(math.hypot(*(root.planar.linear.velocity[t]+w.offset[t] for t in range(2))) for w in root.planar.linear.wheels));history[0]+=sum(z['clipped'] for z in fs);history[1]+=4;clip=history[0]/history[1];minimum=min(minimum,gap);peak=max(peak,ratio);over=max(over,o);pathmax=max(pathmax,q['distance']);bodymax=max(bodymax,body);maxclip=max(maxclip,clip);problems=[]
     if gap<.5:problems.append('MARGIN')
     if ratio>policy.ADMISSION:problems.append('FORCE')
     if o>4.85:problems.append('REFERENCE')
     if q['distance']>3:problems.append('PATH')
     if body>=100:problems.append('BODY')
     if clip>.1:problems.append('CLIP')
     if s-old_s<-.5 or s-old_s>max(5.,2*math.dist(root.center,before.center)):problems.append('PROJECTION')
     if not all(math.isfinite(x) for x in [s,v,gap,ratio,o,body]):problems.append('NONFINITE')
     beforev=math.hypot(*before.planar.linear.velocity)
     if cross is None and beforev>target>=v:
      f=(beforev-target)/(beforev-v);cross=dict(lower_time_s=.02*len(trace),upper_time_s=.02*(len(trace)+1),interpolated_time_s=.02*(len(trace)+f),lower_progress_m=old_s-s0,upper_progress_m=s-s0,interpolated_progress_m=old_s+f*(s-old_s)-s0,raw_before_speed=beforev,raw_after_speed=v)
     state=asdict(root);state.pop('roads');trace.append(dict(index=data['completed']+hold+1,raw=raw+1,root_without_roads=state,progress=s,margin=gap,path_error=q['distance'],target=reference(s,path)[0],body_speed=body,forces=fs,action=action.tolist(),clipping_fraction=clip));self.safety_state=dict(min_margin=minimum,max_force=peak,max_clip=maxclip,progress_from_start=s-s0,speed=v)
     if problems:failure=problems;break
    if failure or cross is not None:break
   if cross and failure is None:
    self.guard(6400);action,detail=self.select(root,s,tuple(history));final=next((r for r in detail.get('reports',[]) if r['mode']=='FINAL'),None);witness=dict(executed=False,action_exists=action is not None,detail=detail,passed=bool(action is not None and final and final['ok'] and final['min_footprint_margin_m']>=.5));failure=None if witness['passed'] else 'NO_EXISTING_POLICY_CONTINUATION_WITNESS'
   d80=(v0*v0-target*target)/(2*80.);d80lower=((v0-.15)**2-(target+.15)**2)/(2*80.);upper=cross['upper_progress_m']+.20 if cross else None;adv=d80lower-upper if cross else None;safe=failure is None and cross is not None and witness is not None and witness['passed'];out=dict(passed=bool(safe and adv>0),safe_source_stopping_witness=safe,mechanism_gate='Conservative source stopping-distance upper (+2*.10m position guard) < scalar80 lower (v0-.15,target+.15). No arbitrary performance gain gate; not lap time.',first_failure=failure,root_index=data['completed']+1,start_speed_m_s=v0,target_speed_m_s=target,constant80_stopping_distance_m=d80,constant80_lower_distance_m=d80lower,source_stopping=cross,source_stopping_distance_upper_with_error_m=upper,conservative_stopping_distance_advantage_m=adv,executed_holds=len(commands),executed_raw=len(trace),min_margin_m=minimum,max_force_ratio=peak,max_reference_overspeed_m_s=over,max_path_error_m=pathmax,max_body_speed_m_s=bodymax,max_cumulative_clipping=maxclip,final_speed_m_s=math.hypot(*root.planar.linear.velocity),existing537_future_witness_passed=bool(witness and witness['passed']),existing537_future_min_margin_m=next((r['min_footprint_margin_m'] for r in witness['detail'].get('reports',[]) if r['mode']=='FINAL'),None) if witness else None,not_a_candidate_or_lap_performance=True,whole_or_actual_promotion=False)
   self.save(D/'braking-witness-private.json',dict(summary=out,trace=trace,commands=commands,future_witness=witness));self.outcomes.append(out);return out
  except BaseException as exc:self.save(D/'probe-interrupted-private.json',dict(error=type(exc).__name__+':'+str(exc),trace=trace,commands=commands,model_ticks=self.counter[0],cost=self.cost));raise
 def run(self):
  from core.vendor.car_racing import CarRacing
  def poison(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN_552_PROBE')
  CarRacing.__init__=CarRacing.reset=CarRacing.step=poison;policy.tick=self.checked_tick
  def interrupt(*a):raise RuntimeError('PROBE_TIMER_CAP')
  signal.signal(signal.SIGPROF,interrupt);signal.setitimer(signal.ITIMER_PROF,self.cpu_cap);signal.signal(signal.SIGALRM,interrupt);signal.setitimer(signal.ITIMER_REAL,self.wall_cap);out={}
  try:out=self.probe()
  except BaseException as exc:out=dict(passed=False,technical_error=type(exc).__name__+':'+str(exc));self.save(D/'probe-error-private.json',dict(error=out['technical_error'],traceback=traceback.format_exc(),model_ticks=self.counter[0],cost=self.cost))
  finally:
   signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);self.checkpoint();out.update(model_ticks=self.counter[0],cost=self.cost,CPU_s=time.process_time()-self.cpu,wall_s=time.perf_counter()-self.wall,new_native_actions=0,new_resets=0,new_seeds=0,protected_queries=0,research_remaining=22758,reserve=84000,reserve_used=0);self.save(G/'retry/defect552_probe_result.json',out);print(json.dumps(out,indent=2))
if __name__=='__main__':Stage().run()
