"""One joint world-pose/corridor/relative-period/continuation source problem."""
import datetime,json,math,signal,time,traceback
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
import retry.safeperiod557_model as previous
import retry.period556_model as engine

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response558-private')
previous.D=D;engine.D=D
save,rd,sha=engine.save,engine.rd,engine.sha
short,rot,wrap,signature,difference=engine.short,engine.rot,engine.wrap,engine.signature,engine.difference
INPUTS=[Path('/workspace/haic-response515-private/collected-map-state-private.json'),Path('/workspace/haic-response551-private/frozen-paths-private.json'),Path('/workspace/haic-response557-private/fixture0-max-period-private.json')]
SOURCES=['retry/corridor558_model.py',*previous.SOURCES]

class Study(previous.Study):
 def __init__(self):
  D.mkdir(mode=0o700,exist_ok=False)
  self.static,self.paths,self.old=map(rd,INPUTS);self.path=self.paths['candidate'];self.initial=engine.load_root(dict(self.old['initial_root_without_roads'],roads=self.static['root']['roads']));self.speed=self.old['speed'];self.s0=self.path['arcs'][self.old['branch']['station']]
  self.goal=self.road(self.s0+self.speed*.48);self.follow_goal=self.road(self.s0+self.speed*.64)
  save(D/'goals-private.json',dict(primary=self.goal,follow=self.follow_goal,initial_station=self.s0,primary_T=.48,follow_T=.64,initial_speed=self.speed))
  self.contract=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',hypothesis='A single finite source shooting problem can connect same557 first synthetic safe-periodic initial state to a world-pose road target and compatible safe relative-periodic mechanical state, and plan a short following corridor segment jointly.',selection='Use first557fixture only, not sweep. Main6holds=.48s: 12 control variables accommodate world pose plus roughly9 independent mechanical endpoint conditions; selected BEFORE science, not a post-failure extension. Follow2holds=.16s independently gated but included in same design. Targets are original seed arc s0+v0*T and its segment tangent/curvature. No retargeting or duration change.',variables='8holds x steer/signed pedal (16), plus endpoint periodic v,beta,delta,gas,omega4 (8). Total24. Periodic v[5,v0]; same beta/joint/gas/omega bounds as557. Signed pedal positive gas/negative brake.',constraints=dict(relative_period='Endpoint target at world goal has source4raw mechanical relative-period equalities7, same scaled formulation557. Independent float32 ALL signature fields required.',world_primary='At exact .48s: distance to fixed goal<=.25m, body angle to road tangent minus target beta<=.02rad; full mechanical target tolerances as557transition.',world_follow='At exact .64s: distance to fixed next road goal<=.35m, velocity direction to road tangent<=.03rad, body angle to road tangent<=.08rad, yaw to v0*k_follow<=.15rad/s, speed to v0<=.5m/s.',all_road='At EVERY initial/post-raw state in32raw rollout AND4raw periodic target forecast: original source footprint>=.50, distance to original seed path<=3.0. Exact existing margin routine, inside solver constraints, not only post-filter.',all_physics='Every raw preclip ratio<=1.059, raw-prefix order statistic buffer.9999 for <=10% clipping; hull/wheel<=99.9; target v0 overspeed<=4.85. Body domain hard100 across every model tick. Target periodic reference is synthetic mechanism only; old551 overspeed separately recorded on independent validation.'),objective='Sum squared normalized primary position/body-angle/mechanical residuals and follow position/direction/body/yaw/speed errors, plus .01*((v_period-v0)/v0)^2. All declared goal tolerances also inequalities, not only objective preferences.',initialization='Single kinematic feedforward atan(3.24*k(s0+v0*(hold+.5)*.08)) for8 steering controls, constant557 initial gas. Endpoint v=v0, beta and gas scaled by k_goal/k_start and its square, delta=atan(3.24*k_goal), omega557initial. No PP, no alternative starts.',solver=dict(method='SLSQP',maxiter=40,ftol=1e-8,eps=1e-6,unique_evaluations=1100,cache='identical float64 vector',feasible='max scaled period equality<=1e-8 and min inequality>=-1e-7; preserve best feasible objective; numerical convergence, feasible witness and float32 accepted validation separate'),gates='No feasible iterate: stop NOT_FOUND, never physical infeasibility. Selected ONE feasible candidate only: independently validate target period4raw with ALL state residuals, then original6holds under unchanged safety and world/mechanical endpoints; only if pass execute preregistered2hold follow from actual predicted endpoint with SAME clip history. No alternate candidate.',caps=dict(model_ticks=42000,explicit_wheel_force_evaluations=175000,geometry_checks=42500,CPU_s=900,wall_s=1000,unique_solver_evaluations=1100,solver_runs=1),stop='finite cap/deadline/model body domain: checkpoint, preserve failure, no restart or extension. Solver nonconvergence and no feasible witness are separate. Unsafe trial forecasts counted, never actual/accepted execution.',actual_cap=0,new_seed_HOLDOUT_SEALED_other_environment_paid=0,research_remaining=22758,reserve=84000,reserve_used=0,source_sha256={p:sha(G/p) for p in SOURCES},private_inputs_sha256={str(p):sha(p) for p in INPUTS},goals_sha256=sha(D/'goals-private.json'))
  save(G/'retry/corridor558_contract.json',self.contract);save(D/'STARTED.json',dict(contract_sha256=sha(G/'retry/corridor558_contract.json')))
  self.cpu,self.wall=time.process_time(),time.perf_counter();self.counter=[0];self.index=engine.bounds(self.static['roads']);self.edge=engine.boundary_index(self.static['boundary']);self.cost=dict(explicit_wheel_force_evaluations=0,geometry_checks=0,body_checks=0,residual_calls=0,unsafe_forecast_raw=0,max_forecast_force=0.,max_body_speed=0.,unique_evaluations=0);self.current='joint_shooting';self.cache={};self.best=None;self.final_eval=None
  self.tol=dict(velocity=.15,yaw=.05,angular_momentum=self.initial.planar.inertia*.05,joints=.02,rates=.15,omega=.5,gas=.02,headings=.02,offsets=.15,levers=1e-6,friction=1e-8,steer=.02,constants=1e-10)
  signal.signal(signal.SIGPROF,self.guard);signal.setitimer(signal.ITIMER_PROF,900);signal.signal(signal.SIGALRM,self.guard);signal.setitimer(signal.ITIMER_REAL,1000)
 def road(self,s):
  from retry.lap518_control import point_at
  i=next(i for i in range(len(self.path['ds'])) if self.path['arcs'][i+1]>=s);p0=self.path['points'][i];p1=self.path['points'][(i+1)%len(self.path['ds'])];d=self.path['ds'][i];t=[(p1[j]-p0[j])/d for j in range(2)]
  return dict(station=s,segment=i,point=list(point_at(s,self.path)),tangent=t,angle=math.atan2(-t[0],t[1]),curvature=self.path['curvature'][i])
 def guard(self,*_):
  if self.counter[0]>=42000 or self.cost['explicit_wheel_force_evaluations']+4>175000:raise RuntimeError('MODEL_OR_FORCE_CAP')
  if self.cost['geometry_checks']>=42500:raise RuntimeError('GEOMETRY_CAP')
  if time.process_time()-self.cpu>=900 or time.perf_counter()-self.wall>=1000:raise RuntimeError('TIME_CAP')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.contract['deadline_utc']):raise RuntimeError('DEADLINE')
 def measure(self,root):
  self.guard();self.cost['geometry_checks']+=1
  mm=engine.margin(root,self.static['roads'],self.index,self.static['boundary'],self.edge,self.static['obstacles'])
  from retry.drive519_control import project
  q=project(root.center,self.path)
  return mm,q['distance']
 def simulate(self,root,actions):
  states=[root];rows=[]
  for action in actions:
   for _ in range(4):root,row=self.raw(root,action);states.append(root);rows.append(row)
  return root,states,rows
 def raw(self,root,action,validate=False,history=None,target_speed=None):
  if not validate:return engine.Study.raw(self,root,action)
  #558's optimizer also counts geometry. Do not inherit556's separate300-check
  #validation ceiling; use the single preregistered42500 ledger throughout.
  from dataclasses import replace
  self.guard();root=replace(root,planar=replace(root.planar,steer=-float(action[0])));fs=engine.force_rows(root,action);self.cost['explicit_wheel_force_evaluations']+=4
  peak=max(f['ratio'] for f in fs);clip=sum(f['clipped'] for f in fs);self.cost['max_forecast_force']=max(self.cost['max_forecast_force'],peak);mm,dd=self.measure(root)
  from retry.drive519_control import project,reference
  s=project(root.center,self.path)['s']%self.path['length'];oldover=math.hypot(*root.planar.linear.velocity)-reference(s,self.path)[0]
  history[0]+=clip;history[1]+=4;reason='FOOTPRINT' if mm<.5 else 'FORCE' if peak>1.059 else 'CLIP_HISTORY' if history[0]/history[1]>.1 else 'PATH' if dd>3 else 'TARGET_OVERSPEED' if math.hypot(*root.planar.linear.velocity)-target_speed>4.85 else None
  before=short(root)
  if reason:return root,dict(accepted=False,reason=reason,before_root_without_roads=before,forces=fs,margin=mm,patherror=dd,old551_overspeed=oldover)
  after=engine.tick(root,float(action[1]),float(action[2]),self.index,self.counter)
  body=max(math.hypot(*engine.hull_pose(after)[1]),*(math.hypot(*(after.planar.linear.velocity[j]+w.offset[j] for j in range(2))) for w in after.planar.linear.wheels));self.cost['body_checks']+=1;self.cost['max_body_speed']=max(self.cost['max_body_speed'],body)
  if body>=100 or not math.isfinite(body):save(D/'body-domain-first-private.json',dict(before=before,after=short(after),action=list(map(float,action)),body=body));raise RuntimeError('MODEL_BODY_DOMAIN')
  return after,dict(accepted=True,before_root_without_roads=before,root_without_roads=short(after),forces=fs,margin=mm,patherror=dd,old551_overspeed=oldover,body_speed=body)
 def actions(self,z,quant=False):return [np.array([-z[2*j],max(0.,z[2*j+1]),max(0.,-z[2*j+1])],np.float32 if quant else float) for j in range(8)]
 def periodic(self,z,quant=False):
  q=z[16:];v=float(q[0])*self.speed;x=np.r_[q[1:4],np.array(q[4:])*self.speed/.54]
  action=np.array([-x[1],x[2],0.],np.float32 if quant else float)
  if quant:x[1]=-float(action[0]);x[2]=float(action[1])
  a=self.goal['angle']-float(x[0]);p=self.initial.planar;delta=a-p.angle;levers=tuple(rot(r,delta) for r in p.levers);wheels=tuple(__import__('dataclasses').replace(w,heading=w.heading+delta,offset=rot(w.offset,delta)) for w in p.linear.wheels)
  pp=__import__('dataclasses').replace(p,angle=a,levers=levers,linear=__import__('dataclasses').replace(p.linear,wheels=wheels));template=__import__('dataclasses').replace(self.initial,center=tuple(self.goal['point']),planar=pp)
  branch=dict(self.old['branch'],speed=v,curvature=self.goal['curvature']);return self.fixture(template,branch,x),action
 def mechanical(self,root,target):
  a,b=signature(root),signature(target);vector=[];by={}
  for k in a:
   d=np.array(a[k]['value'])-b[k]['value']
   if k in ('joints','headings'):d=np.arctan2(np.sin(d),np.cos(d))
   vector.extend(d/self.tol[k]);by[k]=float(max(abs(d))/self.tol[k])
  return np.array(vector),by
 def endpoint(self,primary,follow,target):
  mech,by=self.mechanical(primary,target);dp=(np.array(primary.center)-self.goal['point'])/.25;da=wrap(primary.planar.angle-target.planar.angle)/.02
  vp=follow.planar.linear.velocity;vf=math.hypot(*vp);fd=(np.array(follow.center)-self.follow_goal['point'])/.35;fa=wrap(math.atan2(-vp[0],vp[1])-self.follow_goal['angle'])/.03;fb=wrap(follow.planar.angle-self.follow_goal['angle'])/.08;fy=(follow.planar.yaw-self.speed*self.follow_goal['curvature'])/.15;fv=(vf-self.speed)/.5
  e=np.r_[mech,dp,da,fd,fa,fb,fy,fv];ineq=np.r_[1-abs(mech),1-np.linalg.norm(dp),1-abs(da),1-np.linalg.norm(fd),1-abs(fa),1-abs(fb),1-abs(fy),1-abs(fv)]
  detail=dict(primary_position_error_m=float(np.linalg.norm(dp)*.25),primary_angle_error_rad=abs(da)*.02,primary_mechanical_normalized_errors=by,follow_position_error_m=float(np.linalg.norm(fd)*.35),follow_velocity_angle_error_rad=abs(fa)*.03,follow_body_angle_error_rad=abs(fb)*.08,follow_yaw_error_rad_s=abs(fy)*.15,follow_speed_error_m_s=abs(fv)*.5)
  return e,ineq,detail
 def evaluate(self,z):
  self.guard();key=np.array(z,np.float64).tobytes()
  if key in self.cache:return self.cache[key]
  if len(self.cache)>=1100:raise ValueError('UNIQUE_EVALUATION_CAP')
  target,pa=self.periodic(z);endp,pstates,prows=self.simulate(target,[pa]);final,states,rows=self.simulate(self.initial,self.actions(z));primary=states[24]
  a,b=signature(target),signature(endp);eq=np.r_[(np.array(b['velocity']['value'])-a['velocity']['value'])/90,(endp.planar.yaw-target.planar.yaw)*3.24/90,(np.array(b['omega']['value'])-a['omega']['value'])*.54/90]
  e,goal_ineq,detail=self.endpoint(primary,final,target);ineq=np.r_[self.constraints_from_rows(rows),self.constraints_from_rows(prows),goal_ineq]
  margins=[];distances=[]
  for root in [*states,*pstates]:
   mm,dd=self.measure(root);margins.append(mm);distances.append(dd)
  ineq=np.r_[ineq,(np.array(margins)-.5)/3,(3-np.array(distances))/3,*[(self.speed+4.85-math.hypot(*s.planar.linear.velocity))/100 for s in [*states,*pstates]]]
  objective=float(e@e+.01*(z[16]-1)**2);feasible=bool(max(abs(eq))<=1e-8 and min(ineq)>=-1e-7)
  value=dict(z=np.array(z).copy(),objective=objective,eq=eq,ineq=ineq,feasible=feasible,detail=detail,geometry_min=min(margins),patherror_max=max(distances))
  self.cache[key]=value;self.cost['unique_evaluations']+=1
  if feasible and(self.best is None or objective<self.best['objective']):self.best=value
  self.log.write(json.dumps(dict(call=len(self.cache),z=list(map(float,z)),objective=objective,eq_max=float(max(abs(eq))),ineq_min=float(min(ineq)),feasible=feasible,geometry_min=min(margins),patherror_max=max(distances),detail=detail,model_ticks=self.counter[0]))+'\n');self.log.flush()
  save(D/'latest-checkpoint-private.json',dict(z=list(map(float,z)),initial=short(self.initial),primary=short(primary),terminal=short(final),target=short(target),eq=eq.tolist(),ineq=ineq.tolist(),detail=detail,cost=self.cost,model_ticks=self.counter[0]),True);return value
 def validate(self,z):
  target,pa=self.periodic(z,True);final,pstates,prows=self.simulate(target,[pa]);diff=difference(final,target);periodic=max(x['normalized_max'] for x in diff.values())<=1;period_safe=True;ph=[0,0];pcheck=[]
  # Saved independent full period is also checked geometrically, without more
  # integration. Source forces/body values are from that exact period.
  for root,row in zip(pstates,prows):
   mm,dd=self.measure(root);ph[0]+=sum(f['clipped'] for f in row['forces']);ph[1]+=4;good=mm>=.5 and dd<=3 and max(f['ratio'] for f in row['forces'])<=1.059 and ph[0]/ph[1]<=.1 and row['body_speed']<100;pcheck.append(dict(margin=mm,patherror=dd,safe=good));period_safe &=good
  mm,dd=self.measure(pstates[-1]);period_safe &=mm>=.5 and dd<=3
  result=dict(periodic=periodic,period_safe=bool(period_safe),period_difference=diff,target_root_without_roads=short(target),period_rows=prows,period_checks=pcheck,primary_pass=False,follow_executed=False,passed=False)
  if periodic and period_safe:
   root=self.initial;history=[0,0];rows=[];primary=None;actions=self.actions(z,True)
   for j,action in enumerate(actions):
    for _ in range(4):
     root,row=self.raw(root,action,True,history,self.speed);rows.append(row)
     if not row['accepted']:break
    if not rows[-1]['accepted']:break
    mm,dd=self.measure(root)
    if mm<.5 or dd>3:rows.append(dict(accepted=False,reason='TERMINAL_GEOMETRY',margin=mm,patherror=dd,root_without_roads=short(root)));break
    if j==5:
     primary=root;mech,by=self.mechanical(root,target);pos=math.dist(root.center,self.goal['point']);angle=abs(wrap(root.planar.angle-target.planar.angle));passed=max(abs(mech))<=1 and pos<=.25 and angle<=.02
     result.update(primary_pass=bool(passed),primary_mechanical_normalized_errors=by,primary_position_error_m=pos,primary_angle_error_rad=angle,primary_root_without_roads=short(root))
     if not passed:break
     result['follow_executed']=True
   if primary is not None and result['follow_executed'] and len([r for r in rows if r['accepted']])==32:
    _,gi,detail=self.endpoint(primary,root,target);result.update(endpoint_detail=detail,passed=bool(min(gi)>=0))
   result.update(rows=rows,terminal_root_without_roads=short(root),first_failure=next((r.get('reason') for r in rows if not r['accepted']),None),clip_history=history,actions=[a.tolist() for a in actions])
  save(D/'independent-validation-private.json',result);return result
 def run(self):
  out={};self.log=(D/'solver-private.jsonl').open('x');(D/'solver-private.jsonl').chmod(0o600);opt=None;cap=None;validation=None
  try:
   x0=[]
   for j in range(8):x0.extend([math.atan(3.24*self.road(self.s0+self.speed*(j+.5)*.08)['curvature']),self.old['action'][1]])
   ratio=self.goal['curvature']/self.old['branch']['curvature'];xx=self.old['x'];x0.extend([1.,xx[0]*ratio,math.atan(3.24*self.goal['curvature']),xx[2]*ratio*ratio,*[w*.54/self.speed for w in xx[3:]]]);x0=np.array(x0)
   low=np.r_[np.tile([-.4,-1.],8),5/self.speed,-.6,-.4,0.,0.,0.,0.,0.];high=np.r_[np.tile([.4,1.],8),1.,.6,.4,1.,*[500*.54/self.speed]*4];x0=np.clip(x0,low+1e-10,high-1e-10)
   save(D/'initialization-private.json',dict(z=x0.tolist(),rule=self.contract['initialization']))
   try:
    opt=minimize(lambda z:self.evaluate(z)['objective'],x0,method='SLSQP',bounds=list(zip(low,high)),constraints=[dict(type='eq',fun=lambda z:self.evaluate(z)['eq']),dict(type='ineq',fun=lambda z:self.evaluate(z)['ineq'])],options=dict(maxiter=40,ftol=1e-8,eps=1e-6,disp=False));self.final_eval=self.evaluate(opt.x)
   except ValueError as e:
    if str(e)!='UNIQUE_EVALUATION_CAP':raise
    cap=str(e)
   if self.best is not None:validation=self.validate(self.best['z'])
   out=dict(completed=True,solver_success=bool(opt.success) if opt is not None else False,solver_status=int(opt.status) if opt is not None else None,solver_message=str(opt.message) if opt is not None else cap,nit=int(opt.nit) if opt is not None else None,feasible_iterate_found=self.best is not None,passed=bool(validation and validation['passed']),validation_executed=validation is not None)
  except BaseException as e:
   out=dict(completed=False,error=type(e).__name__+':'+str(e),feasible_iterate_found=self.best is not None);save(D/'failure-private.json',dict(error=out['error'],traceback=traceback.format_exc(),cost=self.cost,model_ticks=self.counter[0]))
  finally:
   self.log.close();signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
   def public(v):return None if v is None else dict(objective=v['objective'],eq_max=float(max(abs(v['eq']))),ineq_min=float(min(v['ineq'])),feasible=v['feasible'],detail=v['detail'],geometry_min=v['geometry_min'],patherror_max=v['patherror_max'])
   out.update(best_feasible=public(self.best),final_evaluation=public(self.final_eval),validation={k:v for k,v in (validation or {}).items() if k not in {'target_root_without_roads','primary_root_without_roads','terminal_root_without_roads','period_rows','rows','actions'}},cost=dict(self.cost,model_ticks=self.counter[0],internal_wheel_force_evaluations=4*self.counter[0],CPU_s=time.process_time()-self.cpu,wall_s=time.perf_counter()-self.wall),new_native_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT_queries=0,SEALED_queries=0,research_remaining=22758,reserve=84000,reserve_used=0,actual_baseline_s=13.66,no_lap_gain_observation=True)
   save(G/'retry/corridor558_result.json',out);print(json.dumps(out,indent=2))

if __name__=='__main__':Study().run()
