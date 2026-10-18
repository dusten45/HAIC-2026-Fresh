"""Bounded sequential feasible source trajectory improvement from saved551.

No periodicity, no no-new-clipping mask, and no comparative yaw constraint.
Every accepted incumbent is a complete exact source rollout from fixed start.
"""
import datetime,json,math,signal,time,traceback
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
import retry.transcribe559_model as previous
import retry.period556_model as engine

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response560-private');previous.D=D;engine.D=D
save,rd,sha,short=engine.save,engine.rd,engine.sha,engine.short
vector,canonical=previous.vector,previous.canonical
INPUTS=previous.INPUTS;SOURCES=['retry/sequential560_model.py',*previous.SOURCES]

class Study(previous.Study):
 def __init__(self):
  D.mkdir(mode=0o700,exist_ok=False);self.static,self.paths,data=map(rd,INPUTS);self.path=self.paths['candidate'];trace=data['trace'];anchor=self.path['arcs'][37]
  at=next(j for j,r in enumerate(trace) if j and r['index']>24 and r['raw']==1 and trace[j-1]['progress']>=anchor);self.saved=trace[at:at+132];assert len(self.saved)==132
  self.before=trace[at-1]['root_without_roads'];self.initial=engine.load_root(dict(self.before,roads=self.static['root']['roads']));self.history=[sum(f['clipped'] for r in trace[:at] if r['index']>24 for f in r['forces']),sum(4 for r in trace[:at] if r['index']>24)];self.progress=trace[at-1]['progress'];self.base_actions=[np.array(self.saved[4*j]['action'],np.float32) for j in range(33)];self.x0=np.array([v for a in self.base_actions[:20] for v in [float(a[0]),float(a[1])-float(a[2])]]);self.nodes=[self.before]+[r['root_without_roads'] for r in self.saved if r['raw']==4];self.gates=[]
  for k in (79,127):
   p=self.saved[k]['root_without_roads'];vv=p['planar']['linear']['velocity'];speed=math.hypot(*vv);root=engine.load_root(dict(p,roads=self.static['root']['roads']));vec,tol,names=vector(root);self.gates.append(dict(point=p['center'],normal=[v/speed for v in vv],baseline_time=.02*(k+1),baseline_vector=vec,tolerance=tol,groups=names))
  save(D/'segment-private.json',dict(entry_action=self.saved[0]['index'],optimized_holds=20,follow_holds=12,measurement_buffer_holds=1,history=self.history,initial=self.before,nodes=self.nodes,commands=[a.tolist() for a in self.base_actions],gates=[dict(g,baseline_vector=g['baseline_vector'].tolist(),tolerance=g['tolerance'].tolist()) for g in self.gates]))
  self.contract=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',hypothesis='Bounded sequential feasible optimization can accumulate source time improvement from exact feasible reset-reachable551 rather than rejecting all sub5ms steps. Preserve559 verdict unchanged.',selection='Same deterministic first551 tracking before-action progress>=533station37. First20holds controls40, fixed12hold follow and1fixed measurement-buffer hold. Frozen physical planes at saved20/32hold endpoints; no synthetic periodic goal, no window selection after outcomes.',transcription='Independent33node4raw replay and sequential132raw must EXACTLY match all saved root/contact/force values. Stop before directions on mismatch. Exact feasible baseline retained forever.',objective='Minimize average arrival time to both frozen common-space planes. Source raw signed-plane interpolation convention and raw brackets reported; not native or full-lap performance.',global_safety='Every raw: preclipforce<=1.059,footprint>=.50,path<=3,ORIGINAL551reference overspeed<=4.85,all hull/wheel<100,cumulative clipping<=10% from true saved tracking history. All model body hard100 even rejected forecasts.',return_design='Main gate position aperture components +/-.7m (Euclidean<=1m); follow gate components +/-.35m (Euclidean<=.5m),body heading difference<=.08rad,velocity direction difference<=.05rad,speed>=baseline-.5m/s. Full world/mechanical state differences logged. NO comparative yaw,omega/gas/joint equality,periodicity,no-new-clip mask or frozen contact branch. Return apertures are local handoff design, not physical necessity.',linearization='40 one-sided exact source rollouts per direction, steering1e-5/pedal1e-4 actual float32 difference. FD points stay inside action bounds, preferably same local brake-lock regime; LP/trials MAY change pedal/lock/contact/clip branch. Derivative clipping-count discontinuities are handled by actual validation, never presumed smooth.',LP='scipy HiGHS one per trial, average two-gate time derivative objective; G*delta>=-.75*g_inc for physical/return constraints, and predicted BOTH arrival times nonworsening. No no-new-clip mask. ZERO delta feasible. Steps bounded by steering .004*radius,pedal .04*radius and action bounds.',acceptance='Actual full source rollout physical+return feasible, both common-plane times<=incumbent+0.5microsecond, mean actual gain>1microsecond. No5ms per-step requirement. Feasible beneficial accepted state immutable and retained; rejects never replace it.',prediction_recovery='Agreement if mean actual/predicted in[.25,2] and max time error<=max(.5ms,.5*maxabs(predicted)). Safe beneficial mismatches MAY be accepted but next radius halves;2consecutive accepted mismatches stop. Safe agreement ratio>=.75 permits radius double up to2 ONLY if no contact/clip/pedal/lock branch change; otherwise do not grow. Unsafe/nonbeneficial/unbracketed trial: incumbent unchanged,radius halved, resolve same linear model; max3trials/direction, radius floor.125. No successful trial after3 -> stop. Relinearize after every acceptance.',limits='Directions<=6,acceptedsteps<=6,trials<=3/direction (18total),radius initial1,max2,min.125. Two consecutive accepted mean gains<.02ms -> numerical stagnation stop. Float32-identical controls/LP failure ->stop. No stop solely for gain<5ms. No new iteration/window/target/threshold after outcomes.',final='Fresh exact source replay of final incumbent with full132raw safety, same-space two times,12hold continued following-state/gate metrics, immutable saved accepted trajectory identity. No actual/full-lap promotion.',caps=dict(model_ticks=36000,explicit_wheel_force_evaluations=150000,geometry_checks=36000,CPU_s=600,wall_s=700,directions=6,acceptances=6,trials=18,FD_rollouts=240),budget_recovery='Before next direction require reserve40FD+3trials+1final replay (5808ticks) and CPU<480s. Soft stop preserves final replay; hard timer/domain/cost checkpoints incumbent and terminates without rerun. Rejected/FD source forecasts charged and private.',actual_cap=0,new_seed_HOLDOUT_SEALED_other_environment_paid=0,research_remaining=22758,reserve=84000,reserve_used=0,source_sha256={p:sha(G/p) for p in SOURCES},private_inputs_sha256={str(p):sha(p) for p in INPUTS},segment_sha256=sha(D/'segment-private.json'))
  save(G/'retry/sequential560_contract.json',self.contract);save(D/'STARTED.json',dict(contract_sha256=sha(G/'retry/sequential560_contract.json')))
  self.cpu,self.wall=time.process_time(),time.perf_counter();self.counter=[0];self.index=engine.bounds(self.initial.roads);self.edge=engine.boundary_index(self.static['boundary']);self.cost=dict(explicit_wheel_force_evaluations=0,geometry_checks=0,body_checks=0,residual_calls=0,unsafe_forecast_raw=0,max_forecast_force=0.,max_body_speed=0.,node_ticks=0,evaluations=0,direction_attempts=0,FD_rollouts=0,trial_rollouts=0,LP_solves=0);self.current='transcription';self.incumbent=None;self.steps=[];self.directions=[];self.evaluation_count=0
  signal.signal(signal.SIGPROF,self.guard);signal.setitimer(signal.ITIMER_PROF,600);signal.signal(signal.SIGALRM,self.guard);signal.setitimer(signal.ITIMER_REAL,700)
 def guard(self,*_):
  if self.counter[0]>=36000 or self.cost['explicit_wheel_force_evaluations']+4>150000 or self.cost['geometry_checks']>=36000:raise RuntimeError('WORK_CAP')
  if time.process_time()-self.cpu>=600 or time.perf_counter()-self.wall>=700:raise RuntimeError('TIME_CAP')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.contract['deadline_utc']):raise RuntimeError('DEADLINE')
 def actions(self,x):return [np.array([x[2*j],max(0.,x[2*j+1]),max(0.,-x[2*j+1])],np.float32) for j in range(20)]+self.base_actions[20:]
 def evaluate(self,x,label):
  self.current=label;states,rows=self.simulate(x);cross=None;cross_error=None
  try:cross=self.crossings(states)
  except RuntimeError as e:cross_error=str(e)
  g=[];labels=[];mins=[];paths=[];overs=[];clips=self.history[0];samples=self.history[1];progress=self.progress;fractions=[]
  def add(values,name):g.extend(values);labels.extend([name]*len(values))
  from retry.drive519_control import project,reference
  for state in states:
   self.guard();mm=engine.margin(state,self.static['roads'],self.index,self.static['boundary'],self.edge,self.static['obstacles']);self.cost['geometry_checks']+=1;q=project(state.center,self.path,progress);progress=q['s'];over=math.hypot(*state.planar.linear.velocity)-reference(progress,self.path)[0];add([mm-.5],'footprint');add([3-q['distance']],'path');add([4.85-over],'reference');mins.append(mm);paths.append(q['distance']);overs.append(over)
  ratios=[]
  for row in rows:
   ratios.extend(f['ratio'] for f in row['forces']);clips+=sum(f['clipped'] for f in row['forces']);samples+=4;fractions.append(clips/samples);add([1.059-f['ratio'] for f in row['forces']],'force');add([.1-clips/samples],'clip');add([100-row['body_speed']],'body')
  differences=[]
  if cross:
   for i,(z,gate) in enumerate(zip(cross,self.gates)):
    d=z['vector']-gate['baseline_vector'];aperture=.7 if i==0 else .35;add(list(aperture-d[:2])+list(aperture+d[:2]),'gate_position');differences.append(d.tolist())
    if i==1:
     da=engine.wrap(d[2]);va=z['vector'][3:5];vb=gate['baseline_vector'][3:5];dv=engine.wrap(math.atan2(-va[0],va[1])-math.atan2(-vb[0],vb[1]));speed=float(np.linalg.norm(va));base=float(np.linalg.norm(vb));add([.08-da,.08+da],'return_angle');add([.05-dv,.05+dv],'return_direction');add([speed-base+.5],'return_speed')
  physical=min(mins)>=.5 and max(paths)<=3 and max(overs)<=4.85 and max(ratios)<=1.059 and max(fractions)<=.1 and max(r['body_speed'] for r in rows)<100
  feasible=physical and cross is not None and min(g)>=-1e-10
  if cross:feasible=feasible and np.linalg.norm(np.array(cross[0]['vector'][:2])-self.gates[0]['baseline_vector'][:2])<=1 and np.linalg.norm(np.array(cross[1]['vector'][:2])-self.gates[1]['baseline_vector'][:2])<=.5
  result=dict(x=np.array(x).copy(),states=states,rows=rows,g=np.array(g),labels=labels,crossings=cross,times=np.array([z['time'] for z in cross]) if cross else None,physical_safe=bool(physical),feasible=bool(feasible),cross_error=cross_error,min_margin=min(mins),max_path=max(paths),max_reference_overspeed=max(overs),max_force=max(ratios),max_clip_fraction=max(fractions),final_clip_history=[clips,samples],max_body=max(r['body_speed'] for r in rows),gate_world_state_differences=differences)
  self.cost['evaluations']+=1;self.evaluation_count+=1
  payload=dict(x=result['x'].tolist(),g=result['g'].tolist(),labels=labels,crossings=[dict(z,vector=z['vector'].tolist(),tolerance=z['tolerance'].tolist()) for z in cross] if cross else None,physical_safe=bool(physical),feasible=bool(feasible),cross_error=cross_error,stats={k:result[k] for k in ['min_margin','max_path','max_reference_overspeed','max_force','max_clip_fraction','final_clip_history','max_body']},gate_world_state_differences=differences,terminal_root_without_roads=short(states[-1]))
  if label.startswith('FD'):
   unsafe=next((r for r in rows if max(f['ratio'] for f in r['forces'])>1.059),None);payload['first_force_violation']=unsafe
  else:payload['rows']=rows
  save(D/f'{label}-private.json',payload);save(D/'latest-checkpoint-private.json',dict(current=label,cost=self.cost,model_ticks=self.counter[0],incumbent_label=self.incumbent['label'] if self.incumbent else None,terminal=short(states[-1])),True);result['label']=label;return result
 def branch_changes(self,a,b):
  contacts=sum(x['root_without_roads']['current_contacts']!=y['root_without_roads']['current_contacts'] for x,y in zip(a['rows'],b['rows']));aa=np.array([f['clipped'] for r in a['rows'] for f in r['forces']]);bb=np.array([f['clipped'] for r in b['rows'] for f in r['forces']]);u=a['x'][1::2];v=b['x'][1::2]
  return dict(contact_raw_changes=int(contacts),new_clipped_samples=int(sum(bb & ~aa)),freed_clipped_samples=int(sum(aa & ~bb)),pedal_mode_changes=int(sum(np.sign(u)!=np.sign(v))),brake_lock_changes=int(sum((u<=-.9)!=(v<=-.9))))
 def active(self,result):
  out={}
  for name in set(result['labels']):
   values=[v for v,n in zip(result['g'],result['labels']) if n==name];out[name]=dict(min_slack=float(min(values)),near_boundary=sum(v<=1e-5 for v in values))
  return out
 def retain(self,result,number):
  assert result['feasible'];self.incumbent=result
  save(D/f'incumbent-{number:02d}-private.json',dict(evaluation_label=result['label'],evaluation_sha256=sha(D/f"{result['label']}-private.json"),x=result['x'].tolist(),times=result['times'].tolist(),full_source_feasible=True,model_ticks=self.counter[0]))
 def run(self):
  out={};stop=None;radius=1.;small=0;bad_prediction=0;final=None;baseline=None
  try:
   exact=True
   for j in range(33):
    root=engine.load_root(dict(self.nodes[j],roads=self.static['root']['roads']));node=[]
    for k in range(4):
     root,row=self.raw(root,self.base_actions[j]);self.cost['node_ticks']+=1;expected=self.saved[4*j+k];match=canonical(short(root))==expected['root_without_roads'] and canonical(row['forces'])==expected['forces'];exact &=match;node.append(dict(exact=match,root_without_roads=short(root),forces=row['forces']))
    save(D/f'node-{j:02d}-private.json',dict(rows=node))
   baseline=self.evaluate(self.x0,'baseline');exact &=all(canonical(short(s))==r['root_without_roads'] and canonical(row['forces'])==r['forces'] for s,row,r in zip(baseline['states'][1:],baseline['rows'],self.saved));out['exact_feasible_initialization']=bool(exact and baseline['feasible'])
   if not out['exact_feasible_initialization']:stop='BASELINE_TRANSCRIPTION_OR_FEASIBILITY_FAILURE'
   else:
    self.retain(baseline,0)
    for iteration in range(6):
     if radius<.125:stop='RADIUS_FLOOR';break
     if self.counter[0]+5808>36000 or time.process_time()-self.cpu>=480:stop='SOFT_BUDGET_RESERVE';break
     self.cost['direction_attempts']+=1;incumbent=self.incumbent;x=incumbent['x'];jac=[];tj=[];fd_steps=[];limit=float(np.float32(.4))
     for j,v in enumerate(x):
      self.current=f'FD-{iteration:02d}-{j:02d}';a,b=(-limit,limit) if j%2==0 else(-1.,1.);h=1e-5 if j%2==0 else 1e-4;dh=h if v+h<=b else-h
      if j%2 and ((v<=-.9)!=(v+dh<=-.9)):dh=-dh
      xp=x.copy();xp[j]=float(np.float32(v+dh));actual=xp[j]-v
      if not actual or xp[j]<a or xp[j]>b:raise RuntimeError('FD_BOUND_OR_FLOAT32')
      ev=self.evaluate(xp,f'FD-{iteration:02d}-{j:02d}');self.cost['FD_rollouts']+=1
      if ev['times'] is None:stop='FD_UNBRACKETED';break
      jac.append((ev['g']-incumbent['g'])/actual);tj.append((ev['times']-incumbent['times'])/actual);fd_steps.append(actual)
     if stop:break
     J=np.array(jac).T;T=np.array(tj).T;objective=T.mean(axis=0);accepted=False;record=dict(direction=iteration+1,incumbent_before=incumbent['label'],FD_steps=fd_steps,trials=[])
     for trial in range(3):
      if radius<.125:stop='RADIUS_FLOOR';break
      bounds=[]
      for j,v in enumerate(x):
       a,b=(-limit,limit) if j%2==0 else(-1.,1.);trust=(.004 if j%2==0 else.04)*radius;bounds.append((max(a-v,-trust),min(b-v,trust)))
      self.cost['LP_solves']+=1;lp=linprog(objective,A_ub=np.vstack([-J,T]),b_ub=np.r_[.75*incumbent['g'],[0.,0.]],bounds=bounds,method='highs')
      if not lp.success:stop='LP_FAILURE';record['LP_status']=int(lp.status);record['LP_message']=str(lp.message);break
      xx=x+lp.x;quant=np.array([float(np.float32(v)) for v in xx]);predicted=-(T@(quant-x));pred=float(np.mean(predicted))
      if np.array_equal(quant,x):stop='FLOAT32_STAGNATION';break
      self.cost['trial_rollouts']+=1;candidate=self.evaluate(quant,f'trial-{iteration:02d}-{trial:02d}');branch=self.branch_changes(incumbent,candidate);actual=incumbent['times']-candidate['times'] if candidate['times'] is not None else None;gain=float(np.mean(actual)) if actual is not None else None
      accept=bool(candidate['feasible'] and actual is not None and min(actual)>=-5e-7 and gain>1e-6);ratio=gain/pred if gain is not None and pred>1e-12 else None;err=float(max(abs(actual-predicted))) if actual is not None else None;agreement=bool(ratio is not None and .25<=ratio<=2 and err<=max(.0005,.5*max(abs(predicted))))
      item=dict(trial=trial+1,label=candidate['label'],radius=radius,predicted_gain_ms=(1000*predicted).tolist(),actual_gain_ms=(1000*actual).tolist() if actual is not None else None,prediction_max_error_ms=1000*err if err is not None else None,actual_predicted_ratio=ratio,agreement=agreement,source_feasible=candidate['feasible'],physical_safe=candidate['physical_safe'],cross_error=candidate['cross_error'],accepted=accept,branch_changes=branch,active_constraints=self.active(candidate),incumbent_preserved_on_reject=not accept)
      record['trials'].append(item)
      if accept:
       accepted=True;self.retain(candidate,len(self.steps)+1);step=dict(direction=iteration+1,accepted_step=len(self.steps)+1,cumulative_gain_ms=(1000*(baseline['times']-candidate['times'])).tolist(),**item);self.steps.append(step);small=small+1 if gain<2e-5 else 0;bad_prediction=0 if agreement else bad_prediction+1
       changed=any(branch.values())
       if not agreement:radius*=.5
       elif ratio>=.75 and not changed:radius=min(2.,radius*2)
       if small>=2:stop='TWO_SMALL_ACCEPTED_GAINS'
       if bad_prediction>=2:stop='TWO_ACCEPTED_PREDICTION_MISMATCHES'
       break
      radius*=.5
     self.directions.append(record);save(D/f'direction-{iteration:02d}-private.json',record)
     if stop:break
     if not accepted:stop='THREE_REJECTED_TRIALS';break
    if stop is None:stop='DIRECTION_LIMIT6'
   if self.incumbent is not None:
    final=self.evaluate(self.incumbent['x'],'final');same=all(canonical(short(a))==canonical(short(b)) for a,b in zip(final['states'],self.incumbent['states']));assert final['feasible'] and same
    out.update(final_fresh_replay_exact=same,final_feasible=final['feasible'],baseline_times_s=baseline['times'].tolist(),final_times_s=final['times'].tolist(),cumulative_gain_ms=(1000*(baseline['times']-final['times'])).tolist(),baseline_brackets=[z['raw_bracket'] for z in baseline['crossings']],final_brackets=[z['raw_bracket'] for z in final['crossings']],final_state_differences=final['gate_world_state_differences'],final_active_constraints=self.active(final),final_stats={k:final[k] for k in ['min_margin','max_path','max_reference_overspeed','max_force','max_clip_fraction','final_clip_history','max_body']})
   out.update(completed=True,stop_reason=stop)
  except BaseException as e:
   out.update(completed=False,error=type(e).__name__+':'+str(e),stop_reason=stop,incumbent_preserved=self.incumbent is not None);save(D/'failure-private.json',dict(error=out['error'],traceback=traceback.format_exc(),current=self.current,incumbent_label=self.incumbent['label'] if self.incumbent else None,cost=self.cost,model_ticks=self.counter[0]))
  finally:
   signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
   out.update(accepted_steps=self.steps,directions=[{k:v for k,v in d.items() if k!='FD_steps'} for d in self.directions],accepted_count=len(self.steps),direction_count=len(self.directions),incumbent_label=self.incumbent['label'] if self.incumbent else None,cost=dict(self.cost,model_ticks=self.counter[0],internal_wheel_force_evaluations=4*self.counter[0],CPU_s=time.process_time()-self.cpu,wall_s=time.perf_counter()-self.wall),new_native_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT_queries=0,SEALED_queries=0,research_remaining=22758,reserve=84000,reserve_used=0,actual_baseline_s=13.66,no_lap_gain_observation=True)
   save(G/'retry/sequential560_result.json',out);print(json.dumps(out,indent=2))

if __name__=='__main__':Study().run()
