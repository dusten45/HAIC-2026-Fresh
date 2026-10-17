"""440 static authority integration and saved data tests; no real constructors."""
import io,json,signal,sys,time,unittest
from pathlib import Path
from unittest.mock import patch
from retry.loss389_analyze import read,save,sha
class StaticStop439(BaseException):pass
def run(root):
 d=root/'stage440';p=read(d/'plan.json');assert not(d/'static-result.json').exists() and sha(d/'plan.json')==(d/'plan.sha256').read_text().strip();cpu=time.process_time();wall=time.perf_counter();stream=io.StringIO();result=None;audit=None;failure=None
 for group in [p['sources'],p['protected'],p['original408_preserve']]:
  for f,h in group.items():assert sha(f)==h,f
 def timeout(*args):raise StaticStop439('staticCPU180_wall300')
 old={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};signal.setitimer(signal.ITIMER_PROF,max(.001,179-time.process_time()));signal.setitimer(signal.ITIMER_REAL,299)
 try:
  from retry import test_early429,test_planner419,test_planner419_model_ledger,test_pilot436,test_audit431,test_boundary434,test_boundary434_more,test_observer435,test_parent436,test_actual437,test_canonical438,test_ledger439,test_native440,diagnose
  from retry.source_vehicle_transition import SourceVehicleTransition
  from retry.terminal410_model import TerminalVehicleTransition
  import Box2D
  from retry.audit439 import run as audit_run
  classes=[test_early429.EarlyProtocol,test_planner419.PlannerLogic,test_planner419_model_ledger.PredictedLedgerTests,test_pilot436.Scope436,test_audit431.ExactReasons,test_boundary434.BoundaryTests,test_boundary434_more.More434,test_observer435.ObserverControls,test_parent436.ParentControls,test_actual437.ActualControls437,test_canonical438.Canonical438,test_ledger439.Ledger439,test_native440.Native440Tests];suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in classes)
  with patch.object(SourceVehicleTransition,'__init__',side_effect=AssertionError('FORBIDDEN_WORLD')) as a,patch.object(TerminalVehicleTransition,'__init__',side_effect=AssertionError('FORBIDDEN_TERMINAL')) as b,patch.object(diagnose,'make_env',side_effect=AssertionError('FORBIDDEN_NATIVE_ENV')) as c,patch.object(Box2D,'b2World',side_effect=AssertionError('FORBIDDEN_B2WORLD')) as e:
   result=unittest.TextTestRunner(stream=stream,verbosity=2,failfast=True).run(suite)
   if result.wasSuccessful():audit=audit_run(root,d)
   if a.call_count or b.call_count or c.call_count or e.call_count:raise AssertionError('FORBIDDEN_CONSTRUCTOR_ATTEMPT')
 except BaseException as e:failure=type(e).__name__+': '+str(e)
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in old.items():signal.signal(s,h)
  (d/'static-tests.log').write_text(stream.getvalue())
 q=dict(stage=440,passed=bool(result and result.wasSuccessful() and audit is not None and failure is None),error=failure,tests=0 if result is None else result.testsRun,failures=0 if result is None else len(result.failures),errors=0 if result is None else len(result.errors),audit_completed=audit is not None,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,new_actual_model_reset_actor_learning_SEALED_reserve_paid=0,plan_sha256=sha(d/'plan.json'));save(d/'static-result.json',q);print(json.dumps(q));print('Staticcontractandsavedauditcomplete; nointegration.' if q['passed'] else stream.getvalue()[-3500:])

if __name__=='__main__':run(Path(sys.argv[1]))
