"""Finite constrained source shooting from a fresh feasible541 trajectory.

Offline known-DEV mechanism experiment, not an online/native participant policy.
"""
import hashlib,json,math,time
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from scipy.optimize import minimize,Bounds
from retry.structure537_control import ADMISSION
from retry.drive519_control import project,reference,force_rows
from retry.closure524_control import tick
from retry.brake508_corridor import bounds
from retry.corner515_model import margin
from retry.lap518_finish import hull_pose
from retry.frozen534_projection import initial_progress


def metrics(root,path,s):
 q=project(root.center,path,s);v=root.planar.linear.velocity;speed=math.hypot(*v);heading=abs(math.atan2(q['tangent'][0]*v[1]-q['tangent'][1]*v[0],sum(q['tangent'][j]*v[j] for j in range(2))))
 return dict(path_error=q['distance'],heading_error=heading,yaw_error=abs(root.planar.yaw-speed*path['curvature'][q['i']]),speed_deficit=max(0.,reference(q['s'],path)[0]-speed),speed=speed)


class Problem:
 def __init__(self,st,data,baseline):
  self.st=st;self.D=Path('/workspace/haic-response545-private');self.data=data;self.root=st.root(data['root']);self.path=st.paths['candidate'];self.index=bounds(self.root.roads);self.gate=json.loads((self.D/'gate-private.json').read_text());self.base_actions=np.array([x['action'] for x in baseline['commands']],dtype=np.float32);assert self.base_actions.shape==(32,3);self.u=np.where(self.base_actions[:20,1]>0,self.base_actions[:20,1],-self.base_actions[:20,2]);end=baseline['trace'][-1];self.terminal=metrics(st.root(end['root_without_roads']),self.path,end['progress']);self.cache={};self.calls=0;self.callbacks=[];self.best=None;self.cross_baseline=None
 def controls(self,x):
  a=self.base_actions.copy();a[:20,0]=np.array(self.base_actions[:20,0]+.4*x[:20],np.float32);u=np.array(self.u+x[20:],np.float32);a[:20,1]=np.maximum(u,0.);a[:20,2]=np.maximum(-u,0.);return a
 def evaluate(self,x,fresh=False,keep=False,feedback=False):
  x=np.asarray(x,dtype=float);key=x.tobytes()
  if not fresh and not feedback and key in self.cache:return self.cache[key]
  self.st.guard();self.calls+=1
  if self.calls>400:raise RuntimeError('SHOOT_ROLLOUT_CAP')
  self.st.current='feedback-validation' if feedback else 'shoot-rollout-'+str(self.calls);actions=self.controls(x);root=self.root;s=initial_progress(root,self.path,54);history=list(self.data['history']);trace=[];commands=[];cons=[];minimum=float('inf');peak=over=pathmax=bodymax=0.;maxclip=history[0]/history[1];cross=None;reason=None;self.st.cost['forecast_calls']+=1;self.st.cost['shooting_rollouts']=self.calls
  def dot(pos):return sum((pos[j]-self.gate['point'][j])*self.gate['tangent'][j] for j in range(2))
  try:
   for i in range(32):
    self.st.checkpoint();self.st.save(self.D/'shoot-active-private.json',dict(decision=x.tolist(),feedback=feedback,hold=i,model_ticks=self.st.counter[0],cost=self.st.cost),True);self.st.guard(6400 if feedback and i>=20 else 4)
    if feedback and i>=20:
     action,detail=self.st.select(root,s,tuple(history))
     if action is None:reason='NO_ADMISSIBLE_FEEDBACK_RETURN';break
    else:action=actions[i];detail=dict(mode='OFFLINE_SHOOTING_SEQUENCE',online_admission=False)
    if not(np.isfinite(action).all() and abs(action[0])<=float(np.float32(.4)) and 0<=action[1]<=1 and 0<=action[2]<=1 and not(action[1]>0 and action[2]>0)):reason='CONTROL_DOMAIN';break
    commands.append(dict(index=55+i,action=action.tolist(),detail=detail));root=replace(root,planar=replace(root.planar,steer=-float(action[0])))
    for k in range(4):
     self.st.guard(4);before=root;old_s=s;f=force_rows(root,action);self.st.cost['force_evaluations']+=4;root=tick(root,float(action[1]),float(action[2]),self.index,self.st.counter);self.st.cost['forecast_ticks']+=1;q=project(root.center,self.path,s);s=q['s'];speed=math.hypot(*root.planar.linear.velocity);o=speed-reference(s,self.path)[0];ratio=max(z['ratio'] for z in f);history[0]+=sum(z['clipped'] for z in f);history[1]+=4;clip=history[0]/history[1]
     if self.st.cost['geometry_checks']>=self.st.geometry['max_checks']:raise RuntimeError('GEOMETRY_CAP')
     self.st.cost['geometry_checks']+=1;gap=margin(root,self.st.static['roads'],self.st.index,self.st.static['boundary'],self.st.edge,self.st.static['obstacles']);body=max(max(math.hypot(*(root.planar.linear.velocity[j]+w.offset[j] for j in range(2))) for w in root.planar.linear.wheels),math.hypot(*hull_pose(root)[1]));delta=s-old_s;upper=max(5.,2*math.dist(root.center,before.center));minimum=min(minimum,gap);peak=max(peak,ratio);over=max(over,o);pathmax=max(pathmax,q['distance']);bodymax=max(bodymax,body);maxclip=max(maxclip,clip);cons.extend([ADMISSION-ratio,gap-.5,(4.85-o)/5,(3.-q['distance'])/3,(99.999-body)/100,(.1-clip)/.1,(delta+.5)/5,(upper-delta)/5])
     if cross is None and dot(before.center)<0<=dot(root.center):
      frac=-dot(before.center)/(dot(root.center)-dot(before.center));vel=tuple(before.planar.linear.velocity[j]+frac*(root.planar.linear.velocity[j]-before.planar.linear.velocity[j]) for j in range(2));v=math.hypot(*vel);heading=abs(math.atan2(self.gate['tangent'][0]*vel[1]-self.gate['tangent'][1]*vel[0],sum(self.gate['tangent'][j]*vel[j] for j in range(2))));yaw=before.planar.yaw+frac*(root.planar.yaw-before.planar.yaw);n=4*i+k;cross=dict(lower_s=.02*n,upper_s=.02*(n+1),time_s=.02*(n+frac),speed=v,heading_error=heading,yaw_error=abs(yaw-v*self.gate['curvature']))
     state=asdict(root);state.pop('roads');trace.append(dict(index=55+i,raw=k+1,root_without_roads=state,progress=s,margin=gap,path_error=q['distance'],overspeed=o,body_speed=body,forces=f,clip_fraction=clip));self.st.safety_state=dict(min_margin_m=minimum,force_peak=peak,max_body_speed=bodymax,max_reference_overspeed=over)
     if body>=100 or not all(math.isfinite(z) for z in (s,speed,gap)):reason='MODEL_BODY_OR_NUMERIC_DOMAIN';break
    if reason:break
  except BaseException as exc:
   self.st.save(self.D/f'shoot-interrupted-{self.calls:03d}-private.json',dict(error=type(exc).__name__+':'+str(exc),decision=x.tolist(),trace=trace,commands=commands,model_ticks=self.st.counter[0],cost=self.st.cost));raise
  terminal=metrics(root,self.path,s);cons.extend([-100.]*(8*(128-len(trace))));assert len(cons)==1024
  cons.extend([self.terminal['path_error']+.10-terminal['path_error'],self.terminal['heading_error']+.02-terminal['heading_error'],self.terminal['yaw_error']+.05-terminal['yaw_error'],self.terminal['speed_deficit']+.15-terminal['speed_deficit'],dot(root.center)/10])
  if self.cross_baseline is not None and cross is not None:cons.extend([(cross['speed']-self.cross_baseline['speed']+.15)/10,self.cross_baseline['heading_error']+.02-cross['heading_error'],self.cross_baseline['yaw_error']+.05-cross['yaw_error']])
  else:cons.extend([0.,0.,0.] if self.cross_baseline is None else [-100.]*3)
  g=np.array(cons);objective=cross['time_s'] if cross else 2.58;physical=bool(reason is None and len(trace)==128 and peak<=ADMISSION and minimum>=.5 and over<=4.85 and bodymax<100 and pathmax<=3 and maxclip<=.1);feasible=bool(physical and cross and g.min()>=-1e-10);summary=dict(rollout=self.calls,feedback=feedback,objective_s=objective,crossing=cross,terminal=terminal,physical_safe=physical,feasible=feasible,minimum_constraint=float(g.min()),min_margin_m=minimum,force_peak=peak,max_reference_overspeed_m_s=over,max_body_speed_m_s=bodymax,max_path_error_m=pathmax,max_running_clipping=maxclip,raw_ticks=len(trace),stop_reason=reason)
  self.st.save(self.D/f'rollout-{self.calls:03d}-private.json',dict(decision=x.tolist(),summary=summary,model_ticks=self.st.counter[0],cost=self.st.cost.copy(),CPU_s=time.process_time()-self.st.cpu));value=dict(objective=objective,g=g,summary=summary)
  if not feedback:self.cache[key]=value
  if keep:value=dict(value,trace=trace,commands=commands)
  self.st.checkpoint();return value
 def callback(self,x):
  r=self.evaluate(x);summary=r['summary'];self.callbacks.append(dict(iteration=len(self.callbacks)+1,**summary));self.st.save(self.D/'solver-callbacks-private.json',self.callbacks,True)
  if summary['feasible'] and r['objective']<self.best['objective']:
   self.best=dict(x=np.array(x).tolist(),objective=r['objective'],summary=summary);self.st.save(self.D/'best-feasible-private.json',self.best,True)


def run_probe(st):
 D=Path('/workspace/haic-response545-private');data=json.loads((D/'entry-private.json').read_text());root=st.root(data['root']);st.arm='candidate';baseline=st.simulate('fresh-feasible541-baseline',root,54,tuple(data['history']),set(),False,32)
 if not baseline['pass_safety']:return dict(passed=False,learning_gate=False,promotion_eligible=False,reason='FEASIBLE_INITIALIZATION_FAILED')
 saved=json.loads((D/'fresh-feasible541-baseline-private.json').read_text());p=Problem(st,data,saved);zero=np.zeros(40);warm=p.evaluate(zero,fresh=True,keep=True);assert [x['root_without_roads'] for x in warm['trace']]==[x['root_without_roads'] for x in saved['trace']];assert warm['summary']['feasible'];p.cross_baseline=warm['summary']['crossing'];p.cache.clear();warm=p.evaluate(zero,fresh=True,keep=True);assert warm['summary']['feasible'];p.best=dict(x=zero.tolist(),objective=warm['objective'],summary=warm['summary']);st.save(D/'warmstart-replay-private.json',dict(summary=warm['summary'],root_replay_bit_identical=True,commands=warm['commands'],trace=warm['trace']));lower=np.r_[(-float(np.float32(.4))-p.base_actions[:20,0])/.4,-1.-p.u];upper=np.r_[(float(np.float32(.4))-p.base_actions[:20,0])/.4,1.-p.u]
 result=minimize(lambda x:p.evaluate(x)['objective'],zero,method='SLSQP',bounds=Bounds(lower,upper),constraints=[dict(type='ineq',fun=lambda x:p.evaluate(x)['g'])],callback=p.callback,options=dict(maxiter=6,ftol=1e-6,eps=1e-4,disp=False))
 solver=dict(success=bool(result.success),status=int(result.status),message=str(result.message),iterations=int(result.nit),function_evaluations=int(result.nfev),callback_count=len(p.callbacks),rollout_count=p.calls);st.save(D/'solver-result-private.json',dict(solver=solver,last_x=result.x.tolist(),best=p.best))
 best=p.evaluate(p.best['x'],fresh=True,keep=True);assert best['summary']['feasible'];st.save(D/'optimized-fresh-witness-private.json',dict(summary=best['summary'],decision=p.best['x'],commands=best['commands'],trace=best['trace']));gain=warm['objective']-best['objective'];learning=bool(gain>=.005);validation=None;performance=False
 if learning:
  validation=p.evaluate(p.best['x'],fresh=True,keep=True,feedback=True);st.save(D/'feedback-return-validation-private.json',dict(summary=validation['summary'],commands=validation['commands'],trace=validation['trace']));v=validation['summary'];performance=bool(v['feasible'] and v['min_margin_m']>=warm['summary']['min_margin_m']-.002 and warm['summary']['crossing']['lower_s']-v['crossing']['upper_s']>=.02-1e-12)
 return dict(passed=performance,learning_gate=learning,promotion_eligible=False,solver=solver,feasible_initialization=True,warmstart_replay_bit_identical=True,baseline=warm['summary'],optimized=best['summary'],interpolated_shooting_gain_s=gain,feedback_validation=validation['summary'] if validation else None,feedback_validation_not_run=not learning,interpretation='Finite feasible control-shooting mechanism only. No path solver continuation, no optimum/global lap/native claim. Only >=5ms feasible shooting gain admits feedback validation; >=20ms conservative common-plane gain and nonworse dynamic margin/terminal required for local performance.')
