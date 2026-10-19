"""One fresh541 cold baseline then one fixed577 cold-only native diagnostic."""
import time
CPU=time.process_time();WALL=time.perf_counter()
import copy,datetime,hashlib,importlib.util,json,math,os,platform,signal,subprocess,sys,traceback,unittest
from collections import Counter
from dataclasses import asdict
from pathlib import Path
import numpy as np
import Box2D,cv2,pygame
from Box2D.b2 import polygonRadius
from gymnasium.wrappers import TimeLimit
from core.vendor.car_racing import CarRacing,TRACK_WIDTH
from core.vendor.car_dynamics import Car
from env_wrapper import CarEnvironment
from damage import calculate_damage_effects
import retry.structure537_control as tracking
import retry.launch540_control as launch
import retry.preview527_control as preview
import retry.handoff562_model as d
import retry.brake502_response as wheel
import retry.brake504_planar as planar
from retry.brake503_diagnostic import com,observed_state
from retry.brake509_adapter import context
from retry.brake508_corridor import bounds,indexed_contacts
from retry.brake510_common import native_roads,track_boundary,boundary_index,clearance
from retry.corner515_model import obstacle_margin
from retry.late568_model import body
from retry.durable568 import Journal,digest,inspect
from retry.clip561_core import atomic_write,plain
from retry.cold593_certificate import certify,finish_raw
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response593-private');C=G/'retry/cold593_contract.json'
INPUTS=dict(tape=Path('/workspace/haic-response577-private/final-independent-tape-private.json'),case=Path('/workspace/haic-response541-private/approved-case-private.json'),baseline_paths=Path('/workspace/haic-response541-private/frozen-paths-private.json'),candidate_paths=Path('/workspace/haic-response551-private/frozen-paths-private.json'),static=Path('/workspace/haic-response515-private/collected-map-state-private.json'),ledger=Path('/workspace/haic-response519-private/model-ledger-private.json'),cold_contract=G/'retry/direct577_contract.json',cold_result=G/'retry/direct577_result.json',cold_audit=G/'retry/direct577_analysis.json',cold_registration=Path('/workspace/haic-response577-private/STARTED.json'),cold_journal=Path('/workspace/haic-response577-private/raw-journal-private.jsonl'),baseline_result=G/'retry/joint541_native_result.json',baseline_contract=G/'retry/joint541_contract.json',carry_failure=G/'retry/carry592_result.json',proposal=G/'retry/validation591_proposed_contract.json')
LIMITS=dict(baseline=dict(model_attempted=90000,model_completed=90000,external_force=410000,internal_force=360000,geometry=100000,actions=500,raw_attempts=1225,native_wheel_reserved=4900,CPU_s=2400,wall_s=2600),candidate=dict(model_attempted=10000,model_completed=10000,external_force=40000,internal_force=40000,geometry=10000,actions=166,raw_attempts=1225,native_wheel_reserved=4900,CPU_s=600,wall_s=700))
CAPS=dict(model_attempted=100000,model_completed=100000,external_force=450000,internal_force=400000,geometry=110000,actions=666,raw_attempts=2450,native_wheel_reserved=9800,worlds=2,resets=2)
class CostStop(RuntimeError):pass
class SafetyStop(RuntimeError):pass
class DomainStop(RuntimeError):pass
class IdentityStop(RuntimeError):pass
class CertificateStop(RuntimeError):pass

class Study:
 def __init__(self):
  D.mkdir(mode=0o700,exist_ok=False);self.counts=Counter();self.arm_counts=Counter();self.model=[0];self.arms=[];self.stage='preparation';self.label=None;self.pending=None;self.journal=None;self.scienceCPU=self.scienceWall=0.;self.prior=10.;self.result={};self.native_live=None;self.env_live=None;self.originals={};self.current=None;self.start_science=False;self.register();self.journal=Journal(D/'journal-private.jsonl')
 @staticmethod
 def short(r):return dict(planar=asdict(r.planar),center=r.center,current_contacts=r.current_contacts,floor=r.floor,skin=r.skin)
 @staticmethod
 def hash(x):return digest(x)
 def times(self):
  active=self.stage=='science';sc=self.scienceCPU+(time.process_time()-self.scCPU if active else 0);sw=self.scienceWall+(time.perf_counter()-self.scWall if active else 0);tc=time.process_time()-CPU+self.prior;tw=time.perf_counter()-WALL+self.prior
  return dict(science_CPU_s=sc,science_wall_s=sw,preparation_audit_CPU_s=tc-sc,preparation_audit_wall_s=tw-sw,total_CPU_s=tc,total_wall_s=tw)
 def guard(self,*a):
  t=self.times()
  for k,v in dict(science_CPU_s=3000,science_wall_s=3300,preparation_audit_CPU_s=120,preparation_audit_wall_s=180,total_CPU_s=3120,total_wall_s=3480).items():
   if t[k]>=v:raise CostStop(k)
  if self.stage!='audit' and (t['preparation_audit_CPU_s']>=105 or t['preparation_audit_wall_s']>=155):raise CostStop('AUDIT_15CPU25WALL_RESERVE')
  if self.stage=='science' and (time.process_time()-self.armCPU>=LIMITS[self.label]['CPU_s'] or time.perf_counter()-self.armWall>=LIMITS[self.label]['wall_s']):raise CostStop('ARM_TIME_CAP')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,20,10,1,55,tzinfo=datetime.timezone.utc):raise CostStop('DEADLINE')
 def add(self,k,n=1):
  self.counts[k]+=n
  if self.stage=='science':self.arm_counts[k]+=n
 def capacity(self,requests):
  self.guard()
  for k,n in requests.items():
   if k in CAPS and self.counts[k]+n>CAPS[k]:raise CostStop('AGGREGATE_'+k)
   if self.stage=='science' and k in LIMITS[self.label] and self.arm_counts[k]+n>LIMITS[self.label][k]:raise CostStop('ARM_'+k)
 def reserve_hold(self):
  if self.label=='baseline':req=dict(model_attempted=1540,model_completed=1540,external_force=6176,internal_force=6160,geometry=1572,actions=1,raw_attempts=4,native_wheel_reserved=16);cpu=45;wall=60
  else:req=dict(model_attempted=52,model_completed=52,external_force=224,internal_force=208,geometry=53,actions=1,raw_attempts=4,native_wheel_reserved=16);cpu=10;wall=15
  self.capacity(req)
  if time.process_time()-self.armCPU+cpu>LIMITS[self.label]['CPU_s'] or time.perf_counter()-self.armWall+wall>LIMITS[self.label]['wall_s']:raise CostStop('HOLD_CERT_EXECUTION_TIME_RESERVE')
  self.journal.append('HOLD_RESERVE',label=self.label,next_hold=self.arm_counts['actions']+1,requests=req,CPU_s=cpu,wall_s=wall,counts=dict(self.counts))
 def register(self):
  local={str(Path(m.__file__).resolve().relative_to(G)):d.sha(Path(m.__file__).resolve()) for m in tuple(sys.modules.values()) if getattr(m,'__file__',None) and Path(m.__file__).is_file() and Path(m.__file__).resolve().is_relative_to(G) and '.venv' not in Path(m.__file__).parts};local.update({p:d.sha(G/p) for p in ['retry/cold593_native.py','retry/cold593_certificate.py','tests/test_cold593.py']});deps={str(Path(m.__file__).resolve()):d.sha(Path(m.__file__).resolve()) for m in tuple(sys.modules.values()) if getattr(m,'__file__',None) and Path(m.__file__).is_file() and ('.venv' in Path(m.__file__).parts or not Path(m.__file__).resolve().is_relative_to(G))}
  for package in [Box2D,cv2,pygame]:
   for p in [*Path(package.__file__).parent.glob('*.so'),*Path(package.__file__).parent.glob('*.ttf')]:deps[str(p.resolve())]=d.sha(p)
  c=dict(study=593,status='FROZEN_BEFORE_TESTS_SOURCE_OR_NATIVE',registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55Z',parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip(),input_sha256={k:d.sha(p) for k,p in INPUTS.items()},implementation_sha256=local,dependency_sha256=deps,runtime=dict(python=sys.version,platform=platform.platform(),numpy=np.__version__,Box2D=Box2D.__version__,opencv=cv2.__version__,pygame=pygame.version.ver,SDL_VIDEODRIVER=os.environ.get('SDL_VIDEODRIVER'),SDL_AUDIODRIVER=os.environ.get('SDL_AUDIODRIVER'),DISPLAY=os.environ.get('DISPLAY')),caps=dict(CAPS,total_model_force=850000,actual_native_wheel=9800,science_CPU_s=3000,science_wall_s=3300,preparation_audit_CPU_s=120,preparation_audit_wall_s=180,total_CPU_s=3120,total_wall_s=3480),arm_caps=LIMITS,spec='Cold-onlynativefullstateknownDEVdiagnostic.Baselineunchanged541paths+540launchfirst24+537trackingandFINAL.Oncefreshsafeofficial683raw/13.66anddrive683thenonly577fixedfloat32tape1..166once. No500msgate.Positivegainonlyintegerofficialrawlessbaseline.No feedback/reindex/fallback/167. Actualstate/history/visitedset/tracker/clock clonedbeforeeachcandidateaction;freshfuture12holdfixedcommands sourcecertificate,globalphase1..24launch2.5/clip15%onlyend24/no referenceveto;25+tracking1.059/clip10%/reference4.85;allfootprint.50/path3/body<100/projection. Certificatehaltsatclonedofficialconfirmationorfinitehorizon/tapeend;no postfinishadmissionveto. SeparateconstantCURRENTaction4rawprediction computedto4rawonlyfordynamicscomparisonincludingpredictedpostfinish;no additionalforce/geometryadmissionafterpredictedfinish,bodydomainstillrequired. Liveactualfinishaloneendswrapper. Actualnativephysicaltracking1.25/ref5/margin.25/clip10%,launch2.5/15%,body<100,collision/damage0,oracle.05N/COM.01,position.10/speed.15/angle.02/yaw.05/forceratioerror.19;payload/friction/sensor/effects/observationidentity. Rawreset51 notincludedcliphistories. Existingkernelhard200kunchanged;attempt100kstronger. Carry592failureandcombinedclosedunchanged;noincumbentpromotion.',reservation='Baselineworldallocated90kmodel/410kexternal/360kinternal/100kgeometry/2400CPU2600wall;candidate10k/40k/40k/10k/600CPU700wallreservedbeforebaseline.Eachworld1225rawincl51reset,actions500/166.Eachholdworstcertificate+4raw+oracle+nativekernelreserved;baseline1540model/6176external/6160internal/1572geometry/45CPU60wall,candidate52/224/208/53/10CPU15wall.15CPU25wallfinalauditreservedfromseparateprepauditpool.10CPU/wallpriorprepcharge;imports/tests/register/pins/auditsmeasured. No phasebeginswithoutfullremainingwallcap+cleanupbeforedeadline.',ledger='Start22758;reserve84000unused.Prechargeeveryattemptedenv.stepbeforecall/fsync,fail/partial/terminalneverrefunded,max666=>22092. World/reset/rawattemptseparatebeforecall.ExclusiveSTARTED,no retries/newworldafteranyerror;onlyprior-toSTARTED/world/reset/action/rawall0import-onlyerrorcouldbeseparatelyreviewed.Failuresimmutable;finallycloseandbodyjoint0.',privacy='Rawcase/seed/map/state/commands/observations/RNG/forcevectors/journalprivatedesignatedcloudoutsidegit.Publictechnicalcode/hash/aggregatesonly.PreservemainParticipantsuserchangesbackupsfailures.No carry/newcondition/HOLDOUT/SEALED/profile/FD/solver/paidcompute.',research_start=22758,reserve=84000,reserve_used=0)
  atomic_write(C,c);self.contract=c;atomic_write(D/'REGISTERED-private.json',dict(contract_sha256=d.sha(C)))
 def pins(self):
  for k,h in self.contract['input_sha256'].items():assert d.sha(INPUTS[k])==h,('INPUT',k)
  for p,h in {**self.contract['implementation_sha256'],**self.contract['dependency_sha256']}.items():assert d.sha(Path(p) if Path(p).is_absolute() else G/p)==h,('CODE_RUNTIME',p)
 def prepare(self):
  self.guard();self.pins();spec=importlib.util.spec_from_file_location('test_cold593',G/'tests/test_cold593.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);r=unittest.TestResult();unittest.defaultTestLoader.loadTestsFromModule(m).run(r);self.result['pure_tests']=dict(count=r.testsRun,passed=r.wasSuccessful());assert r.wasSuccessful(),(r.errors,r.failures)
  self.case=d.rd(INPUTS['case']);self.static=d.rd(INPUTS['static']);fixed=d.rd(INPUTS['baseline_paths']);new=d.rd(INPUTS['candidate_paths']);self.paths=dict(baseline=fixed['candidate'],candidate=new['candidate']);self.backup=fixed['backup'];self.track_nodes=len(self.static['track']);self.source_index=bounds(self.static['roads']);self.source_edges=boundary_index(self.static['boundary']);self.geometry_context=tracking.geometry_context(self.static,110000);tape=d.rd(INPUTS['tape']);cold=d.rd(INPUTS['cold_result']);coldc=d.rd(INPUTS['cold_contract']);old541=d.rd(INPUTS['baseline_contract']);chain=inspect(INPUTS['cold_journal']);assert chain==cold['journal'];assert d.sha(INPUTS['cold_contract'])==d.rd(INPUTS['cold_registration'])['contract_sha256'];assert all(d.sha(G/p)==h for p,h in coldc['source_sha256'].items()) and all(d.sha(Path(p))==h for p,h in coldc['input_sha256'].items());assert d.sha(INPUTS['case'])==old541['case_private_sha256'];assert d.sha(INPUTS['baseline_paths'])==old541['fixed_path_sha256'];assert d.sha(INPUTS['tape'])=='bc432812cdd71702ec030edda72a9aa63ca79e61dceb1f970891a659f20cd5a6';assert len(tape['rows'])==661 and len(tape['commands'])==166 and tape['exact'] and tape['checkpoint_exact'] and d.rd(INPUTS['cold_audit'])['passed'];assert set(tape['checkpoint'])=={'root_without_roads','visited','tracker','elapsed','global_raw','progress','launch','tracking'};assert all(not q['pre_failure'] and not q['post_failure'] and not q['all_failures'] for q in tape['rows']);assert all(d.sha(G/p)==h for p,h in old541['source_sha256'].items());assert not d.rd(INPUTS['carry_failure'])['combined_source_gate'];self.commands={q['index']:np.asarray(q['action'],np.float32) for q in tape['commands']};assert sorted(self.commands)==list(range(1,167));assert all(a.tolist()==q['action'] for a,q in zip(self.commands.values(),tape['commands']));assert self.case['wrapper']==dict(skip_frames=4,stack_frames=4,no_operation=50,max_off_track_steps=100) and self.case['TimeLimit_max_episode_steps']==1224
  self.result['preflight']=dict(cold_661raw_166commands_exact=True,cold_journal_chain_exact=True,cold_input_source_pins=True,baseline_case_paths_pins=True,carry_combined_closed=True,cold_source_ticks=0);atomic_write(D/'frozen-candidate-command-bytes-private.json',{str(h):a.tobytes().hex() for h,a in self.commands.items()});self.pins();self.guard()
 def model_force(self,root,action):
  self.capacity(dict(model_attempted=1,external_force=4,internal_force=4,model_completed=1));self.add('model_attempted');rid=digest(self.short(root));self.journal.append('BEFORE_MODEL_FORCE',root_sha256=rid,action_bits=action.tobytes().hex(),label=self.label);forces=d.force_rows(root,action)
  if len(forces)!=4 or any(not math.isfinite(z['ratio']) or bool(z['clipped'])!=(z['ratio']>1.) for z in forces):raise RuntimeError('MODEL_FORCE_IDENTITY')
  self.pending=dict(root_sha256=rid,gas=float(action[1]),brake=float(action[2]));self.journal.append('MODEL_FORCE_VERDICT',label=self.label,root_sha256=rid,ratios=[z['ratio'] for z in forces]);return forces
 def model_tick(self,root,gas,brake,index,counter):
  self.capacity(dict(model_completed=1,internal_force=4));p=self.pending
  if counter is not self.model or p is None or p['root_sha256']!=digest(self.short(root)) or [gas,brake]!=[p['gas'],p['brake']]:raise RuntimeError('MODEL_TICK_WITHOUT_FORCE_INPUT')
  self.add('model_tick_attempts');self.journal.append('BEFORE_MODEL_TICK',root_sha256=p['root_sha256'],label=self.label);after=d.source_tick(root,gas,brake,index,counter);self.add('model_completed');self.pending=None;v=body(after);self.journal.append('AFTER_MODEL_TICK',root_sha256=digest(self.short(after)),body=v,label=self.label)
  if not math.isfinite(v):raise RuntimeError('NONFINITE_MODEL_BODY')
  if v>=100:raise DomainStop('MODEL_BODY_GE100')
  return after
 def kernel(self,key,fn,*a,**kw):
  self.capacity({key:1});self.add(key);return fn(*a,**kw)
 def source_geometry(self,root,*args):
  self.capacity(dict(geometry=1));self.add('geometry');return d.margin(root,self.static['roads'],self.source_index,self.static['boundary'],self.source_edges,self.static['obstacles'])
 def install_meters(self):
  for module,name,new in [(tracking,'tick',self.model_tick),(tracking,'force_rows',self.model_force),(tracking,'margin',self.source_geometry),(launch,'tick',self.model_tick),(launch,'force_rows',self.model_force),(launch,'margin',self.source_geometry),(preview,'tick',self.model_tick),(preview,'force_rows',self.model_force)]:self.originals[(module,name)]=getattr(module,name);setattr(module,name,new)
  self.originals[(wheel,'wheel_response')]=wheel.wheel_response;self.originals[(planar,'wheel_response')]=planar.wheel_response;oe=wheel.wheel_response;oi=planar.wheel_response;wheel.wheel_response=lambda *a,**k:self.kernel('external_force',oe,*a,**k);planar.wheel_response=lambda *a,**k:self.kernel('internal_force',oi,*a,**k)
 def restore(self):
  for (module,name),fn in self.originals.items():setattr(module,name,fn)
 def world_reserve(self,label):
  self.guard();limits=LIMITS[label];self.capacity(dict(worlds=1,resets=1,raw_attempts=1225,native_wheel_reserved=4900,actions=limits['actions'],model_attempted=limits['model_attempted'],model_completed=limits['model_completed'],external_force=limits['external_force'],internal_force=limits['internal_force'],geometry=limits['geometry']))
  t=self.times();cpu=limits['CPU_s'];wall=limits['wall_s']
  if label=='baseline':cpu+=600;wall+=700
  if t['science_CPU_s']+cpu>3000 or t['science_wall_s']+wall>3300:raise CostStop('WHOLE_WORLD_TIME_RESERVE')
  remaining=(datetime.datetime(2026,10,20,10,1,55,tzinfo=datetime.timezone.utc)-datetime.datetime.now(datetime.timezone.utc)).total_seconds()
  if remaining<wall+25:raise CostStop('DEADLINE_WORLD_RESERVE')
  self.journal.append('WORLD_RESERVE',label=label,limits=limits,candidate_reserved=label=='baseline')
 def arm(self,label):
  self.label=label;self.arm_counts=Counter();self.armCPU=time.process_time();self.armWall=time.perf_counter();self.world_reserve(label);self.stage='science';self.scCPU=time.process_time();self.scWall=time.perf_counter();self.add('worlds');self.journal.append('WORLD_CHARGED',label=label,counts=dict(self.counts));raw=env=None;st=None;rows=[];stop='MAX_ACTIONS';error=None;initial_ok=False;official=None;pred_errors=[]
  try:
   raw=CarRacing(**self.case['base']);self.native_live=raw;env=CarEnvironment(TimeLimit(raw,max_episode_steps=self.case['TimeLimit_max_episode_steps']),**self.case['wrapper']);self.env_live=env;original_step=raw.step;original_reset=raw.reset;path=self.paths[label];skin=2*float(polygonRadius)
   st=dict(mode_counts={},lap_progress=None,reference_arc=None,unused_startup_over=0.,force_groups={g:dict(peak=0.,samples=0,clipped=0) for g in ('launch','running')},phase='reset',resets=0,reset_ticks=0,actions=0,action_ticks=0,active=None,pred=None,flags=[],mesh=None,ticks=[],epoch=None,minimum=float('inf'),max_path_error=0.,max_ref_over=0.,force_oracle_max=0.,impulse_max=0.,max_body=0.)
   def ids(car):return tuple(tuple(sorted(t.idx for t in w.tiles)) for w in car.wheels)
   lines=(G/'core/vendor/car_dynamics.py').read_text().splitlines();rawline=next(i+1 for i,s in enumerate(lines) if 'if abs(force) > 2.0 * friction_limit' in s);finalline=next(i+1 for i,s in enumerate(lines) if 'w.omega -= dt * f_force' in s)
   def reset(**kwargs):
    self.capacity(dict(resets=1))
    if st['resets']:raise IdentityStop('UNEXPECTED_SECOND_RESET')
    st['resets']+=1;self.add('resets');self.journal.append('RESET_CHARGED',label=label,counts=dict(self.counts));return original_reset(**kwargs)
   def step(action):
    self.guard()
    if st['phase']=='reset' and st['reset_ticks']>=51:raise IdentityStop('RESET_RAW51_CAP')
    if st['mesh'] is None:st['mesh']=native_roads(raw.road);st['index']=bounds(st['mesh']);st['base']=[p for p,mu in st['mesh']];st['edge']=track_boundary(raw.track,TRACK_WIDTH);st['edgeindex']=boundary_index(st['edge'])
    before=observed_state(raw.car);position=com(raw.car,True);clock=raw.t;used=ids(raw.car);effects=(raw.car.grip_multiplier,raw.car.engine_multiplier,raw.car.steering_multiplier);sensor=tuple(indexed_contacts([tuple(w.GetWorldPoint(v)) for v in w.fixtures[0].shape.vertices],st['mesh'],st['index'],skin) for w in raw.car.wheels);oracle=[];actual={};beforeplanar=None
    if st['phase']=='action':
     self.capacity(dict(external_force=4));before_root=context(raw.car,raw.road,st['active'],skin=skin);beforeplanar=asdict(before_root.planar);self.journal.append('BEFORE_NATIVE_ORACLE',root=self.short(before_root),action=st['active'].tolist(),label=label);oracle=d.force_rows(before_root,st['active']);self.add('native_oracle_groups')
    def trace(frame,event,arg):
     if frame.f_code is Car.step.__code__:
      if event=='line' and frame.f_lineno in (rawline,finalline):
       x=frame.f_locals;j=raw.car.wheels.index(x['w']);item=actual.setdefault(j,dict(wheel=j))
       if frame.f_lineno==rawline:self.add('native_wheel_observed');item.update(ratio=float(x['force']/x['friction_limit']),friction=float(x['friction_limit']))
       else:item['vector']=[float(x['f_force']*x['forw'][k]+x['p_force']*x['side'][k]) for k in range(2)]
      return trace
     return None
    self.capacity(dict(raw_attempts=1,native_wheel_reserved=4,geometry=1));self.add('raw_attempts');self.add('native_wheel_reserved',4);self.journal.append('BEFORE_NATIVE_RAW',label=label,phase=st['phase'],action=st['actions'],clock=clock,counts=dict(self.counts),before_state=plain(before),before_position=position,payload=None if action is None else action.tolist(),tracker=asdict(raw.finish_line_tracker),visited=sorted(t.idx for t in raw.road if t.road_visited));sys.settrace(trace)
    try:q=original_step(action)
    finally:sys.settrace(None)
    self.add('raw_completed');st['reset_ticks' if st['phase']=='reset' else 'action_ticks']+=1;errors=[]
    if len(actual)!=4 or any('vector' not in x or 'ratio' not in x for x in actual.values()):raise RuntimeError('SOURCE_FORCE_CAPTURE')
    if sensor!=ids(raw.car):errors.append('SOURCE_SENSOR_PHASE')
    if effects!=(raw.car.grip_multiplier,raw.car.engine_multiplier,raw.car.steering_multiplier):errors.append('WITHIN_RAW_EFFECT')
    if st['active'] is not None and (action is None or not np.array_equal(action,st['active'].astype(np.float64))):errors.append('PAYLOAD')
    position_after=com(raw.car,True);velocity=com(raw.car);speed=math.hypot(*velocity);forecast_error=None
    if st['pred'] is not None:
     k=st['action_ticks']-1
     if k>=4:errors.append('HOLD_TICKS')
     else:
      pred=st['pred'][k];forecast_error=dict(position_m=math.dist(pred['position'],position_after),speed_m_s=speed-math.hypot(*pred['velocity']),angle_rad=math.remainder(raw.car.hull.angle-pred['angle'],2*math.pi),yaw_rad_s=raw.car.hull.angularVelocity-pred['yaw'])
      if forecast_error['position_m']>.10 or abs(forecast_error['speed_m_s'])>.15 or abs(forecast_error['angle_rad'])>.02 or abs(forecast_error['yaw_rad_s'])>.05:errors.append('PHYSICAL_PREDICTION')
      mu=lambda t:max([400*raw.car.grass_friction_multiplier*effects[0],*[400*st['mesh'][j][1]*effects[0] for j in t]])
      if any(mu(a)!=mu(b) for a,b in zip(pred['contacts_used'],used)):errors.append('PREDICTED_FRICTION')
    source_error=impulse_error=None
    if oracle:
     source_error=max(math.dist(oracle[i]['vector'],actual[i]['vector']) for i in range(4));st['force_oracle_max']=max(st['force_oracle_max'],source_error);expected=tuple(before.velocity[j]+.02*sum(actual[i]['vector'][j] for i in range(4))/before.mass for j in range(2));impulse_error=math.dist(expected,velocity);st['impulse_max']=max(st['impulse_max'],impulse_error)
     if st['pred'] is not None:
      force_prediction_error=max(abs(actual[i]['ratio']-st['pred'][st['action_ticks']-1]['force_ratios'][i]) for i in range(4));forecast_error['max_force_ratio_error']=force_prediction_error
      if force_prediction_error>.19:errors.append('WHEEL_FORCE_PREDICTION')
     if source_error>.05:errors.append('SOURCE_FORCE_ORACLE')
     if impulse_error>.01:errors.append('SOURCE_COM_IMPULSE')
    maxbody=max(math.hypot(*b.linearVelocity) for b in [raw.car.hull,*raw.car.wheels]);st['max_body']=max(st['max_body'],maxbody)
    if not math.isfinite(maxbody) or maxbody>=100:errors.append('BOX2D_TRANSLATION_MODEL_DOMAIN')
    self.capacity(dict(geometry=1));self.add('geometry');roadgap=clearance(raw.car,st['base'],st['index'],st['edge'],st['edgeindex']);polys=[[tuple(b.GetWorldPoint(v)) for v in f.shape.vertices] for b in [raw.car.hull,*raw.car.wheels] for f in b.fixtures];gap=min(roadgap,obstacle_margin(polys,self.static['obstacles']));st['minimum']=min(st['minimum'],gap)
    if gap<.25:errors.append('ROAD_OR_OBSTACLE_MARGIN')
    if q[4].get('collision',False):errors.append('COLLISION')
    q0=d.project(position,path,st['lap_progress'] if st['phase']=='action' else None);qp=d.project(position_after,path,q0['s']);st['lap_progress']=qp['s'];refspeed,_=d.reference(qp['s'],path)
    if st['phase']=='action':
     st['max_path_error']=max(st['max_path_error'],qp['distance']);delta=qp['s']-q0['s']
     if delta<-.5 or delta>max(5.,2*math.dist(position_after,position)):errors.append('PROJECTION_VALIDITY')
     if qp['distance']>3:errors.append('PATH_ERROR')
     group='launch' if st['actions']<=24 else 'running';z=st['force_groups'][group];z['peak']=max(z['peak'],max(x['ratio'] for x in actual.values()));z['samples']+=4;z['clipped']+=sum(x['ratio']>1 for x in actual.values())
     if group=='launch':
      st['unused_startup_over']=max(st['unused_startup_over'],speed-refspeed)
      if z['peak']>2.5 or (st['actions']==24 and st['action_ticks']==4 and z['clipped']/z['samples']>.15):errors.append('LAUNCH_FORCE_GUARD')
     else:
      st['max_ref_over']=max(st['max_ref_over'],speed-refspeed)
      if speed-refspeed>5 or z['peak']>1.25 or z['clipped']/z['samples']>.10:errors.append('DYNAMICS_GUARD')
     if st['reference_arc'] is None and q0['s']<path['length']<=qp['s']:
      f=(path['length']-q0['s'])/(qp['s']-q0['s']);st['reference_arc']=dict(lower=clock-st['epoch'],upper=raw.t-st['epoch'],time=clock-st['epoch']+.02*f)
     if qp['s']>path['length']+10 and raw.finish_time_s is None:errors.append('NO_OFFICIAL_FINISH_AFTER_ARC')
    record=dict(label=label,body_speed_max=maxbody,phase=st['phase'],action=st['actions'],time=raw.t,before=asdict(before),before_planar=beforeplanar,before_position=position,position=position_after,velocity=velocity,speed=speed,angle=raw.car.hull.angle,yaw=raw.car.hull.angularVelocity,station=qp['s'],path_error=qp['distance'],reference_speed=refspeed,margin=gap,used_contacts=used,after_contacts=ids(raw.car),effects=effects,forces=list(actual.values()),force_oracle_vector_error_N=source_error,COM_impulse_error_m_s=impulse_error,forecast_error=forecast_error,official_tracker=asdict(raw.finish_line_tracker),official_finished=raw.finish_time_s is not None,visited_tiles=raw.tile_visited_count,errors=errors);self.journal.append('AFTER_NATIVE_RAW',record=record,counts=dict(self.counts));st['ticks'].append(record);st['flags'].extend(errors)
    if errors:raise SafetyStop(','.join(errors))
    return q
   raw.reset=reset;raw.step=step;obs,_=env.reset(seed=self.case['seed'],options={'track_id':self.case['track_id']})
   if st['reset_ticks']!=51:raise IdentityStop('RESET51_IDENTITY')
   ready=lambda x:plain(x);oldhash=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,default=ready).encode()).hexdigest();obstacles=[[list(o.position),o.radius] for o in raw.track_variables.obstacles]
   if oldhash(raw.track)!=self.case['old_episode']['geometry_sha256_diagnostic_only'] or oldhash(obstacles)!=self.case['old_episode']['obstacles_sha256_diagnostic_only'] or obstacles!=self.static['obstacles']:raise IdentityStop('GEOMETRY_OBSTACLES_IDENTITY')
   root=context(raw.car,raw.road,[0,0,0],skin=skin);full=oldhash(dict(root=asdict(root),RNG=raw.np_random.bit_generator.state,observation=hashlib.sha256(obs.tobytes()).hexdigest()))
   if full!=self.static['full_identity']:raise IdentityStop('INITIAL_FULL_IDENTITY')
   initial_ok=True;st['epoch']=raw.t;st['phase']='action';st['lap_progress']=d.project(com(raw.car,True),path)['s']
   for i in range(LIMITS[label]['actions']):
    self.current=dict(label=label,next_hold=i+1);self.reserve_hold();root=context(raw.car,raw.road,[0,0,0],skin=skin);before_actual=self.hash(dict(root=self.short(root),tracker=asdict(raw.finish_line_tracker),visited=sorted(t.idx for t in raw.road if t.road_visited),clock=raw.t,groups=st['force_groups'],actuators=[(w.steer,w.gas,w.brake,w.omega) for w in raw.car.wheels],RNG=raw.np_random.bit_generator.state,damage=env.damage.damage,offtrack=env.off_track_counter,stack_sha256=hashlib.sha256(env.stack_state.tobytes()).hexdigest()))
    if label=='baseline':
     if i<24:
      z=st['force_groups']['launch'];action,detail=launch.choose_launch(root,path,self.backup,st['lap_progress'],i,(z['clipped'],z['samples']),self.model,self.planner,90000,self.geometry_context,guard=self.guard)
     else:
      z=st['force_groups']['running'];action,detail=tracking.choose(root,path,self.backup,st['lap_progress'],self.model,self.planner,90000,history=(z['clipped'],z['samples']),geometry=self.geometry_context)
     if action is None or not detail.get('final_recertified') or not any(q['mode']=='FINAL' and q['ok'] for q in detail.get('reports',[])):
      atomic_write(D/f'certificate-rejected-{label}-{i+1:03d}-private.json',dict(detail=detail,root=self.short(root)));raise CertificateStop('BASELINE_NO_FRESH_FINAL')
    else:
     action=self.commands[i+1].copy();groups={k:[v['clipped'],v['samples']] for k,v in st['force_groups'].items()};visited={t.idx for t in raw.road if t.road_visited}
     if len(visited)!=raw.tile_visited_count:raise IdentityStop('VISITED_SET_COUNT')
     detail=certify(self,root,path,st['lap_progress'],i+1,self.commands,groups,raw.finish_line_tracker,visited,raw.t);self.add('fixed_tape_certificates')
     if not detail['ok']:
      atomic_write(D/f'certificate-rejected-{label}-{i+1:03d}-private.json',dict(detail=detail,root=self.short(root),tracker=asdict(raw.finish_line_tracker),visited=sorted(visited),groups=groups,clock=raw.t));raise CertificateStop('CANDIDATE_'+detail['reason'])
     if action.tobytes()!=self.commands[i+1].tobytes():raise IdentityStop('TAPE_BYTES')
    if self.hash(dict(root=self.short(context(raw.car,raw.road,[0,0,0],skin=skin)),tracker=asdict(raw.finish_line_tracker),visited=sorted(t.idx for t in raw.road if t.road_visited),clock=raw.t,groups=st['force_groups'],actuators=[(w.steer,w.gas,w.brake,w.omega) for w in raw.car.wheels],RNG=raw.np_random.bit_generator.state,damage=env.damage.damage,offtrack=env.off_track_counter,stack_sha256=hashlib.sha256(env.stack_state.tobytes()).hexdigest()))!=before_actual:raise IdentityStop('FORECAST_MUTATED_ACTUAL')
    if action.dtype!=np.float32 or not np.isfinite(action).all() or not(-1<=action[0]<=1 and 0<=action[1]<=1 and 0<=action[2]<=1) or action[1]*action[2]!=0:raise IdentityStop('PAYLOAD_DOMAIN')
    _,predrows=preview.forecast(root,action,path,st['lap_progress'],bounds(root.roads),self.model);st['active']=action.copy();st['pred']=predrows;st['action_ticks']=0;begin=len(st['ticks']);self.capacity(dict(actions=1));self.add('actions');st['actions']+=1;st['mode_counts'][detail['mode']]=st['mode_counts'].get(detail['mode'],0)+1
    self.journal.append('ACTION_CHARGED',label=label,index=i+1,payload=action.tolist(),payload_bits=action.tobytes().hex(),counts=dict(self.counts),research_remaining=22758-self.counts['actions'],certificate=detail,prediction=predrows,before_root=self.short(root),tracker=asdict(raw.finish_line_tracker),clock=raw.t,visited=sorted(t.idx for t in raw.road if t.road_visited));obs,reward,terminated,truncated,info=env.step(action)
    if not(obs.shape==(4,84,84) and obs.dtype==np.float32 and np.isfinite(obs).all() and 0<=obs.min()<=obs.max()<=1):st['flags'].append('OBSERVATION')
    e=calculate_damage_effects(env.damage.damage)
    if (raw.car.grip_multiplier,raw.car.engine_multiplier,raw.car.steering_multiplier)!=(e.grip_multiplier,e.engine_multiplier,e.steering_multiplier):st['flags'].append('WRAPPER_EFFECT')
    if env.damage.damage>0:st['flags'].append('DAMAGE')
    record=dict(index=i+1,mode=detail['mode'],obs_sha256=hashlib.sha256(obs.tobytes()).hexdigest(),raw_ticks=st['action_ticks'],flags=list(st['flags']));rows.append(record);self.journal.append('ACTION_COMPLETED',label=label,record=record,counts=dict(self.counts));atomic_write(D/'latest-progress-private.json',dict(label=label,actions=st['actions'],drive_raw=self.arm_counts['raw_completed']-51,progress=st['lap_progress'],counts=dict(self.counts),time=self.times()),True)
    if st['flags']:raise SafetyStop(','.join(st['flags']))
    if raw.finish_time_s is not None and info.get('finished',False):stop='OFFICIAL_FINISH';break
    if terminated or truncated:stop='ENV_TERMINAL_WITHOUT_FINISH';break
   else:stop='TAPE_EXHAUSTED' if label=='candidate' else 'ACTION_CAP'
   if stop=='OFFICIAL_FINISH':official=finish_raw(raw.finish_time_s,st['epoch'])
   if label=='baseline' and (stop!='OFFICIAL_FINISH' or official!=683 or self.arm_counts['raw_completed']-51!=683):raise IdentityStop('BASELINE_NOT_SAFE_EXACT683RAW')
  except BaseException as exc:
   error=type(exc).__name__+':'+str(exc);stop='COST_CENSORED' if isinstance(exc,CostStop) else 'ACTUAL_SAFETY_FAILURE' if isinstance(exc,SafetyStop) else 'MODEL_DOMAIN_STOP' if isinstance(exc,DomainStop) else 'CERTIFICATE_REJECTED' if isinstance(exc,CertificateStop) else 'IDENTITY_FAILURE' if isinstance(exc,IdentityStop) else 'TECHNICAL_FAILURE';atomic_write(D/f'failure-{label}-private.json',dict(error=error,current=self.current,traceback=traceback.format_exc(),counts=dict(self.counts),arm_counts=dict(self.arm_counts),tracker=asdict(raw.finish_line_tracker) if raw is not None and raw.finish_line_tracker else None))
  finally:
   sys.settrace(None);cleanup=None
   if raw is not None:
    try:
     (env or raw).close();cleanup=dict(body=raw.world.bodyCount,joint=raw.world.jointCount)
     if cleanup['body']!=0 or cleanup['joint']!=0:raise RuntimeError('BODY_JOINT_LEAK')
     self.add('closed')
    except BaseException as exc:stop='TECHNICAL_FAILURE';error=(error or '')+';CLEANUP:'+str(exc);cleanup=dict(error=str(exc))
   self.native_live=self.env_live=None;self.scienceCPU+=time.process_time()-self.scCPU;self.scienceWall+=time.perf_counter()-self.scWall;self.stage='audit';item=dict(label=label,stop=stop,error=error,initial_identity=initial_ok,official_finish_raw=official,official_finish_episode_s=(raw.finish_time_s-st['epoch'] if raw is not None and raw.finish_time_s is not None and st and st['epoch'] is not None else None),confirmation_episode_s=(raw.t-st['epoch'] if st and st['epoch'] is not None else None),counts=dict(self.arm_counts),cleanup=cleanup,mode_counts=st['mode_counts'] if st else {},force_groups=st['force_groups'] if st else {},minimum_margin_m=st['minimum'] if st and math.isfinite(st['minimum']) else None,maximum_body_speed_m_s=st['max_body'] if st else None,maximum_path_error_m=st['max_path_error'] if st else None,maximum_reference_excess_m_s=st['max_ref_over'] if st else None,force_oracle_max_N=st['force_oracle_max'] if st else None,COM_impulse_max_m_s=st['impulse_max'] if st else None,reference_arc_diagnostic=st['reference_arc'] if st else None,flags=st['flags'] if st else [],CPU_s=time.process_time()-self.armCPU,wall_s=time.perf_counter()-self.armWall)
   if st:
    relevant=[q['forecast_error'] for q in st['ticks'] if q['forecast_error'] is not None];item['max_prediction_errors']={k:max((abs(q[k]) for q in relevant if k in q),default=0.) for k in ['position_m','speed_m_s','angle_rad','yaw_rad_s','max_force_ratio_error']}
   atomic_write(D/f'arm-{label}-private.json',dict(summary=item,rows=rows,raw_records=st['ticks'] if st else []));self.arms.append(item);self.journal.append('WORLD_CLOSED',summary=item,counts=dict(self.counts));self.guard()
  return item
 def run(self):
  status='TECHNICAL_FAILURE';error=None;self.planner=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0,geometry_checks=0)
  signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(CostStop('TOTAL_CPU_TIMER')));signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(CostStop('TOTAL_WALL_TIMER')));signal.setitimer(signal.ITIMER_PROF,max(.01,3118-self.times()['total_CPU_s']));signal.setitimer(signal.ITIMER_REAL,max(.01,3478-self.times()['total_wall_s']))
  try:
   self.prepare();self.install_meters();self.pins();atomic_write(D/'NATIVE_STARTED-private.json',dict(contract_sha256=d.sha(C)));a=self.arm('baseline');status='BASELINE_'+a['stop']+'_CANDIDATE_NOT_STARTED'
   if a['stop']=='OFFICIAL_FINISH' and a['official_finish_raw']==683 and not a['error']:
    b=self.arm('candidate');status='COLD_ONLY_NATIVE_POSITIVE_DIAGNOSTIC' if b['stop']=='OFFICIAL_FINISH' and b['official_finish_raw']<683 else 'COLD_ONLY_NATIVE_FINISHED_NOT_IMPROVED' if b['stop']=='OFFICIAL_FINISH' else 'CANDIDATE_'+b['stop']
  except BaseException as exc:error=type(exc).__name__+':'+str(exc);status='BUDGET_CENSORED' if isinstance(exc,CostStop) else 'TECHNICAL_FAILURE';atomic_write(D/'outer-failure-private.json',dict(error=error,traceback=traceback.format_exc(),counts=dict(self.counts)))
  finally:
   sys.settrace(None);self.restore();self.stage='audit';self.journal.close()
   try:audit=inspect(D/'journal-private.jsonl');self.pins();self.guard()
   except BaseException as exc:audit=dict(valid=False,error=str(exc));status='BUDGET_CENSORED' if isinstance(exc,CostStop) else 'TECHNICAL_FAILURE';error=(error or '')+';AUDIT:'+str(exc)
   gain=683-self.arms[1]['official_finish_raw'] if len(self.arms)==2 and self.arms[1]['stop']=='OFFICIAL_FINISH' else None;self.result.update(study=593,status=status,error=error,arms=self.arms,cost=dict(self.counts),time=self.times(),journal=audit,planner_cost=self.planner,cold_native_gain_raw=gain,cold_native_gain_s=gain*.02 if gain is not None else None,research_remaining=22758-self.counts['actions'],reserve=84000,reserve_used=0,combined_promotion=False,general_policy_promotion=False,incumbents_changed=False,carry_actions=0,new_conditions=0,HOLDOUT=0,SEALED=0,new_profiles=0,new_FD=0,new_solver=0,paid_compute=0,source_cold_s=13.20,prior_actual_cold_s=13.66);atomic_write(G/'retry/cold593_result.json',self.result);signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);print(json.dumps(self.result,indent=2))
if __name__=='__main__':Study().run()
