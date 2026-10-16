"""Supplemental static channel test under419 shared CPU/wall caps, unchanged selector."""
import datetime,importlib,io,json,os,signal,sys,time,unittest
from pathlib import Path
from retry.loss389_analyze import read,save,sha
G=Path(__file__).resolve().parents[1]
def prepare(root):
 d=root/'stage419';assert not(d/'ledger-plan.json').exists();p=read(d/'plan.json');files=[Path(__file__),G/'retry/planner419.py',G/'retry/planner419_model_ledger.py',G/'retry/test_planner419_model_ledger.py',d/'plan.json',d/'result.json'];q=dict(stage=419,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='AddseparateMODELpredictionledgerhelper, notchangefrozenquery/score/tail/actual-ledger/selector. Syntheticchanneltests, nointegratorimports orresources.',CPU_remaining_s=60-read(d/'result.json')['CPU_s'],wall_remaining_s=120-read(d/'result.json')['wall_s'],sources={str(f):sha(f) for f in files},protected=p['protected'],original408_preserve=p['original408_preserve']);save(d/'ledger-plan.json',q);(d/'ledger-plan.sha256').write_text(sha(d/'ledger-plan.json')+'\n');print('419 separate model-ledger frozen')
def run(root):
 d=root/'stage419';p=read(d/'ledger-plan.json');assert not(d/'ledger-opening.json').exists()
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h
 cpu=time.process_time();wall=time.perf_counter();save(d/'ledger-opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));stream=io.StringIO()
 def timeout(*a):raise TimeoutError('419shared_static_cap')
 old={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};signal.setitimer(signal.ITIMER_PROF,p['CPU_remaining_s']);signal.setitimer(signal.ITIMER_REAL,p['wall_remaining_s'])
 try:
  module=importlib.import_module('retry.test_planner419_model_ledger');result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module));status='SEPARATE_MODEL_LEDGER_TESTS_PASSED' if result.wasSuccessful() else 'MODEL_LEDGER_TEST_FAILURE'
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in old.items():signal.signal(s,h)
 (d/'ledger-tests.log').write_text(stream.getvalue());q=dict(stage=419,status=status,tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,new_native_reset_model_world_actor_learning_SEALED_reserve_paid=0,plan_sha256=sha(d/'ledger-plan.json'));save(d/'ledger-result.json',q);print(json.dumps(q))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
