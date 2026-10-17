"""431 exact-set static controls; constructor calls are forbidden and counted."""
import io,json,signal,sys,time,unittest
from pathlib import Path
from unittest.mock import patch
from retry.loss389_analyze import read,save,sha
class StaticStop(BaseException):pass

def run(root):
 d=root/'stage434';p=read(d/'revision2-plan.json');assert not(d/'revision2-result.json').exists();cpu=time.process_time();wall=time.perf_counter();stream=io.StringIO();result=None;error=None
 for group in [p['sources'],p['protected'],p['original408_preserve']]:
  for f,h in group.items():assert sha(f)==h,f
 def timeout(*a):raise StaticStop('staticCPU60_wall120')
 old={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};signal.setitimer(signal.ITIMER_PROF,max(.001,59-time.process_time()));signal.setitimer(signal.ITIMER_REAL,119)
 try:
  from retry import test_early429,test_planner419,test_planner419_model_ledger,test_pilot433,test_audit431,test_boundary434,test_boundary434_more,diagnose
  from retry.source_vehicle_transition import SourceVehicleTransition
  from retry.terminal410_model import TerminalVehicleTransition
  suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in [test_early429.EarlyProtocol,test_planner419.PlannerLogic,test_planner419_model_ledger.PredictedLedgerTests,test_pilot433.Scope433,test_audit431.ExactReasons,test_boundary434.BoundaryTests,test_boundary434_more.More434])
  with patch.object(SourceVehicleTransition,'__init__',side_effect=AssertionError('FORBIDDEN_WORLD')) as a,patch.object(TerminalVehicleTransition,'__init__',side_effect=AssertionError('FORBIDDEN_TERMINAL')) as b,patch.object(diagnose,'make_env',side_effect=AssertionError('FORBIDDEN_NATIVE')) as c:
   result=unittest.TextTestRunner(stream=stream,verbosity=2,failfast=True).run(suite)
   if a.call_count or b.call_count or c.call_count:raise AssertionError('FORBIDDEN_CONSTRUCTOR_ATTEMPT')
 except BaseException as e:error=type(e).__name__+': '+str(e)
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in old.items():signal.signal(s,h)
  (d/'revision2-tests.log').write_text(stream.getvalue())
 q=dict(stage=434,passed=bool(result and result.wasSuccessful() and error is None),error=error,tests=0 if result is None else result.testsRun,failures=0 if result is None else len(result.failures),errors=0 if result is None else len(result.errors),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,new_model_ticks=0,new_actual_actions=0,plan_sha256=sha(d/'revision2-plan.json'));save(d/'revision2-result.json',q);print(json.dumps(q));print(stream.getvalue()[-3000:] if not q['passed'] else 'Frozen static controls passed. No worlds/actual.')
if __name__=='__main__':run(Path(sys.argv[1]))
