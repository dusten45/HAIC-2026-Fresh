"""Fixed empirical interior targets, nonlinear restoration, fresh policy acceptance."""
import copy,datetime,json,math,signal,time,traceback
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
import retry.filter564_model as algorithm
from retry.clip561_core import atomic_write,plain,nonexempt_branch,prefix_slacks
base=algorithm.base;driver=base.driver;G=base.G;D=Path('/workspace/haic-response565-private')
CAPS=dict(preparation=dict(model_ticks=300,force=1500,geometry=400,CPU_s=10,wall_s=15),local=dict(model_ticks=62000,force=250000,geometry=63000,CPU_s=800,wall_s=950),finite=dict(model_ticks=60000,force=300000,geometry=70000,CPU_s=900,wall_s=1050),full=dict(model_ticks=120000,force=580000,geometry=140000,CPU_s=1500,wall_s=1700),verification=dict(model_ticks=1600,force=8000,geometry=1800,CPU_s=40,wall_s=60))
base.D=driver.D=algorithm.D=D;base.CAPS=CAPS
class Phase(algorithm.OriginalPhase):
 def __enter__(self):
  self.begin={k:self.cost[k] for k in ['force_evaluations','geometry_checks']};self.begin_tick=self.counter[0];self.cpu,self.wall=time.process_time(),time.perf_counter();self.active=True;atomic_write(D/f'{self.label}-STARTED.json',dict(contract_sha256=self.s.contract_hash));cpulimit=min(self.limits['CPU_s']-self.cost['CPU_s'],300 if self.name=='finite' else self.limits['CPU_s']);walllimit=min(self.limits['wall_s']-self.cost['wall_s'],350 if self.name=='finite' else self.limits['wall_s']);signal.signal(signal.SIGPROF,self.guard);signal.setitimer(signal.ITIMER_PROF,max(.01,cpulimit));signal.signal(signal.SIGALRM,self.guard);signal.setitimer(signal.ITIMER_REAL,max(.01,walllimit));self.guard();return self
 def guard(self,*a,**kw):
  super().guard(*a,**kw)
  if time.process_time()-self.s.cpu>=3300:raise RuntimeError('AGGREGATE_CPU565')
base.Phase=Phase
rd,sha,canonical=driver.rd,driver.sha,driver.canonical
SCALE=algorithm.SCALE
INPUTS=base.INPUTS+[Path('/workspace/haic-response564-private/trial-00-02-surrogate-private.json'),G/'retry/interior565_design.json',D/'interior-targets-private.json',G/'retry/continuation563_result.json',G/'retry/filter564_recovery_result.json']
SOURCES=['retry/interior565_model.py','retry/interior565_design.py','retry/filter564_model.py',*base.SOURCES]

class Study(algorithm.Study):
 def __init__(self):
  assert D.is_dir();self.buckets={};self.static,self.paths,self.saved,self.ledger,self.segment,self.seed,oldprefix,self.seed_suffix,self.proof=map(rd,base.INPUTS);self.last=rd(INPUTS[-5]);self.design=rd(INPUTS[-4]);self.targets=rd(INPUTS[-3]);self.margin=np.array(self.targets['physical']);self.prefix_margin=np.array(self.targets['prefix']);self.index=driver.bounds(self.static['root']['roads']);self.edge=driver.boundary_index(self.static['boundary']);self.commands={x['index']:np.array(x['action'],np.float32) for x in self.saved['commands']};self.seed_x=np.array(self.seed['x']);self.gates=[]
  assert sha(INPUTS[-3])==self.design['private_targets_sha256']
  for index in (54,66,75):
   row=next(r for r in self.saved['trace'] if r['index']==index and r['raw']==4);p=row['root_without_roads'];v=p['planar']['linear']['velocity'];speed=math.hypot(*v);self.gates.append(dict(index=index,point=p['center'],normal=[q/speed for q in v]))
  self.contract=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',question='Can fixed positive empirical interior goals repair final564nonlinear infeasibility,then actual unchangedfeedback safely improve terminal time? Separate safe finite program,actualfeedback finite success,wholefinish.',interior_rule=self.design['rule'],interior_immutable_sha256=sha(INPUTS[-3]),interior_scope='Physical slack margins and prefix-orderstat margins are coordinatewise arrays fixed from final TWO564restoration predictions and fullfloat32ULP propagation. No buffer trials,rounding,threshold relaxation or online buffer enlargement. These are numerical targets,not physical constants or universal error bounds.',start='Fresh exact original551prefix136raw,seed180raw verified against561+562;fresh final564point180raw must match saved states/forces before derivatives. Same20variableholds35..54,fixed55..67,initialtracking3/160,reference and original551planes54/66/75. Seed is safe policy incumbent;unsafe restoration centers remain numerical only.',safety='Unchanged563physical/strict-prefix gates,launch history and all forecastbody<100. Locally-safe program only opens fresh unchanged551/537feedback12hold68..79. Exact ratio>1,never round small positives tozero. Same tracker/visited/clock. Actualcontinuation safety+terminal gain>1microsecond to adopt. No5ms individual gate.',method='Start at exact last564unsafe point with frozen seedfeedback derivative tape. Fresh40float32FD per linearization. At each prefix,rank topK exemptions and require remaining ratios<=1-fixedprefixmargin;union uses maximum applicable prefix margin per sample. All physical linearizedslacks>=fixedphysicalmargin. Restoration LP1 min scaled elastic eta;eta>1e-8 stops as linearized internal-target infeasible in currenttrust,not proof nonlinear infeasibility. LP2 minimizes normalizedL1 movement at besteta (feasibility first),with frozen terminal<=bestincumbent+5ms numericfilter. After exactsafe actualcontinuation,run terminaltime LP under same fixedinterior goals. Numerical radius starts1,range.125..1,scales steer.003/pedal.03;correctionwithin.5rho ofcenter andrho ofsafeincumbent. Recompute rank membership and log difference vsseed.',progress='Up to8linearizations/FD320,6restorationlinearizations,10sourceproposals,4finitefeedbackcalls,2safe time-improving accepts. No arbitrary three-trialstop. Continue residual reduction while >=10%;two consecutive nondecreasing restoration steps stop. If insufficient reduction,contractradius*.5 and relinearize bestobserved numericalcenter;rho<.125 stops. Unsafe center may advance only on measured interior merit improvement;physical/adoptedincumbent remains safe. A safe-but-nonimproving finite point may be a working linearization point,but not best policy incumbent. Two nonimproving safe time attempts or2acceptedpredictionmismatches stop. Duplicate/quantizedzerostep stops.',budgets=CAPS,aggregate=dict(model_ticks=243900,force=1139500,geometry=275200,CPU_s=3300,wall_s=4000),caps=dict(linearizations=8,FD_columns=320,restorations=6,candidates=10,finite_feedback_calls=4,accepted=2),finite_case=dict(model_ticks=20000,force=100000,geometry=25000,CPU_s=300,wall_s=350),reserve_rule='Optimization stopCPU>=1650;before proposal reserve one finitecase20000ticks;beforeFD reserve7200+2*180localticks. Local62000 coversseed+starting360+FD57600+10proposals1800+10refresh1800=61560. Full120000/CPU1500 and independenttape1600/CPU40 reserved separately. No newincumbent ->reuse completed562/563wholeproof,do not repeat whole selector/replay.',whole='Final NEW finiteincumbent only:one fresh whole existingfeedback suffix and one independent actualtape replay fromreset. Newwholeincumbent only safe officialfinish<13.22;otherwise retain existingwholeproof. Source estimates are not native/pixel records.',storage='ExclusiveSTARTED;frozen sources/inputs;atomicJSONsafe percase+phasefinallycostFIRST+outercostbefore result;private raw states/actions/FD,tapes. Initial564tuple-list failure preserved;565uses canonical comparisons.',actual_cap=0,new_seed_HOLDOUT_SEALED_other_environment_paid=0,research_remaining=22758,reserve=84000,reserve_used=0,source_sha256={p:sha(G/p) for p in SOURCES},inputs_sha256={str(p):sha(p) for p in INPUTS})
  atomic_write(G/'retry/interior565_contract.json',self.contract);self.contract_hash=sha(G/'retry/interior565_contract.json');atomic_write(D/'STARTED.json',dict(contract_sha256=self.contract_hash));self.cpu,self.wall=time.process_time(),time.perf_counter();self.feedback_calls=0;self.inc=None;self.before35=None;self.prefix=None;self.linear_count=self.restoration_count=self.trial_count=0;self.events=[];self.steps=[];self.offenders=set();self.all_keys=set();self.linear_records=[];self.safe_programs=self.safe_finite=0;self.current_tape=None
 def interior_violation(self,r):
  scale=np.array([.01 if q=='force' else 10. if q=='body' else 1. if q=='reference' else .1 for q in r['labels']]);return max(0.,float(np.max((self.margin-r['g'])/scale)),float(np.max((self.prefix_margin-r['order'])/.01)))
 def linearize(self,center,tape,kind,rho):
  self.linear_count+=1;self.restoration_count+=kind=='restore';assert self.linear_count<=8 and self.restoration_count<=6;J=[];T=[];steps=[]
  for j,v in enumerate(center['x']):
   h=1e-5 if j%2==0 else 1e-4;upper=float(np.float32(.4)) if j%2==0 else 1.;dh=h if v+h<=upper else-h
   if j%2 and ((v<=-.9)!=(v+dh<=-.9)):dh=-dh
   x=center['x'].copy();x[j]=float(np.float32(v+dh));step=x[j]-v;assert step!=0;ev=self.local(x,f'FD-{self.linear_count:02d}-{j:02d}',tape)
   if ev['times'] is None:raise RuntimeError('FD_TERMINAL_UNBRACKETED')
   J.append((ev['g']-center['g'])/step);T.append((ev['times']-center['times'])/step);steps.append(step)
  ids=nonexempt_branch(center['ratios'],3,160);badforce=np.flatnonzero(center['ratios']>1.059);badprefix=np.flatnonzero(center['order']<0);record=dict(number=self.linear_count,kind=kind,center_label=center['label'],center_is_incumbent=center is self.inc,center_global_safe=center['physical_safe'],interior_violation=self.interior_violation(center),physical_violation=self.violation(center),rho=rho,rank_nonexempt_ids=ids.tolist(),rank_membership_difference_vsseed=len(set(ids)^set(self.seed_rank)),force_offenders=badforce.tolist(),violated_prefix_raws=(badprefix+1).tolist(),FD_steps=steps);atomic_write(D/f'linearization-{self.linear_count:02d}-private.json',record);self.linear_records.append(record)
  return dict(J=np.array(J).T*SCALE,T=np.array(T).T*SCALE,force=np.flatnonzero(np.array(center['labels'])=='force'),record=record)
 def solve(self,center,linear,rho,restore):
  J,T,force=linear['J'],linear['T'],linear['force'];rr=-J[force];clipmargin={}
  for raw,margin in enumerate(self.prefix_margin):
   n=4*(raw+1);k=(160+n)//10-3;rank=np.argsort(-center['ratios'][:n],kind='stable')
   for i in rank[max(0,k):]:clipmargin[int(i)]=max(clipmargin.get(int(i),0.),margin)
  ids=np.array(sorted(clipmargin),int);cm=np.array([clipmargin[int(i)] for i in ids]);A=np.vstack([-J,rr[ids]]);b=np.r_[center['g']-self.margin,1-cm-center['ratios'][ids]];vscale=np.r_[[.01 if q=='force' else 10. if q=='body' else 1. if q=='reference' else .1 for q in center['labels']],np.full(len(ids),.01)];offset=(center['x']-self.inc['x'])/SCALE;bound=[]
  for j,v in enumerate(center['x']):
   lo,hi=(-float(np.float32(.4)),float(np.float32(.4))) if j%2==0 else(-1.,1.);r=.5*rho if restore else rho;bound.append((max((lo-v)/SCALE[j],-r,-rho-offset[j]),min((hi-v)/SCALE[j],r,rho-offset[j])))
  meta=dict(restoration=restore,rank_samples=len(ids),interior_sha256=self.contract['interior_immutable_sha256'])
  if any(lo>hi for lo,hi in bound):return None,dict(meta,reason='EMPTY_TRUST_INTERSECTION')
  el=linprog(np.r_[np.zeros(40),1.],A_ub=np.c_[A,-vscale],b_ub=b,bounds=bound+[(0.,None)],method='highs');meta.update(elastic_success=bool(el.success),elastic_status=int(el.status))
  if not el.success:return None,dict(meta,reason='ELASTIC_LP_FAIL')
  eta=float(el.x[-1]);meta['eta']=eta
  if eta>1e-8:return None,dict(meta,reason='LINEARIZED_INTERNAL_TARGET_UNATTAINABLE')
  # Fixed targets are not loosened by the elastic solver at its optimum.
  if restore:
   # Min L1 of normalized correction,subject to every interior affine target.
   Az=np.c_[A,np.zeros((len(A),40))];I=np.eye(40);Az=np.vstack([Az,np.c_[I,-I],np.c_[-I,-I],np.r_[T[2],np.zeros(40)]]);bz=np.r_[b,np.zeros(80),self.inc['times'][2]+.005-center['times'][2]];lp=linprog(np.r_[np.zeros(40),np.ones(40)],A_ub=Az,b_ub=bz,bounds=bound+[(0.,None)]*40,method='highs')
  else:lp=linprog(T[2],A_ub=A,b_ub=b,bounds=bound,method='highs')
  meta.update(success=bool(lp.success),status=int(lp.status))
  if not lp.success:return None,dict(meta,reason='INTERIOR_SECOND_LP_FAIL')
  x=np.array([float(np.float32(v)) for v in center['x']+SCALE*lp.x[:40]]);meta.update(predicted_plane_times_s=(center['times']+T@((x-center['x'])/SCALE)).tolist(),normalized_correction=float(max(abs((x-center['x'])/SCALE))));return x,meta
 def evaluate(self,x,label):
  frozen=self.local(x,label+'-surrogate',self.current_tape);p=dict(frozen);p.update(self.metrics(frozen['states'][:133],frozen['rows'][:132]));p.update(states=frozen['states'][:133],rows=frozen['rows'][:132],handoff=frozen['handoff']);fb=new=None
  if p['physical_safe']:
   self.safe_programs+=1;self.feedback_calls+=1;fb=self.feedback(label+'-feedback',p['handoff'],12,'finite')
   if fb['technical_error']:raise RuntimeError(fb['technical_error'])
   if fb['safe']:
    fs=[];previous=p['states'][-1];progress=p['rows'][-1]['progress']
    for row in fb['rows']:
     root=driver.load_root(dict(row['root_without_roads'],roads=self.static['root']['roads']));row['progress_delta']=row['progress']-progress;row['projection_limit']=max(5.,2*math.dist(previous.center,root.center));previous=root;progress=row['progress'];fs.append(root)
    new=self.metrics(p['states']+fs,p['rows']+fb['rows']);new.update(x=x.copy(),program=p,feedback=fb,states=p['states']+fs,rows=p['rows']+fb['rows'],label=label,suffix=[np.array(q['action'],np.float32) for q in fb['commands']]);self.safe_finite+=int(new['physical_safe'])
   else:
    tape=list(self.current_tape)
    for j,q in enumerate(fb['commands'][:12]):tape[j]=np.array(q['action'],np.float32)
    frozen=self.local(x,label+'-observed-policy-surrogate',tape);frozen['surrogate_tape']=tape
  return p,fb,new,frozen
 def room(self,linear=False):return time.process_time()-self.cpu<1650 and self.trial_count<10 and self.feedback_calls<4 and self.buckets.get('finite',dict(counter=[0]))['counter'][0]+20000<=60000 and self.buckets['local']['counter'][0]+(40*180+2*180 if linear else 2*180)<=62000
 def run(self):
  out={};error=None;stop=None;seed=None;full=None;verification=[];stale=bad=safe_stale=0
  try:
   with Phase(self,'preparation','prefix') as phase:self.prefix=self.run_commands('original-prefix',self.initial(),{i:a for i,a in self.commands.items() if i<=34},phase)
   assert self.prefix['failure'] is None and len(self.prefix['rows'])==136;assert all(canonical(a['root_without_roads'])==b['root_without_roads'] and canonical(a['forces'])==b['forces'] for a,b in zip(self.prefix['rows'],self.saved['trace'][:136]));self.before35=self.prefix['state'];self.current_tape=[np.array(q['action'],np.float32) for q in self.seed_suffix['commands'][:12]];seed=self.local(self.seed_x,'seed',self.current_tape);expected=self.seed['rows']+self.seed_suffix['rows'][:48];assert seed['physical_safe'] and seed['times'] is not None and all(canonical(a['root_without_roads'])==b['root_without_roads'] and canonical(a['forces'])==b['forces'] for a,b in zip(seed['rows'],expected));program=dict(seed);program.update(states=seed['states'][:133],rows=seed['rows'][:132]);seed.update(program=program,feedback=None,suffix=self.current_tape,label='seed');self.retain(seed,0);self.seed_rank=nonexempt_branch(seed['ratios'],3,160)
   center=self.local(np.array(self.last['x']),'starting-restoration',self.current_tape);assert all(canonical(a['root_without_roads'])==b['root_without_roads'] and canonical(a['forces'])==b['forces'] for a,b in zip(center['rows'],self.last['rows']));rho=1.;restore=True;bestcenter=center;besttape=self.current_tape
   for iteration in range(8):
    if not self.room(True):stop='OPTIMIZATION_RESERVE';break
    if restore and self.restoration_count>=6:stop='RESTORATION_LIMIT6';break
    linear=self.linearize(center,self.current_tape,'restore' if restore else'improve',rho);x,meta=self.solve(center,linear,rho,restore);label=f'trial-{iteration:02d}'
    if x is None:self.events.append(dict(label=label,evaluated=False,LP=meta));stop=meta.get('reason','LP_FAIL');break
    if x.tobytes() in self.all_keys or np.array_equal(x,center['x']):self.events.append(dict(label=label,evaluated=False,LP=meta));stop='QUANTIZED_ZERO_OR_DUPLICATE';break
    self.all_keys.add(x.tobytes());self.trial_count+=1;p,fb,new,frozen=self.evaluate(x,label);pred=self.inc['times']-np.array(meta['predicted_plane_times_s']);event=self.event('interior_restore' if restore else'interior_time',self.inc,p,fb,new,pred);vi=self.interior_violation(frozen);oldvi=self.interior_violation(center);event.update(label=label,evaluated=True,LP=meta,rho=rho,center_interior_violation=oldvi,trial_interior_violation=vi,trial_global_violation=self.violation(frozen),internal_target_sha256=self.contract['interior_immutable_sha256']);self.events.append(event);atomic_write(D/(label+'-decision-private.json'),event)
    if new is not None and new['physical_safe']:
     atomic_write(D/(label+'-exact-feasible-private.json'),dict(x=x,actual_times_s=new['times'],handoff=self.checkpoint(p['handoff']),terminal_checkpoint=self.checkpoint(fb['state']),adopted=event['accepted']))
     if event['accepted']:
      self.steps.append(event);self.retain(new,len(self.steps));bad=0 if event['agreement'] else bad+1;safe_stale=0
      if len(self.steps)>=2:stop='ACCEPT_LIMIT2';break
      if bad>=2:stop='TWO_ACCEPTED_PREDICTION_MISMATCHES';break
     else:
      safe_stale+=1
      if not restore and safe_stale>=2:stop='TWO_SAFE_TIME_NONIMPROVEMENTS';break
     center=new;self.current_tape=new['suffix'];bestcenter=center;besttape=self.current_tape;restore=False;stale=0;continue
    if not restore or vi<=.9*oldvi:
     center=frozen;center['label']=label+'-numerical-center';self.current_tape=frozen.get('surrogate_tape',self.current_tape);restore=True;stale=0
     if vi<self.interior_violation(bestcenter):bestcenter=center;besttape=self.current_tape
    else:
     stale+=1
     if stale>=2:stop='TWO_NONDECREASING_RESTORATIONS';break
     rho*=.5
     if rho<.125:stop='MIN_RADIUS';break
     center=bestcenter;self.current_tape=besttape;restore=True
   if stop is None:stop='LINEARIZATION_LIMIT8'
  except BaseException as e:error=type(e).__name__+':'+str(e);atomic_write(D/'optimization-error-private.json',dict(error=error,traceback=traceback.format_exc()))
  finally:
   try:
    if self.inc is not None:
     reused=np.array_equal(self.inc['x'],self.seed_x);new_best=False
     if not reused:
      full=self.feedback('final-full-feedback',self.inc['program']['handoff'],300,'full');tape={i:a for i,a in self.commands.items() if i<=34};tape.update({35+j:a for j,a in enumerate(self.program_actions(self.inc['x']))});tape.update({q['index']:np.array(q['action'],np.float32) for q in full['commands']});expected=self.prefix['rows']+self.inc['program']['rows']+full['rows']
      with Phase(self,'verification','final-tape') as phase:vr=self.run_commands('final-tape',self.initial(),tape,phase)
      exact=len(vr['rows'])==len(expected) and all(canonical(a.get('root_without_roads',a.get('before_root_without_roads')))==canonical(b.get('root_without_roads',b.get('before_root_without_roads'))) and canonical(a['forces'])==canonical(b['forces']) for a,b in zip(vr['rows'],expected));cp=canonical(self.checkpoint(vr['state']))==canonical(self.checkpoint(full['state']));assert exact and cp;verification.append(dict(raw=len(vr['rows']),fullstate_force_exact=exact,checkpoint_exact=cp,safe_finish=vr['safe_finish'],finish_s=vr['finish_s']));new_best=bool(full['safe_finish'] and full['finish_s']<self.proof['whole_source_finish_s']-1e-9)
      if full['technical_error']:error=(error+';' if error else'')+'FULL:'+full['technical_error']
     out.update(final_finite_incumbent=self.inc['label'],finite_plane_times_s=self.inc['times'].tolist(),finite_cumulative_gain_ms=(1000*(seed['times']-self.inc['times'])).tolist(),whole_attempt_safe_finish=full['safe_finish'] if full else None,whole_attempt_finish_s=full['finish_s'] if full else None,whole_attempt_failure=full['failure']['reason'] if full and full['failure'] else None,whole_incumbent='new' if new_best else'seed',whole_incumbent_finish_s=full['finish_s'] if new_best else self.proof['whole_source_finish_s'],whole_gain_vs551_ms=1000*(self.saved['summary']['model_finish_episode_s']-(full['finish_s'] if new_best else self.proof['whole_source_finish_s'])),existing_whole_proof_reused=not new_best,no_redundant_seed_replay=True,independent_verification=verification)
   except BaseException as e:error=(error+';' if error else'')+'FINAL:'+type(e).__name__+':'+str(e);atomic_write(D/'final-error-private.json',dict(error=error,traceback=traceback.format_exc()))
   phases={k:dict(v['cost'],model_ticks=v['counter'][0],internal_wheel_force_evaluations=4*v['counter'][0]) for k,v in self.buckets.items()};total={k:sum(p[k] for p in phases.values()) for k in ['model_ticks','force_evaluations','internal_wheel_force_evaluations','geometry_checks','body_checks']};total.update(CPU_s=time.process_time()-self.cpu,wall_s=time.perf_counter()-self.wall);atomic_write(G/'retry/interior565_cost.json',dict(phases=phases,total=total));out.update(completed=error is None,error=error,stop_reason=stop,accepted_count=len(self.steps),steps=self.steps,events=self.events,linearizations=self.linear_count,restoration_linearizations=self.restoration_count,FD_columns=40*self.linear_count,candidates=self.trial_count,safe_programs=self.safe_programs,safe_finite_continuations=self.safe_finite,finite_feedback_calls=self.feedback_calls,rank_membership_differences=[q['rank_membership_difference_vsseed'] for q in self.linear_records],seed_plane_times_s=seed['times'].tolist() if seed else None,seed_whole_finish_s=self.proof['whole_source_finish_s'],cost=total,phase_costs=phases,new_native_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT_queries=0,SEALED_queries=0,reserve_used=0,research_remaining=22758,reserve=84000,actual_baseline_s=13.66,prior561_aperture_failure_preserved=True,no_native_gain_observation=True);atomic_write(G/'retry/interior565_result.json',out);print(json.dumps(plain(out),indent=2))

if __name__=='__main__':
 from core.vendor.car_racing import CarRacing
 def forbidden(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN')
 CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden
 Study().run()
