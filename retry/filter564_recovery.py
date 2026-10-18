"""Bounded trust/filter SQP with nonlinear rank/force restoration; native cap0.

Unsafe restoration centers are numerical linearization points, never incumbents.
Frozen recorded feedback is a derivative surrogate; acceptance uses fresh policy.
"""
import copy,datetime,json,math,signal,time,traceback
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
import retry.continuation563_model as base
from retry.clip561_core import atomic_write,plain,nonexempt_branch,prefix_slacks

driver=base.driver;G=base.G;D=Path('/workspace/haic-response564-private')
CAPS=dict(preparation=dict(model_ticks=300,force=1500,geometry=400,CPU_s=10,wall_s=15),local=dict(model_ticks=42000,force=170000,geometry=43000,CPU_s=600,wall_s=700),finite=dict(model_ticks=60000,force=300000,geometry=70000,CPU_s=1000,wall_s=1200),full=dict(model_ticks=120000,force=580000,geometry=140000,CPU_s=1600,wall_s=1800),verification=dict(model_ticks=1600,force=8000,geometry=1800,CPU_s=40,wall_s=60))
base.D=driver.D=D;base.CAPS=CAPS
OriginalPhase=base.Phase
class Phase(OriginalPhase):
 def __enter__(self):
  self.begin={k:self.cost[k] for k in ['force_evaluations','geometry_checks']};self.begin_tick=self.counter[0];self.cpu,self.wall=time.process_time(),time.perf_counter();self.active=True;atomic_write(D/f'{self.label}-STARTED.json',dict(contract_sha256=self.s.contract_hash))
  cpulimit=min(self.limits['CPU_s']-self.cost['CPU_s'],300 if self.name=='finite' else self.limits['CPU_s']);walllimit=min(self.limits['wall_s']-self.cost['wall_s'],350 if self.name=='finite' else self.limits['wall_s']);signal.signal(signal.SIGPROF,self.guard);signal.setitimer(signal.ITIMER_PROF,max(.01,cpulimit));signal.signal(signal.SIGALRM,self.guard);signal.setitimer(signal.ITIMER_REAL,max(.01,walllimit));self.guard();return self
 def guard(self,*a,**kw):
  super().guard(*a,**kw)
  if time.process_time()-self.s.cpu>=3300:raise RuntimeError('AGGREGATE_CPU_CAP564')
base.Phase=Phase
rd,sha,canonical=driver.rd,driver.sha,driver.canonical
INPUTS=base.INPUTS+[G/'retry/continuation563_result.json',Path('/workspace/haic-response563-private/proposal-00-00-program-private.json'),Path('/workspace/haic-response563-private/poll-00-program-private.json')]
SOURCES=['retry/filter564_recovery.py','retry/filter564_model.py',*base.SOURCES]
SCALE=np.array([.003 if j%2==0 else .03 for j in range(40)])

class Study(base.Study):
 def __init__(self):
  assert D.is_dir();previous_cost=rd(G/'retry/filter564_cost.json');prep_cost=previous_cost['phases']['preparation'];self.buckets={'preparation':dict(counter=[prep_cost['model_ticks']],cost={k:v for k,v in prep_cost.items() if k not in ['model_ticks','internal_wheel_force_evaluations']})};self.static,self.paths,self.saved,self.ledger,self.segment,self.seed,oldprefix,self.seed_suffix,self.proof=map(rd,base.INPUTS);self.old563=rd(INPUTS[-3]);assert self.old563['accepted_count']==0 and self.old563['whole_incumbent']=='seed';self.index=driver.bounds(self.static['root']['roads']);self.edge=driver.boundary_index(self.static['boundary']);self.commands={x['index']:np.array(x['action'],np.float32) for x in self.saved['commands']};self.seed_x=np.array(self.seed['x']);self.gates=[]
  for index in (54,66,75):
   row=next(r for r in self.saved['trace'] if r['index']==index and r['raw']==4);p=row['root_without_roads'];v=p['planar']['linear']['velocity'];speed=math.hypot(*v);self.gates.append(dict(index=index,point=p['center'],normal=[q/speed for q in v]))
  self.contract=dict(recovery='Preserve initial564source/contract/error/result/cost. JSONcanonical tuple-list equality fix only. Reuse saved136raw prefix after exactcanonical validation; no physics replay. Same algorithm/caps,prior CPU/wall/counters charged. Remaining phaseSTARTED reference recovery contract.',original_failure_sha256={str(p):sha(p) for p in [G/'retry/filter564_contract.json',G/'retry/filter564_result.json',G/'retry/filter564_cost.json',D/'optimization-error-private.json',D/'original-prefix-private.json']},registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',premise='Exact feasible561trajectory with562whole-safe13.22 and563independent662raw proof. Keep all original failures. Study bounded numerical progress,not universal sequential-method verdict.',program='Original551prefix1..34,tracking3/160,20variableholds35..54,fixed55..67. Same ORIGINAL551planes54,66,75 and reference. Fresh unchanged551/537feedback12holds68..79 for EACH locally-safe candidate; actual terminal75 first forward crossing objective,not frozen-policy prediction. No pose/yaw/periodic/aperture veto.',safety='Unchanged563metrics: footprint>=.50,path<=3,force<=1.059,exact strict ratio>1 prefix counts<=10%,reference overspeed<=4.85,projection continuity,all model/forecast body<100. Initial actual clipping/tracker/visited/clock preserved. Source-only unsafe numerical rollout may inform derivatives; never accept unsafe trajectory.',algorithm='Trust/filter sequential LP: normalized coordinate scales steer.003/pedal.03; radius starts1,range.125..1. Each exact feasible incumbent supplies frozen recorded actualfeedback12tape for derivatives only. 40fresh one-sided float32 FD columns per linearization. Primary LP minimizes terminaltime subject to all physical linearized slacks and sufficient perprefix rank branch. On nonlinear rejection,reconstruct active rank membership from measured trial ratios and actual violating prefixes; relinearize at that rejected point for elastic feasibility restoration,not just scalar contraction. Restoration LP1 minimizes scaled L-infinity constraint slack eta;LP2 minimizes terminaltime within eta+1e-10. Correction bounded.75rho around rejected point and within rho of safeincumbent; time worsening bound5ms is numerical-filter guard ONLY,not safety tolerance. Trial exactsource program then actualfreshfeedback validates every adoption.',restoration='At most3restoration relinearizations total,5linearizations/200FD total,3major directions,12candidate trials,4finitefeedback calls. Exactforce/prefix offending sample IDs and active sets logged. A numerical restoration center may advance only with >=20% reduction in scaled max physical/orderstat violation and frozen terminaltime<=incumbent+5ms; never becomes policy incumbent. Fresh actual feedback failure updates recorded surrogate action prefix before restoration. If restoration has no useful progress,contract radius*.5,rebuild at exact safeincumbent,with logged measured force-active samples and all force constraints;rho<.125 stops. Rank branches rebuilt at centers,not frozen no-new-clipping mask.',acceptance='Only program+freshactualfeedback all-global-safe and same terminalplane arrival improves>1microsecond. No individual5ms gate. Small safety-certified gain can become next incumbent. Fresh actual terminal nonimprovement cannot become incumbent. Two accepted gains<.02ms or2accepted prediction mismatches stop; no accepted major after max3trials or resource cap stops. No improvement expected from unsafe center.',budgets=CAPS,aggregate=dict(model_ticks=223900,force=1059500,geometry=255200,CPU_s=3300,wall_s=4000),caps=dict(linearizations=5,FD_columns=200,major_directions=3,restoration_linearizations=3,candidates=12,finite_feedback_calls=4,trials_per_major=3),finite_case=dict(model_ticks=20000,force=100000,geometry=25000,CPU_s=300,wall_s=350),proposal_reserve='Before proposals reserve one finite case20000ticks,stopoptimizationCPU>=1500. Fresh linearization requires local>=40*180+2*180. Full120000/CPU1600 and replay1600/CPU40 are separate. Local42000 coversseed180+FD36000+12trials2160+12surrogate-refresh2160=40500. Unchanged kernel hard200000 per phase.',whole='Only final new accepted finite incumbent gets ONE fresh wholefeedback suffix. Independently replay its actual complete or failed commandtape once. New wholeincumbent only if safe officialfinish<13.22;otherwise retain old562/563wholeproof. If no new incumbent,reuse existing wholeproof/independent563replay without another whole selector or redundant662raw replay.',storage='ExclusiveSTARTED,source/input hashes,atomicJSONsafe percase and phasefinally costFIRST; outerfinally costbefore result; immutable safeincumbents separately from unsafe centers. No duplicate scientific reruns.',actual_cap=0,research_remaining=22758,reserve=84000,reserve_used=0,new_seed_HOLDOUT_SEALED_other_environment_paid=0,source_sha256={p:sha(G/p) for p in SOURCES},inputs_sha256={str(p):sha(p) for p in INPUTS})
  atomic_write(G/'retry/filter564_recovery_contract.json',self.contract);self.contract_hash=sha(G/'retry/filter564_recovery_contract.json');atomic_write(D/'RECOVERY-STARTED.json',dict(contract_sha256=self.contract_hash));self.cpu,self.wall=time.process_time()-previous_cost['total']['CPU_s'],time.perf_counter()-previous_cost['total']['wall_s'];self.feedback_calls=0;self.inc=None;self.before35=None;self.prefix=None;self.linear_count=self.restoration_count=self.trial_count=0;self.events=[];self.steps=[];self.offenders=set();self.all_keys=set();self.linear_records=[]
 def checkpoint_contract(self):return self.contract_hash
 def violation(self,r):
  scale=np.array([.01 if q=='force' else 10. if q=='body' else 1. if q=='reference' else .1 for q in r['labels']]);return max(0.,float(np.max(-r['g']/scale)),float(np.max(-r['order']/.01)))
 def evaluate(self,x,label):
  frozen=self.local(x,label+'-surrogate',self.inc['suffix']);p=dict(frozen);p.update(self.metrics(frozen['states'][:133],frozen['rows'][:132]));p.update(states=frozen['states'][:133],rows=frozen['rows'][:132],handoff=frozen['handoff']);fb=new=None
  if p['physical_safe']:
   self.feedback_calls+=1;fb=self.feedback(label+'-feedback',p['handoff'],12,'finite')
   if fb['technical_error']:raise RuntimeError(fb['technical_error'])
   if fb['safe']:
    previous=p['states'][-1];progress=p['rows'][-1]['progress'];fs=[]
    for row in fb['rows']:
     root=driver.load_root(dict(row['root_without_roads'],roads=self.static['root']['roads']));row['progress_delta']=row['progress']-progress;row['projection_limit']=max(5.,2*math.dist(previous.center,root.center));previous=root;progress=row['progress'];fs.append(root)
    new=self.metrics(p['states']+fs,p['rows']+fb['rows']);new.update(x=x.copy(),program=p,feedback=fb,states=p['states']+fs,rows=p['rows']+fb['rows'],label=label,suffix=[np.array(q['action'],np.float32) for q in fb['commands']])
   else:
    tape=list(self.inc['suffix'])
    for j,q in enumerate(fb['commands'][:12]):tape[j]=np.array(q['action'],np.float32)
    frozen=self.local(x,label+'-observed-policy-surrogate',tape);frozen['surrogate_tape']=tape
  return p,fb,new,frozen
 def linearize(self,center,tape,kind,rho):
  self.linear_count+=1
  if kind=='restore':self.restoration_count+=1
  assert self.linear_count<=5 and self.restoration_count<=3
  J=[];T=[];steps=[]
  for j,v in enumerate(center['x']):
   h=1e-5 if j%2==0 else 1e-4;upper=float(np.float32(.4)) if j%2==0 else 1.;dh=h if v+h<=upper else-h
   if j%2 and ((v<=-.9)!=(v+dh<=-.9)):dh=-dh
   x=center['x'].copy();x[j]=float(np.float32(v+dh));step=x[j]-v;assert step!=0;ev=self.local(x,f'FD-{self.linear_count:02d}-{j:02d}',tape)
   if ev['times'] is None:raise RuntimeError('FD_TERMINAL_UNBRACKETED')
   J.append((ev['g']-center['g'])/step);T.append((ev['times']-center['times'])/step);steps.append(step)
  jac=np.array(J).T*SCALE;timejac=np.array(T).T*SCALE;force=np.flatnonzero(np.array(center['labels'])=='force');ids=nonexempt_branch(center['ratios'],*self.before35['tracking']);badforce=np.flatnonzero(center['ratios']>1.059);self.offenders.update(map(int,badforce));badprefix=np.flatnonzero(center['order']<0);clips=np.flatnonzero(center['ratios']>1);repair_samples=[]
  for raw in badprefix:
   n=4*(raw+1);k=(160+n)//10-3;rank=np.argsort(-center['ratios'][:n],kind='stable');repair_samples.extend(map(int,rank[k:][center['ratios'][rank[k:]]>1]))
  record=dict(number=self.linear_count,kind=kind,center_label=center['label'],center_safe_incumbent=center is self.inc,center_violation=self.violation(center),rho=rho,rank_nonexempt_ids=ids.tolist(),force_offenders=badforce.tolist(),violated_prefix_raws=(badprefix+1).tolist(),prefix_repair_sample_ids=sorted(set(repair_samples)),FD_steps=steps)
  self.linear_records.append(record);atomic_write(D/f'linearization-{self.linear_count:02d}-private.json',record)
  return dict(J=jac,T=timejac,force=force,ids=ids,record=record)
 def solve(self,center,linear,rho,restore):
  J,T,force,ids=linear['J'],linear['T'],linear['force'],linear['ids'];rr=-J[force];ids=np.asarray(ids,dtype=int);scale=np.array([.01 if q=='force' else 10. if q=='body' else 1. if q=='reference' else .1 for q in center['labels']]);buffer=np.minimum(1e-5,.25*np.maximum(0.,1-center['ratios'][ids]));A=np.vstack([-J,rr[ids]]);b=np.r_[center['g'],1-buffer-center['ratios'][ids]];vscale=np.r_[scale,np.full(len(ids),.01)];offset=(center['x']-self.inc['x'])/SCALE;bound=[]
  for j,v in enumerate(center['x']):
   lo,hi=(-float(np.float32(.4)),float(np.float32(.4))) if j%2==0 else(-1.,1.);r=.75*rho if restore else rho;bound.append((max((lo-v)/SCALE[j],-r,-rho-offset[j]),min((hi-v)/SCALE[j],r,rho-offset[j])))
  if any(a>b for a,b in bound):return None,dict(reason='EMPTY_TRUST_INTERSECTION')
  meta=dict(restoration=restore,rank_plus_offender_samples=len(ids),active_force_samples=sorted(self.offenders))
  if restore:
   # A normalized elastic feasibility LP, then time minimization at its best eta.
   el=linprog(np.r_[np.zeros(40),1.],A_ub=np.c_[A,-vscale],b_ub=b,bounds=bound+[(0.,None)],method='highs');meta.update(elastic_success=bool(el.success),elastic_status=int(el.status))
   if not el.success:return None,meta
   eta=float(el.x[-1]);meta['predicted_violation_eta']=eta;b=b+vscale*(eta+1e-10)
   A=np.vstack([A,T[2]]);b=np.r_[b,self.inc['times'][2]+.005-center['times'][2]]
  lp=linprog(T[2],A_ub=A,b_ub=b,bounds=bound,method='highs');meta.update(success=bool(lp.success),status=int(lp.status))
  if not lp.success:return None,meta
  x=np.array([float(np.float32(v)) for v in center['x']+SCALE*lp.x]);meta.update(predicted_plane_times_s=(center['times']+T@((x-center['x'])/SCALE)).tolist(),step_norm=float(np.max(abs((x-center['x'])/SCALE))))
  return x,meta
 def room(self,linear=False):
  return time.process_time()-self.cpu<1500 and self.trial_count<12 and self.feedback_calls<4 and self.buckets.get('finite',dict(counter=[0]))['counter'][0]+20000<=60000 and self.buckets['local']['counter'][0]+(40*180+2*180 if linear else 2*180)<=42000
 def run(self):
  out={};error=None;stop=None;seed=None;full=None;verification=[];small=bad=0
  try:
   stored=rd(D/'original-prefix-private.json');q=stored['checkpoint'];state=dict(root=driver.load_root(dict(q['root_without_roads'],roads=self.static['root']['roads'])),visited=set(q['visited']),tracker=driver.FinishLineTracker(**q['tracker']),elapsed=q['elapsed'],global_raw=q['global_raw'],progress=q['progress'],launch=q['launch'],tracking=q['tracking']);self.prefix=dict(stored,state=state)
   assert self.prefix['failure'] is None and len(self.prefix['rows'])==136;assert all(canonical(a['root_without_roads'])==b['root_without_roads'] and canonical(a['forces'])==b['forces'] for a,b in zip(self.prefix['rows'],self.saved['trace'][:136]));self.before35=self.prefix['state'];tape=[np.array(q['action'],np.float32) for q in self.seed_suffix['commands'][:12]];seed=self.local(self.seed_x,'seed',tape);expected=self.seed['rows']+self.seed_suffix['rows'][:48];assert seed['physical_safe'] and seed['times'] is not None and all(canonical(a['root_without_roads'])==b['root_without_roads'] and canonical(a['forces'])==b['forces'] for a,b in zip(seed['rows'],expected));program=dict(seed);program.update(states=seed['states'][:133],rows=seed['rows'][:132]);seed.update(program=program,feedback=None,suffix=tape,label='seed');self.retain(seed,0)
   # Prior rejected source samples seed actual force cuts, not a no-new-clipping mask.
   for path in INPUTS[-2:]:self.offenders.update(map(int,np.flatnonzero(np.array(rd(path)['ratios'])>1.059)))
   rho=1.
   for major in range(3):
    if self.linear_count>=5 or not self.room(True):stop='OPTIMIZATION_RESERVE';break
    center=self.inc;active_tape=self.inc['suffix'];restore=False;accepted=False;linear=self.linearize(center,active_tape,'improve',rho)
    for trial in range(3):
     if not self.room():stop='OPTIMIZATION_RESERVE';break
     x,meta=self.solve(center,linear,rho,restore);label=f'trial-{major:02d}-{trial:02d}'
     if x is None or x.tobytes() in self.all_keys or np.array_equal(x,self.inc['x']):
      self.events.append(dict(label=label,LP=meta,evaluated=False,reason='LP_FAIL_OR_DUPLICATE_OR_ZERO'));rho*=.5
      if rho<.125:stop='MIN_RADIUS';break
      center=self.inc;active_tape=self.inc['suffix'];restore=False
      if self.linear_count>=5 or not self.room(True):stop='LINEARIZATION_OR_RESERVE';break
      linear=self.linearize(center,active_tape,'improve',rho);continue
     self.all_keys.add(x.tobytes());self.trial_count+=1;p,fb,new,frozen=self.evaluate(x,label);pred=1000*(self.inc['times']-np.array(meta['predicted_plane_times_s']));event=self.event('restoration' if restore else'trust_time',self.inc,p,fb,new,pred/1000);v=self.violation(frozen);origin_v=self.violation(center);delta=x-self.inc['x'];prior=center['x']-self.inc['x'];cos=float(delta@prior/(np.linalg.norm(delta)*np.linalg.norm(prior))) if np.linalg.norm(delta)*np.linalg.norm(prior)>0 else None;event.update(label=label,major=major+1,trial=trial+1,evaluated=True,LP=meta,rho=rho,frozen_violation=v,center_violation=origin_v,cosine_vs_rejected_direction=cos,local_program_safe=p['physical_safe']);self.events.append(event);atomic_write(D/(label+'-decision-private.json'),event)
     self.offenders.update(map(int,np.flatnonzero(frozen['ratios']>1.059)))
     if event['accepted']:
      gain=self.inc['times'][2]-new['times'][2];self.steps.append(event);self.retain(new,len(self.steps));small=small+1 if gain<2e-5 else 0;bad=0 if event['agreement'] else bad+1;accepted=True
      if event['agreement']:rho=min(1.,rho*1.5)
      else:rho=max(.125,rho*.5)
      if small>=2:stop='TWO_SMALL_ACCEPTED_GAINS'
      if bad>=2:stop='TWO_ACCEPTED_PREDICTION_MISMATCHES'
      break
     if trial==2:break
     # Recenter on measured rejection only when filter merit improves or this is first restoration.
     usecenter=frozen['times'] is not None and v>0 and (not restore or v<=.8*origin_v) and frozen['times'][2]<=self.inc['times'][2]+.005
     if usecenter and self.restoration_count<3 and self.linear_count<5 and self.room(True):
      center=frozen;center['label']=label+'-unsafe-restoration-center';active_tape=frozen.get('surrogate_tape',self.inc['suffix']);restore=True;linear=self.linearize(center,active_tape,'restore',rho)
     else:
      rho*=.5
      if rho<.125:stop='MIN_RADIUS';break
      center=self.inc;active_tape=self.inc['suffix'];restore=False
      if self.linear_count>=5 or not self.room(True):stop='LINEARIZATION_OR_RESERVE';break
      linear=self.linearize(center,active_tape,'improve',rho)
    if stop:break
    if not accepted:stop='NO_ACCEPTED_GAIN_WITHIN3_TRIALS';break
   if stop is None:stop='MAJOR_LIMIT3'
  except BaseException as e:error=type(e).__name__+':'+str(e);atomic_write(D/'recovery-optimization-error-private.json',dict(error=error,traceback=traceback.format_exc()))
  finally:
   try:
    if self.inc is not None:
     reused=np.array_equal(self.inc['x'],self.seed_x);new_best=False
     if not reused:
      full=self.feedback('final-full-feedback',self.inc['program']['handoff'],300,'full');tape={i:a for i,a in self.commands.items() if i<=34};tape.update({35+j:a for j,a in enumerate(self.program_actions(self.inc['x']))});tape.update({q['index']:np.array(q['action'],np.float32) for q in full['commands']});expected=self.prefix['rows']+self.inc['program']['rows']+full['rows']
      with Phase(self,'verification','final-tape') as phase:vr=self.run_commands('final-tape',self.initial(),tape,phase)
      exact=len(vr['rows'])==len(expected) and all(canonical(a.get('root_without_roads',a.get('before_root_without_roads')))==canonical(b.get('root_without_roads',b.get('before_root_without_roads'))) and a['forces']==b['forces'] for a,b in zip(vr['rows'],expected));cp=canonical(self.checkpoint(vr['state']))==canonical(self.checkpoint(full['state']));assert exact and cp;verification.append(dict(raw=len(vr['rows']),fullstate_force_exact=exact,checkpoint_exact=cp,safe_finish=vr['safe_finish'],finish_s=vr['finish_s']));new_best=bool(full['safe_finish'] and full['finish_s']<self.proof['whole_source_finish_s']-1e-9)
      if full['technical_error']:error=(error+';' if error else'')+'FULL:'+full['technical_error']
     out.update(final_finite_incumbent=self.inc['label'],finite_plane_times_s=self.inc['times'].tolist(),finite_cumulative_gain_ms=(1000*(seed['times']-self.inc['times'])).tolist(),whole_attempt_safe_finish=full['safe_finish'] if full else None,whole_attempt_finish_s=full['finish_s'] if full else None,whole_attempt_failure=full['failure']['reason'] if full and full['failure'] else None,whole_incumbent='new' if new_best else'seed',whole_incumbent_finish_s=full['finish_s'] if new_best else self.proof['whole_source_finish_s'],whole_gain_vs551_ms=1000*(self.saved['summary']['model_finish_episode_s']-(full['finish_s'] if new_best else self.proof['whole_source_finish_s'])),existing_whole_proof_reused=not new_best,no_redundant_seed_replay=True,independent_verification=verification)
   except BaseException as e:error=(error+';' if error else'')+'FINAL:'+type(e).__name__+':'+str(e);atomic_write(D/'recovery-final-error-private.json',dict(error=error,traceback=traceback.format_exc()))
   phases={k:dict(v['cost'],model_ticks=v['counter'][0],internal_wheel_force_evaluations=4*v['counter'][0]) for k,v in self.buckets.items()};total={k:sum(p[k] for p in phases.values()) for k in ['model_ticks','force_evaluations','internal_wheel_force_evaluations','geometry_checks','body_checks']};total.update(CPU_s=time.process_time()-self.cpu,wall_s=time.perf_counter()-self.wall);atomic_write(G/'retry/filter564_recovery_cost.json',dict(phases=phases,total=total));out.update(completed=error is None,error=error,stop_reason=stop,accepted_count=len(self.steps),steps=self.steps,events=self.events,linearizations=self.linear_count,restoration_linearizations=self.restoration_count,FD_columns=40*self.linear_count,candidates=self.trial_count,finite_feedback_calls=self.feedback_calls,seed_plane_times_s=seed['times'].tolist() if seed else None,seed_whole_finish_s=self.proof['whole_source_finish_s'],cost=total,phase_costs=phases,new_native_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT_queries=0,SEALED_queries=0,reserve_used=0,research_remaining=22758,reserve=84000,actual_baseline_s=13.66,prior561_aperture_failure_preserved=True,no_native_gain_observation=True);atomic_write(G/'retry/filter564_recovery_result.json',out);print(json.dumps(plain(out),indent=2))

if __name__=='__main__':
 from core.vendor.car_racing import CarRacing
 def forbidden(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN')
 CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden
 Study().run()
