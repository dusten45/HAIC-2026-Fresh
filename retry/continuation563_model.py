"""Sequential source improvement with actual feedback continuation terminal cost.

Frozen incumbent feedback tape is a derivative surrogate ONLY. Every proposal
uses newly recomputed policy; finite and whole-lap incumbents are distinguished.
"""
import copy,datetime,hashlib,json,math,signal,time,traceback
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
import retry.handoff562_model as driver
from retry.clip561_core import atomic_write,plain,prefix_slacks,nonexempt_branch,order_slack
from retry.transcribe559_model import vector

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response563-private');driver.D=D
rd,sha,short,canonical=driver.rd,driver.sha,driver.short,driver.canonical
CAPS=dict(preparation=dict(model_ticks=300,force=1500,geometry=400,CPU_s=20,wall_s=30),local=dict(model_ticks=26000,force=110000,geometry=27000,CPU_s=500,wall_s=600),finite=dict(model_ticks=80000,force=400000,geometry=90000,CPU_s=1200,wall_s=1400),full=dict(model_ticks=120000,force=580000,geometry=140000,CPU_s=1600,wall_s=1800),verification=dict(model_ticks=2500,force=12000,geometry=2600,CPU_s=60,wall_s=90))
INPUTS=driver.INPUTS+[Path('/workspace/haic-response562-private/prefix-modified-private.json'),Path('/workspace/haic-response562-private/feedback-suffix-private.json'),G/'retry/handoff562_result.json']
SOURCES=['retry/continuation563_model.py',*driver.SOURCES]

class Phase(driver.Phase):
 def __init__(self,s,name,label):
  self.s,self.name,self.label=s,name,label;self.limits=CAPS[name];self.bucket=s.buckets.setdefault(name,dict(counter=[0],cost=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0,geometry_checks=0,body_checks=0,max_all_model_body=0.,CPU_s=0.,wall_s=0.)));self.counter=self.bucket['counter'];self.cost=self.bucket['cost'];self.current=label;self.active=False
 def __enter__(self):
  self.begin={k:self.cost[k] for k in ['force_evaluations','geometry_checks']};self.begin_tick=self.counter[0];self.cpu,self.wall=time.process_time(),time.perf_counter();self.active=True;atomic_write(D/f'{self.label}-STARTED.json',dict(contract_sha256=sha(G/'retry/continuation563_contract.json')))
  cpulimit=min(self.limits['CPU_s']-self.cost['CPU_s'],300 if self.name=='finite' else self.limits['CPU_s']);walllimit=min(self.limits['wall_s']-self.cost['wall_s'],350 if self.name=='finite' else self.limits['wall_s']);signal.signal(signal.SIGPROF,self.guard);signal.setitimer(signal.ITIMER_PROF,max(.01,cpulimit));signal.signal(signal.SIGALRM,self.guard);signal.setitimer(signal.ITIMER_REAL,max(.01,walllimit));self.guard();return self
 def guard(self,*_,reserve=0):
  if self.counter[0]>self.limits['model_ticks'] or self.cost['force_evaluations']+reserve>self.limits['force'] or self.cost['geometry_checks']>self.limits['geometry']:raise RuntimeError('WORK_CAP:'+self.name)
  cpu=time.process_time()-self.cpu;wall=time.perf_counter()-self.wall
  if self.cost['CPU_s']+cpu>=self.limits['CPU_s'] or self.cost['wall_s']+wall>=self.limits['wall_s'] or time.process_time()-self.s.cpu>=3400 or time.perf_counter()-self.s.wall>=4000:raise RuntimeError('TIME_CAP:'+self.name)
  if self.name=='finite' and (self.counter[0]-self.begin_tick>=20000 or self.cost['force_evaluations']+reserve-self.begin['force_evaluations']>100000 or self.cost['geometry_checks']-self.begin['geometry_checks']>25000 or cpu>=300 or wall>=350):raise RuntimeError('FINITE_CASE_CAP')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.s.contract['deadline_utc']):raise RuntimeError('DEADLINE')
 def snapshot(self,label):
  z=dict(self.cost,model_ticks=self.counter[0],internal_wheel_force_evaluations=4*self.counter[0]);z['CPU_s']+=time.process_time()-self.cpu if self.active else 0.;z['wall_s']+=time.perf_counter()-self.wall if self.active else 0.;atomic_write(D/f'{self.name}-ledger-private.json',dict(label=label,current=self.current,cost=z),True);return z
 def __exit__(self,typ,exc,tb):
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);self.cost['CPU_s']+=time.process_time()-self.cpu;self.cost['wall_s']+=time.perf_counter()-self.wall;self.active=False;self.snapshot('phase-finally-FIRST');return False

class Study(driver.Study):
 def __init__(self):
  D.mkdir(mode=0o700,exist_ok=False);self.buckets={};self.static,self.paths,self.saved,self.ledger,self.segment,self.seed,oldprefix,self.seed_suffix,self.proof=map(rd,INPUTS);self.index=driver.bounds(self.static['root']['roads']);self.edge=driver.boundary_index(self.static['boundary']);self.commands={x['index']:np.array(x['action'],np.float32) for x in self.saved['commands']};self.seed_x=np.array(self.seed['x']);self.gates=[]
  for index in (54,66,75):
   row=next(r for r in self.saved['trace'] if r['index']==index and r['raw']==4);p=row['root_without_roads'];v=p['planar']['linear']['velocity'];speed=math.hypot(*v);self.gates.append(dict(index=index,point=p['center'],normal=[q/speed for q in v]))
  self.contract=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',premise='561first global-safe proposal is feasible for NEW563connection because562proved unchanged551/537feedback whole safe13.22. Keep561aperture rejection unchanged. Preserve seed whole-success trajectory separately from finite incumbents.',program='Same original reset->actions1..34 prefix. Optimize20holds35..54; keep saved55..67 as program context. Feedback terminal starts from each altered after67 fullstate/history/tracker/visited. No pose aperture,relative yaw,baseline actuator equality or periodic terminal condition.',terminal='Actual unchanged551/537feedback12holds,indices68..79,with original reference/global safety/count. Objective is first forward arrival at fixed ORIGINAL551action75 endpoint plane (8feedbackholds plus4hold safety continuation). Original55154/66planes unchanged and recorded,not hard nonworsening constraints. Record recovery time=terminal-plane time minus66plane time and actual end12fullstate/cost. No new arbitrary pose penalty.',seed='Fresh source program plus first12 saved562feedback commands must match all seed132+48raw states/forces. Reuse existing full-safe13.22 proof; do not rerun seed selector. Initial finite command tape is a derivative surrogate for alreadyverified identical input.',linearization='40fresh one-sided actual-float32 FD per direction,steer1e-5/pedal1e-4,source rollout of program plus CURRENTincumbent recorded feedback12tape. This is frozen-policy derivative ONLY; no claim it equals closed-loop derivative. NONCLIP physical gradients and individual force gradients,never count derivatives. Terminal time derivative objective.',mode='Strict initial-history prefix order-stat; primary perprefix rank exemption branch,then ONE reconstruction from actual rejected actual-feedback ranks (unobserved suffix ranks filled only by incumbent surrogate,never physical state). Fixed steer.003/pedal.03 LP trust; no scalar radius retries,no mask/yaw/aperture. If both fail,ONE terminal-time coordinate poll(steer.0005/pedal.005). Max3directions/3acceptances/6LP branches/3polls/9proposals,FD120.',validation='Every proposed program is source checked. Only locallyglobal-safe program opens freshly computed feedback12continuation from that exact handoff. Accept if both program+actualfeedbacksafe,terminalplane bracketed and terminalarrival improves>1microsecond. Local plane gains need not individuallyimprove; no5ms gate. Two accepted terminalgains<.02ms or2accepted prediction mismatches stop. No accepted branch/poll ->stop.',safety='Original551reference,footprint>=.50,path<=3,trackingforce<=1.059,cumulativeclip<=.10 with actual initial history,body<100 for every model/forecast. Global launch special constraints unchanged. Exact ratio>1 count/prefixstat consistency runtime. Different contact/clip modes allowed and checked.',whole_validation='After bounded updates,run ONE whole feedback suffix (if unchanged exact seed,no accepted updates,reuse562full-policy proof and independently replay its complete tape instead of rerunning selector) from final finite-incumbent after67state,starting at same globalclock/history. Distinguish finiteincumbent from provenwholeincumbent. If whole-safe and officialfinish<seed13.22,select new wholeincumbent; onfailure/slower/tie retain seed. Independently replay attempted commandtape and seed if retained,<=2500raw. Never claim finitecontinuation safety implies restoflap.',budgets=CAPS,finite_case_cap=dict(model_ticks=20000,force=100000,geometry=25000,CPU_s=300,wall_s=350),aggregate=dict(model_ticks=228800,force=1103500,geometry=263000,CPU_s=3400,wall_s=4000),budget_reserve_rule='Stop proposing when remaining finite budget<20000ticks,local<40*180+132,or optimizationCPU>=1500. Full120000/CPU1600 and replay2500/CPU60 reserved separately. Local phase budget includes baseline180+FD21600+9program1188; everyphase counters separate under unchangedkernel200000.',storage='Tested clip561atomic JSON-safe writer; per-evaluation/phasefinally cost ledger and outerfinally costFIRST. Immutable finite and seed-whole incumbent. Record unsuccessful partialcontinuation state/commands and cause; no state/history reset.',actual_cap=0,research_remaining=22758,reserve=84000,reserve_used=0,new_seed_HOLDOUT_SEALED_other_environment_paid=0,source_sha256={p:sha(G/p) for p in SOURCES},private_inputs_sha256={str(p):sha(p) for p in INPUTS})
  atomic_write(G/'retry/continuation563_contract.json',self.contract);atomic_write(D/'STARTED.json',dict(contract_sha256=sha(G/'retry/continuation563_contract.json')));self.cpu,self.wall=time.process_time(),time.perf_counter();self.events=[];self.steps=[];self.inc=None;self.before35=None;self.prefix=None;self.feedback_calls=0
 def program_actions(self,x):return [np.array([x[2*j],max(0.,x[2*j+1]),max(0.,-x[2*j+1])],np.float32) for j in range(20)]+[self.commands[i] for i in range(55,68)]
 def metrics(self,states,rows):
  g=[];labels=[];ratios=[];clip,n=self.before35['tracking'];progress=self.before35['progress'];margins=[];paths=[];overs=[];maxclip=clip/n
  def add(v,label):g.extend(v);labels.extend([label]*len(v))
  for row in rows:
   add([row['progress_delta']+.5,row['projection_limit']-row['progress_delta']],'projection');add([row['margin']-.5],'footprint');add([3-row['path_error']],'path');add([4.85-row['reference_overspeed']],'reference');add([1.059-f['ratio'] for f in row['forces']],'force');clip+=sum(f['clipped'] for f in row['forces']);n+=4;maxclip=max(maxclip,clip/n);add([100-row['body']],'body');ratios.extend(f['ratio'] for f in row['forces']);margins.append(row['margin']);paths.append(row['path_error']);overs.append(row['reference_overspeed'])
  rr=np.array(ratios);order=prefix_slacks(rr,*self.before35['tracking']);assert bool(np.all(order>=0))==(maxclip<=.1)
  times=[];cross=[]
  for gate in self.gates:
   signed=[sum((s.center[j]-gate['point'][j])*gate['normal'][j] for j in range(2)) for s in states];found=None
   for k in range(1,len(states)):
    if signed[k-1]<0<=signed[k]:
     f=-signed[k-1]/(signed[k]-signed[k-1]);found=.02*(k-1+f);cross.append(dict(time=found,raw_bracket=[.02*(k-1),.02*k],fraction=f,raw=k));break
   times.append(found)
  safe=min(g)>=0 and np.all(order>=0);return dict(g=np.array(g),labels=labels,ratios=rr,order=order,times=np.array(times) if all(v is not None for v in times) else None,crossings=cross,physical_safe=bool(safe),stats=dict(min_margin=min(margins),max_path=max(paths),max_reference_overspeed=max(overs),max_force=max(rr),max_clip=maxclip,max_body=max(r['body'] for r in rows),tracking_history=[clip,n]))
 def reconstruct(self,states,rows):
  s=copy.deepcopy(self.before35)
  for root,row in zip(states[1:],rows):
   s['root']=root;s['elapsed']+=.02;s['global_raw']+=1;s['tracking'][0]+=sum(f['clipped'] for f in row['forces']);s['tracking'][1]+=4;s['progress']=row['progress']
   for ids in root.current_contacts:s['visited'].update(ids)
   p,v=driver.hull_pose(root);s['tracker'].update(p,v,len(s['visited'])/len(self.static['track']),1.02+s['elapsed'])
  return s
 def local(self,x,label,suffix=None):
  with Phase(self,'local',label) as phase:
   root=self.before35['root'];states=[root];rows=[];progress=self.before35['progress'];actions=self.program_actions(x)+(suffix or [])
   try:
    for j,a in enumerate(actions):
     root=replace(root,planar=replace(root.planar,steer=-float(a[0])))
     for k in range(4):
      fs=phase.force(root,a);phase.cost['force_evaluations']+=4;before=root;old_progress=progress;root=phase.tick(root,float(a[1]),float(a[2]),self.index,phase.counter);q=driver.project(root.center,self.paths['candidate'],progress);progress=q['s'];gap=phase.geometry(root);over=math.hypot(*root.planar.linear.velocity)-driver.reference(progress,self.paths['candidate'])[0];body=max(math.hypot(*driver.hull_pose(root)[1]),*(math.hypot(*(root.planar.linear.velocity[t]+w.offset[t] for t in range(2))) for w in root.planar.linear.wheels));rows.append(dict(index=35+j,raw=k+1,action=a.tolist(),root_without_roads=short(root),forces=fs,margin=gap,path_error=q['distance'],reference_overspeed=over,body=body,progress=progress,progress_delta=progress-old_progress,projection_limit=max(5.,2*math.dist(before.center,root.center))));states.append(root)
    result=self.metrics(states,rows);result.update(x=np.array(x).copy(),states=states,rows=rows,handoff=self.reconstruct(states[:133],rows[:132]),label=label);return result
   finally:
    payload=dict(x=list(map(float,x)),rows=rows if not label.startswith('FD') else None,terminal_root_without_roads=short(root),model_ticks=phase.counter[0])
    if 'result' in locals():payload.update({k:plain(result[k]) for k in ['g','labels','ratios','order','times','crossings','physical_safe','stats']})
    atomic_write(D/f'{label}-private.json',payload);phase.snapshot('local-case-finally')
 def feedback(self,label,handoff,maxholds,category):
  state=copy.deepcopy(handoff);commands=[];rows=[];failure=None;technical=None;stop='FINITE_HORIZON';start_hash=self.checkpoint_hash(state)
  with Phase(self,category,label) as phase:
   try:
    for index in range(68,68+maxholds):
     phase.snapshot('before-policy');geometry=driver.tracking.geometry_context(self.static,phase.limits['geometry']);phase.guard(reserve=6400);ot,of=driver.tracking.tick,driver.tracking.force_rows;driver.tracking.tick=phase.tick;driver.tracking.force_rows=phase.force
     try:
      maxcounter=min(phase.limits['model_ticks'],phase.begin_tick+20000) if category=='finite' else phase.limits['model_ticks'];action,detail=driver.tracking.choose(state['root'],self.paths['candidate'],self.paths['backup'],state['progress'],phase.counter,phase.cost,maxcounter,history=tuple(state['tracking']),geometry=geometry)
     finally:driver.tracking.tick,driver.tracking.force_rows=ot,of
     if action is None:failure=dict(reason='NO_ADMISSIBLE_ACTION',index=index,detail=detail);stop='NO_ADMISSIBLE_ACTION';break
     assert detail['final_recertified'] and next(z for z in detail['reports'] if z['mode']=='FINAL')['ok']
     commands.append(dict(index=index,action=action.tolist(),detail=detail))
     for k in range(4):
      row,reason=self.raw(state,action,index,k+1,phase);rows.append(row)
      if reason:failure=dict(reason=reason,index=index,raw=k+1,row=row);stop=reason;break
      if state['tracker'].finish_time_s is not None:stop='SOURCE_FINISH';break
      if state['global_raw']+50>=1224:failure=dict(reason='SOURCE_TIME_LIMIT',index=index);stop='SOURCE_TIME_LIMIT';break
     if failure or stop=='SOURCE_FINISH':break
   except BaseException as e:technical=type(e).__name__+':'+str(e);stop='TECHNICAL_OR_BUDGET';failure=dict(reason=technical,index=index if 'index' in locals() else 68)
   finally:atomic_write(D/f'{label}-private.json',dict(start_hash=start_hash,checkpoint=self.checkpoint(state),commands=commands,rows=rows,stop=stop,failure=failure,technical_error=technical));phase.snapshot('feedback-case-finally')
  return dict(label=label,state=state,commands=commands,rows=rows,stop=stop,failure=failure,technical_error=technical,safe=failure is None and (len(rows)==maxholds*4 or stop=='SOURCE_FINISH'),safe_finish=failure is None and stop=='SOURCE_FINISH',finish_s=state['tracker'].finish_time_s-1.02 if failure is None and state['tracker'].finish_time_s is not None else None)
 def actual(self,x,label):
  p=self.local(x,label+'-program')
  if not p['physical_safe']:return p,None,None
  self.feedback_calls+=1;fb=self.feedback(label+'-feedback',p['handoff'],12,'finite')
  if fb['technical_error']:raise RuntimeError(fb['technical_error'])
  if not fb['safe']:return p,fb,None
  previous=p['states'][-1];progress=p['rows'][-1]['progress']
  for row in fb['rows']:
   root=driver.load_root(dict(row['root_without_roads'],roads=self.static['root']['roads']));row['progress_delta']=row['progress']-progress;row['projection_limit']=max(5.,2*math.dist(previous.center,root.center));previous=root;progress=row['progress']
  fs=[driver.load_root(dict(r['root_without_roads'],roads=self.static['root']['roads'])) for r in fb['rows']];m=self.metrics(p['states']+fs,p['rows']+fb['rows']);m.update(x=p['x'],program=p,feedback=fb,states=p['states']+fs,rows=p['rows']+fb['rows'],label=label,suffix=[np.array(q['action'],np.float32) for q in fb['commands']]);return p,fb,m
 def retain(self,r,number):
  assert r['physical_safe'] and r['times'] is not None;self.inc=r;atomic_write(D/f'finite-incumbent-{number:02d}-private.json',dict(label=r['label'],x=r['x'].tolist(),times=r['times'].tolist(),handoff=self.checkpoint(r['program']['handoff']),finite_safe=True,whole_validated=number==0))
 def run(self):
  out={};error=None;stop=None;seed=None;full=None;verification=[];small=bad=0
  try:
   assert self.proof['feedback']['safe_finish'] and self.proof['whole_source_finish_s']==self.saved['summary']['model_finish_episode_s']
   with Phase(self,'preparation','prefix') as phase:self.prefix=self.run_commands('original-prefix',self.initial(),{i:a for i,a in self.commands.items() if i<=34},phase)
   assert self.prefix['failure'] is None and len(self.prefix['rows'])==136;assert all(canonical(a['root_without_roads'])==b['root_without_roads'] and canonical(a['forces'])==b['forces'] for a,b in zip(self.prefix['rows'],self.saved['trace'][:136]));self.before35=self.prefix['state'];suffix=[np.array(q['action'],np.float32) for q in self.seed_suffix['commands'][:12]];seed=self.local(self.seed_x,'seed',suffix)
   expected=self.seed['rows']+self.seed_suffix['rows'][:48];assert all(canonical(a['root_without_roads'])==b['root_without_roads'] and canonical(a['forces'])==b['forces'] for a,b in zip(seed['rows'],expected));assert seed['physical_safe'] and seed['times'] is not None
   program=dict(seed);program['states']=seed['states'][:133];program['rows']=seed['rows'][:132];program['handoff']=seed['handoff'];seed.update(program=program,feedback=None,suffix=suffix,label='seed');self.retain(seed,0)
   for d in range(3):
    if self.buckets['local']['counter'][0]+40*180+132>26000 or self.buckets.get('finite',dict(counter=[0]))['counter'][0]+20000>80000 or time.process_time()-self.cpu>=1500:stop='OPTIMIZATION_RESERVE';break
    inc=self.inc;J=[];RR=[];TT=[];steps=[];force=np.array([i for i,n in enumerate(inc['labels']) if n=='force']);limit=float(np.float32(.4))
    for j,v in enumerate(inc['x']):
     h=1e-5 if j%2==0 else 1e-4;a,b=(-limit,limit) if j%2==0 else(-1.,1.);dh=h if v+h<=b else-h
     if j%2 and ((v<=-.9)!=(v+dh<=-.9)):dh=-dh
     xx=inc['x'].copy();xx[j]=float(np.float32(v+dh));step=xx[j]-v;assert step!=0;ev=self.local(xx,f'FD-{d:02d}-{j:02d}',inc['suffix'])
     if ev['times'] is None:raise RuntimeError('FROZEN_POLICY_FD_TERMINAL_UNBRACKETED')
     J.append((ev['g']-inc['g'])/step);RR.append(-(ev['g'][force]-inc['g'][force])/step);TT.append((ev['times']-inc['times'])/step);steps.append(step)
    J=np.array(J).T;RR=np.array(RR).T;T=np.array(TT).T;objective=T[2];bounds=[(max((-limit if j%2==0 else-1)-v,-(.003 if j%2==0 else.03)),min((limit if j%2==0 else 1)-v,(.003 if j%2==0 else.03))) for j,v in enumerate(inc['x'])];accepted=False;last_rank=None;record=dict(direction=d+1,incumbent_before=inc['label'],proposals=[],LP=[],FD_steps=steps)
    proposals=[];seen=set()
    for branch in range(2):
     ids=nonexempt_branch(inc['ratios'] if last_rank is None else last_rank,*self.before35['tracking']);buffer=np.minimum(1e-5,.25*np.maximum(0.,1-inc['ratios'][ids]));lp=linprog(objective,A_ub=np.vstack([-J,RR[ids]]),b_ub=np.r_[.75*inc['g'],1-buffer-inc['ratios'][ids]],bounds=bounds,method='highs');record['LP'].append(dict(branch=branch+1,success=bool(lp.success),status=int(lp.status),rank_samples=len(ids)))
     if not lp.success:continue
     proposals.append((inc['x']+lp.x,'rank' if branch==0 else'reconstructed_rank'))
     xx,kind=proposals[-1];xx=np.array([float(np.float32(v)) for v in xx]);key=xx.tobytes()
     if key in seen:record['LP'][-1]['duplicate_control_skipped']=True;continue
     seen.add(key);pred=-(T@(xx-inc['x']));p,fb,new=self.actual(xx,f'proposal-{d:02d}-{branch:02d}');last_rank=inc['ratios'].copy();last_rank[:len(p['ratios'])]=p['ratios'];
     if fb is not None:
      observed=np.array([f['ratio'] for row in fb['rows'] for f in row['forces']]);last_rank[528:528+min(len(observed),192)]=observed[:192]
     if new is not None:last_rank=new['ratios']
     event=self.event(kind,inc,p,fb,new,pred);record['proposals'].append(event)
     if event['accepted']:chosen=new;chosen_event=event;accepted=True;break
    if not accepted:
     amp=np.array([.0005 if j%2==0 else.005 for j in range(40)]);order=np.argsort(-abs(objective)*amp,kind='stable')
     for j in order:
      if objective[j]==0:continue
      xx=inc['x'].copy();a,b=(-limit,limit) if j%2==0 else(-1.,1.);xx[j]=np.clip(xx[j]-math.copysign(amp[j],objective[j]),a,b)
      if np.float32(xx[j])==np.float32(inc['x'][j]):continue
      xx=np.array([float(np.float32(v)) for v in xx]);
      if xx.tobytes() in seen:break
      seen.add(xx.tobytes());pred=-(T@(xx-inc['x']));p,fb,new=self.actual(xx,f'poll-{d:02d}');event=self.event('terminal_coordinate_poll',inc,p,fb,new,pred);record['proposals'].append(event)
      if event['accepted']:chosen=new;chosen_event=event;accepted=True
      break
    self.events.append(record);atomic_write(D/f'direction-{d:02d}-private.json',record)
    if not accepted:stop='NO_TERMINAL_IMPROVEMENT_AFTER_BRANCHES_POLL';break
    self.retain(chosen,len(self.steps)+1);gain=inc['times'][2]-chosen['times'][2];self.steps.append(dict(step=len(self.steps)+1,direction=d+1,cumulative_plane_gain_ms=(1000*(seed['times']-chosen['times'])).tolist(),**chosen_event));small=small+1 if gain<2e-5 else 0;bad=0 if chosen_event['agreement'] else bad+1
    if small>=2:stop='TWO_SMALL_ACCEPTED_GAINS';break
    if bad>=2:stop='TWO_ACCEPTED_PREDICTION_MISMATCHES';break
   if stop is None:stop='DIRECTION_LIMIT3'
  except BaseException as e:error=type(e).__name__+':'+str(e);atomic_write(D/'optimization-error-private.json',dict(error=error,traceback=traceback.format_exc(),incumbent=self.inc['label'] if self.inc else None))
  finally:
   try:
    if self.inc is not None:
     reused=np.array_equal(self.inc['x'],self.seed_x)
     if reused:
      q=self.seed_suffix['checkpoint'];state=dict(root=driver.load_root(dict(q['root_without_roads'],roads=self.static['root']['roads'])),visited=set(q['visited']),tracker=driver.FinishLineTracker(**q['tracker']),elapsed=q['elapsed'],global_raw=q['global_raw'],progress=q['progress'],launch=q['launch'],tracking=q['tracking']);full=dict(safe_finish=True,finish_s=self.proof['whole_source_finish_s'],commands=self.seed_suffix['commands'],rows=self.seed_suffix['rows'],state=state,failure=None)
     else:full=self.feedback('final-full-feedback',self.inc['program']['handoff'],300,'full')
     candidate_tape={i:a for i,a in self.commands.items() if i<=34};candidate_tape.update({35+j:a for j,a in enumerate(self.program_actions(self.inc['x']))});candidate_tape.update({q['index']:np.array(q['action'],np.float32) for q in full['commands']});seed_tape={i:a for i,a in self.commands.items() if i<=34};seed_tape.update({35+j:a for j,a in enumerate(self.program_actions(self.seed_x))});seed_tape.update({q['index']:np.array(q['action'],np.float32) for q in self.seed_suffix['commands']});new_best=bool(full['safe_finish'] and full['finish_s']<self.proof['whole_source_finish_s']-1e-9)
     chosen='new' if new_best else'seed';tapes=[('new-attempt',candidate_tape,self.prefix['rows']+self.inc['program']['rows']+full['rows'],full['state'])]
     if not new_best and not reused:tapes.append(('seed-whole-incumbent',seed_tape,rd(INPUTS[-3])['rows']+self.seed_suffix['rows'],None))
     for label,tape,expected,state in tapes:
      with Phase(self,'verification',label) as phase:vr=self.run_commands(label,self.initial(),tape,phase)
      exact=len(vr['rows'])==len(expected) and all(canonical(a.get('root_without_roads',a.get('before_root_without_roads')))==canonical(b.get('root_without_roads',b.get('before_root_without_roads'))) and canonical(a['forces'])==canonical(b['forces']) for a,b in zip(vr['rows'],expected));assert exact
      if state is not None:assert canonical(self.checkpoint(vr['state']))==canonical(self.checkpoint(state))
      verification.append(dict(label=label,raw=len(vr['rows']),fullstate_force_exact=exact,safe_finish=vr['safe_finish'],finish_s=vr['finish_s']))
     out.update(final_finite_incumbent=self.inc['label'],full_suffix_reused_from562=reused,finite_plane_times_s=self.inc['times'].tolist(),finite_cumulative_gain_ms=(1000*(seed['times']-self.inc['times'])).tolist(),whole_attempt_safe_finish=full['safe_finish'],whole_attempt_finish_s=full['finish_s'],whole_attempt_failure=full['failure']['reason'] if full['failure'] else None,whole_incumbent=chosen,whole_incumbent_finish_s=full['finish_s'] if new_best else self.proof['whole_source_finish_s'],whole_gain_vs551_ms=1000*(self.saved['summary']['model_finish_episode_s']-(full['finish_s'] if new_best else self.proof['whole_source_finish_s'])),independent_verification=verification)
   except BaseException as e:error=(error+';' if error else'')+'FINAL:'+type(e).__name__+':'+str(e);atomic_write(D/'final-error-private.json',dict(error=error,traceback=traceback.format_exc()))
   phases={k:dict(v['cost'],model_ticks=v['counter'][0],internal_wheel_force_evaluations=4*v['counter'][0]) for k,v in self.buckets.items()};totals={k:sum(v[k] for v in phases.values()) for k in ['model_ticks','force_evaluations','internal_wheel_force_evaluations','geometry_checks','body_checks']};totals.update(CPU_s=time.process_time()-self.cpu,wall_s=time.perf_counter()-self.wall);atomic_write(G/'retry/continuation563_cost.json',dict(phases=phases,total=totals))
   out.update(completed=error is None,error=error,stop_reason=stop,accepted_count=len(self.steps),steps=self.steps,directions=[{k:v for k,v in r.items() if k!='FD_steps'} for r in self.events],seed_plane_times_s=seed['times'].tolist() if seed else None,seed_whole_finish_s=self.proof['whole_source_finish_s'],cost=totals,phase_costs=phases,feedback_finite_calls=self.feedback_calls,prior561_aperture_failure_preserved=True,new_native_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT_queries=0,SEALED_queries=0,research_remaining=22758,reserve=84000,reserve_used=0,actual_baseline_s=13.66,no_native_gain_observation=True);atomic_write(G/'retry/continuation563_result.json',out);print(json.dumps(plain(out),indent=2))
 def event(self,kind,inc,p,fb,new,pred):
  safe=bool(new and new['physical_safe'] and new['times'] is not None);gain=inc['times']-new['times'] if safe else None;accept=bool(safe and gain[2]>1e-6);ratio=float(gain[2]/pred[2]) if gain is not None and pred[2]>1e-12 else None;err=abs(float(gain[2]-pred[2])) if gain is not None else None;agree=bool(ratio is not None and .25<=ratio<=2 and err<=max(.0005,.5*abs(pred[2])))
  return dict(kind=kind,local_program_safe=p['physical_safe'],feedback_executed=fb is not None,feedback_safe=bool(fb and fb['safe']),feedback_failure=fb['failure']['reason'] if fb and fb['failure'] else None,accepted=accept,predicted_plane_gain_ms=(1000*pred).tolist(),actual_plane_gain_ms=(1000*gain).tolist() if gain is not None else None,terminal_gain_ms=1000*gain[2] if gain is not None else None,agreement=agree,terminal_prediction_error_ms=1000*err if err is not None else None,actual_terminal_times_s=new['times'].tolist() if safe else None,recovery_component_s=float(new['times'][2]-new['times'][1]) if safe else None,end_feedback_state=dict(progress=fb['state']['progress'],speed=math.hypot(*fb['state']['root'].planar.linear.velocity),yaw=fb['state']['root'].planar.yaw,tracking_history=fb['state']['tracking'],clip_budget_remaining=fb['state']['tracking'][1]//10-fb['state']['tracking'][0],changed_actions_vs_frozen=sum(q['action']!=a.tolist() for q,a in zip(fb['commands'],inc['suffix']))) if fb else None,local_stats=p['stats'],combined_stats=new['stats'] if new else None)

if __name__=='__main__':
 from core.vendor.car_racing import CarRacing
 def forbidden(*a,**k):raise RuntimeError('NATIVE_FORBIDDEN')
 CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden
 Study().run()
