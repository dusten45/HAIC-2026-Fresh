"""439 static gate and whole saved-data audit; every native/model ctor blocked."""
import datetime,io,json,signal,sys,time,unittest
from pathlib import Path
from unittest.mock import patch
from retry.loss389_analyze import read,save,sha
G=Path(__file__).resolve().parents[1]
class StaticStop439(BaseException):pass

def prepare(root):
 d=root/'stage439';assert not(d/'plan.json').exists();old=read(root/'stage438/plan.json');v=read(root/'project-effective-budget-v458.json');assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(28207,84000,0);assert read(root/'stage438/result.json')['status']=='ACTUAL_PAIR_CENSORED_STOP' and read(root/'stage438/cost.json')['new_wrapper_actions']==119
 for f,h in {**old['sources'],**old['protected'],**old['original408_preserve']}.items():assert sha(f)==h,f
 preserve={str(f):sha(f) for n in range(420,439) for f in (root/('stage'+str(n))).rglob('*') if f.is_file()};save(d/'prior-preservation-manifest.json',preserve);files=set(Path(f) for f in old['sources']);files.update((G/'retry').glob('*439.py'));files.update([d/'prior-preservation-manifest.json',root/'project-effective-budget-v458.json',root/'stage438/cost.json',root/'stage438/publication.json',root/'stage438/C0_decision1-before-actual-dispatch-private.json',root/'stage438/actual_C0/trace-private.jsonl',root/'stage437/actual_C0/final-private.json',root/'stage417/source-prefix-private.json'])
 for stage,name in [(423,'C0'),(427,'P')]:files.add(root/('stage'+str(stage))/('actual_'+name)/'trace-private.jsonl')
 files.update(f for f in (root/'stage438').glob('qualification*-private.json') if f.is_file());deadline=read(root/'research-deadline-current.json')['deadline_utc'];assert deadline=='2026-10-20T10:01:55Z'
 p=dict(stage=439,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=deadline,authorization='Explicit439staticcontractimplementationonly; noactual/modelintegration/actor/learning/SEALED/reserve/paid. Preserve438failureandcost. Noactualrunnerorfollowup.',caps=dict(CPU_s=180,wall_s=300,new_model_ticks=0,new_actual_actions=0,new_worlds=0,new_resets=0),research_remaining=28207,reserve=84000,reserve_used=0,fixed_plan=old['fixed_plan'],position_tolerance_m=read(root/'stage418/plan.json')['fidelity']['body_position_m'],geometry='Sameuniqueinteriorbranch:originalprojectionexpressionevaluatedoverexisting0.1mpositionboxwithoutwardIEEE754elementaryoperations; exactcopiedpositionorconstantcanonicalvertexgetsconstantarc. Differentsegments/interior-vertex/ambiguousprojection/unwrapcut=>unsupportedconservativestop. Noobserved6.979e-6epsilonfit. Preserveoriginal(old+mod)-halfexpressionassociation.',ledger='ObservedcandidatefrompreviousACTUALGoalLedger+ownnativepre/postprojection+rawclock+officialtrackeronly. Exactnativeprogressself-consistency; forecastowngeometry/selfconsistencycheckedseparately. Exactclock/age/deadline/DONE/goalhit; oppositegoalboundarystopsdespitecontinuousinterval. Progress/goalwithinprojection-derivedinterval/goalanchor. Modelneverreplacesactual.',current_inputs='Exactclonedcurrentprepose/COMvelocity/yaw/timeandmemorybefore/afternominal are inputcopy/prephysicsidentity, not futurephysicsbitwiseequality. Fullstoredreplaymemorydriftnotwaivedorfalselycalledcurrent-first. Existingbody/wheel/rawhull/safety/discrete/clip/COMcriteriaunchanged. Nativeauthoritydefaultcannotdispatch; futureexplicitrunnerrequired.',audit='All189actual423C0and177actual427Pphysical/geometry/ledgerrows; prefixmodelmemory/ledgernotrecorded=>reconstructeddiagnosticonly, no inventedproof. Full71/59savedmodelreplaysdistinctfromcurrent-firstqualification. 12stored427currentrestorestateseach2repeats+438first; all437/438adapter/ledgerconditionsandnegativecontrols. Inspectallrowsafterfirststopforreportingbutdonotqualifytail.',stop='Anyunprovenbranch/currentinput/discreteboundary/unsafe/deadline/NaN/tamper=>explicitstaticfailure/notqualified. Staticimplementationbugs mayberepairedbeforegatepasswithoriginalattempt/sourcespreserved. No integrations underanyoutcome. Noautomaticactualresumption.',sources={str(f):sha(f) for f in sorted(files)},protected=old['protected'],original408_preserve=old['original408_preserve'])
 assert p['position_tolerance_m']==.1;save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'preparation-result.json',dict(wall_s=time.time()-read(d/'preparation-opening.json')['epoch'],CPU_s=None,fully_measured=False));print(json.dumps(dict(stage=439,plan_sha256=sha(d/'plan.json'),research_remaining=28207,new_integrations_cap=0)))

def run(root):
 d=root/'stage439';p=read(d/'plan.json');assert not(d/'result.json').exists() and sha(d/'plan.json')==(d/'plan.sha256').read_text().strip();cpu=time.process_time();wall=time.perf_counter();stream=io.StringIO();result=None;audit=None;failure=None
 for group in [p['sources'],p['protected'],p['original408_preserve']]:
  for f,h in group.items():assert sha(f)==h,f
 def timeout(*args):raise StaticStop439('staticCPU180_wall300')
 old={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};signal.setitimer(signal.ITIMER_PROF,max(.001,179-time.process_time()));signal.setitimer(signal.ITIMER_REAL,299)
 try:
  from retry import test_early429,test_planner419,test_planner419_model_ledger,test_pilot436,test_audit431,test_boundary434,test_boundary434_more,test_observer435,test_parent436,test_actual437,test_canonical438,test_ledger439,diagnose
  from retry.source_vehicle_transition import SourceVehicleTransition
  from retry.terminal410_model import TerminalVehicleTransition
  import Box2D
  from retry.audit439 import run as audit_run
  classes=[test_early429.EarlyProtocol,test_planner419.PlannerLogic,test_planner419_model_ledger.PredictedLedgerTests,test_pilot436.Scope436,test_audit431.ExactReasons,test_boundary434.BoundaryTests,test_boundary434_more.More434,test_observer435.ObserverControls,test_parent436.ParentControls,test_actual437.ActualControls437,test_canonical438.Canonical438,test_ledger439.Ledger439];suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in classes)
  with patch.object(SourceVehicleTransition,'__init__',side_effect=AssertionError('FORBIDDEN_WORLD')) as a,patch.object(TerminalVehicleTransition,'__init__',side_effect=AssertionError('FORBIDDEN_TERMINAL')) as b,patch.object(diagnose,'make_env',side_effect=AssertionError('FORBIDDEN_NATIVE_ENV')) as c,patch.object(Box2D,'b2World',side_effect=AssertionError('FORBIDDEN_B2WORLD')) as e:
   result=unittest.TextTestRunner(stream=stream,verbosity=2,failfast=True).run(suite)
   if result.wasSuccessful():audit=audit_run(root,d)
   if a.call_count or b.call_count or c.call_count or e.call_count:raise AssertionError('FORBIDDEN_CONSTRUCTOR_ATTEMPT')
 except BaseException as e:failure=type(e).__name__+': '+str(e)
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in old.items():signal.signal(s,h)
  (d/'tests.log').write_text(stream.getvalue())
 q=dict(stage=439,passed=bool(result and result.wasSuccessful() and audit is not None and failure is None),error=failure,tests=0 if result is None else result.testsRun,failures=0 if result is None else len(result.failures),errors=0 if result is None else len(result.errors),audit_completed=audit is not None,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,new_actual_model_reset_actor_learning_SEALED_reserve_paid=0,plan_sha256=sha(d/'plan.json'));save(d/'result.json',q);print(json.dumps(q));print('Staticcontractandsavedauditcomplete; nointegration.' if q['passed'] else stream.getvalue()[-3500:])
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
