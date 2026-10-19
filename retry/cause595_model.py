"""One <=48raw reproduction of594's rejected source forecast; native forbidden."""
import time
CPU=time.process_time();WALL=time.perf_counter()
import datetime,hashlib,importlib.util,json,math,signal,subprocess,sys,traceback,unittest
from collections import Counter
from dataclasses import asdict
from pathlib import Path
import numpy as np
import retry.handoff562_model as d
import retry.brake502_response as wheel
import retry.brake504_planar as planar
from retry.late568_model import body
from retry.durable568 import Journal,digest,inspect
from retry.clip561_core import atomic_write
from retry.cause595_prepare import INPUTS as ORIGINAL_INPUTS,short
from retry.split595_certificate import certify
from core.vendor.car_racing import CarRacing
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response595-private');C=G/'retry/cause595_contract.json'
INPUTS=dict(ORIGINAL_INPUTS,gate=G/'retry/cause595_checkpoint_gate.json',checkpoint=D/'checkpoint-private.json',expected=D/'expected-model-events-private.json',tests=G/'retry/cause595_tests.json')
class BudgetStop(RuntimeError):pass
class DomainStop(RuntimeError):pass

def physical_difference(a,b):
 p=a['planar'];q=b['planar'];w=p['linear']['wheels'];z=q['linear']['wheels'];return dict(COM_position_m=math.dist(a['center'],b['center']),COM_velocity_m_s=math.dist(p['linear']['velocity'],q['linear']['velocity']),angle_rad=math.remainder(p['angle']-q['angle'],2*math.pi),yaw_rad_s=p['yaw']-q['yaw'],maximum_joint_error_rad=max(abs(x-y) for x,y in zip(p['joints'],q['joints'])),maximum_rate_error_rad_s=max(abs(x-y) for x,y in zip(p['rates'],q['rates'])),maximum_wheel_omega_error=max(abs(x['omega']-y['omega']) for x,y in zip(w,z)),maximum_wheel_gas_error=max(abs(x['gas']-y['gas']) for x,y in zip(w,z)),maximum_wheel_heading_error_rad=max(abs(math.remainder(x['heading']-y['heading'],2*math.pi)) for x,y in zip(w,z)),maximum_lever_error_m=max(math.dist(x,y) for x,y in zip(p['levers'],q['levers'])),inertia_error=p['inertia']-q['inertia'],angular_momentum_error=p['angular_momentum']-q['angular_momentum'],mass_equal=p['linear']['mass']==q['linear']['mass'],engine_equal=p['linear']['engine_multiplier']==q['linear']['engine_multiplier'],frictions_equal=[x['friction'] for x in w]==[y['friction'] for y in z],contacts_equal=tuple(tuple(q) for q in a['current_contacts'])==tuple(tuple(q) for q in b['current_contacts']))

class Study:
 def __init__(self):
  if not D.exists():raise RuntimeError('CHECKPOINT_PREP_REQUIRED')
  self.counts=Counter(geometry=1,path_projection_preflight=1);self.stage='preparation';self.prior=10.;self.scCPU=self.scWall=0.;self.rows=[];self.event_index=0;self.model=[0];self.pending=None;self.result={};self.journal=None;self.register();self.journal=Journal(D/'journal-private.jsonl')
 short=staticmethod(short);hash=staticmethod(digest)
 def times(self):
  active=self.stage=='source';sc=self.scCPU+(time.process_time()-self.pc if active else 0);sw=self.scWall+(time.perf_counter()-self.pw if active else 0);tc=time.process_time()-CPU+self.prior;tw=time.perf_counter()-WALL+self.prior;return dict(source_CPU_s=sc,source_wall_s=sw,preparation_audit_CPU_s=tc-sc,preparation_audit_wall_s=tw-sw,total_CPU_s=tc,total_wall_s=tw)
 def guard(self):
  for k,v in dict(source_CPU_s=60,source_wall_s=90,preparation_audit_CPU_s=60,preparation_audit_wall_s=90,total_CPU_s=120,total_wall_s=180).items():
   if self.times()[k]>=v:raise BudgetStop(k)
  if self.stage!='audit' and (self.times()['preparation_audit_CPU_s']>=55 or self.times()['preparation_audit_wall_s']>=80):raise BudgetStop('AUDIT_RESERVE')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,20,10,1,55,tzinfo=datetime.timezone.utc):raise BudgetStop('DEADLINE')
 def count(self,k,n=1):self.counts[k]+=n
 def geom(self,kind,fn,*args):
  self.guard();tail=98 if self.stage=='source' else 0
  if self.counts['geometry']+1+tail>200:raise BudgetStop('GEOMETRY_COMPARISON_RESERVE')
  self.count('geometry');self.count(kind);return fn(*args)
 def project(self,*args):return self.geom('path_projection_source',d.project,*args)
 def source_geometry(self,r):return self.geom('footprint_geometry',d.margin,r,self.static['roads'],self.source_index,self.static['boundary'],self.source_edges,self.static['obstacles'])
 def expected_event(self,kind):
  q=self.expected[self.event_index]
  if q['kind']!=kind:raise RuntimeError('EXPECTED_EVENT_ORDER')
  self.event_index+=1;return q
 def model_force(self,root,action):
  self.guard()
  if self.counts['attempted_raw']>=48 or self.counts['external_force']+4>192 or self.counts['internal_force']+4>192:raise BudgetStop('RAW_FORCE_CAP')
  self.count('attempted_raw');key=digest(short(root));old=self.expected_event('BEFORE_MODEL_FORCE');assert key==old['root_sha256'] and action.tobytes().hex()==old['action_bits'],'594_BEFORE_FORCE_MISMATCH';self.journal.append('BEFORE_FORCE',root=short(root),action=action.tolist(),attempt=self.counts['attempted_raw']);forces=d.force_rows(root,action);old=self.expected_event('MODEL_FORCE_VERDICT');assert [q['ratio'] for q in forces]==old['ratios'],'594_FORCE_MISMATCH';self.pending=dict(key=key,gas=float(action[1]),brake=float(action[2]));self.journal.append('FORCE_VERDICT',forces=forces,exact594=True);return forces
 def model_tick(self,root,gas,brake,index,counter):
  self.guard();p=self.pending;old=self.expected_event('BEFORE_MODEL_TICK');key=digest(short(root));assert counter is self.model and p and p==dict(key=key,gas=gas,brake=brake) and key==old['root_sha256'],'PENDING_OR_594_TICK_MISMATCH';self.count('tick_attempts');self.journal.append('BEFORE_TICK',root=short(root));after=d.source_tick(root,gas,brake,index,counter);self.count('completed_ticks');self.pending=None;v=body(after);old=self.expected_event('AFTER_MODEL_TICK');self.journal.append('AFTER_TICK',root=short(after),body=v,old594_root_hash_matches=digest(short(after))==old['root_sha256']);assert digest(short(after))==old['root_sha256'] and v==old['body'],'594_AFTER_TICK_MISMATCH'
  if not math.isfinite(v):raise RuntimeError('NONFINITE_BODY')
  if v>=100:raise DomainStop('BODY_GE100')
  return after
 def kernel(self,key,fn,*args,**kw):
  self.guard()
  if self.counts[key]>=192:raise BudgetStop(key)
  self.count(key);return fn(*args,**kw)
 def record(self,row):self.rows.append(row);self.journal.append('ROW_DIAGNOSTIC',row=row)
 def register(self):
  local={str(Path(m.__file__).resolve().relative_to(G)):d.sha(Path(m.__file__).resolve()) for m in tuple(sys.modules.values()) if getattr(m,'__file__',None) and Path(m.__file__).is_file() and Path(m.__file__).resolve().is_relative_to(G) and '.venv' not in Path(m.__file__).parts};local.update({p:d.sha(G/p) for p in ['retry/cause595_model.py','retry/cause595_prepare.py','retry/split595_certificate.py','tests/test_cause595.py']});deps={str(Path(m.__file__).resolve()):d.sha(Path(m.__file__).resolve()) for m in tuple(sys.modules.values()) if getattr(m,'__file__',None) and Path(m.__file__).is_file() and ('.venv' in Path(m.__file__).parts or not Path(m.__file__).resolve().is_relative_to(G))};c=dict(study=595,status='FROZEN_BEFORE_PURE_TESTS_SOURCE',registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55Z',parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip(),input_sha256={k:d.sha(p) for k,p in INPUTS.items()},implementation_sha256=local,dependency_sha256=deps,caps=dict(attempted_raw=48,completed_ticks=48,external_force=192,internal_force=192,total_force=384,geometry=200,source_CPU_s=60,source_wall_s=90,preparation_audit_CPU_s=60,preparation_audit_wall_s=90,total_CPU_s=120,total_wall_s=180),spec='Exactly594storedcertificateinputraw156,currentroot/actualhistories/visited/tracker/clock anddirectstoredprogress;immutablepinnedroadsinput;no guessednativecheckpoint.No coldwhole/nativeprefixrerun.Onefixed577holds40..51<=48raw reproduction,firstsafetyfailurestops;all594beforeforce/actionbytes/forceratios/beforeaftertickrootSHA/bodymustexactmatchold192events;neverretryonmismatch.593certifierphysics/commands/phase/reference/geometrypredicatesunchanged,splitORpredicatesandperrawtelemetryonly. Readstored577raw156..firstfailure andsamepathprojections;alternateold577progresshintqueriesonstorednewrootsareREADONLYprojectionnotnewphysics. Existingfailures/incumbents/ledgerpreserved.',geometry_rule='ChargeALLqueries:preflightactualprogress1,footprintcurrent+post<=49,sourcepathprojections<=48,stored577projections<=49,alternate577hintprojections<=49;max196of200. Reserve98read-onlycomparisonqueriesduringphysics. Audit0newqueries. CPUprep10conservativechargeincludescheckpointrecovery;allimports/tests/register/reads/hash/auditmeasured;prep5CPU10wallreservedforaudit.',recovery='ExclusiveSTARTEDandfsyncedrawinputs/verdict/tick/telemetry;firstexception/strictfailure/capstop;no native/world/reset/action/FD/solver/feedback/profile.New48rawchargedseparatelyfrom594.No postfailurephysics or extra rerun.',research_remaining=22548,reserve=84000,reserve_used=0,privacy='Rawroots/commands/poses/tracker/visited/journalprivateoutsidegit;technicalcode/hash/aggregatesonly,designatedcloud;preservemainParticipantsold593/594andallfailures.')
  atomic_write(C,c);self.contract=c;atomic_write(D/'REGISTERED-private.json',dict(contract_sha256=d.sha(C)))
 def pins(self):
  for k,h in self.contract['input_sha256'].items():assert d.sha(INPUTS[k])==h,('INPUT',k)
  for p,h in {**self.contract['implementation_sha256'],**self.contract['dependency_sha256']}.items():assert d.sha(Path(p) if Path(p).is_absolute() else G/p)==h,('CODE',p)
 def prepare(self):
  self.guard();self.pins();gate=d.rd(INPUTS['gate']);assert gate['status']=='EXACT_STORED_CERTIFICATE_CHECKPOINT_AVAILABLE' and all(gate['checks'].values()) and gate['geometry_used']==1;tests=d.rd(INPUTS['tests']);assert tests['passed'] and tests['tests']==4 and all(d.sha(G/p)==h for p,h in tests['input_sha256'].items());self.result['pure_tests']=dict(count=4,passed=True,finite_boundary_cases=224,executed_before_registration=True)
  self.cp=d.rd(INPUTS['checkpoint']);self.static=d.rd(INPUTS['static']);self.path=d.rd(INPUTS['paths'])['candidate'];self.tape=d.rd(INPUTS['tape']);self.expected=d.rd(INPUTS['expected']);self.commands={q['index']:np.asarray(q['action'],np.float32) for q in self.tape['commands']};self.source_index=d.bounds(self.static['roads']);self.source_edges=d.boundary_index(self.static['boundary']);self.track_nodes=len(self.static['track']);self.root=d.load_root(dict(self.cp['root'],roads=self.static['root']['roads']));assert digest(short(self.root))==d.rd(INPUTS['rejection'])['detail']['actual_start_sha256'];assert d.sha(INPUTS['checkpoint'])==gate['checkpoint_sha256'] and d.sha(INPUTS['expected'])==gate['expected_events_sha256'];self.pins();self.guard()
 def compare(self):
  source=self.tape['rows'];end=self.rows[-1]['global_raw'];new=[dict(global_raw=156,root=self.cp['root'],progress=self.cp['progress'])]+[q for q in self.rows if q.get('tick_executed')];comparisons=[];all_saved_exact=True;all_alt_same=True;visited=set(d.rd(INPUTS['ledger'])['initial_visited']);source_visited156=None
  for old in source[:156]:
   for ids in old['root_without_roads']['current_contacts']:visited.update(ids)
  source_visited156=set(visited)
  for q in new:
   i=q['global_raw'];old=source[i-1];prior=source[i-2]['progress'];savedq=self.geom('stored577_projection_queries',d.project,old['root_without_roads']['center'],self.path,prior);all_saved_exact&=savedq['s']==old['progress'] and savedq['distance']==old['path_error'];hint=old['progress'] if i==156 else prior;alternate=self.geom('alternate_hint_projection_queries',d.project,q['root']['center'],self.path,hint);all_alt_same&=alternate['s']==q['progress'] and (i==156 or alternate['i']==q['projection_segment'])
   comparisons.append(dict(global_raw=i,physical=physical_difference(q['root'],old['root_without_roads']),new_path_error=(d.rd(INPUTS['candidate'])['raw_records'][-1]['path_error'] if i==156 else q['path_error']),stored577_path_error=old['path_error'],stored577_path_slack=3-old['path_error'],new_progress=q['progress'],stored577_progress=old['progress'],stored577_projection_delta=old['progress_delta'],stored577_projection_limit=old['projection_limit'],stored577_margin=old['margin'],same_projection_segment_as_stored577=alternate['i']==savedq['i'],alternate577_hint_same_progress=alternate['s']==q['progress'],alternate577_hint_distance=alternate['distance'],stored577_projection_recomputed_exact=savedq['s']==old['progress'] and savedq['distance']==old['path_error']))
  assert all_saved_exact,'SAVED_SOURCE_PROJECTION_MISMATCH';atomic_write(D/'source-comparison-private.json',comparisons);initial=comparisons[0];final=comparisons[-1];self.result['comparison']=dict(initial=initial,final=final,compared_rows=len(comparisons),stored577_projection_recomputed_exact=all_saved_exact,alternate_old577_progress_hint_same_projection_all_rows=all_alt_same,physical_COM_position_error_growth=final['physical']['COM_position_m']/initial['physical']['COM_position_m'] if initial['physical']['COM_position_m'] else None,initial_tracking_history_actual=self.cp['groups']['running'],initial_tracking_history_stored577=source[155]['proposed_history'],initial_launch_history_actual=self.cp['groups']['launch'],initial_launch_history_stored577=source[155]['launch_history_before'],initial_visited_set_same=source_visited156==set(self.cp['visited']),initial_tracker_exact_to_actual594=digest(self.cp['tracker'])==d.rd(INPUTS['rejection'])['detail']['actual_tracker_sha256'],initial_tracker_same_as_stored577=self.cp['tracker']==source[155]['tracker'],initial_clock_difference_vs_stored577_s=self.cp['clock']-(1.02+source[155]['episode_after_s']),metadata_dataflow='Fixedcommands andsource_tick do not readtracker/clock/visited/cliphistory;projectionreadspreviousprogress. Alternatehintquerieschangeonlyreadonlyprojectiononidenticalstoredroots;no counterfactualphysics.')
 def run(self):
  status='TECHNICAL_FAILURE';error=None;oe=wheel.wheel_response;oi=planar.wheel_response
  def forbidden(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN_595')
  CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden;signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(BudgetStop('TOTAL_CPU')));signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(BudgetStop('TOTAL_WALL')));signal.setitimer(signal.ITIMER_PROF,max(.01,118-self.times()['total_CPU_s']));signal.setitimer(signal.ITIMER_REAL,max(.01,178-self.times()['total_wall_s']))
  try:
   self.prepare();atomic_write(D/'SOURCE_STARTED-private.json',dict(contract_sha256=d.sha(C)));wheel.wheel_response=lambda *a,**k:self.kernel('external_force',oe,*a,**k);planar.wheel_response=lambda *a,**k:self.kernel('internal_force',oi,*a,**k);self.stage='source';self.pc=time.process_time();self.pw=time.perf_counter()
   try:summary=certify(self,self.root,self.path,self.cp['progress'],40,self.commands,self.cp['groups'],d.FinishLineTracker(**self.cp['tracker']),set(self.cp['visited']),self.cp['clock'])
   finally:self.scCPU+=time.process_time()-self.pc;self.scWall+=time.perf_counter()-self.pw;self.stage='analysis'
   self.result['original_summary']=summary;assert summary==d.rd(INPUTS['rejection'])['detail'],'594_SUMMARY_NOT_EXACT';assert self.event_index==192,'594_EVENT_PREFIX_INCOMPLETE';self.result['all_594_model_events_exact']=True;last=self.rows[-1];self.result['first_failure']=dict(global_raw=last['global_raw'],hold=last['hold'],raw=last['raw'],branch=last['first_failure'],geometry_flags=last['geometry_flags'],path_error=last['path_error'],path_slack=3-last['path_error'],projection_delta=last['projection_delta'],projection_lower=last['projection_lower'],projection_upper=last['projection_upper'],footprint=last['footprint'],minimum_footprint=last['minimum_footprint'],force_peak=last['force_peak'],prefix_force_peak=last['prefix_peak'],clip_fraction=last['clip_fraction'],reference_excess=last['reference_excess'],tracker_updated=last['tracker_updated']);self.compare();status='EXACT594_FIRST_FAILURE_IDENTIFIED'
  except BaseException as exc:error=type(exc).__name__+':'+str(exc);status='BUDGET_CENSORED' if isinstance(exc,BudgetStop) else 'SOURCE_DOMAIN_STOP' if isinstance(exc,DomainStop) else 'TECHNICAL_FAILURE';atomic_write(D/'failure-private.json',dict(error=error,traceback=traceback.format_exc(),cost=dict(self.counts)))
  finally:
   wheel.wheel_response=oe;planar.wheel_response=oi;self.stage='audit';atomic_write(D/'diagnostic-rows-private.json',self.rows);self.journal.close()
   try:audit=inspect(D/'journal-private.jsonl');self.pins();self.guard()
   except BaseException as exc:audit=dict(valid=False,error=str(exc));status='TECHNICAL_FAILURE';error=(error or '')+';AUDIT:'+str(exc)
   self.result.update(study=595,status=status,error=error,cost=dict(self.counts),time=self.times(),journal=audit,native_actions=0,native_worlds=0,native_resets=0,new_fullcold_source=0,new_FD=0,new_profile=0,new_solver=0,HOLDOUT=0,SEALED=0,paid_compute=0,research_remaining=22548,reserve=84000,reserve_used=0,original593594_unchanged=True,combined_promotion=False,native_promotion=False);atomic_write(G/'retry/cause595_result.json',self.result);signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);print(json.dumps(self.result,indent=2))
if __name__=='__main__':Study().run()
