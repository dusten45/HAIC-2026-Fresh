"""Single local unchanged537 feedback experiment; every primitive charged, native forbidden."""
import time
CPU=time.process_time(); WALL=time.perf_counter()
import datetime,json,math,signal,subprocess,sys,traceback,unittest
from collections import Counter
from dataclasses import asdict
from pathlib import Path
import numpy as np
import retry.handoff562_model as d
import retry.late568_model as base
import retry.structure537_control as policy
import retry.lap518_control as lap
import retry.brake502_response as wheel
import retry.brake504_planar as planar
from retry.durable568 import Journal,digest,evaluate_force,inspect
from retry.clip561_core import atomic_write
from retry.feedback596_trace import Trial,post_flags
from core.vendor.car_racing import CarRacing
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response596-private');C=G/'retry/feedback596_contract.json'
INPUTS=dict(checkpoint=Path('/workspace/haic-response595-private/checkpoint-private.json'),static=Path('/workspace/haic-response515-private/collected-map-state-private.json'),paths=Path('/workspace/haic-response551-private/frozen-paths-private.json'),ledger=Path('/workspace/haic-response519-private/model-ledger-private.json'),tape=Path('/workspace/haic-response577-private/final-independent-tape-private.json'),fixed595=Path('/workspace/haic-response595-private/diagnostic-rows-private.json'),gate=G/'retry/cause595_checkpoint_gate.json',previous=G/'retry/cause595_result.json',proposal=G/'retry/cause595_next_proposal.json')
EXPECTED=dict(checkpoint='033b7c9b15e1e151a24897c26bd9aa046c4fbcd93bc2e65c629c0163e0f85590',static='e3a36640efba4a2abdf6b02bac6d90e12f97a81ac73ebd7dafc98b7551e1ab3f',paths='a013d2b40cae8c29f53da5405ca51de3e0fb7a74da5ddbfb3d4f4360566f89ef',ledger='28ff0ff7ffec9784e4817b4b55500c40ecd3730e9d09977294ad1dfd9b70763f',tape='bc432812cdd71702ec030edda72a9aa63ca79e61dceb1f970891a659f20cd5a6',previous='a9b42d3996aa08d2f41bfabab518b7949de54a525ca8dce3b8db0f2e4c0597d2')
LIMITS=dict(model_attempted=18480,model_completed=18480,external_force=73920,internal_force=73920,total_force=147840,geometry=40000,applied_attempted=48,applied_completed=48,chooser_calls=12,certificates=384)
TIMES=dict(source_CPU_s=450,source_wall_s=600,preparation_audit_CPU_s=30,preparation_audit_wall_s=45,total_CPU_s=480,total_wall_s=645)
short=lambda r:dict(planar=asdict(r.planar),center=r.center,current_contacts=r.current_contacts,floor=r.floor,skin=r.skin)
class Stop(RuntimeError):pass

def counter_room(counts,need):
 return all(counts.get(k,0)+n<=LIMITS[k] for k,n in need.items())

def records(detail):
 return detail['trials']+[r for r in detail.get('reports',[]) if r['mode']=='FINAL'] if 'trials' in detail else detail.get('reports',[])

class Study:
 def __init__(self):
  D.mkdir(mode=0o700,exist_ok=False);atomic_write(D/'PREP_STARTED-private.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source=0,native=0))
  self.counts=Counter();self.model=[0];self.cost=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0,geometry_checks=0);self.counter=self.model
  self.stage='preparation';self.scCPU=self.scWall=0.;self.rows=[];self.choices=[];self.trials=[];self.trial=None;self.pending=None;self.seed_root=None;self.applied=False;self.hold=None;self.saved=[];self.failure=None;self.status='PREPARATION';self.error=None
  self.orig_project=d.project;self.orig_margin=d.margin;self.ext=wheel.wheel_response;self.intern=planar.wheel_response
  self.journal=Journal(D/'journal-private.jsonl');self.result={};self.state=None
 def times(self):
  active=self.stage=='source';sc=self.scCPU+(time.process_time()-self.pc if active else 0);sw=self.scWall+(time.perf_counter()-self.pw if active else 0);tc=time.process_time()-CPU+10.;tw=time.perf_counter()-WALL+10.
  return dict(source_CPU_s=sc,source_wall_s=sw,preparation_audit_CPU_s=tc-sc,preparation_audit_wall_s=tw-sw,total_CPU_s=tc,total_wall_s=tw)
 def guard(self):
  for k,v in self.times().items():
   if v>=TIMES[k]:raise Stop('TIME_CAP:'+k)
  if self.stage=='source' and (self.times()['preparation_audit_CPU_s']>25 or self.times()['preparation_audit_wall_s']>35):raise Stop('AUDIT_TIME_RESERVE')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,20,10,1,55,tzinfo=datetime.timezone.utc):raise Stop('DEADLINE')
 def count(self,k,n=1):
  self.guard()
  if k in LIMITS and self.counts[k]+n>LIMITS[k]:raise Stop('COST_CAP:'+k)
  self.counts[k]+=n
 def geometry_query(self,kind,fn,*a):
  self.count('geometry');self.counts[kind]+=1;return fn(*a)
 def geometry(self,r):return self.geometry_query('applied_footprint' if self.applied else 'preflight_footprint',self.orig_margin,r,self.static['roads'],self.index,self.static['boundary'],self.edge,self.static['obstacles'])
 def internal_project(self,*a):return self.geometry_query('internal_nominal_steering_projection',self.orig_project,*a)
 def applied_project(self,*a):return self.geometry_query('applied_projection',self.orig_project,*a)
 def kernel(self,key,fn,*a,**kw):
  self.count('total_force');self.count(key);return fn(*a,**kw)
 def tick(self,r,gas,brake,index,counter):
  self.guard();assert counter is self.model and self.pending is not None
  p=self.pending;assert p['root_id']==digest(short(r)) and p['gas']==gas and p['brake']==brake,'PENDING_FORCE_TICK_IDENTITY'
  assert p['gate'] is None,'TICK_AFTER_FORCE_REJECTION'
  self.journal.append('BEFORE_TICK',mode=p['mode'],force_event=p['event'],root_sha256=digest(short(r)))
  out=d.source_tick(r,gas,brake,index,counter);self.count('model_completed')
  if self.applied:self.count('applied_completed')
  value=base.body(out);self.counts['body_checks']+=1;self.counts['max_body']=max(self.counts['max_body'],value)
  self.journal.append('AFTER_TICK',mode=p['mode'],root=short(out),body=value,body_domain_pass=math.isfinite(value) and value<100,force_event=p['event'])
  if not math.isfinite(value) or value>=100:raise Stop('BODY_DOMAIN')
  if not self.applied:
   self.trial.ticks+=1;self.last_before=r;self.last_after=out;p['row'].update(tick_executed=True,root=short(out),body=value,root_sha256=digest(short(out)))
  self.pending=None;return out
 def evaluate(self,r,a,history,context,peak=1.059,clip=.1,check_clip=True):
  self.count('model_attempted')
  if self.applied:self.count('applied_attempted')
  verdict=evaluate_force(self.journal,short(r),a.tolist(),history,context,lambda:d.force_rows(r,a),peak,clip,check_clip)
  self.pending=dict(root_id=digest(short(r)),gas=float(a[1]),brake=float(a[2]),gate=verdict['gate'],event=verdict['event'],mode='applied' if self.applied else 'forecast')
  return verdict
 def finish_trial(self):
  if self.trial is None:return
  summary=self.trial.summary();self.trials.append(dict(hold=self.hold,certificate=len(self.trials)+1,summary=summary,rows=self.trial.rows));self.journal.append('TRIAL_END',hold=self.hold,summary=summary);self.trial=None
 def forecast_margin(self,r,*a):
  gap=self.geometry_query('forecast_footprint',self.orig_margin,r,*a)
  if r is self.seed_root:
   self.finish_trial();self.count('certificates');self.trial=Trial(self.state['tracking'],self.state['progress'],gap);self.journal.append('TRIAL_START',hold=self.hold,history=self.state['tracking'],progress=self.state['progress'],minimum=gap)
  else:
   t=self.trial;row=t.rows[-1];assert row['tick_executed'];q=row['projection'];flags,first=t.post(gap,row['reference_overspeed'],q['distance'],row['projection_delta'],row['projection_limit']);row.update(footprint_margin=gap,minimum_footprint=t.minimum,maximum_reference_overspeed=t.maxover,split_flags=flags,split_first_failure=first)
   self.journal.append('FORECAST_RAW',hold=self.hold,row=row)
  return gap
 def forecast_force(self,r,a):
  t=self.trial;assert t is not None and t.reason is None
  v=self.evaluate(r,a,t.history,dict(mode='forecast',hold=self.hold,forecast_attempt=t.attempts+1),policy.ADMISSION,.1,True)
  reason=t.force(v['forces'],policy.ADMISSION);row=dict(raw=t.attempts,global_raw=self.state['global_raw']+t.attempts,action=a.tolist(),before_root=short(r),forces=v['forces'],history=t.history.copy(),peak=t.peak,pre_failure=reason,tick_executed=False)
  t.rows.append(row);self.pending['row']=row
  # Original537 tests the rolling peak; preserve it even if a diagnostic current-raw gate differs.
  self.pending['gate']=reason
  if reason:self.journal.append('FORECAST_RAW',hold=self.hold,row=row);self.pending=None
  return v['forces']
 def forecast_project(self,*a):
  q=self.geometry_query('forecast_projection',self.orig_project,*a);t=self.trial;row=t.rows[-1];assert row['tick_executed'];previous=t.progress;over=math.hypot(*self.last_after.planar.linear.velocity)-d.reference(q['s'],self.paths['candidate'])[0]
  row.update(projection=q,projection_delta=q['s']-previous,projection_lower=-.5,projection_limit=max(5.,2*math.dist(self.last_before.center,self.last_after.center)),reference_overspeed=over,path_error=q['distance']);t.progress=q['s'];return q
 def checkpoint(self):
  if self.state is None:return None
  return dict(root=short(self.state['root']),progress=self.state['progress'],tracker=asdict(self.state['tracker']),visited=sorted(self.state['visited']),launch=self.state['launch'],tracking=self.state['tracking'],elapsed=self.state['elapsed'],global_raw=self.state['global_raw'])
 def prepare(self):
  self.guard()
  for k,h in EXPECTED.items():assert d.sha(INPUTS[k])==h,('INPUT_PIN',k)
  assert d.sha(G/'retry/structure537_control.py')=='c5a3f3206979085150e8ecda4f96da4b76f74ff4e9064bc3f5b9e3eb8d62c771'
  assert subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31'
  assert not subprocess.check_output(['git','diff','--name-only','main','--','Participants'],cwd=G,text=True).strip()
  tests=unittest.TextTestRunner(stream=sys.stderr).run(unittest.defaultTestLoader.discover(str(G/'tests'),pattern='test_feedback596.py'));assert tests.wasSuccessful()
  atomic_write(G/'retry/feedback596_tests.json',dict(passed=True,tests=tests.testsRun,source_ticks=0,native=0,input_sha256={p:d.sha(G/p) for p in ['tests/test_feedback596.py','retry/feedback596_trace.py','retry/feedback596_model.py']}))
  self.cp=d.rd(INPUTS['checkpoint']);self.static=d.rd(INPUTS['static']);self.paths=d.rd(INPUTS['paths']);self.index=d.bounds(self.static['roads']);self.edge=d.boundary_index(self.static['boundary']);root=d.load_root(dict(self.cp['root'],roads=self.static['root']['roads']))
  assert digest(short(root))==digest(self.cp['root'])=='9d015253cc9f320a5631fe920878935d05d1c9a996660d08b217f39b57c12173'
  assert self.cp['global_raw']==156 and self.cp['next_hold']==40 and self.cp['groups']['running']==[15,240]
  assert all(d.rd(INPUTS['gate'])['checks'].values())
  self.state=dict(root=root,progress=self.cp['progress'],visited=set(self.cp['visited']),tracker=d.FinishLineTracker(**self.cp['tracker']),elapsed=self.cp['clock']-1.02,global_raw=156,launch=self.cp['groups']['launch'].copy(),tracking=self.cp['groups']['running'].copy())
  atomic_write(D/'initial-checkpoint-private.json',self.checkpoint())
  local={str(Path(m.__file__).resolve().relative_to(G)):d.sha(Path(m.__file__).resolve()) for m in tuple(sys.modules.values()) if getattr(m,'__file__',None) and Path(m.__file__).is_file() and Path(m.__file__).resolve().is_relative_to(G) and '.venv' not in Path(m.__file__).parts}
  local.update({p:d.sha(G/p) for p in ['retry/feedback596_model.py','retry/feedback596_trace.py','tests/test_feedback596.py','retry/feedback596_audit.py']})
  deps={str(Path(m.__file__).resolve()):d.sha(Path(m.__file__).resolve()) for m in tuple(sys.modules.values()) if getattr(m,'__file__',None) and Path(m.__file__).is_file() and not Path(m.__file__).resolve().is_relative_to(G) or getattr(m,'__file__',None) and Path(m.__file__).is_file() and '.venv' in Path(m.__file__).parts}
  self.contract=dict(study=596,status='FROZEN_BEFORE_SOURCE_AFTER_PURE_TESTS',registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55Z',parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip(),input_sha256={k:d.sha(p) for k,p in INPUTS.items()},implementation_sha256=local,dependency_sha256=deps,tests_sha256=d.sha(G/'retry/feedback596_tests.json'),caps=LIMITS,time_caps=TIMES,spec='Newcoldpolicy577commands1..39thenunchanged537feedbackfrom40forever. ONLYsourceholds40..51fromexactactualraw156;nofixedtape/baseline/nativeprefixreplay.Original551candidate/backup,reference,gains,cap,finite31trials+freshFINALandstrictguardsunchanged. Everytrialstartsactualhistoryindependently;selectedFINALfirst4mustexactmatchappliedsource. Trialrejectionsareoriginalpolicysemantics,notadditionalpolicies. No trial/FINALcosthidden.',stop='Firstnoadmissibleaction,appliedstrict/domain/technical/IO/integrity/cost/deadlinefailure terminates. No retry,thresholdrelaxation,statepatch,alternatepolicyornewexperiment. Localpassrequiresall48appliedrawsafeandprogressgain>0;nogain/native/carry/wholefinishpromotion.',geometry_rule='IncludeALLmarginandprojectionqueriesincludingnominal/steeringinternals omittedby595proposal37346derivation. Worsthold32*(49margin+48forecastproject+44backupinternalproject)+6initialinternalproject+8applied=4526. Twelveworstholds54312+2preflight>40000:capunchanged,costcensorifinsufficient;reserve4526pernexthold. No claimfull12worstcaserunbudgetguaranteed.',time_rule='Prior10CPU/wallconservativechargecoverspre-runpreparation/reads;imports/tests/hashregistration/source/allloggingmeasured;reserve5CPU10wallforaudit;source450/600,prep30/45,total480/645. Documentation/Gitwaitnotclaimedphysics. Postrunread-onlyauditadded.',telemetry='Fsyncedhashchaincompletepreforceinputs/verdicts/tickroots;passiveoriginal537summaryexactcomparison,splitFOOTPRINT/REFERENCE/PATH/PROJECTION_BACKWARD/FORWARDandnumericvalues,allinternalgeometryandbothwheeloraclescounted. Appliedrawusesunchangedlate568rawstrictsemantics. PhysicalrootsexactFINALfirst4andactualcheckpointimmutableduringchoose.',scope=dict(DEV_only=True,HOLDOUT=0,SEALED=0,native=0,worlds=0,resets=0,actions=0,FD=0,solver=0,new_seed=0,paid=0),research_remaining=22548,reserve=84000,reserve_used=0,privacy='Rawcheckpoint/actions/states/journaloutsidegit;technicalcode/hash/aggregatesonly.Designatedcloud,preservemainParticipantsbackupspriorfailures.',date_correction='Earlier596terminationreportmistakenlyusedoriginalOct16deadline.Latestuser3dayextensionandcontinueinstructionprovidedintranscriptevidenceauthorizesOct20existingdeadline;notnewautomaticextension.Originalreport/resultsretained.')
  atomic_write(C,self.contract);atomic_write(D/'REGISTERED-private.json',dict(contract_sha256=d.sha(C)))
  self.pins();self.guard();q=self.geometry_query('preflight_projection',self.orig_project,root.center,self.paths['candidate'],self.state['progress']);gap=self.geometry(root);assert q['s']==self.state['progress'] and gap>=.5 and q['distance']<=3 and base.body(root)<100
  atomic_write(G/'retry/feedback596_checkpoint_gate.json',dict(checkpoint_sha256=d.sha(INPUTS['checkpoint']),root_sha256=digest(short(root)),history=self.state['tracking'],global_raw=156,root_roundtrip_exact=True,original_policy_pinned=True,original_paths_pinned=True,stored_progress_exact=True,preflight_margin=gap,preflight_path_error=q['distance'],body=base.body(root),native=0,source=0))
 def pins(self):
  for k,h in self.contract['input_sha256'].items():assert d.sha(INPUTS[k])==h,('INPUT',k)
  for p,h in {**self.contract['implementation_sha256'],**self.contract['dependency_sha256']}.items():assert d.sha(Path(p) if Path(p).is_absolute() else G/p)==h,('CODE',p)
 def patch(self,obj,name,value):self.saved.append((obj,name,getattr(obj,name)));setattr(obj,name,value)
 def source(self):
  atomic_write(D/'SOURCE_STARTED-private.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),contract_sha256=d.sha(C),source=0,native=0));self.pc=time.process_time();self.pw=time.perf_counter();self.stage='source'
  for obj,name,fn in [(policy,'tick',self.tick),(policy,'force_rows',self.forecast_force),(policy,'margin',self.forecast_margin),(policy,'project',self.forecast_project),(lap,'project',self.internal_project),(d,'project',self.applied_project),(wheel,'wheel_response',lambda *a,**kw:self.kernel('external_force',self.ext,*a,**kw)),(planar,'wheel_response',lambda *a,**kw:self.kernel('internal_force',self.intern,*a,**kw))]:self.patch(obj,name,fn)
  try:
   for h in range(40,52):
    self.hold=h;self.guard()
    need=dict(model_attempted=1540,model_completed=1540,external_force=6160,internal_force=6160,total_force=12320,geometry=4526,applied_attempted=4,applied_completed=4,chooser_calls=1,certificates=32)
    if not counter_room(self.counts,need):raise Stop('FULL_NEXT_HOLD_RESERVE')
    # Time limits are enforced per primitive and by CPU/real timers; admission reserves audit only.
    if self.times()['source_CPU_s']>405 or self.times()['source_wall_s']>540:raise Stop('NEXT_HOLD_TIME_RESERVE')
    self.journal.append('HOLD_RESERVE',hold=h,counts=dict(self.counts),need=need)
    self.count('chooser_calls');self.seed_root=self.state['root'];before=digest(self.checkpoint());begin=len(self.trials);self.applied=False
    geom=policy.geometry_context(self.static,40000)
    a,detail=policy.choose(self.state['root'],self.paths['candidate'],self.paths['backup'],self.state['progress'],self.model,self.cost,18480,tuple(self.state['tracking']),geom)
    self.finish_trial();assert digest(self.checkpoint())==before,'CHOOSER_MUTATED_ACTUAL_CHECKPOINT'
    expected=records(detail);observed=self.trials[begin:];assert len(expected)==len(observed),'TRIAL_REPORT_COUNT'
    keys=['ok','reason','peak','max_reference_overspeed','clipped','samples','model_ticks','min_footprint_margin_m']
    for old,new in zip(expected,observed):assert all(old[k]==new['summary'][k] for k in keys),('PASSIVE537_SUMMARY_MISMATCH',old,new['summary'])
    choice=dict(hold=h,action=None if a is None else a.tolist(),detail=detail,trial_count=len(observed),passive_summaries_exact=True,actual_checkpoint_unchanged=True)
    self.choices.append(choice);self.journal.append('CHOICE',**choice)
    if a is None:self.status='NO_ADMISSIBLE_ACTION';self.failure=dict(hold=h,reason=self.status);break
    assert detail['final_recertified'] and observed[-1]['summary']['ok'],'FRESH_FINAL_REQUIRED'
    final=observed[-1]['rows'][:4];assert len(final)==4
    self.applied=True
    for k in range(1,5):
     row,why=base.Study.raw(self,self.state,a,h,k,self)
     row['tick_executed']='root_without_roads' in row
     if row['tick_executed']:
      assert digest(row['root_without_roads'])==final[k-1]['root_sha256'] and digest(row['forces'])==digest(final[k-1]['forces']) and row['proposed_history']==final[k-1]['history'],'FINAL_APPLIED_MISMATCH'
      row['fresh_FINAL_exact']=True;flags,first,_=post_flags(row['margin'],row['reference_overspeed'],row['path_error'],row['progress_delta'],row['projection_limit']);row.update(split_flags=flags,split_first_failure=first,projection_lower=-.5)
     self.rows.append(row);self.journal.append('APPLIED_RAW',row=row);atomic_write(D/'latest-checkpoint-private.json',self.checkpoint(),True)
     if why:self.status='APPLIED_STRICT_FAILURE';self.failure=dict(hold=h,raw=k,reason=why,flags=row.get('split_flags'));break
    if self.failure:break
   else:self.status='LOCAL48_STRICT_SAFE_PROGRESS' if self.state['progress']>self.cp['progress'] else 'LOCAL48_SAFE_NO_FORWARD_PROGRESS'
  finally:
   self.scCPU=time.process_time()-self.pc;self.scWall=time.perf_counter()-self.pw;self.stage='analysis'
   for obj,name,value in reversed(self.saved):setattr(obj,name,value)
   self.saved=[]
 def compare(self):
  if not self.rows:return
  old595={q['global_raw']:q for q in d.rd(INPUTS['fixed595'])};old577=d.rd(INPUTS['tape'])['rows'];comparisons=[]
  for r in self.rows:
   if not r.get('tick_executed'):continue
   i=r['global_raw_after'];a=old595[i];b=old577[i-1]
   row=dict(global_raw=i,feedback=dict(progress=r['progress'],speed=math.hypot(*r['root_without_roads']['planar']['linear']['velocity']),path_error=r['path_error'],path_slack=3-r['path_error'],margin=r['margin']),fixed595=dict(progress=a['progress'],speed=math.hypot(*a['root']['planar']['linear']['velocity']),path_error=a['path_error'],path_slack=3-a['path_error']),stored577=dict(progress=b['progress'],speed=math.hypot(*b['root_without_roads']['planar']['linear']['velocity']),path_error=b['path_error'],path_slack=3-b['path_error']))
   comparisons.append(row)
  atomic_write(D/'stored-comparison-private.json',comparisons);self.result['comparison']=dict(rows=len(comparisons),same_global_raw=True,no_new_physics_force_or_geometry=True,first=comparisons[0] if comparisons else None,last=comparisons[-1] if comparisons else None)
 def run(self):
  try:
   self.prepare();self.guard()
   def timer(*_):raise Stop('SOURCE_TIMER_CAP')
   signal.signal(signal.SIGPROF,timer);signal.signal(signal.SIGALRM,timer);signal.setitimer(signal.ITIMER_PROF,450);signal.setitimer(signal.ITIMER_REAL,600)
   try:self.source()
   finally:signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  except BaseException as exc:
   self.error=type(exc).__name__+':'+str(exc);self.status='COST_OR_DOMAIN_STOP' if isinstance(exc,Stop) else 'TECHNICAL_STOP';atomic_write(D/'failure-private.json',dict(error=self.error,traceback=traceback.format_exc()))
  finally:
   for obj,name,value in reversed(self.saved):setattr(obj,name,value)
   self.saved=[]
   if self.stage=='source':self.scCPU=time.process_time()-self.pc;self.scWall=time.perf_counter()-self.pw
   self.stage='analysis'
   atomic_write(D/'applied-rows-private.json',self.rows);atomic_write(D/'trials-private.json',self.trials);atomic_write(D/'choices-private.json',self.choices);atomic_write(D/'final-checkpoint-private.json',self.checkpoint());atomic_write(D/'cost-private.json',dict(counts=dict(self.counts),times=self.times(),original537_cost=self.cost))
   try:self.compare()
   except BaseException as exc:
    self.error=type(exc).__name__+':'+str(exc);self.status='TECHNICAL_STOP';atomic_write(D/'comparison-failure-private.json',dict(error=self.error,traceback=traceback.format_exc()))
   if self.trial is not None:atomic_write(D/'partial-trial-private.json',dict(summary=self.trial.summary(),rows=self.trial.rows,incomplete=True))
   self.journal.append('STUDY_END',status=self.status,counts=dict(self.counts),times=self.times());self.journal.close()
   rows=[r for r in self.rows if r.get('tick_executed')];reasons=Counter(t['summary']['split_first_failure'] or 'SAFE' for t in self.trials)
   self.result.update(study=596,status=self.status,error=self.error,failure=self.failure,applied_raw=len(rows),applied_holds_completed=len(rows)//4,chooser_calls=len(self.choices),certificates=len(self.trials),trial_split_reasons=dict(reasons),all_passive537_summaries_exact=all(q['passive_summaries_exact'] for q in self.choices),all_actual_checkpoints_unchanged_during_choose=all(q['actual_checkpoint_unchanged'] for q in self.choices),fresh_FINAL_applied_exact=bool(rows) and all(r.get('fresh_FINAL_exact') for r in rows),terminal_global_raw=self.state['global_raw'] if self.state else None,progress_gain=self.state['progress']-self.cp['progress'] if self.state else None,minimum_applied_margin=min((r['margin'] for r in rows),default=None),maximum_applied_path=max((r['path_error'] for r in rows),default=None),maximum_applied_force=max((f['ratio'] for r in self.rows for f in r['forces']),default=None),maximum_applied_clip=max((r['proposed_history'][0]/r['proposed_history'][1] for r in self.rows),default=None),maximum_applied_reference_overspeed=max((r['reference_overspeed'] for r in rows),default=None),counts=dict(self.counts),original537_cost=self.cost,times=self.times(),journal=inspect(D/'journal-private.jsonl'),input_sha256={k:d.sha(p) for k,p in INPUTS.items()},private_sha256={p.name:d.sha(p) for p in D.glob('*.json*')},native=0,worlds=0,resets=0,actions=0,HOLDOUT=0,SEALED=0,research_remaining=22548,reserve=84000,reserve_used=0,whole_finish_claim=False,native_gain_claim=False,carry_claim=False,incumbent_promotion=False,subsequent_experiment_executed=False)
   atomic_write(G/'retry/feedback596_result.json',self.result);print(json.dumps(self.result,indent=2))

if __name__=='__main__':
 def forbidden(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN_596')
 CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden
 Study().run()
