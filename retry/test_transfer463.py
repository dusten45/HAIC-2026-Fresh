"""463 integrated native scope, budget and startup fixtures; no integration."""
import ast,copy,inspect,json,pickle,random,tempfile,textwrap,unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.pilot420_backend import ResourceStop

class Transfer463Tests(unittest.TestCase):
 def fixture_plan(self,root):
  d=root/'stage463';d.mkdir();nd=root/'native';nd.mkdir();fixed=root/'fixed.json';pace=root/'pace.json';save(fixed,{});save(pace,{'frozen268':[]})
  before=root/'project-effective-budget-v474.json';save(before,dict(version=474,research_remaining=26695,actual_cumulative_wrapper_actions=1321369,final_reserved_actions=84000,final_reserve_used=0))
  p=dict(deadline_utc='2026-10-20T10:01:55Z',budget_before_path=str(before),budget_before_sha256=sha(before),ledger_path=str(root/'project-effective-budget-v475.json'),native_directory=str(nd),fixed_plan=str(fixed),pace_path=str(pace),caps=dict(ticks=32768,worlds=768,CPU_s=1800,wall_s=2400,max_parallel=1),sources={},semantic_sources={},protected={},original408_preserve={},contract_sha256='fixture',case={})
  save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'static-result.json',dict(passed=True,plan_sha256=sha(d/'plan.json')))
  return d,p

 def test_meter_debit_journal_is_durable_before_fake_native_dispatch_and_never_refunded(self):
  from retry.meter463 import Meter463
  with tempfile.TemporaryDirectory() as td,patch('retry.meter463.signal.setitimer'):
   root=Path(td);d,p=self.fixture_plan(root);meter=Meter463(d);meter.begin_actual()
   try:
    meter.charge('reset','Original');self.assertEqual(read(p['ledger_path'])['stage463_actual_resets'],1)
    def fake_native():
     debit=read(p['ledger_path']);journal=read(Path(p['native_directory'])/'charge463-0002-private.json')
     self.assertEqual(debit['research_remaining'],26694);self.assertEqual(debit['stage463_new_wrapper_actions'],1);self.assertEqual(journal['dispatch_status'],'CHARGED_BEFORE_CALL_CONSERVATIVE_NO_REFUND')
     raise RuntimeError('fixture_native_failure')
    meter.charge('action','Original')
    with self.assertRaisesRegex(RuntimeError,'fixture_native_failure'):fake_native()
    self.assertEqual(read(p['ledger_path'])['research_remaining'],26694);self.assertEqual(meter.nb['actions'],1)
    meter.nb['arm_actions']['Original']=195
    with self.assertRaises(ResourceStop):meter.charge('action','Original')
    meter.nb['actions']=390
    with self.assertRaises(ResourceStop):meter.charge('action','SecantOnce')
    meter.nb['resets']=2
    with self.assertRaises(ResourceStop):meter.charge('reset','SecantOnce')
   finally:meter.end_actual()

 def test_model_scope_hard_caps_and_wholeworker_guard_stop_before_physics(self):
  from retry.meter463 import Meter463
  with tempfile.TemporaryDirectory() as td:
   d,p=self.fixture_plan(Path(td));meter=Meter463(d)
   with patch.object(meter,'guard'):
    meter.b['reserved_ticks']=30370
    with self.assertRaises(ResourceStop):meter.step(object(),[],'fixture')
    meter.b['reserved_ticks']=32768
    with self.assertRaises(ResourceStop):meter.step(object(),[],'fixture')
    for worlds in (597,768):
     meter.b['worlds']=worlds
     with self.assertRaises(ResourceStop):meter.world({},'fixture')
   for timing in ((1800,0),(0,2400)):
    with patch.object(meter,'wholetime',return_value=timing),patch.object(meter,'_disk'):
     with self.assertRaises(ResourceStop):meter.guard()

 def test_real_runner_one_meter_fresh_qualification_then_native_with_no_physics(self):
  from retry import transfer463 as r,diagnose
  from retry.meter463 import Meter463
  from retry.planner419 import GoalLedger
  from retry.source_vehicle_transition import SourceVehicleTransition
  from retry.terminal410_model import TerminalVehicleTransition
  import Box2D
  py=random.getstate();npr=np.random.get_state();seen={}
  with tempfile.TemporaryDirectory() as td,ExitStack() as stack:
   root=Path(td);d,p=self.fixture_plan(root);c=r.contract();p.update(execution=c,caps=c['hard'],budget_fixture=r.calculate(c));save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'static-result.json',dict(passed=True,plan_sha256=sha(d/'plan.json')))
   folder=root/'stage423/actual_C0';folder.mkdir(parents=True);save(folder/'fork-private.json',dict(controller=dict(before={})));row=dict(progress_before=0.,goal_before=3.24,deadline_before=131);(folder/'trace-private.jsonl').write_text('\n'.join(json.dumps(row) for _ in range(119)))
   state=dict(physical=dict(actual_time=0.));ledger=GoalLedger.start(0.,0);blob=pickle.dumps((py,npr))
   stack.enter_context(patch.object(r,'root_inputs',return_value=(state,{},ledger,{},blob,[])));stack.enter_context(patch.object(r,'from_actual_full',return_value=state));stack.enter_context(patch.object(r,'check_storage',return_value={}))
   real_create=r.create_meter
   def create(path):
    meter=real_create(path);seen['meter']=meter;self.assertIs(type(meter),Meter463);self.assertEqual(meter.worker_start,r.WORKER_START);return meter
   stack.enter_context(patch.object(r,'create_meter',side_effect=create))
   def oldqual(_root,meter,*args):
    self.assertIs(meter,seen['meter']);self.assertIsNotNone(meter.active);meter.b.update(ticks=1137,reserved_ticks=1137,worlds=35);seen['oldqual']=True
   def rootqual(_root,meter,*args):
    self.assertIs(meter,seen['meter']);self.assertTrue(seen['oldqual']);self.assertTrue(meter.qualification_passed);meter.b.update(ticks=1353,reserved_ticks=1353,worlds=41);seen['rootqual']=True
   stack.enter_context(patch.object(r,'qualify',side_effect=oldqual));stack.enter_context(patch.object(r,'qualify_pending'));stack.enter_context(patch.object(r,'qualify_parent'));stack.enter_context(patch.object(r,'qualify_root463',side_effect=rootqual))
   def actual(_root,meter,fixed,pace):
    self.assertIs(meter,seen['meter']);self.assertTrue(seen['rootqual']);self.assertIsNone(meter.active);self.assertIsNone(meter.actual_start)
    self.assertEqual((meter.b['ticks'],meter.b['worlds']),(1353,41));self.assertEqual(meter.nb['actions'],0);self.assertEqual(meter.nb['resets'],0)
    self.assertTrue(read(d/'preflight-private.json')['passed']);self.assertFalse(Path(p['ledger_path']).exists());seen['native_entered']=True
    return [dict(completed=True,lap_ms=15000),dict(completed=True,lap_ms=14900)]
   native=stack.enter_context(patch.object(r,'actual463',side_effect=actual));timers=stack.enter_context(patch.object(r.signal,'setitimer'));forbidden=[]
   for cls in (SourceVehicleTransition,TerminalVehicleTransition):
    for method in ('__init__','step'):forbidden.append(stack.enter_context(patch.object(cls,method,side_effect=AssertionError('FORBIDDEN_PHYSICS'))))
   forbidden.append(stack.enter_context(patch.object(diagnose,'make_env',side_effect=AssertionError('FORBIDDEN_NATIVE'))));forbidden.append(stack.enter_context(patch.object(Box2D,'b2World',side_effect=AssertionError('FORBIDDEN_WORLD'))))
   r.run(root);native.assert_called_once();self.assertTrue(seen['native_entered']);out=read(d/'result.json');self.assertEqual(out['status'],'NATIVE_FULL_PAIR_COMPLETED');self.assertEqual(out['official_lap_gain_s'],.1)
   nonzero=[x.args for x in timers.call_args_list if x.args[1]>0];self.assertTrue(nonzero)
   for kind,seconds in nonzero:
    self.assertLessEqual(seconds,1800 if kind==r.signal.ITIMER_PROF else 2400)
   self.assertFalse(Path(p['ledger_path']).exists())
   for mock in forbidden:mock.assert_not_called()
  self.assertEqual(random.getstate(),py);now=np.random.get_state();self.assertEqual(now[0],npr[0]);np.testing.assert_array_equal(now[1],npr[1]);self.assertEqual(now[2:],npr[2:])
 def test_integrated_cost_covers125prefix70suffix_firstfixed69guardian(self):
  fixed=2*2*13*4;guardian=2*69*2*2*13*4
  self.assertEqual((1458+fixed+guardian,41+2*2+2*69*4),(30370,597))
  self.assertEqual((2*(125+70),125+70),(390,195))
  self.assertLessEqual(30370,32768);self.assertLessEqual(597,768)

 def test_modes_one_fixed_then69_guardians_and_pending_no_extra_pulse(self):
  from retry.query463 import mode463
  for arm,recipe in [('Original','nominal'),('SecantOnce','fullgas')]:
   self.assertEqual(mode463(arm,1,'FIRST_LAP',False),('FIXED_FIRST',recipe))
   for n in range(2,71):
    self.assertEqual(mode463(arm,n,'FIRST_LAP',False),('GUARDIAN','nominal'))
    self.assertEqual(mode463(arm,n,'FINISH_CONFIRM',True),('REGISTERED_PENDING_GUARDIAN','nominal'))
   for n in (0,71):
    with self.assertRaises(Exception):mode463(arm,n,'FIRST_LAP',False)
   with self.assertRaises(Exception):mode463(arm,1,'FIRST_LAP',True)
   with self.assertRaises(Exception):mode463(arm,2,'FINISH_CONFIRM',False)

 def test_prefix_source_is_saved_only_and_boundaries22_112_125(self):
  from retry import native463 as r
  prefix=[dict(old=i) for i in range(22)];root=Path('/fixture-not-real')
  with patch.object(r,'load_receipt',side_effect=lambda p:dict(selected_first=dict(path=str(p)))) as load:
   self.assertEqual(r.prefix_source463(root,prefix,22),prefix[21]);load.assert_not_called()
   self.assertIn('candidate_decision1-',r.prefix_source463(root,prefix,23)['path'])
   self.assertIn('candidate_decision90-',r.prefix_source463(root,prefix,112)['path'])
   self.assertIn('P_decision1-',r.prefix_source463(root,prefix,113)['path'])
   self.assertIn('P_decision13-',r.prefix_source463(root,prefix,125)['path'])
   for step in (0,126):
    with self.assertRaises(Exception):r.prefix_source463(root,prefix,step)

 def test_native_prefix_no_query_and_existing_fact_first_charge_path(self):
  from retry.native463 import actual463
  from retry.authority439 import NativeAuthority439
  tree=ast.parse(textwrap.dedent(inspect.getsource(actual463)))
  loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='step')
  self.assertEqual(ast.unparse(loop.iter),'range(1, 196)')
  prefix=next(n for n in loop.body if isinstance(n,ast.If) and ast.unparse(n.test)=='step <= 125')
  calls=[ast.unparse(n.func) for n in ast.walk(ast.Module(body=prefix.body,type_ignores=[])) if isinstance(n,ast.Call)]
  self.assertNotIn('query.query_policy',calls);self.assertIn('native.commit_native_observation',calls);self.assertIn('native.verify_prefix',calls)
  later=[ast.unparse(n) for n in prefix.orelse]
  self.assertTrue(any('step - 125' in line and 'query.query_policy' in line for line in later))
  source=textwrap.dedent(inspect.getsource(NativeAuthority439._dispatch_checked))
  self.assertLess(source.index('self.charge_native()'),source.index('self.dispatcher.call('))
  self.assertIn('charge_native=lambda: meter.charge',ast.unparse(tree))
