"""Joint speed/relative-period/safety constrained design; no speed grid."""
import datetime,hashlib,json,math,signal,time,traceback
from pathlib import Path
from dataclasses import replace
import numpy as np
from scipy.optimize import minimize
import retry.period556_model as engine

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response557-private')
# Reuse mechanics and validation, redirect ONLY runtime storage to the new run.
# The committed556 module and all556 evidence remain byte-identical.
engine.D=D
save,rd,sha=engine.save,engine.rd,engine.sha
short,signature,difference,rot=engine.short,engine.signature,engine.difference,engine.rot
INPUTS=engine.INPUTS+[Path('/workspace/haic-response556-private/fixture0-period-private.json'),Path('/workspace/haic-response556-private/fixture1-period-private.json')]
SOURCES=['retry/safeperiod557_model.py',*engine.SOURCES]

class Study(engine.Study):
 def __init__(self):
  D.mkdir(mode=0o700,exist_ok=False)
  self.contract=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',hypothesis='At the same two synthetic curvatures, jointly optimize speed, full mechanical relative-periodicity and preclip-force/clipping/body-speed constraints. No fixed-speed post-filter or speed grid.',problem=dict(variables='v, beta, delta, gas, four wheel omega; constant steer/gas, brake0; source4raw period including lagged offset memory',bounds='v[5,90], beta +/-.6, delta +/-.4, gas[0,1], omega[0,500]. These are finite branch bounds, not physical impossibility claims.',equalities='body-frame velocity difference/90, yaw difference*3.24/90, four wheel omega differences*.54/90 ==0. Other mechanical memory follows the parameterization and is independently checked, including all556signature fields.',inequalities='all16 raw force ratios<=1.059; for EACH raw prefix, sorted force ratio at rank floor(.1*N)+1 from largest <=.9998 for periodic design, <=.9999 for transition, sufficient for clipping<=10% with float32 reserve; all raw hull/wheel speeds<=99.9. The .9998/.9999 clip reserves is a conservative numerical sufficient condition, not physical necessity.',objectives='For each identical feasible set: first maximize v; then minimize v initialized at selected max solution. Two finite local solves, no speed grid. Feasible endpoint witnesses do not certify global extrema or every intermediate speed.',initialization='One max initialization per fixture: v=.9*556speed, omega=.9*556omega, beta/delta/gas from556solution. No alternate start. Min starts at selected max witness.',optimizer='SLSQP maxiter60,ftol1e-10,eps1e-7; <=700 unique source evaluations/state objective. Cache identical float64 variables across objective/constraints/Jacobian calls. Keep best evaluated feasible iterate according to fixed objective; final convergence and feasible witness are separate.',feasible_numerical_gate='max scaled periodic equality<=1e-8, minimum inequality>=-1e-8; independent float32 fullstate normalized residual<=1 and original safety checks determine admitted witness. No feasible iterate means NOT_FOUND, never no safe orbit proof.'),validation=dict(independent='each selected endpoint: float32 independent4raw mechanical comparison then separate accepted4raw safety; same556tolerances and body/path/footprint/clip guards',cycles='Admitted MAX witness in each fixture:8 exact cycles and8 cycles with one prescribed body-vx+.001 and rear wheel3 omega+.01 perturbation. Finite error growth diagnostic; no asymptotic stability claim. Physical/map failure stops that rollout without changing existence verdict.',references='Synthetic target speed gives mechanical overspeed reference4.85; retain old551 reference overspeed as separate diagnostic. No old551 compliance, whole-road feasibility, native reachability or actual policy promotion is claimed.'),transition=dict(trigger='Both original MAX witnesses independently admitted. Multiple-period or perturbation outcomes remain separate; fresh same source MAX fixture may be used for the preregistered minimal transition.',target='Next existing seed curvature after first fixture only. Maximize safe periodic speed with upper bound source MAX speed; same constrained problem, one initialization from source solution; <=700unique evaluations. No alternative curvature.',control_problem='4holds x steer/signed pedal; SLSQP min sum squared normalized fullstate endpoint errors, subject to raw force/prefixclip/body constraints throughout16raw; maxiter60/ftol1e-10/eps1e-7, <=1000unique rollouts. One linear interpolation of source/target commands.',endpoint='556transition fullstate tolerances: v.15,yaw.05,M=I*.05,joints.02,rates.15,omega.5,gas.02,heading.02,offset.15; lever1e-6/friction1e-8/constants1e-10. Select best feasible iterate; independent float32 validation then3 target holds if endpoint pass.'),caps=dict(model_ticks=38000,explicit_wheel_force_evaluations=160000,geometry_checks=300,CPU_s=480,wall_s=540,periodic_extremum_solves_max=5,unique_evals_per_extremum=700,transition_unique_rollouts_max=1000),stop='Stop phase on finite solver cap; retain best feasible iterate and classify convergence separately. Stop whole run on deadline/body domain/global compute cap with full checkpoint. No rerun, no alternate initialization, no post-result change of gates. No feasible witness is solver/branch uncertainty, not an infeasibility certificate.',actual_cap=0,new_seed_HOLDOUT_SEALED_other_environment_paid=0,research_remaining=22758,reserve=84000,reserve_used=0,source_sha256={p:sha(G/p) for p in SOURCES},private_inputs_sha256={str(p):sha(p) for p in INPUTS})
  save(G/'retry/safeperiod557_contract.json',self.contract);save(D/'STARTED.json',dict(contract_sha256=sha(G/'retry/safeperiod557_contract.json')))
  self.cpu,self.wall=time.process_time(),time.perf_counter();self.counter=[0]
  self.cost=dict(explicit_wheel_force_evaluations=0,geometry_checks=0,body_checks=0,residual_calls=0,unsafe_forecast_raw=0,max_forecast_force=0.,max_body_speed=0.,periodic_unique_evaluations=0,transition_unique_evaluations=0)
  self.static,self.paths,self.branches,self.old,*self.previous=map(rd,INPUTS)
  self.index=engine.bounds(self.static['roads']);self.edge=engine.boundary_index(self.static['boundary']);self.current=None;self.results=[];self.transition_result=None
  signal.signal(signal.SIGPROF,self.guard);signal.setitimer(signal.ITIMER_PROF,480);signal.signal(signal.SIGALRM,self.guard);signal.setitimer(signal.ITIMER_REAL,540)
 def guard(self,*_):
  if self.counter[0]>=38000 or self.cost['explicit_wheel_force_evaluations']+4>160000:raise RuntimeError('INTEGRATION_OR_FORCE_CAP')
  if time.process_time()-self.cpu>=480 or time.perf_counter()-self.wall>=540:raise RuntimeError('TIME_CAP')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.contract['deadline_utc']):raise RuntimeError('DEADLINE')
 def state(self,template,branch,z):
  v=90*float(z[0]);x=np.r_[z[1:4],np.array(z[4:])*90/.54]
  return self.fixture(template,dict(branch,speed=v),x),x
 def constraints_from_rows(self,rows,clip_ceiling=.9999):
  ratios=[f['ratio'] for row in rows for f in row['forces']];ineq=[1.059-z for z in ratios]
  for n in range(4,len(ratios)+1,4):
   rank=int(math.floor(.1*n))+1;ineq.append(clip_ceiling-sorted(ratios[:n],reverse=True)[rank-1])
  ineq.extend((99.9-r['body_speed'])/100 for r in rows)
  return np.array(ineq)
 def solve(self,label,template,branch,seed,direction,ceiling=90.):
  self.current=dict(label=label,phase='constrained_periodic',objective=direction);cache={};best=None
  z0=np.r_[seed['speed']/90,seed['x'][:3],np.array(seed['x'][3:])*.54/90]
  low=np.array([5/90,-.6,-.4,0.,0.,0.,0.,0.]);high=np.array([ceiling/90,.6,.4,1.,3.,3.,3.,3.]);z0=np.clip(z0,low+1e-12,high-1e-12)
  log=(D/f'{label}-solver-private.jsonl').open('x');(D/f'{label}-solver-private.jsonl').chmod(0o600)
  def evaluate(z):
   nonlocal best
   self.guard();key=np.asarray(z,dtype=np.float64).tobytes()
   if key in cache:return cache[key]
   if len(cache)>=700:raise ValueError('UNIQUE_PERIODIC_EVALUATION_CAP')
   initial,x=self.state(template,branch,z);action=[-float(x[1]),float(x[2]),0.];final,rows,_=self.rollout(initial,[action]);a,b=signature(initial),signature(final)
   eq=np.r_[(np.array(b['velocity']['value'])-a['velocity']['value'])/90,(final.planar.yaw-initial.planar.yaw)*3.24/90,(np.array(b['omega']['value'])-a['omega']['value'])*.54/90];ineq=self.constraints_from_rows(rows,.9998)
   feasible=bool(max(abs(eq))<=1e-8 and min(ineq)>=-1e-8)
   value=dict(eq=eq,ineq=ineq,feasible=feasible,z=np.array(z).copy(),speed=90*float(z[0]),x=x.tolist(),raw_force_peak=max(f['ratio'] for row in rows for f in row['forces']),clipped_wheels=sum(f['clipped'] for row in rows for f in row['forces']))
   cache[key]=value;self.cost['periodic_unique_evaluations']+=1
   if feasible and (best is None or (value['speed']>best['speed'] if direction=='max' else value['speed']<best['speed'])):best=value
   log.write(json.dumps(dict(call=len(cache),z=list(map(float,z)),eq=eq.tolist(),min_inequality=float(min(ineq)),feasible=feasible,speed=value['speed'],peak=value['raw_force_peak'],clipped=value['clipped_wheels'],model_ticks=self.counter[0]))+'\n');log.flush()
   save(D/'latest-checkpoint-private.json',dict(current=self.current,z=list(map(float,z)),initial=short(initial),terminal=short(final),eq=eq.tolist(),ineq=ineq.tolist(),cost=self.cost,model_ticks=self.counter[0]),True)
   return value
  opt=None;cap=None
  try:
   opt=minimize(lambda z:(-1 if direction=='max' else 1)*z[0],z0,method='SLSQP',bounds=list(zip(low,high)),constraints=[dict(type='eq',fun=lambda z:evaluate(z)['eq']),dict(type='ineq',fun=lambda z:evaluate(z)['ineq'])],options=dict(maxiter=60,ftol=1e-10,eps=1e-7,disp=False))
   evaluate(opt.x)
  except ValueError as e:
   if str(e)!='UNIQUE_PERIODIC_EVALUATION_CAP':raise
   cap=str(e)
  finally:log.close()
  result=dict(label=label,direction=direction,solver_success=bool(opt.success) if opt is not None else False,solver_status=int(opt.status) if opt is not None else None,solver_message=str(opt.message) if opt is not None else cap,nit=int(opt.nit) if opt is not None else None,unique_evaluations=len(cache),feasible_iterate_found=best is not None,admitted=False,speed=None,mechanical_periodic=False,validation_safe=False,first_failure='NO_FEASIBLE_ITERATE' if best is None else None)
  initial=None;action=None
  if best is not None:
   z=best['z'];_,x=self.state(template,branch,z);action=np.array([-x[1],x[2],0.],np.float32);x[1]=-float(action[0]);x[2]=float(action[1]);v=best['speed'];initial=self.fixture(template,dict(branch,speed=v),x)
   final,independent,_=self.rollout(initial,[action]);diff=difference(final,initial);mech=max(d['normalized_max'] for d in diff.values())<=1
   safe=False;rows=[]
   if mech:_,rows,safe=self.rollout(initial,[action],True,v)
   result.update(speed=v,x=x.tolist(),branch=dict(branch,speed=v),admitted=mech and safe,mechanical_periodic=mech,validation_safe=safe,first_failure=next((r['reason'] for r in rows if not r['accepted']),None) if mech else 'FULLSTATE_PERIOD_RESIDUAL',signature_difference=diff,selected_scaled_period_residual=float(max(abs(best['eq']))),selected_min_inequality=float(min(best['ineq'])),initial_root_without_roads=short(initial),terminal_root_without_roads=short(final),action=action.tolist(),independent_rows=independent,rows=rows)
  save(D/f'{label}-period-private.json',result);self.results.append(result);return result,initial,action
 def transition(self,source,source_root):
  i=(source['branch']['station']+1)%len(self.branches);branch=self.branches[i];seed=dict(speed=source['speed'],x=source['x'])
  target,target_root,target_action=self.solve('transition-target',source_root,branch,seed,'max',source['speed'])
  if not target['admitted']:return dict(executed=False,reason='TARGET_SAFE_PERIODIC_GATE_FAILED')
  self.current=dict(phase='constrained_transition');target_sig=signature(target_root);I=target_root.planar.inertia;cache={};best=None
  tol=dict(velocity=.15,yaw=.05,angular_momentum=I*.05,joints=.02,rates=.15,omega=.5,gas=.02,headings=.02,offsets=.15,levers=1e-6,friction=1e-8,steer=.02,constants=1e-10)
  def errors(root):
   sig=signature(root);z=[];by={}
   for k in sig:
    d=np.array(sig[k]['value'])-target_sig[k]['value']
    if k in ('joints','headings'):d=np.arctan2(np.sin(d),np.cos(d))
    by[k]=float(max(abs(d))/tol[k]);z.extend(d/tol[k])
   return np.array(z),by
  def actions(z,quant=False):return [np.array([-z[2*j],max(0.,z[2*j+1]),max(0.,-z[2*j+1])],np.float32 if quant else float) for j in range(4)]
  log=(D/'transition-solver-private.jsonl').open('x');(D/'transition-solver-private.jsonl').chmod(0o600)
  def evaluate(z):
   nonlocal best
   self.guard();key=np.array(z,np.float64).tobytes()
   if key in cache:return cache[key]
   if len(cache)>=1000:raise ValueError('UNIQUE_TRANSITION_ROLLOUT_CAP')
   final,rows,_=self.rollout(source_root,actions(z));e,by=errors(final);ineq=self.constraints_from_rows(rows);ineq=np.r_[ineq,*[(target['speed']+4.85-math.hypot(*r['root_without_roads']['planar']['linear']['velocity']))/100 for r in rows]]
   obj=float(e@e);v=dict(z=np.array(z).copy(),objective=obj,errors=by,ineq=ineq,feasible=min(ineq)>=-1e-8);cache[key]=v;self.cost['transition_unique_evaluations']+=1
   if v['feasible'] and (best is None or obj<best['objective']):best=v
   log.write(json.dumps(dict(call=len(cache),z=list(map(float,z)),objective=obj,errors=by,min_inequality=float(min(ineq)),feasible=bool(v['feasible']),model_ticks=self.counter[0]))+'\n');log.flush()
   save(D/'latest-checkpoint-private.json',dict(current=self.current,z=list(map(float,z)),terminal=short(final),errors=by,ineq=ineq.tolist(),cost=self.cost,model_ticks=self.counter[0]),True);return v
  z0=np.array([s for t in (.25,.5,.75,1.) for s in ((1-t)*(-source['action'][0])+t*(-target_action[0]),(1-t)*source['action'][1]+t*target_action[1])]);opt=None;cap=None
  try:
   opt=minimize(lambda z:evaluate(z)['objective'],z0,method='SLSQP',bounds=list(zip(np.tile([-.4,-1.],4),np.tile([.4,1.],4))),constraints=[dict(type='ineq',fun=lambda z:evaluate(z)['ineq'])],options=dict(maxiter=60,ftol=1e-10,eps=1e-7,disp=False));evaluate(opt.x)
  except ValueError as e:
   if str(e)!='UNIQUE_TRANSITION_ROLLOUT_CAP':raise
   cap=str(e)
  finally:log.close()
  result=dict(executed=True,unique_evaluations=len(cache),solver_success=bool(opt.success) if opt is not None else False,solver_status=int(opt.status) if opt is not None else None,solver_message=str(opt.message) if opt is not None else cap,nit=int(opt.nit) if opt is not None else None,feasible_iterate_found=best is not None,passed=False,endpoint_match=False,follow_executed=False)
  if best is not None:
   aa=actions(best['z'],True);final,rows,safe=self.rollout(source_root,aa,True,target['speed']);_,by=errors(final);match=safe and max(by.values())<=1;follow=[];fsafe=False;endby=None
   if match:end,follow,fsafe=self.rollout(final,[target_action]*3,True,target['speed']);_,endby=errors(end)
   result.update(endpoint_safe=safe,endpoint_match=match,endpoint_normalized_errors=by,first_failure=next((r['reason'] for r in rows if not r['accepted']),None),follow_executed=bool(follow),follow_safe=fsafe,follow_end_normalized_errors=endby,passed=bool(match and fsafe and max(endby.values())<=1) if endby else False,actions=[a.tolist() for a in aa],rows=rows,follow_rows=follow,terminal_root_without_roads=short(final))
  save(D/'transition-private.json',result);return result
 def run(self):
  out={};cycles=[];maxima=[]
  try:
   for n,old in enumerate(self.previous):
    template=engine.load_root(dict(old['initial_root_without_roads'],roads=self.static['root']['roads']));branch=old['branch'];x=np.array(old['x']);x[3:]*=.9;seed=dict(speed=.9*branch['speed'],x=x.tolist())
    maximum,root,action=self.solve(f'fixture{n}-max',template,branch,seed,'max');maxima.append((maximum,root,action))
    if maximum['feasible_iterate_found']:self.solve(f'fixture{n}-min',template,branch,dict(speed=maximum['speed'],x=maximum['x']),'min')
   for result,root,action in maxima:
    if result['admitted']:
     cycles.append(self.cycles(result['label']+'-exact',root,action,result['speed']));cycles.append(self.cycles(result['label']+'-perturbed',root,action,result['speed'],True))
   if len(maxima)==2 and all(z['admitted'] for z,_,_ in maxima):self.transition_result=self.transition(maxima[0][0],maxima[0][1])
   else:self.transition_result=dict(executed=False,reason='ORIGINAL_SAFE_PERIODIC_GATE_FAILED')
   out=dict(completed=True)
  except BaseException as e:
   out=dict(completed=False,error=type(e).__name__+':'+str(e));save(D/'failure-private.json',dict(error=out['error'],traceback=traceback.format_exc(),current=self.current,cost=self.cost,model_ticks=self.counter[0]))
  finally:
   signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
   excluded={'x','branch','initial_root_without_roads','terminal_root_without_roads','action','rows','independent_rows'}
   out.update(periodic_states=[{k:v for k,v in r.items() if k not in excluded} for r in self.results],cycles=[{k:v for k,v in r.items() if k not in {'rows','initial_root_without_roads','terminal_root_without_roads'}} for r in cycles],transition={k:v for k,v in (self.transition_result or {}).items() if k not in {'rows','follow_rows','actions','terminal_root_without_roads'}},cost=dict(self.cost,model_ticks=self.counter[0],internal_wheel_force_evaluations=4*self.counter[0],CPU_s=time.process_time()-self.cpu,wall_s=time.perf_counter()-self.wall),new_native_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT_queries=0,SEALED_queries=0,research_remaining=22758,reserve=84000,reserve_used=0,actual_baseline_s=13.66,no_lap_gain_observation=True)
   save(G/'retry/safeperiod557_result.json',out);print(json.dumps(out,indent=2))

if __name__=='__main__':Study().run()
