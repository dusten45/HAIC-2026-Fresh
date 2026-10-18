"""Feasible sequential-linear trust regions; inactive model error is diagnostic only."""
import json,math,time,bisect,hashlib
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
from retry.risk548_boundary import near_risk,reserve_for
from retry.coord546_problem import Problem as OriginalProblem,metrics,FOOTPRINT_ADMISSION


def scales():
 bands=np.r_[np.tile([.01,.02,.03,.10/3,.15/100,.1,.02,.02],128),[.10,.02,.05,.15,.1,.015,.02,.05],np.full(128,.01)]
 tolerances=np.r_[np.tile([.001,.002,.15/5,.10/3,.15/100,0.,.02,.02],128),[.10,.02,.05,.15,.01,.015,.02,.05],np.full(128,1e-9)]
 assert len(bands)==len(tolerances)==1160
 return bands,tolerances


def risk_check(g0,predicted,actual):
 bands,tau=scales();risk=near_risk(g0,bands)|near_risk(predicted,bands)|near_risk(actual,bands);optimism=predicted-actual;allowed=np.minimum(tau,np.maximum(1e-9,.5*np.maximum(predicted,0.)));bad=risk&(optimism>allowed+1e-12);rawrisk=risk[:1024].reshape(128,8);rawerr=optimism[:1024].reshape(128,8);geom=risk[:1024].reshape(128,8)[:,1]
 return dict(passed=not bool(bad.any()),risky_constraints=int(risk.sum()),violating_risky_predictions=int(bad.sum()),unexpectedly_near_risk=int(((~near_risk(g0,bands))&(~near_risk(predicted,bands))&near_risk(actual,bands)).sum()),max_risky_geometry_optimism_m=float(max(np.maximum(rawerr[:,1][geom],0),default=0.)),max_inactive_geometry_absolute_error_m=float(max(abs(rawerr[:,1][~geom]),default=0.)),active_geometry_samples=int(geom.sum()),bad_constraint_indices=np.where(bad)[0].tolist())


class Problem(OriginalProblem):
 def __init__(self,st,data,baseline):
  super().__init__(st,data,baseline);self.D=Path('/workspace/haic-response548-private');self.reuse_hits=[];manifest=json.loads((self.D/'reuse-manifest-private.json').read_text());self.reuse_sources={};sourcehash=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
  for rec in manifest['prior_pointwise']:
   assert sourcehash(rec['path'])==rec['sha256'];q=json.loads(Path(rec['path']).read_text());key=np.asarray(q['decision'],dtype=float).tobytes();sign=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest();branch=q['branch'];projection=[bisect.bisect_left(self.path['arcs'][1:],r['progress']) for r in q['trace']];signatures={k:sign(v) for k,v in dict(contact_ids=branch['contact_ids'],effective_friction=branch['effective_friction'],clip_pattern=branch['clip_pattern'],projection_segment=projection).items()};self.cache[key]=dict(objective=q['summary']['objective_s'],g=np.array(q['g']),summary=q['summary'],trace=q['trace'],commands=q['commands'],signatures=signatures);self.reuse_sources[key]=rec
  self.calls=st.c['prior_547']['core_rollouts'];prior=manifest['prior_first_model'];assert sourcehash(prior['path'])==prior['sha256'];self.prior_model=json.loads(Path(prior['path']).read_text());zero=np.zeros(12);dold=np.array(json.loads((self.D/'prior546-local-model-private.json').read_text())['direction']);needed=[zero,.25*dold,.5*dold]
  for j in range(12):
   z=zero.copy();z[j]+=(1. if j<6 else -1.)*1e-4;needed.append(z)
  assert all(np.asarray(z,dtype=float).tobytes() in self.cache for z in needed)
  st.save(self.D/'cache-import-private.json',dict(verified_records=len(manifest['prior_pointwise']),unique_decisions=len(self.cache),guaranteed_initial_and_FD_cache_queries=len(needed),precharged_rollouts=self.calls,precharged_model_ticks=st.counter[0]))
 def evaluate(self,x,fresh=False,keep=False,feedback=False):
  previous=self.calls;key=np.asarray(x,dtype=float).tobytes()
  if not fresh and key in self.reuse_sources:
   self.reuse_hits.append(dict(path=self.reuse_sources[key]['path'],sha256=self.reuse_sources[key]['sha256']));self.st.save(self.D/'cache-hit-log-private.json',self.reuse_hits,True)
  value=super().evaluate(x,fresh=fresh,keep=keep,feedback=feedback)
  if self.calls!=previous:
   branch=dict(contact_ids=[z['root_without_roads']['current_contacts'] for z in value['trace']],effective_friction=[[w['friction'] for w in z['root_without_roads']['planar']['linear']['wheels']] for z in value['trace']],clip_pattern=[[w['clipped'] for w in z['forces']] for z in value['trace']])
   self.st.save(self.D/f'pointwise-{self.calls:03d}-private.json',dict(decision=np.asarray(x).tolist(),g=value['g'].tolist(),summary=value['summary'],branch=branch,trace=value['trace'],commands=value['commands']))
  return value


def run_probe(st):
 D=Path('/workspace/haic-response548-private');read=lambda p:json.loads(p.read_text());data=read(D/'entry-private.json');saved=read(D/'fresh-feasible541-baseline-private.json');p=Problem(st,data,saved);x=np.zeros(12);base=p.evaluate(x);initial=base;assert base['summary']['feasible'];assert json.dumps([z['root_without_roads'] for z in base['trace']],sort_keys=True)==json.dumps([z['root_without_roads'] for z in saved['trace']],sort_keys=True);st.save(D/'warmstart-private.json',dict(summary=base['summary'],trace=base['trace'],commands=base['commands'],canonical_replay_exact=True))
 prior=read(D/'prior546-local-model-private.json');Jold=np.array(prior['J']);dold=np.array(prior['direction']);reconstruction=[]
 for alpha,index in ((.25,14),(.5,15)):
  v=p.evaluate(alpha*dold);old=read(Path('/workspace/haic-response546-private')/f'unified-{index:03d}-private.json');assert v['signatures']==old['signatures'];assert v['summary']['objective_s']==old['summary']['objective_s'] and v['summary']['min_margin_m']==old['summary']['min_margin_m'];predg=initial['g']+alpha*Jold@dold;predgain=float(-alpha*np.array(prior['gradient'])@dold);actualgain=initial['objective']-v['objective'];reconstruction.append(dict(step_fraction=alpha,exact_previous_summary_and_signature_reconstruction=True,actual_gain_s=actualgain,predicted_gain_s=predgain,rho=actualgain/predgain,risk=risk_check(initial['g'],predg,v['g']),branch_changes={k:initial['signatures'][k]!=v['signatures'][k] for k in v['signatures']}))
 st.save(D/'prior546-pointwise-reconstruction-private.json',reconstruction);models=[];radius=.05;reason='LOCAL_MODEL_LIMIT';accepted_count=0;eps=1e-4;bands,_=scales();rejections=dict(exact_constraint=0,model_reliability=0,objective=0,numerical=0)
 for model_index in range(3):
  gradient=np.zeros(12);J=np.zeros((len(base['g']),12))
  for j in range(12):
   sign=1. if j<6 else -1.;z=x.copy();z[j]+=sign*eps;v=p.evaluate(z);gradient[j]=(v['objective']-base['objective'])/(sign*eps);J[:,j]=(v['g']-base['g'])/(sign*eps)
  # Action-bound constraints are exactly affine in the coefficients.
  J[1032:,:]=0.;J[1032:1064,:6]=-.4*p.B;J[1064:1096,:6]=.4*p.B;J[1096:1128,6:]=-p.B;J[1128:1160,6:]=p.B
  if model_index==0:
   assert p.calls==st.c['prior_547']['core_rollouts'];assert np.array_equal(gradient.view(np.uint64),np.array(p.prior_model['gradient']).view(np.uint64));assert np.array_equal(J.view(np.uint64),np.array(p.prior_model['J']).view(np.uint64));assert np.array_equal(base['g'].view(np.uint64),np.array(p.prior_model['g0']).view(np.uint64));st.save(D/'first-J-exact-reuse-private.json',dict(gradient_bit_exact=True,J_bit_exact=True,g0_bit_exact=True,new_source_ticks_for_initial_and_differences=0,cache_hits=len(p.reuse_hits)))
  model=dict(index=model_index+1,center_time_s=base['objective'],radius_initial=radius,trials=[]);st.save(D/f'local-model-{model_index}-private.json',dict(center=x.tolist(),gradient=gradient.tolist(),J=J.tolist(),g0=base['g'].tolist(),risk_band=bands.tolist()));accepted=False
  for attempt in range(4):
   reserve=reserve_for(base['g'],bands);lp=linprog(gradient,A_ub=-J,b_ub=base['g']-reserve,bounds=[(-radius,radius)]*12,method='highs',options=dict(time_limit=5.,primal_feasibility_tolerance=1e-9,dual_feasibility_tolerance=1e-9));trial=dict(attempt=attempt+1,radius=radius,LP_success=bool(lp.success),LP_status=int(lp.status))
   if not lp.success:trial['classification']='LOCAL_LP_NUMERICAL_FAILURE';rejections['numerical']+=1;model['trials'].append(trial);reason='LOCAL_LP_NUMERICAL_FAILURE';break
   d=np.asarray(lp.x);predicted_gain=float(-gradient@d);trial.update(predicted_gain_s=predicted_gain,direction_norm_inf=float(max(abs(d))),linear_reserved_constraint_minimum=float(min(base['g']+J@d-reserve)))
   if predicted_gain<=1e-6 or max(abs(d))<1e-8:trial['classification']='NO_MEANINGFUL_PREDICTED_DESCENT';rejections['objective']+=1;model['trials'].append(trial);reason='NO_MEANINGFUL_PREDICTED_DESCENT';break
   v=p.evaluate(x+d);actual_gain=base['objective']-v['objective'];rho=actual_gain/predicted_gain;predg=base['g']+J@d;risk=risk_check(base['g'],predg,v['g']);ok=bool(v['summary']['feasible'] and actual_gain>=1e-6 and rho>=.1 and risk['passed']);trial.update(actual_gain_s=actual_gain,rho=rho,exact_feasible=v['summary']['feasible'],exact_min_margin_m=v['summary']['min_margin_m'],risk=risk,branch_changes={k:base['signatures'][k]!=v['signatures'][k] for k in v['signatures']},accepted=ok)
   if ok:
    x=x+d;base=v;accepted=True;accepted_count+=1;trial['classification']='FEASIBLE_OBJECTIVE_DECREASE'
    if rho>=.75 and max(abs(d))>=.8*radius:radius=min(.05,2*radius)
    elif rho<.25:radius=.5*radius
    model['trials'].append(trial);st.save(D/'accepted-progress-private.json',dict(decision=x.tolist(),summary=base['summary'],accepted_updates=accepted_count),True);break
   if not v['summary']['feasible']:category='exact_constraint';trial['classification']='EXACT_NONLINEAR_CONSTRAINT_REJECTION'
   elif actual_gain<1e-6:category='objective';trial['classification']='INSUFFICIENT_ACTUAL_DECREASE'
   else:category='model_reliability';trial['classification']='REDUCTION_RATIO_OR_RISK_PREDICTION_REJECTION'
   rejections[category]+=1;radius=.5*min(radius,float(max(abs(d))));trial['radius_after_rejection']=radius;model['trials'].append(trial)
   if radius<1e-4:reason='RADIUS_BELOW_FINITE_DIFFERENCE_SCALE';break
  model['accepted_update']=accepted;model['radius_final']=radius;models.append(model);st.save(D/'progress-models-private.json',models,True)
  if not accepted:
   if reason=='LOCAL_MODEL_LIMIT':reason='NO_ADMISSIBLE_TRUST_STEP_IN_FINITE_ATTEMPTS'
   break
  if initial['objective']-base['objective']>=.005:reason='LEARNING_GAIN_REACHED';break
 final=p.evaluate(x,fresh=True);assert final['summary']['feasible'];st.save(D/'selected-fresh-witness-private.json',dict(decision=x.tolist(),summary=final['summary'],trace=final['trace'],commands=final['commands']));gain=initial['objective']-final['objective'];learning=bool(gain>=.005);validation=None;performance=False
 if learning:
  returns=[]
  for label,trial in [('baseline',initial),('candidate',final)]:
   history=(data['history'][0]+sum(z['clipped'] for r in trial['trace'] for z in r['forces']),data['history'][1]+512);root=st.root(trial['trace'][-1]['root_without_roads']);case=st.simulate('feedback-return-'+label,root,86,history,set(),False,12);returns.append(case)
   if not case['pass_safety']:break
  if len(returns)==2 and all(z['pass_safety'] for z in returns):
   a=read(D/'feedback-return-baseline-private.json')['trace'][-1];b=read(D/'feedback-return-candidate-private.json')['trace'][-1];ma=metrics(st.root(a['root_without_roads']),p.path,a['progress']);mb=metrics(st.root(b['root_without_roads']),p.path,b['progress']);terminal=bool(mb['path_error']<=ma['path_error']+.10 and mb['heading_error']<=ma['heading_error']+.02 and mb['yaw_error']<=ma['yaw_error']+.05 and mb['speed_deficit']<=ma['speed_deficit']+.15);validation=dict(passed=terminal,cases=returns,terminal_baseline=ma,terminal_candidate=mb)
  else:validation=dict(passed=False,cases=returns)
  performance=bool(validation['passed'] and initial['summary']['crossing']['lower_s']-final['summary']['crossing']['upper_s']>=.02-1e-12)
 return dict(boundary_defect_repaired=True,prior547preserved=True,cache_hits=len(p.reuse_hits),first_model_inputs_and_J_bit_exact_reuse=True,prior_core_rollouts=st.c['prior_547']['core_rollouts'],new_core_rollouts=p.calls-st.c['prior_547']['core_rollouts'],passed=performance,learning_gate=learning,promotion_eligible=False,reason=reason,reconstruction_of_missing546_pointwise_data=reconstruction,accepted_feasible_updates=accepted_count,rejection_counts=rejections,unified_floor_m=FOOTPRINT_ADMISSION,basis_coefficients=12,initial=initial['summary'],selected=final['summary'],interpolated_time_gain_s=gain,local_models=models,core_rollouts=p.calls,core_raw_ticks=st.cost['core_raw_ticks'],feedback_return_validation=validation,feedback_return_not_run=not learning,interpretation='Separate feasible sequential-linear trust-region experiment. Exact all-constraint checks unchanged; inactive prediction error alone cannot reject. No retrospective546success, physicalbound, full-lap or nativeclaim.')
