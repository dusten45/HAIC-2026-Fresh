"""Exact feasible saved-source transcription, then ONE constrained time direction.

No periodicity condition. Hold nodes are checked independently, then condensed
state sensitivities are used for one finite LP direction and one source trial.
"""
import datetime,json,math,signal,time,traceback
from pathlib import Path
from dataclasses import asdict,replace
import numpy as np
from scipy.optimize import linprog
import retry.period556_model as engine

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response559-private');engine.D=D
save,rd,sha,short=engine.save,engine.rd,engine.sha,engine.short
INPUTS=[Path('/workspace/haic-response515-private/collected-map-state-private.json'),Path('/workspace/haic-response551-private/frozen-paths-private.json'),Path('/workspace/haic-response551-private/cold-candidate-private.json')]
SOURCES=['retry/transcribe559_model.py',*engine.SOURCES]
def canonical(x):return json.loads(json.dumps(x))
def vector(root):
 p=root.planar;w=p.linear.wheels
 groups=[('position',root.center,.1),('angle',[p.angle],.02),('velocity',p.linear.velocity,.15),('yaw',[p.yaw],.05),('momentum',[p.angular_momentum],p.inertia*.05),('joints',p.joints,.02),('rates',p.rates,.15),('omega',[q.omega for q in w],.5),('gas',[q.gas for q in w],.02),('headings',[q.heading for q in w],.02),('offsets',[v for q in w for v in q.offset],.15),('levers',[v for q in p.levers for v in q],.1),('friction',[q.friction for q in w],1e-8),('steer',[p.steer],.02),('constants',[p.linear.mass,p.linear.engine_multiplier,p.inertia,*p.wheel_inertias,p.steering_multiplier,root.floor,root.skin],1e-10)]
 return np.array([float(v) for _,a,_ in groups for v in a]),np.array([t for _,a,t in groups for _ in a]),[(name,len(a)) for name,a,_ in groups]

class Study(engine.Study):
 def __init__(self):
  D.mkdir(mode=0o700,exist_ok=False);self.static,self.paths,data=map(rd,INPUTS);self.path=self.paths['candidate'];trace=data['trace'];anchor=self.path['arcs'][37]
  at=next(j for j,r in enumerate(trace) if j and r['index']>24 and r['raw']==1 and trace[j-1]['progress']>=anchor)
  self.saved=trace[at:at+36];self.before=trace[at-1]['root_without_roads'];self.initial=engine.load_root(dict(self.before,roads=self.static['root']['roads']));self.history=[sum(f['clipped'] for r in trace[:at] if r['index']>24 for f in r['forces']),sum(4 for r in trace[:at] if r['index']>24)];self.progress=trace[at-1]['progress']
  self.base_actions=[np.array(self.saved[4*j]['action'],np.float32) for j in range(9)];self.x0=np.array([v for a in self.base_actions[:6] for v in [float(a[0]),float(a[1])-float(a[2])]])
  self.nodes=[self.before]+[r['root_without_roads'] for r in self.saved if r['raw']==4];self.gates=[]
  for k in (23,31):
   r=self.saved[k];p=r['root_without_roads'];vv=p['planar']['linear']['velocity'];speed=math.hypot(*vv);root=engine.load_root(dict(p,roads=self.static['root']['roads']));vec,tol,names=vector(root);self.gates.append(dict(point=p['center'],normal=[v/speed for v in vv],baseline_time=.02*(k+1),baseline_vector=vec,tolerance=tol,groups=names))
  save(D/'selected-segment-private.json',dict(entry_action=self.saved[0]['index'],selection='First551 before-action progress>=old533station37, action>24; six optimized holds, two follow, one fixed bracketing-buffer hold',history=self.history,initial=self.before,nodes=self.nodes,commands=[a.tolist() for a in self.base_actions],gates=[dict(g,baseline_vector=g['baseline_vector'].tolist(),tolerance=g['tolerance'].tolist()) for g in self.gates]))
  self.contract=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',hypothesis='First verify exact feasible world/fullstate source transcription on a reset-reachable saved551 segment, without periodicity. Only then inspect one constrained common-space arrival-time improvement direction.',selection='First551 tracking before-action progress>=existing533station37, no outcome selection; optimize first6holds, fixed next2follow, fixed ninth control ONLY as late-crossing measurement buffer. The same physical planes at saved6/8hold endpoints; no558 target or synthetic state.',transcription='For each of9 holds, independently source-propagate saved node+saved float32 action and compare ALL4raw fullroot excluding immutable roads, INCLUDING contacts/pose/gas/omega/joints and forces EXACTLY. Then sequential36raw replay must match every saved fullstate and force. Canonical tuple/list normalization only. Any mismatch stops before sensitivity/time study.',representation='Saved hold nodes with exact zero defects; source-condensed forward state sensitivities of12 controls. No periodicity condition, no arbitrary target state/time or world-frame quotient.',direction=dict(variables='First6holds x steering and signed pedal; final3controls fixed. One LP minimizing average arrival time to the two frozen physical planes. No basis/window/step sweep or repeated nonlinear solve.',finite_difference='12 one-sided source rollouts, steering step1e-5/pedal1e-4; direction chosen inside action bounds and SAME brake-lock/pedal branch; divide by actual float32 perturbation. Source geometry and all world state responses included.',trust_box='steering delta<=.002rad,pedal delta<=.02, existing +/-float32(.4) and[-1,1] and same pedal/lock branch. These are finite design choices, not physical necessity.',LP='Keep half the baseline slack in linearized constraints G*delta>=-.5*g0; constraints include all raw safety, no NEW clipped samples vs frozen baseline mask, two-sided world/fullstate gate-state comparison tolerances, and both plane arrival times nonworsening. ZERO delta must be feasible. One scipy HiGHS linprog; select full solution as ONE candidate, no backtracking.',candidate_gate='All real source raw safety; primary+follow interpolated gains each>=5ms and full gate comparison tolerances. Report raw crossing brackets and interpolation convention; no native or full-lap gain inference. Even effect failure retains transcription evidence.'),safety='source footprint>=.50,path<=3,ORIGINAL551reference overspeed<=4.85,preclip force<=1.059,hull/allwheel<100,cumulative clipping<=10% INCLUDING true saved tracking history. No-new-clip LP mask is conservative design only. All trial model body hard100. Unsafe finite-difference/trial forecasts counted, never actual execution.',gate_measurement='First forward plane crossing within36raw, signed plane interpolation defines model time. Interpolate numeric world state solely as a comparison metric between raw states; it is NOT a physically reachable intermediate source state. Record exact raw brackets and preserve ALL actual raw safety. World position tolerance components.1m plus Euclidean<=.15,angle.02,velocity components.15,yaw.05,M=I*.05,omega.5,gas/joints.02,rates.15,heading.02,offset.15,lever.1; unchanged friction/constants. Contact IDs compared exactly for transcription, logged separately for changed trajectory.',caps=dict(model_ticks=800,explicit_wheel_force_evaluations=4000,geometry_checks=700,CPU_s=90,wall_s=120,node_replays=9,FD_rollouts=12,LP_solves=1,candidate_rollouts=1),stop='Mismatch -> no time experiment. FD crossing not bracketed/LP failure -> stop classification, no alternate direction. Candidate failure -> stop with full record, no smaller step/other controls. Deadline/domain/cost -> checkpoint and no rerun.',actual_cap=0,new_seed_HOLDOUT_SEALED_other_environment_paid=0,research_remaining=22758,reserve=84000,reserve_used=0,source_sha256={p:sha(G/p) for p in SOURCES},private_inputs_sha256={str(p):sha(p) for p in INPUTS},segment_sha256=sha(D/'selected-segment-private.json'))
  save(G/'retry/transcribe559_contract.json',self.contract);save(D/'STARTED.json',dict(contract_sha256=sha(G/'retry/transcribe559_contract.json')))
  self.cpu,self.wall=time.process_time(),time.perf_counter();self.counter=[0];self.index=engine.bounds(self.initial.roads);self.edge=engine.boundary_index(self.static['boundary']);self.cost=dict(explicit_wheel_force_evaluations=0,geometry_checks=0,body_checks=0,residual_calls=0,unsafe_forecast_raw=0,max_forecast_force=0.,max_body_speed=0.,node_ticks=0,FD_rollouts=0,candidate_rollouts=0);self.current='transcription'
  signal.signal(signal.SIGPROF,self.guard);signal.setitimer(signal.ITIMER_PROF,90);signal.signal(signal.SIGALRM,self.guard);signal.setitimer(signal.ITIMER_REAL,120)
 def guard(self,*_):
  if self.counter[0]>=800 or self.cost['explicit_wheel_force_evaluations']+4>4000 or self.cost['geometry_checks']>=700:raise RuntimeError('WORK_CAP')
  if time.process_time()-self.cpu>=90 or time.perf_counter()-self.wall>=120:raise RuntimeError('TIME_CAP')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.contract['deadline_utc']):raise RuntimeError('DEADLINE')
 def actions(self,x):return [np.array([x[2*j],max(0.,x[2*j+1]),max(0.,-x[2*j+1])],np.float32) for j in range(6)]+self.base_actions[6:]
 def simulate(self,x):
  root=self.initial;states=[root];rows=[]
  for action in self.actions(x):
   for _ in range(4):root,row=self.raw(root,action);states.append(root);rows.append(row)
  return states,rows
 def crossings(self,states):
  out=[]
  for gate in self.gates:
   signed=[sum((s.center[j]-gate['point'][j])*gate['normal'][j] for j in range(2)) for s in states];found=None
   for k in range(1,len(states)):
    if signed[k-1]<0<=signed[k]:
     f=-signed[k-1]/(signed[k]-signed[k-1]);a,tol,names=vector(states[k-1]);b,_,_=vector(states[k]);value=a+f*(b-a);found=dict(time=.02*(k-1+f),raw_bracket=[.02*(k-1),.02*k],fraction=f,raw_index=k,vector=value,tolerance=tol,groups=names,bracket_contact_ids=[states[k-1].current_contacts,states[k].current_contacts]);break
   if found is None:raise RuntimeError('PLANE_NOT_BRACKETED_IN_FIXED_BUFFER')
   out.append(found)
  return out
 def evaluate(self,x,label):
  self.current=label;states,rows=self.simulate(x);cross=self.crossings(states);g=[];mins=[];paths=[];overs=[];clips=self.history[0];samples=self.history[1];progress=self.progress
  from retry.drive519_control import project,reference
  for state in states:
   self.guard();mm=engine.margin(state,self.static['roads'],self.index,self.static['boundary'],self.edge,self.static['obstacles']);self.cost['geometry_checks']+=1;q=project(state.center,self.path,progress);progress=q['s'];over=math.hypot(*state.planar.linear.velocity)-reference(progress,self.path)[0];g.extend([mm-.5,3-q['distance'],4.85-over]);mins.append(mm);paths.append(q['distance']);overs.append(over)
  ratios=[];clipfractions=[]
  for row in rows:
   ratios.extend(f['ratio'] for f in row['forces']);clips+=sum(f['clipped'] for f in row['forces']);samples+=4;clipfractions.append(clips/samples);g.extend([1.059-f['ratio'] for f in row['forces']]);g.extend([.1-clips/samples,100-row['body_speed']])
  if not hasattr(self,'baseline_clip_mask'):self.baseline_clip_mask=np.array([f['clipped'] for row in rows for f in row['forces']],bool)
  g.extend(1-np.array(ratios)[~self.baseline_clip_mask])
  for z,gate in zip(cross,self.gates):
   delta=(z['vector']-gate['baseline_vector'])/gate['tolerance'];g.extend(1-delta);g.extend(1+delta);g.append(gate['baseline_time']-z['time'])
  result=dict(x=list(map(float,x)),g=np.array(g),times=np.array([z['time'] for z in cross]),crossings=cross,states=states,rows=rows,min_margin=min(mins),max_path=max(paths),max_reference_overspeed=max(overs),max_force=max(ratios),max_clip_fraction=max(clipfractions),final_clip_history=[clips,samples],max_body=max(row['body_speed'] for row in rows))
  save(D/f'{label}-private.json',dict(x=result['x'],g=result['g'].tolist(),crossings=[dict(z,vector=z['vector'].tolist(),tolerance=z['tolerance'].tolist()) for z in cross],rows=rows,min_margin=result['min_margin'],max_path=result['max_path'],max_reference_overspeed=result['max_reference_overspeed'],max_force=result['max_force'],max_clip_fraction=result['max_clip_fraction'],final_clip_history=result['final_clip_history']))
  save(D/'latest-checkpoint-private.json',dict(current=label,cost=self.cost,model_ticks=self.counter[0],terminal=short(states[-1])),True);return result
 def run(self):
  out={};transcription={};direction=None;candidate=None
  try:
   matches=[]
   for j in range(9):
    root=engine.load_root(dict(self.nodes[j],roads=self.static['root']['roads']));each=[]
    for k in range(4):
     root,row=self.raw(root,self.base_actions[j]);self.cost['node_ticks']+=1;expected=self.saved[4*j+k];same=canonical(short(root))==expected['root_without_roads'] and canonical(row['forces'])==expected['forces'];each.append(dict(raw=k+1,fullstate_and_force_exact=same,root_without_roads=short(root),forces=row['forces']))
    matches.extend(r['fullstate_and_force_exact'] for r in each);save(D/f'node-{j:02d}-private.json',dict(rows=each,terminal_defect_exact_zero=canonical(short(root))==self.nodes[j+1]))
   baseline=self.evaluate(self.x0,'baseline');sequential=all(canonical(short(s))==expected['root_without_roads'] and canonical(row['forces'])==expected['forces'] for s,row,expected in zip(baseline['states'][1:],baseline['rows'],self.saved));safe=min(baseline['g'])>=-1e-10
   transcription=dict(independent_node_raw_exact=all(matches),node_raw_compared=len(matches),sequential_raw_exact=sequential,exact_feasible=safe and sequential and all(matches),baseline_min_constraint=float(min(baseline['g'])),baseline_times_s=baseline['times'].tolist(),entry_action=self.saved[0]['index'],source_reset_reachable=True,native_reachability_claim=False)
   save(G/'retry/transcribe559_transcription.json',transcription)
   if transcription['exact_feasible']:
    self.current='state_sensitivity';lower=[];upper=[];steps=[];jac=[];timejac=[];limit=float(np.float32(.4));lock=float(np.nextafter(np.float32(.9),np.float32(1.)));unlock=float(np.float32(.9))
    for j,v in enumerate(self.x0):
     if j%2==0:a,b=-limit,limit;h=1e-5;trust=.002
     else:
      a,b=(-1.,-lock) if v<=-lock else (-unlock,0.) if v<0 else (0.,1.);h=1e-4;trust=.02
     lower.append(max(a-v,-trust));upper.append(min(b-v,trust));requested=h if v+h<=b else -h
     xp=self.x0.copy();xp[j]=float(np.float32(v+requested));actual=xp[j]-v
     if not actual or xp[j]<a or xp[j]>b:raise RuntimeError('FINITE_DIFFERENCE_BRANCH_BOUND')
     ev=self.evaluate(xp,f'FD-{j:02d}');self.cost['FD_rollouts']+=1;jac.append((ev['g']-baseline['g'])/actual);timejac.append((ev['times']-baseline['times'])/actual);steps.append(actual)
    J=np.array(jac).T;T=np.array(timejac).T;objective=T.mean(axis=0);lp=linprog(objective,A_ub=-J,b_ub=.5*baseline['g'],bounds=list(zip(lower,upper)),method='highs');direction=dict(success=bool(lp.success),status=int(lp.status),message=str(lp.message),FD_steps=steps,zero_direction_linear_feasible=bool(min(.5*baseline['g'])>=-1e-10))
    if lp.success:
     delta=lp.x;direction.update(delta=delta.tolist(),predicted_gain_ms=(-1000*(T@delta)).tolist(),linear_min_slack=float(min(J@delta+.5*baseline['g'])),predicted_average_gain_ms=float(-1000*objective@delta));candidate=self.evaluate(self.x0+delta,'candidate');self.cost['candidate_rollouts']+=1
     gain=1000*(baseline['times']-candidate['times']);position=[float(np.linalg.norm(z['vector'][:2]-gate['baseline_vector'][:2])) for z,gate in zip(candidate['crossings'],self.gates)];physical=candidate['min_margin']>=.5 and candidate['max_path']<=3 and candidate['max_reference_overspeed']<=4.85 and candidate['max_force']<=1.059 and candidate['max_clip_fraction']<=.1 and candidate['max_body']<100;comparisons=min(candidate['g'])>=-1e-9 and max(position)<=.15
     out.update(candidate_evaluated=True,candidate_physical_safe=physical,candidate_comparison_pass=bool(comparisons),candidate_gain_ms=gain.tolist(),candidate_gate_position_errors_m=position,candidate_times_s=candidate['times'].tolist(),candidate_raw_brackets=[z['raw_bracket'] for z in candidate['crossings']],candidate_stats=dict(min_margin=candidate['min_margin'],max_path=candidate['max_path'],max_reference_overspeed=candidate['max_reference_overspeed'],max_force=candidate['max_force'],max_clip_fraction=candidate['max_clip_fraction'],max_body=candidate['max_body']),improvement_gate_pass=bool(physical and comparisons and min(gain)>=5.))
    save(D/'direction-private.json',direction)
   out.update(completed=True,transcription=transcription,direction={k:v for k,v in (direction or {}).items() if k not in {'delta','FD_steps'}})
  except BaseException as e:
   out.update(completed=False,error=type(e).__name__+':'+str(e),transcription=transcription);save(D/'failure-private.json',dict(error=out['error'],traceback=traceback.format_exc(),current=self.current,cost=self.cost,model_ticks=self.counter[0]))
  finally:
   signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
   out.update(cost=dict(self.cost,model_ticks=self.counter[0],internal_wheel_force_evaluations=4*self.counter[0],CPU_s=time.process_time()-self.cpu,wall_s=time.perf_counter()-self.wall),new_native_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT_queries=0,SEALED_queries=0,research_remaining=22758,reserve=84000,reserve_used=0,actual_baseline_s=13.66,no_lap_gain_observation=True)
   save(G/'retry/transcribe559_result.json',out);print(json.dumps(out,indent=2))

if __name__=='__main__':Study().run()
