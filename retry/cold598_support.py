"""598 frozen budgets, transition policy and passive model/native meters."""
from retry.cold594_native import *
import retry.cold594_native as previous
import retry.lap518_control as lap
from retry.cold598_transition import certify as prefix_certificate
from retry.feedback596_trace import Trial,post_flags
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response598-private');C=G/'retry/cold598_contract.json'
INPUTS={k:previous.INPUTS[k] for k in ['tape','case','baseline_paths','candidate_paths','static','ledger','baseline_contract','carry_failure']}
INPUTS.update({f'old{x}':G/f'retry/{name}_result.json' for x,name in [(593,'cold593'),(594,'cold594'),(595,'cause595'),(596,'feedback596'),(597,'cold597')]});INPUTS.update(source597_contract=G/'retry/cold597_contract.json',source597_audit=G/'retry/cold597_audit.json',proposal=G/'retry/cold597_next_review.json')
CAPS=dict(worlds=2,resets=2,raw_attempts=2450,native_raw_calls=2450,actions=588,action_calls=588,model_attempted=180000,model_completed=180000,external_force=730000,internal_force=720000,total_force=1450000,native_wheel_reserved=9800,native_wheel_observed=9800,geometry=600000)
LIMITS={k:dict(model_attempted=90000,model_completed=90000,external_force=365000,internal_force=360000,total_force=725000,geometry=300000,actions=294,raw_attempts=1225,native_wheel_reserved=4900,CPU_s=cpu,wall_s=wall) for k,cpu,wall in [('baseline',2000,2300),('candidate',1600,1900)]}
class Support(previous.Study):
 def __init__(self,cpu,wall):
  self.bootCPU=cpu;self.bootWall=wall;D.mkdir(mode=0o700,exist_ok=False);self.counts=Counter();self.arm_counts=Counter();self.model=[0];self.arms=[];self.stage='preparation';self.label=None;self.pending=None;self.scienceCPU=self.scienceWall=0.;self.prior=10.;self.result={};self.native_live=self.env_live=None;self.originals={};self.current=None;self.model_mode='preparation';self.active_trial=None;self.trial_summaries=[];self.diag=None;self.last_model_before=self.last_model_after=None;self.journal=Journal(D/'journal-private.jsonl');self.register()
 def times(self):
  active=self.stage=='science';sc=self.scienceCPU+(time.process_time()-self.scCPU if active else 0);sw=self.scienceWall+(time.perf_counter()-self.scWall if active else 0);tc=time.process_time()-self.bootCPU+10;tw=time.perf_counter()-self.bootWall+10;return dict(science_CPU_s=sc,science_wall_s=sw,preparation_audit_CPU_s=tc-sc,preparation_audit_wall_s=tw-sw,total_CPU_s=tc,total_wall_s=tw)
 def guard(self,*a):
  limits=dict(science_CPU_s=3600,science_wall_s=4200,preparation_audit_CPU_s=180,preparation_audit_wall_s=240,total_CPU_s=3780,total_wall_s=4440)
  for k,v in self.times().items():
   if v>=limits[k]:raise CostStop('598_'+k)
  if self.stage=='science':
   if time.process_time()-self.armCPU>=LIMITS[self.label]['CPU_s'] or time.perf_counter()-self.armWall>=LIMITS[self.label]['wall_s']:raise CostStop('ARM_TIME_CAP')
  if self.stage!='audit' and (self.times()['preparation_audit_CPU_s']>=150 or self.times()['preparation_audit_wall_s']>=195):raise CostStop('FINAL_AUDIT_30CPU45WALL_RESERVE')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,20,10,1,55,tzinfo=datetime.timezone.utc):raise CostStop('DEADLINE')
 def capacity(self,req):
  self.guard()
  for k,n in req.items():
   if k in CAPS and self.counts[k]+n>CAPS[k]:raise CostStop('AGGREGATE_'+k)
   if self.stage=='science' and k in LIMITS[self.label] and self.arm_counts[k]+n>LIMITS[self.label][k]:raise CostStop('ARM_'+k)
 def add(self,k,n=1):
  if k in CAPS and self.counts[k]+n>CAPS[k]:raise CostStop('ADD_AGGREGATE_'+k)
  if self.stage=='science' and k in LIMITS[self.label] and self.arm_counts[k]+n>LIMITS[self.label][k]:raise CostStop('ADD_ARM_'+k)
  self.counts[k]+=n
  if self.stage=='science':self.arm_counts[k]+=n
 def reserve_hold(self):
  h=self.arm_counts['actions']+1;transition=self.label=='candidate' and h<=39 and h+11>=40;n=1588 if transition else 1540 if self.label=='baseline' or h>=40 else 52
  req=dict(model_attempted=n,model_completed=n,external_force=4*n+16,internal_force=4*n,total_force=8*n+16,geometry=5000 if n>52 else 300,actions=1,raw_attempts=4,native_raw_calls=4,native_wheel_reserved=16)
  self.capacity(req)
  if time.process_time()-self.armCPU+65>LIMITS[self.label]['CPU_s'] or time.perf_counter()-self.armWall+85>LIMITS[self.label]['wall_s']:raise CostStop('NEXT_HOLD_AND_CLOSE_RESERVE')
  if self.times()['science_CPU_s']+65>3600 or self.times()['science_wall_s']+85>4200:raise CostStop('EXECUTION_CLEANUP_RESERVE')
  if (datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(seconds=130))>=datetime.datetime(2026,10,20,10,1,55,tzinfo=datetime.timezone.utc):raise CostStop('HOLD_DEADLINE_AND_AUDIT_RESERVE')
  self.journal.append('HOLD_RESERVE',label=self.label,next_hold=h,transition_anchor_possible=transition,requests=req,CPU_s=60,wall_s=75,close_CPU_s=5,close_wall_s=10,counts=dict(self.counts))
 def world_reserve(self,label):
  self.guard();lim=LIMITS[label]
  if label=='baseline':req={k:v for k,v in CAPS.items() if k not in ['native_wheel_observed','native_raw_calls','action_calls']};cpu=3600;wall=4200
  else:req={k:v for k,v in lim.items() if k not in ['CPU_s','wall_s']};req.update(worlds=1,resets=1);cpu=lim['CPU_s'];wall=lim['wall_s']
  self.capacity(req)
  if self.times()['science_CPU_s']+cpu>3600 or self.times()['science_wall_s']+wall>4200:raise CostStop('WHOLE_ARM_TIME_RESERVE')
  if (datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(seconds=wall+45))>=datetime.datetime(2026,10,20,10,1,55,tzinfo=datetime.timezone.utc):raise CostStop('WHOLE_ARM_DEADLINE_RESERVE')
  self.journal.append('WORLD_RESERVE',label=label,requests=req,limits=lim,candidate_reserved=label=='baseline',CPU_s=cpu,wall_s=wall)
 def register(self):
  tests=unittest.TextTestRunner(stream=sys.stderr).run(unittest.TestSuite([unittest.defaultTestLoader.discover(str(G/'tests'),pattern='test_cold594.py'),unittest.defaultTestLoader.discover(str(G/'tests'),pattern='test_cold598.py'),unittest.defaultTestLoader.discover(str(G/'tests'),pattern='test_feedback596.py')]))
  if not tests.wasSuccessful():raise IdentityStop('PURE_TEST_FAILURE_WORLD0')
  files=['retry/cold598_native.py','retry/cold598_support.py','retry/cold598_transition.py','retry/cold598_audit.py','tests/test_cold598.py','retry/cold594_logging.py','tests/test_cold594.py','tests/test_cold593.py','retry/feedback596_trace.py']
  atomic_write(G/'retry/cold598_tests.json',dict(passed=True,tests=tests.testsRun,source=0,worlds=0,native=0,input_sha256={p:d.sha(G/p) for p in files if (G/p).exists()}))
  local={str(Path(m.__file__).resolve().relative_to(G)):d.sha(Path(m.__file__).resolve()) for m in tuple(sys.modules.values()) if getattr(m,'__file__',None) and Path(m.__file__).is_file() and Path(m.__file__).resolve().is_relative_to(G) and '.venv' not in Path(m.__file__).parts};local.update({p:d.sha(G/p) for p in files})
  deps={str(Path(m.__file__).resolve()):d.sha(Path(m.__file__).resolve()) for m in tuple(sys.modules.values()) if getattr(m,'__file__',None) and Path(m.__file__).is_file() and ('.venv' in Path(m.__file__).parts or not Path(m.__file__).resolve().is_relative_to(G))}
  for package in [Box2D,cv2,pygame]:
   for p in [*Path(package.__file__).parent.glob('*.so'),*Path(package.__file__).parent.glob('*.ttf')]:deps[str(p.resolve())]=d.sha(p)
  self.contract=dict(study=598,status='FROZEN_AFTER_PURE_TESTS_BEFORE_ALL_WORLDS',registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55Z',parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip(),input_sha256={k:d.sha(p) for k,p in INPUTS.items()},implementation_sha256=local,dependency_sha256=deps,tests_sha256=d.sha(G/'retry/cold598_tests.json'),caps=CAPS,arm_caps=LIMITS,time_caps=dict(science_CPU_s=3600,science_wall_s=4200,preparation_audit_CPU_s=180,preparation_audit_wall_s=240,total_CPU_s=3780,total_wall_s=4440),spec='ONEfreshunchanged541coldbaselinewith540launchfirst24/537tracking/FINALand541paths,requiringinitialfullidentity,safe683officialrawand683driveraw,thenONE597policy:577float32commands1..39andfrom40unchanged537choosefromACTUALnativecurrentroot/ACTUALclippinghistorythroughofficialconfirmation.No52switchback,candidate551pathsAND551backup/reference/capunchanged.',transition_semantics='Before39fixedprefixactualpayloadstays577. EachprefixadmissionfromACTUALcurrentroot/tracker/visited/clock/historieshas12OUTERholds:futureh<=39exact577bytes;iffuture40reachedcalloriginal537chooseONCEonFORECAST40root/historywithfreshFINAL;futureh>=41usesunchanged537backupfromeachforecastroot. Nofixedtape40+,nonestedreplanningat41+,noadditionalfeedbackfamily. Original537anchorinternalcertificate12holds40..51canextendbeyondouterhorizon;allcostcounted. ACTUALnative40+replans537EVERYholdfromactualroot/history. Thusforecastbackupisfiniteadmissionwitness,notclaimallfuturepolicycommandsidentical. Prefixgatecanconservativelyrejectevenifeventualreplanningwouldpass;firstrejectionterminateswholetrial.',transition_bounds='AtmostONEfuture40chooserperprefixcertificate(h29..39only),<=32*48anchorraw+48outerprefixraw+4prediction=1588model/hold. Ordinaryfeedback<=32*48+4=1540;nontransitionprefix48+4=52. Neverrecursivechoosefromanchorforecasts,whichuseoriginalbackup. Perholdgeometry5000boundincludinginternalnominal/steering+postprojections/margins+prediction/nativequeries;cheap52holds300. Baseline540launchworst<=20filters*4+6full*36*4+4prediction=948model<1540;horizoninternalqueriescoveredby5000.',time_limit=dict(TimeLimit=1224,warmup=50,reset_internal_outside_TimeLimit=1,reset_physics=51,max_drive_raw=1174,max_action_holds=294,dt=.02,epoch=1.02),source_safety='UNCHANGEDlaunchglobal1..24force2.5/clip.15atend24,noreferenceveto;tracking1.059literal/clip.10/referenceexcess4.85;footprint.50/path3/projection[-.5,max(5,2COMstep)];allmodelbody<100. Original537ADMISSIONbinary64and540bufferedlaunchcertunchanged. 4rawconstantcurrentactionpreviewunchangedforphysicalerror:all4bodychecks,sourceadmissionbyoriginalchooser/certificate;noextraadmissionafterpredictedfinish. Actualofficialfinishaloneendswrapper.',native_safety='UNCHANGEDphysicaltrackingforce1.25/reference5/footprint.25/clip.10;launch2.5/clip.15;allbody<100;collision/damage0,payload/sensor/effects/observationidentity,sourceoracle.05N,COMimpulse.01m/s,4rawposition.10m/speed.15m/s/angle.02/yaw.05/force_ratio_error.19. DetailedPATH/projectionflagswithoriginaldecisionorder.',metering='Allrejectedtrial/FINAL/transitionanchor+outer+4rawpreviewcounted;external+internalwheeloraclescounttowardtotalforce;nativewheelobservedseparate. ChargeALLhighlevelmargin/projectionpacksincludinglapnominal/steering,tracking/launch/previewandnatived.project;modelcontactinternalsincludedtickcost. fsyncedcompleteState/asdictinputbeforeactualphysics;raw/action/world/resetreservationsdistinctfromdispatchcallcounters. Primitivejournalroot/ratio/bodyandPATH/projectionnumbersprivate;537passivesummaryexact.',reservation='BeforebaselineallocateBOTH90kmodel/365kexternal/360kinternal/725ktotal/300kgeometry/294actions/1225raw/4900nativewheelperarm. Baseline2000CPU2300wall,candidate1600CPU1900wall(sum3600/4200)inclworldinit/close. Eachholdbookfullchooser+prediction+4nativeoracle/raw+5CPU10wallclose;60CPU75wallhold. Finalaudit30CPU45wallreservedinprep180/240. Prior10CPU/wallconservativeprepchargeandallimports/tests/hash/analysis/auditsmeasured. Kernelhard200000unchanged,global180000stronger.',ledger='Start22548;reserve84000unused.Prechargeeveryattemptedenv.stepBEFOREfsyncedACTION_CHARGEDandcall,failed/partialchargesnotrefunded. action_callsincrementatdispatchboundaryafterdurablecharge;raw_attempts/nativewheelreservedbeforedurableinput, native_raw_callsatfunctiondispatch. World/resetreservationslikewisebeforecalls. Max588chargesremaining>=21960.',stop='Firstbaselineidentity/683/safetyfailure,candidatecertificate/no-safe-action/actualstrict/domain/IO/integrity/cost/deadlinefailureterminatesALL;no retry/newworld/otherpolicy. finallycloseandbody/joint0mandatory. Nativegainonlyofficialintegerrawbelowfreshbaseline683;no500msgate. Baselinereproductionnotnewperformancegain.',privacy='PrivilegedfullstateDEVdiagnosticonly,notpixelpolicy/Agent.act5s/otherinitialization. Samecloudnoadditionalpaidresources.Rawcase/seed/map/root/commands/transcript/journalprivateoutsideGit;technicalcode/hash/aggregatesonly.PreservemainParticipantsuserchangesbackups593..597costs/failures.Carry/combined/generalpromotionCLOSED.',research_start=22548,reserve=84000,reserve_used=0,runtime=dict(python=sys.version,platform=platform.platform(),numpy=np.__version__,Box2D=Box2D.__version__,opencv=cv2.__version__,pygame=pygame.version.ver,SDL_VIDEODRIVER=os.environ.get('SDL_VIDEODRIVER'),SDL_AUDIODRIVER=os.environ.get('SDL_AUDIODRIVER'),DISPLAY=os.environ.get('DISPLAY')))
  atomic_write(C,self.contract);atomic_write(D/'REGISTERED-private.json',dict(contract_sha256=d.sha(C),worlds=0))
 def pins(self):
  for k,h in self.contract['input_sha256'].items():assert d.sha(INPUTS[k])==h,('INPUT',k)
  for p,h in {**self.contract['implementation_sha256'],**self.contract['dependency_sha256']}.items():assert d.sha(Path(p) if Path(p).is_absolute() else G/p)==h,('CODE_RUNTIME',p)
 def prepare(self):
  self.guard();self.pins();self.case=d.rd(INPUTS['case']);self.static=d.rd(INPUTS['static']);fixed=d.rd(INPUTS['baseline_paths']);new=d.rd(INPUTS['candidate_paths']);self.paths=dict(baseline=fixed['candidate'],candidate=new['candidate']);self.backup=fixed['backup'];self.candidate_backup=new['backup'];self.track_nodes=len(self.static['track']);self.source_index=bounds(self.static['roads']);self.source_edges=boundary_index(self.static['boundary']);self.geometry_context=tracking.geometry_context(self.static,600000);tape=d.rd(INPUTS['tape']);self.commands={q['index']:np.asarray(q['action'],np.float32) for q in tape['commands'] if q['index']<=39};assert sorted(self.commands)==list(range(1,40))
  old541=d.rd(INPUTS['baseline_contract']);assert d.sha(INPUTS['case'])==old541['case_private_sha256'] and d.sha(INPUTS['baseline_paths'])==old541['fixed_path_sha256']
  for k in ['tape','static','ledger']:
   assert d.sha(INPUTS[k])==d.rd(INPUTS['source597_contract'])['input_sha256'][k]
  assert d.sha(INPUTS['candidate_paths'])==d.rd(INPUTS['source597_contract'])['input_sha256']['paths'];assert d.rd(INPUTS['source597_audit'])['status']=='READ_ONLY_AUDIT_PASS';assert d.rd(INPUTS['old597'])['whole_source_verified'] and d.rd(INPUTS['old597'])['whole']['official_candidate_raw']==661;assert not d.rd(INPUTS['carry_failure'])['combined_source_gate']
  assert all(d.sha(G/p)==h for p,h in old541['source_sha256'].items());assert self.case['wrapper']==dict(skip_frames=4,stack_frames=4,no_operation=50,max_off_track_steps=100) and self.case['TimeLimit_max_episode_steps']==1224
  assert subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31' and not subprocess.check_output(['git','diff','--name-only','main','--','Participants'],cwd=G,text=True).strip()
  self.result['preflight']=dict(exact_original_case_paths_pins=True,source597_verified661=True,source577_prefix39_exact_bytes=True,carry_combined_closed=True,all_worlds0_before_freeze=True,pure_tests=d.rd(G/'retry/cold598_tests.json')['tests']);atomic_write(D/'frozen-prefix-command-bytes-private.json',{str(h):a.tobytes().hex() for h,a in self.commands.items()});self.pins();self.guard()
 def kernel(self,key,fn,*a,**kw):
  self.capacity({key:1,'total_force':1});self.add(key);self.add('total_force');return fn(*a,**kw)
 def project(self,kind,*a):
  self.capacity(dict(geometry=1));self.add('geometry');self.add('geometry_'+kind);q=self.original_project(*a)
  if kind in ['tracking_forecast','launch_forecast'] and self.last_model_after is not None and tuple(a[0])==tuple(self.last_model_after.center):
   before=self.last_model_before;over=math.hypot(*self.last_model_after.planar.linear.velocity)-d.reference(q['s'],a[1])[0];self.diag=dict(root_sha256=self.hash(self.short(self.last_model_after)),path_error=q['distance'],projection_segment=q['i'],projection_delta=q['s']-a[2],projection_lower=-.5,projection_upper=max(5.,2*math.dist(before.center,self.last_model_after.center)),reference_excess=over)
  return q
 def source_geometry(self,root,*args):
  self.capacity(dict(geometry=1));self.add('geometry');self.add('geometry_source_footprint');gap=self.original_margin(root,self.static['roads'],self.source_index,self.static['boundary'],self.source_edges,self.static['obstacles']);t=self.active_trial
  if t is not None and t.minimum==float('inf'):
   t.minimum=gap
   if gap<.5:t.reason='CURRENT_FOOTPRINT_MARGIN';t.first_failure='CURRENT_FOOTPRINT'
  elif self.diag is not None and self.diag['root_sha256']==self.hash(self.short(root)):
   z=dict(self.diag,footprint=gap,mode=self.model_mode,label=self.label)
   if t is not None:
    flags,first=t.post(gap,z['reference_excess'],z['path_error'],z['projection_delta'],z['projection_upper']);z.update(minimum_footprint=t.minimum,max_reference_excess=t.maxover,history=t.history.copy(),flags=flags,first_failure=first)
   else:flags,first,_=post_flags(gap,0.,z['path_error'],z['projection_delta'],z['projection_upper']);z.update(flags=flags,first_failure=first,minimum_scope='current_raw_only_original_launch_summary_separate',reference_scope='phase_not_inferred_original_launch_report_controls_reference_gate')
   self.journal.append('SOURCE_GEOMETRY_DIAGNOSTIC',**z);self.diag=None
  return gap
 def model_force(self,root,action):
  self.capacity(dict(model_attempted=1,external_force=4,internal_force=4,total_force=8,model_completed=1));self.add('model_attempted');rid=self.hash(self.short(root));t=self.active_trial;self.journal.append('BEFORE_MODEL_FORCE',root_sha256=rid,root=self.short(root),action_bits=action.tobytes().hex(),label=self.label,mode=self.model_mode,history=t.history.copy() if t else None);forces=d.force_rows(root,action)
  if len(forces)!=4 or any(not math.isfinite(z['ratio']) or bool(z['clipped'])!=(z['ratio']>1.) for z in forces):raise IdentityStop('MODEL_FORCE_IDENTITY')
  reason=t.force(forces,tracking.ADMISSION) if t is not None else None;self.pending=dict(root_sha256=rid,gas=float(action[1]),brake=float(action[2]));self.journal.append('MODEL_FORCE_VERDICT',label=self.label,mode=self.model_mode,root_sha256=rid,ratios=[z['ratio'] for z in forces],prefix_history=t.history.copy() if t else None,pre_failure=reason);return forces
 def model_tick(self,root,gas,brake,index,counter):
  self.capacity(dict(model_completed=1,internal_force=4,total_force=4));p=self.pending
  if counter is not self.model or p is None or p['root_sha256']!=self.hash(self.short(root)) or [gas,brake]!=[p['gas'],p['brake']]:raise IdentityStop('MODEL_TICK_WITHOUT_FORCE')
  self.add('model_tick_attempts');self.journal.append('BEFORE_MODEL_TICK',root_sha256=p['root_sha256'],label=self.label,mode=self.model_mode);after=d.source_tick(root,gas,brake,index,counter);self.add('model_completed');self.pending=None;v=body(after);self.journal.append('AFTER_MODEL_TICK',root_sha256=self.hash(self.short(after)),root=self.short(after),body=v,label=self.label,mode=self.model_mode)
  if not math.isfinite(v) or v>=100:raise DomainStop('MODEL_BODY_GE100_OR_NONFINITE')
  self.last_model_before=root;self.last_model_after=after;self.diag=None
  if self.active_trial is not None:self.active_trial.ticks+=1
  return after
 def certifier_factory(self,*a,**kw):
  fn=self.original_certifier(*a,**kw);history=kw.get('history',a[8] if len(a)>8 else (0,0));progress=a[3]
  def wrapped(action):
   prior=self.active_trial;t=Trial(history,progress,float('inf'));self.active_trial=t;self.journal.append('TRACKING_TRIAL_START',label=self.label,mode=self.model_mode,history=history,progress=progress,root_sha256=self.hash(self.short(a[0])),action_bits=action.tobytes().hex())
   try:
    report=fn(action);summary=t.summary();keys=['ok','reason','peak','max_reference_overspeed','clipped','samples','model_ticks','min_footprint_margin_m'];assert all(report[k]==summary[k] for k in keys),'PASSIVE537_SUMMARY_MISMATCH';entry=dict(label=self.label,mode=self.model_mode,summary=summary,original=report,exact=True);self.trial_summaries.append(entry);self.journal.append('TRACKING_TRIAL_END',**entry);return report
   finally:self.active_trial=prior
  return wrapped
 def install_meters(self):
  self.original_project=d.project;self.original_margin=d.margin;self.original_certifier=tracking.certifier
  patches=[(tracking,'tick',self.model_tick),(tracking,'force_rows',self.model_force),(tracking,'margin',self.source_geometry),(tracking,'certifier',self.certifier_factory),(launch,'tick',self.model_tick),(launch,'force_rows',self.model_force),(launch,'margin',self.source_geometry),(preview,'tick',self.model_tick),(preview,'force_rows',self.model_force)]
  for module,name,kind in [(tracking,'project','tracking_forecast'),(launch,'project','launch_forecast'),(preview,'project','four_raw_prediction'),(lap,'project','internal_nominal_steering'),(d,'project','native_or_initial')]:patches.append((module,name,lambda *a,_kind=kind:self.project(_kind,*a)))
  for module,name,new in patches:self.originals[(module,name)]=getattr(module,name);setattr(module,name,new)
  oe=wheel.wheel_response;oi=planar.wheel_response;self.originals[(wheel,'wheel_response')]=oe;self.originals[(planar,'wheel_response')]=oi;wheel.wheel_response=lambda *a,**k:self.kernel('external_force',oe,*a,**k);planar.wheel_response=lambda *a,**k:self.kernel('internal_force',oi,*a,**k)
 def backup_command(self,*a):return preview.backup(*a)
 def transition_choose(self,root,path,low,progress,history):
  before=self.model_mode;self.model_mode='prefix_future40_anchor';self.add('transition_anchor_choosers')
  try:
   a,detail=tracking.choose(root,path,low,progress,self.model,self.planner,180000,history=history,geometry=self.geometry_context)
   if a is None or not detail.get('final_recertified') or not any(z['mode']=='FINAL' and z['ok'] for z in detail.get('reports',[])):return None,detail
   return a,detail
  finally:self.model_mode=before
 def candidate_select(self,root,path,st,i,raw,skin):
  h=i+1;groups={k:[v['clipped'],v['samples']] for k,v in st['force_groups'].items()};visited={t.idx for t in raw.road if t.road_visited}
  if len(visited)!=raw.tile_visited_count:raise IdentityStop('VISITED_SET_COUNT')
  if h<=39:
   action=self.commands[h].copy();detail=prefix_certificate(self,root,path,st['lap_progress'],h,self.commands,groups,raw.finish_line_tracker,visited,raw.t);self.add('prefix_certificates')
   if not detail['ok']:atomic_write(D/f'certificate-rejected-candidate-{h:03d}-private.json',dict(detail=detail,root=self.short(root),tracker=asdict(raw.finish_line_tracker),visited=sorted(visited),groups=groups,clock=raw.t));raise CertificateStop('CANDIDATE_PREFIX_'+detail['reason'])
   if action.tobytes()!=self.commands[h].tobytes():raise IdentityStop('PREFIX_TAPE_BYTES')
  else:
   self.add('actual_feedback_choosers');action,detail=tracking.choose(root,path,self.candidate_backup,st['lap_progress'],self.model,self.planner,180000,history=tuple(groups['running']),geometry=self.geometry_context)
   if action is None or not detail.get('final_recertified') or not any(z['mode']=='FINAL' and z['ok'] for z in detail.get('reports',[])):atomic_write(D/f'certificate-rejected-candidate-{h:03d}-private.json',dict(detail=detail,root=self.short(root),tracker=asdict(raw.finish_line_tracker),visited=sorted(visited),groups=groups,clock=raw.t));raise CertificateStop('CANDIDATE_FEEDBACK_NO_FRESH_FINAL')
  return action,detail
 def run(self):
  status='TECHNICAL_FAILURE';error=None;self.planner=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0,geometry_checks=0)
  signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(CostStop('TOTAL_CPU_TIMER')));signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(CostStop('TOTAL_WALL_TIMER')));signal.setitimer(signal.ITIMER_PROF,max(.01,3778-self.times()['total_CPU_s']));signal.setitimer(signal.ITIMER_REAL,max(.01,4438-self.times()['total_wall_s']))
  try:
   self.prepare();self.install_meters();self.pins();atomic_write(D/'NATIVE_STARTED-private.json',dict(contract_sha256=d.sha(C)));a=self.arm('baseline');status='BASELINE_'+a['stop']+'_CANDIDATE_NOT_STARTED'
   if a['stop']=='OFFICIAL_FINISH' and a['official_finish_raw']==683 and a['initial_identity'] and not a['error'] and not a['flags'] and a['cleanup']==dict(body=0,joint=0):
    b=self.arm('candidate');status='COLD_ONLY_NATIVE_POSITIVE_DIAGNOSTIC' if b['stop']=='OFFICIAL_FINISH' and b['official_finish_raw']<683 else 'COLD_ONLY_NATIVE_FINISHED_NOT_IMPROVED' if b['stop']=='OFFICIAL_FINISH' else 'CANDIDATE_'+b['stop']
  except BaseException as exc:error=type(exc).__name__+':'+str(exc);status='BUDGET_CENSORED' if isinstance(exc,CostStop) else 'TECHNICAL_FAILURE';atomic_write(D/'outer-failure-private.json',dict(error=error,traceback=traceback.format_exc(),counts=dict(self.counts)))
  finally:
   sys.settrace(None);self.restore();self.stage='audit';self.journal.close()
   try:audit=inspect(D/'journal-private.jsonl');self.pins();self.guard()
   except BaseException as exc:audit=dict(valid=False,error=str(exc));status='BUDGET_CENSORED' if isinstance(exc,CostStop) else 'TECHNICAL_FAILURE';error=(error or '')+';AUDIT:'+str(exc)
   gain=683-self.arms[1]['official_finish_raw'] if len(self.arms)==2 and self.arms[1]['stop']=='OFFICIAL_FINISH' else None;atomic_write(D/'tracking-trial-summaries-private.json',self.trial_summaries)
   self.result.update(study=598,status=status,error=error,arms=self.arms,cost=dict(self.counts),time=self.times(),journal=audit,planner_cost=self.planner,cold_native_gain_raw=gain,cold_native_gain_s=gain*.02 if gain is not None else None,research_start=22548,research_remaining=22548-self.counts['actions'],reserve=84000,reserve_used=0,combined_promotion=False,general_policy_promotion=False,incumbents_changed=False,carry_actions=0,new_conditions=0,HOLDOUT=0,SEALED=0,new_profiles=0,new_FD=0,new_solver=0,paid_compute=0,source_cold_s=13.22,prior_actual_cold_s=13.66,tracking_trial_summaries=len(self.trial_summaries),all_tracking_passive_summaries_exact=all(t['exact'] for t in self.trial_summaries),input_sha256=self.contract['input_sha256'],private_sha256={p.name:d.sha(p) for p in D.glob('*.json*')});atomic_write(G/'retry/cold598_result.json',self.result);signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);print(json.dumps(self.result,indent=2))
