"""Relative-periodic shooting on the unchanged source mechanical map.

World pose is quotiented by SE(2); road IDs are logged separately. All source
mechanical memory, including the closure524 one-step wheel-offset lag, is checked.
"""
import datetime,hashlib,json,math,signal,time,traceback
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from retry.plan513_model import load_root
from retry.closure524_control import tick
from retry.speed516_control import force_rows
from retry.brake508_corridor import bounds,indexed_contacts
from retry.brake506_geometry import rectangle
from retry.brake510_common import boundary_index
from retry.corner515_model import margin
from retry.lap518_finish import hull_pose

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response556-private')
INPUTS=[Path('/workspace/haic-response515-private/collected-map-state-private.json'),Path('/workspace/haic-response551-private/frozen-paths-private.json'),Path('/workspace/haic-response555-recovery-private/steady-branches-private.json'),Path('/workspace/haic-response555-recovery-private/source-witnesses-private.json')]
SOURCES=['retry/period556_model.py','retry/plan513_model.py','retry/closure524_control.py','retry/plan512_control.py','retry/brake504_planar.py','retry/brake502_response.py','retry/speed516_control.py','retry/corner515_model.py','retry/lap518_finish.py']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rd=lambda p:json.loads(p.read_text())
def save(p,x,overwrite=False):
 data=(json.dumps(x,allow_nan=False,indent=2)+'\n').encode()
 if overwrite:
  tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_bytes(data);tmp.replace(p)
 else:
  with p.open('xb') as f:f.write(data)
 p.chmod(0o600 if D in p.parents else 0o644)
def short(root):
 z=asdict(root);z.pop('roads');return z
def rot(v,a):
 c,s=math.cos(a),math.sin(a);return (c*v[0]-s*v[1],s*v[0]+c*v[1])
def wrap(a):return math.atan2(math.sin(a),math.cos(a))
def signature(root):
 p=root.planar;w=p.linear.wheels;a=p.angle
 values={
 'velocity':(rot(p.linear.velocity,-a),1e-4),
 'yaw':([p.yaw],1e-5),'angular_momentum':([p.angular_momentum],1e-5),
 'joints':(p.joints,1e-7),'rates':(p.rates,1e-5),
 'omega':([z.omega for z in w],1e-4),'gas':([z.gas for z in w],1e-7),
 'headings':([wrap(z.heading-a) for z in w],1e-7),
 'offsets':([v for z in w for v in rot(z.offset,-a)],1e-4),
 'levers':([v for z in p.levers for v in rot(z,-a)],1e-6),
 'friction':([z.friction for z in w],1e-8),'steer':([p.steer],1e-7),
 'constants':([p.linear.mass,p.linear.engine_multiplier,p.inertia,*p.wheel_inertias,p.steering_multiplier,root.floor,root.skin],1e-10)}
 return {k:dict(value=list(v),tolerance=t) for k,(v,t) in values.items()}
def difference(after,before):
 a,b=signature(after),signature(before);out={}
 for k in a:
  delta=np.array(a[k]['value'])-b[k]['value']
  if k in ('headings','joints'):delta=np.arctan2(np.sin(delta),np.cos(delta))
  out[k]=dict(max_abs=float(max(abs(delta))),normalized_max=float(max(abs(delta))/a[k]['tolerance']))
 return out

class Study:
 def __init__(self):
  D.mkdir(mode=0o700,exist_ok=False)
  self.contract=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',hypothesis='At the SAME two555 synthetic fixtures, source four-raw relative-periodic mechanical states exist including wheel omega, gas memory, steering joint/rates and lagged wheel offsets. Constant gas/steer, no braking in periodic-state branch. This is a new discrete shooting representation, not more iterations of555 continuous equilibrium.',representation='Mechanical full state modulo SE(2), including mass/inertia, wheel headings/friction, joints/rates, omega/gas, yaw/angular momentum, offsets/levers and steering memory. Global roads are not SE(2) invariant: road tile identities are logged, all accepted validations require original map footprint/friction. Synthetic fixture, not reachable native state.',solve=dict(period_raw=4,variables='beta,delta,gas, four wheel omega; speed and initial yaw=v*k fixed from same555fixture',bounds='beta +/-.6, delta +/-.4, gas[0,1], omega[0,500]',max_nfev=60,max_residual_calls_per_state=800,gtol=None,ftol=1e-11,xtol=1e-11,solver_gate='velocity body-frame <=1e-4m/s, yaw<=1e-5rad/s, wheel omega<=1e-4rad/s; independently verify ALL signature fields after float32 actions; normalized maximum<=1. No solver_success substitution.'),validation=dict(independent_period_raw=4,exact_cycles=8,perturbed_cycles=8,perturbation='one deterministic vx +=1e-3m/s in body coordinates and rear wheel3 omega +=1e-2rad/s, same synthetic pose; no multiple perturbation search',finite_stability='report initial/final/max normalized deviation from matched unperturbed period phases; contraction is diagnostic, not a necessary physical gate or asymptotic stability proof',safety='accepted validation: footprint>=.50, raw force<=1.059, hull/all wheels<100, clipping<=10% cumulatively from fixture validation start, position error to original seed path<=3m; diagnostic speed reference is each synthetic branch target, overspeed<=4.85. Also log old551 reference overspeed separately; this is NOT an old551 compliant participant controller.'),transition=dict(trigger='Both original fixtures pass independent four-raw mechanical fullstate and safety; exact multi-period safety failures are logged separately, not evidence that the periodic state does not exist. Minimum transition may still run in fresh initial fixture if periodic existence passes; perturbed stability is diagnostic.',target='Only next seed station after first555fixture, same speed as source fixture, its existing signed curvature. Solve once using same budget/parameterization; no alternate target.',controls='4 holds x steer and signed pedal, continuous solver then float32 independent validation; negative pedal is brake, positive gas. No PP/reference steering. One initial linear command interpolation; max_nfev60/max residual calls1000.',endpoint='ALL mechanical signature normalized residual<=1 using transition tolerances: velocity .15m/s,yaw .05,angular momentum I*.05,joints .02,rates .15,omega .5,gas .02,headings .02,offsets .15; levers/constants/friction unchanged; pose angle free moduloSE2.',after='If endpoint+physical safety pass, three additional constant-target holds must stay safe and within same endpoint tolerances. No cold/carry/native or lap-time claim.'),caps=dict(model_ticks=30000,explicit_wheel_force_evaluations=125000,geometry_checks=300,CPU_s=300,wall_s=360,periodic_states_max=3,transition_rollouts_max=1000),stop='Budget/deadline/model body domain -> stop with checkpoint; failure of both original periodic gates -> no transition. No parameter/speed/curvature sweep or rerun. Finite solver failure is not physical impossibility. Unsafe solver trials are forecasts only, counted and retained, never accepted validation.',actual_cap=0,research_remaining=22758,reserve=84000,reserve_used=0,new_seed_HOLDOUT_SEALED_other_environment_paid=0,source_sha256={p:sha(G/p) for p in SOURCES},private_inputs_sha256={str(p):sha(p) for p in INPUTS})
  save(G/'retry/period556_contract.json',self.contract);save(D/'STARTED.json',dict(contract_sha256=sha(G/'retry/period556_contract.json')))
  self.cpu=time.process_time();self.wall=time.perf_counter();self.counter=[0];self.cost=dict(explicit_wheel_force_evaluations=0,geometry_checks=0,body_checks=0,residual_calls=0,unsafe_forecast_raw=0,max_forecast_force=0.,max_body_speed=0.)
  self.static,self.paths,self.branches,self.old=map(rd,INPUTS);self.index=bounds(self.static['roads']);self.edge=boundary_index(self.static['boundary']);self.current=None;self.results=[];self.transition_result=None
  signal.signal(signal.SIGPROF,self.guard);signal.setitimer(signal.ITIMER_PROF,300);signal.signal(signal.SIGALRM,self.guard);signal.setitimer(signal.ITIMER_REAL,360)
 def guard(self,*_):
  if self.counter[0]>=30000 or self.cost['explicit_wheel_force_evaluations']+4>125000:raise RuntimeError('INTEGRATION_OR_FORCE_CAP')
  if time.process_time()-self.cpu>=300 or time.perf_counter()-self.wall>=360:raise RuntimeError('TIME_CAP')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.contract['deadline_utc']):raise RuntimeError('DEADLINE')
 def fixture(self,template,branch,x):
  beta,delta,gas,*omega=map(float,x);p=template.planar;yaw=branch['speed']*branch['curvature'];a=p.angle
  # closure524 offsets use PRE-step levers: the periodic offset has one-step
  # rotation lag. The complete offset residual is still independently tested.
  lag=tuple(rot(r,-.02*yaw) for r in p.levers)
  velocity=rot((-branch['speed']*math.sin(beta),branch['speed']*math.cos(beta)),a)
  wheels=tuple(replace(w,omega=omega[i],gas=gas if i>=2 else 0.,heading=a+(delta if i<2 else 0.),offset=(-yaw*lag[i][1],yaw*lag[i][0]),friction=400.) for i,w in enumerate(p.linear.wheels))
  pp=replace(p,linear=replace(p.linear,velocity=velocity,wheels=wheels),yaw=yaw,angular_momentum=p.inertia*yaw,joints=(delta,delta,0.,0.),rates=(0.,)*4,steer=delta)
  root=replace(template,planar=pp)
  ids=tuple(indexed_contacts(rectangle(tuple(root.center[t]+r[t] for t in range(2)),w.heading),root.roads,self.index,root.skin) for r,w in zip(p.levers,wheels))
  return replace(root,current_contacts=ids)
 def raw(self,root,action,validate=False,history=None,target_speed=None):
  self.guard();root=replace(root,planar=replace(root.planar,steer=-float(action[0])))
  fs=force_rows(root,action);self.cost['explicit_wheel_force_evaluations']+=4;peak=max(z['ratio'] for z in fs);clip=sum(z['clipped'] for z in fs)
  self.cost['max_forecast_force']=max(self.cost['max_forecast_force'],peak)
  before=short(root);mm=None;patherror=None;oldover=None
  if validate:
   if self.cost['geometry_checks']>=300:raise RuntimeError('GEOMETRY_CAP')
   mm=margin(root,self.static['roads'],self.index,self.static['boundary'],self.edge,self.static['obstacles']);self.cost['geometry_checks']+=1
   from retry.drive519_control import project,reference
   projection=project(root.center,self.paths['candidate']);progress=projection['s']%self.paths['candidate']['length'];patherror=projection['distance'];oldref=reference(progress,self.paths['candidate'])[0];oldover=math.hypot(*root.planar.linear.velocity)-oldref
   history[0]+=clip;history[1]+=4
   reason='FOOTPRINT' if mm<.5 else 'FORCE' if peak>1.059 else 'CLIP_HISTORY' if history[0]/history[1]>.1 else 'PATH' if patherror>3 else 'TARGET_OVERSPEED' if math.hypot(*root.planar.linear.velocity)-target_speed>4.85 else None
   if reason:return root,dict(accepted=False,reason=reason,before_root_without_roads=before,forces=fs,margin=mm,patherror=patherror,old551_overspeed=oldover)
  elif peak>1.059:self.cost['unsafe_forecast_raw']+=1
  after=tick(root,float(action[1]),float(action[2]),self.index,self.counter)
  body=max(math.hypot(*hull_pose(after)[1]),*(math.hypot(*(after.planar.linear.velocity[j]+w.offset[j] for j in range(2))) for w in after.planar.linear.wheels));self.cost['body_checks']+=1;self.cost['max_body_speed']=max(self.cost['max_body_speed'],body)
  if body>=100 or not math.isfinite(body):
   save(D/'body-domain-first-private.json',dict(before=before,after=short(after),action=list(map(float,action)),body=body));raise RuntimeError('MODEL_BODY_DOMAIN')
  return after,dict(accepted=True,before_root_without_roads=before,root_without_roads=short(after),forces=fs,margin=mm,patherror=patherror,old551_overspeed=oldover,body_speed=body)
 def rollout(self,root,actions,validate=False,target_speed=None):
  rows=[];history=[0,0]
  for action in actions:
   for _ in range(4):
    root,row=self.raw(root,action,validate,history,target_speed);rows.append(row)
    if not row['accepted']:return root,rows,False
  if validate:
   if self.cost['geometry_checks']>=300:raise RuntimeError('GEOMETRY_CAP')
   mm=margin(root,self.static['roads'],self.index,self.static['boundary'],self.edge,self.static['obstacles']);self.cost['geometry_checks']+=1
   from retry.drive519_control import project
   patherror=project(root.center,self.paths['candidate'])['distance']
   reason='TERMINAL_FOOTPRINT' if mm<.5 else 'TERMINAL_PATH' if patherror>3 else 'TERMINAL_TARGET_OVERSPEED' if math.hypot(*root.planar.linear.velocity)-target_speed>4.85 else None
   if reason:
    rows.append(dict(accepted=False,reason=reason,terminal_check=True,root_without_roads=short(root),margin=mm,patherror=patherror));return root,rows,False
  return root,rows,True
 def solve(self,label,template,branch):
  self.current=dict(label=label,phase='periodic_solve');calls=0
  x0=np.array([branch['beta'],branch['delta'],branch['gas'],*branch['omegas']]);low=np.array([-.6,-.4,0.,0.,0.,0.,0.]);high=np.array([.6,.4,1.,500.,500.,500.,500.]);x0=np.clip(x0,low+1e-10,high-1e-10)
  log=(D/f'{label}-solver-private.jsonl').open('x');(D/f'{label}-solver-private.jsonl').chmod(0o600)
  def residual(x):
   nonlocal calls
   self.guard();calls+=1;self.cost['residual_calls']+=1
   if calls>800:raise RuntimeError('PERIODIC_RESIDUAL_CALL_CAP')
   start=self.fixture(template,branch,x);action=[-float(x[1]),float(x[2]),0.];end,rows,_=self.rollout(start,[action]);a,b=signature(start),signature(end)
   z=np.r_[np.array(b['velocity']['value'])-a['velocity']['value'],3.24*(end.planar.yaw-start.planar.yaw),.54*(np.array(b['omega']['value'])-a['omega']['value'])]
   log.write(json.dumps(dict(call=calls,x=list(map(float,x)),residual=z.tolist(),peak=max(max(f['ratio'] for f in r['forces']) for r in rows),model_ticks=self.counter[0]))+'\n');log.flush()
   save(D/'latest-checkpoint-private.json',dict(current=self.current,x=list(map(float,x)),initial=short(start),terminal=short(end),residual=z.tolist(),cost=self.cost,model_ticks=self.counter[0]),True)
   return z
  try:opt=least_squares(residual,x0,bounds=(low,high),max_nfev=60,gtol=None,ftol=1e-11,xtol=1e-11)
  finally:log.close()
  x=opt.x;action=np.array([-x[1],x[2],0.],np.float32)
  # Commands and the corresponding fixed gas/joint memory must be representable
  # by actual float32 actions. Omega/beta remain solved physical state variables.
  quant=x.copy();quant[1]=-float(action[0]);quant[2]=float(action[1]);initial=self.fixture(template,branch,quant)
  final,diagnostic_rows,_=self.rollout(initial,[action]);diff=difference(final,initial);mech=max(z['normalized_max'] for z in diff.values())<=1
  rows=[];safe=False
  if mech:_,rows,safe=self.rollout(initial,[action],True,branch['speed'])
  result=dict(label=label,solver_success=bool(opt.success),solver_status=int(opt.status),nfev=opt.nfev,residual_calls=calls,solver_residual_max=float(max(abs(opt.fun))),independent_raw_completed=len(diagnostic_rows),mechanical_periodic=mech,validation_safe=safe,signature_difference=diff,first_failure=next((r['reason'] for r in rows if not r['accepted']),None) if mech else 'FULLSTATE_PERIOD_RESIDUAL',initial_root_without_roads=short(initial),terminal_root_without_roads=short(final),action=action.tolist(),rows=rows,independent_rows=diagnostic_rows,x=quant.tolist(),branch=branch)
  save(D/f'{label}-period-private.json',result);self.results.append(result)
  return result,initial,action
 def cycles(self,label,initial,action,speed,perturb=False):
  nominal=initial;p=initial.planar
  if perturb:
   dv=rot((.001,0.),p.angle);w=list(p.linear.wheels);w[3]=replace(w[3],omega=w[3].omega+.01)
   initial=replace(initial,planar=replace(p,linear=replace(p.linear,velocity=tuple(p.linear.velocity[j]+dv[j] for j in range(2)),wheels=tuple(w))))
  final,rows,safe=self.rollout(initial,[action]*8,True,speed)
  initial_error=difference(initial,nominal);end_error=difference(final,nominal);e0=max(z['normalized_max'] for z in initial_error.values());e1=max(z['normalized_max'] for z in end_error.values())
  out=dict(label=label,perturbed=perturb,safe=safe,raw_completed=sum(z['accepted'] for z in rows),first_failure=next((z['reason'] for z in rows if not z['accepted']),None),initial_root_without_roads=short(initial),terminal_root_without_roads=short(final),rows=rows,signature_drift=difference(final,initial),initial_error_to_nominal=initial_error,end_error_to_nominal=end_error,initial_error_normalized_max=e0,end_error_normalized_max=e1,finite_horizon_error_ratio=e1/e0 if perturb and safe and e0 else None)
  save(D/f'{label}-cycles-private.json',out);return out
 def transition(self,source,source_root):
  self.current=dict(phase='transition_target_solve');i=(source['branch']['station']+1)%len(self.branches);branch=dict(self.branches[i],speed=source['branch']['speed'])
  target,target_root,target_action=self.solve('transition-target',source_root,branch)
  if not(target['mechanical_periodic'] and target['validation_safe']):return dict(executed=False,reason='TARGET_PERIODIC_GATE_FAILED')
  self.current=dict(phase='transition_shooting');calls=0;target_sig=signature(target_root);I=target_root.planar.inertia
  tolerances=dict(velocity=.15,yaw=.05,angular_momentum=I*.05,joints=.02,rates=.15,omega=.5,gas=.02,headings=.02,offsets=.15,levers=1e-6,friction=1e-8,steer=.02,constants=1e-10)
  def errors(root):
   sig=signature(root);v=[];by={}
   for key in sig:
    d=np.array(sig[key]['value'])-target_sig[key]['value']
    if key in ('joints','headings'):d=np.arctan2(np.sin(d),np.cos(d))
    by[key]=float(max(abs(d))/tolerances[key]);v.extend(d/tolerances[key])
   return np.array(v),by
  def actions(x,quantize=False):
   return [np.array([-x[2*j],max(0.,x[2*j+1]),max(0.,-x[2*j+1])],np.float32 if quantize else float) for j in range(4)]
  log=(D/'transition-solver-private.jsonl').open('x');(D/'transition-solver-private.jsonl').chmod(0o600)
  def residual(x):
   nonlocal calls
   self.guard();calls+=1;self.cost['residual_calls']+=1
   if calls>1000:raise RuntimeError('TRANSITION_ROLLOUT_CAP')
   final,rows,_=self.rollout(source_root,actions(x));z,by=errors(final)
   log.write(json.dumps(dict(call=calls,x=list(map(float,x)),normalized_errors=by,objective=float(z@z),peak=max(max(f['ratio'] for f in r['forces']) for r in rows),model_ticks=self.counter[0]))+'\n');log.flush()
   save(D/'latest-checkpoint-private.json',dict(current=self.current,x=list(map(float,x)),terminal=short(final),normalized_errors=by,cost=self.cost,model_ticks=self.counter[0]),True)
   return z
  x0=np.array([z for t in (.25,.5,.75,1.) for z in ((1-t)*(-source['action'][0])+t*(-target_action[0]),(1-t)*source['action'][1]+t*target_action[1])])
  try:opt=least_squares(residual,x0,bounds=(np.tile([-.4,-1.],4),np.tile([.4,1.],4)),max_nfev=60,gtol=None,ftol=1e-11,xtol=1e-11)
  finally:log.close()
  aa=actions(opt.x,True);final,rows,safe=self.rollout(source_root,aa,True,branch['speed']);_,by=errors(final);match=max(by.values())<=1 and safe
  follow=[];follow_safe=False;endby=None
  if match:
   end,follow,follow_safe=self.rollout(final,[target_action]*3,True,branch['speed']);_,endby=errors(end)
  result=dict(executed=True,residual_calls=calls,nfev=opt.nfev,solver_success=bool(opt.success),endpoint_safe=safe,endpoint_match=match,endpoint_normalized_errors=by,first_failure=next((r['reason'] for r in rows if not r['accepted']),None),follow_executed=bool(follow),follow_safe=follow_safe,follow_end_normalized_errors=endby,passed=match and follow_safe and max(endby.values())<=1 if endby else False,actions=[z.tolist() for z in aa],rows=rows,follow_rows=follow,target_periodic_label=target['label'],terminal_root_without_roads=short(final))
  save(D/'transition-private.json',result);return result
 def run(self):
  out={};cycle_results=[];original=[]
  try:
   for n,w in enumerate(self.old):
    template=load_root(dict(w['initial_root_without_roads'],roads=self.static['root']['roads']));branch=self.branches[w['station']]
    result,initial,action=self.solve(f'fixture{n}',template,branch);original.append((result,initial,action))
   for result,initial,action in original:
    if result['mechanical_periodic'] and result['validation_safe']:
     cycle_results.append(self.cycles(result['label']+'-exact',initial,action,result['branch']['speed']))
     cycle_results.append(self.cycles(result['label']+'-perturbed',initial,action,result['branch']['speed'],True))
   if len(original)==2 and all(r['mechanical_periodic'] and r['validation_safe'] for r,_,_ in original):self.transition_result=self.transition(original[0][0],original[0][1])
   else:self.transition_result=dict(executed=False,reason='ORIGINAL_PERIODIC_GATE_FAILED')
   out=dict(completed=True)
  except BaseException as e:
   out=dict(completed=False,error=type(e).__name__+':'+str(e));save(D/'failure-private.json',dict(error=out['error'],traceback=traceback.format_exc(),current=self.current,cost=self.cost,model_ticks=self.counter[0]))
  finally:
   signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
   public=lambda r:dict(label=r['label'],solver_success=r['solver_success'],nfev=r['nfev'],residual_calls=r['residual_calls'],solver_residual_max=r['solver_residual_max'],independent_raw_completed=r['independent_raw_completed'],mechanical_periodic=r['mechanical_periodic'],validation_safe=r['validation_safe'],first_failure=r['first_failure'],signature_difference=r['signature_difference'])
   out.update(periodic_states=[public(r) for r in self.results],cycles=[dict(label=r['label'],perturbed=r['perturbed'],safe=r['safe'],raw_completed=r['raw_completed'],first_failure=r['first_failure'],signature_drift=r['signature_drift'],initial_error_normalized_max=r['initial_error_normalized_max'],end_error_normalized_max=r['end_error_normalized_max'],finite_horizon_error_ratio=r['finite_horizon_error_ratio']) for r in cycle_results],transition={k:v for k,v in (self.transition_result or {}).items() if k not in ('rows','follow_rows','actions','terminal_root_without_roads')},cost=dict(self.cost,model_ticks=self.counter[0],internal_wheel_force_evaluations=4*self.counter[0],CPU_s=time.process_time()-self.cpu,wall_s=time.perf_counter()-self.wall),new_native_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT_queries=0,SEALED_queries=0,research_remaining=22758,reserve=84000,reserve_used=0,actual_baseline_s=13.66,no_lap_gain_observation=True)
   save(G/'retry/period556_result.json',out);print(json.dumps(out,indent=2))

if __name__=='__main__':Study().run()
