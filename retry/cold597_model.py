"""One complete new cold source policy, then conditional independent command replay."""
import time
CPU=time.process_time();WALL=time.perf_counter()
import datetime,inspect as pyinspect,json,math,signal,subprocess,sys,traceback,unittest
from collections import Counter
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from gymnasium.wrappers import TimeLimit
import retry.feedback596_model as meter
from retry.feedback596_model import d,base,policy,lap,wheel,planar,short,Stop,records
from retry.cold597_core import *
from retry.lap518_finish import tracker_for
from retry.clip561_core import atomic_write
from retry.durable568 import Journal,digest
from core.vendor.car_racing import CarRacing,FPS
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response597-private');C=G/'retry/cold597_contract.json'
INPUTS=dict(static=meter.INPUTS['static'],paths=meter.INPUTS['paths'],ledger=meter.INPUTS['ledger'],tape=meter.INPUTS['tape'],case=Path('/workspace/haic-response541-private/approved-case-private.json'),source541=G/'retry/joint541_cold_result.json',source577=G/'retry/direct577_result.json',previous=G/'retry/feedback596_result.json',previous_audit=G/'retry/feedback596_audit.json',proposal=G/'retry/feedback596_next_proposal.json',old593=G/'retry/cold593_result.json',old594=G/'retry/cold594_result.json',old595=G/'retry/cause595_result.json')
CAPS=dict(model_attempted=120000,model_completed=120000,external_force=480000,internal_force=480000,total_force=960000,geometry=400000,applied_attempted=2*MAX_APPLIED,applied_completed=2*MAX_APPLIED,chooser_calls=255,certificates=8160)
PHASE_TIME=dict(main=(1000,1200),replay=(60,90))
PREFIX_KEYS=['before_root_without_roads','root_without_roads','forces','proposed_history','tracker','episode_before_s','episode_after_s','global_raw_before','global_raw_after','tracking_history_before','launch_history_before','visited_count','progress','margin','path_error','reference_overspeed','body']
REPLAY_KEYS=PREFIX_KEYS+['index','raw','action','progress_delta','projection_limit','pre_failure','post_failure','all_failures','visited','checkpoint_sha256']
class Study(meter.Study):
 def __init__(self):
  D.mkdir(mode=0o700,exist_ok=False);atomic_write(D/'PREP_STARTED-private.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source=0,native=0))
  self.counts=Counter();self.phase_counts={};self.phase='preparation';self.phase_cpu=self.phase_wall=None;self.phase_times={};self.model=[0];self.counter=self.model;self.cost=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0,geometry_checks=0)
  self.rows=[];self.replay_rows=[];self.choices=[];self.trials=[];self.trial=None;self.pending=None;self.seed_root=None;self.applied=False;self.hold=None;self.saved=[];self.failure=None;self.status='PREPARATION';self.error=None;self.state=None;self.whole=None;self.replay=None;self.commands=[];self.prefix_rows_exact=0;self.whole_cp=None
  self.orig_project=d.project;self.orig_margin=d.margin;self.ext=wheel.wheel_response;self.intern=planar.wheel_response;self.journal=Journal(D/'journal-private.jsonl')
 def times(self):
  values={k:dict(v) for k,v in self.phase_times.items()}
  if self.phase in PHASE_TIME:values[self.phase]=dict(CPU_s=time.process_time()-self.phase_cpu,wall_s=time.perf_counter()-self.phase_wall)
  tc=time.process_time()-CPU+10.;tw=time.perf_counter()-WALL+10.;sourcecpu=sum(q['CPU_s'] for q in values.values());sourcewall=sum(q['wall_s'] for q in values.values())
  return dict(total_CPU_s=tc,total_wall_s=tw,source_CPU_s=sourcecpu,source_wall_s=sourcewall,preparation_audit_CPU_s=tc-sourcecpu,preparation_audit_wall_s=tw-sourcewall,phases=values)
 def guard(self):
  t=self.times()
  if t['total_CPU_s']>=1200 or t['total_wall_s']>=1500:raise Stop('597_TOTAL_TIME_CAP')
  if t['preparation_audit_CPU_s']>=100 or t['preparation_audit_wall_s']>=150:raise Stop('597_PREPARATION_AUDIT_CAP')
  if self.phase in PHASE_TIME:
   used=t['phases'][self.phase];limit=PHASE_TIME[self.phase]
   if used['CPU_s']>=limit[0] or used['wall_s']>=limit[1]:raise Stop('597_PHASE_TIME_CAP:'+self.phase)
   if t['total_CPU_s']+30>1200 or t['total_wall_s']+45>1500:raise Stop('597_CLEANUP_AUDIT_RESERVE')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,20,10,1,55,tzinfo=datetime.timezone.utc):raise Stop('DEADLINE')
 def count(self,k,n=1):
  self.guard()
  if k in CAPS and self.counts[k]+n>CAPS[k]:raise Stop('597_COST_CAP:'+k)
  self.counts[k]+=n;self.phase_counts.setdefault(self.phase,Counter())[k]+=n
 def pins(self):
  for k,h in self.contract['input_sha256'].items():assert d.sha(INPUTS[k])==h,('INPUT',k)
  for p,h in {**self.contract['implementation_sha256'],**self.contract['dependency_sha256']}.items():assert d.sha(Path(p) if Path(p).is_absolute() else G/p)==h,('CODE',p)
 def initial(self):
  root=d.load_root(self.static['root']);visited=set(self.ledger['initial_visited']);s=self.geometry_query('initial_projection',self.orig_project,root.center,self.paths['candidate'],0.)['s'];tracker=tracker_for(self.static,root,visited,False,EPOCH)
  state=dict(root=root,progress=s,visited=visited,tracker=tracker,elapsed=0.,global_raw=0,launch=[0,0],tracking=[0,0]);gap=self.geometry_query('initial_footprint',self.orig_margin,root,self.static['roads'],self.index,self.static['boundary'],self.edge,self.static['obstacles'])
  assert gap>=.5 and base.body(root)<100 and tracker.finish_time_s is None,'INITIAL_DOMAIN'
  return state
 def prepare(self):
  self.guard()
  for k in ['static','paths','ledger','tape']:assert d.sha(INPUTS[k])==meter.EXPECTED[k],('ORIGINAL_PIN',k)
  assert d.sha(INPUTS['case'])=='5a3f5677267d25c6a69b1b9190e73ff1f35558caf123162e7e385efbfd21dcc8'
  assert d.sha(INPUTS['previous'])=='6435f703c35c513f280e12058285f5f34c62352f4b7c75e036b8575eb89534ef'
  assert d.sha(G/'retry/structure537_control.py')=='c5a3f3206979085150e8ecda4f96da4b76f74ff4e9064bc3f5b9e3eb8d62c771'
  assert subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31'
  assert not subprocess.check_output(['git','diff','--name-only','main','--','Participants'],cwd=G,text=True).strip()
  self.static=d.rd(INPUTS['static']);self.paths=d.rd(INPUTS['paths']);self.ledger=d.rd(INPUTS['ledger']);self.tape=d.rd(INPUTS['tape']);self.case=d.rd(INPUTS['case']);self.index=d.bounds(self.static['roads']);self.edge=d.boundary_index(self.static['boundary']);self.fixed={q['index']:np.asarray(q['action'],np.float32) for q in self.tape['commands'] if q['index']<=39}
  assert digest(self.static['roads'])==digest(self.static['root']['roads']),'STATIC_ROOT_ROADS_EXACT'
  assert self.case['TimeLimit_max_episode_steps']==TIME_LIMIT and self.case['wrapper']['no_operation']==WARMUP and self.case['wrapper']['skip_frames']==4 and FPS==50
  assert 'self._elapsed_steps = 0' in pyinspect.getsource(TimeLimit.reset) and 'self._elapsed_steps += 1' in pyinspect.getsource(TimeLimit.step) and 'self._elapsed_steps >= self._max_episode_steps' in pyinspect.getsource(TimeLimit.step)
  assert 'return self.step(None)[0], {}' in (G/'core/vendor/car_racing.py').read_text() and 'range(self._no_operation)' in (G/'env_wrapper.py').read_text()
  assert official_raw(self.tape['checkpoint']['tracker']['finish_time_s'])==660 and len(self.tape['rows'])==661 and d.rd(INPUTS['source541'])['case']['pass_safety'] and official_raw(EPOCH+d.rd(INPUTS['source541'])['case']['model_finish_episode_s'])==683
  suite=unittest.TestSuite([unittest.defaultTestLoader.discover(str(G/'tests'),pattern='test_cold597.py'),unittest.defaultTestLoader.discover(str(G/'tests'),pattern='test_feedback596.py')]);tests=unittest.TextTestRunner(stream=sys.stderr).run(suite);assert tests.wasSuccessful()
  atomic_write(G/'retry/cold597_tests.json',dict(passed=True,tests=tests.testsRun,source=0,native=0,input_sha256={p:d.sha(G/p) for p in ['retry/cold597_core.py','tests/test_cold597.py','retry/feedback596_model.py','retry/feedback596_trace.py','tests/test_feedback596.py']}))
  local={str(Path(m.__file__).resolve().relative_to(G)):d.sha(Path(m.__file__).resolve()) for m in tuple(sys.modules.values()) if getattr(m,'__file__',None) and Path(m.__file__).is_file() and Path(m.__file__).resolve().is_relative_to(G) and '.venv' not in Path(m.__file__).parts}
  local.update({p:d.sha(G/p) for p in ['retry/cold597_model.py','retry/cold597_core.py','retry/cold597_audit.py','tests/test_cold597.py','env_wrapper.py','local_runner.py','core/vendor/car_racing.py','core/finish_line.py']})
  deps={str(Path(m.__file__).resolve()):d.sha(Path(m.__file__).resolve()) for m in tuple(sys.modules.values()) if getattr(m,'__file__',None) and Path(m.__file__).is_file() and (not Path(m.__file__).resolve().is_relative_to(G) or '.venv' in Path(m.__file__).parts)}
  self.contract=dict(study=597,status='FROZEN_AFTER_PURE_TESTS_BEFORE_SOURCE',registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55Z',parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip(),input_sha256={k:d.sha(p) for k,p in INPUTS.items()},implementation_sha256=local,dependency_sha256=deps,tests_sha256=d.sha(G/'retry/cold597_tests.json'),caps=CAPS,time_caps=dict(total_CPU_s=1200,total_wall_s=1500,preparation_audit_CPU_s=100,preparation_audit_wall_s=150,main_CPU_s=1000,main_wall_s=1200,replay_CPU_s=60,replay_wall_s=90),time_limit=dict(approved_case_max_elapsed_steps=TIME_LIMIT,warmup_TimeLimit_steps=WARMUP,max_policy_applied_raw=MAX_APPLIED,reset_internal_step_counted_by_TimeLimit=0,reset_internal_physics_raw=1,total_reset_physics_raw=51,source_epoch=EPOCH,dt=DT,skip_frames=4,clock='1.02+actualrawelapsed;elapsed+=.02eachraw,matchingoldsourcefloataccumulation',finish='UnchangedFinishLineTracker:qualification95%,departure/forwardcrossing/width/halfdepthconfirmation. officialcandidateintegerraw=round((finish_time-1.02)/.02);confirmationrawdistinct.No interpolatedtimeobjective. OriginalfinishfirstthenTimeLimitcheckatsameterminalraw,neverexecuteafterconfirmationor1174raw.'),spec='Exactlyonecoldsourceepisodefrompinnedoriginalpostreset/warmupstaticinitialstate+initialvisited+tracker_for(carryFalse).577fixedfloat32commands1..39,from40unchanged537chooseuntilofficialconfirmation/failure;neverreturntofixedtapeat52. Original551paths/backup/reference/cap,gains,physics,strictlaunch/trackinggates,finite31trials+freshFINALunchanged. Reuse596passivemeterswithallinternalnominal/steeringgeometry,bothwheeloracles,prefixcountsandnewFINALfirst4exact. Everytrialactualhistoryindependent;actualCPimmutableduringchoose.',strict='Launchglobalholds1..24:force<=2.5,clip<=.15checkedfromhold24,no referenceveto. Tracking25+:force<=literal1.059,clip<=.10,referenceexcess<=4.85. Everyappliedrawfootprint>=.5,path<=3,projectiondelta[-.5,max(5,2COMstepdistance)],allforecast/appliedbody<100. Original537forecastADMISSIONbinary64unchanged. Firstappliedstrict/noadmissibleaction/domain/technical/IO/integrity/cost/deadlinestops,no retry/fallback/tuning.',prefix='Readstored577first156rowsandinitialvisited;eachnewprefixrawbefore/afterroot,forcevectors/ratio/clips,bothhistories,clock,fulltracker,progress/geometry/bodymustexactmatch. ReconstructstoredvisitedsetfromstoredcontactsandcompareactualfullsetatEVERYprefixraw. Prefixintegrationchargednew,notread-onlysimulationclaim.',verification='OnlywholestrictsafefinishwithnoerrorallowsONEindependentreplayofnewrecordedfloat32commandtapeFROMsameoriginalinitialstate. Nochooserinreplay. Everyrowbefore/afterroot,forces,histories,fullvisited/tracker,clock,checkpointSHAandfinishmustexactmatch;stoponfirstmismatch. Neverreplayfailedwhole. Bothprefixandconditionalreplaychargedasnewphysics.',reservation='Beforeeachmainholdreserveworstwholehold1540model/12320totalforce/4526geometryforfeedback,4/32/8forprefix,PLUSentireconditionalreplay1174model/9392totalforce/2350geometryincludinginitialqueries. Beforemainstartreserve1000CPU1200wallmain+60CPU90wallreplay+30CPU45wallcleanupbeforetotalcaps/deadline;eachmainholdreserve45CPU60wallfeedbackor2CPU3wallprefixplusreplay60/90andcleanup30/45. Replayreserveactualremainingraw+cleanup;noquery/callbeyondcapacity. Alltrial/FINAL/rejectedcostincluded. Originalsourcekernel200000unchanged,strongerglobal120000. Prep10CPU/wallconservativechargeplusallimports/tests/pins/serialization/analysis/auditmeasured.',comparison='Officialintegerfinishrawvs577source660/13.20and541source683/13.66separately.Onlyverifiedwholefinishcomparisons;nointerpolation/localpathgainpromotion. Nativeincumbentunchanged,nonnativepolicyonly.',privacy='Designatedcloudonly;fullroots/commands/visited/tracker/seed/map/transcript/journalprivateoutsideGit.Publictechnicalcode/hash/aggregates.PreservemainParticipantsuserchangesbackups593..596andoldcosts.',research_remaining=22548,reserve=84000,reserve_used=0,scope=dict(native=0,worlds=0,resets=0,actions=0,HOLDOUT=0,SEALED=0,new_seed=0,carry=0,paid=0,FD=0,solver=0))
  atomic_write(C,self.contract);atomic_write(D/'REGISTERED-private.json',dict(contract_sha256=d.sha(C)));self.pins();self.state=self.initial();atomic_write(D/'initial-checkpoint-private.json',self.checkpoint());self.initial_sha=digest(self.checkpoint());assert digest(short(replace(self.state['root'],planar=replace(self.state['root'].planar,steer=-float(self.fixed[1][0])))))==digest(self.tape['rows'][0]['before_root_without_roads'])
  atomic_write(G/'retry/cold597_preflight.json',dict(initial_checkpoint_sha256=self.initial_sha,first577_preforce_root_exact=True,original_policy_pinned=True,original_paths_pinned=True,time_limit=self.contract['time_limit'],pure_tests=tests.testsRun,baseline_source_raw=dict(source577=660,source541=683),source=0,native=0))
 def start_phase(self,label):
  self.guard();needcpu,needwall=PHASE_TIME[label]
  tailcpu,tailwall=(90,135) if label=='main' else (30,45)
  if self.times()['total_CPU_s']+needcpu+tailcpu>1200 or self.times()['total_wall_s']+needwall+tailwall>1500:raise Stop('597_FULL_PHASE_TIME_RESERVE')
  if (datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(seconds=needwall+tailwall))>=datetime.datetime(2026,10,20,10,1,55,tzinfo=datetime.timezone.utc):raise Stop('597_DEADLINE_PHASE_RESERVE')
  atomic_write(D/(label.upper()+'_STARTED-private.json'),dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),contract_sha256=d.sha(C),counts=dict(self.counts)))
  self.phase=label;self.phase_cpu=time.process_time();self.phase_wall=time.perf_counter();self.phase_counts.setdefault(label,Counter());self.journal.append('PHASE_START',phase=label,counts=dict(self.counts))
  def timer(*_):raise Stop('597_PHASE_TIMER:'+label)
  signal.signal(signal.SIGPROF,timer);signal.signal(signal.SIGALRM,timer);signal.setitimer(signal.ITIMER_PROF,needcpu);signal.setitimer(signal.ITIMER_REAL,needwall)
 def end_phase(self):
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  if self.phase in PHASE_TIME:
   label=self.phase;self.phase_times[label]=dict(CPU_s=time.process_time()-self.phase_cpu,wall_s=time.perf_counter()-self.phase_wall);self.phase='analysis';self.journal.append('PHASE_END',phase=label,counts=dict(self.counts),time=self.phase_times[label]);atomic_write(D/(label+'-cost-private.json'),dict(counts=dict(self.phase_counts[label]),times=self.phase_times[label]))
 def install(self):
  for obj,name,fn in [(policy,'tick',self.tick),(policy,'force_rows',self.forecast_force),(policy,'margin',self.forecast_margin),(policy,'project',self.forecast_project),(lap,'project',self.internal_project),(d,'project',self.applied_project),(wheel,'wheel_response',lambda *a,**kw:self.kernel('external_force',self.ext,*a,**kw)),(planar,'wheel_response',lambda *a,**kw:self.kernel('internal_force',self.intern,*a,**kw))]:self.patch(obj,name,fn)
 def reserve_hold(self,feedback):
  self.guard();req=reserve_request(feedback,self.phase=='main')
  if not fits(self.counts,req,CAPS):raise Stop('597_NEXT_HOLD_AND_REPLAY_COST_RESERVE')
  t=self.times();current=t['phases'][self.phase];hc,hw=(45,60) if feedback else (2,3)
  if self.phase=='main':
   if current['CPU_s']+hc>1000 or current['wall_s']+hw>1200 or t['total_CPU_s']+hc+60+30>1200 or t['total_wall_s']+hw+90+45>1500:raise Stop('597_NEXT_HOLD_REPLAY_CLEANUP_TIME_RESERVE')
  else:
   remaining=self.whole['raw']-self.state['global_raw'];req=dict(model_attempted=remaining,model_completed=remaining,external_force=4*remaining,internal_force=4*remaining,total_force=8*remaining,geometry=2*remaining)
   if not fits(self.counts,req,CAPS):raise Stop('597_REPLAY_REMAINDER_RESERVE')
   if t['total_CPU_s']+2+30>1200 or t['total_wall_s']+3+45>1500:raise Stop('597_REPLAY_CLEANUP_TIME_RESERVE')
  self.journal.append('HOLD_RESERVE',phase=self.phase,hold=self.hold,feedback=feedback,requests=req,counts=dict(self.counts))
 def choose(self,h):
  self.count('chooser_calls');self.seed_root=self.state['root'];before=digest(self.checkpoint());begin=len(self.trials);self.applied=False
  a,detail=policy.choose(self.state['root'],self.paths['candidate'],self.paths['backup'],self.state['progress'],self.model,self.cost,120000,tuple(self.state['tracking']),policy.geometry_context(self.static,400000));self.finish_trial();assert digest(self.checkpoint())==before,'CHOOSER_MUTATED_ACTUAL_CHECKPOINT'
  old=records(detail);observed=self.trials[begin:];assert len(old)==len(observed),'TRIAL_REPORT_COUNT';keys=['ok','reason','peak','max_reference_overspeed','clipped','samples','model_ticks','min_footprint_margin_m']
  for report,new in zip(old,observed):assert all(report[k]==new['summary'][k] for k in keys),'PASSIVE537_SUMMARY_MISMATCH'
  choice=dict(hold=h,action=None if a is None else a.tolist(),detail=detail,trial_count=len(observed),passive_summaries_exact=True,actual_checkpoint_unchanged=True);self.choices.append(choice);self.journal.append('CHOICE',**choice)
  if a is not None:assert detail['final_recertified'] and observed[-1]['summary']['ok'],'FRESH_FINAL_REQUIRED'
  return a,None if a is None else observed[-1]['rows'][:4]
 def applied_raw(self,a,h,k,final=None):
  self.applied=True;row,why=base.Study.raw(self,self.state,a,h,k,self);row['tick_executed']='root_without_roads' in row
  if row['tick_executed']:
   if final is not None:
    z=final[k-1];assert digest(row['root_without_roads'])==z['root_sha256'] and digest(row['forces'])==digest(z['forces']) and row['proposed_history']==z['history'],'FINAL_APPLIED_MISMATCH';row['fresh_FINAL_exact']=True
   row['visited']=sorted(self.state['visited']);row['checkpoint_sha256']=digest(self.checkpoint());row['official_finish_raw']=official_raw(self.state['tracker'].finish_time_s)
  self.journal.append('APPLIED_RAW',phase=self.phase,row=row);atomic_write(D/(self.phase+'-latest-checkpoint-private.json'),self.checkpoint(),True);return row,why
 def main_episode(self):
  status='TIME_LIMIT';failure=None;expectedvisited=set(self.ledger['initial_visited'])
  for h in range(1,math.ceil(MAX_APPLIED/4)+1):
   self.hold=h;self.reserve_hold(h>=40)
   if h<=39:a=self.fixed[h];final=None
   else:
    a,final=self.choose(h)
    if a is None:status='NO_ADMISSIBLE_ACTION';failure=dict(hold=h,reason=status);break
   self.commands.append(dict(index=h,action=a.tolist()))
   for k in range(1,5):
    if WARMUP+self.state['global_raw']>=TIME_LIMIT:break
    row,why=self.applied_raw(a,h,k,final);self.rows.append(row)
    if why:status='APPLIED_STRICT_FAILURE';failure=dict(hold=h,raw=k,reason=why,global_raw=self.state['global_raw'],row_index=len(self.rows)-1);break
    if h<=39:
     old=self.tape['rows'][len(self.rows)-1]
     for ids in old['root_without_roads']['current_contacts']:expectedvisited.update(ids)
     assert all(digest(row[key])==digest(old[key]) for key in PREFIX_KEYS) and self.state['visited']==expectedvisited,'PREFIX577_EXACT_MISMATCH';self.prefix_rows_exact+=1
    if self.state['tracker'].finish_time_s is not None:status='WHOLE_STRICT_SAFE_OFFICIAL_FINISH';break
    if WARMUP+self.state['global_raw']>=TIME_LIMIT:status='TIME_LIMIT';failure=dict(hold=h,raw=k,reason=status,global_raw=self.state['global_raw']);break
   if failure or status=='WHOLE_STRICT_SAFE_OFFICIAL_FINISH':break
  self.whole_cp=self.checkpoint();self.whole=dict(status=status,safe=status=='WHOLE_STRICT_SAFE_OFFICIAL_FINISH' and failure is None,failure=failure,raw=self.state['global_raw'],applied_attempts=len(self.rows),commands=len(self.commands),official_candidate_raw=official_raw(self.state['tracker'].finish_time_s),confirmation_raw=self.state['global_raw'] if self.state['tracker'].finish_time_s is not None else None,prefix_rows_exact=self.prefix_rows_exact,final_checkpoint_sha256=digest(self.whole_cp));self.status=status;self.failure=failure;atomic_write(D/'whole-episode-private.json',dict(summary=self.whole,checkpoint=self.whole_cp,commands=self.commands,rows=self.rows))
 def replay_episode(self):
  assert replay_allowed(self.status,self.error) and self.whole['safe'],'FAILED_WHOLE_REPLAY_FORBIDDEN';self.state=self.initial();assert digest(self.checkpoint())==self.initial_sha,'REPLAY_INITIAL_MISMATCH';commands={q['index']:np.asarray(q['action'],np.float32) for q in self.commands}
  for old in self.rows:
   h,k=old['index'],old['raw'];self.hold=h
   if k==1:self.reserve_hold(False)
   row,why=self.applied_raw(commands[h],h,k);self.replay_rows.append(row)
   assert not why and all(digest(row[key])==digest(old[key]) for key in REPLAY_KEYS),'INDEPENDENT_REPLAY_ROW_MISMATCH'
   assert (row['official_finish_raw'] is not None)==(old['official_finish_raw'] is not None),'INDEPENDENT_REPLAY_FINISH_MISMATCH'
  assert digest(self.checkpoint())==digest(self.whole_cp),'INDEPENDENT_REPLAY_FINAL_CHECKPOINT_MISMATCH';self.replay=dict(exact=True,raw=len(self.replay_rows),initial_checkpoint_exact=True,final_checkpoint_exact=True,all_roots_forces_histories_visited_tracker_clock_exact=True,official_candidate_raw=official_raw(self.state['tracker'].finish_time_s),confirmation_raw=self.state['global_raw']);self.status='WHOLE_SOURCE_FINISH_INDEPENDENTLY_VERIFIED';atomic_write(D/'independent-replay-private.json',dict(summary=self.replay,checkpoint=self.checkpoint(),rows=self.replay_rows));atomic_write(D/'final-independent-tape-private.json',dict(commands=self.commands,rows=self.replay_rows,checkpoint=self.checkpoint(),exact=True))
 def run(self):
  try:
   self.prepare();self.start_phase('main');self.install()
   try:self.main_episode()
   finally:self.end_phase()
   if replay_allowed(self.status,self.error):
    self.start_phase('replay')
    try:self.replay_episode()
    finally:self.end_phase()
  except BaseException as exc:
   self.error=type(exc).__name__+':'+str(exc);self.status='COST_OR_DOMAIN_STOP' if isinstance(exc,Stop) else 'TECHNICAL_STOP';atomic_write(D/'failure-private.json',dict(error=self.error,traceback=traceback.format_exc(),phase=self.phase))
  finally:
   self.end_phase()
   for obj,name,value in reversed(self.saved):setattr(obj,name,value)
   self.saved=[];self.phase='analysis';atomic_write(D/'applied-rows-private.json',self.rows);atomic_write(D/'replay-rows-private.json',self.replay_rows);atomic_write(D/'trials-private.json',self.trials);atomic_write(D/'choices-private.json',self.choices);atomic_write(D/'final-checkpoint-private.json',self.checkpoint());atomic_write(D/'commands-private.json',self.commands)
   if self.trial is not None:atomic_write(D/'partial-trial-private.json',dict(summary=self.trial.summary(),rows=self.trial.rows,incomplete=True))
   self.journal.append('STUDY_END',status=self.status,counts=dict(self.counts),phase_counts=self.phase_counts,times=self.times());self.journal.close()
   raw=[q for q in self.rows if q.get('tick_executed')];verified=self.replay is not None and self.replay['exact'] and self.error is None;n=self.whole['official_candidate_raw'] if self.whole else None
   comparisons={label:dict(baseline_source_raw=b,baseline_source_s=b*DT,candidate_source_raw=n,candidate_source_s=n*DT if n else None,gain_raw=b-n if verified else None,gain_ms=(b-n)*20 if verified else None,strictly_earlier=bool(verified and n<b)) for label,b in [('stored577',660),('stored541',683)]}
   result=dict(study=597,status=self.status,error=self.error,failure=self.failure,whole=self.whole,replay=self.replay,whole_source_verified=verified,official_integer_comparison=comparisons,applied_raw=len(raw),applied_attempts=len(self.rows),replay_raw=len(self.replay_rows),chooser_calls=len(self.choices),certificates=len(self.trials),trial_split_reasons=dict(Counter(t['summary']['split_first_failure'] or 'SAFE' for t in self.trials)),prefix39_exact=self.prefix_rows_exact==156,prefix_rows_exact=self.prefix_rows_exact,passive537_summaries_exact=all(q['passive_summaries_exact'] for q in self.choices),chooser_actual_checkpoints_unchanged=all(q['actual_checkpoint_unchanged'] for q in self.choices),fresh_FINAL_applied_exact=all(q.get('fresh_FINAL_exact') for q in raw if q['index']>=40),minimum_applied_margin=min((q['margin'] for q in raw),default=None),maximum_applied_path=max((q['path_error'] for q in raw),default=None),maximum_applied_tracking_force=max((f['ratio'] for q in self.rows if q['index']>=25 for f in q['forces']),default=None),maximum_applied_launch_force=max((f['ratio'] for q in self.rows if q['index']<=24 for f in q['forces']),default=None),maximum_applied_tracking_clip=max((q['proposed_history'][0]/q['proposed_history'][1] for q in self.rows if q['index']>=25),default=None),maximum_checked_launch_clip=max((q['proposed_history'][0]/q['proposed_history'][1] for q in self.rows if q['index']==24),default=None),maximum_applied_tracking_reference_excess=max((q['reference_overspeed'] for q in raw if q['index']>=25),default=None),counts=dict(self.counts),phase_counts=self.phase_counts,original537_cost=self.cost,times=self.times(),input_sha256={k:d.sha(p) for k,p in INPUTS.items()},private_sha256={p.name:d.sha(p) for p in D.glob('*.json*')},native=0,worlds=0,resets=0,actions=0,new_seed=0,HOLDOUT=0,SEALED=0,carry=0,research_remaining=22548,reserve=84000,reserve_used=0,native_incumbent_s=13.66,native_incumbent_changed=False,subsequent_native_executed=False)
   atomic_write(G/'retry/cold597_result.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':
 def forbidden(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN_597')
 CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden
 Study().run()
