"""457 runner wiring tests: real budget construction, no physics or native calls."""
import ast,inspect,json,pickle,random,tempfile,textwrap,time,unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.pilot420_backend import ResourceStop

class FixtureStop457(Exception):pass

class Compare457Tests(unittest.TestCase):
 def test_policy_root_scope_and_qualification_are_label_only_copies(self):
  from retry import compare456 as old,compare457 as new
  pairs=[(old.Comparison456.policy456,new.Comparison457.policy457),(old.scope456,new.scope457),(old.root_inputs,new.root_inputs),(old.qualify_root456,new.qualify_root457)]
  for before,after in pairs:
   oldtree=ast.parse(textwrap.dedent(inspect.getsource(before)))
   newtree=ast.parse(textwrap.dedent(inspect.getsource(after)).replace('457','456'))
   self.assertEqual(ast.dump(oldtree,include_attributes=False),ast.dump(newtree,include_attributes=False))

 def test_actual_top_level_startup_connects_same_real_meter_to_query_and_worker_caps(self):
  from retry import compare457 as runner,budget456
  from retry.source_vehicle_transition import SourceVehicleTransition
  from retry.terminal410_model import TerminalVehicleTransition
  from retry.planner419 import GoalLedger
  import Box2D
  from retry import diagnose
  seen={};py=random.getstate();npr=np.random.get_state()
  with tempfile.TemporaryDirectory() as td,ExitStack() as stack:
   root=Path(td);d=root/'stage457';d.mkdir();fixed=root/'fixed.json';pace=root/'pace.json';save(fixed,{});save(pace,{'frozen268':[]})
   p=dict(caps=dict(runner.PLAN_CAPS),deadline_utc='2026-10-20T10:01:55Z',fixed_plan=str(fixed),pace_path=str(pace),contract_sha256='fixture',semantic_sources={},sources={},protected={},original408_preserve={},order=['C0-1','P-1','C0-2','P-2'])
   save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'static-result.json',dict(passed=True,plan_sha256=sha(d/'plan.json')))
   folder=root/'stage423/actual_C0';folder.mkdir(parents=True);save(folder/'fork-private.json',dict(controller=dict(before={})))
   row=dict(progress_before=0.,goal_before=3.24,deadline_before=131);(folder/'trace-private.jsonl').write_text('\n'.join(json.dumps(row) for _ in range(119)))
   state=dict(physical=dict(actual_time=0.));ledger=GoalLedger.start(0.,0);blob=pickle.dumps((py,npr))
   stack.enter_context(patch.object(runner,'root_inputs',return_value=(state,{},ledger,{},blob,[])))
   stack.enter_context(patch.object(runner,'from_actual_full',return_value=state))
   def oldqual(_root,meter,*args):
    seen['qualification_meter']=meter;meter.b.update(ticks=1137,reserved_ticks=1137,worlds=35)
   def rootqual(_root,meter,*args):
    self.assertIs(meter,seen['qualification_meter']);meter.b.update(ticks=1353,reserved_ticks=1353,worlds=41)
   stack.enter_context(patch.object(runner,'qualify',side_effect=oldqual));stack.enter_context(patch.object(runner,'qualify_pending'));stack.enter_context(patch.object(runner,'qualify_parent'));stack.enter_context(patch.object(runner,'qualify_root457',side_effect=rootqual))
   realcreate=runner.create_meter
   def create(path):
    meter=realcreate(path);seen['meter']=meter
    self.assertIs(type(meter),budget456.Meter);self.assertEqual(meter.wall,runner.WORKER_START)
    return meter
   stack.enter_context(patch.object(runner,'create_meter',side_effect=create))
   def schedule(ctx,budget):
    seen['query_budget']=(budget.ticks,budget.worlds);raise FixtureStop457('intentional_no_integration_startup_probe')
   stack.enter_context(patch.object(budget456,'query_schedule',side_effect=schedule))
   def policy(pilot,name):
    seen['arm']=name;seen['pilot_meter']=pilot.meter
    self.assertIs(pilot.meter,seen['meter']);self.assertIs(pilot.meter,seen['qualification_meter'])
    self.assertEqual(pilot.d,d);self.assertEqual(pilot.meter.p['caps'],runner.PLAN_CAPS)
    # The unchanged planner computes its schedule with this same actual meter.
    pilot.planning_query(None,None,None,'fixture')
   stack.enter_context(patch.object(runner.Comparison457,'policy457',new=policy))
   timers=stack.enter_context(patch.object(runner.signal,'setitimer'))
   forbidden=[]
   for cls in (SourceVehicleTransition,TerminalVehicleTransition):
    for method in ('__init__','step'):
     forbidden.append(stack.enter_context(patch.object(cls,method,side_effect=AssertionError('FORBIDDEN_PHYSICS'))))
   forbidden.append(stack.enter_context(patch.object(diagnose,'make_env',side_effect=AssertionError('FORBIDDEN_NATIVE'))))
   forbidden.append(stack.enter_context(patch.object(Box2D,'b2World',side_effect=AssertionError('FORBIDDEN_WORLD'))))
   runner.run(root)
   result=read(d/'result.json');self.assertEqual(result['status'],'STOP');self.assertIn('FixtureStop457: intentional_no_integration_startup_probe',result['error'])
   self.assertEqual(seen['arm'],'C0-1');self.assertEqual(seen['query_budget'],(211639,1751));self.assertEqual((seen['meter'].b['ticks'],seen['meter'].b['worlds']),(1353,41))
   nonzero=[call.args for call in timers.call_args_list if call.args[1]>0]
   self.assertEqual(len(nonzero),2);self.assertEqual(nonzero[0][0],runner.signal.ITIMER_PROF);self.assertLessEqual(nonzero[0][1],6000);self.assertEqual(nonzero[1][0],runner.signal.ITIMER_REAL);self.assertLessEqual(nonzero[1][1],9000)
   meter=seen['meter'];meter.b['reserved_ticks']=212992
   with self.assertRaises(ResourceStop):meter.step(object(),[0.,0.,0.],'fixture_cap')
   with patch.object(budget456.time,'process_time',return_value=6000):
    with self.assertRaises(ResourceStop):meter.guard()
   for mock in forbidden:mock.assert_not_called()
  self.assertEqual(random.getstate(),py)
  current=np.random.get_state();self.assertEqual(current[0],npr[0]);np.testing.assert_array_equal(current[1],npr[1]);self.assertEqual(current[2:],npr[2:])
