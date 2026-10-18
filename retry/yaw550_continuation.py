"""One bounded source continuation per saved549 endpoint, no replay/native."""
import datetime,hashlib,json,math,signal,time,traceback
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
import retry.retime549_model as previous
import retry.structure537_control as policy
from retry.closure524_control import tick as original_tick
from retry.drive519_control import project,reference,force_rows
from retry.corner515_model import margin
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
from retry.lap518_finish import hull_pose
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response550-private');FLOOR=.5251524480367317
previous.D=D

def body_speed(root):return max(math.hypot(*hull_pose(root)[1]),*(math.hypot(*(root.planar.linear.velocity[j]+w.offset[j] for j in range(2))) for w in root.planar.linear.wheels))

class Stage(previous.Stage):
 def __init__(self):
  self.phase='continuation';self.cpu=time.process_time();self.wall=time.perf_counter();self.counter=[0];self.cost=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0,geometry_checks=0,executed_ticks=0,model_body_checks=0,max_all_model_body_speed_m_s=0.);self.c=json.loads((G/'retry/yaw550_contract.json').read_text());self.outcomes=[];self.current=None;self.safety_state=None;self.arm='baseline';lim=self.c['caps'];self.tick_cap=lim['model_ticks'];self.force_cap=lim['force'];self.cpu_cap=lim['CPU_s'];self.wall_cap=lim['wall_s'];self.probe_gate=None
  for p,h in self.c['source_sha256'].items():assert hashlib.sha256((G/p).read_bytes()).hexdigest()==h
  for p,h in self.c['private_inputs_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
  self.static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());self.paths=json.loads((D/'frozen-paths-private.json').read_text());self.inputs=json.loads((D/'continuation-input-private.json').read_text());self.index=bounds(self.static['roads']);self.edge=boundary_index(self.static['boundary']);self.geometry=policy.geometry_context(self.static,lim['geometry']);self.save(D/'continuation-STARTED.json',dict(contract_sha256=hashlib.sha256((G/'retry/yaw550_contract.json').read_bytes()).hexdigest()))
 def checked_tick(self,root,gas,brake,index,counter):
  self.guard();after=original_tick(root,gas,brake,index,counter);v=body_speed(after);self.cost['model_body_checks']+=1;self.cost['max_all_model_body_speed_m_s']=max(self.cost['max_all_model_body_speed_m_s'],v)
  if not math.isfinite(v) or v>=100:raise RuntimeError('MODEL_BODY_DOMAIN')
  return after
 def geometry_check(self,root):
  if self.cost['geometry_checks']>=self.geometry['max_checks']:raise RuntimeError('GEOMETRY_CAP')
  self.cost['geometry_checks']+=1;return margin(root,self.static['roads'],self.index,self.static['boundary'],self.edge,self.static['obstacles'])
 def one_arm(self,arm,path):
  self.arm=arm;self.current=arm;self.paths['candidate']=path;data=self.inputs['arms'][arm];root=self.root(data['root']);s=data['end_station'];assert abs(project(root.center,path,s)['s']-s)<1e-10;history=list(data['history']);gate=self.inputs['gate'];offset=data['elapsed_since549_entry_s'];trace=[];commands=[];cross=None;failure=None;witness=None;minimum=self.geometry_check(root);peak=maxover=maxpath=0.;maxbody=body_speed(root);maxclip=history[0]/history[1];dot=lambda p:sum((p[j]-gate['point'][j])*gate['tangent'][j] for j in range(2));assert dot(root.center)<0
  try:
   for hold in range(self.c['max_executed_holds_per_arm']):
    self.checkpoint();self.guard(6400);action,detail=self.select(root,s,tuple(history));commands.append(dict(index=data['completed']+hold+1,action=action.tolist() if action is not None else None,detail=detail))
    if action is None:failure='NO_ADMISSIBLE_ACTION';break
    root=replace(root,planar=replace(root.planar,steer=-float(action[0])))
    for raw in range(4):
     self.guard(4);before=root;old_s=s;force=force_rows(root,action);self.cost['force_evaluations']+=4;root=self.checked_tick(root,float(action[1]),float(action[2]),self.index,self.counter);self.cost['executed_ticks']+=1;q=project(root.center,path,s);s=q['s'];gap=self.geometry_check(root);v=math.hypot(*root.planar.linear.velocity);o=v-reference(s,path)[0];ratio=max(x['ratio'] for x in force);history[0]+=sum(x['clipped'] for x in force);history[1]+=4;clip=history[0]/history[1];body=body_speed(root);minimum=min(minimum,gap);peak=max(peak,ratio);maxover=max(maxover,o);maxpath=max(maxpath,q['distance']);maxbody=max(maxbody,body);maxclip=max(maxclip,clip);problems=[]
     if gap<FLOOR:problems.append('MARGIN')
     if ratio>policy.ADMISSION:problems.append('FORCE')
     if o>4.85:problems.append('REFERENCE')
     if q['distance']>3:problems.append('PATH')
     if clip>.1:problems.append('CLIP')
     if body>=100:problems.append('BODY')
     if not all(math.isfinite(x) for x in [s,gap,v,o,ratio,body]):problems.append('NONFINITE')
     if s-old_s<-.5 or s-old_s>max(5.,2*math.dist(root.center,before.center)):problems.append('PROJECTION')
     if cross is None and dot(before.center)<0<=dot(root.center):
      fraction=-dot(before.center)/(dot(root.center)-dot(before.center));vel=[before.planar.linear.velocity[j]+fraction*(root.planar.linear.velocity[j]-before.planar.linear.velocity[j]) for j in range(2)];sv=math.hypot(*vel);yaw=before.planar.yaw+fraction*(root.planar.yaw-before.planar.yaw);angle=before.planar.angle+fraction*(root.planar.angle-before.planar.angle);heading=math.atan2(gate['tangent'][0]*vel[1]-gate['tangent'][1]*vel[0],sum(gate['tangent'][j]*vel[j] for j in range(2)));position=[before.center[j]+fraction*(root.center[j]-before.center[j]) for j in range(2)];qp=project(position,path,old_s);assert sum(gate['tangent'][j]*vel[j] for j in range(2))>0;cross=dict(lower_s=offset+.02*len(trace),upper_s=offset+.02*(len(trace)+1),time_s=offset+.02*(len(trace)+fraction),speed=sv,yaw=yaw,yaw_target=sv*gate['curvature'],yaw_error=abs(yaw-sv*gate['curvature']),heading_error=abs(heading),sideslip_rad=math.atan2(math.sin(math.atan2(vel[1],vel[0])-angle-math.pi/2),math.cos(math.atan2(vel[1],vel[0])-angle-math.pi/2)),path_error=qp['distance'])
     state=asdict(root);state.pop('roads');trace.append(dict(index=data['completed']+hold+1,raw=raw+1,root_without_roads=state,progress=s,margin=gap,force_rows=force,overspeed=o,path_error=q['distance'],body_speed=body,clipping_fraction=clip,action=action.tolist()));self.safety_state=dict(min_margin_m=minimum,force_peak=peak,clipping_max=maxclip,max_body_speed=maxbody)
     if problems:failure=problems;break
    if failure or cross is not None:break
   if cross is not None and failure is None:
    self.guard(6400);action,detail=self.select(root,s,tuple(history));final=next((r for r in detail.get('reports',[]) if r['mode']=='FINAL'),None);witness=dict(action=action.tolist() if action is not None else None,detail=detail,passed=bool(action is not None and final and final['ok'] and final['min_footprint_margin_m']>=FLOOR and final['peak']<=policy.ADMISSION and final['max_reference_overspeed']<=4.85 and final['clipped']/final['samples']<=.1),executed=False)
   item=dict(arm=arm,passed=bool(cross is not None and failure is None and witness and witness['passed']),crossing=cross,first_failure=failure,raw_ticks=len(trace),holds=len(commands),continued_from_saved_completed=data['completed'],saved_prefix_ticks_replayed=0,min_margin_m=minimum,peak_force=peak,max_reference_overspeed=maxover,max_path_error=maxpath,max_body_speed=maxbody,max_cumulative_clipping=maxclip,terminal=previous.terminal_metrics(root,path,s),fresh12hold_witness_passed=bool(witness and witness['passed']),fresh12hold_witness_min_margin_m=next((r['min_footprint_margin_m'] for r in witness['detail']['reports'] if r['mode']=='FINAL'),None) if witness else None)
   self.save(D/(arm+'-continuation-private.json'),dict(summary=item,trace=trace,commands=commands,witness=witness));self.outcomes.append(item);self.checkpoint();return item
  except BaseException as exc:
   self.save(D/(arm+'-interrupted-private.json'),dict(error=type(exc).__name__+':'+str(exc),trace=trace,commands=commands,model_ticks=self.counter[0],cost=self.cost));raise
 def run(self):
  from core.vendor.car_racing import CarRacing
  def poison(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN_550')
  CarRacing.__init__=CarRacing.reset=CarRacing.step=poison;policy.tick=self.checked_tick
  def interrupt(*a):raise RuntimeError('PHASE_TIMER_CAP')
  signal.signal(signal.SIGPROF,interrupt);signal.setitimer(signal.ITIMER_PROF,self.cpu_cap);signal.signal(signal.SIGALRM,interrupt);signal.setitimer(signal.ITIMER_REAL,self.wall_cap);out={}
  try:
   candidate=self.paths['candidate'];baseline=self.paths['baseline'];items=[]
   for arm,path in [('baseline',baseline),('candidate',candidate)]:
    item=self.one_arm(arm,path);items.append(item)
    if not item['passed']:break
   safe=len(items)==2 and all(x['passed'] for x in items);gain=items[0]['crossing']['lower_s']-items[1]['crossing']['upper_s'] if safe else None;interp=items[0]['crossing']['time_s']-items[1]['crossing']['time_s'] if safe else None;out=dict(passed=bool(safe and gain>=.02-1e-12),finite_horizon_safety_recovered=safe,conservative_gain_from549_entry_s=gain,interpolated_gain_from549_entry_s=interp,original549_gate_passed=False,whole_lap_or_native_promotion=False,new_native_actions=0,new_resets=0,replayed_saved549_ticks=0)
  except BaseException as exc:
   out=dict(passed=False,technical_error=type(exc).__name__+':'+str(exc),new_native_actions=0,new_resets=0);self.save(D/'continuation-error-private.json',dict(error=out['technical_error'],traceback=traceback.format_exc(),cost=self.cost,model_ticks=self.counter[0]))
  finally:
   signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);self.checkpoint();out.update(cases=self.outcomes,cost=self.cost,model_ticks=self.counter[0],integrator_wheel_force_evaluations=4*self.counter[0],CPU_s=time.process_time()-self.cpu,wall_s=time.perf_counter()-self.wall,research_remaining=22758,reserve=84000,reserve_used=0,new_seeds=0,protected_queries=0);self.save(G/'retry/yaw550_continuation_result.json',out);print(json.dumps(out,indent=2))
if __name__=='__main__':Stage().run()
