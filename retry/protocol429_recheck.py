"""Preregistered static-only implementation and saved-evidence validation."""
import ast,datetime,io,json,os,signal,sys,time,unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch
from retry.loss389_analyze import read,save,sha
G=Path(__file__).resolve().parents[1]

def prepare(root):
 d=root/'stage429';assert not(d/'recheck-plan.json').exists();prior=read(root/'stage428/plan.json');v=read(root/'project-effective-budget-v448.json');assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(28444,84000,0)
 for f,h in {**prior['sources'],**prior['protected'],**prior['original408_preserve']}.items():assert sha(f)==h,f
 files=set(Path(f) for f in prior['sources']);files.update([Path(__file__),G/'retry/early429.py',G/'retry/audit429.py',G/'retry/test_early429.py',G/'retry/test_planner419.py',G/'retry/test_planner419_model_ledger.py',G/'retry/proposal429.py',root/'project-effective-budget-v448.json',root/'research-deadline-current.json']);files.update(f for f in (root/'stage428').rglob('*') if f.is_file())
 preserve={str(f):sha(f) for stage in range(420,429) for f in (root/('stage'+str(stage))).rglob('*') if f.is_file()};save(d/'prior-preservation-manifest.json',preserve);files.add(d/'prior-preservation-manifest.json')
 p=dict(stage=429,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],scope='STATIC_ONLY. Nonewmodel/world/native/reset/actor/learning/SEALED/reserve/paid. Newtypedearlyphysicalineligibleobserved1..12,H13requested,confirmedrawlength/cost/stopstate/reasonsretained,noend13/padding/finish/ranking/actualDONE/promotion. Technical/nonfinite/domain/restore/repeat/parent/RNGerrorsremainProtocolStop. Original419chooseusedunchangedwithnewinadmissibleobject, baseline/guardian semanticsunchanged.',
 raw_gap='428query36originalcontext/RNGstampnotpersisted. Preserveunboundrecord; authenticate/choose rejects it. ExplicitSYNTHETIC_STATIC_CONTEXTonlyfortype/selectioncontrols, notoriginal36ranking orphysicalproof. RawperbranchCPU/wallnotfullyretained,None ratherthanestimate.',
 tests='Frozennewtypedcontrols+alloriginal419logiccases.35stored428receiptschoiceequal,4unsafetailtimesNone; officialpartial423/427andDONErightsunchanged; early8rawpair; nofinish/padding/promotion; allgatefailures/nonfinite/domain/repeat/parentstateRNG/phase/clock/sample/cost/staleidentitynegatives; nominalneutralbaseline/missing/bothinvalidrules. World/envconstructorspatchedtofailifcalled.',
 caps=dict(static_CPU_s=60,static_wall_s=120,new_model_ticks=0,new_actual_actions=0),first_static_failure='Preservefailure; nomodeloractualregardless. Noactorpolicyinference.',sources={str(f):sha(f) for f in sorted(files)},protected=prior['protected'],original408_preserve=prior['original408_preserve']);save(d/'recheck-plan.json',p);(d/'recheck-plan.sha256').write_text(sha(d/'recheck-plan.json')+'\n');save(d/'preparation-result.json',dict(implementation_interval_wall_s=time.time()-read(d/'preparation-opening.json')['epoch'],CPU_s=None,total_preparation_fully_measured=False,scope=read(d/'preparation-opening.json')['scope']));print('429 static frozen',sha(d/'recheck-plan.json'))

class BudgetStop(BaseException):pass
def run(root):
 d=root/'stage429';p=read(d/'recheck-plan.json');assert not(d/'recheck-opening.json').exists() and sha(d/'recheck-plan.json')==(d/'recheck-plan.sha256').read_text().strip()
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 save(d/'recheck-opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));cpu=time.process_time();wall=time.perf_counter();result=None;error=None;stream=io.StringIO()
 def timeout(*a):raise BudgetStop('staticCPU60_wall120')
 old={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};signal.setitimer(signal.ITIMER_PROF,max(.001,59-time.process_time()));signal.setitimer(signal.ITIMER_REAL,119)
 try:
  from retry import test_early429,test_planner419,test_planner419_model_ledger
  from retry.source_vehicle_transition import SourceVehicleTransition
  from retry.terminal410_model import TerminalVehicleTransition
  from retry import diagnose
  suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(test_early429.EarlyProtocol),unittest.defaultTestLoader.loadTestsFromTestCase(test_planner419.PlannerLogic),unittest.defaultTestLoader.loadTestsFromTestCase(test_planner419_model_ledger.PredictedLedgerTests)])
  with patch.object(SourceVehicleTransition,'__init__',side_effect=AssertionError('FORBIDDEN_MODEL_WORLD')) as source_calls,patch.object(TerminalVehicleTransition,'__init__',side_effect=AssertionError('FORBIDDEN_TERMINAL_MODEL_WORLD')) as terminal_calls,patch.object(diagnose,'make_env',side_effect=AssertionError('FORBIDDEN_NATIVE_ENV')) as native_calls:
   result=unittest.TextTestRunner(stream=stream,verbosity=2,failfast=True).run(suite)
   if source_calls.call_count or terminal_calls.call_count or native_calls.call_count:raise AssertionError('FORBIDDEN_INTEGRATION_ATTEMPT')
  if result.wasSuccessful():
   from retry.audit429 import saved36_fixture
   from retry.early429 import ProtocolStop,choose
   from retry.receipt421_io import save_receipt
   ctx,raw,_=saved36_fixture(root);save_receipt(d/'early36-unbound-private.json',asdict(raw));save(d/'raw-evidence-gap.json',dict(original_query36_context_RNG_stamp_available=False,original_choice36_reconstructed=False,record_type='EarlyPhysicalIneligible_UNBOUND',observed_actions=raw.observed_actions,requested_initial_actions=13,observed_cost=asdict(raw.cost),proofs=asdict(raw.proofs),missing_authentication='rootstamp_and_verified_context_gate_evidence',no_original_authority_inferred=True))
 except BaseException as e:error=type(e).__name__+': '+str(e)
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in old.items():signal.signal(s,h)
  (d/'recheck-tests.log').write_text(stream.getvalue())
 q=dict(stage=429,status='STATIC_PASSED' if result and result.wasSuccessful() and error is None else 'STATIC_FAILED',error=error,tests=0 if result is None else result.testsRun,failures=0 if result is None else len(result.failures),errors=0 if result is None else len(result.errors),new_model_ticks=0,new_model_worlds=0,new_actual_actions=0,new_resets=0,world_and_env_constructors_forbidden=True,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,wholeprocess_CPU_s=time.process_time(),plan_sha256=sha(d/'recheck-plan.json'));save(d/'recheck-result.json',q);print(json.dumps(q));print(stream.getvalue()[-5000:] if q['status']!='STATIC_PASSED' else 'Frozen controls passed; no integration or actual replay.')
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
