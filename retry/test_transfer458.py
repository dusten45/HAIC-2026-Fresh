"""458 native transfer wiring fixtures: no simulation or native dispatch."""
import ast,copy,inspect,json,tempfile,textwrap,unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
from retry.loss389_analyze import read,save,sha
from retry.pilot420_backend import ResourceStop

class FixtureStop458(Exception):pass

class Transfer458Tests(unittest.TestCase):
 def test_bounded_same100_suffix_cost_fits_approved_envelope(self):
  planned=8*3*2*(13+308)*4+(2*100-8)*2*2*13*4+1458
  worlds=8*3*2+(2*100-8)*2*2+41
  self.assertEqual((planned,worlds),(103026,857))
  self.assertLessEqual(planned,212992);self.assertLessEqual(worlds,1792)
  self.assertEqual(112+100,212);self.assertLessEqual(2*212,440)

 def test_native_readonly_query_is442_with_only_scope_and_provenance_labels_changed(self):
  from retry.paired442_query import Query442
  from retry.query458 import Query458
  old=textwrap.dedent(inspect.getsource(Query442.query)).replace("CURRENT_ACTUAL_PARENT442_READONLY","CURRENT_ACTUAL_PARENT458_READONLY")
  old=old.replace("_,planned=scope(arm,planner_used,ctrl.phase());planned=planned and pending is None","_,planned=scope457(arm,planner_used,ctrl.phase(),pending is not None)")
  old=old.replace("Explicit442once_only_actual_pair; model_receipt_itself_has_no_authority","EXPLICIT458_ONCE_KNOWN_DEV_NATIVE_PAIR_CHARGE_AND_OWN_FACTS_ONLY; model_receipt_itself_has_no_authority")
  new=textwrap.dedent(inspect.getsource(Query458.query))
  self.assertEqual(ast.dump(ast.parse(old),include_attributes=False),ast.dump(ast.parse(new),include_attributes=False))
  self.assertEqual(ast.dump(ast.parse(textwrap.dedent(inspect.getsource(Query442.unchanged)))),ast.dump(ast.parse(textwrap.dedent(inspect.getsource(Query458.unchanged)))))
  from retry.budget456 import Planning456
  self.assertIs(Query458.planning_query,Planning456.planning_query)
  for method in ('new','guardian','short_pair','runtime_evidence','validate_child','validate_saved_child'):
   self.assertIs(getattr(Query458,method),getattr(Query442,method))
 def test_first8_quota_consumed_only_by_eligible_fresh_planning_queries(self):
  from retry.compare457 import scope457
  for used in range(9):
   self.assertEqual(scope457('C0',used,'FIRST_LAP',False),(100,False))
   self.assertEqual(scope457('P',used,'FIRST_LAP',False),(100,used<8))
   self.assertEqual(scope457('P',used,'FIRST_LAP',True),(100,False))
   self.assertEqual(scope457('P',used,'FINISH_CONFIRM',False),(100,False))
  from retry.native458 import actual458
  s=inspect.getsource(actual458)
  self.assertIn("planner+=int(record['planner_used'])",s)
  self.assertIn('query.query(history,before,nominal,arm,step-112,planner)',s)
 def test_prefix112_uses_fact_first_existing_native_authority_and_exact_root(self):
  from retry.native458 import actual458
  tree=ast.parse(textwrap.dedent(inspect.getsource(actual458)))
  prefix=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='step <= 112')
  calls=[ast.unparse(n.func) for stmt in prefix.body for n in ast.walk(stmt) if isinstance(n,ast.Call)]
  self.assertLess(calls.index('native.dispatch'),calls.index('native.commit_native_observation'))
  self.assertLess(calls.index('native.commit_native_observation'),calls.index('native.verify_prefix'))
  s=inspect.getsource(actual458)
  for required in ('range(1,213)','if step==113:',"require_equal(fork,root_proof",'step<=22',"candidate_decision",'suffix_step(native,history,frame,trace,pending)',"native.ledger.done","native.last_verification['passed']"):
   self.assertIn(required,s)
  self.assertNotIn('query.query(',ast.unparse(ast.Module(body=prefix.body,type_ignores=[])))
 def test_meter212992_bypasses_old98304_and_charges_before_native_limits(self):
  from retry.meter458 import Meter458
  from retry.paired442_meter import Meter as Meter442
  m=Meter458.__new__(Meter458);m.p=dict(caps=dict(ticks=212992,worlds=1792));m.active=(1.,1.);m.b=dict(reserved_ticks=98304)
  with patch.object(Meter442,'step',return_value='no_integration') as step:
   self.assertEqual(m.step(object(),[],'fixture'),'no_integration');step.assert_called_once()
  m.b['reserved_ticks']=212992
  with patch.object(Meter442,'step') as step:
   with self.assertRaises(ResourceStop):m.step(object(),[],'fixture')
   step.assert_not_called()
  m.active=None;m.actual_start=(1.,1.);m.guard=lambda:None;m.persist=lambda:None
  for arm in ('C0','P'):
   m.nb=dict(actions=219,resets=0,arm_actions={arm:219},arm_resets={});m.charge('action',arm)
   self.assertEqual(m.nb['actions'],220)
   with self.assertRaises(ResourceStop):m.charge('action',arm)
  m.nb=dict(actions=440,resets=2,arm_actions={},arm_resets={})
  with self.assertRaises(ResourceStop):m.charge('action','C0')
  with self.assertRaises(ResourceStop):m.charge('reset','P')
  m.nb=dict(actions=0,resets=0,arm_actions={},arm_resets={});m.charge('reset','C0')
  with self.assertRaises(ResourceStop):m.charge('reset','C0')
 def test_real_top_level_startup_binds_same_meter_to_qualification_native_query_and_exclusive_timers(self):
  from retry import transfer458 as runner,budget456,meter458
  from retry.query458 import Query458
  from retry.source_vehicle_transition import SourceVehicleTransition
  from retry.terminal410_model import TerminalVehicleTransition
  from retry.planner419 import GoalLedger
  from retry import diagnose
  import pickle,random,numpy as np,Box2D
  seen={};py=random.getstate();npr=np.random.get_state()
  with tempfile.TemporaryDirectory() as td,ExitStack() as stack:
   root=Path(td);d=root/'stage458';d.mkdir();fixed=root/'fixed.json';pace=root/'pace.json';save(fixed,{});save(pace,{'frozen268':[]})
   p=dict(caps=dict(ticks=212992,worlds=1792,CPU_s=6000,wall_s=9000),model_caps=dict(planned_ticks=103026,planned_worlds=857,hard_ticks=212992,hard_worlds=1792,CPU_s=6000,wall_s=9000,workers=1),actual_caps=dict(actions=440,arm_actions=220,resets=2,CPU_s=240,wall_s=480),deadline_utc='2026-10-20T10:01:55Z',fixed_plan=str(fixed),pace_path=str(pace),semantic_sources={},sources={},protected={},original408_preserve={})
   save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'static-result.json',dict(passed=True,plan_sha256=sha(d/'plan.json')))
   folder=root/'stage423/actual_C0';folder.mkdir(parents=True);save(folder/'fork-private.json',dict(controller=dict(before={})))
   row=dict(progress_before=0.,goal_before=3.24,deadline_before=131);(folder/'trace-private.jsonl').write_text('\n'.join(json.dumps(row) for _ in range(119)))
   state=dict(physical=dict(actual_time=0.));ledger=GoalLedger.start(0.,0);blob=pickle.dumps((py,npr))
   stack.enter_context(patch.object(runner,'root_inputs',return_value=(state,{},ledger,{},blob,[])))
   stack.enter_context(patch.object(runner,'from_actual_full',return_value=state))
   def oldqual(_root,meter,*args):
    seen['qualification_meter']=meter;meter.b.update(ticks=1137,reserved_ticks=1137,worlds=35)
    self.assertIsNotNone(meter.active)
   def rootqual(_root,meter,*args):
    self.assertIs(meter,seen['qualification_meter']);meter.b.update(ticks=1353,reserved_ticks=1353,worlds=41)
    self.assertIsNotNone(meter.active)
   stack.enter_context(patch.object(runner,'qualify',side_effect=oldqual));stack.enter_context(patch.object(runner,'qualify_pending'));stack.enter_context(patch.object(runner,'qualify_parent'))
   qualname='qualify_root458' if hasattr(runner,'qualify_root458') else 'qualify_root457'
   stack.enter_context(patch.object(runner,qualname,side_effect=rootqual))
   realcreate=runner.create_meter
   def create(path):
    meter=realcreate(path);seen['meter']=meter;self.assertIs(type(meter),meter458.Meter458);return meter
   stack.enter_context(patch.object(runner,'create_meter',side_effect=create))
   def schedule(ctx,budget):
    seen['query_budget']=(budget.ticks,budget.worlds);raise FixtureStop458('intentional_no_integration_startup_probe')
   stack.enter_context(patch.object(budget456,'query_schedule',side_effect=schedule))
   def actual(_root,meter,fixed_data,pace_data):
    self.assertIs(meter,seen['meter']);self.assertIs(meter,seen['qualification_meter'])
    self.assertTrue(meter.qualification_passed);self.assertIsNone(meter.active)
    meter.begin_actual();pilot=Query458(_root,meter,fixed_data,pace_data);self.assertIs(pilot.meter,meter)
    with meter.model('fixture_actual_fresh_query'):
     pilot.planning_query(None,None,None,'fixture')
   stack.enter_context(patch.object(runner,'actual458',side_effect=actual))
   timers=stack.enter_context(patch.object(meter458.signal,'setitimer'))
   forbidden=[]
   for cls in (SourceVehicleTransition,TerminalVehicleTransition):
    for method in ('__init__','step'):forbidden.append(stack.enter_context(patch.object(cls,method,side_effect=AssertionError('FORBIDDEN_PHYSICS'))))
   forbidden.append(stack.enter_context(patch.object(diagnose,'make_env',side_effect=AssertionError('FORBIDDEN_NATIVE'))))
   forbidden.append(stack.enter_context(patch.object(Box2D,'b2World',side_effect=AssertionError('FORBIDDEN_WORLD'))))
   runner.run(root)
   result=read(d/'result.json');self.assertEqual(result['status'],'STOP');self.assertIn('FixtureStop458: intentional_no_integration_startup_probe',result['error'])
   self.assertEqual(seen['query_budget'],(211639,1751));m=seen['meter'];self.assertEqual((m.b['ticks'],m.b['worlds']),(1353,41));self.assertEqual((m.nb['actions'],m.nb['resets']),(0,0))
   nonzero=[call.args for call in timers.call_args_list if len(call.args)>1 and call.args[1]>0]
   prof=[args[1] for args in nonzero if args[0]==meter458.signal.ITIMER_PROF];wall=[args[1] for args in nonzero if args[0]==meter458.signal.ITIMER_REAL]
   self.assertTrue(any(5000<x<=6000 for x in prof));self.assertTrue(any(0<x<=240 for x in prof))
   self.assertTrue(any(8000<x<=9000 for x in wall));self.assertTrue(any(0<x<=480 for x in wall))
   with patch.object(m,'modeltime',return_value=(6000.,0.)):
    with self.assertRaises(ResourceStop):m.guard()
   with patch.object(m,'nativetime',return_value=(240.,0.)):
    with self.assertRaises(ResourceStop):m.guard()
   for mock in forbidden:mock.assert_not_called()
  self.assertEqual(random.getstate(),py);current=np.random.get_state();self.assertEqual(current[0],npr[0]);np.testing.assert_array_equal(current[1],npr[1]);self.assertEqual(current[2:],npr[2:])
