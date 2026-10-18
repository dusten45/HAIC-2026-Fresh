"""Two bounded local models of a12-coefficient full-window coordinated control law."""
import bisect,hashlib,json,math,time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize,Bounds,LinearConstraint
from retry.shoot545_problem import Problem as OriginalProblem,metrics
from retry.coord546_return_control import FOOTPRINT_ADMISSION


class Problem(OriginalProblem):
 def __init__(self,st,data,baseline):
  super().__init__(st,data,baseline);self.D=Path('/workspace/haic-response546-private');t=(np.arange(32)+.5)/32;self.B=np.stack([math.comb(5,j)*t**j*(1-t)**(5-j) for j in range(6)],axis=1);assert np.allclose(self.B.sum(axis=1),1.) and np.linalg.matrix_rank(self.B)==6;self.u32=np.where(self.base_actions[:,1]>0,self.base_actions[:,1],-self.base_actions[:,2]).astype(float);self.cross_baseline=st.c['baseline_metrics']['crossing'];self.local_models=[]
 def controls(self,x):
  a=self.base_actions.copy();a[:,0]=np.array(self.base_actions[:,0]+.4*self.B@x[:6],np.float32);u=np.array(self.u32+self.B@x[6:],np.float32);a[:,1]=np.maximum(u,0.);a[:,2]=np.maximum(-u,0.);return a
 def evaluate(self,x,fresh=False,keep=False,feedback=False):
  assert not feedback;x=np.asarray(x,dtype=float);key=x.tobytes()
  if not fresh and key in self.cache:return self.cache[key]
  if self.calls>=64:raise RuntimeError('CORE64_FULLWINDOW_CAP')
  value=super().evaluate(x,fresh=True,keep=True);g=value['g'].copy();g[1:1024:8]-=FOOTPRINT_ADMISSION-.5;steer=self.base_actions[:,0].astype(float)+.4*self.B@x[:6];u=self.u32+self.B@x[6:];g=np.r_[g,float(np.float32(.4))-steer,float(np.float32(.4))+steer,1-u,1+u];summary=value['summary'];summary['physical_safe']=bool(summary['physical_safe'] and summary['min_margin_m']>=FOOTPRINT_ADMISSION);summary['feasible']=bool(summary['physical_safe'] and summary['crossing'] and g.min()>=-1e-10);summary['minimum_constraint']=float(g.min());value['g']=g;self.cache[key]=value
  contacts=[r['root_without_roads']['current_contacts'] for r in value['trace']];friction=[[w['friction'] for w in r['root_without_roads']['planar']['linear']['wheels']] for r in value['trace']];clips=[[z['clipped'] for z in r['forces']] for r in value['trace']];projections=[bisect.bisect_left(self.path['arcs'][1:],r['progress']) for r in value['trace']];signature=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest();value['signatures']={k:signature(v) for k,v in dict(contact_ids=contacts,effective_friction=friction,clip_pattern=clips,projection_segment=projections).items()};self.st.cost['core_rollouts']=self.calls;self.st.cost['core_raw_ticks']=self.st.cost.get('core_raw_ticks',0)+len(value['trace'])
  self.st.save(self.D/f'unified-{self.calls:03d}-private.json',dict(decision=x.tolist(),summary=summary,signatures=value['signatures'],core_raw_ticks=self.st.cost['core_raw_ticks'],model_ticks=self.st.counter[0]));return value
 def validate_direction(self,base,J,gradient,d,model_index):
  records=[];reliable=True
  for alpha in (.25,.5):
   x=np.asarray(base['decision'])+alpha*d;v=self.evaluate(x);pred_time=base['value']['objective']+alpha*gradient@d;predg=base['value']['g']+alpha*J@d;err=v['g']-predg;raw=err[:1024].reshape(128,8);timeerr=abs(v['objective']-pred_time);expected_gain=base['value']['objective']-pred_time;force_error=float(max(abs(raw[:,0])));geometry_error=float(max(abs(raw[:,1])));rest=float(max(abs(err[1024:])));ok=bool(timeerr<=max(.0001,.25*abs(expected_gain)) and force_error<=.001 and geometry_error<=.002 and max(abs(raw[:,2]))*5<=.15 and max(abs(raw[:,3]))*3<=.10 and max(abs(raw[:,4]))*100<=.15 and rest<=.02 and (expected_gain<.0001 or v['objective']<=base['value']['objective']))
   records.append(dict(step_fraction=alpha,predicted_time_s=float(pred_time),actual_time_s=v['objective'],time_prediction_error_s=timeerr,force_linearization_error=force_error,footprint_linearization_error_m=geometry_error,remaining_normalized_constraint_error=rest,feasible=v['summary']['feasible'],reliable=ok,signature_changes={k:base['value']['signatures'][k]!=v['signatures'][k] for k in v['signatures']}));reliable &= ok
  self.st.save(self.D/f'direction-check-{model_index}-private.json',records);return reliable,records


def run_probe(st):
 D=Path('/workspace/haic-response546-private');data=json.loads((D/'entry-private.json').read_text());saved=json.loads((D/'fresh-feasible541-baseline-private.json').read_text());p=Problem(st,data,saved);x=np.zeros(12);base=p.evaluate(x);assert base['summary']['feasible'];assert json.dumps([r['root_without_roads'] for r in base['trace']],sort_keys=True)==json.dumps([r['root_without_roads'] for r in saved['trace']],sort_keys=True);st.save(D/'warmstart-private.json',dict(summary=base['summary'],trace=base['trace'],commands=base['commands'],canonical_replay_exact=True));initial=base;models=[];reason='TWO_LOCAL_MODELS_COMPLETED';eps=1e-4
 for model_index in range(2):
  st.guard();gradient=np.zeros(12);J=np.zeros((len(base['g']),12));fd=[]
  for j in range(12):
   sign=1. if j<6 else -1.;z=x.copy();z[j]+=sign*eps;v=p.evaluate(z);gradient[j]=(v['objective']-base['objective'])/(sign*eps);J[:,j]=(v['g']-base['g'])/(sign*eps);fd.append(dict(column=j,sign=sign,signature_changes={k:base['signatures'][k]!=v['signatures'][k] for k in v['signatures']}))
  qp=minimize(lambda d:float(gradient@d+.5*d@d),np.zeros(12),jac=lambda d:gradient+d,method='SLSQP',bounds=Bounds(np.full(12,-.05),np.full(12,.05)),constraints=[LinearConstraint(J,-base['g'],np.full(len(base['g']),np.inf))],options=dict(maxiter=80,ftol=1e-10,disp=False));d=np.asarray(qp.x);predicted=float(-gradient@d);record=dict(model=model_index+1,QP_success=bool(qp.success),QP_status=int(qp.status),QP_iterations=int(qp.nit),predicted_full_step_time_gain_s=predicted,linear_constraint_minimum=float(min(base['g']+J@d)),direction_norm_inf=float(max(abs(d))),finite_difference=fd)
  st.save(D/f'local-model-{model_index}-private.json',dict(record=record,center=x.tolist(),direction=d.tolist(),gradient=gradient.tolist(),J=J.tolist()))
  if not qp.success or record['linear_constraint_minimum']< -1e-8:reason='LOCAL_QP_NUMERICAL_FAILURE';models.append(record);break
  if predicted<.0001 or max(abs(d))<1e-8:reason='NO_USEFUL_PREDICTED_DESCENT_IN_BASIS_TRUST_REGION';models.append(record);break
  reliable,checks=p.validate_direction(dict(decision=x.tolist(),value=base),J,gradient,d,model_index);record['direction_checks']=checks;record['direction_prediction_reliable']=bool(reliable)
  if not reliable:reason='DIRECTION_MODEL_PREDICTION_INACCURATE';models.append(record);break
  accepted=False;steps=[]
  for alpha in (1.,.5,.25,.125):
   z=x+alpha*d;v=p.evaluate(z);ok=bool(v['summary']['feasible'] and v['objective']<=base['objective']-1e-6);steps.append(dict(step_fraction=alpha,actual_time_gain_s=base['objective']-v['objective'],feasible=v['summary']['feasible'],accepted=ok,min_margin_m=v['summary']['min_margin_m']))
   if ok:x=z;base=v;accepted=True;break
  record['backtracking']=steps;record['feasible_update_accepted']=accepted;models.append(record);st.save(D/'accepted-progress-private.json',dict(decision=x.tolist(),summary=base['summary'],models=models),True)
  if not accepted:reason='NO_FEASIBLE_IMPROVING_BACKTRACKING_STEP';break
 final=p.evaluate(x,fresh=True);assert final['summary']['feasible'];st.save(D/'selected-fresh-witness-private.json',dict(decision=x.tolist(),summary=final['summary'],trace=final['trace'],commands=final['commands']));gain=initial['objective']-final['objective'];learning=bool(gain>=.005);validation=None;performance=False
 if learning:
  returns=[]
  for label,trial in [('baseline',initial),('candidate',final)]:
   history=(data['history'][0]+sum(z['clipped'] for r in trial['trace'] for z in r['forces']),data['history'][1]+512);root=st.root(trial['trace'][-1]['root_without_roads']);case=st.simulate('feedback-return-'+label,root,86,history,set(),False,12);returns.append(case)
   if not case['pass_safety']:break
  if len(returns)==2 and all(z['pass_safety'] for z in returns):
   a=json.loads((D/'feedback-return-baseline-private.json').read_text())['trace'][-1];b=json.loads((D/'feedback-return-candidate-private.json').read_text())['trace'][-1];ma=metrics(st.root(a['root_without_roads']),p.path,a['progress']);mb=metrics(st.root(b['root_without_roads']),p.path,b['progress']);terminal=bool(mb['path_error']<=ma['path_error']+.10 and mb['heading_error']<=ma['heading_error']+.02 and mb['yaw_error']<=ma['yaw_error']+.05 and mb['speed_deficit']<=ma['speed_deficit']+.15);validation=dict(passed=terminal,cases=returns,terminal_baseline=ma,terminal_candidate=mb)
  else:validation=dict(passed=False,cases=returns)
  performance=bool(validation['passed'] and initial['summary']['crossing']['lower_s']-final['summary']['crossing']['upper_s']>=.02-1e-12)
 return dict(passed=performance,learning_gate=learning,promotion_eligible=False,reason=reason,feasible_initialization=True,canonical_replay_exact=True,unified_floor_m=FOOTPRINT_ADMISSION,basis_coefficients=12,basis_covers_all32holds=True,local_models=models,initial=initial['summary'],selected=final['summary'],interpolated_time_gain_s=gain,core_rollouts=p.calls,core_raw_ticks=st.cost['core_raw_ticks'],feedback_return_validation=validation,feedback_return_not_run=not learning,interpretation='Two-local-model finite feasible method. Unreliable prediction, no feasible/useful direction, and local effect are separate outcomes; no wholelap/native/optimality claim.')
