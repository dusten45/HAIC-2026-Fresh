"""460 full-arm budget, two-root startup wiring; every physics entry is forbidden."""
import ast,inspect,json,pickle,random,tempfile,textwrap,unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.pilot420_backend import ResourceStop

class FixtureStop460(Exception):pass

class Compare460Tests(unittest.TestCase):
 def test_budget_is_derived_from_all_four_scheduled_arm_quotas(self):
  from retry import compare460 as r
  b=r.planned_budget()
  self.assertEqual(b['quotas'],dict.fromkeys(r.ORDER,8))
  self.assertEqual((b['parts']['planner']['queries'],b['parts']['guardian']['queries']),(32,368))
  self.assertEqual((b['ticks'],b['worlds']),(326346,1715))
  self.assertLessEqual(b['ticks'],r.PLAN_CAPS['ticks']);self.assertLessEqual(b['worlds'],r.PLAN_CAPS['worlds'])
  for root in ['NoPulse','Pulse']:
   for quota in [0,7,8,99]:
    self.assertEqual(r.scope460(root,quota,'FIRST_LAP'),(100,quota<8))
    self.assertEqual(r.scope460(root,quota,'FIRST_LAP',True),(100,False))
    self.assertEqual(r.scope460(root,quota,'FINISH_CONFIRM'),(100,False))
  with patch.object(r,'ORDER',r.ORDER+['Pulse-3']):
   self.assertGreater(r.planned_budget()['ticks'],r.PLAN_CAPS['ticks'])

 def test_parent_loop_is_unchanged_except_labels_and_scope_adapter(self):
  from retry import compare457 as old,compare460 as new
  a=ast.parse(textwrap.dedent(inspect.getsource(old.Comparison457.policy457)))
  b=ast.parse(textwrap.dedent(inspect.getsource(new.Comparison460.policy460)).replace('460','457'))
  self.assertEqual(ast.dump(a,include_attributes=False),ast.dump(b,include_attributes=False))

 def test_root_selector_and_factual_nominal13_saved_inputs(self):
  from retry import compare460 as r
  root=Path('/workspace/haic-private-retry-20261009')
  for label,n in [('NoPulse',117),('Pulse',113)]:
   state,memory,ledger,rng,blob,expected=r.root_inputs(root,label)
   self.assertEqual(expected[0]['step'],n);self.assertEqual(len(expected),13)
   self.assertEqual(memory,expected[0]['memory_before']);self.assertFalse(ledger.done)
   self.assertTrue(all(x['command']==x['nominal'] for x in expected))

 def test_real_startup_meter_query_caps_and_both_root_qualifications(self):
  self.startup(False)

 def test_all_four_arms_bind_own_root_and_prefix_before_dispatch(self):
  self.startup(True)

 def startup(self,full):
  from retry import compare460 as r,budget456,diagnose
  from retry.source_vehicle_transition import SourceVehicleTransition
  from retry.terminal410_model import TerminalVehicleTransition
  from retry.planner419 import GoalLedger
  import Box2D
  py=random.getstate();npr=np.random.get_state();seen=dict(roots=[],arms=[])
  with tempfile.TemporaryDirectory() as td,ExitStack() as stack:
   root=Path(td);d=root/'stage460';d.mkdir();fixed=root/'fixed.json';pace=root/'pace.json';save(fixed,{});save(pace,{'frozen268':[]})
   p=dict(caps=dict(r.PLAN_CAPS),deadline_utc='2026-10-20T10:01:55Z',fixed_plan=str(fixed),pace_path=str(pace),contract_sha256='fixture',semantic_sources={},sources={},protected={},original408_preserve={},order=r.ORDER,prefix_elapsed_s=dict(NoPulse=9.28,Pulse=8.96))
   save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'static-result.json',dict(passed=True,plan_sha256=sha(d/'plan.json')))
   folder=root/'stage423/actual_C0';folder.mkdir(parents=True);save(folder/'fork-private.json',dict(controller=dict(before={})))
   row=dict(progress_before=0.,goal_before=3.24,deadline_before=131);(folder/'trace-private.jsonl').write_text('\n'.join(json.dumps(row) for _ in range(119)))
   ledgers={x:GoalLedger.start(i,0) for i,x in enumerate(['NoPulse','Pulse'])};blob=pickle.dumps((py,npr))
   def inputs(_root,label):return dict(physical=dict(actual_time=0.),label=label),dict(label=label),ledgers[label],dict(label=label),blob,[]
   stack.enter_context(patch.object(r,'root_inputs',side_effect=inputs));stack.enter_context(patch.object(r,'from_actual_full',return_value=dict(physical=dict(actual_time=0.))))
   def oldqual(_root,meter,*args):seen['meter']=meter;meter.b.update(ticks=1137,reserved_ticks=1137,worlds=35)
   def rootqual(_root,meter,*args):
    self.assertIs(meter,seen['meter']);label=args[-1];seen['roots'].append(label)
    meter.b['ticks']+=216;meter.b['reserved_ticks']+=216;meter.b['worlds']+=6
   stack.enter_context(patch.object(r,'qualify',side_effect=oldqual));stack.enter_context(patch.object(r,'qualify_pending'));stack.enter_context(patch.object(r,'qualify_parent'));stack.enter_context(patch.object(r,'qualify_root460',side_effect=rootqual))
   def schedule(ctx,budget):
    seen['query_budget']=(budget.ticks,budget.worlds);raise FixtureStop460('intentional_static_no_integration')
   stack.enter_context(patch.object(budget456,'query_schedule',side_effect=schedule))
   def policy(pilot,name):
    base=name.split('-')[0];seen['arms'].append(name)
    self.assertIs(pilot.meter,seen['meter']);self.assertIs(type(pilot.meter),r.Meter460)
    self.assertEqual(pilot.state['label'],base);self.assertEqual(pilot.memory['label'],base);self.assertIs(pilot.actual_ledger,ledgers[base]);self.assertEqual(pilot.archive_rng['label'],base)
    binding=read(d/(name+'-root-binding-private.json'));self.assertEqual(binding['prefix_elapsed_s'],9.28 if base=='NoPulse' else 8.96)
    if not full:pilot.planning_query(None,None,None,'fixture')
    pilot.results.append(dict(arm=name,finish_ticks=dict(lo=1,hi=2),official_model_finish=True))
   stack.enter_context(patch.object(r.Comparison460,'policy460',new=policy))
   timers=stack.enter_context(patch.object(r.signal,'setitimer'));forbidden=[]
   for cls in (SourceVehicleTransition,TerminalVehicleTransition):
    for method in ('__init__','step'):forbidden.append(stack.enter_context(patch.object(cls,method,side_effect=AssertionError('FORBIDDEN_PHYSICS'))))
   forbidden.append(stack.enter_context(patch.object(diagnose,'make_env',side_effect=AssertionError('FORBIDDEN_NATIVE'))));forbidden.append(stack.enter_context(patch.object(Box2D,'b2World',side_effect=AssertionError('FORBIDDEN_WORLD'))))
   r.run(root);result=read(d/'result.json')
   self.assertEqual(seen['roots'],['NoPulse','Pulse']);self.assertEqual((seen['meter'].b['ticks'],seen['meter'].b['worlds']),(1569,47))
   if full:
    self.assertEqual(seen['arms'],r.ORDER);self.assertEqual(result['hybrid_total_NoPulse_minus_Pulse_bracket_s'],[.30,.34])
   else:
    self.assertEqual(result['status'],'STOP');self.assertIn('FixtureStop460: intentional_static_no_integration',result['error']);self.assertEqual(seen['query_budget'],(326111,1745))
   nonzero=[call.args for call in timers.call_args_list if call.args[1]>0]
   self.assertEqual(len(nonzero),2);self.assertLessEqual(nonzero[0][1],9000);self.assertLessEqual(nonzero[1][1],12000)
   meter=seen['meter'];meter.b['reserved_ticks']=327680
   with self.assertRaises(ResourceStop):meter.step(object(),[0.,0.,0.],'fixture_cap')
   with patch.object(budget456.time,'process_time',return_value=9000):
    with self.assertRaises(ResourceStop):meter.guard()
   for mock in forbidden:mock.assert_not_called()
  self.assertEqual(random.getstate(),py);now=np.random.get_state();self.assertEqual(now[0],npr[0]);np.testing.assert_array_equal(now[1],npr[1]);self.assertEqual(now[2:],npr[2:])
