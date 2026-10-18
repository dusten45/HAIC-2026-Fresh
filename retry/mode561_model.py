"""Exact prefix-order-stat gate, then bounded rank-branch feasible optimization."""
import datetime,json,math,signal,time,traceback
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
import retry.sequential560_model as old
import retry.period556_model as engine
from retry.clip561_core import atomic_write,plain,allowance,order_slack,prefix_slacks,nonexempt_branch
from retry.clip561_preflight import run as preflight

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response561-private');old.D=D;engine.D=D;old.save=atomic_write;engine.save=atomic_write
rd,sha=engine.rd,engine.sha
INPUTS=[Path('/workspace/haic-response515-private/collected-map-state-private.json'),Path('/workspace/haic-response551-private/frozen-paths-private.json'),Path('/workspace/haic-response560-private/segment-private.json'),Path('/workspace/haic-response560-private/baseline-private.json'),*[Path(f'/workspace/haic-response560-private/FD-00-{i:02d}-private.json') for i in range(40)],*[Path(f'/workspace/haic-response560-private/trial-00-{i:02d}-private.json') for i in range(3)]]
SOURCES=['retry/mode561_model.py','retry/clip561_core.py','retry/clip561_preflight.py',*old.SOURCES]

class Study(old.Study):
 def __init__(self):
  D.mkdir(mode=0o700,exist_ok=False)
  self.contract=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',hypothesis='Replace wrong smooth differentiation of clipping counts with exact strict-prefix order statistics and mode-aware force-rank branches. Verify storage/count equivalence/saved560cases BEFORE any new source. Preserve560 failures and CPU gap.',exact_rule='For prefix n and actual history C0,N0: k=floor((N0+n)/10)-C0. If k<0 impossible; if k>=n automatic; otherwise count(r>1)<=k iff descending r[k]<=1. EXACT1 unclipped; ties do not alter predicate. Finite ratios/source integer counts, tested denominators<=1e6. Nonsmooth, not a smooth-function claim.',preflight='Atomic writer NumPy scalars/arrays,NaN rejection,exclusive overwrite prevention,injected os.replace failure and finally cost persistence. Exhaustive short synthetic arrays including float64/f32 nextafter1,ties,exact1,existingC0/denominator boundaries. Reclassify saved560baseline and3rejected trajectories with no model/force/geometry calls. Stop if any gate fails.',selection='Same frozen560 first551 tracking segment:20optimized+12follow+1measurement buffer,source initial/gates/history identical. No new seed/goal/window. Fresh baseline132raw must match saved560 ALL root/contact/force exactly.',reuse='First direction reuses40saved560 FD columns: individual ratio gradients from NEGATIVE force-slack gradient, non-clip physical/return gradients from cached features. NO clipping-count derivatives. Source/inputs/fresh baseline checked. Subsequent accepted incumbents get40fresh FD columns,actual float32 step1e-5steer/1e-4pedal.',direction='At most4directions/4acceptances. Each: primary branch exempts each prefix topk(current exact ratios); constrain complement individual LINEARIZED ratios<=1-buffer,buffer=min(1e-5,.25*max(0,1-currentratio)). Deduplicate union. Not frozen baseline clipped mask: exemptions use allowed budget, may include unclipped samples.',branch_reconstruction='On primary failure, ONE alternate branch from rejected proposal rank (or saved560quarter proposal if LP has no source proposal); may require freeing old clips while permitting new identities. Solve same force-linear model, not repeated radius shrink. Fixed trust steer.004/pedal.04,action bounds; max2LP branches/direction.',poll='If both branches do not yield accepted step, at most2 exact-source coordinate polls: time-descent coordinate maximizing abs(mean time gradient)*amplitude; then clip-relief coordinate maximizing abs(selected critical order-stat force gradient)*amplitude. Amplitude steer.0005/pedal.005,clipped to action bounds. Fixed rules, no poll/radius grid.',LP='Average two common-plane time derivative; nonclip physical/return Gdelta>=-.75*g, predicted BOTH gate times nonworsening, plus individual selected rank-branch force constraints. Actual count/orderstat ALWAYS checked by source. New clipping allowed inside true budget; no comparative yaw or periodicity.',acceptance='Actual full132raw source physical+return feasible, exact prefix count/order predicates agree, both gate times<=incumbent+0.5microsecond,mean gain>1microsecond. No5ms minimum. Retain immutable incumbent. Report prediction/actual/error and branch changes; two accepted prediction mismatches or two accepted gains<.02ms stop. Failed branch/polls never replace incumbent.',termination='No accepted step after two branches+two polls ->stop. Limits/float32 identity/deadline/domain ->stop with ledger and incumbent. Fresh final replay if reserve remains. Not all safe trajectories must share a chosen rank branch; branch failure is not global infeasibility.',caps=dict(model_ticks=20000,explicit_wheel_force_evaluations=85000,geometry_checks=20000,CPU_s=400,wall_s=480,directions=4,acceptances=4,LP_branches=8,polls=8,source_proposals=16,fresh_FD_columns=120,preflight_CPU_s=20,preflight_wall_s=30),budget_reserve_rule='Before fresh40FD require132*(40+4+1)ticks reserve and CPU<280s; final replay132ticks reserved. First40FD reused at modelcost0. Units/count checks cost0model and includedCPU/wall.',storage='JSON-safe recursive basic conversion; atomic exclusive link or replace; per-evaluation finally cost ledger and outer finally FIRST independent final ledger then result. CPU/wall/counters never dependent on direction result serialization.',actual_cap=0,new_seed_HOLDOUT_SEALED_other_environment_paid=0,research_remaining=22758,reserve=84000,reserve_used=0,source_sha256={p:sha(G/p) for p in SOURCES},private_inputs_sha256={str(p):sha(p) for p in INPUTS})
  atomic_write(G/'retry/mode561_contract.json',self.contract);atomic_write(D/'STARTED.json',dict(contract_sha256=sha(G/'retry/mode561_contract.json')))
  self.cpu,self.wall=time.process_time(),time.perf_counter();self.counter=[0];self.cost=dict(explicit_wheel_force_evaluations=0,geometry_checks=0,body_checks=0,residual_calls=0,unsafe_forecast_raw=0,max_forecast_force=0.,max_body_speed=0.,evaluations=0,directions=0,LP_branches=0,polls=0,source_proposals=0,reused_FD_columns=0,fresh_FD_columns=0);self.current='preflight';self.incumbent=None;self.evaluation_count=0;self.steps=[];self.records=[];self.pre=None
  self.static=rd(INPUTS[0]);self.paths=rd(INPUTS[1]);self.path=self.paths['candidate'];self.segment=rd(INPUTS[2]);self.saved_baseline=rd(INPUTS[3]);self.initial=engine.load_root(dict(self.segment['initial'],roads=self.static['root']['roads']));self.history=self.segment['history'];self.progress=self.path['arcs'][37]
  from retry.drive519_control import project
  self.progress=project(self.initial.center,self.path,self.progress)['s'];self.base_actions=[np.array(a,np.float32) for a in self.segment['commands']];self.x0=np.array(self.saved_baseline['x']);self.gates=[dict(g,baseline_vector=np.array(g['baseline_vector']),tolerance=np.array(g['tolerance'])) for g in self.segment['gates']];self.index=engine.bounds(self.initial.roads);self.edge=engine.boundary_index(self.static['boundary'])
  signal.signal(signal.SIGPROF,self.guard);signal.setitimer(signal.ITIMER_PROF,400);signal.signal(signal.SIGALRM,self.guard);signal.setitimer(signal.ITIMER_REAL,480)
 def guard(self,*_):
  if self.counter[0]>20000 or self.cost['explicit_wheel_force_evaluations']>85000 or self.cost['geometry_checks']>=20000:raise RuntimeError('WORK_CAP')
  if time.process_time()-self.cpu>=400 or time.perf_counter()-self.wall>=480:raise RuntimeError('TIME_CAP')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.contract['deadline_utc']):raise RuntimeError('DEADLINE')
 def raw(self,*args,**kwargs):
  if self.counter[0]>=20000 or self.cost['explicit_wheel_force_evaluations']+4>85000:raise RuntimeError('SOURCE_CAP')
  return engine.Study.raw(self,*args,**kwargs)
 def ledger(self,label):
  cost=dict(self.cost,model_ticks=self.counter[0],internal_wheel_force_evaluations=4*self.counter[0],CPU_s=time.process_time()-self.cpu,wall_s=time.perf_counter()-self.wall)
  atomic_write(D/'cost-ledger-private.json',dict(label=label,current=self.current,incumbent_label=self.incumbent['label'] if self.incumbent else None,cost=cost),True);return cost
 def evaluate(self,x,label):
  try:
   r=super().evaluate(x,label);ratios=np.array([f['ratio'] for row in r['rows'] for f in row['forces']]);assert all((f['ratio']>1)==f['clipped'] for row in r['rows'] for f in row['forces']);slack=prefix_slacks(ratios,*self.history)
   r.update(ratios=ratios,order_slacks=slack);assert bool(np.all(slack>=0))==(r['max_clip_fraction']<=.1)
   p=D/f'{label}-private.json';payload=rd(p);payload.update(ratios=ratios.tolist(),order_slacks=slack.tolist());atomic_write(p,payload,True);return r
  finally:self.ledger('evaluation-finally')
 def active(self,r):
  out=super().active(r)
  for v in out.values():v['near_boundary']=int(v['near_boundary'])
  out['prefix_orderstat']=dict(min_slack=float(min(r['order_slacks'])),near_boundary=int(sum(r['order_slacks']<=1e-5)));return out
 def linearization(self,inc,direction):
  keep=np.array([n!='clip' for n in inc['labels']]);force=np.array([i for i,n in enumerate(inc['labels']) if n=='force']);GG=[];TT=[];RR=[];steps=[]
  for j,v in enumerate(inc['x']):
   if direction==0:
    z=rd(INPUTS[4+j]);step=z['x'][j]-v;g=np.array(z['g']);times=np.array([q['time'] for q in z['crossings']]);assert z['labels']==inc['labels'];self.cost['reused_FD_columns']+=1
   else:
    limit=float(np.float32(.4));a,b=(-limit,limit) if j%2==0 else(-1.,1.);h=1e-5 if j%2==0 else 1e-4;dh=h if v+h<=b else -h
    if j%2 and ((v<=-.9)!=(v+dh<=-.9)):dh=-dh
    x=inc['x'].copy();x[j]=float(np.float32(v+dh));step=x[j]-v
    z=self.evaluate(x,f'FD-{direction:02d}-{j:02d}');self.cost['fresh_FD_columns']+=1
    if z['times'] is None:raise RuntimeError('FD_UNBRACKETED')
    g=z['g'];times=z['times']
   if step==0:raise RuntimeError('FD_ZERO_STEP')
   GG.append((g[keep]-inc['g'][keep])/step);RR.append(-(g[force]-inc['g'][force])/step);TT.append((times-inc['times'])/step);steps.append(step)
  return np.array(GG).T,np.array(RR).T,np.array(TT).T,keep,steps
 def consider(self,x,label,inc,T,kind,branchids=None):
  x=np.array([float(np.float32(v)) for v in x]);delta=x-inc['x']
  if np.array_equal(x,inc['x']):return None,None
  self.cost['source_proposals']+=1;r=self.evaluate(x,label);pred=-(T@delta);actual=inc['times']-r['times'] if r['times'] is not None else None;gain=float(np.mean(actual)) if actual is not None else None;accept=bool(r['feasible'] and actual is not None and min(actual)>=-5e-7 and gain>1e-6);ratio=gain/float(np.mean(pred)) if gain is not None and np.mean(pred)>1e-12 else None;err=float(max(abs(actual-pred))) if actual is not None else None;agreement=bool(ratio is not None and .25<=ratio<=2 and err<=max(.0005,.5*max(abs(pred))))
  event=dict(label=label,kind=kind,physical_safe=r['physical_safe'],source_feasible=r['feasible'],accepted=accept,predicted_gain_ms=(1000*pred).tolist(),actual_gain_ms=(1000*actual).tolist() if actual is not None else None,prediction_error_ms=1000*err if err is not None else None,agreement=agreement,branch_changes=self.branch_changes(inc,r),active_constraints=self.active(r))
  if branchids is not None:event['rank_branch_nonexempt_samples']=len(branchids)
  return r,event
 def run(self):
  out={};baseline=final=None;stop=None;error=None;small=bad=0
  try:
   self.pre=preflight(D);atomic_write(G/'retry/mode561_preflight.json',self.pre)
   if not self.pre['passed']:raise RuntimeError('PREFLIGHT_GATE')
   baseline=self.evaluate(self.x0,'baseline');exact=all(old.canonical(engine.short(s))==r['root_without_roads'] and old.canonical(row['forces'])==r['forces'] for s,row,r in zip(baseline['states'][1:],baseline['rows'],self.saved_baseline['rows']));assert exact and baseline['feasible'];out['exact_feasible_initialization']=True;self.retain(baseline,0)
   for d in range(4):
    if d and(self.counter[0]+132*45>20000 or time.process_time()-self.cpu>=280):stop='SOFT_BUDGET_RESERVE';break
    self.cost['directions']+=1;inc=self.incumbent;GG,RR,T,keep,steps=self.linearization(inc,d);g=inc['g'][keep];record=dict(direction=d+1,incumbent_before=inc['label'],FD_steps=steps,proposals=[],LP_statuses=[]);accepted=False;rejected=None;meanT=T.mean(axis=0);limit=float(np.float32(.4));bounds=[(max((-limit if j%2==0 else-1)-v,-(.004 if j%2==0 else.04)),min((limit if j%2==0 else 1)-v,(.004 if j%2==0 else.04))) for j,v in enumerate(inc['x'])]
    for branch in range(2):
     rank=inc['ratios'] if branch==0 else(rejected['ratios'] if rejected is not None else np.array([f['ratio'] for row in rd(INPUTS[-1])['rows'] for f in row['forces']]))
     ids=nonexempt_branch(rank,*self.history);buffer=np.minimum(1e-5,.25*np.maximum(0.,1-inc['ratios'][ids]));self.cost['LP_branches']+=1
     lp=linprog(meanT,A_ub=np.vstack([-GG,T,RR[ids]]),b_ub=np.r_[.75*g,[0.,0.],1-buffer-inc['ratios'][ids]],bounds=bounds,method='highs');record['LP_statuses'].append(dict(branch=branch+1,status=int(lp.status),success=bool(lp.success),nonexempt_count=len(ids),reconstruction=branch==1))
     if not lp.success:continue
     r,event=self.consider(inc['x']+lp.x,f'branch-{d:02d}-{branch:02d}',inc,T,'rank_branch' if branch==0 else 'reconstructed_rank_branch',ids)
     if event is not None:record['proposals'].append(event)
     if r is not None and event['accepted']:accepted=True;chosen=r;chosen_event=event;break
     if r is not None:rejected=r
    if not accepted:
     #Fixed non-radius recovery: coordinate time probe, then critical-rank relief.
     ncrit=int(np.argmin(inc['order_slacks']));_,critical=order_slack(inc['ratios'][:4*(ncrit+1)],*self.history);amplitude=np.array([.0005 if j%2==0 else.005 for j in range(40)])
     for p in range(2):
      gradient=meanT if p==0 else(RR[critical] if critical is not None else meanT);scores=abs(gradient)*amplitude;order=np.argsort(-scores,kind='stable');x=None;coordinate=None
      for j in order:
       if gradient[j]==0:continue
       change=-math.copysign(amplitude[j],gradient[j]);a,b=(-limit,limit) if j%2==0 else(-1.,1.);xx=inc['x'].copy();xx[j]=np.clip(xx[j]+change,a,b)
       if np.float32(xx[j])!=np.float32(inc['x'][j]):x=xx;coordinate=int(j);break
      if x is None:continue
      self.cost['polls']+=1;r,event=self.consider(x,f'poll-{d:02d}-{p:02d}',inc,T,'time_coordinate_poll' if p==0 else 'critical_clip_relief_poll')
      if event is not None:event['coordinate']=coordinate;record['proposals'].append(event)
      if r is not None and event['accepted']:accepted=True;chosen=r;chosen_event=event;break
    self.records.append(record);atomic_write(D/f'direction-{d:02d}-private.json',record)
    if not accepted:stop='NO_ACCEPTED_BRANCH_OR_TWO_POLLS';break
    self.retain(chosen,len(self.steps)+1);self.steps.append(dict(step=len(self.steps)+1,direction=d+1,cumulative_gain_ms=(1000*(baseline['times']-chosen['times'])).tolist(),**chosen_event));gain=float(np.mean(inc['times']-chosen['times']));small=small+1 if gain<2e-5 else 0;bad=0 if chosen_event['agreement'] else bad+1
    if small>=2:stop='TWO_SMALL_ACCEPTED_GAINS';break
    if bad>=2:stop='TWO_ACCEPTED_PREDICTION_MISMATCHES';break
   if stop is None:stop='DIRECTION_LIMIT4'
  except BaseException as e:
   error=type(e).__name__+':'+str(e);atomic_write(D/'failure-private.json',dict(error=error,traceback=traceback.format_exc(),current=self.current,incumbent=self.incumbent['label'] if self.incumbent else None))
  finally:
   try:
    if self.incumbent is not None and self.counter[0]+132<=20000 and time.process_time()-self.cpu<380 and time.perf_counter()-self.wall<460:
     final=self.evaluate(self.incumbent['x'],'final');same=all(old.canonical(engine.short(a))==old.canonical(engine.short(b)) for a,b in zip(final['states'],self.incumbent['states']));assert same and final['feasible'];out.update(final_fresh_replay_exact=same,final_feasible=True,baseline_times_s=baseline['times'].tolist(),final_times_s=final['times'].tolist(),cumulative_gain_ms=(1000*(baseline['times']-final['times'])).tolist(),baseline_brackets=[z['raw_bracket'] for z in baseline['crossings']],final_brackets=[z['raw_bracket'] for z in final['crossings']],final_stats={k:final[k] for k in ['min_margin','max_path','max_reference_overspeed','max_force','max_clip_fraction','final_clip_history','max_body']},final_active_constraints=self.active(final),final_world_state_differences=final['gate_world_state_differences'])
   except BaseException as e:
    error=(error+';' if error else '')+'FINAL:'+type(e).__name__+':'+str(e);atomic_write(D/'final-error-private.json',dict(error=error,traceback=traceback.format_exc()))
   signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
   #Independent, JSON-safe atomic cost FIRST; richer result cannot erase it.
   cost=self.ledger('outer-finally-cost-FIRST');atomic_write(G/'retry/mode561_cost.json',cost)
   out.update(completed=error is None,error=error,stop_reason=stop,preflight_passed=bool(self.pre and self.pre['passed']),accepted_count=len(self.steps),accepted_steps=self.steps,directions=[{k:v for k,v in r.items() if k!='FD_steps'} for r in self.records],incumbent_preserved=self.incumbent is not None,cost=cost,new_native_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT_queries=0,SEALED_queries=0,research_remaining=22758,reserve=84000,reserve_used=0,actual_baseline_s=13.66,no_lap_gain_observation=True)
   atomic_write(G/'retry/mode561_result.json',out);print(json.dumps(plain(dict(completed=out['completed'],error=error,stop_reason=stop,accepted_count=len(self.steps),cumulative_gain_ms=out.get('cumulative_gain_ms'),cost=cost)),indent=2))

if __name__=='__main__':Study().run()
